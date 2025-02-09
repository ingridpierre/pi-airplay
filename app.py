from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json
import os
import subprocess
from utils.audio_control import AudioController

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
socketio = SocketIO(app)

audio_controller = AudioController()

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    print('Client connected')
    # Send initial state
    emit('playback_state', {'playing': audio_controller.is_playing()})

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

def handle_metadata_change(metadata):
    socketio.emit('metadata_update', metadata)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
