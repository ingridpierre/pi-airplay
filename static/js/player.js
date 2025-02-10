document.addEventListener('DOMContentLoaded', () => {
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');
    const trackAlbum = document.getElementById('track-album');

    function updateDisplay() {
        fetch('/now-playing')
            .then(response => response.json())
            .then(data => {
                trackTitle.textContent = data.title;
                trackArtist.textContent = data.artist;
                trackAlbum.textContent = data.album;
            });
    }

    // Update every 5 seconds
    setInterval(updateDisplay, 5000);
    updateDisplay();
});