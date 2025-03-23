#!/bin/bash
# Script to create and configure the systemd service

# Determine if we're using system Python or virtual environment
if [ -d ".venv" ]; then
    echo "Virtual environment detected. Setting up service with virtual environment..."
    USE_VENV=true
else
    echo "No virtual environment detected. Setting up service with system Python..."
    USE_VENV=false
fi

# Create the service file
SERVICE_FILE="music-display.service"
echo "[Unit]
Description=Music Display with AirPlay and Recognition
After=network.target

[Service]
User=$USER
WorkingDirectory=$PWD" > $SERVICE_FILE

# Add appropriate ExecStart line based on environment
if [ "$USE_VENV" = true ]; then
    echo "# Using a bash script wrapper that handles virtual environment activation
ExecStart=/bin/bash $PWD/start_music_display.sh" >> $SERVICE_FILE
else
    echo "# Using system Python directly
ExecStart=/usr/bin/python3 $PWD/app.py" >> $SERVICE_FILE
fi

# Add remaining service configuration
echo "Restart=always
StandardOutput=journal
StandardError=journal
SyslogIdentifier=music-display
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target" >> $SERVICE_FILE

# Copy to system directory
echo "Copying service file to /etc/systemd/system/"
sudo cp $SERVICE_FILE /etc/systemd/system/

# Reload daemon
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable and start the service
echo "Enabling and starting the service..."
sudo systemctl enable music-display
sudo systemctl start music-display

# Show status
echo "Service status:"
sudo systemctl status music-display

echo "Setup complete! You can check logs with: sudo journalctl -u music-display -f"