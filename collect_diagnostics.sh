
#!/bin/bash

# Pi-AirPlay diagnostic script
# This script collects detailed diagnostics about your Pi-AirPlay setup

# Colors for better visibility
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

LOG_FILE="pi_airplay_diagnostics_$(date +%Y%m%d_%H%M%S).log"

# Function to log information
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

log "===== Pi-AirPlay Diagnostic Collection ====="
log "Date: $(date)"
log "Hostname: $(hostname)"
log "IP Addresses: $(hostname -I)"
log ""

# System information
log "===== System Information ====="
log "OS Version:"
cat /etc/os-release | tee -a "$LOG_FILE"
log ""
log "Kernel Version: $(uname -a)"
log ""
log "Memory Usage:"
free -h | tee -a "$LOG_FILE"
log ""
log "Disk Usage:"
df -h | tee -a "$LOG_FILE"
log ""

# Network information
log "===== Network Information ====="
log "Network Interfaces:"
ip addr | tee -a "$LOG_FILE"
log ""
log "Listening Ports:"
if command -v netstat > /dev/null; then
    netstat -tuln | tee -a "$LOG_FILE"
elif command -v ss > /dev/null; then
    ss -tuln | tee -a "$LOG_FILE"
else
    log "No network port tool found (netstat or ss)"
fi
log ""
log "Route Table:"
ip route | tee -a "$LOG_FILE"
log ""
log "Firewall Status:"
if command -v ufw > /dev/null; then
    ufw status | tee -a "$LOG_FILE"
elif command -v iptables > /dev/null; then
    iptables -L -n | tee -a "$LOG_FILE"
else
    log "No firewall tool found"
fi
log ""

# Audio information
log "===== Audio Information ====="
log "ALSA Devices:"
if command -v aplay > /dev/null; then
    aplay -l | tee -a "$LOG_FILE"
    log ""
    aplay -L | tee -a "$LOG_FILE"
else
    log "aplay not found"
fi
log ""
log "Audio Cards:"
cat /proc/asound/cards 2>/dev/null | tee -a "$LOG_FILE" || log "No audio cards info available"
log ""
log "ALSA Config:"
if [ -f "/etc/asound.conf" ]; then
    cat /etc/asound.conf | tee -a "$LOG_FILE"
elif [ -f "~/.asoundrc" ]; then
    cat ~/.asoundrc | tee -a "$LOG_FILE"
else
    log "No ALSA config found"
fi
log ""

# Shairport-sync information
log "===== Shairport-Sync Information ====="
log "Shairport-Sync Installed:"
if command -v shairport-sync > /dev/null; then
    log "Yes - $(shairport-sync -V 2>&1)"
else
    log "No"
fi
log ""
log "Shairport-Sync Running:"
ps aux | grep shairport-sync | grep -v grep | tee -a "$LOG_FILE" || log "Not running"
log ""
log "Shairport-Sync Config:"
if [ -f "/usr/local/etc/shairport-sync.conf" ]; then
    cat /usr/local/etc/shairport-sync.conf | tee -a "$LOG_FILE"
elif [ -f "/etc/shairport-sync.conf" ]; then
    cat /etc/shairport-sync.conf | tee -a "$LOG_FILE"
else
    log "No shairport-sync config found"
fi
log ""
log "Metadata Pipe:"
if [ -p "/tmp/shairport-sync-metadata" ]; then
    ls -la /tmp/shairport-sync-metadata | tee -a "$LOG_FILE"
    log "Pipe exists and permissions are correct"
else
    log "Metadata pipe does not exist"
fi
log ""

# Pi-AirPlay service
log "===== Pi-AirPlay Service Information ====="
log "Service Status:"
systemctl status pi-airplay.service 2>&1 | tee -a "$LOG_FILE" || log "Service not found or systemctl not available"
log ""
log "Service Log:"
journalctl -u pi-airplay.service -n 100 --no-pager 2>&1 | tee -a "$LOG_FILE" || log "Cannot access logs"
log ""

# Web server test
log "===== Web Server Tests ====="
PI_IP=$(hostname -I | awk '{print $1}')
log "Testing localhost:8000:"
curl -s -I http://localhost:8000/ 2>&1 | tee -a "$LOG_FILE" || log "Failed to connect to localhost:8000"
log ""
log "Testing ${PI_IP}:8000:"
curl -s -I http://${PI_IP}:8000/ 2>&1 | tee -a "$LOG_FILE" || log "Failed to connect to ${PI_IP}:8000"
log ""

# Check Python environment
log "===== Python Environment ====="
log "Python Version:"
python3 --version 2>&1 | tee -a "$LOG_FILE" || log "Python3 not found"
log ""
log "Flask and Dependencies:"
pip3 list | grep -E "flask|socket|audio" 2>&1 | tee -a "$LOG_FILE" || log "pip3 not found or no dependencies listed"
log ""

log "===== Diagnostic Collection Complete ====="
log "Diagnostics saved to: $LOG_FILE"
echo -e "${GREEN}Diagnostics collection complete!${NC}"
echo -e "Log file: ${GREEN}$LOG_FILE${NC}"
echo "Please share this log file to get help with troubleshooting."
