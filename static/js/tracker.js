function sendData(linkId, latitude, longitude) {
  fetch('/api/save-location/' + linkId, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      latitude: latitude,
      longitude: longitude
    })
  })
  .then(() => { window.location.href = '/success'; })
  .catch(() => { window.location.href = '/success'; });
}

function initTracker(linkId) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        sendData(linkId, position.coords.latitude, position.coords.longitude);
      },
      (error) => {
        sendData(linkId, null, null);
      },
      { timeout: 5000, enableHighAccuracy: true }
    );
  } else {
    sendData(linkId, null, null);
  }
}