# Pi-AirPlay

Pi-AirPlay transforms your Raspberry Pi with IQaudio DAC into a high-quality AirPlay receiver with a modern web interface. Stream music wirelessly from your Apple devices to your Raspberry Pi and enjoy a beautiful metadata display.

## Features

- **AirPlay Integration**: Stream audio from iOS devices, macOS, and iTunes to your Raspberry Pi
- **Metadata Display**: View track information, album art, and playback status in real-time
- **Clean UI Design**: Elegant dark theme that complements any album artwork
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **High-Quality Audio**: Uses your IQaudio DAC for superior sound quality
- **Kiosk Mode**: Can run in full-screen kiosk mode for dedicated displays

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
sudo ./install_pi_airplay_simple.sh
```

3. Follow the on-screen prompts to configure your audio device.

## Manual Usage

To start services manually:

```bash
sudo systemctl restart shairport-sync.service
sudo systemctl restart pi-airplay.service
```

## Setting Up Kiosk Mode

To have Pi-AirPlay automatically launch in full-screen kiosk mode at boot:

1. Create an autostart directory:
```bash
mkdir -p /home/ivpi/.config/autostart
```

2. Create a kiosk mode desktop entry:
```bash
nano /home/ivpi/.config/autostart/pi-airplay-kiosk.desktop
```

Add this content:
```
[Desktop Entry]
Type=Application
Name=Pi-AirPlay Kiosk
Exec=chromium-browser --kiosk --app=http://localhost:8000 --disable-restore-session-state --noerrdialogs
X-GNOME-Autostart-enabled=true
```

3. Make the file executable:
```bash
chmod +x /home/ivpi/.config/autostart/pi-airplay-kiosk.desktop
```

4. Configure Raspberry Pi to boot to desktop:
```bash
sudo raspi-config
```
Navigate to: System Options → Boot / Auto Login → Desktop Autologin

5. Disable screen blanking/sleeping:
```bash
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart
```
Add these lines:
```
@xset s off
@xset -dpms
@xset s noblank
```

6. Hide the cursor when not in use:
```bash
sudo apt-get install unclutter
echo "@unclutter -idle 0.1 -root" | sudo tee -a /etc/xdg/lxsession/LXDE-pi/autostart
```

7. Reboot to test:
```bash
sudo reboot
```

## Troubleshooting

If you encounter issues, run the troubleshooting script:
```bash
./troubleshoot.sh
```

For more detailed diagnostics:
```bash
sudo systemctl status shairport-sync.service
sudo systemctl status pi-airplay.service
```

To exit kiosk mode, press Alt+F4 or connect a keyboard and press F11.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Shairport-Sync for AirPlay support
- Flask-SocketIO for real-time web interface