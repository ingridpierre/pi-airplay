# Setup Instructions for Music Display with AirPlay and Recognition

This guide will help you set up the complete music display system on a Raspberry Pi with both AirPlay streaming capabilities and music recognition from analog sources.

## Hardware Requirements

- Raspberry Pi (3B+ or 4 recommended)
- IQaudio DAC for high-quality audio output
- USB microphone (Adafruit USB microphone recommended)
- Display with HDMI input
- MicroSD card (16GB+ recommended)
- Power supply for Raspberry Pi
- Speakers connected to IQaudio DAC

## Software Setup

### 1. Prepare the Raspberry Pi

Start with a fresh installation of Raspberry Pi OS (Lite or Desktop):

```bash
# Update the system
sudo apt update
sudo apt upgrade -y

# Install required dependencies
sudo apt install -y python3 python3-pip git ffmpeg alsa-utils chromaprint-tools libchromaprint-dev libffi-dev portaudio19-dev chromium-browser
```

### 2. Set up Shairport-Sync for AirPlay

```bash
# Install Shairport-Sync
sudo apt install -y shairport-sync

# Copy config files
sudo cp config/shairport-sync.conf /etc/shairport-sync.conf
sudo cp config/asound.conf /etc/asound.conf

# Enable and start the service
sudo systemctl enable shairport-sync
sudo systemctl start shairport-sync
```

### 3. Configure the IQaudio DAC

```bash
# Check if the DAC is recognized
aplay -l | grep IQaudIO

# If not recognized, add to config.txt and reboot
sudo sh -c "echo 'dtoverlay=iqaudio-dacplus' >> /boot/config.txt"
sudo reboot
```

### 4. Install Python Dependencies

There are two approaches for handling dependencies on newer Raspberry Pi OS versions (Bullseye or Bookworm) that have the "externally-managed-environment" restriction:

#### Option 1: Virtual Environment (Recommended)

This keeps dependencies isolated and won't interfere with system packages:

```bash
# Install required build dependencies first
sudo apt install -y build-essential libffi-dev libasound2-dev portaudio19-dev ffmpeg libchromaprint-dev pkg-config libopenblas-dev

# Create a virtual environment (important for newer Pi OS versions)
sudo apt install -y python3-venv python3-dev
python3 -m venv .venv
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install packages one by one for better tracking
pip install flask flask-socketio eventlet
pip install numpy  # Install first as many packages depend on it
pip install pillow requests
pip install pyaudio
pip install pydub
pip install musicbrainzngs
pip install colorthief

# Install slower/larger packages last
pip install sounddevice
pip install librosa  # This might take a while on Raspberry Pi
pip install pyacoustid
```

When using this option, the included `start_music_display.sh` script will handle activating the virtual environment when the service starts.

#### Option 2: System-wide Installation Script

If you prefer installing packages system-wide, you can use the included script that works around the "externally-managed-environment" restriction:

```bash
# Make the script executable
chmod +x system_install_dependencies.sh

# Run the script (may take some time)
./system_install_dependencies.sh
```

If you use this option, you should modify the `config/music-display.service` file to use system Python instead of the virtual environment by changing the `ExecStart` line to:

```
ExecStart=/usr/bin/python3 /home/pi/music-display/app.py
```

### 5. Get an AcoustID API Key

The music recognition feature requires an AcoustID API key:

1. Go to [acoustid.org/login](https://acoustid.org/login) and create an account
2. After logging in, go to [acoustid.org/applications](https://acoustid.org/applications)
3. Register a new application, providing a name (e.g., "Pi Music Display") and a version
4. Copy the API key for later use

### 6. Clone and Configure the Application

```bash
# Clone the repository
git clone https://github.com/yourusername/Pi-DAD.git
cd Pi-DAD

# Create required directories if they don't exist
mkdir -p static/artwork
```

### 7. Set Up the Web Interface Service

We've included a service setup script that automatically detects whether you're using a virtual environment or system Python and configures the service accordingly:

```bash
# Make the script executable
chmod +x start_music_display.sh system_service.sh

# Run the service setup script
./system_service.sh
```

The script will:
1. Detect if you're using a virtual environment
2. Create the appropriate service file
3. Install and start the service
4. Show you the current status

If you want to view the logs at any time:

```bash
# View logs from the service
sudo journalctl -u pi-dad -f
```

**Note:** If you prefer manual setup, the service file is available at `config/pi-dad.service`. You can edit it as needed and install it with:

```bash
sudo cp config/pi-dad.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable pi-dad
sudo systemctl start pi-dad
```

### 8. Configure Chromium to Start in Kiosk Mode

```bash
# Create autostart directory if it doesn't exist
mkdir -p ~/.config/autostart

# Create the autostart file
cat > ~/.config/autostart/chromium.desktop << EOF
[Desktop Entry]
Type=Application
Name=Pi-DAD AirPlay Display
Exec=chromium-browser --kiosk --disable-restore-session-state http://localhost:5000
EOF
```

### 9. Configure Display Settings

```bash
# Prevent screen from going blank
sudo raspi-config nonint do_blanking 1

# For console-based systems, add to /etc/xdg/lxsession/LXDE-pi/autostart:
@xset s off
@xset -dpms
@xset s noblank
```

### 10. Final Configuration and Testing

```bash
# Reboot to apply all changes
sudo reboot
```

After rebooting:

1. The system will start the AirPlay receiver service (shairport-sync)
2. The Flask application will run
3. Chromium will open in kiosk mode showing the music display interface
4. When you first open the interface, you'll need to enter your AcoustID API key in the setup page

## Usage Instructions

- To display music via AirPlay: Simply select your Raspberry Pi from the AirPlay devices list on your iPhone, iPad, or Mac
- To recognize music from analog sources: Play music near the USB microphone, and the system will attempt to identify it

## Troubleshooting

### AirPlay Issues

```bash
# Check shairport-sync status
sudo systemctl status shairport-sync

# Check logs for errors
sudo journalctl -u shairport-sync -n 50

# Verify AirPlay is being advertised
avahi-browse -a | grep AirPlay
```

Common AirPlay issues:
- If shairport-sync fails to start: Check permissions with `sudo usermod -aG audio shairport-sync`
- If device doesn't appear in AirPlay list: Ensure devices are on the same network

### Audio Recognition Issues

```bash
# Check if the USB microphone is detected
arecord -l | grep USB

# Test microphone recording
arecord -d 5 -f cd test.wav

# Check if chromaprint/acoustid tools are working
fpcalc test.wav
```

### Web Interface Issues

```bash
# Check web interface status
sudo systemctl status pi-dad

# View web interface logs
sudo journalctl -u pi-dad -n 50

# Verify the web server is running
curl http://localhost:5000
```

To exit kiosk mode if needed: press Alt+F4