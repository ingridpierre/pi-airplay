#!/bin/bash
# Pi-AirPlay: A streamlined AirPlay receiver for Raspberry Pi
# This script sets up and runs only the essential AirPlay functionality

# Make sure we're in the project directory
cd "$(dirname "$0")"

# Stop any existing processes
echo "Stopping any existing processes..."
pkill -f "python app.py" 2>/dev/null || true
sudo killall shairport-sync 2>/dev/null || true
sleep 2

# Create the shairport-sync config file with optimal settings
echo "Creating shairport-sync configuration..."
sudo mkdir -p /usr/local/etc
sudo bash -c "cat > /usr/local/etc/shairport-sync.conf << EOL
// Optimized shairport-sync configuration
general = 
{
  name = \"Pi-AirPlay\";
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
  log_verbosity = 1;
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

# Start shairport-sync
echo "Starting shairport-sync..."
sudo shairport-sync -c /usr/local/etc/shairport-sync.conf &
sleep 2

# Check if it's running
if pgrep "shairport-sync" > /dev/null; then
    echo "✓ AirPlay receiver started successfully!"
else
    echo "✗ Failed to start AirPlay receiver."
    echo "  Trying fallback method..."
    sudo shairport-sync -a "Pi-AirPlay" -o alsa -- -d hw:4 &
    sleep 2
    if pgrep "shairport-sync" > /dev/null; then
        echo "✓ AirPlay receiver started with fallback method!"
    else
        echo "✗ All attempts to start AirPlay receiver failed."
        exit 1
    fi
fi

# Use port 8080 for the web interface
WEB_PORT=8080
echo "✓ Using port $WEB_PORT for web interface"

# Start the web interface
echo "Starting web interface on port $WEB_PORT..."
echo "Access the interface at http://$(hostname -I | awk '{print $1}'):$WEB_PORT"
echo ""
echo "AirPlay device name: Pi-AirPlay"
echo ""

# Start the application with the web interface port
if [ -d "./venv" ]; then
    echo "Using virtual environment..."
    source ./venv/bin/activate
    ./venv/bin/python app.py --port $WEB_PORT
else
    echo "Using system Python..."
    python3 app.py --port $WEB_PORT
fi