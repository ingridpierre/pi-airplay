#!/bin/bash
# Pi-AirPlay Startup Script
# This script ensures shairport-sync is running and starts the web interface

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}Starting Pi-AirPlay...${NC}"

# Change to script directory to ensure relative paths work
cd "$(dirname "$0")"

# Ensure the metadata pipe exists and has correct permissions
if [ ! -e /tmp/shairport-sync-metadata ]; then
  echo -e "${YELLOW}→${NC} Creating metadata pipe..."
  mkfifo /tmp/shairport-sync-metadata
fi

echo -e "${YELLOW}→${NC} Setting permissions for metadata pipe..."
chmod 666 /tmp/shairport-sync-metadata

# Check for critical directories
if [ ! -d "templates" ] || [ ! -d "static" ]; then
  echo -e "${RED}✗${NC} Error: Missing required directories. Please check your installation."
else
  echo -e "${GREEN}✓${NC} Required directories present."
fi

# Check if shairport-sync is already running
if ! pgrep -x "shairport-sync" > /dev/null; then
  echo -e "${YELLOW}→${NC} Starting shairport-sync..."
  # Using basic command-line startup without config file to avoid issues
  shairport-sync &
  sleep 2
else
  echo -e "${GREEN}✓${NC} Shairport-sync is already running."
fi

# Verify shairport-sync is running
if pgrep -x "shairport-sync" > /dev/null; then
  echo -e "${GREEN}✓${NC} Shairport-sync verified running."
else
  echo -e "${RED}✗${NC} Error: Could not start shairport-sync."
  # Continue anyway to get the web interface
fi

# Start the web interface
echo -e "${YELLOW}→${NC} Starting Pi-AirPlay web interface..."
echo -e "${YELLOW}→${NC} Interface will be available at: http://$(hostname -I | awk '{print $1}'):8000"
echo -e "${YELLOW}→${NC} Debug interface at: http://$(hostname -I | awk '{print $1}'):8000/debug"

# Use host 0.0.0.0 to ensure it's accessible from all network interfaces
exec python3 app_airplay.py --port 8000 --host 0.0.0.0