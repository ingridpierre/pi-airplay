#!/bin/bash
# Script to ensure shairport-sync is running correctly

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}Starting Shairport-Sync for Pi-AirPlay...${NC}"

# Ensure the metadata pipe exists with correct permissions
if [ ! -p /tmp/shairport-sync-metadata ]; then
  echo -e "${YELLOW}→${NC} Creating metadata pipe..."
  mkfifo /tmp/shairport-sync-metadata
fi

echo -e "${YELLOW}→${NC} Setting correct permissions for metadata pipe..."
chmod 666 /tmp/shairport-sync-metadata

# Check if system shairport-sync is running
if ! pgrep -x "shairport-sync" > /dev/null; then
  echo -e "${YELLOW}→${NC} Starting shairport-sync..."
  shairport-sync -v
else
  echo -e "${GREEN}✓${NC} Shairport-sync is already running."
fi

# Verify metadata pipe is working
if [ -p /tmp/shairport-sync-metadata ]; then
  echo -e "${GREEN}✓${NC} Metadata pipe verified at /tmp/shairport-sync-metadata"
else
  echo -e "${RED}✗${NC} Error: Metadata pipe not found"
  exit 1
fi

echo -e "${GREEN}✓${NC} All systems ready. Pi-AirPlay is now using shairport-sync."
