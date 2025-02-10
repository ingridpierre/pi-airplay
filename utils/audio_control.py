
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
            with open(self.metadata_pipe, 'rb') as pipe:
                data = pipe.read(4096)
                if data:
                    try:
                        # Try to decode the data as UTF-8
                        decoded = data.decode('utf-8')
                        # Look for specific metadata tags
                        artist = None
                        title = None
                        album = None
                        
                        if 'artist' in decoded:
                            artist = decoded.split('artist')[1].split('"')[2]
                        if 'title' in decoded:
                            title = decoded.split('title')[1].split('"')[2]
                        if 'album' in decoded:
                            album = decoded.split('album')[1].split('"')[2]
                            
                        if any([artist, title, album]):
                            return {
                                'artist': artist or 'Unknown Artist',
                                'title': title or 'Unknown Title',
                                'album': album or 'Unknown Album'
                            }
                    except:
                        pass
        except:
            pass
        return {
            'artist': 'No Artist',
            'title': 'Not Playing',
            'album': 'No Album'
        }
