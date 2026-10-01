function initTracker(linkId) {
    const storageKey = `tracker-consent-${linkId}`;
    let savedUsername = 'ไม่ระบุตัวตน';

    try {
        const storedUsername = localStorage.getItem(storageKey);
        if (storedUsername && storedUsername.trim().length <= 100) {
            savedUsername = storedUsername.trim();
        }
    } catch (error) {
        console.error(error);
    }

    if (!navigator.geolocation) {
        document.body.textContent = 'เบราว์เซอร์นี้ไม่รองรับการระบุตำแหน่ง';
        return;
    }

    navigator.geolocation.getCurrentPosition(
        async function (position) {
            try {
                const response = await fetch(`/api/save-location/${encodeURIComponent(linkId)}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        consent: true,
                        username: savedUsername,
                        latitude: position.coords.latitude,
                        longitude: position.coords.longitude,
                        accuracy: position.coords.accuracy
                    })
                });

                if (!response.ok) {
                    throw new Error(`Save failed: ${response.status}`);
                }
                window.location.href = '/success';
            } catch (error) {
                document.body.textContent = 'บันทึกข้อมูลไม่สำเร็จ';
                console.error(error);
            }
        },
        function (error) {
            const messages = {
                1: 'คุณไม่อนุญาตตำแหน่ง จึงไม่มีการบันทึกข้อมูล',
                2: 'ไม่สามารถระบุตำแหน่งได้ จึงไม่มีการบันทึกข้อมูล',
                3: 'ระบุตำแหน่งนานเกินไป จึงไม่มีการบันทึกข้อมูล'
            };
            document.body.textContent = messages[error.code] || 'ไม่สามารถระบุตำแหน่งได้';
        },
        { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 }
    );
}