function sendLocationPayload() {
    fetch('/api/save-location/{{ link_id }}', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: 'Unknown'
        })
    }).then(() => {
        window.location.href = '/success';
    });
}

window.onload = sendLocationPayload;