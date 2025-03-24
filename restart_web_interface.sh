
#!/bin/bash
# Script to restart Pi-AirPlay web interface

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BOLD}Restarting Pi-AirPlay Web Interface...${NC}"

# Find and kill any existing app_airplay.py process
echo -e "${YELLOW}→${NC} Stopping any existing web interface processes..."
pkill -f "python.*app_airplay\.py" || echo -e "${YELLOW}→${NC} No existing process found"

# Wait a moment to ensure port is freed
sleep 2

# Check if port 8000 is still in use
if lsof -i:8000 > /dev/null 2>&1; then
  echo -e "${RED}✗${NC} Port 8000 is still in use. Trying to forcefully free it..."
  # Try to forcefully terminate whatever is using port 8000
  fuser -k 8000/tcp
  sleep 2
else
  echo -e "${GREEN}✓${NC} Port 8000 is available"
fi

# Start the web interface
echo -e "${YELLOW}→${NC} Starting Pi-AirPlay web interface..."
echo -e "${YELLOW}→${NC} Interface will be available at: http://$(hostname -I | awk '{print $1}'):8000"

# Use host 0.0.0.0 to ensure it's accessible from all network interfaces
python3 app_airplay.py --port 8000 --host 0.0.0.0
