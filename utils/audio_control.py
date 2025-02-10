import subprocess
import json
import os
import re
import logging
import stat

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
                # Ensure the pipe has correct permissions (666)
                os.chmod(self.metadata_pipe, stat.S_IRUSR | stat.S_IWUSR | 
                                          stat.S_IRGRP | stat.S_IWGRP |
                                          stat.S_IROTH | stat.S_IWOTH)
                logger.info(f"Created metadata pipe at {self.metadata_pipe}")
            except OSError as e:
                logger.error(f"Failed to create metadata pipe: {e}")
                pass
        else:
            logger.info(f"Metadata pipe already exists at {self.metadata_pipe}")
            # Log current permissions
            try:
                perms = oct(os.stat(self.metadata_pipe).st_mode)[-3:]
                logger.info(f"Current pipe permissions: {perms}")
            except Exception as e:
                logger.error(f"Failed to check pipe permissions: {e}")

    def _parse_metadata(self, data):
        try:
            # Convert bytes to string if needed
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')

            logger.debug(f"Parsing metadata: {data[:200]}...")  # Log first 200 chars

            # Regular expressions for metadata extraction
            patterns = {
                'artist': r'<item><type>666d6572</type><code>asar</code><length>\d+</length><data>(.*?)</data></item>',
                'title': r'<item><type>666d6574</type><code>minm</code><length>\d+</length><data>(.*?)</data></item>',
                'album': r'<item><type>666d6572</type><code>asal</code><length>\d+</length><data>(.*?)</data></item>'
            }

            # Extract metadata using regex patterns
            metadata = {}
            for key, pattern in patterns.items():
                match = re.search(pattern, data)
                if match:
                    metadata[key] = match.group(1)
                    logger.debug(f"Found {key}: {metadata[key]}")
                else:
                    logger.debug(f"No match found for {key}")

            # Update only if we found any valid metadata
            if metadata:
                self.current_metadata.update({
                    k: metadata.get(k, self.current_metadata[k])
                    for k in ['artist', 'title', 'album']
                })
                logger.info(f"Updated metadata: {self.current_metadata}")
            else:
                logger.debug("No metadata found in current data")

            return self.current_metadata

        except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
            return self.current_metadata

    def is_playing(self):
        try:
            subprocess.check_output(['pidof', 'shairport-sync'])
            return True
        except subprocess.CalledProcessError:
            logger.debug("shairport-sync process not found")
            return False

    def get_current_metadata(self):
        try:
            if not os.path.exists(self.metadata_pipe):
                logger.error(f"Metadata pipe not found at {self.metadata_pipe}")
                return self.current_metadata

            # Open pipe in non-blocking mode
            import fcntl
            fd = os.open(self.metadata_pipe, os.O_RDONLY | os.O_NONBLOCK)
            try:
                data = os.read(fd, 4096)
                if data:
                    return self._parse_metadata(data)
                else:
                    logger.debug("No data available in pipe")
            except BlockingIOError:
                logger.debug("No new metadata available")
            except Exception as e:
                logger.error(f"Error reading metadata pipe: {e}")
            finally:
                os.close(fd)

        except Exception as e:
            logger.error(f"Error in get_current_metadata: {e}")

        return self.current_metadata