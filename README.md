# Pi-AirPlay

A streamlined AirPlay receiver for Raspberry Pi with IQaudio DAC. Turn your Raspberry Pi into a high-quality AirPlay receiver with a clean web interface showing now playing information.

## System Architecture

The Pi-AirPlay system consists of two main components:

1. **Shairport-Sync**: The core AirPlay receiver service that handles the audio streaming protocol and outputs audio to your DAC.

2. **Flask Web Interface**: A lightweight web server that:
   - Extracts metadata from shairport-sync (artist, title, album, artwork)
   - Provides a responsive web interface accessible from any device
   - Dynamically adapts the interface colors based on album artwork
   - Delivers real-time updates via websockets

## Features

* **AirPlay Streaming**: Stream audio wirelessly from Apple devices
* **Album Art Display**: View album artwork, track info, and artist
* **Adaptive Theme Colors**: Background color adapts to album artwork
* **High-Quality Audio**: Works with IQaudio DAC for superior sound quality
* **Simple Web Interface**: Access music information from any device
* **Resource Efficient**: Optimized for Raspberry Pi's limited resources
* **Robust Metadata Handling**: Enhanced shairport-sync metadata decoder implementation

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
   pip3 install flask flask-socketio eventlet pillow colorthief
   ```

3. Configure your audio output:
   Make sure your DAC is properly connected and configure shairport-sync to use it.

## Understanding the Scripts

This project includes several scripts with specific purposes:

1. **pi_airplay.sh** - The main script to run after installation. This starts the AirPlay receiver and web interface.
2. **install_pi_airplay.sh** - One-time installation script that sets up all dependencies and services.
3. **run_pi_airplay.sh** - A testing/development script that runs the service temporarily without installation.
4. **app_airplay.py** - The core Python application (not meant to be run directly).
5. **alt_port_fix.sh** - Helper script to resolve port conflicts.

For normal use, run the installation script once, then use pi_airplay.sh to start the service (or rely on the automatic startup if enabled).

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
3. Choose "DAD" from the list of available devices
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

For quick troubleshooting:

1. Run the diagnostic script:
   ```bash
   ./diagnose_shairport.sh
   ```

2. Check logs:
   ```bash
   cat pi_airplay.log
   ```

3. For metadata pipe issues:
   ```bash
   # Fix pipe permissions
   sudo rm -f /tmp/shairport-sync-metadata
   sudo mkfifo /tmp/shairport-sync-metadata
   sudo chmod 666 /tmp/shairport-sync-metadata
   ```

## Web Interface Features

The Pi-AirPlay web interface provides several features:

1. **Real-time track information**: Artist, album, and song title are updated immediately when playback changes
2. **Album artwork display**: Cover art from the currently playing track is shown
3. **Adaptive theme**: The background color automatically adapts to match the dominant color in the album artwork
4. **Playback status**: Clear indication of when AirPlay is active or waiting for connection
5. **Mobile-friendly layout**: Works well on smartphones and tablets for remote monitoring

## Audio Configuration

### Identify Your Audio Device

Check your audio hardware:

```bash
aplay -l
cat /proc/asound/cards
```

Look for your IQaudio DAC in the output and note the card number.

### Configure ALSA (if needed)

If your DAC isn't automatically configured:

```bash
sudo nano /etc/asound.conf
```

Add the following (replace X with your DAC's card number):

```
pcm.!default {
    type hw
    card X
}

ctl.!default {
    type hw
    card X
}
```

## Auto-Starting on Boot

To have Pi-AirPlay start automatically when your Raspberry Pi boots:

```bash
crontab -e
```

Add this line to the end:

```
@reboot /home/pi/Pi-AirPlay/pi_airplay.sh
```

Replace `/home/pi/Pi-AirPlay` with the actual path to your installation.

## Notes

* The web interface runs on port 8000 by default (shairport-sync uses port 5000)
* AirPlay device name is set to "DAD" by default
* For improved security, consider changing the default port
* For detailed troubleshooting, refer to [FIXES.md](FIXES.md)

## License

Open source - feel free to modify and distribute.