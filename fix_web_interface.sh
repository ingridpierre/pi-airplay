
#!/bin/bash

# Colors for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "===== Pi-AirPlay Web Interface Troubleshooter ====="

# Get IP address
PI_IP=$(hostname -I | awk '{print $1}')
if [ -z "$PI_IP" ]; then
    PI_IP=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1' | head -n 1)
fi

# Check for critical directories and files
echo "Checking configuration..."

if [ -d "static" ]; then
    echo -e "${GREEN}✓${NC} Static directory exists"
else
    echo -e "${RED}✗${NC} Static directory missing"
fi

if [ -d "templates" ]; then
    echo -e "${GREEN}✓${NC} Templates directory exists"
else
    echo -e "${RED}✗${NC} Templates directory missing"
fi

# Check for critical template files
if [ -f "templates/display.html" ]; then
    echo -e "${GREEN}✓${NC} Template exists: display.html"
else
    echo -e "${RED}✗${NC} Template missing: display.html"
fi

if [ -f "templates/debug.html" ]; then
    echo -e "${GREEN}✓${NC} Template exists: debug.html"
else
    echo -e "${RED}✗${NC} Template missing: debug.html"
fi

# Verify that app_airplay.py has the debug route
if grep -n "@app.route('/debug')" app_airplay.py > /dev/null; then
    LINE_NUM=$(grep -n "@app.route('/debug')" app_airplay.py | cut -d: -f1)
    echo -e "${LINE_NUM}:@app.route('/debug')"
    echo -e "${GREEN}✓${NC} Checked routes configuration"
else
    echo -e "${RED}✗${NC} Missing debug route in app_airplay.py"
fi

# Check if the web app is running on port 8000
echo "Checking if web app is running on port 8000..."
if command -v netstat > /dev/null; then
    if netstat -tuln | grep ":8000" > /dev/null; then
        echo -e "${GREEN}✓${NC} Web app is running on port 8000"
        PROCESS_INFO=$(ps aux | grep "python.*app_airplay\.py" | grep -v grep)
        echo "Process info: $PROCESS_INFO"
    else
        echo -e "${RED}ERROR:${NC} Web app not detected on port 8000"
    fi
else
    echo -e "${YELLOW}Command netstat not found - installing net-tools package${NC}"
    sudo apt-get update && sudo apt-get install -y net-tools
    if netstat -tuln | grep ":8000" > /dev/null; then
        echo -e "${GREEN}✓${NC} Web app is running on port 8000"
        PROCESS_INFO=$(ps aux | grep "python.*app_airplay\.py" | grep -v grep)
        echo "Process info: $PROCESS_INFO"
    else
        echo -e "${RED}ERROR:${NC} Web app not detected on port 8000"
    fi
fi

# Test URLs with better error handling and timeout
echo "Testing URLs..."

test_url() {
    local url=$1
    echo "Testing ${url}..."
    response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)
    
    if [ "$response" = "000" ]; then
        echo -e "${RED}WARNING:${NC} URL $url returned status $response or timed out."
        echo -e "${YELLOW}This could indicate a network/firewall issue or the server is not running.${NC}"
        return 1
    elif [ "$response" = "200" ]; then
        echo -e "${GREEN}✓${NC} URL $url is accessible (HTTP 200)"
        return 0
    else
        echo -e "${RED}WARNING:${NC} URL $url returned status $response"
        return 1
    fi
}

# Check both localhost and actual IP URLs
LOCALHOST_OK=true
IP_OK=true

# Test localhost URLs
test_url "http://localhost:8000/" || LOCALHOST_OK=false
test_url "http://localhost:8000/debug" || LOCALHOST_OK=false

# Test IP-based URLs
test_url "http://${PI_IP}:8000/" || IP_OK=false
test_url "http://${PI_IP}:8000/debug" || IP_OK=false

# Advanced network diagnostics if we're having issues
if [ "$LOCALHOST_OK" = false ] || [ "$IP_OK" = false ]; then
    echo -e "${YELLOW}Running network diagnostics...${NC}"
    echo "Checking if port 8000 is open on all interfaces..."
    if command -v ss > /dev/null; then
        ss -tuln | grep ":8000"
    elif command -v netstat > /dev/null; then
        netstat -tuln | grep ":8000"
    fi
    
    echo "Checking firewall status..."
    if command -v ufw > /dev/null; then
        ufw status
    elif command -v iptables > /dev/null; then
        iptables -L -n
    fi
    
    echo "Checking listening interfaces in app_airplay.py..."
    grep -n "host=" app_airplay.py
fi

if [ "$LOCALHOST_OK" = true ] && [ "$IP_OK" = false ]; then
    echo -e "${YELLOW}NOTE: If localhost URLs work but IP URLs fail, this could be due to:${NC}"
    echo -e "1. Your app is binding to 'localhost' or '127.0.0.1' instead of '0.0.0.0'"
    echo -e "2. A firewall is blocking external connections to port 8000"
    echo -e "3. The network interface is not properly configured"
elif [ "$LOCALHOST_OK" = false ] && [ "$IP_OK" = true ]; then
    echo -e "${YELLOW}NOTE: If IP URLs work but localhost fails, this is normal for external access.${NC}"
    echo -e "Always use http://${PI_IP}:8000 when accessing from another device."
fi

echo "===== Troubleshooting Complete ====="
echo -e "To access the web interface, use: ${GREEN}http://${PI_IP}:8000${NC}"
echo -e "To access the debug interface, use: ${GREEN}http://${PI_IP}:8000/debug${NC}"
echo -e "${YELLOW}NOTE: Always use the actual IP address when accessing from another device, not 'localhost'${NC}"
echo "If issues persist, check the console output for errors."

# Suggest how to restart the service if needed
echo -e "\n${YELLOW}If the web interface is not responding, you can restart the service:${NC}"
echo "sudo systemctl restart pi-airplay.service"
