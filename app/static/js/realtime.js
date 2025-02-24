function setupRealtimeUpdates(path, updateCallback) {
    function fetchUpdates() {
        fetch(`/api/updates/${path}`)
            .then(response => response.json())
            .then(data => {
                updateCallback(data);
            })
            .catch(error => console.error('Error:', error));
    }

    // Initial fetch
    fetchUpdates();

    // Set up polling for updates every 5 seconds
    setInterval(fetchUpdates, 5000);
}
