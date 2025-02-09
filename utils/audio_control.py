import subprocess
import json
import os

class AudioController:
    def __init__(self):
        self.current_track = None
        self.playing = False

    def is_playing(self):
        try:
            output = subprocess.check_output(['pidof', 'shairport-sync'])
            return True
        except subprocess.CalledProcessError:
            return False

    def get_current_metadata(self):
        # This would normally read from shairport-sync's metadata pipe
        # For demo purposes, returning mock data
        return {
            'artist': 'Unknown Artist',
            'title': 'Unknown Title',
            'album': 'Unknown Album',
            'artwork': None
        }
