#!/bin/bash

# Install and configure services for Pi-AirPlay
# This script must be run as root (sudo)

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Error: Please run as root (sudo)${NC}"
  exit 1
fi

echo -e "${BOLD}Pi-AirPlay Service Installer${NC}"
echo -e "Setting up autostart services for Pi-AirPlay\n"

# Get the current directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}→${NC} Installing from directory: ${SCRIPT_DIR}"

# Verify necessary files exist
echo -e "${YELLOW}→${NC} Verifying required files..."
if [ ! -f "${SCRIPT_DIR}/app_airplay.py" ]; then
  echo -e "${RED}Error: app_airplay.py not found in ${SCRIPT_DIR}${NC}"
  exit 1
fi

if [ ! -f "${SCRIPT_DIR}/config/shairport-sync.conf" ]; then
  echo -e "${RED}Error: config/shairport-sync.conf not found in ${SCRIPT_DIR}/config${NC}"
  exit 1
fi

echo -e "${GREEN}✓${NC} Required files found"

# Create systemd service files
echo -e "\n${YELLOW}→${NC} Creating systemd service files..."

# Create shairport-sync service
cat > /etc/systemd/system/shairport-sync.service << EOL
[Unit]
Description=Shairport Sync - AirPlay Audio Receiver
After=sound.target network.target
Wants=avahi-daemon.service

[Service]
ExecStartPre=/bin/bash -c "if [ -e /tmp/shairport-sync-metadata ]; then rm /tmp/shairport-sync-metadata; fi && mkfifo /tmp/shairport-sync-metadata && chmod 666 /tmp/shairport-sync-metadata"
ExecStart=/usr/bin/shairport-sync -c ${SCRIPT_DIR}/config/shairport-sync.conf
Restart=always
RestartSec=5
User=root
Group=root
WorkingDirectory=${SCRIPT_DIR}

[Install]
WantedBy=multi-user.target
EOL

# Create Pi-AirPlay web interface service
cat > /etc/systemd/system/pi-airplay.service << EOL
[Unit]
Description=Pi-AirPlay Web Interface
After=network.target shairport-sync.service
Wants=shairport-sync.service

[Service]
ExecStart=/usr/bin/python3 ${SCRIPT_DIR}/app_airplay.py --port 8000 --host 0.0.0.0
Restart=always
RestartSec=5
User=ivpi
Group=ivpi
WorkingDirectory=${SCRIPT_DIR}

[Install]
WantedBy=multi-user.target
EOL

echo -e "${GREEN}✓${NC} Service files created"

# Reload systemd and enable services
echo -e "\n${YELLOW}→${NC} Enabling services to start on boot..."
systemctl daemon-reload
systemctl enable shairport-sync.service
systemctl enable pi-airplay.service

# Stop any already running services
echo -e "\n${YELLOW}→${NC} Stopping any existing services..."
systemctl stop shairport-sync.service 2>/dev/null
systemctl stop pi-airplay.service 2>/dev/null
killall -9 shairport-sync 2>/dev/null
killall -9 python3 2>/dev/null

# Clean up metadata pipe
echo -e "\n${YELLOW}→${NC} Setting up metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
  rm /tmp/shairport-sync-metadata
fi
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata
echo -e "${GREEN}✓${NC} Metadata pipe created"

# Start services
echo -e "\n${YELLOW}→${NC} Starting services..."
systemctl start shairport-sync.service
sleep 2
systemctl start pi-airplay.service
sleep 2

# Check service status
echo -e "\n${BOLD}Service Status:${NC}"
systemctl status shairport-sync.service | grep Active
systemctl status pi-airplay.service | grep Active

# Create a desktop shortcut for kiosk mode
echo -e "\n${YELLOW}→${NC} Creating desktop shortcut for kiosk mode..."
mkdir -p /home/ivpi/Desktop

cat > /home/ivpi/Desktop/Pi-AirPlay.desktop << EOL
[Desktop Entry]
Name=Pi-AirPlay
Comment=Open Pi-AirPlay Web Interface
Exec=chromium-browser --app=http://localhost:8000 --kiosk
Type=Application
Icon=${SCRIPT_DIR}/static/artwork/default_album.svg
Categories=AudioVideo;
Terminal=false
X-KeepTerminal=false
StartupNotify=true
EOL

chmod +x /home/ivpi/Desktop/Pi-AirPlay.desktop
chown ivpi:ivpi /home/ivpi/Desktop/Pi-AirPlay.desktop

echo -e "${GREEN}✓${NC} Desktop shortcut created"

# Setup is complete
echo -e "\n${BOLD}Installation Complete!${NC}"
echo -e "\nPi-AirPlay services are now configured to start automatically on boot."
echo -e "\nAccess the web interface at: ${BOLD}http://localhost:8000${NC}"
echo -e "Connect to ${BOLD}DAD${NC} via AirPlay from your Apple device"
echo -e "\n${YELLOW}Control Commands:${NC}"
echo -e "  ${BOLD}sudo systemctl restart shairport-sync${NC} - Restart AirPlay service"
echo -e "  ${BOLD}sudo systemctl restart pi-airplay${NC} - Restart web interface"
echo -e "  ${BOLD}sudo systemctl status shairport-sync${NC} - Check AirPlay service status"
echo -e "  ${BOLD}sudo systemctl status pi-airplay${NC} - Check web interface status"