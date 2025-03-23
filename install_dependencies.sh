#!/bin/bash
#
# Pi-AirPlay Dependencies Installer
# This script installs all required dependencies for the Pi-AirPlay web interface
#
# Created: March 23, 2025

# Text formatting
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Pi-AirPlay Dependencies Installer${NC}"
echo -e "${BOLD}=========================================${NC}\n"

# Function to display progress
show_progress() {
  echo -e "${GREEN}✓${NC} $1"
}

# Function to display errors
show_error() {
  echo -e "${RED}✗${NC} $1"
  echo -e "${YELLOW}→${NC} $2"
}

# Check if pip is installed
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
  show_error "Python pip not found" "Installing pip..."
  sudo apt-get update
  sudo apt-get install -y python3-pip
fi

# Determine which pip command to use
if command -v pip3 &> /dev/null; then
  PIP="pip3"
else
  PIP="pip"
fi

echo -e "${YELLOW}→${NC} Installing required Python packages..."

# Install the required packages
PACKAGES=(
  "colorthief"
  "flask"
  "flask-socketio"
  "eventlet"
  "pillow"
  "numpy"
  "requests"
)

for package in "${PACKAGES[@]}"; do
  echo -e "  ${YELLOW}→${NC} Installing $package..."
  $PIP install $package
  if [ $? -eq 0 ]; then
    show_progress "$package installed successfully"
  else
    show_error "Failed to install $package" "Please check your internet connection and try again"
  fi
done

# Create a virtual environment (optional)
echo -e "\n${YELLOW}→${NC} Would you like to create a virtual environment for Pi-AirPlay? (y/n)"
read -r create_venv

if [[ "$create_venv" == "y" || "$create_venv" == "Y" ]]; then
  echo -e "${YELLOW}→${NC} Installing virtualenv..."
  $PIP install virtualenv
  
  if [ -d "venv" ]; then
    echo -e "${YELLOW}→${NC} Virtual environment already exists. Updating it..."
    source venv/bin/activate
    
    for package in "${PACKAGES[@]}"; do
      $PIP install $package
    done
    
    deactivate
  else
    echo -e "${YELLOW}→${NC} Creating virtual environment..."
    python3 -m virtualenv venv
    
    if [ $? -eq 0 ]; then
      show_progress "Virtual environment created successfully"
      
      echo -e "${YELLOW}→${NC} Installing packages in virtual environment..."
      source venv/bin/activate
      
      for package in "${PACKAGES[@]}"; do
        $PIP install $package
      done
      
      deactivate
    else
      show_error "Failed to create virtual environment" "Continuing with system-wide installation"
    fi
  fi
fi

echo -e "\n${BOLD}=========================================${NC}"
echo -e "${BOLD}   Installation Complete!${NC}"
echo -e "${BOLD}=========================================${NC}\n"

echo -e "You can now run the Pi-AirPlay server with:"
echo -e "  ${YELLOW}→${NC} ./clean_fix.sh"
echo -e ""
echo -e "If you created a virtual environment, you can activate it with:"
echo -e "  ${YELLOW}→${NC} source venv/bin/activate"
echo -e ""
echo -e "Happy streaming!"