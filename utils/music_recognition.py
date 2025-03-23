"""
Music recognition utility to identify songs from microphone input.
Uses AcoustID/Chromaprint for audio fingerprinting and MusicBrainz for metadata.
"""

import os
import time
import logging
import tempfile
import threading
import subprocess
from io import BytesIO
from pathlib import Path

import requests
import pyaudio
import acoustid
import numpy as np
import musicbrainzngs
from PIL import Image
from colorthief import ColorThief

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# MusicBrainz configuration
musicbrainzngs.set_useragent("PiAudioDisplay", "1.0", "https://github.com/yourusername/pi-audio-display")

# AcoustID API key - This needs to be obtained from https://acoustid.org/
ACOUSTID_API_KEY = None  # Will be set from environment variable or file

def load_api_key_from_file():
    """Load AcoustID API key from file."""
    global ACOUSTID_API_KEY
    
    # Possible locations for API key file
    key_file_paths = [
        '.acoustid_api_key',  # Current directory
        os.path.expanduser('~/.acoustid_api_key'),  # User's home directory
        '/etc/acoustid_api_key'  # System-wide location
    ]
    
    # Try to load from each location
    for path in key_file_paths:
        try:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    key = f.read().strip()
                    if key:
                        logger.info(f"Loaded AcoustID API key from {path}")
                        ACOUSTID_API_KEY = key
                        return True
        except Exception as e:
            logger.error(f"Error reading API key from {path}: {e}")
    
    return False

# Try to load API key from file
load_api_key_from_file()

