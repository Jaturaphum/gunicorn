function requestHighAccuracyLocation(username, linkId) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      function (position) {
        sendLocationData(linkId, username, position.coords.latitude, position.coords.longitude);
      },
      function (error) {
        sendLocationData(linkId, username, null, null);
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  } else {
    sendLocationData(linkId, username, null, null);
  }
}

function sendLocationData(linkId, username, latitude, longitude) {
  fetch('/api/save-location/' + linkId, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      username: username,
      latitude: latitude,
      longitude: longitude
    })
  }).then(function () {
    window.location.href = '/success';
  }).catch(function () {
    window.location.href = '/success';
  });
}