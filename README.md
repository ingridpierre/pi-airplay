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

## License

[License information to be determined]