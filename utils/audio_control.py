import subprocess
import json
import os
import re
import logging
import stat
import select

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AudioController:
    def __init__(self):
        self.metadata_pipe = '/tmp/shairport-sync-metadata'
        self._ensure_metadata_pipe()
        self.current_metadata = {
            'artist': 'No Artist',
            'title': 'Not Playing',
            'album': 'No Album'
        }

    def _ensure_metadata_pipe(self):
        if not os.path.exists(self.metadata_pipe):
            try:
                os.mkfifo(self.metadata_pipe)
                os.chmod(self.metadata_pipe, stat.S_IRUSR | stat.S_IWUSR | 
                                          stat.S_IRGRP | stat.S_IWGRP |
                                          stat.S_IROTH | stat.S_IWOTH)
                logger.info(f"Created metadata pipe at {self.metadata_pipe}")
            except OSError as e:
                logger.error(f"Failed to create metadata pipe: {e}")

    def _parse_metadata(self, data):
        if isinstance(data, bytes):
            data = data.decode('utf-8', errors='ignore')

        metadata = {}
        for item in data.split('</item>'):
            if 'asar' in item and '<data>' in item:
                metadata['artist'] = item.split('<data>')[1].split('</data>')[0]
            elif 'minm' in item and '<data>' in item:
                metadata['title'] = item.split('<data>')[1].split('</data>')[0]
            elif 'asal' in item and '<data>' in item:
                metadata['album'] = item.split('<data>')[1].split('</data>')[0]

        if metadata:
            self.current_metadata.update(metadata)
            logger.debug(f"Updated metadata: {self.current_metadata}")

        return self.current_metadata

    def get_current_metadata(self):
        try:
            if not os.path.exists(self.metadata_pipe):
                return self.current_metadata

            with open(self.metadata_pipe, 'rb') as pipe:
                ready, _, _ = select.select([pipe], [], [], 0.5)
                if ready:
                    data = pipe.read(4096)
                    if data:
                        return self._parse_metadata(data)
        except Exception as e:
            logger.error(f"Error reading metadata: {e}")

        return self.current_metadata

    def is_playing(self):
        try:
            subprocess.check_output(['pidof', 'shairport-sync'])
            return True
        except subprocess.CalledProcessError:
            logger.debug("shairport-sync process not found")
            return False