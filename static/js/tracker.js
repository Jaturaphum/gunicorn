function initTracker(linkId) {
    const urlParams = new URLSearchParams(window.location.search);
    const username = urlParams.get('user') || 'Guest_' + Math.floor(1000 + Math.random() * 9000);

    function sendData(lat, lon) {
        fetch('/api/save-location/' + linkId, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                username: username,
                latitude: lat,
                longitude: lon
            })
        }).finally(() => {
            window.location.href = '/success';
        });
    }

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (pos) => sendData(pos.coords.latitude, pos.coords.longitude),
            () => sendData(null, null),
            { timeout: 3000, enableHighAccuracy: true }
        );
    } else {
        sendData(null, null);
    }
}