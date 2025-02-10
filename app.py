from flask import Flask, render_template, jsonify
import logging
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

from utils.audio_control import AudioController

audio_controller = AudioController()

@app.route('/now-playing')
def now_playing():
    try:
        # Check metadata pipe existence and permissions
        pipe_path = '/tmp/shairport-sync-metadata'
        debug_info = {
            'pipe_exists': os.path.exists(pipe_path),
            'permissions': oct(os.stat(pipe_path).st_mode)[-3:] if os.path.exists(pipe_path) else 'N/A',
            'last_error': None
        }

        metadata = audio_controller.get_current_metadata()
        metadata['_debug'] = debug_info
        logger.debug(f"Returning metadata: {metadata}")
        return jsonify(metadata)
    except Exception as e:
        logger.error(f"Error in now_playing endpoint: {e}")
        return jsonify({
            'artist': 'Error',
            'title': 'Cannot get metadata',
            'album': 'Please check logs'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)