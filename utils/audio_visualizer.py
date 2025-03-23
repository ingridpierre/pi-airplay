import numpy as np
import time
import threading
import logging
import subprocess
import os
from collections import deque
import random

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AudioVisualizer:
    def __init__(self, buffer_size=5, sample_rate=44100, block_size=2048, channels=1):
        """
        Initialize the audio visualizer with the given parameters.
        
        Args:
            buffer_size: Size of the audio buffer in seconds
            sample_rate: Audio sample rate (Hz)
            block_size: Size of audio blocks to process
            channels: Number of audio channels (1 for mono, 2 for stereo)
        """
        self.sample_rate = sample_rate
        self.block_size = block_size
        self.channels = channels
        self.buffer_size = buffer_size
        
        # Store visualization data
        self.spectrum_data = np.zeros(64)  # Simple fixed-size spectrum
        self.rms_energy = 0
        self.is_running = False
        self.lock = threading.Lock()
        self.thread = None
        self.last_update_time = 0
        self.update_interval = 0.1  # 100ms update interval
        
        # Audio input device (Adafruit USB microphone)
        self.audio_device = "plughw:1,0"  # Default name for USB audio device
        
        # Status tracking
        self._is_playing = False
        
        logger.info(f"AudioVisualizer initialized with sample_rate={sample_rate}, block_size={block_size}")
    
    def start(self):
        """Start the audio capture and analysis."""
        if self.is_running:
            logger.warning("AudioVisualizer is already running")
            return
        
        logger.info("Starting AudioVisualizer")
        self.is_running = True
        self.thread = threading.Thread(target=self._audio_capture_thread)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        """Stop the audio capture and analysis."""
        logger.info("Stopping AudioVisualizer")
        self.is_running = False
        if self.thread:
            self.thread.join(timeout=1.0)
    
    def _detect_audio_device(self):
        """Attempt to detect the USB audio device."""
        try:
            # Look for USB audio devices
            result = subprocess.run(['arecord', '-l'], capture_output=True, text=True)
            lines = result.stdout.split('\n')
            
            # Look for lines containing 'USB Audio' or similar
            for line in lines:
                if 'USB Audio' in line or 'USB PnP' in line:
                    parts = line.split(':')
                    if len(parts) >= 2:
                        card_num = parts[0].strip().split(' ')[-1]
                        device_num = parts[1].strip().split(',')[0]
                        self.audio_device = f"plughw:{card_num},{device_num}"
                        logger.info(f"Detected USB audio device: {self.audio_device}")
                        return True
                        
            logger.warning("No USB audio device detected, using default")
            return False
        except Exception as e:
            logger.error(f"Error detecting audio device: {e}")
            return False
    
    def _audio_capture_thread(self):
        """Thread for continuous audio capture and analysis."""
        try:
            logger.info("Audio capture thread started")
            
            # Detect the audio device
            self._detect_audio_device()
            
            # In our simplified version, since we're facing PortAudio issues,
            # we'll simulate audio analysis for now until we can properly integrate
            # with the hardware on the Raspberry Pi
            while self.is_running:
                # Update visualization at regular intervals
                current_time = time.time()
                if current_time - self.last_update_time >= self.update_interval:
                    self._simulate_audio_analysis()
                    self.last_update_time = current_time
                time.sleep(0.01)  # Small sleep to reduce CPU usage
        
        except Exception as e:
            logger.error(f"Error in audio capture thread: {e}")
            self.is_running = False
    
    def _simulate_audio_analysis(self):
        """
        Simulate audio analysis with semi-realistic values.
        This is a temporary solution until direct audio capture is fixed.
        """
        with self.lock:
            try:
                # Use the flag set by the app based on AirPlay status
                if self._is_playing:
                    # Generate more pronounced spectrum for "playing" state
                    # Base shape with lower frequencies having higher amplitude
                    base_spectrum = np.array([max(0, 1 - (i / 64)) for i in range(64)]) * 40
                    
                    # Add randomness to simulate music
                    noise = np.random.normal(0, 10, 64)
                    
                    # Add some "beats" - occasional spikes in the lower frequencies
                    if random.random() < 0.2:  # 20% chance of a "beat"
                        beat_intensity = random.uniform(15, 30)
                        beat_range = random.randint(3, 10)
                        base_spectrum[:beat_range] += beat_intensity
                    
                    # Update spectrum with our simulated data
                    self.spectrum_data = base_spectrum + noise
                    
                    # Update RMS energy (volume level)
                    self.rms_energy = random.uniform(0.3, 0.7)
                else:
                    # Generate minimal activity for "not playing" state
                    base_spectrum = np.array([max(0, 0.5 - (i / 64)) for i in range(64)]) * 15
                    noise = np.random.normal(0, 3, 64)
                    self.spectrum_data = base_spectrum + noise
                    self.rms_energy = random.uniform(0.05, 0.2)
            except Exception as e:
                logger.error(f"Error in audio simulation: {e}")
                # Fall back to minimal visualization
                self.spectrum_data = np.random.normal(0, 5, 64)
                self.rms_energy = 0.1
    
    def get_visualization_data(self):
        """Get the current visualization data."""
        with self.lock:
            # Scale spectrum data to dB-like range similar to real audio
            # Real spectrum would be in range like -80 to 0 dB
            scaled_spectrum = self.spectrum_data - 60
            
            result = {
                'rms_energy': float(self.rms_energy) if self.rms_energy is not None else 0,
                'spectrum': scaled_spectrum.tolist() if self.spectrum_data is not None else [],
                'timestamp': time.time()
            }
        return result