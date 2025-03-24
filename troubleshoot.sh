#!/bin/bash
# Pi-AirPlay Troubleshooting Tool

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n${BOLD}Pi-AirPlay Troubleshooting Tool${NC}\n"

# Function to display information
show_info() {
  echo -e "${YELLOW}→${NC} $1"
}

# Function to display success
show_success() {
  echo -e "${GREEN}✓${NC} $1"
}

# Function to display error
show_error() {
  echo -e "${RED}✗${NC} $1"
}

# Check if shairport-sync is installed
show_info "Checking if shairport-sync is installed..."
if command -v shairport-sync >/dev/null 2>&1; then
  SHAIRPORT_VERSION=$(shairport-sync -V | head -n 1)
  show_success "shairport-sync is installed."
  echo -e "   Version: $SHAIRPORT_VERSION"
else
  show_error "shairport-sync is not installed."
  echo -e "   Please install with: sudo apt install shairport-sync"
fi

# Check metadata pipe
show_info "Checking metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
  PIPE_PERMISSIONS=$(stat -c "%a" /tmp/shairport-sync-metadata)
  show_success "Metadata pipe exists."
  echo -e "   Permissions: $PIPE_PERMISSIONS (should be 666)"
  if [ "$PIPE_PERMISSIONS" != "666" ]; then
    echo -e "   ${YELLOW}→${NC} Fixing permissions..."
    sudo chmod 666 /tmp/shairport-sync-metadata
  fi
else
  show_error "Metadata pipe does not exist."
  echo -e "   ${YELLOW}→${NC} Creating metadata pipe..."
  sudo rm -f /tmp/shairport-sync-metadata
  sudo mkfifo /tmp/shairport-sync-metadata
  sudo chmod 666 /tmp/shairport-sync-metadata
fi

# Check if shairport-sync is running
show_info "Checking if shairport-sync is running..."
if pgrep -x "shairport-sync" > /dev/null; then
  show_success "shairport-sync is running."
else
  show_error "Error: shairport-sync is not running."
  echo -e "   ${YELLOW}→${NC} Attempting to start shairport-sync..."
  sudo systemctl restart shairport-sync.service
  sleep 2
  if pgrep -x "shairport-sync" > /dev/null; then
    show_success "shairport-sync started successfully."
  else
    show_error "Failed to start shairport-sync."
  fi
fi

# Check if Pi-AirPlay web interface is running
show_info "Checking if Pi-AirPlay web interface is running..."
if pgrep -f "python3 app_airplay.py" > /dev/null; then
  WEB_PROCESS=$(ps aux | grep "python3 app_airplay.py" | grep -v grep)
  show_success "Pi-AirPlay web interface is running."
  echo -e "   Process: $WEB_PROCESS"
else
  show_error "Pi-AirPlay web interface is not running."
  echo -e "   ${YELLOW}→${NC} Attempting to start Pi-AirPlay web interface..."
  sudo systemctl restart pi-airplay.service
  sleep 2
  if pgrep -f "python3 app_airplay.py" > /dev/null; then
    show_success "Pi-AirPlay web interface started successfully."
  else
    show_error "Failed to start Pi-AirPlay web interface."
  fi
fi

# Check systemd service status
show_info "Checking systemd service status..."
SHAIRPORT_SERVICE_STATUS=$(systemctl is-enabled shairport-sync.service 2>/dev/null)
PIAIRPLAY_SERVICE_STATUS=$(systemctl is-enabled pi-airplay.service 2>/dev/null)

if [ "$SHAIRPORT_SERVICE_STATUS" == "enabled" ]; then
  show_success "shairport-sync.service is enabled."
else
  show_error "shairport-sync.service is not enabled."
  echo -e "   ${YELLOW}→${NC} Enabling shairport-sync.service..."
  sudo systemctl enable shairport-sync.service
fi

if [ "$PIAIRPLAY_SERVICE_STATUS" == "enabled" ]; then
  show_success "pi-airplay.service is enabled."
else
  show_error "pi-airplay.service is not enabled."
  echo -e "   ${YELLOW}→${NC} Enabling pi-airplay.service..."
  sudo systemctl enable pi-airplay.service
fi

# Check audio devices
show_info "Checking audio devices..."
echo "Available audio devices:"
aplay -l

# Check Avahi daemon
show_info "Checking Avahi daemon..."
if systemctl is-active --quiet avahi-daemon; then
  show_success "Avahi daemon is running."
else
  show_error "Avahi daemon is not running."
  echo -e "   ${YELLOW}→${NC} Starting Avahi daemon..."
  sudo systemctl restart avahi-daemon
fi

# Display recovery options
echo -e "\n${BOLD}Recovery Options:${NC}"
echo -e "1. Restart both services:"
echo -e "   ${BOLD}sudo systemctl restart shairport-sync.service${NC}"
echo -e "   ${BOLD}sudo systemctl restart pi-airplay.service${NC}"
echo -e ""
echo -e "2. Fix permissions for metadata pipe:"
echo -e "   ${BOLD}sudo rm /tmp/shairport-sync-metadata${NC}"
echo -e "   ${BOLD}sudo mkfifo /tmp/shairport-sync-metadata${NC}"
echo -e "   ${BOLD}sudo chmod 666 /tmp/shairport-sync-metadata${NC}"
echo -e ""
echo -e "3. Run services manually for debugging:"
echo -e "   ${BOLD}shairport-sync${NC}"
echo -e "   ${BOLD}python3 app_airplay.py --port 8000 --host 0.0.0.0${NC}"
echo -e ""
echo -e "Need more help? Check the README.md for detailed instructions."