# Pi-DAD: Raspberry Pi Digital Audio Display

A Raspberry Pi-powered AirPlay receiver that transforms music streaming into an interactive, user-friendly experience. The system provides seamless audio playback through your audio hardware with a modern web interface and intuitive music recognition capabilities.

## Features

- **AirPlay Receiver**: Display metadata from AirPlay streaming sources
- **Music Recognition**: Identify songs playing from analog sources using a microphone
- **Clean Interface**: Minimalist display with album art and track information
- **Easy Setup**: Simple installation process with minimal dependencies

## Requirements

- Raspberry Pi (3 or newer recommended)
- Raspberry Pi OS (Bullseye or newer)
- Audio output hardware (e.g., IQaudio DAC or USB audio device)
- USB microphone for music recognition (optional)
- AcoustID API key for music recognition (get one at [acoustid.org](https://acoustid.org/))

## Installation

### Simple Method (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/pi-dad.git
cd pi-dad

# Run the installation script
sudo ./install_pi_dad.sh
```

During installation, you'll be prompted to enter your AcoustID API key. This is required for the music recognition feature to work properly.

### Manual Installation

If you prefer to install components manually:

1. Install required system packages:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip ffmpeg libasound2-dev portaudio19-dev shairport-sync
   ```

2. Install Python dependencies:
   ```bash
   pip3 install flask flask-socketio pyaudio requests pyacoustid colorthief musicbrainzngs
   ```

3. Configure shairport-sync:
   ```bash
   sudo cp config/shairport-sync.conf /etc/shairport-sync.conf
   ```

4. Install systemd service:
   ```bash
   sudo cp config/pi-dad.service.system /etc/systemd/system/pi-dad.service
   sudo systemctl daemon-reload
   sudo systemctl enable pi-dad.service
   ```

5. Set up your AcoustID API key:
   ```bash
   echo "YOUR_API_KEY" > .acoustid_api_key
   ```

## Usage

### Starting Pi-DAD

Automatically at boot (recommended):
```bash
sudo systemctl start pi-dad
```

Manually:
```bash
./start_pi_dad.sh
```

### Accessing the Interface

Once Pi-DAD is running, you can access the interface by opening a web browser and navigating to:

```
http://raspberrypi.local:5000
```

Or use the Pi's IP address:

```
http://[your-pi-ip-address]:5000
```

### Testing Music Recognition

You can test the music recognition feature without playing actual music by visiting:

```
http://[your-pi-ip-address]:5000/test-recognition
```

### Setting up AcoustID API Key via Web Interface

Visit the setup page to configure your AcoustID API key:

```
http://[your-pi-ip-address]:5000/setup
```

## Troubleshooting

- **Metadata Pipe Issues**: If you encounter problems with AirPlay metadata, check that the metadata pipe exists with the correct permissions:
  ```bash
  sudo mkfifo /tmp/shairport-sync-metadata
  sudo chmod 666 /tmp/shairport-sync-metadata
  ```

- **No Sound**: Ensure your audio device is properly configured in Raspberry Pi OS.

- **Music Recognition Not Working**: Check that your microphone is properly connected and recognized by the system.

## License

This project is licensed under the MIT License - see the LICENSE file for details.