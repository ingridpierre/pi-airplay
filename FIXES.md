# Pi-AirPlay Fixes and Troubleshooting

This document outlines the major issues that were fixed in the Pi-AirPlay project and how to resolve them.

## Main Issues Fixed

### 1. Service Startup Conflicts

**Problem**: The original setup had multiple services (shairport-sync.service and pi-airplay.service) that were causing conflicts. The web interface would not start properly when the system shairport-sync was already running.

**Solution**: Combined both services into a single service that:
1. Starts shairport-sync directly
2. Creates and sets permissions on the metadata pipe
3. Launches the web interface

This eliminates race conditions and conflicts between different startup methods.

### 2. Metadata Pipe Permission Issues

**Problem**: The metadata pipe (/tmp/shairport-sync-metadata) sometimes had incorrect permissions or didn't exist at startup.

**Solution**: The startup script now ensures the pipe exists and has the correct permissions (666) before starting any services.

### 3. Multiple Shairport-Sync Configurations

**Problem**: The system had two different shairport-sync configurations - one system-wide at /etc/shairport-sync.conf and another in the project's config directory.

**Solution**: Simplified to use the system shairport-sync installation and configuration. The start_pi_airplay.sh script now:
1. Checks if shairport-sync is already running
2. Starts it if needed
3. Proceeds with starting the web interface

### 4. IQaudio DAC Recognition Issues

**Problem**: Sometimes the IQaudio DAC wasn't being correctly recognized or targeted.

**Solution**: The service now waits for the sound.target to ensure the audio hardware is properly initialized before starting.

## How to Test the Fix

1. After installing the service:
   ```bash
   sudo systemctl start pi-airplay.service
   ```

2. Check if both components are running:
   ```bash
   # Check if the web service is running
   curl http://localhost:8000
   
   # Check if shairport-sync is running
   pgrep -l shairport-sync
   ```

3. Reboot the Raspberry Pi to verify auto-start works:
   ```bash
   sudo reboot
   ```

4. After reboot, check again:
   ```bash
   curl http://localhost:8000
   pgrep -l shairport-sync
   ```

## Common Issues and Solutions

### Web Interface Shows "Waiting for Music" but AirPlay Doesn't Connect

1. Check if shairport-sync is running:
   ```bash
   pgrep -l shairport-sync
   ```

2. Check the logs:
   ```bash
   sudo journalctl -u pi-airplay.service
   ```

3. Restart the service if needed:
   ```bash
   sudo systemctl restart pi-airplay.service
   ```

### Audio Device Issues

If there are issues with audio device selection:

1. Check available audio devices:
   ```bash
   aplay -l
   ```

2. Edit the system-wide shairport-sync config:
   ```bash
   sudo nano /etc/shairport-sync.conf
   ```

3. Update the alsa section to match your IQaudio DAC device:
   ```
   alsa = {
     output_device = "hw:4,0"; // Use the correct card and device for your DAC
   };
   ```