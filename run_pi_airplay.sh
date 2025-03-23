#!/bin/bash
# Pi-AirPlay Quick Start Script
# This script runs Pi-AirPlay directly for testing/development

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay Quick Start${NC}"
echo -e "${BOLD}=========================================${NC}\n"

# Function to display progress
show_progress() {
  echo -e "${GREEN}✓${NC} $1"
}

# Function to display errors
show_error() {
  echo -e "${RED}✗${NC} $1"
  echo -e "${YELLOW}→${NC} $2"
}

# Check if shairport-sync is installed
if ! command -v shairport-sync &> /dev/null; then
  show_error "Shairport-Sync not found" "Please install it first with: sudo apt install shairport-sync"
  exit 1
fi

# First check for audio devices
echo -e "${YELLOW}→${NC} Checking audio devices..."
aplay -l
echo ""

# Ask user for sound card number
echo -e "${YELLOW}→${NC} From the list above, find your IQaudio DAC or USB audio device"
read -p "Enter the card number for your audio device (e.g., 0, 1, 2...): " CARD_NUMBER

# Create a temporary shairport-sync config
mkdir -p /tmp/pi-airplay
cat > /tmp/pi-airplay/shairport-sync.conf << EOL
general = {
  name = "Pi-AirPlay";
  interpolation = "basic";
  output_backend = "alsa";
  mdns_backend = "avahi";
  port = 5000;
  drift_tolerance_in_seconds = 0.002;
  ignore_volume_control = "no";
  volume_range_db = 60;
  regtype = "_raop._tcp";
  playback_mode = "stereo";
};

alsa = {
  output_device = "hw:${CARD_NUMBER}";
  mixer_control_name = "PCM";
  mixer_device = "hw:${CARD_NUMBER}";
};

metadata = {
  enabled = "yes";
  include_cover_art = "yes";
  pipe_name = "/tmp/shairport-sync-metadata";
  pipe_timeout = 5000;
};

diagnostics = {
  log_verbosity = 0;
};
EOL

show_progress "Created temporary config with audio card ${CARD_NUMBER}"

# Kill any existing shairport-sync processes
echo -e "\n${YELLOW}→${NC} Stopping any existing shairport-sync processes..."
killall shairport-sync 2>/dev/null
sleep 1

# Create the metadata pipe if it doesn't exist
if [ ! -p /tmp/shairport-sync-metadata ]; then
  mkfifo /tmp/shairport-sync-metadata
  chmod 666 /tmp/shairport-sync-metadata
  show_progress "Created metadata pipe"
else
  chmod 666 /tmp/shairport-sync-metadata
  show_progress "Using existing metadata pipe"
fi

# Start shairport-sync
echo -e "\n${YELLOW}→${NC} Starting shairport-sync..."
shairport-sync -c /tmp/pi-airplay/shairport-sync.conf &
SHAIRPORT_PID=$!
show_progress "Started shairport-sync"

# Start Pi-AirPlay web interface
echo -e "\n${YELLOW}→${NC} Starting Pi-AirPlay web interface..."
python app_airplay.py --port 5000 &
WEB_PID=$!
show_progress "Started Pi-AirPlay web interface"

# Get the IP address of the current device
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay is now running!${NC}"
echo -e "${BOLD}=========================================${NC}\n"

echo -e "Access the web interface at: ${BOLD}http://$IP_ADDRESS:5000${NC}"
echo -e "Connect to ${BOLD}Pi-AirPlay${NC} via AirPlay from your Apple device\n"
echo -e "Press ${BOLD}Ctrl+C${NC} to stop Pi-AirPlay"

# Clean up on exit
trap 'echo -e "\nStopping Pi-AirPlay..."; kill $SHAIRPORT_PID $WEB_PID 2>/dev/null; echo "Done."; exit 0' INT TERM

# Wait for processes to complete
wait $WEB_PID