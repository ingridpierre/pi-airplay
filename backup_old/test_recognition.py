#!/usr/bin/env python3
"""
Test script for music recognition functionality
This bypasses the microphone input to test the AcoustID API integration
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("test-recognition")

# Try to import required libraries
try:
    import acoustid
    import musicbrainzngs
    logger.info("Successfully imported acoustid and musicbrainzngs")
except ImportError as e:
    logger.error(f"Failed to import required libraries: {e}")
    logger.error("Please install the required libraries: pip install pyacoustid musicbrainzngs")
    sys.exit(1)

# Set up MusicBrainz client
musicbrainzngs.set_useragent(
    "Pi-DAD",
    "1.0",
    "https://github.com/yourusername/pi-dad"
)

def load_api_key():
    """Load AcoustID API key from various locations"""
    api_key = None
    api_key_paths = [
        '.acoustid_api_key',
        os.path.expanduser('~/.acoustid_api_key'),
        '/etc/acoustid_api_key',
        os.path.join('config', 'acoustid_api_key')
    ]
    
    for path in api_key_paths:
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        logger.info(f"Loaded AcoustID API key from {path}")
                        break
        except Exception as e:
            logger.error(f"Error reading API key from {path}: {e}")
    
    # Also check environment variable
    if not api_key:
        api_key = os.environ.get('ACOUSTID_API_KEY')
        if api_key:
            logger.info("Using AcoustID API key from environment variable")
    
    return api_key

def identify_song(file_path, api_key):
    """Identify a song from an audio file"""
    if not api_key:
        logger.error("No AcoustID API key provided")
        return None
    
    try:
        logger.info(f"Analyzing audio file: {file_path}")
        
        # Calculate audio fingerprint
        duration, fingerprint = acoustid.fingerprint_file(file_path)
        logger.info(f"Generated fingerprint (duration: {duration:.2f}s)")
        
        # Look up the fingerprint with AcoustID
        logger.info("Searching AcoustID database...")
        results = acoustid.lookup(api_key, fingerprint, duration)
        
        if not results:
            logger.info("No matches found")
            return None
            
        # Process results
        for result in results:
            score = result['score']
            
            if score < 0.5:
                logger.info(f"Match with low score ({score:.2f}), skipping")
                continue
                
            logger.info(f"Found match with score: {score:.2f}")
            
            if 'recordings' not in result:
                logger.info("No recording data in result")
                continue
                
            for recording in result['recordings']:
                rec_id = recording.get('id')
                
                if not rec_id:
                    continue
                    
                # Get detailed information
                logger.info(f"Looking up recording details for ID: {rec_id}")
                try:
                    mb_result = musicbrainzngs.get_recording_by_id(
                        rec_id, includes=["artists", "releases"]
                    )
                    
                    if mb_result and "recording" in mb_result:
                        recording_info = mb_result["recording"]
                        
                        # Extract metadata
                        metadata = {
                            'title': recording_info.get('title', 'Unknown'),
                            'artist': recording_info.get('artist-credit-phrase', 'Unknown Artist'),
                            'album': None,
                            'background_color': "#121212"
                        }
                        
                        # Try to get album title
                        if "release-list" in recording_info and recording_info["release-list"]:
                            metadata['album'] = recording_info["release-list"][0].get("title")
                        
                        logger.info(f"Identified song: {metadata['title']} by {metadata['artist']}")
                        return metadata
                        
                except Exception as e:
                    logger.error(f"Error getting MusicBrainz data: {e}")
        
        logger.info("No suitable matches found")
        return None
        
    except acoustid.FingerprintGenerationError as e:
        logger.error(f"Error generating fingerprint: {e}")
        return None
    except acoustid.WebServiceError as e:
        logger.error(f"AcoustID API error: {e}")
        return None
    except Exception as e:
        logger.error(f"Error in song identification: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def main():
    """Test the music recognition functionality"""
    api_key = load_api_key()
    
    if not api_key:
        logger.error("No AcoustID API key found. Please set one up first.")
        logger.error("Visit https://acoustid.org/login to get an API key.")
        return
    
    # Check if a file was provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # Use a demo file if no file is provided
        logger.info("No audio file specified. Please provide a path to an audio file.")
        logger.info("Usage: python test_recognition.py <path-to-audio-file>")
        return
    
    # Check if the file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return
    
    # Identify the song
    metadata = identify_song(file_path, api_key)
    
    if metadata:
        logger.info("=" * 40)
        logger.info("Song identified!")
        logger.info(f"Title: {metadata['title']}")
        logger.info(f"Artist: {metadata['artist']}")
        logger.info(f"Album: {metadata['album']}")
        logger.info("=" * 40)
    else:
        logger.error("Failed to identify the song.")

if __name__ == "__main__":
    main()