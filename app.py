from flask import Flask, render_template, jsonify, request
import logging
import os
import select
from os import O_RDONLY, O_NONBLOCK
from flask_socketio import SocketIO
import threading
import time
from utils.audio_control import AudioController
from utils.music_recognition import MusicRecognitionService
import json

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'airplay-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize controllers and services
audio_controller = AudioController()
music_recognition = MusicRecognitionService(sample_rate=44100, chunk_size=1024, record_seconds=10)

# Create artwork directory if it doesn't exist
if not os.path.exists(os.path.join('static', 'artwork')):
    os.makedirs(os.path.join('static', 'artwork'))

# Thread for sending metadata updates
def metadata_update_thread():
    """Thread to periodically send metadata updates from music recognition service"""
    logger.info("Starting metadata update thread")
    
    # Start the music recognition service
    music_recognition.start()
    
    while True:
        try:
            # Get the current metadata from the music recognition service
            metadata = music_recognition.get_current_metadata()
            
            # Send the metadata to clients
            socketio.emit('metadata_update', metadata)
            
            # Add AirPlay status too
            metadata['airplay_active'] = audio_controller.is_playing()
            
            # Log current playback state (less frequently to avoid log spam)
            if metadata.get('title') != 'Not Playing':
                logger.debug(f"Currently playing: {metadata.get('title')} by {metadata.get('artist')}")
            
        except Exception as e:
            logger.error(f"Error in metadata thread: {e}")
        
        # Sleep for a bit to avoid too frequent updates
        time.sleep(2)

# Start the metadata update thread
metadata_thread = threading.Thread(target=metadata_update_thread)
metadata_thread.daemon = True

@app.route('/health')
def health_check():
    """Health check endpoint"""
    logger.info("Health check requested")
    return jsonify({
        "status": "healthy", 
        "server": "running",
        "airplay_active": audio_controller.is_playing(),
        "recognition_active": music_recognition.is_running
    })

@app.route('/')
def index():
    """Main display page"""
    logger.info("Display page requested")
    return render_template('display.html')

@app.route('/setup')
def setup():
    """Setup page for AcoustID API configuration"""
    return render_template('setup.html')

@app.route('/now-playing')
def now_playing():
    """Get current playback metadata"""
    try:
        # Get metadata from the music recognition service
        metadata = music_recognition.get_current_metadata()
        
        # Check if AirPlay is active
        metadata['airplay_active'] = audio_controller.is_playing()
        
        # Add debug info for Shairport-Sync
        pipe_path = '/tmp/shairport-sync-metadata'
        pipe_exists = os.path.exists(pipe_path)
        pipe_perms = 'N/A'
        pipe_owner = 'N/A'
        
        if pipe_exists:
            try:
                stat = os.stat(pipe_path)
                pipe_perms = oct(stat.st_mode)[-3:]
                pipe_owner = f"{stat.st_uid}:{stat.st_gid}"
            except OSError as e:
                logger.error(f"Error checking pipe permissions: {e}")
        
        metadata['_debug'] = {
            'pipe_exists': pipe_exists,
            'permissions': pipe_perms,
            'owner': pipe_owner,
            'shairport_running': audio_controller.is_playing(),
            'last_error': None
        }
        
        return jsonify(metadata)
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error in now-playing endpoint: {error_msg}")
        return jsonify({
            'title': 'Cannot get metadata',
            'artist': None,
            'album': None,
            'artwork': None,
            '_debug': {
                'pipe_exists': False,
                'permissions': 'N/A',
                'owner': 'N/A',
                'shairport_running': False,
                'last_error': error_msg
            }
        })

@app.route('/debug/pipe-data')
def debug_pipe_data():
    """Diagnostic endpoint to check raw pipe data"""
    try:
        pipe_path = '/tmp/shairport-sync-metadata'
        if not os.path.exists(pipe_path):
            return jsonify({'error': 'Pipe not found'})

        # Open pipe in non-blocking mode
        fd = os.open(pipe_path, os.O_RDONLY | os.O_NONBLOCK)
        try:
            with os.fdopen(fd, 'rb') as pipe:
                ready, _, _ = select.select([pipe], [], [], 0.5)  # 500ms timeout
                if ready:
                    data = pipe.read(4096)
                    if data:
                        try:
                            decoded = data.decode('utf-8', errors='ignore')
                            return jsonify({
                                'status': 'success',
                                'raw_data_length': len(data),
                                'decoded_data': decoded[:500],  # First 500 chars
                                'hex_data': data.hex()[:100]  # First 50 bytes in hex
                            })
                        except Exception as e:
                            return jsonify({
                                'status': 'decode_error',
                                'error': str(e),
                                'raw_length': len(data),
                                'hex_data': data.hex()[:100]
                            })
                    else:
                        return jsonify({
                            'status': 'no_data',
                            'message': 'Pipe is empty'
                        })
                else:
                    return jsonify({
                        'status': 'timeout',
                        'message': 'No data available within timeout period'
                    })
        finally:
            # Ensure we always close the file descriptor
            try:
                os.close(fd)
            except:
                pass

    except Exception as e:
        logger.error(f"Error in debug_pipe_data: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        })

@app.route('/recognition/status')
def recognition_status():
    """Get the status of the music recognition service"""
    return jsonify({
        "running": music_recognition.is_running,
        "last_recognition_time": music_recognition.last_recognition_time,
        "cooldown": music_recognition.recognition_cooldown
    })

@app.route('/api-key', methods=['POST'])
def set_api_key():
    """Set the AcoustID API key"""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({"status": "error", "message": "No API key provided"}), 400
            
        api_key = data['api_key']
        
        # Save the API key to environment variable
        os.environ['ACOUSTID_API_KEY'] = api_key
        
        # Update the API key in the music recognition service
        # Access the global variable in the music_recognition module
        import utils.music_recognition
        utils.music_recognition.ACOUSTID_API_KEY = api_key
        
        return jsonify({"status": "success", "message": "API key set successfully"})
    except Exception as e:
        logger.error(f"Error setting API key: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application on port 5000...")
        # Start the metadata update thread
        metadata_thread.start()
        
        # Use 0.0.0.0 to ensure the server is accessible externally
        # Set use_reloader to False since we're in a thread
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                    use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        raise