
#!/bin/bash
# Pi-AirPlay Web Interface Troubleshooter
# Enhanced version for detailed diagnostics

echo "===== Pi-AirPlay Web Interface Troubleshooter ====="

# Use colorful output for better readability
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Basic Configuration Checks ===${NC}"

# Check if static files exist
if [ ! -d "static" ]; then
  echo -e "${RED}ERROR: 'static' directory missing!${NC}"
else
  echo -e "${GREEN}✓ Static directory exists${NC}"
fi

# Check templates
if [ ! -d "templates" ]; then
  echo -e "${RED}ERROR: 'templates' directory missing!${NC}"
else
  echo -e "${GREEN}✓ Templates directory exists${NC}"
  
  # Check for critical templates
  for template in display.html debug.html; do
    if [ ! -f "templates/$template" ]; then
      echo -e "${RED}ERROR: Missing template: $template${NC}"
    else
      echo -e "${GREEN}✓ Template exists: $template${NC}"
    fi
  done
fi

# Check routes in main application
grep -n "route.*debug" app_airplay.py
echo -e "${GREEN}✓ Checked routes configuration${NC}"

echo -e "${BLUE}=== System Status Checks ===${NC}"

# Check system resources
echo "Memory usage:"
free -h

# Check disk space
echo "Disk space:"
df -h | grep -E "/dev/(root|mmcblk0p1)"

# Check Python and Flask
echo "Python version:"
python3 --version

# Try to find processes using port 8000
echo "Processes running on port 8000:"
if command -v lsof >/dev/null 2>&1; then
  lsof -i :8000
elif command -v netstat >/dev/null 2>&1; then
  netstat -tuln | grep ":8000"
elif command -v ss >/dev/null 2>&1; then
  ss -tuln | grep ":8000"
else
  echo -e "${YELLOW}Could not check port usage - netstat, lsof, and ss not available${NC}"
fi

# Check for shairport-sync
if pgrep -x "shairport-sync" > /dev/null; then
  echo -e "${GREEN}✓ Shairport-sync is running${NC}"
else
  echo -e "${RED}✗ Shairport-sync is NOT running${NC}"
fi

# Check if the Python app is running
if pgrep -f "python3.*app_airplay.py" > /dev/null; then
  echo -e "${GREEN}✓ Pi-AirPlay web app is running${NC}"
else
  echo -e "${RED}✗ Pi-AirPlay web app is NOT running${NC}"
fi

echo -e "${BLUE}=== Network Interface Status ===${NC}"

# Show network interfaces
echo "Network interfaces:"
ip addr show | grep -E "inet |^[0-9]"

# Get the IP address of the Pi
PI_IP=$(hostname -I | awk '{print $1}')
echo "Primary IP address: ${PI_IP}"

# Check for firewall rules blocking port 8000
echo "Checking firewall rules (if any):"
if command -v iptables >/dev/null 2>&1; then
  iptables -L | grep -E "8000|reject|drop"
elif command -v ufw >/dev/null 2>&1; then
  ufw status
else
  echo "No firewall utility found to check"
fi

echo -e "${BLUE}=== URL Accessibility Tests ===${NC}"

# Attempt verbose curl to help debug connection issues
echo "Detailed test of http://${PI_IP}:8000/ :"
curl -v --max-time 5 http://${PI_IP}:8000/ 2>&1 | grep -E "< HTTP|Connected to|Failed to connect"

# Test URLs with more verbose output
for base_url in "http://localhost:8000" "http://${PI_IP}:8000" "http://127.0.0.1:8000"; do
  for path in "/" "/debug"; do
    url="${base_url}${path}"
    echo "Testing $url..."
    response=$(curl -s -I --max-time 5 $url)
    http_code=$(echo "$response" | grep HTTP | awk '{print $2}')
    
    if [ -n "$http_code" ] && [ "$http_code" = "200" ]; then
      echo -e "${GREEN}✓ URL $url is accessible (HTTP $http_code)${NC}"
    elif [ -n "$http_code" ]; then
      echo -e "${YELLOW}WARNING: URL $url returned HTTP $http_code${NC}"
    else
      echo -e "${RED}ERROR: URL $url timed out or connection failed${NC}"
    fi
  done
done

echo -e "${BLUE}=== Socket Connectivity Test ===${NC}"
# Test socket direct connection to port 8000
timeout 3 bash -c "</dev/tcp/${PI_IP}/8000" 2>/dev/null
if [ $? -eq 0 ]; then
  echo -e "${GREEN}✓ Socket connection to ${PI_IP}:8000 successful${NC}"
else
  echo -e "${RED}✗ Socket connection to ${PI_IP}:8000 failed${NC}"
fi

echo -e "${BLUE}=== Recommendations ===${NC}"

echo "1. Ensure the Pi-AirPlay service is running:"
echo "   sudo systemctl status pi-airplay.service"
echo "   If not running: sudo systemctl restart pi-airplay.service"

echo "2. Check application logs:"
echo "   sudo journalctl -u pi-airplay.service -n 50"

echo "3. Try starting manually to see errors:"
echo "   ./start_pi_airplay.sh"

echo "4. Check for any network issues:"
echo "   - Is there a firewall on the Pi or your network blocking port 8000?"
echo "   - Are you on the same network as the Pi?"

echo "===== Troubleshooting Complete ====="
echo -e "${GREEN}To access the web interface, use: http://${PI_IP}:8000${NC}"
echo -e "${GREEN}To access the debug interface, use: http://${PI_IP}:8000/debug${NC}"
echo "NOTE: Always use the actual IP address when accessing from another device, not 'localhost'"
