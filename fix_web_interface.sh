
#!/bin/bash
# Pi-AirPlay Web Interface Troubleshooter

echo "===== Pi-AirPlay Web Interface Troubleshooter ====="
echo "Checking configuration..."

# Check if static files exist
if [ ! -d "static" ]; then
  echo "ERROR: 'static' directory missing!"
else
  echo "✓ Static directory exists"
fi

# Check templates
if [ ! -d "templates" ]; then
  echo "ERROR: 'templates' directory missing!"
else
  echo "✓ Templates directory exists"
  
  # Check for critical templates
  for template in display.html debug.html; do
    if [ ! -f "templates/$template" ]; then
      echo "ERROR: Missing template: $template"
    else
      echo "✓ Template exists: $template"
    fi
  done
fi

# Check routes in main application
grep -n "route.*debug" app_airplay.py
echo "✓ Checked routes configuration"

# Check that the Flask app is running
echo "Checking if web app is running on port 8000..."
if netstat -tuln | grep ":8000" > /dev/null; then
  echo "✓ Web app is running on port 8000"
else
  echo "ERROR: Web app not detected on port 8000"
fi

# Try accessing the main URL and debug URL with timeout using both localhost and IP address
echo "Testing URLs..."
# Get the IP address of the Pi
PI_IP=$(hostname -I | awk '{print $1}')

# Test both localhost and the actual IP
for base_url in "http://localhost:8000" "http://${PI_IP}:8000"; do
  for path in "/" "/debug"; do
    url="${base_url}${path}"
    echo "Testing $url..."
    code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 3 $url)
    if [ "$code" = "200" ]; then
      echo "✓ URL $url is accessible"
    else
      echo "WARNING: URL $url returned status $code or timed out"
    fi
  done
done

# Provide clearer guidance
echo "NOTE: If localhost URLs fail but IP URLs work, this is normal for external access."
echo "Always use http://${PI_IP}:8000 when accessing from another device."

echo "===== Troubleshooting Complete ====="
# Get the IP address of the Pi again to make sure we have it
PI_IP=$(hostname -I | awk '{print $1}')
echo "To access the web interface, use: http://${PI_IP}:8000"
echo "To access the debug interface, use: http://${PI_IP}:8000/debug"
echo "NOTE: Always use the actual IP address when accessing from another device, not 'localhost'"
echo "If issues persist, check the console output for errors."
