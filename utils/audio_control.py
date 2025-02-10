
import subprocess
import json
import os

class AudioController:
    def __init__(self):
        self.metadata_pipe = '/tmp/shairport-sync-metadata'
        self._ensure_metadata_pipe()

    def _ensure_metadata_pipe(self):
        if not os.path.exists(self.metadata_pipe):
            try:
                os.mkfifo(self.metadata_pipe)
            except OSError:
                pass

    def is_playing(self):
        try:
            output = subprocess.check_output(['pidof', 'shairport-sync'])
            return True
        except subprocess.CalledProcessError:
            return False

    def get_current_metadata(self):
        try:
            with open(self.metadata_pipe, 'r') as pipe:
                data = pipe.read()
                if data:
                    return {
                        'artist': data.get('artist', 'Unknown Artist'),
                        'title': data.get('title', 'Unknown Title'),
                        'album': data.get('album', 'Unknown Album')
                    }
        except:
            pass
        return {
            'artist': 'No Artist',
            'title': 'Not Playing',
            'album': 'No Album'
        }
