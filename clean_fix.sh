#!/bin/bash
#
# Clean Fix Script for Pi-AirPlay
# This script completely cleans up all running instances and properly
# configures port assignments to avoid conflicts with legacy installations.
#
# Created: March 23, 2025

# Set up logging
LOG_FILE="clean_fix.log"
echo "$(date) - Running Pi-AirPlay clean fix..." > "$LOG_FILE"

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
echo -e "${BOLD}   Pi-AirPlay Clean Fix${NC}"
echo -e "${BOLD}=========================================${NC}\n"

# 1. Stop all running Python and shairport-sync processes
log_message "Stopping all Python processes..."
echo -e "${YELLOW}→${NC} Terminating all Python and shairport-sync processes..."
sudo killall -9 python python3 shairport-sync 2>/dev/null
sleep 2

# 2. Check nothing is running on our ports
log_message "Checking ports 5000 and 8000..."
PROCESSES_5000=$(sudo netstat -tulpn | grep :5000 || echo "None")
PROCESSES_8000=$(sudo netstat -tulpn | grep :8000 || echo "None")

if [[ "$PROCESSES_5000" != "None" ]]; then
    log_message "WARNING: Processes still using port 5000: $PROCESSES_5000"
    echo -e "${RED}✗${NC} Processes still using port 5000"
    echo -e "   Attempting to terminate them..."
    sudo fuser -k 5000/tcp 2>/dev/null
fi

if [[ "$PROCESSES_8000" != "None" ]]; then
    log_message "WARNING: Processes still using port 8000: $PROCESSES_8000"
    echo -e "${RED}✗${NC} Processes still using port 8000"
    echo -e "   Attempting to terminate them..."
    sudo fuser -k 8000/tcp 2>/dev/null
fi

# 3. Clean up the metadata pipe
log_message "Cleaning up the metadata pipe..."
echo -e "${YELLOW}→${NC} Removing and recreating metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
    rm /tmp/shairport-sync-metadata
fi
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata
log_message "Metadata pipe recreated"

# 4. Create proper shairport-sync configuration with port 5000
log_message "Creating shairport-sync configuration..."
echo -e "${YELLOW}→${NC} Creating proper shairport-sync config..."

mkdir -p /usr/local/etc
CONF_FILE="/usr/local/etc/shairport-sync.conf"

cat > "$CONF_FILE" << EOF
// Shairport-Sync Configuration for Pi-AirPlay
general = {
  name = "DAD";
  port = 5000;
  interpolation = "basic";
  output_backend = "alsa";
  mdns_backend = "avahi";
  drift_tolerance_in_seconds = 0.002;
  ignore_volume_control = "no";
  volume_range_db = 60;
  regtype = "_raop._tcp";
  playback_mode = "stereo";
};

alsa = {
  output_device = "default"; // Will be auto-detected
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

# 5. Start shairport-sync on port 5000
log_message "Starting shairport-sync on port 5000..."
echo -e "${YELLOW}→${NC} Starting shairport-sync on port 5000..."
shairport-sync -c "$CONF_FILE" -v >> "$LOG_FILE" 2>&1 &
SHAIRPORT_PID=$!
sleep 3

# Check if shairport-sync is running
if pgrep -f "shairport-sync" > /dev/null; then
    log_message "shairport-sync started successfully on port 5000"
    echo -e "${GREEN}✓${NC} shairport-sync started successfully on port 5000"
else
    log_message "ERROR: Failed to start shairport-sync"
    echo -e "${RED}✗${NC} Failed to start shairport-sync"
    echo -e "   Check log file for details: $LOG_FILE"
fi

# 6. Start Pi-AirPlay web interface on port 8000
log_message "Starting Pi-AirPlay web interface on port 8000..."
echo -e "${YELLOW}→${NC} Starting Pi-AirPlay web interface on port 8000..."

# Determine if the virtual environment exists
if [ -d "venv" ]; then
    log_message "Using virtual environment..."
    source venv/bin/activate
    PYTHON="python"
else
    log_message "Using system Python..."
    PYTHON="python3"
fi

$PYTHON app_airplay.py --port 8000 --host 0.0.0.0 >> "$LOG_FILE" 2>&1 &
WEB_PID=$!
sleep 3

# 7. Verify everything is running correctly
log_message "Verifying services..."
echo -e "${YELLOW}→${NC} Verifying services..."

# Check for the web interface
if pgrep -f "app_airplay.py --port 8000" > /dev/null; then
    log_message "Pi-AirPlay web interface running on port 8000"
    echo -e "${GREEN}✓${NC} Pi-AirPlay web interface running on port 8000"
else
    log_message "ERROR: Pi-AirPlay web interface not running"
    echo -e "${RED}✗${NC} Pi-AirPlay web interface not running"
    echo -e "   Check log file for details: $LOG_FILE"
fi

# Get IP address
IP_ADDRESS=$(hostname -I | awk '{print $1}')

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay is now running!${NC}"
echo -e "${BOLD}=========================================${NC}\n"

echo -e "Services status:"
echo -e "  ${GREEN}•${NC} AirPlay service on port 5000"
echo -e "  ${GREEN}•${NC} Web interface on port 8000"
echo -e ""
echo -e "Access the web interface at: ${BOLD}http://$IP_ADDRESS:8000${NC}"
echo -e "Connect to ${BOLD}DAD${NC} via AirPlay from your Apple device"
echo -e ""
echo -e "If you still experience issues:"
echo -e "  ${YELLOW}1.${NC} Reboot your Raspberry Pi"
echo -e "  ${YELLOW}2.${NC} Check for errors in $LOG_FILE"
echo -e "  ${YELLOW}3.${NC} Try running this script again"
echo -e ""
echo -e "Log saved to: $LOG_FILE"
echo -e "-----------------------------------------"