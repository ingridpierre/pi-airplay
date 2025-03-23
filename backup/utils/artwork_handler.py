import logging
import base64
import os
from io import BytesIO

logger = logging.getLogger(__name__)

class ArtworkHandler:
    """
    Utility class to handle album artwork from AirPlay metadata
    """
    def __init__(self, static_folder):
        """
        Initialize the artwork handler.
        
        Args:
            static_folder: Path to the Flask static folder to store artwork temporarily
        """
        self.static_folder = static_folder
        self.artwork_folder = os.path.join(static_folder, 'artwork')
        self.current_artwork_path = None
        self._ensure_artwork_folder()
    
    def _ensure_artwork_folder(self):
        """Ensure the artwork folder exists."""
        if not os.path.exists(self.artwork_folder):
            try:
                os.makedirs(self.artwork_folder)
                logger.info(f"Created artwork folder at {self.artwork_folder}")
            except OSError as e:
                logger.error(f"Failed to create artwork folder: {e}")
    
    def save_artwork_from_metadata(self, metadata):
        """
        Extract and save artwork from metadata.
        
        Args:
            metadata: The metadata dictionary containing artwork
            
        Returns:
            str: Relative URL path to the artwork or None if no artwork
        """
        # Check if metadata contains artwork data (base64 encoded)
        if not metadata or 'artwork' not in metadata or not metadata['artwork']:
            return None
        
        try:
            # Decode base64 data
            artwork_data = base64.b64decode(metadata['artwork'])
            
            # Create a unique filename based on current track info
            track_id = f"{metadata.get('artist', 'unknown')}_{metadata.get('album', 'unknown')}_{metadata.get('title', 'unknown')}"
            track_id = "".join([c if c.isalnum() else "_" for c in track_id])
            artwork_filename = f"artwork_{track_id}.jpg"
            artwork_path = os.path.join(self.artwork_folder, artwork_filename)
            
            # Save the artwork
            with open(artwork_path, 'wb') as f:
                f.write(artwork_data)
            
            logger.info(f"Saved artwork to {artwork_path}")
            self.current_artwork_path = f"/static/artwork/{artwork_filename}"
            return self.current_artwork_path
        
        except Exception as e:
            logger.error(f"Error saving artwork: {e}")
            return None
    
    def get_current_artwork_url(self):
        """Get the URL of the current artwork."""
        return self.current_artwork_path