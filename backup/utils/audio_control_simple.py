"""
Simplified audio control module that handles AirPlay metadata from shairport-sync.
"""

import os
import logging
import select
import json
from os import O_RDONLY, O_NONBLOCK

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
        self._ensure_metadata_pipe()
        
    def _ensure_metadata_pipe(self):
        """Ensure the metadata pipe exists with correct permissions."""
        try:
            # Check if pipe exists
            if not os.path.exists(self.pipe_path):
                logger.warning(f"Metadata pipe {self.pipe_path} not found")
                return False
                
            # Check permissions
            stat = os.stat(self.pipe_path)
            perms = oct(stat.st_mode)[-3:]
            owner = f"{stat.st_uid}:{stat.st_gid}"
            
            logger.info(f"Metadata pipe exists with permissions: {perms}")
            logger.info(f"Pipe owner: {owner}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking metadata pipe: {e}")
            return False
            
    def _parse_metadata(self, data):
        """Parse the metadata from the pipe data with improved error handling."""
        metadata = {
            'title': None,
            'artist': None,
            'album': None,
            'artwork': None
        }
        
        try:
            # Simple parsing approach that just looks for key data items
            if b'<item><type>core</type><code>PICT</code>' in data:
                # Image data is present, but we'll handle artwork separately
                metadata['artwork'] = '/static/artwork/current_album.jpg'
                
            if b'<item><type>core</type><code>mper</code>' in data:
                parts = data.split(b'<item><type>core</type><code>mper</code><length>')
                if len(parts) > 1:
                    artist_part = parts[1].split(b'</data></item>')[0]
                    artist_start = artist_part.find(b'<data encoding="base64">') + len(b'<data encoding="base64">')
                    artist_end = artist_part.rfind(b'</data>')
                    if artist_start > 0 and artist_end > artist_start:
                        import base64
                        artist_b64 = artist_part[artist_start:artist_end].strip()
                        try:
                            metadata['artist'] = base64.b64decode(artist_b64).decode('utf-8')
                        except:
                            pass
                            
            if b'<item><type>core</type><code>asal</code>' in data:
                parts = data.split(b'<item><type>core</type><code>asal</code><length>')
                if len(parts) > 1:
                    album_part = parts[1].split(b'</data></item>')[0]
                    album_start = album_part.find(b'<data encoding="base64">') + len(b'<data encoding="base64">')
                    album_end = album_part.rfind(b'</data>')
                    if album_start > 0 and album_end > album_start:
                        import base64
                        album_b64 = album_part[album_start:album_end].strip()
                        try:
                            metadata['album'] = base64.b64decode(album_b64).decode('utf-8')
                        except:
                            pass
            
            if b'<item><type>core</type><code>minm</code>' in data:
                parts = data.split(b'<item><type>core</type><code>minm</code><length>')
                if len(parts) > 1:
                    title_part = parts[1].split(b'</data></item>')[0]
                    title_start = title_part.find(b'<data encoding="base64">') + len(b'<data encoding="base64">')
                    title_end = title_part.rfind(b'</data>')
                    if title_start > 0 and title_end > title_start:
                        import base64
                        title_b64 = title_part[title_start:title_end].strip()
                        try:
                            metadata['title'] = base64.b64decode(title_b64).decode('utf-8')
                        except:
                            pass
                
        except Exception as e:
            logger.error(f"Error parsing metadata: {e}")
            
        return metadata
            
    def get_current_metadata(self):
        """Get the current metadata with improved error handling and responsiveness."""
        metadata = {
            'title': "Not Playing",
            'artist': None, 
            'album': None,
            'artwork': None
        }
        
        if not os.path.exists(self.pipe_path):
            return metadata
            
        try:
            # Open pipe in non-blocking mode
            fd = os.open(self.pipe_path, os.O_RDONLY | os.O_NONBLOCK)
            try:
                with os.fdopen(fd, 'rb') as pipe:
                    ready, _, _ = select.select([pipe], [], [], 0.5)  # 500ms timeout
                    if ready:
                        data = pipe.read(4096)
                        if data:
                            parsed = self._parse_metadata(data)
                            # Only update fields that have values
                            for key, value in parsed.items():
                                if value:
                                    metadata[key] = value
            finally:
                # Ensure we always close the file descriptor
                try:
                    os.close(fd)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error reading metadata pipe: {e}")
            
        return metadata
        
    def is_playing(self):
        """Check if shairport-sync is actively streaming."""
        try:
            # A simple approach to check if the service is active and playing
            # This could be improved with actual stream status detection
            import subprocess
            result = subprocess.run(['pgrep', 'shairport-sync'], capture_output=True, text=True)
            if result.returncode == 0:
                # Process is running, now check if it's actively streaming
                # by seeing if the pipe has recent data
                fd = os.open(self.pipe_path, os.O_RDONLY | os.O_NONBLOCK)
                try:
                    with os.fdopen(fd, 'rb') as pipe:
                        ready, _, _ = select.select([pipe], [], [], 0.1)
                        if ready:
                            return True
                finally:
                    try:
                        os.close(fd)
                    except:
                        pass
                        
            return False
            
        except Exception as e:
            logger.error(f"Error checking playback status: {e}")
            return False