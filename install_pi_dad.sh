#!/bin/bash
# Pi-DAD: Raspberry Pi Digital Audio Display
# Installation script

set -e  # Exit on any error

# Text formatting
BOLD="\033[1m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
RED="\033[0;31m"
RESET="\033[0m"

# Banner
echo -e "${BOLD}${GREEN}"
echo "====================================================="
echo "   Pi-DAD: Raspberry Pi Digital Audio Display"
echo "   Installation Script"
echo "====================================================="
echo -e "${RESET}"

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (sudo)${RESET}" 
   exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Ask for installation type
echo -e "${BOLD}Select installation type:${RESET}"
echo "1) System-wide installation (recommended)"
echo "2) Virtual environment installation"
read -p "Enter choice [1-2]: " install_type

if [[ "$install_type" != "1" && "$install_type" != "2" ]]; then
    echo -e "${RED}Invalid choice. Exiting.${RESET}"
    exit 1
fi

# Install required system packages
echo -e "\n${BOLD}${GREEN}Installing system dependencies...${RESET}"
apt-get update
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    ffmpeg \
    libasound2-dev \
    portaudio19-dev \
    shairport-sync

# Configure shairport-sync
echo -e "\n${BOLD}${GREEN}Configuring shairport-sync...${RESET}"
cp -f "$SCRIPT_DIR/config/shairport-sync.conf" /etc/shairport-sync.conf

# Create metadata pipe if it doesn't exist
if [ ! -e /tmp/shairport-sync-metadata ]; then
    echo "Creating metadata pipe..."
    mkfifo /tmp/shairport-sync-metadata
    chmod 666 /tmp/shairport-sync-metadata
fi

# Restart shairport-sync to apply configuration
systemctl restart shairport-sync

# Create application directory and copy files
echo -e "\n${BOLD}${GREEN}Creating application directory and copying files...${RESET}"

# Detect the current user instead of hardcoding "pi"
CURRENT_USER=$(whoami)
if [ "$CURRENT_USER" = "root" ]; then
    # If running as root, try to get the real user who called sudo
    if [ -n "$SUDO_USER" ]; then
        CURRENT_USER=$SUDO_USER
    else
        # Ask for the username if we can't detect automatically
        read -p "Enter your username (not root): " CURRENT_USER
        if [ -z "$CURRENT_USER" ] || [ "$CURRENT_USER" = "root" ]; then
            echo -e "${RED}Invalid username. Using 'pi' as fallback.${RESET}"
            CURRENT_USER="pi"
        fi
    fi
fi

echo "Using username: $CURRENT_USER"

mkdir -p /opt/pi-dad
cp -r "$SCRIPT_DIR/app.py" "$SCRIPT_DIR/utils" "$SCRIPT_DIR/static" "$SCRIPT_DIR/templates" /opt/pi-dad/
chown -R $CURRENT_USER:$CURRENT_USER /opt/pi-dad

# Install Python dependencies
echo -e "\n${BOLD}${GREEN}Installing Python dependencies...${RESET}"

if [[ "$install_type" == "1" ]]; then
    # System-wide installation (using virtual env to avoid externally-managed-environment error)
    echo "Creating system virtual environment in /opt/pi-dad-venv..."
    python3 -m venv /opt/pi-dad-venv
    /opt/pi-dad-venv/bin/pip install --upgrade pip
    /opt/pi-dad-venv/bin/pip install flask "flask-socketio>=5.0.0" pyaudio requests pyacoustid colorthief musicbrainzngs pillow eventlet
    
    # Modify the service file for the new venv location and current user
    sed -e 's|/usr/bin/python3|/opt/pi-dad-venv/bin/python|g' \
        -e "s|User=pi|User=$CURRENT_USER|g" \
        -e "s|Group=pi|Group=$CURRENT_USER|g" \
        "$SCRIPT_DIR/config/pi-dad.service.system" > /etc/systemd/system/pi-dad.service
    
elif [[ "$install_type" == "2" ]]; then
    # Virtual environment installation
    echo "Creating virtual environment in /opt/pi-dad/venv..."
    python3 -m venv /opt/pi-dad/venv
    
    # Install dependencies in the virtual environment
    /opt/pi-dad/venv/bin/pip install --upgrade pip
    /opt/pi-dad/venv/bin/pip install flask "flask-socketio>=5.0.0" pyaudio requests pyacoustid colorthief musicbrainzngs pillow eventlet
    
    # Copy the venv service file and update it with correct paths and current user
    sed -e 's|/opt/pi-dad/venv|/opt/pi-dad/venv|g' \
        -e "s|User=pi|User=$CURRENT_USER|g" \
        -e "s|Group=pi|Group=$CURRENT_USER|g" \
        "$SCRIPT_DIR/config/pi-dad.service.venv" > /etc/systemd/system/pi-dad.service
fi

# Reload systemd
systemctl daemon-reload
systemctl enable pi-dad.service

# Set up AcoustID API key
echo -e "\n${BOLD}${YELLOW}Setting up AcoustID API key${RESET}"
echo "An AcoustID API key is required for the music recognition feature."
echo "If you don't have one, get a free key at: https://acoustid.org/new-application"
echo ""

read -p "Enter your AcoustID API key (leave blank to skip): " api_key

if [[ -n "$api_key" ]]; then
    echo "$api_key" > /etc/acoustid_api_key
    chmod 644 /etc/acoustid_api_key
    echo -e "${GREEN}API key saved to /etc/acoustid_api_key${RESET}"
else
    echo -e "${YELLOW}No API key provided. Music recognition will be limited to simulation mode.${RESET}"
    echo "You can add an API key later by editing /etc/acoustid_api_key or through the web interface."
fi

# Start the service
echo -e "\n${BOLD}${GREEN}Starting Pi-DAD service...${RESET}"
systemctl start pi-dad.service

# Final instructions
echo -e "\n${BOLD}${GREEN}Installation complete!${RESET}"
echo -e "Pi-DAD is now installed and running."
echo ""
echo -e "${BOLD}Access the web interface at:${RESET}"
echo -e "http://$(hostname).local:5000"
echo -e "or"
echo -e "http://$(hostname -I | awk '{print $1}'):5000"
echo ""
echo -e "${BOLD}To check the service status:${RESET}"
echo "sudo systemctl status pi-dad"
echo ""
echo -e "${BOLD}To view logs:${RESET}"
echo "sudo journalctl -u pi-dad -f"
echo ""

exit 0