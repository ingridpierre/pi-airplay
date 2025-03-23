"""
Improved audio control module for shairport-sync metadata - based on shairport-decoder.
This version adds enhanced debugging, raw data access, and improved metadata parsing.
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
from datetime import datetime
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

# Item types from shairport-sync
ITEM_TYPE_METADATA = 1       # Core
ITEM_TYPE_PLAYBACK_STATUS = 2  # Play status and track info
ITEM_TYPE_ARTWORK = 3          # Album artwork

# Debug codes - needed to match with app.py
DEBUG_CODE_READ_ATTEMPT = 'read_attempts'
DEBUG_CODE_READ_SUCCESS = 'successful_reads'
DEBUG_CODE_PARSE_ERROR = 'parse_errors'
DEBUG_CODE_PROCESS_ERROR = 'process_errors'
DEBUG_CODE_METADATA_UPDATE = 'metadata_updates'

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
        self.artwork_default = '/static/artwork/default_album.jpg'
        
        # Debug tracking
        self.last_pipe_read_time = None
        self.last_pipe_data_time = None
        self.debug_counters = {
            DEBUG_CODE_READ_ATTEMPT: 0,
            DEBUG_CODE_READ_SUCCESS: 0,
            DEBUG_CODE_PARSE_ERROR: 0,
            DEBUG_CODE_PROCESS_ERROR: 0,
            DEBUG_CODE_METADATA_UPDATE: 0
        }
        self.last_error = None
        
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
        Extract the dominant color from the artwork for background color
        with enhanced visual impact.
        """
        try:
            image = Image.open(io.BytesIO(artwork_data))
            # Save temporary file for ColorThief
            temp_path = 'static/artwork/temp_cover.jpg'
            image.save(temp_path)
            color_thief = ColorThief(temp_path)
            
            # Get a larger palette for more color options
            palette = color_thief.get_palette(color_count=6, quality=1)
            
            # Filter out very dark and very light colors
            filtered_palette = []
            for color in palette:
                brightness = sum(color) / 3  # Average brightness
                if 30 < brightness < 220:  # Avoid too dark (<30) or too light (>220)
                    filtered_palette.append(color)
            
            # Use filtered palette or fall back to original if filtered is empty
            working_palette = filtered_palette if filtered_palette else palette
            
            # Find the most saturated color for better visual impact
            from colorsys import rgb_to_hsv
            
            best_color = working_palette[0]
            max_saturation = 0
            
            for color in working_palette:
                r, g, b = [x/255.0 for x in color]
                h, s, v = rgb_to_hsv(r, g, b)
                
                # Combination of saturation and brightness for impact
                impact_score = s * (0.7 + 0.3 * v)  # Weight saturation higher, but brightness matters too
                
                if impact_score > max_saturation:
                    max_saturation = impact_score
                    best_color = color
            
            # Additional enhancement: boost saturation and adjust brightness
            from colorsys import rgb_to_hsv, hsv_to_rgb
            r, g, b = [x/255.0 for x in best_color]
            h, s, v = rgb_to_hsv(r, g, b)
            
            # Increase saturation by 30% and ensure brightness is in a good range
            s = min(s * 1.3, 1.0)  # More aggressive saturation boost
            v = max(min(v * 1.1, 0.9), 0.3)  # Keep brightness in a good range
            
            # Convert back to RGB
            r, g, b = hsv_to_rgb(h, s, v)
            enhanced_color = (int(r*255), int(g*255), int(b*255))
            
            # Convert RGB to hex
            hex_color = '#{:02x}{:02x}{:02x}'.format(*enhanced_color)
            logger.info(f"Extracted vibrant color: {hex_color} from album art")
            return hex_color
        except Exception as e:
            logger.error(f"Error extracting dominant color: {e}")
            return "#121212"  # Default dark background

    def read_raw_pipe_data(self, max_chunks=5):
        """
        Read raw data from the pipe for debugging purposes.
        Returns a list of binary chunks or None if no data is available.
        """
        result = []
        
        try:
            # Check if pipe exists
            if not os.path.exists(self.pipe_path):
                return None
                
            # Create a new file descriptor just for this read
            try:
                # Try non-blocking mode with fcntl
                import fcntl
                temp_fd = os.open(self.pipe_path, os.O_RDONLY)
                fcntl.fcntl(temp_fd, fcntl.F_SETFL, os.O_NONBLOCK)
            except (ImportError, AttributeError):
                # Fallback to blocking mode
                temp_fd = os.open(self.pipe_path, os.O_RDONLY)
            
            # Try to read some data with timeout using select
            readable, _, _ = select.select([temp_fd], [], [], 0.5)
            if temp_fd in readable:
                # Read up to max_chunks
                for i in range(max_chunks):
                    try:
                        # Read a small chunk
                        chunk = os.read(temp_fd, 128)
                        if not chunk:
                            break
                        result.append(chunk)
                    except:
                        break
            
            # Close the temporary file descriptor
            os.close(temp_fd)
            
            return result
            
        except Exception as e:
            logger.error(f"Error reading raw pipe data: {e}")
            return None

    def _metadata_reader_thread(self):
        """Thread for continuous reading of the metadata pipe."""
        logger.info("Starting metadata reader thread")
        
        while self.running:
            try:
                # Increment attempt counter and update timestamp
                self.debug_counters[DEBUG_CODE_READ_ATTEMPT] += 1
                self.last_pipe_read_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                if not os.path.exists(self.pipe_path):
                    logger.warning(f"Metadata pipe does not exist: {self.pipe_path}")
                    self.last_error = f"Metadata pipe does not exist: {self.pipe_path}"
                    time.sleep(5)
                    continue
                
                # Check if it's a proper FIFO using stat module
                try:
                    import stat as stat_module
                    st = os.stat(self.pipe_path)
                    if not stat_module.S_ISFIFO(st.st_mode):
                        logger.warning(f"Metadata path exists but is not a FIFO pipe: {self.pipe_path}")
                        self.last_error = f"Metadata path exists but is not a FIFO pipe: {self.pipe_path}"
                        time.sleep(5)
                        continue
                except Exception as e:
                    logger.warning(f"Error checking if path is FIFO: {e}")
                    self.last_error = f"Error checking if path is FIFO: {e}"
                    time.sleep(5)
                    continue
                
                # Open the pipe in non-blocking mode
                if self.pipe_fd is None:
                    try:
                        # Try to import fcntl for non-blocking mode
                        import fcntl
                        self.pipe_fd = os.open(self.pipe_path, os.O_RDONLY)
                        fcntl.fcntl(self.pipe_fd, fcntl.F_SETFL, os.O_NONBLOCK)
                        logger.info(f"Opened metadata pipe with non-blocking mode: {self.pipe_path}")
                    except (ImportError, AttributeError):
                        # Fallback if fcntl is not available or O_NONBLOCK is not defined
                        self.pipe_fd = os.open(self.pipe_path, os.O_RDONLY)
                        logger.info(f"Opened metadata pipe with blocking mode: {self.pipe_path}")
                    
                    logger.info(f"Pipe FD: {self.pipe_fd}, Path: {self.pipe_path}")
                
                # Use select to check if data is available with a timeout
                try:
                    readable, _, _ = select.select([self.pipe_fd], [], [], 1.0)
                    if self.pipe_fd in readable:
                        # Data is available to read
                        data = os.read(self.pipe_fd, 4)  # Read header (4 bytes)
                        if not data or len(data) == 0:
                            # Pipe was closed or empty read, reopen it
                            logger.warning("Empty read from pipe, reopening")
                            self.last_error = "Empty read from pipe, reopening"
                            os.close(self.pipe_fd)
                            self.pipe_fd = None
                            time.sleep(1)
                            continue
                        
                        # We got data - update the success counter and timestamp
                        self.debug_counters[DEBUG_CODE_READ_SUCCESS] += 1
                        self.last_pipe_data_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        # Parse the header
                        if len(data) == 4:
                            try:
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
                                if len(item_data) == item_length:
                                    # Success - process the data
                                    self._process_metadata_item(item_type, item_code, item_data)
                                    # Increment metadata update counter
                                    self.debug_counters[DEBUG_CODE_METADATA_UPDATE] += 1
                                else:
                                    # Incomplete data
                                    logger.warning(f"Incomplete data: expected {item_length} bytes, got {len(item_data)}")
                                    self.debug_counters[DEBUG_CODE_PARSE_ERROR] += 1
                                    self.last_error = f"Incomplete data: expected {item_length} bytes, got {len(item_data)}"
                            except Exception as e:
                                # Error parsing header or data
                                logger.error(f"Error parsing metadata: {e}")
                                self.debug_counters[DEBUG_CODE_PARSE_ERROR] += 1
                                self.last_error = f"Error parsing metadata: {e}"
                    else:
                        # No data available
                        time.sleep(0.1)
                except Exception as e:
                    logger.error(f"Error in select/read operation: {e}")
                    self.last_error = f"Error in select/read operation: {e}"
                    # Close and reopen pipe
                    if self.pipe_fd is not None:
                        try:
                            os.close(self.pipe_fd)
                        except:
                            pass
                        self.pipe_fd = None
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in metadata reader thread: {e}")
                self.last_error = f"Error in metadata reader thread: {e}"
                self.debug_counters[DEBUG_CODE_PROCESS_ERROR] += 1
                
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