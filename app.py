from flask import Flask, render_template, jsonify
import logging
import os
import select
from os import O_RDONLY, O_NONBLOCK  # Add O_NONBLOCK import
from utils.audio_control import AudioController

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
audio_controller = AudioController()

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

        # Add debug information
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
                'pipe_exists': pipe_exists if 'pipe_exists' in locals() else False,
                'permissions': pipe_perms if 'pipe_perms' in locals() else 'N/A',
                'owner': pipe_owner if 'pipe_owner' in locals() else 'N/A',
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

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application on port 5001...")
        # Use 0.0.0.0 to ensure the server is accessible externally
        app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        raise