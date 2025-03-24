#!/bin/bash

# Ensure the metadata pipe exists and has correct permissions
if [ -e /tmp/shairport-sync-metadata ]; then
  rm /tmp/shairport-sync-metadata
fi

echo "Creating metadata pipe..."
mkfifo /tmp/shairport-sync-metadata
chmod 666 /tmp/shairport-sync-metadata

# Start shairport-sync with ALSA backend and no mDNS
echo "Starting shairport-sync..."
shairport-sync -c config/shairport-sync.conf -o alsa -m avahi -- -d default

# Keep script running
while true; do
  echo "Checking shairport-sync status..."
  if ! pgrep -f shairport-sync > /dev/null; then
    echo "Restarting shairport-sync..."
    shairport-sync -c config/shairport-sync.conf -o alsa -m dummy -- -d default
  fi
  sleep 5
done