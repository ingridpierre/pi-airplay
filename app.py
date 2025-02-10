from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

from utils.audio_control import AudioController

audio_controller = AudioController()

@app.route('/now-playing')
def now_playing():
    return jsonify(audio_controller.get_current_metadata())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)