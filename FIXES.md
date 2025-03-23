# Pi-AirPlay Troubleshooting Fixes

This document contains common issues and their solutions for the Pi-AirPlay system.

## Recent Improvements

The following improvements have been made to address common issues:

1. **Enhanced Metadata Handling**: The system now uses a more robust approach to extract metadata from shairport-sync, with better error handling and non-blocking reads.

2. **Reduced Update Latency**: Metadata updates now refresh every 1 second instead of 5 seconds for more responsive UI updates.

3. **Background Color Adaptation**: The web interface now extracts dominant colors from album art to create a cohesive visual experience.

4. **Improved Process Detection**: Better distinction between shairport-sync running vs. active playback status.

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

The updated code now includes improved error handling for metadata pipe access:
- Non-blocking reads from the pipe
- Automatic handling for different platforms (with/without fcntl)
- Improved pipe creation and permission management
- Proper cleanup when pipe access fails

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
   python3 app_airplay.py --port 8000 --host 0.0.0.0
   ```

4. Important: Use HTTP, not HTTPS to access the web interface:
   ```
   http://your-pi-ip:8000
   ```
   (Not https://your-pi-ip:8000)

5. If you get "Connection Refused" errors, check these potential issues:
   - Firewall blocking port 8000 on your Pi:
     ```bash
     sudo iptables -L
     # To allow port 8000:
     sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
     ```
   - Network isolation - make sure your device and Pi are on the same network
   - Test local connection on the Pi itself:
     ```bash
     curl http://localhost:8000
     ```
   - Try binding to all interfaces explicitly when starting the app:
     ```bash
     python3 app_airplay.py --port 8000 --host 0.0.0.0
     ```
   - Check for IP address changes (Pi might have a different IP than expected)

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