#!/bin/bash
# Pi-DAD Quick Fix Script
# This script applies the working configuration and starts Pi-DAD with AirPlay enabled

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

# Check for busy ports and find an available one
PORTS_TO_TRY="5000 5001 5002 8080 8888"
CHOSEN_PORT=""

for port in $PORTS_TO_TRY; do
    if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null; then
        CHOSEN_PORT=$port
        echo "✓ Using port $CHOSEN_PORT for web interface"
        break
    fi
done

if [ -z "$CHOSEN_PORT" ]; then
    echo "✗ All ports are busy. Please restart your Raspberry Pi and try again."
    exit 1
fi

# Start the web interface on the available port
echo "Starting Pi-DAD web interface on port $CHOSEN_PORT..."
echo "Access the interface at http://$(hostname -I | awk '{print $1}'):$CHOSEN_PORT"
echo ""
echo "AirPlay device name: Pi-DAD"
echo ""
exec $PYTHON app.py --port $CHOSEN_PORT