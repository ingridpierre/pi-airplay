from flask import Flask, render_template, jsonify
import logging
import os
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

        if pipe_exists:
            try:
                pipe_perms = oct(os.stat(pipe_path).st_mode)[-3:]
                logger.info(f"Metadata pipe exists with permissions: {pipe_perms}")
            except OSError as e:
                logger.error(f"Error checking pipe permissions: {e}")

        # Get metadata from controller
        metadata = audio_controller.get_current_metadata()
        logger.debug(f"Retrieved metadata: {metadata}")

        # Add debug information
        metadata['_debug'] = {
            'pipe_exists': pipe_exists,
            'permissions': pipe_perms,
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
                'last_error': error_msg
            }
        })

if __name__ == '__main__':
    try:
        logger.info("Starting Flask application on port 5001...")
        # Use 0.0.0.0 to ensure the server is accessible externally
        app.run(host='0.0.0.0', port=5001, debug=True)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        raise