class MusicRecognitionService:
    """Service for recognizing music from microphone input and retrieving metadata."""
    
    def __init__(self, sample_rate=44100, chunk_size=1024, record_seconds=10):
        """
        Initialize the music recognition service.
        
        Args:
            sample_rate: Audio sample rate in Hz
            chunk_size: Size of audio chunks to process
            record_seconds: Number of seconds to record for fingerprinting
        """
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.record_seconds = record_seconds
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.is_running = False
        self.recognition_thread = None
        self.current_metadata = {
            'title': "Not Playing",
            'artist': None,
            'album': None,
            'artwork': None,
            'background_color': "#121212"  # Default dark background
        }
        self.last_recognition_time = 0
        self.recognition_cooldown = 30  # seconds between recognition attempts
        self.static_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static')
        
        # Set API key from environment variable if not already loaded from file
        global ACOUSTID_API_KEY
        if not ACOUSTID_API_KEY:
            ACOUSTID_API_KEY = os.environ.get('ACOUSTID_API_KEY')
            if ACOUSTID_API_KEY:
                logger.info("Using AcoustID API key from environment variable")
        
        # Ensure artwork directory exists
        os.makedirs(os.path.join(self.static_folder, 'artwork'), exist_ok=True)
        
        # Set default artwork path
        self.default_artwork_path = os.path.join(self.static_folder, 'artwork', 'default_album.svg')
        
        # For simulation mode when no microphone is available
        self.simulation_counter = 0
        self.simulation_songs = [
            {
                'title': 'Bohemian Rhapsody',
                'artist': 'Queen',
                'album': 'A Night at the Opera',
                'recording_id': '5e2e55ff-bd95-40f5-b5cf-c9f8702077f6',
                'album_id': '1476f824-ced9-4645-953c-3ba704568ada'
            },
            {
                'title': 'Imagine',
                'artist': 'John Lennon',
                'album': 'Imagine',
                'recording_id': 'b95ce3ff-3d05-4e87-9e01-c808a422d7d9',
                'album_id': 'b8ee4327-cc36-3137-9b83-b20723839ff5'
            },
            {
                'title': 'Billie Jean',
                'artist': 'Michael Jackson',
                'album': 'Thriller',
                'recording_id': 'f91e3192-8347-4b44-b7ee-8f9f274a46d8',
                'album_id': 'cfc01deb-4515-4e8d-bf98-1c5ed1c1303e'
            }
        ]

    def start(self):
        """Start the music recognition service."""
        if self.is_running:
            return
            
        self.is_running = True
        self.recognition_thread = threading.Thread(target=self._recognition_loop)
        self.recognition_thread.daemon = True
        self.recognition_thread.start()
        logger.info("Music recognition service started")

    def stop(self):
        """Stop the music recognition service."""
        self.is_running = False
        if self.recognition_thread:
            self.recognition_thread.join(timeout=2.0)
        logger.info("Music recognition service stopped")

    def get_current_metadata(self):
        """Get the current song metadata."""
        return self.current_metadata.copy()

    def _recognition_loop(self):
        """Main loop for continuous music recognition."""
        while self.is_running:
            try:
                current_time = time.time()
                # Only try to recognize music after cooldown period
                if current_time - self.last_recognition_time >= self.recognition_cooldown:
                    logger.info("Attempting music recognition...")
                    self._record_and_recognize()
                    self.last_recognition_time = time.time()
                
                # Sleep to avoid consuming too many resources
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in recognition loop: {e}")
                time.sleep(10)  # Wait longer if there's an error

    def _record_and_recognize(self):
        """Record audio and attempt to recognize the song."""
        try:
            # Check if API key is available
            if not ACOUSTID_API_KEY:
                logger.warning("AcoustID API key not set. Music recognition is disabled.")
                return
                
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            logger.info(f"Recording {self.record_seconds} seconds of audio...")
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Try to find the microphone device
            device_index = self._find_microphone_device(p)
            if device_index is None:
                logger.error("No microphone device found")
                p.terminate()
                
                # For testing purposes, use simulation mode when no microphone is available
                self._use_simulation_mode()
                return
                
            # Open stream
            stream = p.open(format=self.audio_format,
                           channels=self.channels,
                           rate=self.sample_rate,
                           input=True,
                           input_device_index=device_index,
                           frames_per_buffer=self.chunk_size)
            
            frames = []
            
            # Record audio data
            for i in range(0, int(self.sample_rate / self.chunk_size * self.record_seconds)):
                data = stream.read(self.chunk_size, exception_on_overflow=False)
                frames.append(data)
            
            # Stop recording
            stream.stop_stream()
            stream.close()
            p.terminate()
            
            logger.info("Recording complete, processing audio...")
            
            # Save the recorded audio to the temporary file
            self._save_wav(temp_filename, frames)
            
            # Fingerprint and identify the song
            self._identify_song(temp_filename)
            
            # Clean up the temporary file
            os.unlink(temp_filename)
            
        except Exception as e:
            logger.error(f"Error during recording and recognition: {e}")

    def _find_microphone_device(self, p):
        """Find the index of the microphone device."""
        device_index = None
        
        try:
            # Get the number of audio devices
            device_count = p.get_device_count()
            
            # Look for a device with microphone capabilities
            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)
                # Check if this is an input device (microphone)
                if device_info.get('maxInputChannels', 0) > 0:
                    logger.info(f"Found microphone device: {device_info.get('name')}")
                    # Prioritize USB Audio devices
                    if 'usb' in device_info.get('name', '').lower():
                        logger.info(f"Selected USB microphone: {device_info.get('name')}")
                        return i
                    # Otherwise, just use the first microphone we find
                    if device_index is None:
                        device_index = i
        except Exception as e:
            logger.error(f"Error finding microphone device: {e}")
        
        return device_index

    def _save_wav(self, filename, frames):
        """Save recorded audio as WAV file using ffmpeg."""
        try:
            # Create a raw audio file first
            with open(f"{filename}.raw", 'wb') as f:
                for frame in frames:
                    f.write(frame)
            
            # Convert raw to wav with ffmpeg
            cmd = [
                'ffmpeg', 
                '-f', 's16le',  # Input format (signed 16-bit little-endian)
                '-ar', str(self.sample_rate),  # Sample rate
                '-ac', str(self.channels),  # Channels
                '-i', f"{filename}.raw",  # Input file
                '-y',  # Overwrite output file if it exists
                filename  # Output file
            ]
            
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # Clean up the raw file
            os.unlink(f"{filename}.raw")
            
        except Exception as e:
            logger.error(f"Error saving WAV file: {e}")
            raise

    def _identify_song(self, filename):
        """
        Identify a song from an audio file using AcoustID/Chromaprint.
        
        Args:
            filename: Path to the audio file
        """
        try:
            logger.info("Fingerprinting audio...")
            results = acoustid.match(ACOUSTID_API_KEY, filename)
            
            # Process the best result
            for score, recording_id, title, artist in results:
                logger.info(f"Match found: {title} by {artist} (score: {score})")
                
                if score < 0.5:  # Skip low confidence matches
                    logger.info(f"Low confidence match ({score}), skipping")
                    continue
                
                # Get detailed information from MusicBrainz
                self._get_musicbrainz_data(recording_id)
                return
                
            # If we get here, no good match was found
            logger.info("No confident match found for the audio")
            
        except acoustid.FingerprintGenerationError as e:
            logger.error(f"Error generating fingerprint: {e}")
        except acoustid.WebServiceError as e:
            logger.error(f"AcoustID web service error: {e}")
        except Exception as e:
            logger.error(f"Error identifying song: {e}")

    def _get_musicbrainz_data(self, recording_id):
        """
        Get detailed information about a recording from MusicBrainz.
        
        Args:
            recording_id: MusicBrainz recording ID
        """
        try:
            # Get recording information with release data
            recording = musicbrainzngs.get_recording_by_id(
                recording_id, 
                includes=["artists", "releases"]
            )
            
            # Extract the basic data
            recording_data = recording["recording"]
            title = recording_data.get("title", "Unknown Title")
            
            # Get artist information
            artist_credit = recording_data.get("artist-credit", [])
            artist_names = []
            for artist in artist_credit:
                if isinstance(artist, dict) and "artist" in artist:
                    artist_names.append(artist["artist"]["name"])
                elif isinstance(artist, str) and artist.strip():
                    artist_names.append(artist.strip())
            
            artist = ", ".join(artist_names) if artist_names else "Unknown Artist"
            
            # Get album information
            album = None
            album_id = None
            if "release-list" in recording_data and recording_data["release-list"]:
                release = recording_data["release-list"][0]
                album = release.get("title", "Unknown Album")
                album_id = release.get("id")
            
            # Update the metadata
            metadata = {
                'title': title,
                'artist': artist,
                'album': album,
                'artwork': None,
                'background_color': "#121212"  # Default dark background
            }
            
            # Fetch album art and dominant color if album ID is available
            if album_id:
                artwork_url, background_color = self._get_album_art(album_id)
                if artwork_url:
                    metadata['artwork'] = artwork_url
                if background_color:
                    metadata['background_color'] = background_color
            
            # Update the current metadata
            self.current_metadata = metadata
            logger.info(f"Updated metadata: {title} by {artist}")
            
        except musicbrainzngs.WebServiceError as e:
            logger.error(f"MusicBrainz web service error: {e}")
        except Exception as e:
            logger.error(f"Error getting MusicBrainz data: {e}")

    def _get_album_art(self, album_id):
        """
        Get album art for an album.
        
        Args:
            album_id: MusicBrainz album ID
            
        Returns:
            tuple: (artwork_url, background_color)
        """
        try:
            # First try to get cover art from CoverArtArchive
            artwork_filename = f"album_{album_id}.jpg"
            artwork_path = os.path.join(self.static_folder, 'artwork', artwork_filename)
            
            # Check if we already have this artwork cached
            if os.path.exists(artwork_path):
                logger.info(f"Using cached artwork for album: {album_id}")
                return self._get_artwork_url(artwork_filename)
            
            # Try to fetch from CoverArtArchive
            cover_art_url = f"http://coverartarchive.org/release/{album_id}/front"
            response = requests.get(cover_art_url, timeout=10)
            
            if response.status_code == 200:
                # Save the artwork
                with open(artwork_path, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"Downloaded artwork for album: {album_id}")
                return self._get_artwork_url(artwork_filename)
            else:
                logger.info(f"No cover art found for album: {album_id}")
                return self._get_artwork_url(None)
                
        except Exception as e:
            logger.error(f"Error getting album art: {e}")
            return self._get_artwork_url(None)

    def _use_simulation_mode(self):
        """
        Simulate song recognition when microphone is not available.
        This is for testing purposes only.
        """
        try:
            # Use a rotating selection of songs
            song = self.simulation_songs[self.simulation_counter % len(self.simulation_songs)]
            self.simulation_counter += 1
            
            logger.info(f"SIMULATION MODE: Pretending to recognize {song['title']} by {song['artist']}")
            
            # Create metadata for the simulated song
            metadata = {
                'title': song['title'],
                'artist': song['artist'],
                'album': song['album'],
                'artwork': None,
                'background_color': "#121212"  # Default dark background
            }
            
            # Try to get album art
            if song['album_id']:
                artwork_url, background_color = self._get_album_art(song['album_id'])
                if artwork_url:
                    metadata['artwork'] = artwork_url
                if background_color:
                    metadata['background_color'] = background_color
            
            # Update the current metadata
            self.current_metadata = metadata
            logger.info(f"Updated metadata with simulated song: {song['title']} by {song['artist']}")
            
        except Exception as e:
            logger.error(f"Error in simulation mode: {e}")
    
    def _get_artwork_url(self, artwork_filename):
        """
        Get the URL and dominant color for album artwork.
        
        Args:
            artwork_filename: Filename of the artwork or None for default
            
        Returns:
            tuple: (artwork_url, background_color)
        """
        if not artwork_filename:
            # Use default artwork
            artwork_url = "/static/artwork/default_album.svg"
            return artwork_url, "#121212"  # Default dark background
        
        # Get the path to the artwork
        artwork_path = os.path.join(self.static_folder, 'artwork', artwork_filename)
        
        # Get the URL
        artwork_url = f"/static/artwork/{artwork_filename}"
        
        # Extract the dominant color
        try:
            color_thief = ColorThief(artwork_path)
            dominant_color = color_thief.get_color(quality=1)
            
            # Convert RGB to hex with darkened value for better text contrast
            r, g, b = dominant_color
            # Darken the color for better text contrast
            r = int(r * 0.4)  # Reduce brightness to 40%
            g = int(g * 0.4)
            b = int(b * 0.4)
            background_color = f"#{r:02x}{g:02x}{b:02x}"
            
            logger.info(f"Extracted background color: {background_color}")
            return artwork_url, background_color
            
        except Exception as e:
            logger.error(f"Error extracting dominant color: {e}")
            return artwork_url, "#121212"  # Default dark background