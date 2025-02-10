document.addEventListener('DOMContentLoaded', () => {
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');
    const trackAlbum = document.getElementById('track-album');
    const connectionStatus = document.getElementById('connection-status');
    const debugLog = document.getElementById('debug-log'); // Added to get debug log element

    let lastUpdate = {};

    function updateDisplay() {
        fetch('/now-playing')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                // Only update if data has changed
                if (JSON.stringify(data) !== JSON.stringify(lastUpdate)) {
                    console.log('New metadata received:', data);
                    const timestamp = new Date().toLocaleTimeString();
                    debugLog.textContent = `${timestamp}\nMetadata Pipe: ${data._debug?.pipe_exists ? 'Exists' : 'Missing'}\nPermissions: ${data._debug?.permissions}\nLast Error: ${data._debug?.last_error || 'None'}\n\nData: ${JSON.stringify(data, null, 2)}`;

                    trackTitle.textContent = data.title || 'Not Playing';
                    trackArtist.textContent = data.artist || 'No Artist';
                    trackAlbum.textContent = data.album || 'No Album';

                    if (data.title !== 'Not Playing') {
                        connectionStatus.textContent = 'Connected - Playing';
                    } else {
                        connectionStatus.textContent = 'Waiting for AirPlay...';
                    }

                    lastUpdate = data;
                }
            })
            .catch(error => {
                console.error('Error fetching metadata:', error);
                connectionStatus.textContent = 'Connection Error';
            });
    }

    // Update every 2 seconds instead of 1 to reduce server load
    setInterval(updateDisplay, 2000);
    updateDisplay();
});