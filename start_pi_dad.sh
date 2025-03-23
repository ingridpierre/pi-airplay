#!/bin/bash
# Pi-DAD: Raspberry Pi Digital Audio Display
# Startup script

# Ensure the script runs from the correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

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

# Create the metadata pipe if it doesn't exist
if [ ! -e /tmp/shairport-sync-metadata ]; then
    echo "Creating metadata pipe..."
    mkfifo /tmp/shairport-sync-metadata
    chmod 666 /tmp/shairport-sync-metadata
fi

# Check if shairport-sync is running
if ! pgrep -x "shairport-sync" > /dev/null; then
    echo "Starting shairport-sync..."
    shairport-sync &
else
    echo "shairport-sync is already running"
fi

# Start the Pi-DAD application
echo "Starting Pi-DAD..."
exec $PYTHON app.py