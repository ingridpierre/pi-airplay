document.addEventListener('DOMContentLoaded', () => {
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');
    const trackAlbum = document.getElementById('track-album');
    const connectionStatus = document.getElementById('connection-status');
    const debugLog = document.getElementById('debug-log');
    const defaultUpdateInterval = 1000; // 1 second default
    const maxUpdateInterval = 5000;     // 5 seconds maximum

    let lastUpdate = {};
    let consecutiveErrors = 0;
    let updateInterval = defaultUpdateInterval;
    let isPlaying = false;

    function updateMetadataDisplay(data) {
        if (!data) return;

        // Only update if there are actual changes
        if (JSON.stringify(data) === JSON.stringify(lastUpdate)) {
            return;
        }

        console.log('New metadata received:', data);
        const timestamp = new Date().toLocaleTimeString();

        // Update track information
        if (data.title !== trackTitle.textContent) {
            trackTitle.textContent = data.title || 'Not Playing';
        }
        if (data.artist !== trackArtist.textContent) {
            trackArtist.textContent = data.artist || 'No Artist';
        }
        if (data.album !== trackAlbum.textContent) {
            trackAlbum.textContent = data.album || 'No Album';
        }

        // Update connection status
        const newStatus = data.title !== 'Not Playing';
        if (newStatus !== isPlaying) {
            isPlaying = newStatus;
            connectionStatus.textContent = isPlaying ? 'Connected - Playing' : 'Waiting for AirPlay...';
            connectionStatus.style.color = isPlaying ? '#4CAF50' : '#FFA500';
        }

        // Update debug information if available
        if (data._debug) {
            debugLog.textContent = `${timestamp}
Metadata Pipe: ${data._debug.pipe_exists ? 'Exists' : 'Missing'}
Permissions: ${data._debug.permissions}
Last Error: ${data._debug.last_error || 'None'}

Data: ${JSON.stringify(data, null, 2)}`;
        }

        lastUpdate = data;

        // Reset error counter and update interval on successful update
        if (consecutiveErrors > 0) {
            consecutiveErrors = 0;
            updateInterval = defaultUpdateInterval;
        }
    }

    async function updateDisplay() {
        try {
            const response = await fetch('/now-playing');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            updateMetadataDisplay(data);
        } catch (error) {
            console.error('Error fetching metadata:', error);
            consecutiveErrors++;

            if (consecutiveErrors >= 3) {
                connectionStatus.textContent = 'Connection Error';
                connectionStatus.style.color = '#FF0000';
                // Gradually increase update interval on errors
                updateInterval = Math.min(updateInterval * 1.5, maxUpdateInterval);
            }
        }

        // Schedule next update
        setTimeout(updateDisplay, updateInterval);
    }

    // Initial update
    updateDisplay();
});