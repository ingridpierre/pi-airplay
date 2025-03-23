# Pi-AirPlay

A streamlined AirPlay receiver for Raspberry Pi with IQaudio DAC. Turn your Raspberry Pi into a high-quality AirPlay receiver with a clean web interface showing now playing information.

## Features

* **AirPlay Streaming**: Stream audio wirelessly from Apple devices
* **Album Art Display**: View album artwork, track info, and artist
* **High-Quality Audio**: Works with IQaudio DAC for superior sound quality
* **Simple Web Interface**: Access music information from any device
* **Resource Efficient**: Optimized for Raspberry Pi's limited resources

## Quick Installation (Easy Method)

Simply run the included installation script which will handle everything automatically:

```bash
sudo ./install_pi_airplay.sh
```

The script will:
1. Install all required packages
2. Configure shairport-sync for your audio device
3. Set up systemd services to run at boot
4. Create a desktop shortcut for kiosk mode

Once installed, Pi-AirPlay will start automatically on boot.

## Manual Installation

If you prefer to install components manually:

1. Clone this repository to your Raspberry Pi:
   ```bash
   git clone https://github.com/yourusername/pi-airplay.git
   cd pi-airPlay
   ```

2. Install required packages:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-flask shairport-sync avahi-daemon
   pip3 install flask flask-socketio eventlet pillow
   ```

3. Configure your audio output:
   Make sure your DAC is properly connected and configure shairport-sync to use it.

## Quick Start (Testing)

For testing or development, you can run Pi-AirPlay directly without installation:

```bash
./run_pi_airplay.sh
```

This will start both shairport-sync and the web interface temporarily.

## Usage

### Web Interface Access

Open a browser on any device connected to the same network and navigate to:
```
http://your-raspberry-pi-ip:8000
```

**Important:** Use HTTP, not HTTPS. Make sure to type `http://` at the beginning of the URL.

### AirPlay Streaming

1. On your iPhone/iPad/Mac, connect to the same WiFi network
2. Select the AirPlay icon in Control Center or Music app
3. Choose "Pi-AirPlay" from the list of available devices
4. Start playing music
5. View playback information on the web interface

### Kiosk Mode

For a dedicated display (like a small touchscreen on your Pi):
```bash
chromium-browser --kiosk --app=http://localhost:8000
```

## Troubleshooting

See the [FIXES.md](FIXES.md) file for common issues and solutions.

Common issues:
* **No Audio Output**: Make sure your DAC is correctly configured
* **AirPlay Device Not Found**: Check that avahi-daemon is running
* **Port Conflict**: Use the alt_port_fix.sh script if port 5000 is already in use

## Notes

* The web interface runs on port 8000 by default (shairport-sync uses port 5000)
* AirPlay device name is set to "Pi-AirPlay" by default
* For improved security, consider changing the default port

## License

Open source - feel free to modify and distribute.