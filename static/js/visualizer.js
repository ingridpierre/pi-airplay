document.addEventListener('DOMContentLoaded', () => {
    // Canvas setup
    const canvas = document.getElementById('spectrum-canvas');
    const ctx = canvas.getContext('2d');
    const volumeBar = document.getElementById('volume-bar');
    const startButton = document.getElementById('start-visualizer');
    const stopButton = document.getElementById('stop-visualizer');
    const visualizerStatus = document.getElementById('visualizer-status');
    
    // Track elements
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');
    const trackAlbum = document.getElementById('track-album');
    const connectionStatus = document.getElementById('connection-status');
    
    // Socket.io connection
    const socket = io();
    let isVisualizerRunning = false;
    
    // Audio data buffers
    let spectrumData = [];
    let rmsEnergy = 0;
    let maxEnergy = 0.5; // Initial max energy threshold
    
    // Color gradients for visualizations
    const gradients = {
        spectrum: [
            { pos: 0, color: '#1DB954' }, // Spotify green
            { pos: 0.5, color: '#2E77D0' }, // Blue
            { pos: 1, color: '#9B59B6' }  // Purple
        ],
        volume: [
            { pos: 0, color: '#1DB954' }, // Green
            { pos: 0.7, color: '#FFA500' }, // Orange
            { pos: 1, color: '#FF4500' }  // Red-orange
        ]
    };

    // Function to create gradient
    function createGradient(ctx, width, height, stops, vertical = false) {
        const gradient = vertical 
            ? ctx.createLinearGradient(0, 0, 0, height)
            : ctx.createLinearGradient(0, 0, width, 0);
        
        stops.forEach(stop => {
            gradient.addColorStop(stop.pos, stop.color);
        });
        
        return gradient;
    }
    
    // Handle metadata updates for what's playing
    function updateMetadata() {
        fetch('/now-playing')
            .then(response => response.json())
            .then(data => {
                trackTitle.textContent = data.title || 'Not Playing';
                trackArtist.textContent = data.artist || 'No Artist';
                trackAlbum.textContent = data.album || 'No Album';
                
                // Update album artwork if available
                const albumArt = document.getElementById('album-art');
                if (data.artwork_url) {
                    // Clear current content (icon or previous image)
                    albumArt.innerHTML = '';
                    
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
                        albumArt.innerHTML = '';
                        albumArt.appendChild(defaultImg);
                        console.error('Failed to load artwork image');
                    };
                    
                    albumArt.appendChild(artworkImg);
                } else if (albumArt.querySelector('img')) {
                    // Reset to default SVG if we had artwork but now we don't
                    const defaultImg = document.createElement('img');
                    defaultImg.src = '/static/artwork/default_album.svg';
                    defaultImg.alt = 'Default album artwork';
                    defaultImg.className = 'default-album-art';
                    albumArt.innerHTML = '';
                    albumArt.appendChild(defaultImg);
                }
                
                // Update connection status
                const isPlaying = data.title !== 'Not Playing';
                connectionStatus.textContent = isPlaying 
                    ? 'Connected - Playing' 
                    : 'Waiting for AirPlay...';
                connectionStatus.style.color = isPlaying ? '#4CAF50' : '#FFA500';
                
                // If not playing, also update visualizer status
                if (!isPlaying) {
                    visualizerStatus.textContent = 'Visualizer: Idle';
                    visualizerStatus.style.color = '#FF9800';
                }
            })
            .catch(error => {
                console.error('Error fetching metadata:', error);
                connectionStatus.textContent = 'Connection Error';
                connectionStatus.style.color = '#FF0000';
            });
    }
    
    // Draw the spectrum visualization
    function drawSpectrum() {
        if (!spectrumData || spectrumData.length === 0) return;
        
        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        // Set up dimensions
        const width = canvas.width;
        const height = canvas.height;
        const barWidth = width / Math.min(64, spectrumData.length);
        const gradient = createGradient(ctx, width, height, gradients.spectrum, true);
        
        // Draw spectrum bars
        ctx.fillStyle = gradient;
        
        for (let i = 0; i < Math.min(64, spectrumData.length); i++) {
            // Normalize and scale the value (apply some non-linear scaling for better visualization)
            let value = spectrumData[i];
            
            // Apply logarithmic scaling to make visualization more dynamic
            value = Math.max(0, (value + 80) / 40); // Normalize from dB scale
            value = Math.min(1, Math.max(0, value)); // Clamp between 0 and 1
            
            // Calculate bar height (higher frequencies are given less height to emphasize bass)
            const exponentialFactor = 1 - (i / spectrumData.length) * 0.5;
            const barHeight = value * height * exponentialFactor;
            
            // Draw bar
            ctx.fillRect(i * barWidth, height - barHeight, barWidth - 1, barHeight);
        }
        
        // Draw decorative line on top of the bars
        ctx.strokeStyle = 'rgba(255, 255, 255, 0.7)';
        ctx.lineWidth = 2;
        ctx.beginPath();
        
        for (let i = 0; i < Math.min(64, spectrumData.length); i++) {
            let value = spectrumData[i];
            value = Math.max(0, (value + 80) / 40);
            value = Math.min(1, Math.max(0, value));
            
            const exponentialFactor = 1 - (i / spectrumData.length) * 0.5;
            const y = height - (value * height * exponentialFactor);
            
            if (i === 0) {
                ctx.moveTo(0, y);
            } else {
                ctx.lineTo(i * barWidth, y);
            }
        }
        
        ctx.stroke();
    }
    
    // Update the volume meter
    function updateVolumeMeter() {
        // Auto-adjust maximum energy for better visualization
        maxEnergy = Math.max(maxEnergy, rmsEnergy * 1.2);
        maxEnergy = maxEnergy * 0.995; // Slowly decrease max threshold if no loud sounds
        
        // Calculate percentage (0-100) of current volume relative to max
        const percentage = Math.min(100, (rmsEnergy / maxEnergy) * 100);
        
        // Update volume bar
        volumeBar.style.width = `${percentage}%`;
        
        // Change color based on volume level
        if (percentage > 80) {
            volumeBar.style.background = gradients.volume[2].color;
        } else if (percentage > 50) {
            volumeBar.style.background = gradients.volume[1].color;
        } else {
            volumeBar.style.background = gradients.volume[0].color;
        }
    }
    
    // Start the visualizer
    function startVisualizer() {
        if (isVisualizerRunning) return;
        
        fetch('/visualizer/start')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    isVisualizerRunning = true;
                    visualizerStatus.textContent = 'Visualizer: Active';
                    visualizerStatus.style.color = '#4CAF50';
                    startButton.disabled = true;
                    stopButton.disabled = false;
                }
            })
            .catch(error => {
                console.error('Error starting visualizer:', error);
                visualizerStatus.textContent = 'Visualizer: Error';
                visualizerStatus.style.color = '#FF0000';
            });
    }
    
    // Stop the visualizer
    function stopVisualizer() {
        if (!isVisualizerRunning) return;
        
        fetch('/visualizer/stop')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    isVisualizerRunning = false;
                    visualizerStatus.textContent = 'Visualizer: Idle';
                    visualizerStatus.style.color = '#FF9800';
                    startButton.disabled = false;
                    stopButton.disabled = true;
                }
            })
            .catch(error => {
                console.error('Error stopping visualizer:', error);
            });
    }
    
    // Socket.io event handlers
    socket.on('connect', () => {
        console.log('Connected to server');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        isVisualizerRunning = false;
        visualizerStatus.textContent = 'Visualizer: Disconnected';
        visualizerStatus.style.color = '#FF0000';
    });
    
    socket.on('visualization_data', (data) => {
        spectrumData = data.spectrum || [];
        rmsEnergy = data.rms_energy || 0;
        
        drawSpectrum();
        updateVolumeMeter();
    });
    
    // Button event handlers
    startButton.addEventListener('click', startVisualizer);
    stopButton.addEventListener('click', stopVisualizer);
    
    // Initial setup
    stopButton.disabled = true;
    updateMetadata();
    
    // Update metadata periodically
    setInterval(updateMetadata, 2000);
    
    // Initial canvas size adjustment
    function resizeCanvas() {
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;
    }
    
    // Handle window resize
    window.addEventListener('resize', resizeCanvas);
    resizeCanvas();
});