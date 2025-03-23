# Pi-AirPlay

Pi-AirPlay transforms your Raspberry Pi with IQaudio DAC into a high-quality AirPlay receiver with a modern web interface. Stream music wirelessly from your Apple devices to your Raspberry Pi and enjoy a beautiful metadata display.

## Features

- **AirPlay Integration**: Stream audio from iOS devices, macOS, and iTunes to your Raspberry Pi
- **Metadata Display**: View track information, album art, and playback status in real-time
- **Adaptive UI**: Background color adapts to the dominant color in the album artwork
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **High-Quality Audio**: Uses your IQaudio DAC for superior sound quality

## Web Interface

Access the web interface at `http://your-pi-ip:8000` to see currently playing music:

![Pi-AirPlay Interface](static/artwork/default_album.jpg)

## Requirements

- Raspberry Pi 3 or newer
- Raspberry Pi OS (Bullseye or newer)
- IQaudio DAC or compatible USB audio output device
- Network connection (wired or wireless)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/pi-airplay.git
cd pi-airplay
```

2. Run the installer script:
```bash
sudo ./install_pi_airplay.sh
```

3. Follow the on-screen prompts to configure your audio device.

## Manual Usage

To start Pi-AirPlay manually:

```bash
./pi_airplay.sh
```

## Troubleshooting

If you encounter issues, check the [FIXES.md](FIXES.md) file for common problems and solutions.

For more detailed logs:
```bash
cat pi_airplay.log
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Shairport-Sync for AirPlay support
- Flask-SocketIO for real-time web interface