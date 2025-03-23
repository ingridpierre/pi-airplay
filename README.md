# AirPlay Web Interface Project

A Raspberry Pi-based AirPlay receiver with a web interface for music playback through IQaudio DAC, designed for seamless audio streaming and local control.

## Overview

This project provides a complete solution for turning a Raspberry Pi into an AirPlay receiver with an elegant web interface to control and display music playback. The system uses Shairport-Sync for AirPlay functionality and a custom Flask web interface for control and monitoring.

## Key Features

- AirPlay audio streaming reception via Shairport-Sync
- Real-time music metadata display (artist, album, track)
- Web-based interface for control and display
- Optimized for IQaudio DAC hardware
- Designed for Raspberry Pi with kiosk mode display option

## Technology Stack

- **OS**: Raspberry Pi OS
- **Backend**: Python Flask with Flask-SocketIO
- **AirPlay Receiver**: Shairport-Sync 
- **Frontend**: HTML, CSS, JavaScript
- **Display**: Chromium Browser in Kiosk Mode
- **Audio**: IQaudio DAC hardware

## Project Structure

- `/app.py` - Main Flask application
- `/utils/` - Helper utilities
  - `/utils/audio_control.py` - Audio control and metadata handling
  - `/utils/metadata_reader.py` - Reading metadata from Shairport-Sync
- `/static/` - Static assets (CSS, JavaScript)
- `/templates/` - HTML templates
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