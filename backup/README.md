# Music Display with AirPlay and Recognition

A Raspberry Pi-powered system that bridges modern and analog music experiences, functioning as an AirPlay receiver while also using a microphone to recognize songs from any audio source.

## Overview

This project creates a beautiful music display system that works in two ways:
1. As an **AirPlay Receiver** for streaming audio from your Apple devices
2. As a **Music Recognition System** that uses a microphone to identify songs being played from analog sources (like vinyl records, cassette tapes, or radio)

The system shows album art, track information, and artist details on a clean, minimal interface designed to look great on a dedicated display.

## Key Features

- **Dual Input Sources**:
  - Wireless AirPlay streaming from Apple devices
  - Microphone-based audio recognition for analog audio sources
- **Clean, Modern Display**:
  - Large album art display
  - Dynamic background colors based on album artwork
  - Minimal text using the elegant Inter font
- **Easy Setup**:
  - Simple configuration process
  - AcoustID-based music recognition with easy API key setup
  - Optimized for Raspberry Pi with IQaudio DAC and USB microphone

## Technology Stack

- **OS**: Raspberry Pi OS
- **Backend**: Python Flask with Flask-SocketIO
- **Audio Processing**:
  - Shairport-Sync for AirPlay functionality
  - AcoustID/Chromaprint for audio fingerprinting
  - MusicBrainz for metadata retrieval
- **Frontend**: HTML5, CSS3, JavaScript
- **Display**: Chromium Browser in Kiosk Mode
- **Hardware**: 
  - Raspberry Pi
  - IQaudio DAC for high-quality audio output
  - USB microphone for audio capture

## Project Structure

- `/app.py` - Main Flask application with both AirPlay and recognition integration
- `/utils/` - Helper utilities
  - `/utils/audio_control.py` - AirPlay audio control
  - `/utils/music_recognition.py` - Microphone-based song recognition
- `/static/` - Static assets
  - `/static/css/main.css` - Clean, modern styling
  - `/static/artwork/` - Album art including default placeholder
- `/templates/` - HTML templates
  - `/templates/display.html` - Main display interface
  - `/templates/setup.html` - AcoustID API key configuration page
- `/config/` - Configuration files for system services
- `/development_log.md` - Development history and progress tracking

## Development Log

The `development_log.md` file in this repository tracks the history, design decisions, and progress of this project. To view the latest development status and notes, check this file.

### Using the Development Log Utility

This project includes utility scripts for maintaining and sharing the development log:

```bash
# Add a new entry to the log
python update_log.py entry "Description of what was implemented or changed"

# Add a new design decision
python update_log.py decision "Description of the design decision and its rationale"

# Update the future enhancements section
python update_log.py enhancement "- Enhancement 1\n- Enhancement 2\n- Enhancement 3"

# Generate a summary of recent changes (last 7 days by default)
python sync_log.py

# Generate a summary of changes for a specific number of days
python sync_log.py 14  # Shows changes from the last 14 days
```

The sync_log.py utility is particularly useful when working with multiple Replit assistant windows, as it provides a concise summary of recent changes, design decisions, and planned enhancements that can be copied and pasted to maintain context across sessions.

## Installation & Setup

Please refer to `setup_instructions.md` for detailed setup and installation instructions for Raspberry Pi deployment.

### Setting up AcoustID API Key

The music recognition feature requires an AcoustID API key. You can obtain one for free from [acoustid.org](https://acoustid.org/):

1. Create an account at [acoustid.org/login](https://acoustid.org/login)
2. After logging in, go to [acoustid.org/applications](https://acoustid.org/applications)
3. Register a new application (e.g., "Pi Music Display")
4. Copy your API key

There are three ways to set up your API key:

#### Method 1: Using the Setup Script (Recommended)

A setup script is included to easily configure your API key:

```bash
# Set up API key in the local directory
python setup_api_key.py YOUR_API_KEY_HERE

# Or set it up in your user directory (recommended)
python setup_api_key.py --location user YOUR_API_KEY_HERE

# Or set it up system-wide (requires sudo)
sudo python setup_api_key.py --location system YOUR_API_KEY_HERE
```

#### Method 2: Using the Web Interface

1. Navigate to the setup page at `http://YOUR_PI_IP:5000/setup`
2. Enter your AcoustID API key in the form
3. Click "Save"

#### Method 3: Manual File Creation

You can manually create a file containing your API key:

```bash
# Option 1: In the project directory
echo "YOUR_API_KEY_HERE" > .acoustid_api_key

# Option 2: In your home directory
echo "YOUR_API_KEY_HERE" > ~/.acoustid_api_key
chmod 600 ~/.acoustid_api_key

# Option 3: System-wide (requires sudo)
echo "YOUR_API_KEY_HERE" | sudo tee /etc/acoustid_api_key
sudo chmod 600 /etc/acoustid_api_key
```

## License

[License information to be determined]