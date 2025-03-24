#!/bin/bash

# Troubleshooting script for Pi-AirPlay
# This script helps diagnose and fix common issues with shairport-sync and Pi-AirPlay

# Color formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}Pi-AirPlay Troubleshooting Tool${NC}\n"

# Check if shairport-sync is installed
echo -e "${YELLOW}→${NC} Checking if shairport-sync is installed..."
if ! command -v shairport-sync &> /dev/null; then
  echo -e "${RED}✗ Error: shairport-sync is not installed.${NC}"
  echo "Please install it using: sudo apt-get install shairport-sync"
  exit 1
else
  echo -e "${GREEN}✓${NC} shairport-sync is installed."
  SHAIRPORT_VERSION=$(shairport-sync -V | head -n 1)
  echo "   Version: $SHAIRPORT_VERSION"
fi

# Check if metadata pipe exists
echo -e "\n${YELLOW}→${NC} Checking metadata pipe..."
if [ -p /tmp/shairport-sync-metadata ]; then
  echo -e "${GREEN}✓${NC} Metadata pipe exists."
  # Check permissions
  PERMISSIONS=$(stat -c "%a" /tmp/shairport-sync-metadata)
  if [ "$PERMISSIONS" != "666" ]; then
    echo -e "${YELLOW}⚠ Warning: Incorrect permissions on metadata pipe: $PERMISSIONS${NC}"
    echo "   Fixing permissions..."
    chmod 666 /tmp/shairport-sync-metadata
    echo -e "${GREEN}✓${NC} Permissions fixed."
  else
    echo "   Permissions: $PERMISSIONS (correct)"
  fi
else
  echo -e "${YELLOW}⚠ Warning: Metadata pipe does not exist.${NC}"
  echo "   Creating pipe..."
  mkfifo /tmp/shairport-sync-metadata
  chmod 666 /tmp/shairport-sync-metadata
  echo -e "${GREEN}✓${NC} Metadata pipe created."
fi

# Check if shairport-sync process is running
echo -e "\n${YELLOW}→${NC} Checking if shairport-sync is running..."
if pgrep -f shairport-sync > /dev/null; then
  echo -e "${GREEN}✓${NC} shairport-sync is running."
  PS_INFO=$(ps -ef | grep shairport-sync | grep -v grep)
  echo "   Process: $PS_INFO"
else
  echo -e "${RED}✗ Error: shairport-sync is not running.${NC}"
fi

# Check if the web interface is running
echo -e "\n${YELLOW}→${NC} Checking if Pi-AirPlay web interface is running..."
if pgrep -f "python.*app_airplay.py" > /dev/null; then
  echo -e "${GREEN}✓${NC} Pi-AirPlay web interface is running."
  PS_INFO=$(ps -ef | grep "python.*app_airplay.py" | grep -v grep)
  echo "   Process: $PS_INFO"
else
  echo -e "${RED}✗ Error: Pi-AirPlay web interface is not running.${NC}"
fi

# Check if systemd services are enabled
echo -e "\n${YELLOW}→${NC} Checking systemd service status..."
if systemctl is-enabled shairport-sync.service &> /dev/null; then
  echo -e "${GREEN}✓${NC} shairport-sync.service is enabled."
else
  echo -e "${YELLOW}⚠ Warning: shairport-sync.service is not enabled.${NC}"
fi

if systemctl is-enabled pi-airplay.service &> /dev/null; then
  echo -e "${GREEN}✓${NC} pi-airplay.service is enabled."
else
  echo -e "${YELLOW}⚠ Warning: pi-airplay.service is not enabled.${NC}"
fi

# Check audio devices
echo -e "\n${YELLOW}→${NC} Checking audio devices..."
if command -v aplay &> /dev/null; then
  echo "Available audio devices:"
  aplay -l
else
  echo -e "${YELLOW}⚠ Warning: aplay command not found, can't list audio devices.${NC}"
fi

# Check avahi daemon
echo -e "\n${YELLOW}→${NC} Checking Avahi daemon..."
if systemctl is-active avahi-daemon &> /dev/null; then
  echo -e "${GREEN}✓${NC} Avahi daemon is running."
else
  echo -e "${YELLOW}⚠ Warning: Avahi daemon is not running.${NC}"
  echo "   This may affect mDNS discovery."
  
  # Check if using dummy backend in config
  if grep -q "mdns_backend.*=.*\"dummy\"" config/shairport-sync.conf; then
    echo -e "${GREEN}✓${NC} Using dummy mDNS backend in config, which is appropriate when Avahi is not available."
  else
    echo -e "${YELLOW}⚠ Suggestion: Consider changing mdns_backend to \"dummy\" in config/shairport-sync.conf${NC}"
  fi
fi

# Provide recovery options
echo -e "\n${BOLD}Recovery Options:${NC}"
echo "1. Restart both services:"
echo "   sudo systemctl restart shairport-sync.service"
echo "   sudo systemctl restart pi-airplay.service"
echo ""
echo "2. Fix permissions for metadata pipe:"
echo "   sudo rm /tmp/shairport-sync-metadata"
echo "   sudo mkfifo /tmp/shairport-sync-metadata"
echo "   sudo chmod 666 /tmp/shairport-sync-metadata"
echo ""
echo "3. Run services manually for debugging:"
echo "   shairport-sync -c config/shairport-sync.conf -m dummy -o alsa -- -d default"
echo "   python3 app_airplay.py --port 8000 --host 0.0.0.0"
echo ""
echo -e "${BOLD}Need more help?${NC} Check the README.md for detailed instructions."