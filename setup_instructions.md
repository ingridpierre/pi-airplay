# Pi-DAD Setup Instructions

## Quick Start (Recommended)

1. Open a terminal on your Raspberry Pi
2. Run the alternative port script:
   ```
   cd ~/Pi-DAD
   ./alt_port_fix.sh
   ```
3. The script will display the web interface URL (usually http://YOUR_PI_IP:8080)
4. Open a web browser and navigate to that URL

## Music Recognition Setup (Optional)

To enable music recognition (for identifying songs playing nearby):

1. Get a free API key from [AcoustID](https://acoustid.org/login)
   - Register for an account
   - Go to Applications → New application
   - Give it a name (like "Pi-DAD") and submit

2. Save the API key to your Pi-DAD folder:
   ```
   cd ~/Pi-DAD
   echo "YOUR_API_KEY_HERE" > .acoustid_api_key
   ```

3. Restart Pi-DAD using the alt_port_fix.sh script

## AirPlay Usage

Your Pi-DAD device is now showing up as an AirPlay device named "Pi-DAD".

1. On your iPhone/iPad/Mac:
   - Connect to the same WiFi network as your Raspberry Pi
   - Open Control Center (swipe down from top-right)
   - Tap AirPlay
   - Select "Pi-DAD"
   - Start playing music

2. The song information and artwork will appear on the Pi-DAD web interface

## Troubleshooting

If the web interface doesn't load:
- Make sure you're using the URL with the port number shown in the script output
- Try restarting your Pi with `sudo reboot`
- Run `./alt_port_fix.sh` again after reboot

If AirPlay isn't working:
- Ensure your phone and Pi are on the same network
- Make sure shairport-sync is running with `ps aux | grep shairport`
- Restart Pi-DAD with `./alt_port_fix.sh`