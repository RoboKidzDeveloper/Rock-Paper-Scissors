document.getElementById('start-btn').addEventListener('click', function() {
    fetch('/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data.status);
            document.getElementById('video-feed').src = "{{ url_for('video_feed') }}";
        });
});

document.getElementById('stop-btn').addEventListener('click', function() {
    fetch('/stop', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            console.log(data.status);
            document.getElementById('video-feed').src = "";
        });
});
