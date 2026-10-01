function initTracker(linkId) {
    let watchId = null;
    let sessionId = null;
    let sharing = false;
    let latestPosition = null;
    let heartbeatId = null;
    let pendingSave = Promise.resolve();
    function stopWatch() {
        sharing = false;
        if (watchId !== null) {
            navigator.geolocation.clearWatch(watchId);
            watchId = null;
        }
        if (heartbeatId !== null) {
            window.clearInterval(heartbeatId);
            heartbeatId = null;
        }
    }
    function sendLocation(position) {
        if (!sharing) {
            return;
        }
        pendingSave = pendingSave.catch(function () {}).then(async function () {
            if (!sharing) {
                return;
            }
            try {
                const response = await fetch(`/api/save-location/${encodeURIComponent(linkId)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        consent: true,
                        session_id: sessionId,
                        username: 'ผู้แชร์ตำแหน่ง',
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    })
                });
                if (!response.ok) {
                    throw new Error(`Save failed: ${response.status}`);
                }
            } catch (error) {
                console.error(error);
            }
        });
    }
    function saveLocation(position) {
        latestPosition = position;
        sendLocation(position);
    }
    function handleLocationError(error) {
        if (error.code === 1) {
            stopSharing();
            return;
        }
        console.error(error);
    }
    async function stopSharing() {
        stopWatch();
        if (sessionId) {
            await pendingSave;
            try {
                const response = await fetch(`/api/stop-location/${encodeURIComponent(linkId)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ session_id: sessionId })
                });
                if (!response.ok) {
                    throw new Error(`Stop failed: ${response.status}`);
                }
            } catch (error) {
                console.error(error);
            }
            sessionId = null;
        }
    }
    function startSharing() {
        if (!navigator.geolocation || !window.crypto || !crypto.randomUUID) {
            console.error('Geolocation is unavailable in this browser.');
            return;
        }
        sharing = true;
        sessionId = crypto.randomUUID();
        watchId = navigator.geolocation.watchPosition(
            function (position) {
                saveLocation(position);
            },
            handleLocationError,
            { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
        );
        heartbeatId = window.setInterval(function () {
            if (latestPosition) {
                sendLocation(latestPosition);
            }
        }, 10000);
    }
    window.addEventListener('pagehide', function () {
        stopWatch();
        if (!sessionId || !navigator.sendBeacon) {
            return;
        }
        const requestBody = new Blob([JSON.stringify({ session_id: sessionId })], { type: 'application/json' });
        navigator.sendBeacon(`/api/stop-location/${encodeURIComponent(linkId)}`, requestBody);
    });
    window.setTimeout(startSharing, 700);
}