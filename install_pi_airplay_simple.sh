#!/bin/bash
# Pi-AirPlay Installation Script - Simple Version
# This script installs the Pi-AirPlay web interface and configures it to use the system-wide shairport-sync

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay Simplified Installer${NC}"
echo -e "${BOLD}=========================================${NC}\n"
echo -e "This script will install Pi-AirPlay web interface.\n"

# Function to display progress
show_progress() {
  echo -e "${GREEN}✓${NC} $1"
}

# Function to display errors
show_error() {
  echo -e "${RED}✗${NC} $1"
  echo -e "${YELLOW}→${NC} $2"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${YELLOW}This script requires root privileges to install dependencies.${NC}"
  echo -e "Please run with: ${BOLD}sudo ./install_pi_airplay_simple.sh${NC}\n"
  exit 1
fi

# Get username of the non-root user who called sudo
if [ -n "$SUDO_USER" ]; then
  USERNAME="$SUDO_USER"
else
  # Try to get the username of a non-root user with a home directory
  USERNAME=$(getent passwd | grep -v "nologin\|false" | grep "/home" | head -1 | cut -d: -f1)
  
  if [ -z "$USERNAME" ]; then
    # Default to "pi" if no other user is found
    USERNAME="ivpi"
  fi
fi

echo -e "${YELLOW}→${NC} Installing as user: ${BOLD}$USERNAME${NC}"
USER_HOME=$(eval echo ~$USERNAME)

# Step 1: Check if shairport-sync is installed
echo -e "\n${BOLD}Step 1:${NC} Checking for shairport-sync..."
if command -v shairport-sync >/dev/null 2>&1; then
  show_progress "Shairport-sync is already installed"
else
  echo -e "${YELLOW}→${NC} Installing shairport-sync..."
  apt update && apt install -y shairport-sync
  if [ $? -eq 0 ]; then
    show_progress "Shairport-sync installed"
  else
    show_error "Failed to install shairport-sync" "This is required for Pi-AirPlay to work"
    exit 1
  fi
fi

# Step 2: Install Python dependencies
echo -e "\n${BOLD}Step 2:${NC} Installing required dependencies..."
apt install -y python3-pip python3-flask python3-eventlet alsa-utils

pip3 install flask flask-socketio eventlet pillow colorthief requests

if [ $? -eq 0 ]; then
  show_progress "Dependencies installed"
else
  show_error "Failed to install dependencies" "Pi-AirPlay may not work correctly"
fi

# Step 3: Install files to user's home directory
echo -e "\n${BOLD}Step 3:${NC} Installing Pi-AirPlay to $USER_HOME/pi-airplay..."
INSTALL_DIR="$USER_HOME/pi-airplay"

# Create directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Copy all necessary files
cp -r app_airplay.py utils templates static "$INSTALL_DIR/"
cp run_shairport.sh troubleshoot.sh README.md "$INSTALL_DIR/"

# Set permissions
chown -R $USERNAME:$USERNAME "$INSTALL_DIR"
chmod +x "$INSTALL_DIR"/*.sh

show_progress "Files installed to $INSTALL_DIR"

# Step 4: Configure system shairport-sync
echo -e "\n${BOLD}Step 4:${NC} Configuring system shairport-sync..."

# Check for audio devices
echo -e "${YELLOW}→${NC} Checking audio devices..."
aplay -l
echo ""

# Ask user for sound card number
echo -e "${YELLOW}→${NC} From the list above, find your IQaudio DAC or USB audio device"
read -p "Enter the card number for your audio device (e.g., 0, 1, 2...) or press Enter for automatic detection: " CARD_INPUT

if [ -z "$CARD_INPUT" ]; then
  # Use 'default' as the device name for automatic detection
  DEVICE_CONFIG="output_device = \"default\";"
else
  # Use the specified card number
  DEVICE_CONFIG="output_device = \"plughw:${CARD_INPUT},0\";"
fi

# Create shairport-sync configuration
cat > /etc/shairport-sync.conf << EOL
general = {
  name = "DAD";
  interpolation = "basic";
  output_backend = "alsa";
  mdns_backend = "avahi";
  drift_tolerance_in_seconds = 0.002;
  ignore_volume_control = "no";
  volume_range_db = 60;
  playback_mode = "stereo";
};

alsa = {
  $(echo -e $DEVICE_CONFIG)
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
EOL

show_progress "Shairport-sync configured"

# Step 5: Create systemd services
echo -e "\n${BOLD}Step 5:${NC} Creating systemd services..."

# Create service file for the web interface
cat > /etc/systemd/system/pi-airplay.service << EOL
[Unit]
Description=Pi-AirPlay Web Interface
After=network.target shairport-sync.service
Wants=shairport-sync.service

[Service]
ExecStart=/usr/bin/python3 app_airplay.py --port 8000 --host 0.0.0.0
Restart=always
RestartSec=5
User=$USERNAME
Group=$USERNAME
WorkingDirectory=$INSTALL_DIR

[Install]
WantedBy=multi-user.target
EOL

# Create service file for shairport-sync
cat > /etc/systemd/system/shairport-sync.service << EOL
[Unit]
Description=Shairport Sync - AirPlay Audio Receiver
After=sound.target network.target
Wants=avahi-daemon.service

[Service]
ExecStartPre=/bin/bash -c "if [ -e /tmp/shairport-sync-metadata ]; then rm /tmp/shairport-sync-metadata; fi && mkfifo /tmp/shairport-sync-metadata && chmod 666 /tmp/shairport-sync-metadata"
ExecStart=/usr/bin/shairport-sync
Restart=always
RestartSec=5
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOL

show_progress "Service files created"

# Step 6: Enable and start services
echo -e "\n${BOLD}Step 6:${NC} Enabling services..."
systemctl daemon-reload
systemctl enable shairport-sync.service
systemctl enable pi-airplay.service
systemctl restart shairport-sync.service
sleep 2
systemctl restart pi-airplay.service

if [ $? -eq 0 ]; then
  show_progress "Services enabled and started"
else
  show_error "Failed to start services" "Try running 'sudo systemctl status pi-airplay.service' to check status"
fi

# Step 7: Create desktop shortcut
echo -e "\n${BOLD}Step 7:${NC} Creating desktop shortcut..."
HOSTNAME=$(hostname -I | awk '{print $1}')
mkdir -p "$USER_HOME/Desktop"

cat > "$USER_HOME/Desktop/Pi-AirPlay.desktop" << EOL
[Desktop Entry]
Name=Pi-AirPlay
Comment=Open Pi-AirPlay Web Interface
Exec=chromium-browser --app=http://localhost:8000 --kiosk
Type=Application
Icon=$INSTALL_DIR/static/artwork/default_album.svg
Categories=AudioVideo;
EOL

chmod +x "$USER_HOME/Desktop/Pi-AirPlay.desktop"
chown $USERNAME:$USERNAME "$USER_HOME/Desktop/Pi-AirPlay.desktop"

show_progress "Desktop shortcut created"

# Installation complete
echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Installation Complete!${NC}"
echo -e "${BOLD}=========================================${NC}\n"

echo -e "${GREEN}Pi-AirPlay has been installed successfully!${NC}"
echo -e "\nYou can access the web interface at: ${BOLD}http://$HOSTNAME:8000${NC}"
echo -e "Connect to ${BOLD}DAD${NC} via AirPlay from your Apple device"
echo -e "\nTo start in kiosk mode on your Raspberry Pi, click the desktop icon" 
echo -e "or run: ${BOLD}chromium-browser --app=http://localhost:8000 --kiosk${NC}"
echo -e "\nBoth services will automatically start on boot\n"

exit 0