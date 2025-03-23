#!/bin/bash
# Pi-DAD: Raspberry Pi Digital Audio Display
# Startup script

# Ensure the script runs from the correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Function to check if port 5000 is already in use
check_port() {
    if command -v lsof &> /dev/null; then
        if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
            echo "WARNING: Port 5000 is already in use!"
            echo "Would you like to kill the process using this port? (y/n)"
            read -r response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                echo "Stopping process on port 5000..."
                # Get all PIDs using port 5000
                PIDS=$(lsof -t -i:5000)
                if [ -n "$PIDS" ]; then
                    echo "Found processes using port 5000: $PIDS"
                    # First try gentle SIGTERM
                    sudo kill $PIDS
                    sleep 2
                    
                    # Check if any processes are still using the port
                    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null; then
                        echo "Processes still running, using SIGKILL..."
                        sudo kill -9 $PIDS
                        sleep 2
                        
                        # Final check
                        if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null; then
                            echo "ERROR: Failed to free port 5000. Please reboot your system and try again."
                            exit 1
                        fi
                    fi
                    echo "Port 5000 is now free."
                fi
            else
                echo "Please stop the process using port 5000 manually before starting Pi-DAD."
                echo "You can find the process with: lsof -i :5000"
                echo "Then stop it with: sudo kill <PID>"
                exit 1
            fi
        fi
    else
        echo "lsof command not found - skipping port check."
    fi
}

# Check if we should use virtual environment
if [ -d "./venv" ]; then
    echo "Using virtual environment..."
    source ./venv/bin/activate
    PYTHON="./venv/bin/python"
else
    echo "Using system Python..."
    PYTHON="python3"
    
    # Check if required packages are installed
    echo "Checking for required Python packages..."
    if ! $PYTHON -c "import flask_socketio" &> /dev/null; then
        echo "flask-socketio package is missing. Would you like to install it? (y/n)"
        read -r install_choice
        if [[ "$install_choice" == "y" || "$install_choice" == "Y" ]]; then
            echo "Creating local virtual environment..."
            $PYTHON -m venv ./venv
            source ./venv/bin/activate
            PYTHON="./venv/bin/python"
            echo "Installing required packages..."
            ./venv/bin/pip install --upgrade pip
            ./venv/bin/pip install flask "flask-socketio>=5.0.0" pyaudio requests pyacoustid colorthief musicbrainzngs pillow eventlet
            echo "Dependencies installed in local virtual environment"
        else
            echo "Required packages are missing. Please install them manually."
            echo "pip install flask flask-socketio pyaudio requests pyacoustid colorthief musicbrainzngs pillow eventlet"
            exit 1
        fi
    fi
fi

# This section has been moved up near line 145

# Check for AcoustID API key
if [ ! -f "/etc/acoustid_api_key" ] && [ ! -f "$SCRIPT_DIR/config/acoustid_api_key" ]; then
    echo "No AcoustID API key found. Music recognition will run in simulation mode."
    echo "To set up an API key, visit http://[your-pi-ip]:5000/setup after starting Pi-DAD."
    echo "or create /etc/acoustid_api_key with your API key."
fi

# Handle audio device configuration
echo "Checking audio devices..."
if command -v arecord &> /dev/null; then
    if ! arecord -l | grep -q "USB"; then
        echo "WARNING: No USB audio device detected! Music recognition may not work properly."
        echo "Connect a USB microphone and try again."
    else
        echo "USB audio device detected."
        # Create audio configuration if needed
        if [ ! -f "/etc/asound.conf" ]; then
            echo "Would you like to create a basic ALSA configuration for your USB audio device? (y/n)"
            read -r create_alsa_conf
            if [[ "$create_alsa_conf" == "y" || "$create_alsa_conf" == "Y" ]]; then
                # Get the card number of the USB device
                CARD_NUM=$(arecord -l | grep USB | head -n 1 | awk -F'card ' '{print $2}' | cut -d: -f1)
                if [ -n "$CARD_NUM" ]; then
                    echo "Creating ALSA configuration for card $CARD_NUM..."
                    sudo bash -c "cat > /etc/asound.conf << EOL
# Use the USB audio device as default
pcm.!default {
    type hw
    card $CARD_NUM
}

ctl.!default {
    type hw
    card $CARD_NUM
}
EOL"
                    echo "ALSA configuration created."
                else
                    echo "Could not determine USB audio card number. Skipping ALSA configuration."
                fi
            fi
        fi
    fi
else
    echo "arecord command not found - skipping audio device check."
fi

# Check if port 5000 is already in use
check_port

# Kill any existing shairport-sync processes
if pgrep -x "shairport-sync" > /dev/null; then
    echo "Stopping existing shairport-sync..."
    sudo pkill -x "shairport-sync"
    sleep 1
fi

# Clear any stale PID files
for pidfile in "/var/run/shairport-sync.pid" "/run/shairport-sync/shairport-sync.pid" "/run/shairport-sync.pid"; do
    if [ -f "$pidfile" ]; then
        echo "Removing stale PID file: $pidfile"
        sudo rm "$pidfile"
    fi
done

# Ensure the metadata pipe exists with correct permissions
if [ -e /tmp/shairport-sync-metadata ]; then
    echo "Setting metadata pipe permissions..."
    sudo chmod 666 /tmp/shairport-sync-metadata
else
    echo "Creating metadata pipe..."
    sudo mkfifo /tmp/shairport-sync-metadata
    sudo chmod 666 /tmp/shairport-sync-metadata
fi

# Create the shairport-sync config file if it doesn't exist
if [ ! -f "/usr/local/etc/shairport-sync.conf" ]; then
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
else
    echo "Using existing shairport-sync configuration file."
fi

echo "Starting shairport-sync..."
# Start shairport-sync with the configuration file
sudo shairport-sync -c /usr/local/etc/shairport-sync.conf &

# Check if shairport-sync started successfully
sleep 2
if ! pgrep "shairport-sync" > /dev/null; then
    echo "WARNING: Failed to start shairport-sync with config file!"
    
    # Backup plan: Try direct command line with working parameters
    echo "Trying to start with direct command line parameters..."
    
    # Get the IQaudIO card number
    CARD_NUM=$(aplay -l | grep IQaudIO | head -n 1 | awk -F'card ' '{print $2}' | cut -d: -f1)
    if [ -n "$CARD_NUM" ]; then
        echo "Using IQaudio DAC on card $CARD_NUM for audio output"
        sudo shairport-sync -a "Pi-DAD" -o alsa -m pipe=/tmp/shairport-sync-metadata -- -d hw:$CARD_NUM &
    else
        echo "Could not find IQaudIO DAC, trying default output"
        sudo shairport-sync -a "Pi-DAD" -o alsa -m pipe=/tmp/shairport-sync-metadata &
    fi
    
    sleep 2
    if ! pgrep "shairport-sync" > /dev/null; then
        echo "ERROR: AirPlay functionality is not available!"
        echo "Please check your shairport-sync installation."
    else
        echo "shairport-sync started with backup configuration."
    fi
else
    echo "shairport-sync started successfully with configuration file"
fi

# Start the Pi-DAD application
echo "Starting Pi-DAD..."
exec $PYTHON app.py