#!/bin/bash
# Fix for microphone recording issues

# Make sure we're in the Pi-DAD directory
cd "$(dirname "$0")"

# Kill any current Pi-DAD processes
echo "Stopping any running Pi-DAD processes..."
pkill -f "python app.py"
sleep 1

# Set the correct input device using environment variables
export AUDIODEV=hw:3,0  # Card 3, device 0 (USB microphone)
export PYTHONUNBUFFERED=1

# Run the alt_port_fix.sh script
echo "Starting Pi-DAD with microphone fix..."
./alt_port_fix.sh