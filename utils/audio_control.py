import subprocess
import json
import os
import re
import logging
import stat
import select
from time import time

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        self.last_read_time = 0
        self.read_interval = 0.5  # Reduced interval for more responsive updates

    def _ensure_metadata_pipe(self):
        """Ensure the metadata pipe exists with correct permissions."""
        try:
            if not os.path.exists(self.metadata_pipe):
                logger.info(f"Creating metadata pipe at {self.metadata_pipe}")
                os.mkfifo(self.metadata_pipe)
                os.chmod(self.metadata_pipe, 
                        stat.S_IRUSR | stat.S_IWUSR | 
                        stat.S_IRGRP | stat.S_IWGRP |
                        stat.S_IROTH | stat.S_IWOTH)
            else:
                logger.info(f"Metadata pipe already exists at {self.metadata_pipe}")
        except OSError as e:
            logger.error(f"Failed to create/verify metadata pipe: {e}")
            raise

    def _parse_metadata(self, data):
        """Parse the metadata from the pipe data with improved error handling."""
        if not data:
            return self.current_metadata

        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')

            changes_made = False
            for item in data.split('</item>'):
                if '<code>' not in item or '<data>' not in item:
                    continue

                code = re.search(r'<code>([^<]+)</code>', item)
                if not code:
                    continue

                code = code.group(1)
                data_match = re.search(r'<data>([^<]+)</data>', item)

                if not data_match:
                    continue

                value = data_match.group(1)

                if code == 'asar' and value != self.current_metadata['artist']:
                    self.current_metadata['artist'] = value
                    changes_made = True
                elif code == 'minm' and value != self.current_metadata['title']:
                    self.current_metadata['title'] = value
                    changes_made = True
                elif code == 'asal' and value != self.current_metadata['album']:
                    self.current_metadata['album'] = value
                    changes_made = True

            if changes_made:
                logger.info(f"Updated metadata: {self.current_metadata}")

        except Exception as e:
            logger.error(f"Error parsing metadata item: {e}")

        return self.current_metadata

    def get_current_metadata(self):
        """Get the current metadata with improved error handling and responsiveness."""
        current_time = time()

        if current_time - self.last_read_time < self.read_interval:
            return self.current_metadata

        try:
            if not os.path.exists(self.metadata_pipe):
                logger.warning("Metadata pipe not found, ensuring it exists...")
                self._ensure_metadata_pipe()
                return self.current_metadata

            fd = os.open(self.metadata_pipe, os.O_RDONLY | os.O_NONBLOCK)
            with os.fdopen(fd, 'rb') as pipe:
                ready, _, _ = select.select([pipe], [], [], 0.1)
                if ready:
                    data = pipe.read(4096)
                    if data:
                        self.last_read_time = current_time
                        return self._parse_metadata(data)

        except Exception as e:
            logger.error(f"Error reading metadata: {e}")

        return self.current_metadata

    def is_playing(self):
        """Check if shairport-sync is actively streaming."""
        try:
            # Check if the pipe is being written to
            if not os.path.exists(self.metadata_pipe):
                return False

            # Check if shairport-sync process is running
            result = subprocess.run(['pgrep', 'shairport-sync'], capture_output=True, text=True)
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Error checking play status: {e}")
            return False