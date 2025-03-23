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

For newer versions of Raspberry Pi OS (Bullseye or Bookworm), you'll need to use a virtual environment to avoid the "externally-managed-environment" error:

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

If you're using an older version of Raspberry Pi OS and prefer system-wide installation, you can try:

```bash
sudo apt update
sudo apt install -y python3-flask python3-flask-socketio python3-eventlet python3-pyaudio python3-numpy python3-pydub python3-requests python3-sounddevice python3-pillow

# Install packages that aren't available via apt
sudo pip3 install pyacoustid musicbrainzngs colorthief librosa
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
git clone https://github.com/yourusername/music-display.git
cd music-display

# Create required directories if they don't exist
mkdir -p static/artwork
```

### 7. Set Up the Web Interface Service

```bash
# Create log file with appropriate permissions
sudo touch /var/log/music-display.log
sudo chown pi:pi /var/log/music-display.log

# Copy the service file
sudo cp config/music-display.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable music-display
sudo systemctl start music-display

# Verify service status
sudo systemctl status music-display
```

### 8. Configure Chromium to Start in Kiosk Mode

```bash
# Create autostart directory if it doesn't exist
mkdir -p ~/.config/autostart

# Create the autostart file
cat > ~/.config/autostart/chromium.desktop << EOF
[Desktop Entry]
Type=Application
Name=Music Display Kiosk
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
sudo systemctl status music-display

# View web interface logs
sudo journalctl -u music-display -n 50

# Verify the web server is running
curl http://localhost:5000
```

To exit kiosk mode if needed: press Alt+F4