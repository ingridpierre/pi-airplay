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