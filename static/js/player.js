document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');
    const trackAlbum = document.getElementById('track-album');
    const connectionStatus = document.getElementById('connection-status');
    const albumArt = document.querySelector('.album-art');

    socket.on('connect', () => {
        connectionStatus.textContent = 'Connected - Waiting for AirPlay';
    });

    socket.on('disconnect', () => {
        connectionStatus.textContent = 'Disconnected';
        resetPlayerDisplay();
    });

    socket.on('metadata_update', (data) => {
        updatePlayerDisplay(data);
    });

    socket.on('playback_state', (data) => {
        if (data.playing) {
            connectionStatus.textContent = 'Playing';
        } else {
            connectionStatus.textContent = 'Connected - Waiting for AirPlay';
        }
    });

    function updatePlayerDisplay(data) {
        trackTitle.textContent = data.title || 'Unknown Title';
        trackArtist.textContent = data.artist || 'Unknown Artist';
        trackAlbum.textContent = data.album || 'Unknown Album';
        
        if (data.artwork) {
            albumArt.innerHTML = `<img src="data:image/jpeg;base64,${data.artwork}" alt="Album Art">`;
        } else {
            albumArt.innerHTML = '<i class="fa fa-music default-album-art"></i>';
        }
    }

    function resetPlayerDisplay() {
        trackTitle.textContent = 'Not Playing';
        trackArtist.textContent = 'No Artist';
        trackAlbum.textContent = 'No Album';
        albumArt.innerHTML = '<i class="fa fa-music default-album-art"></i>';
    }
});
