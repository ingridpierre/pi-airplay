#!/usr/bin/env python3
"""
Diagnostic script for audio recording issues with the Pi-DAD system.
This will test microphone access, audio recording, and give detailed error information.
"""

import os
import sys
import time
import wave
import logging
import tempfile
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("audio-diagnostics")

def test_pyaudio_import():
    """Test importing PyAudio"""
    logger.info("Testing PyAudio import...")
    try:
        import pyaudio
        logger.info(f"PyAudio imported successfully (version: {pyaudio.get_version_string()})")
        return True
    except ImportError as e:
        logger.error(f"Failed to import PyAudio: {str(e)}")
        logger.error("Please ensure PyAudio is installed: pip install pyaudio")
        return False
    except Exception as e:
        logger.error(f"Unexpected error importing PyAudio: {str(e)}")
        return False

def list_audio_devices():
    """List all available audio devices"""
    logger.info("Listing available audio devices...")
    
    try:
        import pyaudio
        pa = pyaudio.PyAudio()
        
        logger.info(f"Audio system information:")
        logger.info(f"  Version: {pyaudio.get_version_string()}")
        logger.info(f"  Default input device: {pa.get_default_input_device_info().get('name', 'Unknown') if pa.get_default_input_device_info() else 'None'}")
        
        info = pa.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        
        logger.info(f"Found {numdevices} audio devices:")
        
        for i in range(numdevices):
            device_info = pa.get_device_info_by_index(i)
            name = device_info.get('name')
            max_input_channels = device_info.get('maxInputChannels')
            max_output_channels = device_info.get('maxOutputChannels')
            default_sample_rate = device_info.get('defaultSampleRate')
            
            device_type = []
            if max_input_channels > 0:
                device_type.append("INPUT")
            if max_output_channels > 0:
                device_type.append("OUTPUT")
            
            logger.info(f"  Device {i}: {name} ({', '.join(device_type)})")
            logger.info(f"    Max channels: {max_input_channels} in, {max_output_channels} out")
            logger.info(f"    Default sample rate: {default_sample_rate} Hz")
        
        pa.terminate()
        return True
    except Exception as e:
        logger.error(f"Error listing audio devices: {str(e)}")
        return False

def test_audio_recording(device_index=None, duration=5):
    """
    Test audio recording with PyAudio
    
    Args:
        device_index: Optional device index to use
        duration: Recording duration in seconds
    """
    logger.info(f"Testing audio recording (duration: {duration}s)...")
    
    try:
        import pyaudio
        
        # Create temp file for recording
        temp_file = tempfile.mktemp(suffix='.wav')
        
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 1
        RATE = 44100
        
        pa = pyaudio.PyAudio()
        
        # If no device specified, try to find one
        if device_index is None:
            # First try to find a USB device
            for i in range(pa.get_device_count()):
                device_info = pa.get_device_info_by_index(i)
                if (device_info.get('maxInputChannels', 0) > 0 and 
                    'usb' in device_info.get('name', '').lower()):
                    device_index = i
                    logger.info(f"Found USB audio device: {device_info.get('name')} (index {i})")
                    break
            
            # If no USB device, use default
            if device_index is None:
                device_index = pa.get_default_input_device_info().get('index')
                logger.info(f"Using default input device (index {device_index})")
                
        # Get device info
        device_info = pa.get_device_info_by_index(device_index)
        logger.info(f"Recording from device: {device_info.get('name')}")
        
        # Open stream
        logger.info("Opening audio stream...")
        stream = pa.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=device_index,
            frames_per_buffer=CHUNK
        )
        
        logger.info(f"Recording for {duration} seconds...")
        frames = []
        
        for i in range(0, int(RATE / CHUNK * duration)):
            try:
                data = stream.read(CHUNK)
                frames.append(data)
                
                # Print progress every second
                if i % int(RATE / CHUNK) == 0:
                    logger.info(f"Recording... {i // int(RATE / CHUNK)}s")
                    
            except Exception as e:
                logger.error(f"Error reading audio chunk {i}: {str(e)}")
                break
        
        logger.info("Stopping recording...")
        stream.stop_stream()
        stream.close()
        
        # Save recording
        logger.info(f"Saving recording to {temp_file}...")
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pa.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        pa.terminate()
        
        # Check if file was created and has content
        if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            logger.info(f"Successfully recorded audio to {temp_file} ({os.path.getsize(temp_file)} bytes)")
            return True, temp_file
        else:
            logger.error(f"Recording failed - file is empty or not created")
            return False, None
            
    except Exception as e:
        logger.error(f"Error recording audio: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False, None

def test_arecord():
    """Test recording with arecord (Linux only)"""
    logger.info("Testing recording with arecord...")
    
    try:
        temp_file = tempfile.mktemp(suffix='.wav')
        duration = 3  # seconds
        
        # List available devices
        logger.info("Available recording devices:")
        os.system("arecord -l")
        
        # Try recording
        logger.info(f"Recording {duration} seconds to {temp_file}...")
        result = os.system(f"arecord -d {duration} -f cd {temp_file}")
        
        if result == 0 and os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
            logger.info(f"Successfully recorded with arecord to {temp_file} ({os.path.getsize(temp_file)} bytes)")
            return True, temp_file
        else:
            logger.error(f"arecord failed with exit code {result}")
            return False, None
            
    except Exception as e:
        logger.error(f"Error with arecord test: {str(e)}")
        return False, None

def test_alsa_config():
    """Check ALSA configuration"""
    logger.info("Checking ALSA configuration...")
    
    try:
        # Check asound.conf
        if os.path.exists('/etc/asound.conf'):
            logger.info("Found /etc/asound.conf:")
            with open('/etc/asound.conf', 'r') as f:
                logger.info(f.read())
        else:
            logger.info("No /etc/asound.conf file found")
            
        # Run aplay -L
        logger.info("ALSA device list (aplay -L):")
        os.system("aplay -L")
        
        return True
    except Exception as e:
        logger.error(f"Error checking ALSA config: {str(e)}")
        return False

def run_all_tests():
    """Run all diagnostic tests"""
    logger.info("=== Audio Diagnostic Tests ===")
    logger.info(f"Date/Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info("=" * 40)
    
    # Run tests
    pyaudio_ok = test_pyaudio_import()
    
    if pyaudio_ok:
        list_audio_devices()
        
        # Try recording with PyAudio
        recording_ok, temp_file = test_audio_recording()
        
        # Try different device if first attempt failed
        if not recording_ok:
            logger.info("First recording attempt failed. Trying different device...")
            for device_index in range(10):  # Try first 10 devices
                recording_ok, temp_file = test_audio_recording(device_index=device_index)
                if recording_ok:
                    break
    
    # Test with arecord (Linux command-line tool)
    test_alsa_config()
    arecord_ok, _ = test_arecord()
    
    # Summary
    logger.info("=" * 40)
    logger.info("Diagnostic Summary:")
    logger.info(f"PyAudio import: {'OK' if pyaudio_ok else 'FAILED'}")
    if pyaudio_ok:
        logger.info(f"PyAudio recording: {'OK' if recording_ok else 'FAILED'}")
    logger.info(f"arecord recording: {'OK' if arecord_ok else 'FAILED'}")

if __name__ == "__main__":
    run_all_tests()