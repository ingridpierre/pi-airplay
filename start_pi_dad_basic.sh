#!/bin/bash
# Pi-DAD: Raspberry Pi Digital Audio Display
# Simplified startup script for troubleshooting

# Ensure the script runs from the correct directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Function to check if port 5000 is already in use
check_port() {
    if command -v lsof &> /dev/null; then
        if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null ; then
            echo "WARNING: Port 5000 is already in use!"
            echo "Would you like to kill the process using this port? (y/n)"
            read -r response
            if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
                echo "Stopping process on port 5000..."
                # Get all PIDs using port 5000
                PIDS=$(lsof -t -i:5000)
                if [ -n "$PIDS" ]; then
                    echo "Found processes using port 5000: $PIDS"
                    # First try gentle SIGTERM
                    sudo kill $PIDS
                    sleep 2
                    
                    # Check if any processes are still using the port
                    if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null; then
                        echo "Processes still running, using SIGKILL..."
                        sudo kill -9 $PIDS
                        sleep 2
                        
                        # Final check
                        if lsof -Pi :5000 -sTCP:LISTEN -t >/dev/null; then
                            echo "ERROR: Failed to free port 5000. Please reboot your system and try again."
                            exit 1
                        fi
                    fi
                    echo "Port 5000 is now free."
                fi
            else
                echo "Please stop the process using port 5000 manually before starting Pi-DAD."
                echo "You can find the process with: lsof -i :5000"
                echo "Then stop it with: sudo kill <PID>"
                exit 1
            fi
        fi
    else
        echo "lsof command not found - skipping port check."
    fi
}

# Check if we should use virtual environment
if [ -d "./venv" ]; then
    echo "Using virtual environment..."
    source ./venv/bin/activate
    PYTHON="./venv/bin/python"
else
    echo "Using system Python..."
    PYTHON="python3"
fi

# Check for AcoustID API key
if [ ! -f "/etc/acoustid_api_key" ] && [ ! -f "$SCRIPT_DIR/config/acoustid_api_key" ]; then
    echo "No AcoustID API key found. Music recognition will run in simulation mode."
    echo "To set up an API key, visit http://[your-pi-ip]:5000/setup after starting Pi-DAD."
    echo "or create /etc/acoustid_api_key with your API key."
fi

# Check if port 5000 is already in use
check_port

echo "============================================================"
echo "STARTING PI-DAD IN BASIC MODE (TROUBLESHOOTING)"
echo "* NOT starting shairport-sync due to segmentation fault issues"
echo "* Only starting the web interface and music recognition"
echo "* For full functionality, please fix shairport-sync installation"
echo "============================================================"

# Create metadata pipe for compatibility
if [ ! -e /tmp/shairport-sync-metadata ]; then
    echo "Creating metadata pipe..."
    sudo mkfifo /tmp/shairport-sync-metadata
    sudo chmod 666 /tmp/shairport-sync-metadata
else
    echo "Setting metadata pipe permissions..."
    sudo chmod 666 /tmp/shairport-sync-metadata
fi

echo ""
echo "Starting Pi-DAD in basic mode..."
echo ""

# Create a simulation file to trigger default content
echo "Setting up simulation mode..."
touch .simulation_mode

# Start the Pi-DAD application
exec $PYTHON app.py