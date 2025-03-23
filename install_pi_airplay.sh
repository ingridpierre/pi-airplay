#!/bin/bash
# Pi-AirPlay Installation Script
# This script installs all necessary dependencies and sets up Pi-AirPlay
# for use with IQaudio DAC on Raspberry Pi

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay Installer${NC}"
echo -e "${BOLD}=========================================${NC}\n"
echo -e "This script will install Pi-AirPlay and all dependencies.\n"

# Function to display progress
show_progress() {
  echo -e "${GREEN}✓${NC} $1"
}

# Function to display errors
show_error() {
  echo -e "${RED}✗${NC} $1"
  echo -e "${YELLOW}→${NC} $2"
}

# Check if running as root (needed for some installations)
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}This script requires root privileges to install dependencies.${NC}"
  echo -e "Please run with: ${BOLD}sudo ./install_pi_airplay.sh${NC}\n"
  exit 1
fi

# Step 1: Update system packages
echo -e "\n${BOLD}Step 1:${NC} Updating system packages..."
apt update && apt upgrade -y
if [ $? -eq 0 ]; then
  show_progress "System packages updated"
else
  show_error "Failed to update system packages" "Check your internet connection and try again"
  exit 1
fi

# Step 2: Install required dependencies
echo -e "\n${BOLD}Step 2:${NC} Installing dependencies..."
apt install -y shairport-sync python3-pip python3-flask python3-venv python3-eventlet
if [ $? -eq 0 ]; then
  show_progress "Dependencies installed"
else
  show_error "Failed to install dependencies" "Please check the error message above"
  exit 1
fi

# Step 3: Set up virtual environment
echo -e "\n${BOLD}Step 3:${NC} Setting up Python virtual environment..."
mkdir -p /opt/pi-airplay
cp -r * /opt/pi-airplay/
cd /opt/pi-airplay
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask flask-socketio eventlet pillow
if [ $? -eq 0 ]; then
  show_progress "Python virtual environment set up"
else
  show_error "Failed to set up Python environment" "Please check your Python installation"
  exit 1
fi

# Step 4: Configure shairport-sync
echo -e "\n${BOLD}Step 4:${NC} Configuring Shairport-Sync..."
# First check for audio devices
echo -e "${YELLOW}→${NC} Checking audio devices..."
aplay -l
echo ""

# Ask user for sound card number
echo -e "${YELLOW}→${NC} From the list above, find your IQaudio DAC or USB audio device"
read -p "Enter the card number for your audio device (e.g., 0, 1, 2...): " CARD_NUMBER

# Create shairport-sync configuration
cat > /etc/shairport-sync.conf << EOL
general = {
  name = "Pi-AirPlay";
  interpolation = "basic";
  output_backend = "alsa";
  mdns_backend = "avahi";
  port = 5000;
  drift_tolerance_in_seconds = 0.002;
  ignore_volume_control = "no";
  volume_range_db = 60;
  regtype = "_raop._tcp";
  playback_mode = "stereo";
};

alsa = {
  output_device = "hw:${CARD_NUMBER}";
  mixer_control_name = "PCM";
  mixer_device = "hw:${CARD_NUMBER}";
};

metadata = {
  enabled = "yes";
  include_cover_art = "yes";
  pipe_name = "/tmp/shairport-sync-metadata";
  pipe_timeout = 5000;
};

diagnostics = {
  log_verbosity = 0;
};
EOL

if [ $? -eq 0 ]; then
  show_progress "Shairport-Sync configured with card ${CARD_NUMBER}"
else
  show_error "Failed to configure Shairport-Sync" "Please check permissions"
  exit 1
fi

# Step 5: Create service files
echo -e "\n${BOLD}Step 5:${NC} Creating service files..."

# Create systemd service for shairport-sync
cat > /etc/systemd/system/shairport-sync.service << EOL
[Unit]
Description=Shairport Sync - AirPlay Audio Receiver
After=sound.target
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/shairport-sync
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOL

# Create systemd service for Pi-AirPlay web interface
cat > /etc/systemd/system/pi-airplay.service << EOL
[Unit]
Description=Pi-AirPlay Web Interface
After=network.target shairport-sync.service

[Service]
WorkingDirectory=/opt/pi-airplay
Environment=PATH=/opt/pi-airplay/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=/opt/pi-airplay/venv/bin/python /opt/pi-airplay/app_airplay.py --port 8080
Restart=on-failure
User=pi
Group=pi

[Install]
WantedBy=multi-user.target
EOL

if [ $? -eq 0 ]; then
  show_progress "Service files created"
else
  show_error "Failed to create service files" "Please check permissions"
  exit 1
fi

# Step 6: Enable services
echo -e "\n${BOLD}Step 6:${NC} Enabling services..."
systemctl daemon-reload
systemctl enable shairport-sync.service
systemctl enable pi-airplay.service
systemctl start shairport-sync.service
systemctl start pi-airplay.service

if [ $? -eq 0 ]; then
  show_progress "Services enabled and started"
else
  show_error "Failed to enable services" "Please check systemd status"
  exit 1
fi

# Step 7: Create desktop shortcut for browser
echo -e "\n${BOLD}Step 7:${NC} Creating desktop shortcut..."
HOSTNAME=$(hostname -I | awk '{print $1}')
mkdir -p /home/pi/Desktop

cat > /home/pi/Desktop/Pi-AirPlay.desktop << EOL
[Desktop Entry]
Name=Pi-AirPlay
Comment=Open Pi-AirPlay Web Interface
Exec=chromium-browser --app=http://localhost:8080 --kiosk
Type=Application
Icon=/opt/pi-airplay/static/artwork/default_album.svg
Categories=AudioVideo;
EOL

chmod +x /home/pi/Desktop/Pi-AirPlay.desktop
chown pi:pi /home/pi/Desktop/Pi-AirPlay.desktop

show_progress "Desktop shortcut created"

# Installation complete
echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Installation Complete!${NC}"
echo -e "${BOLD}=========================================${NC}\n"

echo -e "${GREEN}Pi-AirPlay has been installed successfully!${NC}"
echo -e "\nYou can access the web interface at: ${BOLD}http://$HOSTNAME:8080${NC}"
echo -e "Connect to ${BOLD}Pi-AirPlay${NC} via AirPlay from your Apple device"
echo -e "\nTo start in kiosk mode on your Raspberry Pi, click the desktop icon" 
echo -e "or run: ${BOLD}chromium-browser --app=http://localhost:8080 --kiosk${NC}"
echo -e "\nServices will automatically start on boot\n"

exit 0