#!/bin/bash
# Pi-DAD Alternative Port Fix Script
# This script uses an alternative port to avoid conflicts

# Make sure we're in the Pi-DAD directory
cd "$(dirname "$0")"

# Kill any existing shairport-sync processes
echo "Stopping any existing shairport-sync processes..."
sudo killall shairport-sync 2>/dev/null || true
sleep 1

# Ensure proper environment
if [ -d "./venv" ]; then
    echo "Using virtual environment..."
    source ./venv/bin/activate
    PYTHON="./venv/bin/python"
else
    echo "Using system Python..."
    PYTHON="python3"
fi

# Create config directory if it doesn't exist
sudo mkdir -p /usr/local/etc

# Create the shairport-sync config file with working settings
echo "Creating shairport-sync configuration file..."
sudo bash -c "cat > /usr/local/etc/shairport-sync.conf << EOL
// Basic shairport-sync configuration
general = 
{
  name = \"Pi-DAD\";
};

alsa =
{
  output_device = \"hw:4\";  // IQaudio DAC card
};

metadata =
{
  enabled = \"yes\";
  include_cover_art = \"yes\";
  pipe_name = \"/tmp/shairport-sync-metadata\";
  pipe_timeout = 5000;
};

diagnostics =
{
  log_verbosity = 1;  // 0 is silent, 1 is normal, 2 is verbose
};
EOL"

# Ensure the metadata pipe exists with correct permissions
if [ -e /tmp/shairport-sync-metadata ]; then
    echo "Setting metadata pipe permissions..."
    sudo chmod 666 /tmp/shairport-sync-metadata
else
    echo "Creating metadata pipe..."
    sudo mkfifo /tmp/shairport-sync-metadata
    sudo chmod 666 /tmp/shairport-sync-metadata
fi

# Start shairport-sync with the configuration file
echo "Starting shairport-sync..."
sudo shairport-sync -c /usr/local/etc/shairport-sync.conf &
sleep 2

# Check if it's running
if pgrep "shairport-sync" > /dev/null; then
    echo "✓ Shairport-sync started successfully!"
else
    echo "✗ Shairport-sync failed to start."
    echo "  Trying fallback method..."
    sudo shairport-sync -a "Pi-DAD" -o alsa -- -d hw:4 &
    sleep 2
    if pgrep "shairport-sync" > /dev/null; then
        echo "✓ Shairport-sync started with fallback method!"
    else
        echo "✗ All attempts to start shairport-sync failed."
    fi
fi

# Use alternative port 8080
WEB_PORT=8080
echo "✓ Using port $WEB_PORT for web interface"

# Start the web interface on the available port
echo "Starting Pi-DAD web interface on port $WEB_PORT..."
echo "Access the interface at http://$(hostname -I | awk '{print $1}'):$WEB_PORT"
echo ""
echo "AirPlay device name: Pi-DAD"
echo ""
exec $PYTHON app.py --port $WEB_PORT