#!/bin/bash
#
# Pi-AirPlay: Startup script for Raspberry Pi AirPlay Receiver
# This script sets up a streamlined AirPlay receiver with web interface

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Change to the script directory
cd "$(dirname "$0")"

# Set up logging
LOG_FILE="pi_airplay.log"
echo "$(date) - Starting Pi-AirPlay..." > "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date) - $1" | tee -a "$LOG_FILE"
}

# Function to show progress
show_progress() {
    echo -e "${GREEN}✓${NC} $1" | tee -a "$LOG_FILE"
}

# Function to show errors
show_error() {
    echo -e "${RED}✗${NC} $1" | tee -a "$LOG_FILE"
    echo -e "${YELLOW}→${NC} $2" | tee -a "$LOG_FILE"
}

# Function to check if a process is running
is_running() {
    pgrep -f "$1" >/dev/null
    return $?
}

# Check for Python dependencies
log_message "Checking for required Python packages..."
MISSING_PKGS=()

check_python_package() {
    python3 -c "import $1" 2>/dev/null
    if [ $? -ne 0 ]; then
        MISSING_PKGS+=("$1")
        return 1
    fi
    return 0
}

# Check essential packages
check_python_package "flask"
check_python_package "socketio"
check_python_package "eventlet"

# Install missing packages if needed
if [ ${#MISSING_PKGS[@]} -gt 0 ]; then
    show_error "Missing Python packages:" "${MISSING_PKGS[*]}"
    read -p "Would you like to install these packages now? (y/n): " INSTALL_PKGS
    
    if [[ "$INSTALL_PKGS" == "y" || "$INSTALL_PKGS" == "Y" ]]; then
        echo "Installing missing Python packages..."
        pip3 install flask flask-socketio eventlet pillow requests numpy
        
        if [ $? -eq 0 ]; then
            show_progress "Python packages installed successfully"
        else
            show_error "Failed to install packages" "Please run: sudo pip3 install flask flask-socketio eventlet pillow"
        fi
    else
        show_error "Missing dependencies" "Please install required packages before running this script"
        exit 1
    fi
fi

# Check audio devices
log_message "Checking audio devices..."
aplay -l >> "$LOG_FILE" 2>&1

# Log the default audio device
log_message "Default audio device:"
cat /proc/asound/cards >> "$LOG_FILE" 2>&1

# Stop any existing shairport-sync processes
log_message "Stopping any existing shairport-sync processes..."
pkill -f shairport-sync
pkill -f "python.*app_airplay"

# Check if any services are using ports 5000 and 8000
log_message "Checking ports 5000 and 8000..."
PORT_5000_PID=$(lsof -i:5000 -t 2>/dev/null)
PORT_8000_PID=$(lsof -i:8000 -t 2>/dev/null)

if [ ! -z "$PORT_5000_PID" ]; then
    show_error "Port 5000 is in use by process $PORT_5000_PID" "Killing process..."
    kill -9 $PORT_5000_PID 2>/dev/null
    sleep 1
fi

if [ ! -z "$PORT_8000_PID" ]; then
    show_error "Port 8000 is in use by process $PORT_8000_PID" "Killing process..."
    kill -9 $PORT_8000_PID 2>/dev/null
    sleep 1
fi

# Make sure the metadata pipe exists with the right permissions
log_message "Cleaning up the metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
    rm /tmp/shairport-sync-metadata
fi
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata
show_progress "Metadata pipe recreated"

# Check for config directory and create if needed
mkdir -p config

# Create shairport-sync configuration if it doesn't exist
if [ ! -f "config/shairport-sync.conf" ]; then
    log_message "Creating shairport-sync configuration..."
    cat > "config/shairport-sync.conf" << EOF
general = {
  name = "DAD";
  port = 5000;
  ignore_volume_control = "yes";
};

alsa = {
  output_device = "default";
  mixer_control_name = "PCM";
};

metadata = {
  enabled = "yes";
  include_cover_art = "yes";
  pipe_name = "/tmp/shairport-sync-metadata";
  pipe_timeout = 5000;
};

diagnostics = {
  log_verbosity = 1;
};
EOF
    show_progress "Created shairport-sync configuration"
fi

# Start shairport-sync
log_message "Starting shairport-sync on port 5000..."
shairport-sync -c config/shairport-sync.conf -v >> "$LOG_FILE" 2>&1 &

# Wait a moment to ensure shairport-sync is running
sleep 2

# Check if shairport-sync is running
if is_running "shairport-sync"; then
    show_progress "shairport-sync started successfully on port 5000"
else
    show_error "Failed to start shairport-sync" "Check the log file for more information"
fi

# Start the web interface
log_message "Starting Pi-AirPlay web interface on port 8000..."
python3 app_airplay.py --port 8000 --host 0.0.0.0 >> "$LOG_FILE" 2>&1 &
sleep 3

# Verify that services are running
log_message "Verifying services..."
if is_running "app_airplay.py"; then
    show_progress "Pi-AirPlay web interface running on port 8000"
else
    show_error "Pi-AirPlay web interface not running" "Check the log file for more information"
fi

# Get the local IP address
IP_ADDR=$(hostname -I | awk '{print $1}')

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay Started Successfully!${NC}"
echo -e "${BOLD}=========================================${NC}\n"

echo -e "${GREEN}✓${NC} AirPlay device '${BOLD}DAD${NC}' is available for streaming"
echo -e "${GREEN}✓${NC} Web interface is running at ${BOLD}http://$IP_ADDR:8000${NC}"
echo -e "\n${YELLOW}→${NC} Connect to ${BOLD}DAD${NC} via AirPlay from your Apple device"
echo -e "${YELLOW}→${NC} Open a web browser and go to ${BOLD}http://$IP_ADDR:8000${NC}"
echo -e "${YELLOW}→${NC} If you encounter any issues, check the log file: ${BOLD}pi_airplay.log${NC}\n"