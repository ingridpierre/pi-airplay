#!/bin/bash
# Fix script for AcoustID API key setup and microphone issues

# Make sure we're in the Pi-DAD directory
cd "$(dirname "$0")"

# Stop any running processes
echo "Stopping any existing Pi-DAD processes..."
pkill -f "python app.py" 2>/dev/null || true
sudo killall shairport-sync 2>/dev/null || true
sleep 2

# Check if the API key file exists
if [ -f ".acoustid_api_key" ]; then
    echo "Found existing AcoustID API key file."
    API_KEY=$(cat .acoustid_api_key | tr -d '\n' | tr -d ' ')
    echo "API key length: ${#API_KEY} characters"
    
    if [ ${#API_KEY} -lt 8 ]; then
        echo "API key seems too short or empty."
        echo "Enter your AcoustID API key:"
        read -r NEW_API_KEY
        echo "$NEW_API_KEY" > .acoustid_api_key
        echo "API key updated."
    else
        echo "API key seems valid."
    fi
else
    echo "No AcoustID API key file found."
    echo "Enter your AcoustID API key (get one from https://acoustid.org/login):"
    read -r NEW_API_KEY
    echo "$NEW_API_KEY" > .acoustid_api_key
    echo "API key saved to .acoustid_api_key"
fi

# Set the proper permissions on the API key file
chmod 600 .acoustid_api_key

# Enable microphone access by setting device environment variables
export AUDIODEV=hw:3,0  # Card 3, device 0 (USB microphone)
export PYTHONUNBUFFERED=1

# Disable simulation mode if it's enabled
if [ -f ".simulation_mode" ]; then
    echo "Removing simulation mode file..."
    rm .simulation_mode
fi

# Create the shairport-sync config file with working settings
echo "Creating shairport-sync configuration file..."
sudo mkdir -p /usr/local/etc
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
echo "✓ Using port 8080 for web interface"

# Start the web interface on the alternative port
echo "Starting Pi-DAD web interface on port 8080..."
echo "Access the interface at http://$(hostname -I | awk '{print $1}'):8080"
echo ""
echo "AirPlay device name: Pi-DAD"
echo ""

# Run the app with the alternative port
./venv/bin/python app.py --port 8080