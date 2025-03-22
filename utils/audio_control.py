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
        logger.info(f"Initializing AudioController with pipe: {self.metadata_pipe}")
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
                logger.info("Successfully created metadata pipe with permissions 666")
            else:
                # Log existing pipe details
                st = os.stat(self.metadata_pipe)
                logger.info(f"Metadata pipe exists with permissions: {oct(st.st_mode)[-3:]}")
                logger.info(f"Pipe owner: {st.st_uid}:{st.st_gid}")
        except OSError as e:
            logger.error(f"Failed to create/verify metadata pipe: {e}")
            raise

    def _parse_metadata(self, data):
        """Parse the metadata from the pipe data with improved error handling."""
        if not data:
            logger.debug("No data received from pipe")
            return self.current_metadata

        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')
                logger.debug(f"Raw metadata received: {data[:200]}...")

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
                logger.debug(f"Parsed metadata item - Code: {code}, Value: {value}")

                # Enhanced metadata mapping
                metadata_map = {
                    'asar': ('artist', str),
                    'minm': ('title', str),
                    'asal': ('album', str),
                    'pvol': ('volume', float),
                    'caps': ('play_status', str),
                    'pfls': ('shuffle', bool),
                    'prgr': ('progress', str),
                    'dacp': ('dacp_id', str)
                }

                if code in metadata_map:
                    field, type_conv = metadata_map[code]
                    try:
                        new_value = type_conv(value)
                        if self.current_metadata.get(field) != new_value:
                            self.current_metadata[field] = new_value
                            changes_made = True
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Failed to convert {code} value: {e}")

            if changes_made:
                logger.info(f"Updated metadata: {self.current_metadata}")
            else:
                logger.debug("No changes to metadata")

        except Exception as e:
            logger.error(f"Error parsing metadata item: {e}")

        return self.current_metadata

    def get_current_metadata(self):
        """Get the current metadata with improved error handling and responsiveness."""
        current_time = time()

        if current_time - self.last_read_time < self.read_interval:
            return self.current_metadata

        try:
            # Check if shairport-sync is running
            result = subprocess.run(['pgrep', 'shairport-sync'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("shairport-sync process is not running")
                return self.current_metadata

            if not os.path.exists(self.metadata_pipe):
                logger.warning("Metadata pipe not found, ensuring it exists...")
                self._ensure_metadata_pipe()
                return self.current_metadata

            logger.debug("Attempting to read from metadata pipe...")
            fd = os.open(self.metadata_pipe, os.O_RDONLY | os.O_NONBLOCK)
            with os.fdopen(fd, 'rb') as pipe:
                ready, _, _ = select.select([pipe], [], [], 0.1)
                if ready:
                    data = pipe.read(4096)
                    if data:
                        logger.debug(f"Read {len(data)} bytes from pipe")
                        self.last_read_time = current_time
                        return self._parse_metadata(data)
                    else:
                        logger.debug("No data available in pipe")
                else:
                    logger.debug("No data ready to read from pipe")

        except Exception as e:
            logger.error(f"Error reading metadata: {e}")

        return self.current_metadata

    def is_playing(self):
        """Check if shairport-sync is actively streaming."""
        try:
            # Check if shairport-sync process is running
            result = subprocess.run(['pgrep', 'shairport-sync'], capture_output=True, text=True)
            is_running = result.returncode == 0
            logger.debug(f"shairport-sync process running: {is_running}")

            if not is_running:
                return False

            # Check if the pipe exists and is readable
            if not os.path.exists(self.metadata_pipe):
                logger.debug("Metadata pipe does not exist")
                return False

            return True

        except Exception as e:
            logger.error(f"Error checking play status: {e}")
            return False