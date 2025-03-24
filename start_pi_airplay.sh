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

# Ensure the metadata pipe exists and has correct permissions
if [ ! -e /tmp/shairport-sync-metadata ]; then
  echo -e "${YELLOW}→${NC} Creating metadata pipe..."
  mkfifo /tmp/shairport-sync-metadata
fi

echo -e "${YELLOW}→${NC} Setting permissions for metadata pipe..."
chmod 666 /tmp/shairport-sync-metadata

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
cd "$(dirname "$0")"  # Change to script directory
exec python3 app_airplay.py --port 8000 --host 0.0.0.0