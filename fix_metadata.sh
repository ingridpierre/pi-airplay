#!/bin/bash
#
# Metadata Fix Script for Pi-AirPlay
# This script fixes the shairport-sync configuration to enable metadata transfer
#
# Created: March 23, 2025

# Set up logging
LOG_FILE="metadata_fix.log"
echo "$(date) - Running Pi-AirPlay metadata fix..." > "$LOG_FILE"

# Function to log messages
log_message() {
    echo "$(date) - $1" | tee -a "$LOG_FILE"
}

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay Metadata Fix${NC}"
echo -e "${BOLD}=========================================${NC}\n"

# 1. Stop the shairport-sync service
log_message "Stopping shairport-sync service..."
echo -e "${YELLOW}→${NC} Terminating shairport-sync process..."
killall -9 shairport-sync 2>/dev/null
sleep 2

# 2. Clean up the metadata pipe
log_message "Cleaning up the metadata pipe..."
echo -e "${YELLOW}→${NC} Removing and recreating metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
    rm /tmp/shairport-sync-metadata
fi
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata
log_message "Metadata pipe recreated"
echo -e "${GREEN}✓${NC} Metadata pipe recreated"

# 3. Create a local config file with dns-sd backend
log_message "Creating proper shairport-sync configuration..."
echo -e "${YELLOW}→${NC} Creating fixed shairport-sync config..."

mkdir -p config
CONF_FILE="config/shairport-sync.conf"

cat > "$CONF_FILE" << EOF
// Shairport-Sync Configuration for Pi-AirPlay
general = {
  name = "DAD";
  port = 5000;
  interpolation = "basic";
  output_backend = "alsa";
  mdns_backend = "dns-sd";
  drift_tolerance_in_seconds = 0.002;
  ignore_volume_control = "yes";
  volume_range_db = 60;
  log_verbosity = 1;
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

log_message "Created shairport-sync configuration"
echo -e "${GREEN}✓${NC} Created shairport-sync configuration"

# 4. Start shairport-sync with the new config
log_message "Starting shairport-sync with the new config..."
echo -e "${YELLOW}→${NC} Starting shairport-sync on port 5000..."
shairport-sync -c "$CONF_FILE" -v >> "$LOG_FILE" 2>&1 &
SHAIRPORT_PID=$!
sleep 3

# Check if shairport-sync is running
if pgrep -f "shairport-sync" > /dev/null; then
    log_message "shairport-sync started successfully with new config"
    echo -e "${GREEN}✓${NC} shairport-sync started successfully with new config"
else
    log_message "ERROR: Failed to start shairport-sync"
    echo -e "${RED}✗${NC} Failed to start shairport-sync"
    echo -e "   Check log file for details: $LOG_FILE"
fi

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay Metadata Fix Complete!${NC}"
echo -e "${BOLD}=========================================${NC}\n"

echo -e "The metadata configuration has been updated."
echo -e "Shairport-sync should now be able to provide metadata to the web interface."
echo -e ""
echo -e "If you still experience issues:"
echo -e "  ${YELLOW}1.${NC} Check for errors in $LOG_FILE"
echo -e "  ${YELLOW}2.${NC} Restart the Shairport-Sync Service workflow"
echo -e "  ${YELLOW}3.${NC} Restart the Pi-AirPlay Server workflow"
echo -e ""
echo -e "Log saved to: $LOG_FILE"
echo -e "-----------------------------------------"