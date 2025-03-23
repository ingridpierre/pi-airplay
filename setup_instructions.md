# Pi-AirPlay Setup Instructions

This guide will walk you through setting up Pi-AirPlay on your Raspberry Pi with IQaudio DAC.

## Hardware Requirements

* Raspberry Pi (3 or newer recommended)
* IQaudio DAC or similar audio HAT
* SD card with Raspberry Pi OS installed
* Power supply
* Network connection (Ethernet or Wi-Fi)

## Software Setup

### 1. Basic System Setup

First, make sure your Raspberry Pi OS is up to date:

```bash
sudo apt-get update
sudo apt-get upgrade
```

### 2. Install Required Packages

Install the necessary packages for Pi-AirPlay:

```bash
sudo apt-get install -y python3-pip python3-flask shairport-sync avahi-daemon alsa-utils
```

### 3. Clone the Pi-AirPlay Repository

```bash
git clone https://github.com/yourusername/Pi-AirPlay.git
cd Pi-AirPlay
```

### 4. Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

## Audio Configuration

### 1. Identify Your Audio Device

Check your audio hardware:

```bash
aplay -l
cat /proc/asound/cards
```

Look for your IQaudio DAC in the output and note the card number.

### 2. Configure ALSA (if needed)

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

## Running Pi-AirPlay

### 1. Start the Service

Use the provided startup script:

```bash
./pi_airplay.sh
```

This will:
- Configure and start shairport-sync
- Set up the metadata pipe
- Launch the web interface

### 2. Access the Web Interface

Open a web browser on any device connected to the same network:

```
http://your-raspberry-pi-ip:8080
```

### 3. Connect Your Apple Device

1. Connect your iPhone/iPad/Mac to the same WiFi network
2. Open Control Center and select the AirPlay icon
3. Choose "Pi-AirPlay" from the list of available devices
4. Start playing music

## Troubleshooting

If you encounter issues, try these steps:

1. Run the diagnostic script:
   ```bash
   ./diagnose_shairport.sh
   ```

2. Check logs:
   ```bash
   cat pi_airplay.log
   ```

3. If you have port conflicts:
   ```bash
   ./alt_port_fix.sh
   ```

4. See the FIXES.md file for common solutions

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

## Additional Resources

* Shairport-sync documentation: https://github.com/mikebrady/shairport-sync
* AirPlay protocol information: https://nto.github.io/AirPlay.html
* IQaudio DAC resources: https://www.iqaudio.com/downloads/