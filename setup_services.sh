#!/bin/bash

# Set up Systemd services for Pi-AirPlay
# This script must be run with sudo

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Please run as root (sudo)${NC}"
  exit 1
fi

# Get the current directory
INSTALL_DIR="$(pwd)"
echo -e "${BOLD}Installing services from:${NC} $INSTALL_DIR"

# Check if files exist
if [ ! -f "$INSTALL_DIR/app_airplay.py" ]; then
  echo -e "${RED}Error: app_airplay.py not found in current directory${NC}"
  exit 1
fi

if [ ! -f "$INSTALL_DIR/config/shairport-sync.conf" ]; then
  echo -e "${RED}Error: config/shairport-sync.conf not found${NC}"
  exit 1
fi

# Clean up any existing metadata pipe
echo -e "${YELLOW}→${NC} Setting up metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
  rm /tmp/shairport-sync-metadata
fi
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata
echo -e "${GREEN}✓${NC} Metadata pipe created with proper permissions"

# Get the current user
CURRENT_USER=$(who am i | awk '{print $1}')
if [ -z "$CURRENT_USER" ]; then
  CURRENT_USER="pi"  # Default to pi user
fi
echo -e "${BOLD}Setting up services for user:${NC} $CURRENT_USER"

# Create the shairport-sync service
echo -e "${YELLOW}→${NC} Creating shairport-sync service..."
cat > /etc/systemd/system/shairport-sync.service << EOL
[Unit]
Description=Shairport Sync - AirPlay Audio Receiver
After=sound.target
Requires=avahi-daemon.service
After=avahi-daemon.service

[Service]
ExecStart=/bin/bash -c "while true; do chmod 666 /tmp/shairport-sync-metadata 2>/dev/null || (mkfifo /tmp/shairport-sync-metadata && chmod 666 /tmp/shairport-sync-metadata) && shairport-sync -c $INSTALL_DIR/config/shairport-sync.conf -v; sleep 2; done"
Restart=always
RestartSec=5
User=root
Group=root
WorkingDirectory=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOL

# Create the Pi-AirPlay web interface service
echo -e "${YELLOW}→${NC} Creating Pi-AirPlay web interface service..."
cat > /etc/systemd/system/pi-airplay.service << EOL
[Unit]
Description=Pi-AirPlay Web Interface
After=network.target shairport-sync.service
Wants=shairport-sync.service

[Service]
ExecStart=/usr/bin/python3 $INSTALL_DIR/app_airplay.py --port 8000 --host 0.0.0.0
Restart=always
RestartSec=5
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOL

echo -e "${GREEN}✓${NC} Service files created"

# Reload systemd and enable services
echo -e "${YELLOW}→${NC} Enabling and starting services..."
systemctl daemon-reload
systemctl enable shairport-sync.service
systemctl enable pi-airplay.service

# Stop any running services first
systemctl stop shairport-sync.service 2>/dev/null
systemctl stop pi-airplay.service 2>/dev/null

# Start the services
systemctl start shairport-sync.service
sleep 2  # Give time for shairport-sync to start
systemctl start pi-airplay.service

# Check service status
echo -e "\n${BOLD}Service Status:${NC}"
systemctl status shairport-sync.service | grep Active
systemctl status pi-airplay.service | grep Active

echo -e "\n${GREEN}${BOLD}Setup Complete!${NC}"
echo -e "Pi-AirPlay services are now configured to start on boot."
echo -e "You can access the web interface at: ${BOLD}http://localhost:8000${NC}"
echo -e "Connect to ${BOLD}DAD${NC} via AirPlay from your Apple device\n"

echo -e "${YELLOW}Control Commands:${NC}"
echo -e "  ${BOLD}sudo systemctl restart shairport-sync${NC} - Restart AirPlay service"
echo -e "  ${BOLD}sudo systemctl restart pi-airplay${NC} - Restart web interface"
echo -e "  ${BOLD}sudo systemctl status shairport-sync${NC} - Check AirPlay service status"
echo -e "  ${BOLD}sudo systemctl status pi-airplay${NC} - Check web interface status"