# Music Display with AirPlay and Recognition: Development Log

## Project Overview
A Raspberry Pi-powered system that bridges modern and analog music experiences, functioning as an AirPlay receiver while also using a microphone to recognize songs from any audio source.

**Stack:**
- Raspberry Pi OS
- Python Flask with Flask-SocketIO
- Shairport-Sync for AirPlay functionality
- AcoustID/Chromaprint for audio fingerprinting
- MusicBrainz for metadata retrieval
- IQaudio DAC hardware
- USB Microphone (Adafruit)

## Development History

### [2025-03-23] Installation Improvements and Pi Compatibility
- Updated installation script to handle "externally-managed-environment" error on newer Raspberry Pi OS
- Implemented virtual environment approach for both installation types to ensure compatibility
- Enhanced file copying and permissions handling in the installation process
- Updated README with detailed installation instructions and troubleshooting section
- Improved error handling for common installation issues
- Added simulation mode testing via the /test-recognition endpoint

### [2025-03-22] Major Redesign: Adding Music Recognition
- Pivoted from purely AirPlay metadata display to including microphone-based song recognition
- Installed necessary audio fingerprinting and recognition libraries (acoustid, pydub, pyaudio, musicbrainzngs)
- Created new music_recognition.py utility to identify songs from microphone input
- Developed a simplified, modern interface with focus on large album art display and minimal text
- Updated server to run on port 5000 for Replit compatibility
- Created a clean SVG placeholder for unrecognized music
- Added AcoustID API key setup page for music recognition configuration

### [2025-03-22] Initial Development Log
- Created development log file to track project progress, design decisions and key insights
- Project currently has a Flask web server with routes for health checks and displaying metadata
- Audio control functionality implemented through AudioController class
- Set up infrastructure for reading metadata from shairport-sync
- Added development log update utility script to help maintain consistent progress tracking
- Created update_log.py utility script to simplify maintaining the development log across multiple coding sessions
- Created README.md with comprehensive project overview and instructions for using the development log utility
- Created sync_log.py utility to generate summaries for sharing across multiple assistant conversations
- Updated README with instructions for using sync_log.py utility

## Design Decisions
- Hybrid approach combining AirPlay streaming with microphone-based recognition provides flexibility for both digital and analog sources
- Clean, minimal interface design with focus on album art creates a visually pleasing display
- Dark theme with dynamic background color tinting based on album art enhances visual appeal
- Using Inter font for all text elements provides a modern, clean typography
- Microphone recognition triggered periodically rather than continuously to reduce CPU usage
- Socket.IO for real-time updates without page refreshes
- Separation of AirPlay control and music recognition into distinct modules for maintainability
- Virtual environment based installation to ensure compatibility with newer Raspberry Pi OS versions
- Comprehensive installation script to streamline deployment on various Pi configurations

## Key Configuration Notes
- Shairport-sync configured to write metadata to a named pipe
- IQaudio DAC requires specific ALSA configuration
- Web interface runs on port 5000
- System services configured for auto-start on boot via systemd
- Python dependencies isolated in virtual environment to avoid conflicts
- Application files installed to /opt/pi-dad for consistent location
- AcoustID API key required for music recognition functionality (stored in /etc/acoustid_api_key)
- USB microphone needed for analog music recognition
- Simulation mode available for testing without microphone via /test-recognition endpoint

## Future Enhancements
- Add volume control for AirPlay and system output
- Implement track history to show recently played songs
- Create a mobile-friendly remote control interface
- Add music visualization options
- Support for Apple Music and Spotify web API integration for richer metadata
- Improve music recognition accuracy with longer sample durations
- Add option to save favorite/recognized tracks to a playlist

## Technical References
- [Shairport-sync Metadata](https://github.com/mikebrady/shairport-sync/blob/master/METADATA.md)
- [AcoustID Documentation](https://acoustid.org/webservice)
- [MusicBrainz API Documentation](https://musicbrainz.org/doc/MusicBrainz_API)
- [Flask-SocketIO Documentation](https://flask-socketio.readthedocs.io/)