"""
Improved audio control module for shairport-sync metadata - based on shairport-decoder.
"""

import os
import logging
import time
import base64
import io
import select
import binascii
import threading
import struct
import json
from pathlib import Path
from PIL import Image, ImageDraw
from colorthief import ColorThief

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Airplay metadata codes
CODE_ALBUM_NAME = 'asal'
CODE_ARTIST = 'asar'
CODE_TITLE = 'minm'
CODE_ARTWORK = 'PICT'
CODE_VOLUME = 'pvol'
CODE_PROGRESS = 'prgr'
CODE_DACP_ID = 'daid'
CODE_ACTIVE_REMOTE = 'acre'
CODE_CLIENT_IP = 'clip'

class AudioController:
    def __init__(self, pipe_path='/tmp/shairport-sync-metadata'):
        """
        Initialize the audio controller.
        
        Args:
            pipe_path: Path to the shairport-sync metadata pipe
        """
        self.pipe_path = pipe_path
        self.pipe_fd = None
        self.running = True
        self.metadata_lock = threading.Lock()
        self.current_metadata = {
            'title': "Not Playing",
            'artist': None,
            'album': None,
            'artwork': None,
            'background_color': "#121212",  # Default dark background
            'volume': 0,
            'progress': None
        }
        self.last_activity_time = 0
        self.artwork_path = Path('static/artwork/current_album.jpg')
        self.artwork_default = '/static/artwork/default_album.svg'
        
        # Ensure the artwork directory exists
        os.makedirs(os.path.dirname(self.artwork_path), exist_ok=True)
        
        # Ensure the pipe exists with proper permissions
        self._ensure_metadata_pipe()
        
        # Start the metadata reader thread
        self.reader_thread = threading.Thread(target=self._metadata_reader_thread)
        self.reader_thread.daemon = True
        self.reader_thread.start()
        
        logger.info("AudioController initialized and metadata reader thread started")

    def _ensure_metadata_pipe(self):
        """Ensure the metadata pipe exists with correct permissions."""
        try:
            if not os.path.exists(self.pipe_path):
                logger.info(f"Creating metadata pipe at {self.pipe_path}")
                try:
                    os.mkfifo(self.pipe_path)
                except PermissionError:
                    logger.warning(f"Permission denied. Run with sudo to create {self.pipe_path}")
                    return
                
            # Set permissions to be readable by all users
            os.chmod(self.pipe_path, 0o666)
            logger.info(f"Metadata pipe setup complete: {self.pipe_path}")
        except Exception as e:
            logger.error(f"Error setting up metadata pipe: {e}")

    def _extract_dominant_color(self, artwork_data):
        """
        Extract the dominant color from the artwork for background color.
        """
        try:
            image = Image.open(io.BytesIO(artwork_data))
            # Save temporary file for ColorThief
            temp_path = 'static/artwork/temp_cover.jpg'
            image.save(temp_path)
            color_thief = ColorThief(temp_path)
            dominant_color = color_thief.get_color(quality=1)
            # Convert RGB to hex
            hex_color = '#{:02x}{:02x}{:02x}'.format(*dominant_color)
            return hex_color
        except Exception as e:
            logger.error(f"Error extracting dominant color: {e}")
            return "#121212"  # Default dark background

    def _metadata_reader_thread(self):
        """Thread for continuous reading of the metadata pipe."""
        logger.info("Starting metadata reader thread")
        
        while self.running:
            try:
                if not os.path.exists(self.pipe_path):
                    logger.warning(f"Metadata pipe does not exist: {self.pipe_path}")
                    time.sleep(5)
                    continue
                
                # Open the pipe in non-blocking mode
                if self.pipe_fd is None:
                    try:
                        # Try to import fcntl for non-blocking mode
                        import fcntl
                        self.pipe_fd = os.open(self.pipe_path, os.O_RDONLY)
                        fcntl.fcntl(self.pipe_fd, fcntl.F_SETFL, os.O_NONBLOCK)
                    except (ImportError, AttributeError):
                        # Fallback if fcntl is not available or O_NONBLOCK is not defined
                        self.pipe_fd = os.open(self.pipe_path, os.O_RDONLY)
                    logger.info(f"Opened metadata pipe: {self.pipe_path}")
                
                # Use select to check if data is available
                readable, _, _ = select.select([self.pipe_fd], [], [], 1.0)
                if self.pipe_fd in readable:
                    # Data is available to read
                    data = os.read(self.pipe_fd, 4)  # Read header (4 bytes)
                    if not data:
                        # Pipe was closed, reopen it
                        os.close(self.pipe_fd)
                        self.pipe_fd = None
                        continue
                    
                    # Parse the header
                    if len(data) == 4:
                        # Extract tag and length from header
                        item_type, item_code, item_length = struct.unpack('>BBH', data)
                        
                        # Read the actual data
                        item_data = b''
                        while len(item_data) < item_length:
                            chunk = os.read(self.pipe_fd, item_length - len(item_data))
                            if not chunk:  # End of file or error
                                break
                            item_data += chunk
                        
                        # Process the data
                        self._process_metadata_item(item_type, item_code, item_data)
                else:
                    # No data available
                    time.sleep(0.1)
                    
            except Exception as e:
                logger.error(f"Error in metadata reader thread: {e}")
                # Close and reopen the pipe on error
                if self.pipe_fd is not None:
                    try:
                        os.close(self.pipe_fd)
                    except:
                        pass
                    self.pipe_fd = None
                time.sleep(5)
        
        # Cleanup on thread exit
        if self.pipe_fd is not None:
            try:
                os.close(self.pipe_fd)
            except:
                pass
            self.pipe_fd = None

    def _process_metadata_item(self, item_type, item_code, item_data):
        """Process a single metadata item from the pipe."""
        try:
            # Convert code to 4-char string for easier comparison
            code = struct.pack('>I', item_code).decode('utf-8', errors='ignore').strip('\0')
            
            # Update the last activity time
            self.last_activity_time = time.time()
            
            with self.metadata_lock:
                if code == CODE_ARTWORK:
                    # Handle artwork (binary data)
                    try:
                        # Save the artwork to disk
                        with open(self.artwork_path, 'wb') as f:
                            f.write(item_data)
                        
                        # Set the artwork URL
                        self.current_metadata['artwork'] = str(self.artwork_path).replace('\\', '/')
                        
                        # Extract the dominant color for background
                        bg_color = self._extract_dominant_color(item_data)
                        self.current_metadata['background_color'] = bg_color
                        
                        logger.info(f"Updated artwork and background color: {bg_color}")
                    except Exception as e:
                        logger.error(f"Error processing artwork: {e}")
                        # Use default artwork on error
                        self.current_metadata['artwork'] = self.artwork_default
                
                elif code == CODE_TITLE:
                    # Handle track title (text data)
                    title = item_data.decode('utf-8', errors='ignore')
                    if title:
                        self.current_metadata['title'] = title
                        logger.info(f"Updated title: {title}")
                
                elif code == CODE_ARTIST:
                    # Handle artist (text data)
                    artist = item_data.decode('utf-8', errors='ignore')
                    if artist:
                        self.current_metadata['artist'] = artist
                        logger.info(f"Updated artist: {artist}")
                
                elif code == CODE_ALBUM_NAME:
                    # Handle album name (text data)
                    album = item_data.decode('utf-8', errors='ignore')
                    if album:
                        self.current_metadata['album'] = album
                        logger.info(f"Updated album: {album}")
                
                elif code == CODE_VOLUME:
                    # Handle volume data
                    if len(item_data) >= 4:
                        # First byte is the denominator, rest is numerator
                        denominator = item_data[0]
                        numerator = int.from_bytes(item_data[1:4], byteorder='big')
                        if denominator > 0:
                            volume = (numerator * 100) // (denominator * 0x1000000)
                            self.current_metadata['volume'] = volume
                            logger.debug(f"Updated volume: {volume}%")
                
                elif code == CODE_PROGRESS:
                    # Handle progress data
                    if len(item_data) >= 16:
                        start = int.from_bytes(item_data[0:4], byteorder='big')
                        current = int.from_bytes(item_data[4:8], byteorder='big')
                        end = int.from_bytes(item_data[8:12], byteorder='big')
                        if end > 0:
                            progress = (current - start) / (end - start)
                            self.current_metadata['progress'] = progress
                            logger.debug(f"Updated progress: {progress:.2f}")
                
        except Exception as e:
            logger.error(f"Error processing metadata item: {e}")

    def get_current_metadata(self):
        """Get the current metadata with improved error handling and responsiveness."""
        with self.metadata_lock:
            # Create a copy to avoid modification during return
            metadata = self.current_metadata.copy()
            
            # Check if playback is active
            if self.is_playing():
                # Add default artwork if missing
                if not metadata.get('artwork'):
                    metadata['artwork'] = self.artwork_default
                # Add background color if missing
                if not metadata.get('background_color'):
                    metadata['background_color'] = "#121212"
            else:
                # Default "not playing" metadata
                metadata = {
                    'title': "Not Playing",
                    'artist': None,
                    'album': None,
                    'artwork': self.artwork_default,
                    'background_color': "#121212",
                    'volume': 0,
                    'progress': None
                }
        
        return metadata

    def is_playing(self):
        """Check if shairport-sync is actively streaming."""
        # Check if the shairport-sync process is running and activity is recent
        try:
            # Look for the shairport-sync process
            with os.popen('pgrep shairport-sync') as proc:
                if not proc.read().strip():
                    return False
            
            # Check for recent metadata activity
            current_time = time.time()
            if current_time - self.last_activity_time > 30:  # 30 seconds of inactivity
                return False
            
            # Check if we have meaningful metadata
            with self.metadata_lock:
                if (self.current_metadata.get('title') == "Not Playing" or
                    (self.current_metadata.get('artist') is None and 
                     self.current_metadata.get('album') is None)):
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking playback status: {e}")
            return False