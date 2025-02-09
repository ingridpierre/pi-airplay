# AirPlay Setup Troubleshooting Guide

1. First, verify that shairport-sync and avahi-daemon are installed and running:
```bash
# Install if not already present
sudo apt update
sudo apt install -y shairport-sync avahi-daemon

# Start and enable the services
sudo systemctl start avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start shairport-sync
sudo systemctl enable shairport-sync
```

2. Copy the configuration files to the correct locations:
```bash
# Copy config files
sudo cp config/shairport-sync.conf /etc/shairport-sync.conf
sudo cp config/asound.conf /etc/asound.conf
```

3. Verify IQaudIO DAC recognition:
```bash
# Check if the DAC is recognized
aplay -l | grep IQaudIO

# If not recognized, add to config.txt and reboot
sudo sh -c "echo 'dtoverlay=iqaudio-dacplus' >> /boot/config.txt"
sudo reboot
```

4. Check service status:
```bash
# Check shairport-sync status
sudo systemctl status shairport-sync

# Check logs for errors
sudo journalctl -u shairport-sync -n 50
```

5. Verify network connectivity:
```bash
# Check if AirPlay service is being advertised
avahi-browse -a | grep AirPlay
```

Common issues and solutions:

1. If shairport-sync fails to start:
   - Check permissions: `sudo usermod -aG audio shairport-sync`
   - Verify audio device: `sudo chown -R shairport-sync:shairport-sync /dev/snd`

2. If device doesn't appear in AirPlay list:
   - Ensure your iOS/macOS device is on the same network as the Raspberry Pi
   - Check firewall settings: `sudo ufw status` and allow ports 5000-5005 if needed
   - Verify mDNS: `sudo netstat -tulpn | grep avahi`

3. If audio device is not detected:
   - Double-check the DAC jumper settings
   - Verify the overlay in /boot/config.txt
   - Try running `sudo alsactl restore`

For additional debugging:
```bash
# Test audio output
speaker-test -D hw:CARD=IQaudIODAC -c 2

# Check detailed audio configuration
amixer -c IQaudIODAC scontrols
```
