"""
Simplified music recognition utility to identify songs from microphone input.
Uses AcoustID/Chromaprint for audio fingerprinting and MusicBrainz for metadata.
"""

import os
import time
import logging
import tempfile
import threading
import requests
from pathlib import Path

import pyaudio
import acoustid
import musicbrainzngs
from colorthief import ColorThief
from PIL import Image
from io import BytesIO

# Set up logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# MusicBrainz configuration
musicbrainzngs.set_useragent("Pi-DAD", "1.0", "https://github.com/yourusername/pi-dad")

class MusicRecognitionService:
    """Simplified service for recognizing music from microphone input."""
    
    def __init__(self, api_key=None, sample_rate=44100, chunk_size=1024, record_seconds=10):
        """
        Initialize the music recognition service.
        
        Args:
            api_key: AcoustID API key (required for production use)
            sample_rate: Audio sample rate in Hz
            chunk_size: Size of audio chunks to process
            record_seconds: Number of seconds to record for fingerprinting
        """
        self.api_key = api_key or os.environ.get('ACOUSTID_API_KEY') or None
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
        
        # Ensure artwork directory exists
        os.makedirs(os.path.join(self.static_folder, 'artwork'), exist_ok=True)
        
        # For simulation mode
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
                # Only try to recognize music after cooldown period
                current_time = time.time()
                if current_time - self.last_recognition_time >= self.recognition_cooldown:
                    logger.info("Attempting music recognition...")
                    # Check for API key each time (in case it was updated)
                    if not self.api_key:
                        # Check common API key locations
                        for path in [
                            '.acoustid_api_key',  # Current directory
                            os.path.expanduser('~/.acoustid_api_key'),  # User's home directory
                            '/etc/acoustid_api_key',  # System-wide location
                            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config/acoustid_api_key')  # Config folder
                        ]:
                            try:
                                if os.path.exists(path):
                                    with open(path, 'r') as f:
                                        self.api_key = f.read().strip()
                                        if self.api_key:
                                            logger.info(f"Loaded AcoustID API key from {path}")
                                            break
                            except Exception as e:
                                logger.error(f"Error reading API key from {path}: {e}")
                    
                    if not self.api_key:
                        logger.warning("AcoustID API key not set. Music recognition is disabled.")
                        # Only use simulation mode if requested
                        if os.environ.get('PI_DAD_ENABLE_SIMULATION', '0') == '1':
                            self._use_simulation_mode()
                        else:
                            # Just set metadata to "Waiting for music"
                            self.current_metadata = {
                                'title': "Waiting for music...",
                                'artist': "Please set up AcoustID API key",
                                'album': None,
                                'artwork': None,
                                'background_color': "#121212"
                            }
                    else:
                        self._record_and_recognize()
                    self.last_recognition_time = time.time()
                
                # Sleep to avoid consuming too many resources
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error in recognition loop: {e}")
                time.sleep(10)  # Wait longer if there's an error

    def _record_and_recognize(self):
        """Record audio and attempt to recognize the song."""
        temp_filename = None
        p = None
        stream = None

        try:
            # Check if there's a .simulation_mode file, which indicates we should use simulation
            if os.path.exists('.simulation_mode'):
                logger.info("Found .simulation_mode file - using simulation mode")
                self._use_simulation_mode()
                return
            
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_filename = temp_file.name
            
            # Initialize PyAudio
            p = pyaudio.PyAudio()
            
            # Find microphone device
            device_index = None
            
            # First try to check for command-line audio tools
            try:
                import subprocess
                logger.info("Checking audio devices with arecord...")
                result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
                if result.returncode == 0:
                    devices = result.stdout.strip()
                    logger.info(f"Available audio devices:\n{devices}")
                    
                    # Look for USB audio devices
                    if 'USB' in devices:
                        logger.info("Found USB audio device in arecord output")
                
                logger.info("Testing direct recording with arecord...")
                # Try a quick 1-second recording to verify microphone access
                test_file = f"{temp_filename}_test.wav"
                subprocess.run(['arecord', '-d', '1', '-f', 'cd', test_file], 
                               capture_output=True, check=False)
                if os.path.exists(test_file) and os.path.getsize(test_file) > 0:
                    logger.info("Successfully recorded test audio with arecord")
                    os.unlink(test_file)
                else:
                    logger.warning("Failed to record test audio with arecord")
            except Exception as e:
                logger.warning(f"Error checking with arecord: {e}")
            
            # Now try PyAudio device detection
            for i in range(p.get_device_count()):
                device_info = p.get_device_info_by_index(i)
                # Check if this is an input device
                if device_info.get('maxInputChannels', 0) > 0:
                    logger.info(f"Found microphone: {device_info.get('name')}")
                    # Prioritize USB audio devices
                    if 'usb' in str(device_info.get('name', '')).lower():
                        device_index = i
                        break
                    # Otherwise, use the first microphone we find
                    if device_index is None:
                        device_index = i
            
            if device_index is None:
                logger.error("No microphone device found - using simulation mode instead")
                p.terminate()
                self._use_simulation_mode()
                return
                
            # Record audio with more robust error handling
            logger.info(f"Recording {self.record_seconds} seconds of audio...")
            try:
                stream = p.open(format=self.audio_format,
                              channels=self.channels,
                              rate=self.sample_rate,
                              input=True,
                              input_device_index=device_index,
                              frames_per_buffer=self.chunk_size)
                
                frames = []
                for i in range(0, int(self.sample_rate / self.chunk_size * self.record_seconds)):
                    try:
                        data = stream.read(self.chunk_size, exception_on_overflow=False)
                        frames.append(data)
                    except Exception as e:
                        logger.error(f"Error reading audio chunk {i}: {e}")
                        # Continue collecting what we can
                        continue
                
                if not frames:
                    raise Exception("No audio data captured")
                
                stream.stop_stream()
                stream.close()
                stream = None
                
                p.terminate()
                p = None
                
                # Save the recorded audio
                import wave
                with wave.open(temp_filename, 'wb') as wf:
                    wf.setnchannels(self.channels)
                    wf.setsampwidth(p.get_sample_size(self.audio_format))
                    wf.setframerate(self.sample_rate)
                    wf.writeframes(b''.join(frames))
                
                # Verify the file was created
                if not os.path.exists(temp_filename) or os.path.getsize(temp_filename) == 0:
                    raise Exception("Failed to save audio data")
                
                # Fingerprint and identify
                self._identify_song(temp_filename)
                
            except Exception as e:
                logger.error(f"Error during recording stream: {e}")
                # Fall back to simulation mode for demo purposes
                self._use_simulation_mode()
            
        except Exception as e:
            logger.error(f"Error during recording: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Show error message with helpful details
            self.current_metadata = {
                'title': "Error recording audio",
                'artist': f"Error: {str(e)}",
                'album': "Try simulation mode with /test-recognition",
                'artwork': None,
                'background_color': "#121212"
            }
            
        finally:
            # Clean up resources
            if stream:
                try:
                    stream.stop_stream()
                    stream.close()
                except:
                    pass
                    
            if p:
                try:
                    p.terminate()
                except:
                    pass
                    
            if temp_filename and os.path.exists(temp_filename):
                try:
                    os.unlink(temp_filename)
                except:
                    pass

    def _identify_song(self, filename):
        """Identify a song from an audio file using AcoustID."""
        try:
            results = acoustid.match(self.api_key, filename)
            
            for score, recording_id, title, artist in results:
                if score < 0.5:  # Skip low confidence matches
                    continue
                    
                logger.info(f"Match found: {title} by {artist} (score: {score})")
                
                # Get detailed info from MusicBrainz
                recording = musicbrainzngs.get_recording_by_id(
                    recording_id,
                    includes=["artists", "releases"]
                )
                
                recording_data = recording["recording"]
                album = None
                album_id = None
                
                if "release-list" in recording_data and recording_data["release-list"]:
                    release = recording_data["release-list"][0]
                    album = release.get("title", "Unknown Album")
                    album_id = release.get("id")
                
                # Update metadata
                metadata = {
                    'title': title,
                    'artist': artist,
                    'album': album,
                    'artwork': None,
                    'background_color': "#121212"
                }
                
                # Try to get album art
                if album_id:
                    try:
                        cover_art_url = f"http://coverartarchive.org/release/{album_id}/front"
                        response = requests.get(cover_art_url, timeout=5)
                        
                        if response.status_code == 200:
                            # Save artwork
                            artwork_filename = f"album_{album_id}.jpg"
                            artwork_path = os.path.join(self.static_folder, 'artwork', artwork_filename)
                            
                            with open(artwork_path, 'wb') as f:
                                f.write(response.content)
                                
                            # Get dominant color for background
                            color_thief = ColorThief(BytesIO(response.content))
                            dominant_color = color_thief.get_color(quality=1)
                            background_color = "#{:02x}{:02x}{:02x}".format(*dominant_color)
                            
                            metadata['artwork'] = f"/static/artwork/{artwork_filename}"
                            metadata['background_color'] = background_color
                    except Exception as e:
                        logger.error(f"Error getting album art: {e}")
                
                # Update current metadata
                self.current_metadata = metadata
                return
                
            logger.info("No confident match found")
                
        except Exception as e:
            logger.error(f"Error identifying song: {e}")
            # Show error instead of simulation
            self.current_metadata = {
                'title': "Error identifying music",
                'artist': str(e),
                'album': None,
                'artwork': None,
                'background_color': "#121212"
            }

    def _use_simulation_mode(self):
        """Use simulation mode when no microphone is available."""
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
                'artwork': '/static/artwork/default_album.svg',  # Use default artwork
                'background_color': "#121212"  # Default dark background
            }
            
            # Try to get album art if possible
            if song['album_id']:
                try:
                    cover_art_url = f"http://coverartarchive.org/release/{song['album_id']}/front"
                    response = requests.get(cover_art_url, timeout=5)
                    
                    if response.status_code == 200:
                        # Save artwork
                        artwork_filename = f"album_{song['album_id']}.jpg"
                        artwork_path = os.path.join(self.static_folder, 'artwork', artwork_filename)
                        
                        with open(artwork_path, 'wb') as f:
                            f.write(response.content)
                            
                        # Get dominant color for background
                        color_thief = ColorThief(BytesIO(response.content))
                        dominant_color = color_thief.get_color(quality=1)
                        background_color = "#{:02x}{:02x}{:02x}".format(*dominant_color)
                        
                        metadata['artwork'] = f"/static/artwork/{artwork_filename}"
                        metadata['background_color'] = background_color
                    else:
                        logger.info(f"No cover art found for album: {song['album_id']}")
                except Exception as e:
                    logger.error(f"Error getting album art in simulation: {e}")
            
            # Update the current metadata
            self.current_metadata = metadata
            logger.info(f"Updated metadata with simulated song: {song['title']} by {song['artist']}")
            
        except Exception as e:
            logger.error(f"Error in simulation mode: {e}")
            
    def trigger_simulation(self):
        """Manually trigger the simulation mode for testing."""
        logger.info("Manual simulation triggered via /test-recognition endpoint")
        # Create flag file to enable simulation mode for future runs
        try:
            with open('.simulation_mode', 'w') as f:
                f.write('1')
            logger.info("Created .simulation_mode file for future runs")
        except Exception as e:
            logger.error(f"Error creating simulation flag file: {e}")
            
        # Run simulation immediately
        self._use_simulation_mode()
        return True