#!/usr/bin/env python3
"""
Pi-DAD: Raspberry Pi Digital Audio Display
A simplified AirPlay receiver with music recognition capabilities.
"""

from flask import Flask, render_template, jsonify, request
import logging
import os
import threading
import time
from flask_socketio import SocketIO

# Import simplified utility classes
from utils.audio_control import AudioController
from utils.music_recognition import MusicRecognitionService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'pi-dad-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Try to load API key
api_key = None
api_key_paths = [
    '.acoustid_api_key',  # Current directory
    os.path.expanduser('~/.acoustid_api_key'),  # User's home directory
    '/etc/acoustid_api_key',  # System-wide location
    os.path.join('config', 'acoustid_api_key')  # Config directory
]

for path in api_key_paths:
    try:
        if os.path.exists(path):
            with open(path, 'r') as f:
                api_key = f.read().strip()
                if api_key:
                    logger.info(f"Loaded AcoustID API key from {path}")
                    break
    except Exception as e:
        logger.error(f"Error reading API key from {path}: {e}")

# Also check environment variable
if not api_key:
    api_key = os.environ.get('ACOUSTID_API_KEY')
    if api_key:
        logger.info("Using AcoustID API key from environment variable")

# Initialize controllers
audio_controller = AudioController()
music_recognition = MusicRecognitionService(api_key=api_key)

# Ensure artwork directory exists
os.makedirs(os.path.join('static', 'artwork'), exist_ok=True)

def metadata_update_thread():
    """Thread to send metadata updates to clients."""
    logger.info("Starting metadata update thread")
    
    # Start the music recognition service
    music_recognition.start()
    
    while True:
        try:
            # Get metadata from music recognition first
            metadata = music_recognition.get_current_metadata()
            
            # Check if AirPlay is active
            if audio_controller.is_playing():
                # AirPlay has priority, get its metadata
                airplay_metadata = audio_controller.get_current_metadata()
                
                # Only update if AirPlay is actually playing something
                if airplay_metadata.get('title') != "Not Playing":
                    metadata = airplay_metadata
                    # Add the artwork URL if not present
                    if not metadata.get('artwork'):
                        metadata['artwork'] = '/static/artwork/default_album.svg'
                    # Add background color if not present
                    if not metadata.get('background_color'):
                        metadata['background_color'] = "#121212"
            
            # Add AirPlay status
            metadata['airplay_active'] = audio_controller.is_playing()
            
            # Send metadata to clients
            socketio.emit('metadata_update', metadata)
            
        except Exception as e:
            logger.error(f"Error in metadata thread: {e}")
        
        # Sleep to avoid too frequent updates
        time.sleep(2)

# Start the metadata update thread
metadata_thread = threading.Thread(target=metadata_update_thread)
metadata_thread.daemon = True

@app.route('/')
def index():
    """Main display page."""
    logger.info("Display page requested")
    return render_template('display.html')

@app.route('/setup')
def setup():
    """Setup page for AcoustID API configuration."""
    return render_template('setup.html')

@app.route('/now-playing')
def now_playing():
    """Get current playback metadata."""
    try:
        # Get metadata from the music recognition service
        metadata = music_recognition.get_current_metadata()
        
        # Check if AirPlay is active
        if audio_controller.is_playing():
            # AirPlay has priority, get its metadata
            airplay_metadata = audio_controller.get_current_metadata()
            
            # Only update if AirPlay is actually playing something
            if airplay_metadata.get('title') != "Not Playing":
                metadata = airplay_metadata
                # Add the artwork URL if not present
                if not metadata.get('artwork'):
                    metadata['artwork'] = '/static/artwork/default_album.svg'
                # Add background color if not present
                if not metadata.get('background_color'):
                    metadata['background_color'] = "#121212"
        
        # Add AirPlay status
        metadata['airplay_active'] = audio_controller.is_playing()
        
        # Add debug info for troubleshooting
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
            'background_color': "#121212",
            '_debug': {
                'pipe_exists': False,
                'permissions': 'N/A',
                'owner': 'N/A',
                'shairport_running': False,
                'last_error': error_msg
            }
        })

@app.route('/test-recognition')
def test_recognition():
    """
    Test route to simulate music recognition without microphone.
    Useful for testing in environments without audio input.
    """
    try:
        logger.info("Simulating music recognition...")
        music_recognition.trigger_simulation()
        return jsonify({
            "status": "success",
            "message": "Simulation triggered. Check the display for recognized music."
        })
    except Exception as e:
        logger.error(f"Error in simulation mode: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api-key', methods=['POST'])
def set_api_key():
    """Set the AcoustID API key."""
    try:
        data = request.get_json()
        if not data or 'api_key' not in data:
            return jsonify({"status": "error", "message": "No API key provided"}), 400
            
        api_key = data['api_key']
        
        # Save API key to environment variable
        os.environ['ACOUSTID_API_KEY'] = api_key
        
        # Save to file for persistence
        with open('.acoustid_api_key', 'w') as f:
            f.write(api_key)
        
        # Update the music recognition service
        music_recognition.api_key = api_key
        
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
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Pi-DAD: Raspberry Pi Digital Audio Display')
    parser.add_argument('--port', type=int, default=5000, help='Port to run the web server on (default: 5000)')
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting Flask application on port {args.port}...")
        
        # Start the metadata update thread
        metadata_thread.start()
        
        # Use 0.0.0.0 to ensure the server is accessible externally
        # Set use_reloader to False since we're in a thread
        socketio.run(app, host='0.0.0.0', port=args.port, debug=True, 
                    use_reloader=False, log_output=True, allow_unsafe_werkzeug=True)
                    
    except Exception as e:
        logger.error(f"Failed to start Pi-DAD: {e}")
        raise