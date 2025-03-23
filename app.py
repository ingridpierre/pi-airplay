from flask import Flask, render_template, jsonify
import logging
import os
import select
from os import O_RDONLY, O_NONBLOCK  # Add O_NONBLOCK import
from flask_socketio import SocketIO
import threading
import time
from utils.audio_control import AudioController
from utils.audio_visualizer import AudioVisualizer
from utils.artwork_handler import ArtworkHandler
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

# Initialize controllers and helpers
audio_controller = AudioController()
audio_visualizer = AudioVisualizer(buffer_size=3, sample_rate=44100, block_size=2048, channels=1)
artwork_handler = ArtworkHandler(os.path.abspath('static'))

# Create artwork directory if it doesn't exist
if not os.path.exists(os.path.join('static', 'artwork')):
    os.makedirs(os.path.join('static', 'artwork'))

# Thread for sending real-time audio visualization data
def send_visualization_thread():
    logger.info("Starting visualization data thread")
    last_is_playing = False
    
    while True:
        if audio_visualizer.is_running:
            try:
                # Check if music is playing via AirPlay
                is_playing = audio_controller.is_playing()
                
                # If playing status changed, update the visualizer
                if is_playing != last_is_playing:
                    audio_visualizer._is_playing = is_playing
                    last_is_playing = is_playing
                
                # Get and send visualization data
                vis_data = audio_visualizer.get_visualization_data()
                
                # Add playing status to visualization data
                vis_data['is_playing'] = is_playing
                
                # Send the data via Socket.IO
                socketio.emit('visualization_data', vis_data)
            except Exception as e:
                logger.error(f"Error sending visualization data: {e}")
        time.sleep(0.1)  # Send every 100ms

# Start the visualization thread
visualization_thread = threading.Thread(target=send_visualization_thread)
visualization_thread.daemon = True

@app.route('/health')
def health_check():
    logger.info("Health check requested")
    return jsonify({"status": "healthy", "server": "running"})

@app.route('/')
def index():
    logger.info("Index page requested")
    return render_template('index.html')

@app.route('/now-playing')
def now_playing():
    try:
        # Check metadata pipe existence and permissions
        pipe_path = '/tmp/shairport-sync-metadata'
        pipe_exists = os.path.exists(pipe_path)
        pipe_perms = 'N/A'
        pipe_owner = 'N/A'

        if pipe_exists:
            try:
                stat = os.stat(pipe_path)
                pipe_perms = oct(stat.st_mode)[-3:]
                pipe_owner = f"{stat.st_uid}:{stat.st_gid}"
                logger.info(f"Metadata pipe exists with permissions: {pipe_perms}, owner: {pipe_owner}")
            except OSError as e:
                logger.error(f"Error checking pipe permissions: {e}")

        # Get metadata from controller
        metadata = audio_controller.get_current_metadata()
        logger.debug(f"Retrieved metadata: {metadata}")
        
        # Process artwork if it exists in the metadata
        if 'artwork' in metadata and metadata['artwork']:
            # Save the artwork and get the URL
            artwork_url = artwork_handler.save_artwork_from_metadata(metadata)
            if artwork_url:
                metadata['artwork_url'] = artwork_url
                logger.info(f"Saved artwork at {artwork_url}")
            else:
                logger.warning("Failed to save artwork")
        # Check for existing artwork
        else:
            artwork_url = artwork_handler.get_current_artwork_url()
            if artwork_url:
                metadata['artwork_url'] = artwork_url
        
        # Add debug information with proper initialization
        pipe_exists = False
        pipe_perms = "N/A"
        pipe_owner = "N/A"
        
        # Get pipe information if it exists
        try:
            pipe_path = '/tmp/shairport-sync-metadata'
            if os.path.exists(pipe_path):
                pipe_exists = True
                pipe_stats = os.stat(pipe_path)
                pipe_perms = oct(pipe_stats.st_mode)[-3:]  # Get last 3 digits (file permissions)
                pipe_owner = f"{pipe_stats.st_uid}:{pipe_stats.st_gid}"
                logger.info(f"Metadata pipe exists with permissions: {pipe_perms}, owner: {pipe_owner}")
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
            'artist': 'Error',
            'album': str(error_msg),
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

@app.route('/visualizer')
def visualizer():
    """Route for the audio visualizer page"""
    logger.info("Visualizer page requested")
    return render_template('visualizer.html')

@app.route('/visualizer/start')
def start_visualizer():
    """Start the audio visualizer"""
    try:
        if not audio_visualizer.is_running:
            audio_visualizer.start()
            logger.info("Audio visualizer started")
        return jsonify({"status": "success", "message": "Visualizer started"})
    except Exception as e:
        logger.error(f"Error starting visualizer: {e}")
        return jsonify({"status": "error", "message": str(e)})

@app.route('/visualizer/stop')
def stop_visualizer():
    """Stop the audio visualizer"""
    try:
        if audio_visualizer.is_running:
            audio_visualizer.stop()
            logger.info("Audio visualizer stopped")
        return jsonify({"status": "success", "message": "Visualizer stopped"})
    except Exception as e:
        logger.error(f"Error stopping visualizer: {e}")
        return jsonify({"status": "error", "message": str(e)})

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application on port 5000...")
        # Start the visualization thread
        visualization_thread.start()
        
        # Use 0.0.0.0 to ensure the server is accessible externally
        # Set use_reloader to False since we're in a thread
        socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                    use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        raise