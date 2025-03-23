#!/bin/bash
#
# Shairport-sync Diagnostic Tool
#
# This script helps diagnose issues with shairport-sync in the Pi-AirPlay setup
# It checks for common problems and provides solutions

echo "=========================================================="
echo "Shairport-sync Diagnostic Tool"
echo "Checking status and configuration of the AirPlay receiver..."
echo "=========================================================="
echo ""

# Check if shairport-sync is installed
echo "1. Checking if shairport-sync is installed..."
if command -v shairport-sync &> /dev/null; then
    echo "   ✓ shairport-sync is installed"
    SHAIRPORT_VERSION=$(shairport-sync -V | head -n 1)
    echo "   Version: $SHAIRPORT_VERSION"
else
    echo "   ✗ shairport-sync is not installed"
    echo "   Run: sudo apt-get install shairport-sync"
fi
echo ""

# Check if shairport-sync is running
echo "2. Checking if shairport-sync is running..."
if pgrep -x "shairport-sync" > /dev/null; then
    echo "   ✓ shairport-sync process is running"
    ps aux | grep shairport-sync | grep -v grep
else
    echo "   ✗ shairport-sync is not running"
fi
echo ""

# Check shairport-sync config
CONF_FILE="/usr/local/etc/shairport-sync.conf"
echo "3. Checking shairport-sync configuration..."
if [ -f "$CONF_FILE" ]; then
    echo "   ✓ Configuration file exists: $CONF_FILE"
    
    # Check for important settings
    echo "   Important configuration settings:"
    
    # Check name setting
    NAME=$(grep -A 2 "general" "$CONF_FILE" | grep "name" | cut -d '"' -f 2)
    if [ -n "$NAME" ]; then
        echo "   - Device name: $NAME"
    else
        echo "   ✗ Device name not set in config"
    fi
    
    # Check output device
    DEVICE=$(grep -A 5 "alsa" "$CONF_FILE" | grep "output_device" | cut -d '"' -f 2)
    if [ -n "$DEVICE" ]; then
        echo "   - Audio output device: $DEVICE"
    else
        echo "   ✗ Output device not set in config"
    fi
    
    # Check metadata pipe
    PIPE=$(grep -A 5 "metadata" "$CONF_FILE" | grep "pipe_name" | cut -d '"' -f 2)
    if [ -n "$PIPE" ]; then
        echo "   - Metadata pipe: $PIPE"
        
        # Check if pipe exists
        if [ -p "$PIPE" ]; then
            echo "   ✓ Metadata pipe exists"
            PIPE_PERMS=$(stat -c "%a" "$PIPE")
            PIPE_OWNER=$(stat -c "%U:%G" "$PIPE")
            echo "   - Pipe permissions: $PIPE_PERMS, Owner: $PIPE_OWNER"
            
            if [ "$PIPE_PERMS" != "666" ]; then
                echo "   ✗ Pipe permissions should be 666 for proper access"
            fi
        else
            echo "   ✗ Metadata pipe does not exist"
            echo "   Run: mkfifo $PIPE && chmod 666 $PIPE"
        fi
    else
        echo "   ✗ Metadata pipe not configured"
    fi
else
    echo "   ✗ Configuration file not found: $CONF_FILE"
    echo "   Creating a basic config file is recommended"
fi
echo ""

# Check audio devices
echo "4. Checking audio devices..."
echo "   Available audio output devices:"
aplay -l

echo ""
echo "   Current ALSA configuration:"
cat /proc/asound/cards
echo ""

# Check port usage
echo "5. Checking port usage..."
if command -v netstat &> /dev/null; then
    echo "   Checking if port 5000 is in use (default AirPlay port):"
    PORT_5000=$(netstat -tuln | grep ":5000 ")
    if [ -n "$PORT_5000" ]; then
        echo "   ✗ Port 5000 is already in use:"
        echo "   $PORT_5000"
        echo "   - This may cause conflicts with shairport-sync"
        echo "   - Consider using alt_port_fix.sh to resolve this"
    else
        echo "   ✓ Port 5000 is available for AirPlay"
    fi
    
    echo "   Checking if port 8080 is in use (alternative web interface port):"
    PORT_8080=$(netstat -tuln | grep ":8080 ")
    if [ -n "$PORT_8080" ]; then
        echo "   ✗ Port 8080 is already in use:"
        echo "   $PORT_8080"
    else
        echo "   ✓ Port 8080 is available for web interface"
    fi
else
    echo "   ✗ netstat not available, skipping port check"
fi
echo ""

# Check avahi-daemon
echo "6. Checking if Avahi daemon is running (required for AirPlay discovery)..."
if systemctl is-active --quiet avahi-daemon; then
    echo "   ✓ Avahi daemon is running"
else
    echo "   ✗ Avahi daemon is not running"
    echo "   Run: sudo systemctl start avahi-daemon"
fi
echo ""

# Diagnostic results
echo "=========================================================="
echo "Diagnostic Summary"
echo "=========================================================="

if pgrep -x "shairport-sync" > /dev/null && [ -f "$CONF_FILE" ] && [ -p "$PIPE" ]; then
    echo "✓ Basic shairport-sync setup appears to be working."
    echo "  - Check the audio settings if you're not hearing sound"
    echo "  - Ensure your Apple device can see the AirPlay receiver"
    echo ""
    echo "If still having issues:"
    echo "1. Try running './alt_port_fix.sh' to resolve port conflicts"
    echo "2. Use 'shairport-sync -v' to see verbose output"
    echo "3. Check Pi-AirPlay logs with 'cat pi_airplay.log'"
else
    echo "✗ There are issues with the shairport-sync configuration."
    echo "  Recommended actions:"
    echo "  1. Ensure shairport-sync is installed"
    echo "  2. Create a proper configuration file"
    echo "  3. Create metadata pipe with correct permissions"
    echo "  4. Run './pi_airplay.sh' to set up everything automatically"
fi
echo "=========================================================="