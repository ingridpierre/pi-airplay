#!/bin/bash

# Clean fix script for Pi-AirPlay
# This script fixes common issues with shairport-sync and Pi-AirPlay

# Color formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}Pi-AirPlay Clean Fix Tool${NC}\n"
echo -e "This script will fix common issues with Pi-AirPlay and shairport-sync."
echo -e "Note: You may need to run this script with sudo.\n"

# Check if we have root privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}⚠ Warning: Running without root privileges. Some operations may fail.${NC}"
  echo -e "Consider running with: sudo ./clean_fix.sh\n"
fi

# Stop any running processes
echo -e "${YELLOW}→${NC} Stopping any running processes..."
sudo systemctl stop shairport-sync.service 2>/dev/null
sudo systemctl stop pi-airplay.service 2>/dev/null
killall -9 shairport-sync 2>/dev/null
killall -9 python3 2>/dev/null
echo -e "${GREEN}✓${NC} Processes stopped."

# Fix the metadata pipe
echo -e "\n${YELLOW}→${NC} Setting up metadata pipe..."
sudo rm -f /tmp/shairport-sync-metadata
sudo mkfifo /tmp/shairport-sync-metadata
sudo chmod 666 /tmp/shairport-sync-metadata
echo -e "${GREEN}✓${NC} Metadata pipe created with correct permissions."

# Update shairport-sync configuration
echo -e "\n${YELLOW}→${NC} Checking shairport-sync configuration..."
if grep -q "mdns_backend.*=.*\"avahi\"" config/shairport-sync.conf; then
  echo -e "${YELLOW}⚠ Warning: Using Avahi mDNS backend which may cause issues if Avahi isn't running.${NC}"
  echo -e "   Updating config to use dummy mDNS backend..."
  sed -i 's/mdns_backend.*=.*"avahi"/mdns_backend = "dummy"/' config/shairport-sync.conf
  echo -e "${GREEN}✓${NC} Configuration updated."
else
  echo -e "${GREEN}✓${NC} Configuration is already using non-Avahi backend."
fi

# Verify ports are not in conflict
echo -e "\n${YELLOW}→${NC} Checking for port conflicts..."
if grep -q "port.*=.*5000" config/shairport-sync.conf; then
  echo -e "${YELLOW}⚠ Note: shairport-sync is using port 5000 for AirPlay.${NC}"
fi

# Check if the pi-airplay.service exists
echo -e "\n${YELLOW}→${NC} Checking service files..."
if [ -f /etc/systemd/system/pi-airplay.service ]; then
  echo -e "${GREEN}✓${NC} Pi-AirPlay service file exists."
else
  echo -e "${YELLOW}⚠ Warning: Pi-AirPlay service is not installed.${NC}"
  echo -e "   Run install_services.sh to install the services."
fi

# Check if the shairport-sync.service exists
if [ -f /etc/systemd/system/shairport-sync.service ]; then
  echo -e "${GREEN}✓${NC} Shairport-sync service file exists."
else
  echo -e "${YELLOW}⚠ Warning: Shairport-sync service is not installed.${NC}"
  echo -e "   Run install_services.sh to install the services."
fi

# Restart services
echo -e "\n${YELLOW}→${NC} Starting services..."
if [ -f /etc/systemd/system/shairport-sync.service ]; then
  sudo systemctl daemon-reload
  sudo systemctl start shairport-sync.service
  echo -e "${GREEN}✓${NC} Shairport-sync service started."
else
  echo -e "${YELLOW}⚠ Warning: Can't start shairport-sync service (not installed).${NC}"
  echo -e "   Starting manually..."
  shairport-sync -c $(pwd)/config/shairport-sync.conf -m dummy -o alsa -- -d default &
  echo -e "${GREEN}✓${NC} Shairport-sync started manually."
fi

sleep 2

if [ -f /etc/systemd/system/pi-airplay.service ]; then
  sudo systemctl start pi-airplay.service
  echo -e "${GREEN}✓${NC} Pi-AirPlay service started."
else
  echo -e "${YELLOW}⚠ Warning: Can't start pi-airplay service (not installed).${NC}"
  echo -e "   Starting manually..."
  python3 app_airplay.py --port 8000 --host 0.0.0.0 &
  echo -e "${GREEN}✓${NC} Pi-AirPlay started manually."
fi

# Final status check
echo -e "\n${BOLD}Status Check:${NC}"
echo -e "${YELLOW}→${NC} Checking if shairport-sync is running..."
if pgrep -f shairport-sync > /dev/null; then
  echo -e "${GREEN}✓${NC} Shairport-sync is running."
else
  echo -e "${RED}✗ Error: Shairport-sync failed to start.${NC}"
  echo -e "   Try running: shairport-sync -c $(pwd)/config/shairport-sync.conf -m dummy -o alsa -- -d default"
fi

echo -e "${YELLOW}→${NC} Checking if Pi-AirPlay web interface is running..."
if pgrep -f "python.*app_airplay.py" > /dev/null; then
  echo -e "${GREEN}✓${NC} Pi-AirPlay web interface is running."
else
  echo -e "${RED}✗ Error: Pi-AirPlay web interface failed to start.${NC}"
  echo -e "   Try running: python3 app_airplay.py --port 8000 --host 0.0.0.0"
fi

# Print access information
echo -e "\n${BOLD}Access Information:${NC}"
echo -e "Pi-AirPlay web interface: http://localhost:8000"
echo -e "AirPlay device name: DAD"

echo -e "\n${BOLD}Cleanup Complete!${NC}"
echo -e "If you're still experiencing issues, try rebooting your Raspberry Pi."