# Pi-AirPlay

A streamlined AirPlay receiver for Raspberry Pi with IQaudio DAC.

## Features

* **AirPlay Streaming**: Stream audio wirelessly from Apple devices
* **Album Art Display**: View album artwork, track info, and artist
* **High-Quality Audio**: Works with IQaudio DAC for superior sound quality
* **Simple Web Interface**: Access music information from any device

## Installation

1. Clone this repository to your Raspberry Pi:
   ```
   git clone https://github.com/yourusername/Pi-AirPlay.git
   cd Pi-AirPlay
   ```

2. Install required packages:
   ```
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-flask shairport-sync avahi-daemon
   pip3 install -r requirements.txt
   ```

3. Configure your audio output (for IQaudio DAC):
   Make sure your DAC is properly connected and configured.

## Usage

1. Launch Pi-AirPlay:
   ```
   ./pi_airplay.sh
   ```

2. Access the web interface:
   Open a browser on any device connected to the same network and navigate to:
   ```
   http://your-raspberry-pi-ip:8080
   ```

3. Stream to your Pi:
   - On your iPhone/iPad/Mac, connect to the same WiFi network
   - Select the AirPlay icon in the Control Center
   - Choose "Pi-AirPlay" from the list of available devices
   - Start playing music

## Troubleshooting

* **No Audio Output**: Make sure your DAC is correctly configured and set as the default output device
* **AirPlay Device Not Found**: Ensure avahi-daemon is running: `sudo systemctl status avahi-daemon`
* **Web Interface Unavailable**: Check that the port 8080 is not being used by another application

## Notes

* The web interface runs on port 8080 to avoid conflicts with shairport-sync
* Configuration files are stored in /usr/local/etc/
* AirPlay device name is set to "Pi-AirPlay" by default

## Dependencies

* shairport-sync: For AirPlay functionality
* Flask: Web interface
* Flask-SocketIO: Real-time updates
* Python 3.7+

## License

Open source, feel free to modify and distribute.