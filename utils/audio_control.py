import subprocess
import json
import os
import re
import logging
import stat
import select
import socket
import struct
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

        # Initialize multicast socket as backup
        try:
            self._setup_multicast()
            logger.info("Multicast socket initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize multicast socket: {e}")
            self.mcast_sock = None

    def _setup_multicast(self):
        """Setup multicast socket for metadata reception"""
        self.mcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.mcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.mcast_sock.bind(('', 5555))  # Bind to port 5555
            mreq = struct.pack('4sl', socket.inet_aton('226.0.0.1'), socket.INADDR_ANY)
            self.mcast_sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            self.mcast_sock.setblocking(False)
            logger.info("Successfully joined multicast group 226.0.0.1:5555")
        except Exception as e:
            logger.error(f"Failed to setup multicast: {e}")
            raise

    def _ensure_metadata_pipe(self):
        """Ensure the metadata pipe exists with correct permissions."""
        try:
            if not os.path.exists(self.metadata_pipe):
                logger.info(f"Creating metadata pipe at {self.metadata_pipe}")
                os.mkfifo(self.metadata_pipe)
                # Set permissions to allow both shairport-sync (creator) and ivpi (reader) access
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

                # Verify pipe is actually a FIFO
                if not stat.S_ISFIFO(st.st_mode):
                    logger.error("Metadata pipe exists but is not a FIFO!")
                    os.remove(self.metadata_pipe)
                    logger.info("Removed invalid pipe, recreating...")
                    os.mkfifo(self.metadata_pipe)
                    os.chmod(self.metadata_pipe, 0o666)
                    logger.info("Recreated pipe with correct FIFO type")

        except OSError as e:
            logger.error(f"Failed to create/verify metadata pipe: {e}")
            raise

    def _check_multicast(self):
        """Check for metadata from multicast socket"""
        if not self.mcast_sock:
            return None

        try:
            ready, _, _ = select.select([self.mcast_sock], [], [], 0.1)
            if ready:
                data, _ = self.mcast_sock.recvfrom(4096)
                if data:
                    logger.debug(f"Received {len(data)} bytes from multicast")
                    return data
        except Exception as e:
            logger.error(f"Error reading from multicast: {e}")
        return None

    def _parse_metadata(self, data):
        """Parse the metadata from the pipe data with improved debugging."""
        if not data:
            logger.debug("No data to parse")
            return self.current_metadata

        try:
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')
                logger.debug(f"Decoded data length: {len(data)}")
                logger.debug(f"Sample of decoded data: {data[:200]}")

            # Look for complete items
            changes_made = False
            for item in data.split('</item>'):
                if not item or '<item>' not in item:
                    continue

                try:
                    # Extract code and data using more precise regex
                    code_match = re.search(r'<code>([^<]+)</code>', item)
                    data_match = re.search(r'<data>([^<]+)</data>', item)

                    if not code_match or not data_match:
                        continue

                    code = code_match.group(1)
                    value = data_match.group(1)

                    logger.debug(f"Found metadata item - Code: {code}, Value: {value}")

                    # Update metadata if different
                    if code == 'asar' and value != self.current_metadata['artist']:
                        logger.info(f"Updating artist: {value}")
                        self.current_metadata['artist'] = value
                        changes_made = True
                    elif code == 'minm' and value != self.current_metadata['title']:
                        logger.info(f"Updating title: {value}")
                        self.current_metadata['title'] = value
                        changes_made = True
                    elif code == 'asal' and value != self.current_metadata['album']:
                        logger.info(f"Updating album: {value}")
                        self.current_metadata['album'] = value
                        changes_made = True

                except Exception as e:
                    logger.error(f"Error parsing item: {e}")
                    continue

            if changes_made:
                logger.info(f"Metadata updated: {self.current_metadata}")
            else:
                logger.debug("No changes to metadata after parsing")

        except Exception as e:
            logger.error(f"Error in _parse_metadata: {str(e)}")

        return self.current_metadata

    def get_current_metadata(self):
        """Get the current metadata with improved error handling and logging."""
        current_time = time()

        try:
            # Check if shairport-sync is running
            result = subprocess.run(['pgrep', 'shairport-sync'], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning("shairport-sync process is not running")
                return self.current_metadata

            # Only read if enough time has passed
            if current_time - self.last_read_time < self.read_interval:
                return self.current_metadata

            # Try multicast first
            mcast_data = self._check_multicast()
            if mcast_data:
                self.last_read_time = current_time
                return self._parse_metadata(mcast_data)

            # Fall back to pipe if multicast didn't provide data
            if not os.path.exists(self.metadata_pipe):
                logger.warning("Metadata pipe not found, attempting to create...")
                self._ensure_metadata_pipe()
                return self.current_metadata

            logger.debug("Attempting to read from metadata pipe...")
            try:
                # Open pipe in non-blocking mode
                fd = os.open(self.metadata_pipe, os.O_RDONLY | os.O_NONBLOCK)
                try:
                    with os.fdopen(fd, 'rb') as pipe:
                        # Use select with a short timeout
                        ready, _, _ = select.select([pipe], [], [], 0.1)
                        if ready:
                            data = pipe.read()  # Read all available data
                            if data:
                                logger.debug(f"Read {len(data)} bytes of raw data")
                                logger.debug(f"Raw data (first 200 bytes): {data[:200]}")
                                self.last_read_time = current_time
                                return self._parse_metadata(data)
                            else:
                                logger.debug("Pipe is empty (no data available)")
                        else:
                            logger.debug("No data ready in pipe")
                finally:
                    os.close(fd)
            except Exception as e:
                logger.error(f"Error reading from pipe: {e}")
                return self.current_metadata

        except Exception as e:
            logger.error(f"Error in get_current_metadata: {e}")
            return self.current_metadata

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

            # Check if metadata is being received (either through pipe or multicast)
            current_metadata = self.get_current_metadata()
            return current_metadata['title'] != 'Not Playing'

        except Exception as e:
            logger.error(f"Error checking play status: {e}")
            return False