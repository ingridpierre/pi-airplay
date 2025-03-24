# Pi-AirPlay Fixes and Troubleshooting

This document contains fixes and troubleshooting steps for common issues with the Pi-AirPlay setup.

## Table of Contents
1. [Overview of Issues](#overview-of-issues)
2. [Service Conflicts Fix](#service-conflicts-fix)
3. [Avahi Daemon Issues](#avahi-daemon-issues)
4. [Metadata Pipe Problems](#metadata-pipe-problems)
5. [Automatic Startup Fix](#automatic-startup-fix)
6. [Troubleshooting Scripts](#troubleshooting-scripts)

## Overview of Issues

The Pi-AirPlay system consists of two main components:
1. **shairport-sync**: The AirPlay receiver that handles audio streaming
2. **Pi-AirPlay web interface**: The web-based control interface

Common issues:
- Services stopping each other when started manually
- Metadata pipe permission issues
- Avahi daemon conflicts
- Services not starting automatically on boot

## Service Conflicts Fix

The original setup had the Pi-AirPlay web interface script (`pi_airplay.sh`) stopping any running shairport-sync instance before starting its own. This caused conflicts when both services were needed.

### Solution:
We've separated the services into two independent systemd services:
- `shairport-sync.service`: Handles just the AirPlay receiver
- `pi-airplay.service`: Handles just the web interface

This ensures they don't interfere with each other and can be managed independently.

## Avahi Daemon Issues

Shairport-sync by default uses the Avahi daemon for mDNS advertisement, which can cause issues if Avahi isn't running or is misconfigured.

### Solution:
We've configured shairport-sync to use the "dummy" mDNS backend when Avahi isn't available:

```
general = {
  name = "DAD";
  output_backend = "alsa";
  mdns_backend = "dummy";  // Uses dummy backend when Avahi isn't available
  port = 5000;
  // Other settings...
};
```

## Metadata Pipe Problems

Issues with the metadata pipe (`/tmp/shairport-sync-metadata`) are common, including:
- Pipe doesn't exist
- Wrong permissions (not readable by web interface)
- Pipe gets corrupted

### Solution:
The service startup scripts now ensure the pipe exists with the correct permissions:

```bash
# Setup metadata pipe
if [ -e /tmp/shairport-sync-metadata ]; then
  rm /tmp/shairport-sync-metadata
fi
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata
```

## Automatic Startup Fix

To ensure both services start automatically on boot, we've created proper systemd service files.

### shairport-sync.service
```
[Unit]
Description=Shairport Sync - AirPlay Audio Receiver
After=sound.target network.target
# Only use the next line if avahi-daemon is installed and functional
# Wants=avahi-daemon.service

[Service]
ExecStartPre=/bin/bash -c "if [ -e /tmp/shairport-sync-metadata ]; then rm /tmp/shairport-sync-metadata; fi && mkfifo /tmp/shairport-sync-metadata && chmod 666 /tmp/shairport-sync-metadata"
ExecStart=/usr/bin/shairport-sync -c /home/ivpi/pi-airplay/config/shairport-sync.conf
Restart=always
RestartSec=5
User=root
Group=root
WorkingDirectory=/home/ivpi/pi-airplay

[Install]
WantedBy=multi-user.target
```

### pi-airplay.service
```
[Unit]
Description=Pi-AirPlay Web Interface
After=network.target shairport-sync.service
Wants=shairport-sync.service

[Service]
ExecStart=/usr/bin/python3 /home/ivpi/pi-airplay/app_airplay.py --port 8000 --host 0.0.0.0
Restart=always
RestartSec=5
User=ivpi
Group=ivpi
WorkingDirectory=/home/ivpi/pi-airplay

[Install]
WantedBy=multi-user.target
```

## Troubleshooting Scripts

We've created several scripts to help diagnose and fix issues:

### 1. install_services.sh
Installs and configures the systemd services correctly:
```bash
sudo ./install_services.sh
```

### 2. troubleshoot.sh
Checks your system for common issues and provides solutions:
```bash
./troubleshoot.sh
```

### 3. clean_fix.sh
Automatically fixes common issues with one command:
```bash
sudo ./clean_fix.sh
```

## Manual Recovery Steps

If the automatic scripts don't work, try these manual steps:

1. Stop all services:
```bash
sudo systemctl stop shairport-sync.service
sudo systemctl stop pi-airplay.service
killall -9 shairport-sync
killall -9 python3
```

2. Fix the metadata pipe:
```bash
sudo rm -f /tmp/shairport-sync-metadata
sudo mkfifo /tmp/shairport-sync-metadata
sudo chmod 666 /tmp/shairport-sync-metadata
```

3. Start services in order:
```bash
sudo systemctl start shairport-sync.service
sleep 2
sudo systemctl start pi-airplay.service
```

4. Check status:
```bash
sudo systemctl status shairport-sync.service
sudo systemctl status pi-airplay.service
```

## Debugging

For advanced debugging, check these logs:
```bash
journalctl -u shairport-sync.service
journalctl -u pi-airplay.service
```

For more detailed diagnostics, use the debug interface at:
```
http://your-pi-ip:8000/debug
```