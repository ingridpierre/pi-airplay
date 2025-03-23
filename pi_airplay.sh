#!/bin/bash
#
# Pi-AirPlay: Startup script for Raspberry Pi AirPlay Receiver
# This script sets up a streamlined AirPlay receiver with web interface

# Change to the script directory
cd "$(dirname "$0")"

# Set up logging
LOG_FILE="pi_airplay.log"
echo "$(date) - Starting Pi-AirPlay..." > "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date) - $1" | tee -a "$LOG_FILE"
}

# Function to check if a process is running
is_running() {
    pgrep -f "$1" >/dev/null
    return $?
}

# Check audio devices
log_message "Checking audio devices..."
aplay -l >> "$LOG_FILE" 2>&1

# Log the default audio device
log_message "Default audio device:"
cat /proc/asound/cards >> "$LOG_FILE" 2>&1

# Stop any existing shairport-sync processes
log_message "Stopping any existing shairport-sync processes..."
pkill -f shairport-sync

# Make sure the metadata pipe exists with the right permissions
log_message "Setting up metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
    rm /tmp/shairport-sync-metadata
fi
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata

# Check if shairport-sync.conf exists
CONF_FILE="/usr/local/etc/shairport-sync.conf"
if [ ! -f "$CONF_FILE" ]; then
    log_message "Creating shairport-sync.conf..."
    mkdir -p /usr/local/etc
    cat > "$CONF_FILE" << EOF
general = {
  name = "Pi-AirPlay";
};

alsa = {
  output_device = "hw:4";
  mixer_control_name = "PCM";
};

metadata = {
  enabled = "yes";
  include_cover_art = "yes";
  pipe_name = "/tmp/shairport-sync-metadata";
  pipe_timeout = 5000;
};
EOF
fi

# Start shairport-sync
log_message "Starting shairport-sync..."
shairport-sync -v >> "$LOG_FILE" 2>&1 &

# Wait a moment to ensure shairport-sync is running
sleep 2

# Check if shairport-sync is running
if is_running "shairport-sync"; then
    log_message "shairport-sync started successfully"
else
    log_message "ERROR: Failed to start shairport-sync"
fi

# Start the web interface
log_message "Starting web interface on port 8080..."
python3 app_airplay.py --port 8080 >> "$LOG_FILE" 2>&1 &

log_message "Pi-AirPlay started! Web interface available at: http://$(hostname -I | awk '{print $1}'):8080"
echo "-----------------------------------------"
echo "Pi-AirPlay is running!"
echo "Access the web interface at: http://$(hostname -I | awk '{print $1}'):8080"
echo "(Important: Use HTTP, not HTTPS in your browser)"
echo "Stream music using AirPlay from your Apple device"
echo "-----------------------------------------"