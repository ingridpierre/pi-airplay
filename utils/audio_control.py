"""
Audio control module that handles AirPlay metadata from shairport-sync.
"""

import os
import logging
import re
import json
import time
import base64
import binascii
import xml.etree.ElementTree as ET
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AudioController:
    def __init__(self, pipe_path='/tmp/shairport-sync-metadata'):
        """
        Initialize the audio controller.
        
        Args:
            pipe_path: Path to the shairport-sync metadata pipe
        """
        self.pipe_path = pipe_path
        self.last_metadata = {}
        self.current_metadata = {
            'title': "Not Playing",
            'artist': None,
            'album': None,
            'artwork': None,
            'background_color': "#121212"  # Default dark background
        }
        self.last_check_time = 0
        self.check_interval = 2  # seconds
        self.artwork_path = Path('static/artwork/current_album.jpg')
        
        # Ensure the pipe exists with proper permissions
        self._ensure_metadata_pipe()

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
        except Exception as e:
            logger.error(f"Error setting up metadata pipe: {e}")

    def _parse_metadata(self, data):
        """Parse the metadata from the pipe data with improved error handling."""
        result = {}
        
        try:
            # Try to parse as XML
            if b'<item>' in data:
                root = ET.fromstring(data.decode('utf-8', errors='ignore'))
                
                for item in root.findall('.//item'):
                    item_type = item.get('type')
                    
                    if item_type == 'ssnc':
                        code = item.findtext('code')
                        if code == 'PICT':
                            # Base64 encoded image data
                            raw_data = item.findtext('data')
                            if raw_data:
                                try:
                                    # Decode and save the image
                                    img_data = base64.b64decode(raw_data)
                                    with open(self.artwork_path, 'wb') as f:
                                        f.write(img_data)
                                    result['artwork'] = '/static/artwork/current_album.jpg'
                                except (binascii.Error, OSError) as e:
                                    logger.error(f"Error saving artwork: {e}")
                    
                    elif item_type == 'core':
                        code = item.findtext('code')
                        text = item.findtext('data')
                        
                        if code == 'asar' and text:  # Artist
                            result['artist'] = text
                        elif code == 'asal' and text:  # Album
                            result['album'] = text
                        elif code == 'minm' and text:  # Track name
                            result['title'] = text
                            
            # Try to parse as JSON
            else:
                try:
                    json_data = json.loads(data.decode('utf-8', errors='ignore'))
                    
                    if 'metadata' in json_data:
                        metadata = json_data['metadata']
                        if 'minm' in metadata:
                            result['title'] = metadata['minm']
                        if 'asar' in metadata:
                            result['artist'] = metadata['asar']
                        if 'asal' in metadata:
                            result['album'] = metadata['asal']
                except json.JSONDecodeError:
                    # Not valid JSON, try regex parsing
                    text = data.decode('utf-8', errors='ignore')
                    
                    # Try to extract metadata with regex
                    title_match = re.search(r'"minm"\s*:\s*"([^"]+)"', text)
                    if title_match:
                        result['title'] = title_match.group(1)
                    
                    artist_match = re.search(r'"asar"\s*:\s*"([^"]+)"', text)
                    if artist_match:
                        result['artist'] = artist_match.group(1)
                        
                    album_match = re.search(r'"asal"\s*:\s*"([^"]+)"', text)
                    if album_match:
                        result['album'] = album_match.group(1)
                    
        except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
        
        return result

    def get_current_metadata(self):
        """Get the current metadata with improved error handling and responsiveness."""
        current_time = time.time()
        
        # Only check for new metadata periodically to avoid excessive file operations
        if current_time - self.last_check_time >= self.check_interval:
            self.last_check_time = current_time
            
            try:
                # Non-blocking check if pipe exists and has data
                if os.path.exists(self.pipe_path):
                    pipe_fd = os.open(self.pipe_path, os.O_RDONLY | os.O_NONBLOCK)
                    try:
                        data = os.read(pipe_fd, 16384)  # Read up to 16KB
                        if data:
                            new_metadata = self._parse_metadata(data)
                            
                            # Only update if we got meaningful data
                            if new_metadata:
                                if 'title' in new_metadata:
                                    self.current_metadata['title'] = new_metadata['title']
                                if 'artist' in new_metadata:
                                    self.current_metadata['artist'] = new_metadata['artist']
                                if 'album' in new_metadata:
                                    self.current_metadata['album'] = new_metadata['album']
                                if 'artwork' in new_metadata:
                                    self.current_metadata['artwork'] = new_metadata['artwork']
                                
                                # If all fields are None except title, consider it not playing
                                if (self.current_metadata['artist'] is None and 
                                    self.current_metadata['album'] is None and
                                    self.current_metadata['artwork'] is None):
                                    logger.info("No complete metadata available, using default")
                                    self.current_metadata['artwork'] = '/static/artwork/default_album.svg'
                                    
                                self.last_metadata = self.current_metadata.copy()
                                
                    except (OSError, IOError) as e:
                        # No data available or error reading pipe
                        pass
                    finally:
                        os.close(pipe_fd)
                else:
                    logger.debug(f"Metadata pipe {self.pipe_path} does not exist")
                    
            except Exception as e:
                logger.error(f"Error getting metadata: {e}")
        
        return self.current_metadata

    def is_playing(self):
        """Check if shairport-sync is actively streaming."""
        # Method 1: Check process status
        try:
            # Check if the shairport-sync process is running
            with os.popen('pgrep shairport-sync') as proc:
                if proc.read().strip():
                    # Method 2: Check if there's recent metadata
                    if self.current_metadata.get('title') != "Not Playing":
                        current_time = time.time()
                        # Consider it playing if we've received metadata in the last 10 seconds
                        if current_time - self.last_check_time < 10:
                            return True
        except Exception as e:
            logger.error(f"Error checking playback status: {e}")
            
        return False