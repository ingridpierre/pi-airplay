# Pi-DAD: Raspberry Pi Digital Audio Display

## Troubleshooting

### Shairport-sync Issues

If shairport-sync isn't starting properly:

1. **Check the permissions**: Run `sudo chmod 666 /tmp/shairport-sync-metadata` to ensure proper pipe permissions.

2. **Check for stale PID files**: Run `sudo find /var/run /run -name "shairport*" -delete` to remove stale PID files.

3. **Verify installation**: Run `shairport-sync -V` to check if it's installed and get the version number.

4. **Try a simpler command**: Run `sudo shairport-sync -a "Pi-DAD" -o alsa` for a basic configuration without metadata.

5. **Check for conflicts**: Run `sudo systemctl status shairport-sync` to see if the system service is active and potentially conflicting.

6. **Appropriate shutdown**: Always use `sudo pkill shairport-sync` to stop existing processes before starting new ones.

7. **Check IQaudio DAC**: If using IQaudio DAC, ensure it appears in `aplay -l` output.

### AcoustID API Key Setup

To use the music recognition feature:

1. Get an API key from [AcoustID](https://acoustid.org/login).
2. Save it to any of these locations:
   - `.acoustid_api_key` in the Pi-DAD directory
   - `~/.acoustid_api_key` in your home directory
   - `/etc/acoustid_api_key` system-wide
   - `config/acoustid_api_key` in the Pi-DAD config directory
3. Alternatively, use the setup page at http://[pi-ip]:5000/setup

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

# Make the installation script executable
chmod +x install_pi_dad.sh

# Run the installation script
sudo ./install_pi_dad.sh
```

During installation:
1. You'll be asked to choose between system-wide or virtual environment installation
2. You'll be prompted to enter your AcoustID API key (optional, but required for music recognition)

The script handles:
- Installing all required system dependencies
- Setting up a Python virtual environment (to avoid "externally-managed-environment" errors)
- Configuring shairport-sync
- Creating and enabling the systemd service
- Setting up the application to start automatically at boot

### Manual Installation

If you prefer to install components manually:

1. Install required system packages:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3 python3-pip python3-venv ffmpeg libasound2-dev portaudio19-dev shairport-sync
   ```

2. Create a directory for the application and copy files:
   ```bash
   sudo mkdir -p /opt/pi-dad
   sudo cp -r app.py utils static templates /opt/pi-dad/
   sudo chown -R $(whoami):$(whoami) /opt/pi-dad
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   sudo python3 -m venv /opt/pi-dad-venv
   sudo /opt/pi-dad-venv/bin/pip install --upgrade pip
   sudo /opt/pi-dad-venv/bin/pip install flask "flask-socketio>=5.0.0" pyaudio requests pyacoustid colorthief musicbrainzngs pillow eventlet
   ```

4. Configure shairport-sync:
   ```bash
   sudo cp config/shairport-sync.conf /etc/shairport-sync.conf
   sudo systemctl restart shairport-sync
   ```

5. Create metadata pipe:
   ```bash
   sudo mkfifo /tmp/shairport-sync-metadata
   sudo chmod 666 /tmp/shairport-sync-metadata
   ```

6. Create systemd service:
   ```bash
   sudo bash -c 'cat > /etc/systemd/system/pi-dad.service << EOL
   [Unit]
   Description=Pi-DAD - Raspberry Pi Digital Audio Display
   After=network.target shairport-sync.service

   [Service]
   ExecStart=/opt/pi-dad-venv/bin/python /opt/pi-dad/app.py
   WorkingDirectory=/opt/pi-dad
   Restart=always
   RestartSec=5
   User=$(whoami)
   Group=$(whoami)
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   EOL'
   ```

7. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable pi-dad.service
   sudo systemctl start pi-dad.service
   ```

8. Set up your AcoustID API key (optional):
   ```bash
   sudo bash -c 'echo "YOUR_API_KEY" > /etc/acoustid_api_key'
   sudo chmod 644 /etc/acoustid_api_key
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

- **"externally-managed-environment" Error**: If you see this error during installation, it means your Python installation is managed by the system package manager. Our installation script handles this by using virtual environments.

- **"Invalid user: 'pi:pi'" Error**: This occurs if your username is not "pi" (the default Raspberry Pi username). We've updated the installation script to automatically detect your username, so download the latest version. If you still encounter this error, modify the script to replace "pi" with your actual username:
  ```bash
  # Find all instances of "pi:pi" in the install script and replace with your username
  sed -i 's/pi:pi/yourusername:yourusername/g' install_pi_dad.sh
  ```

- **"ModuleNotFoundError: No module named 'flask_socketio'"**: This means the Flask-SocketIO package is missing. Install it with:
  ```bash
  # If using virtual environment (recommended):
  /opt/pi-dad-venv/bin/pip install "flask-socketio>=5.0.0" eventlet
  
  # Or if using system Python (not recommended):
  pip3 install "flask-socketio>=5.0.0" eventlet
  ```
  The simplest solution is to run the application with `./start_pi_dad.sh` which will detect and offer to install missing dependencies.

- **Metadata Pipe Issues**: If you encounter problems with AirPlay metadata, check that the metadata pipe exists with the correct permissions:
  ```bash
  sudo mkfifo /tmp/shairport-sync-metadata
  sudo chmod 666 /tmp/shairport-sync-metadata
  ```

- **No Sound**: Ensure your audio device is properly configured in Raspberry Pi OS. You may need to set your audio output device using `raspi-config`.

- **ALSA Errors (error -524 or Unknown PCM)**: These are related to audio device configuration issues. Create or update your ALSA configuration:
  ```bash
  # Create or edit ALSA config file
  sudo nano /etc/asound.conf
  
  # Add these lines (change the card number to match your USB audio device)
  # You can find your card number with 'arecord -l'
  pcm.!default {
      type hw
      card 4  # Replace with your actual card number
  }
  
  ctl.!default {
      type hw
      card 4  # Should match the card number above
  }
  ```

- **Music Recognition Not Working**: Make sure you've set up your AcoustID API key (via the installation script or the web interface at `/setup`). Also check that your microphone is properly connected and recognized by the system:
  ```bash
  # List audio input devices
  arecord -l
  
  # Test microphone recording (replace X with your card number)
  arecord -D hw:X,0 -d 5 -f cd test.wav
  ```

- **Service Won't Start**: Check the service status and logs with:
  ```bash
  sudo systemctl status pi-dad
  sudo journalctl -u pi-dad -f
  ```

## License

This project is licensed under the MIT License - see the LICENSE file for details.