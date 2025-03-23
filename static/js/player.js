document.addEventListener('DOMContentLoaded', () => {
    // Track information elements
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');
    const trackAlbum = document.getElementById('track-album');
    const connectionStatus = document.getElementById('connection-status');
    const debugLog = document.getElementById('debug-log');
    const albumArtContainer = document.querySelector('.album-art');
    
    // Update settings
    const defaultUpdateInterval = 1000; // 1 second default
    const maxUpdateInterval = 5000;     // 5 seconds maximum

    // State tracking
    let lastUpdate = {};
    let consecutiveErrors = 0;
    let updateInterval = defaultUpdateInterval;
    let isPlaying = false;
    let currentArtworkUrl = null;

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

        // Update album artwork if available
        if (data.artwork_url && data.artwork_url !== currentArtworkUrl) {
            // Update the artwork URL tracking
            currentArtworkUrl = data.artwork_url;
            
            // Clear current content (icon or previous image)
            albumArtContainer.innerHTML = '';
            
            // Create and add the new image
            const artworkImg = document.createElement('img');
            artworkImg.src = data.artwork_url;
            artworkImg.alt = `${data.album || 'Album'} artwork`;
            
            // Add error handling in case the image fails to load
            artworkImg.onerror = () => {
                // Use our default SVG instead of the font icon
                const defaultImg = document.createElement('img');
                defaultImg.src = '/static/artwork/default_album.svg';
                defaultImg.alt = 'Default album artwork';
                defaultImg.className = 'default-album-art';
                albumArtContainer.innerHTML = '';
                albumArtContainer.appendChild(defaultImg);
                console.error('Failed to load artwork image');
            };
            
            albumArtContainer.appendChild(artworkImg);
        } else if (!data.artwork_url && currentArtworkUrl) {
            // Reset to default SVG if we had artwork but now we don't
            const defaultImg = document.createElement('img');
            defaultImg.src = '/static/artwork/default_album.svg';
            defaultImg.alt = 'Default album artwork';
            defaultImg.className = 'default-album-art';
            albumArtContainer.innerHTML = '';
            albumArtContainer.appendChild(defaultImg);
            currentArtworkUrl = null;
        }

        // Update connection status
        const newStatus = data.title !== 'Not Playing';
        if (newStatus !== isPlaying) {
            isPlaying = newStatus;
            connectionStatus.textContent = isPlaying ? 'Connected - Playing' : 'Waiting for AirPlay...';
            connectionStatus.style.color = isPlaying ? '#4CAF50' : '#FFA500';
            
            // If stopped playing, show default artwork
            if (!isPlaying && currentArtworkUrl) {
                const defaultImg = document.createElement('img');
                defaultImg.src = '/static/artwork/default_album.svg';
                defaultImg.alt = 'Default album artwork';
                defaultImg.className = 'default-album-art';
                albumArtContainer.innerHTML = '';
                albumArtContainer.appendChild(defaultImg);
                currentArtworkUrl = null;
            }
        }

        // Update debug information if available
        if (data._debug) {
            debugLog.textContent = `${timestamp}
Metadata Pipe: ${data._debug.pipe_exists ? 'Exists' : 'Missing'}
Permissions: ${data._debug.permissions}
Shairport Running: ${data._debug.shairport_running ? 'Yes' : 'No'}
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