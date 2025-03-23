#!/bin/bash
#
# Alt Port Fix for Pi-AirPlay
# This script resolves port conflicts between shairport-sync and the web interface

# Set up logging
LOG_FILE="alt_port_fix.log"
echo "$(date) - Running alternative port configuration..." > "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date) - $1" | tee -a "$LOG_FILE"
}

# Stop any existing shairport-sync processes
log_message "Stopping any existing shairport-sync processes..."
pkill -f shairport-sync

# Using virtual environment if it exists
if [ -d "venv" ]; then
    log_message "Using virtual environment..."
    source venv/bin/activate
fi

# Make sure the metadata pipe exists with the right permissions
log_message "Setting up metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
    rm /tmp/shairport-sync-metadata
fi
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata

# Create or update shairport-sync configuration
CONF_FILE="/usr/local/etc/shairport-sync.conf"
log_message "Creating shairport-sync configuration file..."
mkdir -p /usr/local/etc
cat > "$CONF_FILE" << EOF
general = {
  name = "Pi-AirPlay";
  port = 5000;
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

# Start shairport-sync on port 5000
log_message "Starting shairport-sync on port 5000..."
shairport-sync -v >> "$LOG_FILE" 2>&1 &

# Wait a moment to ensure shairport-sync is running
sleep 2

# Check if shairport-sync is running
if pgrep -f "shairport-sync" > /dev/null; then
    log_message "shairport-sync started successfully on port 5000"
else
    log_message "ERROR: Failed to start shairport-sync"
fi

# Start the web interface on port 8080
log_message "Starting web interface on port 8080..."
python3 app_airplay.py --port 8080 >> "$LOG_FILE" 2>&1 &

log_message "Port conflict resolved!"
echo "-----------------------------------------"
echo "Port conflict resolved!"
echo "AirPlay service running on port 5000"
echo "Web interface available at: http://$(hostname -I | awk '{print $1}'):8080"
echo "-----------------------------------------"