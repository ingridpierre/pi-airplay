#!/bin/bash
# Script to install Python dependencies directly on system Python
# This works around the "externally-managed-environment" restriction

# Install system packages
echo "Installing system packages..."
sudo apt update
sudo apt install -y python3-flask python3-flask-socketio python3-eventlet python3-pyaudio \
    python3-numpy python3-pydub python3-requests python3-pillow python3-dev \
    build-essential libffi-dev libasound2-dev portaudio19-dev ffmpeg \
    libchromaprint-dev pkg-config libopenblas-dev

# Create temporary no-externally-managed.pth file to bypass the check
echo "Working around externally-managed-environment restriction..."
SITE_PACKAGES=$(python3 -c "import site; print(site.getsitepackages()[0])")
sudo touch "$SITE_PACKAGES/no-externally-managed.pth" 

# Install Python packages that aren't available via apt
echo "Installing Python packages..."
sudo pip3 install pyacoustid musicbrainzngs colorthief librosa sounddevice

# Remove the temporary file
echo "Cleaning up..."
sudo rm "$SITE_PACKAGES/no-externally-managed.pth"

echo "Installation complete!"
echo "Note: If you update your system Python packages in the future, you may need to rerun this script."