# Pi-AirPlay Troubleshooting Fixes

This document contains common issues and their solutions for the Pi-AirPlay system.

## Port Conflicts

### Problem
The default configuration uses port 5000 for both shairport-sync and the Flask web server, causing conflicts.

### Solution
Run the `alt_port_fix.sh` script which:
1. Configures shairport-sync to use port 5000 (AirPlay default)
2. Configures the web interface to use port 8080
3. Correctly sets permissions for the metadata pipe

```bash
./alt_port_fix.sh
```

## Audio Output Issues

### Problem
No audio output or incorrect audio device is being used.

### Solution
The IQaudio DAC needs to be properly configured:

1. Make sure the DAC is correctly connected
2. Identify your audio card number:
   ```bash
   aplay -l
   cat /proc/asound/cards
   ```
3. Update the `output_device` in `/usr/local/etc/shairport-sync.conf` to match your DAC card number:
   ```
   alsa = {
     output_device = "hw:X";  # Replace X with your card number (e.g., hw:4)
     mixer_control_name = "PCM";
   };
   ```

## Metadata Pipe Issues

### Problem
Metadata not showing up in the web interface.

### Solution
Fix the metadata pipe permissions:

```bash
# Remove existing pipe
rm -f /tmp/shairport-sync-metadata

# Create new pipe with correct permissions
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata
```

## Startup Issues

### Problem
Pi-AirPlay doesn't start properly.

### Solution
Run the diagnostic to see what's wrong:

```bash
./diagnose_shairport.sh
```

Check the logs for any errors:
```bash
cat pi_airplay.log
```

## Web Interface Not Working

### Problem
Can't access the web interface.

### Solution
1. Make sure the web server is running on the correct port:
   ```bash
   ps aux | grep app_airplay
   ```

2. Check what port it's running on:
   ```bash
   netstat -tuln | grep python
   ```

3. If needed, restart the web interface manually:
   ```bash
   python3 app_airplay.py --port 8080
   ```

4. Important: Use HTTP, not HTTPS to access the web interface:
   ```
   http://your-pi-ip:8080
   ```
   (Not https://your-pi-ip:8080)

## Shairport-sync Issues

### Problem
Shairport-sync crashes or doesn't start.

### Solution
1. Check if it's running:
   ```bash
   pgrep -l shairport-sync
   ```

2. Start it manually to see error messages:
   ```bash
   shairport-sync -v
   ```

3. Reinstall if necessary:
   ```bash
   sudo apt-get update
   sudo apt-get install --reinstall shairport-sync
   ```