#!/usr/bin/env python3
"""
Pi-AirPlay: Raspberry Pi AirPlay Receiver
A streamlined AirPlay receiver for Raspberry Pi with IQaudio DAC.
"""

from flask import Flask, render_template, jsonify
import logging
import os
import threading
import time
from flask_socketio import SocketIO

# Import only the audio controller for AirPlay
from utils.audio_control import AudioController

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
app.config['SECRET_KEY'] = 'pi-airplay-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize audio controller
audio_controller = AudioController()

# Ensure artwork directory exists
os.makedirs(os.path.join('static', 'artwork'), exist_ok=True)

def metadata_update_thread():
    """Thread to send metadata updates to clients."""
    logger.info("Starting metadata update thread")
    
    while True:
        try:
            # Default metadata when nothing is playing
            metadata = {
                'title': 'Waiting for music...',
                'artist': 'Connect via AirPlay to start streaming',
                'album': None,
                'artwork': '/static/artwork/default_album.svg',
                'background_color': "#121212",
                'airplay_active': False
            }
            
            # Check if AirPlay is active
            if audio_controller.is_playing():
                # AirPlay is active, get its metadata
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
                    # Set AirPlay active flag
                    metadata['airplay_active'] = True
            
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
            
            # Send metadata to clients
            socketio.emit('metadata_update', metadata)
            
        except Exception as e:
            logger.error(f"Error in metadata thread: {e}")
        
        # Sleep to avoid too frequent updates
        time.sleep(5)

# Start the metadata update thread
metadata_thread = threading.Thread(target=metadata_update_thread)
metadata_thread.daemon = True

@app.route('/')
def index():
    """Main display page."""
    logger.info("Display page requested")
    return render_template('display.html')

@app.route('/now-playing')
def now_playing():
    """Get current playback metadata."""
    try:
        # Default metadata
        metadata = {
            'title': 'Waiting for music...',
            'artist': 'Connect via AirPlay to start streaming',
            'album': None,
            'artwork': '/static/artwork/default_album.svg',
            'background_color': "#121212",
            'airplay_active': False
        }
        
        # Check if AirPlay is active
        if audio_controller.is_playing():
            # Get AirPlay metadata
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
                # Set AirPlay active flag
                metadata['airplay_active'] = True
        
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

@socketio.on('connect')
def handle_connect():
    logger.info("Client connected")

@socketio.on('disconnect')
def handle_disconnect():
    logger.info("Client disconnected")

if __name__ == '__main__':
    import argparse
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description='Pi-AirPlay: Raspberry Pi AirPlay Receiver')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the web server on (default: 8080)')
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting Pi-AirPlay on port {args.port}...")
        
        # Start the metadata update thread
        metadata_thread.start()
        
        # Use 0.0.0.0 to ensure the server is accessible externally
        # Set debug=False to avoid common issues with Flask debugging
        socketio.run(app, host='0.0.0.0', port=args.port, debug=False, 
                    use_reloader=False, log_output=True)
                    
    except Exception as e:
        logger.error(f"Failed to start Pi-AirPlay: {e}")
        raise