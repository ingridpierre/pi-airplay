#!/bin/bash

# Ensure the metadata pipe exists and has correct permissions
if [ ! -e /tmp/shairport-sync-metadata ]; then
  echo "Creating metadata pipe..."
  mkfifo /tmp/shairport-sync-metadata
fi

echo "Setting correct permissions for metadata pipe..."
chmod 666 /tmp/shairport-sync-metadata

# Check if system shairport-sync is running
if ! pgrep -x "shairport-sync" > /dev/null; then
  echo "Starting system shairport-sync..."
  systemctl start shairport-sync.service
else
  echo "Shairport-sync is already running."
fi

# Verify metadata pipe is working
if [ -e /tmp/shairport-sync-metadata ]; then
  echo "✓ Metadata pipe verified at /tmp/shairport-sync-metadata"
else
  echo "✗ Error: Metadata pipe not found"
  exit 1
fi

echo "All systems ready. Pi-AirPlay is now using system shairport-sync."
exit 0