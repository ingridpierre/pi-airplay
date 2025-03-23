#!/bin/bash
# Script to diagnose shairport-sync issues

echo "=== Shairport-sync Diagnostic Tool ==="
echo

# Check shairport-sync installation
echo "Checking shairport-sync installation..."
SHAIRPORT_PATH=$(which shairport-sync)
if [ -z "$SHAIRPORT_PATH" ]; then
    echo "ERROR: shairport-sync not found in PATH. Please install it."
    echo "Run: sudo apt-get install shairport-sync"
    exit 1
else
    echo "shairport-sync found at: $SHAIRPORT_PATH"
    echo "Version information:"
    shairport-sync -V
fi

# Check for libraries
echo
echo "Checking required libraries..."
ldd $SHAIRPORT_PATH

# Check for configuration file
echo
echo "Checking configuration file..."
if [ -f "/etc/shairport-sync.conf" ]; then
    echo "Found configuration file at /etc/shairport-sync.conf"
    grep -v "^#" /etc/shairport-sync.conf | grep -v "^$" | head -n 20
    echo "(showing first 20 non-comment lines)"
else
    echo "No config file found at /etc/shairport-sync.conf"
fi

# Test with very basic options
echo
echo "Trying minimal startup (no sound output)..."
shairport-sync -a "Pi-DAD" -o dummy &
SHAIRPORT_PID=$!
sleep 2
if ps -p $SHAIRPORT_PID > /dev/null; then
    echo "SUCCESS: shairport-sync started with minimal options."
    kill $SHAIRPORT_PID
else
    echo "FAILED: shairport-sync crashed with minimal options."
fi

# Test audio device enumeration
echo
echo "Available audio output devices:"
shairport-sync -h | grep "hardware output devices:" -A 20

echo
echo "Checking for IQaudio DAC hardware..."
if aplay -l | grep -q "IQaudIO"; then
    echo "Found IQaudio DAC hardware"
    aplay -l | grep "IQaudIO" -A 3
    # Get DAC card number
    CARD_NUM=$(aplay -l | grep IQaudIO | head -n 1 | awk -F'card ' '{print $2}' | cut -d: -f1)
    echo "IQaudio DAC is card $CARD_NUM"
    
    # Test basic playback
    echo
    echo "Testing basic audio output to IQaudio DAC..."
    speaker-test -D hw:$CARD_NUM -c 2 -t sine -l 1 &> /dev/null
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Basic audio test passed"
    else
        echo "WARNING: Basic audio test failed"
    fi
else
    echo "IQaudio DAC not found in audio device list."
fi

# Check for metadata pipe
echo
echo "Checking metadata pipe..."
if [ -e /tmp/shairport-sync-metadata ]; then
    OWNER=$(ls -l /tmp/shairport-sync-metadata | awk '{print $3}')
    PERMS=$(ls -l /tmp/shairport-sync-metadata | awk '{print $1}')
    echo "Metadata pipe exists"
    echo "Owner: $OWNER, Permissions: $PERMS"
else
    echo "Metadata pipe does not exist, creating it..."
    mkfifo /tmp/shairport-sync-metadata
    chmod 666 /tmp/shairport-sync-metadata
    echo "Created metadata pipe with permissions 666"
fi

echo
echo "Diagnostic complete! Please provide this output for troubleshooting."