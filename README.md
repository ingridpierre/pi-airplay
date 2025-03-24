# Pi-AirPlay

A Raspberry Pi-powered AirPlay receiver that transforms music streaming into an interactive, immersive digital audio platform. Designed to provide a smart, engaging music experience with advanced device management and multimedia integration.

## Features

- AirPlay audio streaming using shairport-sync
- Web interface showing album artwork, track info, and visualization
- Automatic detection of AirPlay devices
- IQAudio DAC support for high-quality audio playback

## Installation

### Quick Install

```bash
# Clone the repository
git clone https://github.com/yourusername/pi-airplay.git
cd pi-airplay

# Make install script executable
chmod +x install_pi_airplay_simple.sh

# Run the installer
./install_pi_airplay_simple.sh
```

### Manual Installation

1. **Install required system packages**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y build-essential git autoconf automake libtool libdaemon-dev libasound2-dev libpopt-dev libconfig-dev avahi-daemon libavahi-client-dev libssl-dev libsoxr-dev
   ```

2. **Install or verify shairport-sync**:
   ```bash
   # Check if shairport-sync is already installed
   which shairport-sync
   
   # If not installed, install it:
   git clone https://github.com/mikebrady/shairport-sync.git
   cd shairport-sync
   autoreconf -fi
   ./configure --with-alsa --with-avahi --with-ssl=openssl --with-metadata --with-soxr
   make
   sudo make install
   ```

3. **Set up the service**:
   ```bash
   # Copy the service file to systemd directory
   sudo cp pi-airplay.service /etc/systemd/system/
   
   # Make the startup script executable
   chmod +x start_pi_airplay.sh
   
   # Reload systemd
   sudo systemctl daemon-reload
   
   # Enable service to start on boot
   sudo systemctl enable pi-airplay.service
   
   # Start the service
   sudo systemctl start pi-airplay.service
   ```

4. **Check service status**:
   ```bash
   sudo systemctl status pi-airplay.service
   ```

## Troubleshooting

If you encounter issues with the service not starting properly:

1. Check the service logs:
   ```bash
   sudo journalctl -u pi-airplay.service
   ```

2. Ensure the startup script has execute permissions:
   ```bash
   chmod +x start_pi_airplay.sh
   ```

3. Run the services manually for debugging:
   ```bash
   # The manual approach works like this - this is what our service does for you:
   shairport-sync
   python3 app_airplay.py --port 8000 --host 0.0.0.0
   ```

4. Check that the metadata pipe exists and has correct permissions:
   ```bash
   ls -la /tmp/shairport-sync-metadata
   # Should show permissions like: prw-rw-rw-
   
   # If needed, fix permissions:
   mkfifo /tmp/shairport-sync-metadata
   chmod 666 /tmp/shairport-sync-metadata
   ```

## Accessing the Interface

The web interface is available at:
```
http://[raspberry-pi-ip-address]:8000
```

Connect to your Pi-AirPlay device via AirPlay from any compatible device (iOS, macOS, etc.) to start streaming music.

## License

[Your License Information]