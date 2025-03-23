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
import binascii
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
            # Get current metadata from audio controller
            airplay_metadata = audio_controller.get_current_metadata()
            
            # Default metadata structure
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
                    
            # Check for shairport-sync process
            shairport_running = bool(os.popen('pgrep shairport-sync').read().strip())
            
            metadata['_debug'] = {
                'pipe_exists': pipe_exists,
                'permissions': pipe_perms,
                'owner': pipe_owner,
                'shairport_running': shairport_running,
                'airplay_active': audio_controller.is_playing(),
                'last_error': None
            }
            
            # Send metadata to clients
            socketio.emit('metadata_update', metadata)
            
        except Exception as e:
            logger.error(f"Error in metadata thread: {e}")
        
        # Sleep to avoid too frequent updates
        time.sleep(1)

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
        # Get current metadata from audio controller
        airplay_metadata = audio_controller.get_current_metadata()
        
        # Default metadata structure
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
                
        # Check for shairport-sync process
        shairport_running = bool(os.popen('pgrep shairport-sync').read().strip())
        
        metadata['_debug'] = {
            'pipe_exists': pipe_exists,
            'permissions': pipe_perms,
            'owner': pipe_owner,
            'shairport_running': shairport_running,
            'airplay_active': audio_controller.is_playing(),
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

@app.route('/debug')
def debug_interface():
    """Debug interface for troubleshooting issues."""
    logger.info("Debug page requested")
    
    # Get raw system info
    system_info = {
        'hostname': os.popen('hostname').read().strip(),
        'os_info': os.popen('cat /etc/os-release 2>/dev/null || echo "OS info not available"').read().strip(),
        'uptime': os.popen('uptime').read().strip(),
        'date': os.popen('date').read().strip()
    }
    
    # Get shairport-sync info
    shairport_info = {
        'installed': bool(os.popen('command -v shairport-sync').read().strip()),
        'version': os.popen('shairport-sync -V 2>/dev/null || echo "Not installed"').read().strip(),
        'running': bool(os.popen('pgrep shairport-sync').read().strip()),
        'processes': os.popen('ps aux | grep shairport-sync | grep -v grep').read().strip(),
        'config_exists': os.path.exists('/usr/local/etc/shairport-sync.conf'),
        'config_sample': os.popen('cat /usr/local/etc/shairport-sync.conf 2>/dev/null | head -n 20 || echo "Config not found"').read().strip()
    }
    
    # Get audio info
    audio_info = {
        'devices': os.popen('aplay -l 2>/dev/null || echo "Command not available"').read().strip(),
        'cards': os.popen('cat /proc/asound/cards 2>/dev/null || echo "No audio cards info available"').read().strip()
    }
    
    # Get metadata pipe info
    pipe_path = '/tmp/shairport-sync-metadata'
    pipe_info = {
        'exists': os.path.exists(pipe_path),
        'permissions': 'N/A',
        'owner': 'N/A',
        'type': 'N/A',
        'last_read_attempt': audio_controller.last_pipe_read_time,
        'last_read_success': audio_controller.last_pipe_data_time
    }
    
    if pipe_info['exists']:
        try:
            import stat as stat_module
            file_stat = os.stat(pipe_path)
            pipe_info['permissions'] = oct(file_stat.st_mode)
            pipe_info['owner'] = f"{file_stat.st_uid}:{file_stat.st_gid}"
            pipe_info['type'] = 'FIFO' if stat_module.S_ISFIFO(file_stat.st_mode) else 'Regular file'
        except OSError as e:
            pipe_info['error'] = str(e)
    
    # Get network info
    network_info = {
        'interfaces': os.popen('ip addr show 2>/dev/null || ifconfig 2>/dev/null || echo "Network info not available"').read().strip(),
        'listening_ports': os.popen('netstat -tuln 2>/dev/null || echo "Port info not available"').read().strip(),
        'airplay_port': os.popen('netstat -tuln | grep ":5000" 2>/dev/null || echo "Not found"').read().strip()
    }
    
    # Get AirPlay metadata state
    metadata_state = audio_controller.get_current_metadata()
    
    # Add internal debug counters
    debug_counters = {
        'read_attempts': audio_controller.debug_counters.get('read_attempts', 0),
        'successful_reads': audio_controller.debug_counters.get('successful_reads', 0),
        'parse_errors': audio_controller.debug_counters.get('parse_errors', 0),
        'process_errors': audio_controller.debug_counters.get('process_errors', 0),
        'metadata_updates': audio_controller.debug_counters.get('metadata_updates', 0)
    }
    
    # Add last error
    last_error = audio_controller.last_error or "No errors reported"
    
    return render_template('debug.html', 
                          system_info=system_info,
                          shairport_info=shairport_info,
                          audio_info=audio_info,
                          pipe_info=pipe_info,
                          network_info=network_info,
                          metadata_state=metadata_state,
                          debug_counters=debug_counters,
                          last_error=last_error)

@app.route('/raw-pipe-data')
def raw_pipe_data():
    """View raw data from the metadata pipe."""
    pipe_path = '/tmp/shairport-sync-metadata'
    
    if not os.path.exists(pipe_path):
        return jsonify({
            'error': 'Metadata pipe does not exist',
            'path': pipe_path
        })
    
    # Attempt to read from the pipe in a non-blocking way
    try:
        import time
        result = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'pipe_exists': True,
            'raw_chunks': []
        }
        
        # Use the raw pipe reader from audio_controller
        raw_data = audio_controller.read_raw_pipe_data(max_chunks=10)
        
        if raw_data:
            for chunk in raw_data:
                # Convert binary data to hex for display
                result['raw_chunks'].append({
                    'hex': binascii.hexlify(chunk).decode('utf-8'),
                    'ascii': ''.join(c if 32 <= ord(c) < 127 else '.' for c in chunk.decode('utf-8', errors='replace'))
                })
        else:
            result['message'] = 'No data available in pipe (empty or blocked read)'
        
        return jsonify(result)
    except Exception as e:
        return jsonify({
            'error': str(e),
            'path': pipe_path
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
    parser.add_argument('--host', type=str, default='0.0.0.0', help='Host address to bind to (default: 0.0.0.0)')
    args = parser.parse_args()
    
    try:
        logger.info(f"Starting Pi-AirPlay on {args.host}:{args.port}...")
        
        # Start the metadata update thread
        metadata_thread.start()
        
        # Use host from args (default 0.0.0.0) to ensure the server is accessible externally
        # Set debug=False to avoid common issues with Flask debugging
        socketio.run(app, host=args.host, port=args.port, debug=False, 
                    use_reloader=False, log_output=True)
                    
    except Exception as e:
        logger.error(f"Failed to start Pi-AirPlay: {e}")
        raise