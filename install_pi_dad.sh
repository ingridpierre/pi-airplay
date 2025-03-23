#!/bin/bash
# Pi-DAD: Installation Script
# This script installs all necessary dependencies and sets up the Pi-DAD system
# with minimal manual steps required.

set -e  # Exit on error

echo "====================================================="
echo "           Pi-DAD Installation Script"
echo "     Raspberry Pi Digital Audio Display System"
echo "====================================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root. Try 'sudo $0'"
   exit 1
fi

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "Installing system dependencies..."
apt-get update
apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    alsa-utils \
    ffmpeg \
    libasound2-dev \
    portaudio19-dev \
    shairport-sync

echo "Configuring shairport-sync..."
# Backup existing config if present
if [ -f /etc/shairport-sync.conf ]; then
    mv /etc/shairport-sync.conf /etc/shairport-sync.conf.bak
fi

# Copy our custom configuration
cp config/shairport-sync.conf /etc/shairport-sync.conf

# Ensure the metadata pipe exists and has correct permissions
PIPE_PATH="/tmp/shairport-sync-metadata"
if [ ! -p "$PIPE_PATH" ]; then
    mkfifo "$PIPE_PATH"
fi
chmod 666 "$PIPE_PATH"

echo "Installing Python dependencies..."
# Check for --system flag to determine installation method
SYSTEM_INSTALL=false
for arg in "$@"; do
    if [ "$arg" == "--system" ]; then
        SYSTEM_INSTALL=true
        break
    fi
done

if [ "$SYSTEM_INSTALL" == "true" ]; then
    echo "Installing Python packages system-wide..."
    # Handle externally-managed environment in newer Python versions
    if grep -q "externally-managed-environment" "$(python3 -m site --user-site)/../../../EXTERNALLY-MANAGED" 2>/dev/null; then
        echo "Detected externally-managed environment, using PEP668 workaround..."
        pip3 install --break-system-packages \
            flask \
            flask-socketio \
            pyaudio \
            requests \
            pyacoustid \
            colorthief \
            musicbrainzngs
    else
        pip3 install \
            flask \
            flask-socketio \
            pyaudio \
            requests \
            pyacoustid \
            colorthief \
            musicbrainzngs
    fi
else
    echo "Creating Python virtual environment..."
    pip3 install --user virtualenv
    python3 -m virtualenv venv
    source venv/bin/activate
    pip install \
        flask \
        flask-socketio \
        pyaudio \
        requests \
        pyacoustid \
        colorthief \
        musicbrainzngs
    deactivate
    
    echo "Virtual environment created at $SCRIPT_DIR/venv"
    echo "Use 'source venv/bin/activate' to activate it for manual testing."
fi

# Set up systemd service
echo "Installing systemd service..."
if [ "$SYSTEM_INSTALL" == "true" ]; then
    # Use system-wide service for system install
    cp config/pi-dad.service.system /etc/systemd/system/pi-dad.service
else
    # Use virtual environment service
    cp config/pi-dad.service.venv /etc/systemd/system/pi-dad.service
    # Update the path in the service file
    sed -i "s|INSTALL_PATH|$SCRIPT_DIR|g" /etc/systemd/system/pi-dad.service 
fi

systemctl daemon-reload
systemctl enable pi-dad.service

# Create startup script
echo "#!/bin/bash" > start_pi_dad.sh
if [ "$SYSTEM_INSTALL" == "true" ]; then
    echo "python3 $SCRIPT_DIR/app.py" >> start_pi_dad.sh
else
    echo "source $SCRIPT_DIR/venv/bin/activate" >> start_pi_dad.sh
    echo "python $SCRIPT_DIR/app.py" >> start_pi_dad.sh
    echo "deactivate" >> start_pi_dad.sh
fi
chmod +x start_pi_dad.sh

echo "Setting up AcoustID API key..."
read -p "Enter your AcoustID API key: " acoustid_key
echo "$acoustid_key" > .acoustid_api_key
chmod 600 .acoustid_api_key

echo "====================================================="
echo "Installation complete!"
echo "You can start Pi-DAD manually with: ./start_pi_dad.sh"
echo "Or start the service with: sudo systemctl start pi-dad"
echo "====================================================="