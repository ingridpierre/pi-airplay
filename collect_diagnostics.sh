
#!/bin/bash
# Pi-AirPlay Diagnostic Information Collection Script
# This script collects comprehensive diagnostic information to help troubleshoot issues

LOG_FILE="pi_airplay_diagnostics.log"
echo "Pi-AirPlay Diagnostic Collection - $(date)" > $LOG_FILE

# Function to run a command and log output
run_and_log() {
  echo "=== $1 ===" >> $LOG_FILE
  echo "$ $2" >> $LOG_FILE
  eval "$2" >> $LOG_FILE 2>&1
  echo -e "\n" >> $LOG_FILE
}

echo "Collecting diagnostic information. This may take a moment..."

# System information
run_and_log "System Information" "uname -a"
run_and_log "Operating System" "cat /etc/os-release"
run_and_log "Hostname" "hostname"
run_and_log "IP Addresses" "hostname -I"
run_and_log "Uptime" "uptime"

# System resources
run_and_log "CPU Info" "cat /proc/cpuinfo"
run_and_log "Memory Usage" "free -h"
run_and_log "Disk Space" "df -h"
run_and_log "Running Processes" "ps aux | grep -E 'python|shairport|flask'"

# Audio configuration
run_and_log "Audio Devices" "aplay -l"
run_and_log "PulseAudio Status" "command -v pulseaudio && pulseaudio --check"
run_and_log "ALSA Cards" "cat /proc/asound/cards"

# Network
run_and_log "Network Interfaces" "ip addr show"
run_and_log "Network Routes" "ip route"
run_and_log "Listening Ports" "ss -tuln || netstat -tuln"
run_and_log "Port 8000 Usage" "ss -tuln | grep 8000 || netstat -tuln | grep 8000"

# Check services
run_and_log "Shairport-sync Service Status" "command -v systemctl && systemctl status shairport-sync.service"
run_and_log "Pi-AirPlay Service Status" "command -v systemctl && systemctl status pi-airplay.service"

# Check Pi-AirPlay files
run_and_log "Pi-AirPlay Files" "ls -la"
run_and_log "Template Files" "ls -la templates/"
run_and_log "Static Files" "ls -la static/"

# Check if app is running
run_and_log "Python Processes" "ps aux | grep python"
run_and_log "Shairport Processes" "ps aux | grep shairport"

# Test connectivity
run_and_log "Curl localhost:8000" "curl -v --max-time 5 http://localhost:8000/ 2>&1"
IP=$(hostname -I | awk '{print $1}')
run_and_log "Curl IP:8000" "curl -v --max-time 5 http://${IP}:8000/ 2>&1"

# Test metadata pipe
run_and_log "Metadata Pipe Check" "ls -la /tmp/shairport-sync-metadata"

# Collect journal logs if available
run_and_log "Pi-AirPlay Service Logs" "command -v journalctl && journalctl -u pi-airplay.service -n 50"
run_and_log "Shairport-sync Service Logs" "command -v journalctl && journalctl -u shairport-sync.service -n 50"

echo "Diagnostic information collected in $LOG_FILE"
echo "Please share this file to help troubleshoot your issue."
