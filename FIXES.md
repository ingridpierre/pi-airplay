# Pi-DAD Startup Script Fixes

This document explains the fixes made to resolve startup issues with the Pi-DAD application.

## Issues Fixed

1. **Port 5000 Conflict Resolution**
   - Enhanced the port conflict detection and resolution process
   - Added a more robust approach to killing processes using port 5000
   - Added additional checks to ensure the port is truly free before starting the application

2. **Shairport-sync Metadata Pipe Configuration**
   - Fixed the command-line syntax for shairport-sync metadata pipe configuration
   - Updated from `-M metadata=/tmp/shairport-sync-metadata` (incorrect) to `-m pipe=/tmp/shairport-sync-metadata` (correct)
   - Added version-specific syntax for different versions of shairport-sync
   - Configured fallback options to ensure metadata is available regardless of version

3. **General Improvements**
   - Better error messages to aid in troubleshooting
   - Improved detection and handling of IQaudio DAC hardware
   - Added additional checks for shairport-sync startup success

## How to Test

Test the updated script by running:

```bash
./start_pi_dad.sh
```

The script should now:
1. Properly detect and handle port conflicts
2. Correctly configure shairport-sync for metadata collection
3. Work with your IQaudio DAC hardware

## Troubleshooting

If you still encounter issues:

1. **Port 5000 Still in Use**
   - Try rebooting the Raspberry Pi
   - Check for stuck processes: `sudo lsof -i :5000`
   - Kill them manually: `sudo kill -9 <PID>`

2. **Shairport-sync Issues**
   - Check that shairport-sync is properly installed: `shairport-sync -V`
   - Try reinstalling it: `sudo apt-get install --reinstall shairport-sync`
   - Check permissions on the metadata pipe: `ls -la /tmp/shairport-sync-metadata`

3. **Audio Device Issues**
   - The "Unknown PCM" warnings in ALSA are often non-critical
   - Check your audio device configuration: `aplay -l`
   - Consider creating a custom `/etc/asound.conf` file for your specific audio setup