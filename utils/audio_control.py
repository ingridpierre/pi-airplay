import os
import fcntl
import select
import base64
import logging
import json
import time
import subprocess
from threading import Lock

logger = logging.getLogger(__name__)

class AudioController:
    def __init__(self):
        self.metadata_pipe_path = '/tmp/shairport-sync-metadata'
        self.current_metadata = {
            'title': 'Not Playing',
            'artist': None,
            'album': None,
            'artwork': None
        }
        self.lock = Lock()
        self.last_update_time = 0
        self.update_interval = 1.0  # Check metadata every second
        self._ensure_metadata_pipe()
    
    def _ensure_metadata_pipe(self):
        """Ensure the metadata pipe exists with correct permissions."""
        if not os.path.exists(self.metadata_pipe_path):
            logger.warning(f"Metadata pipe not found at {self.metadata_pipe_path}")
            return False
        
        try:
            stat = os.stat(self.metadata_pipe_path)
            perms = oct(stat.st_mode)[-3:]
            owner = f"{stat.st_uid}:{stat.st_gid}"
            logger.info(f"Metadata pipe exists with permissions: {perms}")
            logger.info(f"Pipe owner: {owner}")
            return True
        except OSError as e:
            logger.error(f"Error checking metadata pipe: {e}")
            return False
    
    def _parse_metadata(self, data):
        """Parse the metadata from the pipe data with improved error handling."""
        parsed = {}
        
        # Extract base64-encoded artwork if present (appears between <data encoding="base64"> and </data>)
        artwork = None
        if b'<data encoding="base64">' in data and b'</data>' in data:
            try:
                start_tag = b'<data encoding="base64">'
                end_tag = b'</data>'
                start_pos = data.find(start_tag) + len(start_tag)
                end_pos = data.find(end_tag, start_pos)
                
                if start_pos >= 0 and end_pos >= 0:
                    artwork_data = data[start_pos:end_pos].strip()
                    # Store the base64 encoded artwork
                    artwork = artwork_data.decode('utf-8', errors='ignore')
            except Exception as e:
                logger.error(f"Error parsing artwork: {e}")
        
        # Extract track info (appears between <item><type>core</type><code>PICT</code> and </item>)
        try:
            decoded = data.decode('utf-8', errors='ignore')
            
            # Extract title
            if '<code>minm</code>' in decoded:
                title_start = decoded.find('<code>minm</code>') + len('<code>minm</code>')
                title_end = decoded.find('</item>', title_start)
                if title_start >= 0 and title_end >= 0:
                    # Extract text between <data>...</data>
                    data_start = decoded.find('<data>', title_start) + len('<data>')
                    data_end = decoded.find('</data>', data_start)
                    if data_start >= 0 and data_end >= 0:
                        parsed['title'] = decoded[data_start:data_end].strip()
            
            # Extract artist
            if '<code>asar</code>' in decoded:
                artist_start = decoded.find('<code>asar</code>') + len('<code>asar</code>')
                artist_end = decoded.find('</item>', artist_start)
                if artist_start >= 0 and artist_end >= 0:
                    # Extract text between <data>...</data>
                    data_start = decoded.find('<data>', artist_start) + len('<data>')
                    data_end = decoded.find('</data>', data_start)
                    if data_start >= 0 and data_end >= 0:
                        parsed['artist'] = decoded[data_start:data_end].strip()
            
            # Extract album
            if '<code>asal</code>' in decoded:
                album_start = decoded.find('<code>asal</code>') + len('<code>asal</code>')
                album_end = decoded.find('</item>', album_start)
                if album_start >= 0 and album_end >= 0:
                    # Extract text between <data>...</data>
                    data_start = decoded.find('<data>', album_start) + len('<data>')
                    data_end = decoded.find('</data>', data_start)
                    if data_start >= 0 and data_end >= 0:
                        parsed['album'] = decoded[data_start:data_end].strip()
            
            # Add the artwork if found
            if artwork:
                parsed['artwork'] = artwork
            
        except Exception as e:
            logger.error(f"Error parsing metadata text: {e}")
        
        return parsed
    
    def get_current_metadata(self):
        """Get the current metadata with improved error handling and responsiveness."""
        current_time = time.time()
        
        # Only check if enough time has passed since last update (to avoid constant reads)
        if current_time - self.last_update_time >= self.update_interval:
            self.last_update_time = current_time
            
            if not os.path.exists(self.metadata_pipe_path):
                logger.warning("Metadata pipe not found")
                return self.current_metadata
            
            try:
                # Open the pipe in non-blocking mode
                fd = os.open(self.metadata_pipe_path, os.O_RDONLY | os.O_NONBLOCK)
                try:
                    # Use select to wait for data with a short timeout
                    with os.fdopen(fd, 'rb') as pipe:
                        ready, _, _ = select.select([pipe], [], [], 0.2)  # 200ms timeout
                        
                        if ready:
                            data = pipe.read(16384)  # Read a good chunk to get complete metadata
                            if data:
                                with self.lock:
                                    new_metadata = self._parse_metadata(data)
                                    
                                    # Update only the fields that were parsed successfully
                                    for key, value in new_metadata.items():
                                        if value:  # Only update if the value is not empty
                                            self.current_metadata[key] = value
                except Exception as e:
                    logger.error(f"Error reading from metadata pipe: {e}")
                finally:
                    try:
                        os.close(fd)
                    except:
                        pass
            except Exception as e:
                logger.error(f"Error opening metadata pipe: {e}")
        
        # Return a copy of the current metadata to prevent external modification
        with self.lock:
            metadata_copy = dict(self.current_metadata)
        
        return metadata_copy
    
    def is_playing(self):
        """Check if shairport-sync is actively streaming."""
        # Method 1: Check if the process exists and is running
        try:
            # Look for shairport-sync process
            result = subprocess.run(['pgrep', 'shairport-sync'], 
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
            
            # If process exists, check title in metadata
            if result.returncode == 0:
                metadata = self.get_current_metadata()
                # Consider it playing if we have a title that's not the default
                return metadata.get('title') != 'Not Playing'
            
            return False
        except Exception as e:
            logger.error(f"Error checking if playing: {e}")
            return False