import uuid
from flask import Flask, jsonify, redirect, request, url_for

app = Flask(__name__)

# เก็บข้อมูลไว้ในหน่วยความจำ (Memory Storage)
links_db = {}


@app.route("/")
def home():
    links_list = list(links_db.keys())

    links_html = "".join(
        [
            f'<li><a href="/track/{link_id}">ลิงก์ {link_id}</a> - '
            f'(<a href="/stats/{link_id}">ดูสถิติ</a>)</li>'
            for link_id in links_list
        ]
    )

    return f"""
    <h2>ระบบสร้าง ลิงก์ติดตาม Session</h2>
    <form action="/create-link" method="post">
        <button type="submit">สร้าง Unique Link ใหม่</button>
    </form>
    <h3>รายการลิงก์ทั้งหมดที่ถูกสร้าง:</h3>
    <ul>
        {links_html if links_html else "<li>ยังไม่มีลิงก์ในระบบ</li>"}
    </ul>
    """


@app.route("/create-link", methods=["POST"])
def create_link():
    """สร้าง Unique Link ID ใหม่ด้วย UUID"""
    unique_id = str(uuid.uuid4())[:8]
    # เพิ่มเติม: เปลี่ยนการบันทึกข้อมูลจาก Firebase มาเก็บใน links_db (dict)
    links_db[unique_id] = []
    return redirect(url_for("home"))


@app.route("/track/<link_id>")
def track_session(link_id):
    """เมื่อมีคนกดเข้าลิงก์นี้ ระบบจะรัน JavaScript ดึงพิกัด Lat/Long แล้วบันทึก"""
    if link_id not in links_db:
        return "ไม่พบลิงก์นี้ในระบบ", 404

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>กำลังบันทึกข้อมูล...</title>
    </head>
    <body>
        <h3>กำลังบันทึกข้อมูลและนำคุณไปยังหน้าถัดไป...</h3>
        <script>
            function sendData(latitude, longitude) {{
                fetch('/save-location/{link_id}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        latitude: latitude,
                        longitude: longitude
                    }})
                }}).then(() => {{
                    window.location.href = '/success/{link_id}';
                }}).catch(() => {{
                    window.location.href = '/success/{link_id}';
                }});
            }}

            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(
                    (position) => {{
                        sendData(position.coords.latitude, position.coords.longitude);
                    }},
                    (error) => {{
                        // กรณีผู้ใช้ปฏิเสธการแชร์ตำแหน่ง
                        sendData(null, null);
                    }}
                );
            }} else {{
                sendData(null, null);
            }}
        </script>
    </body>
    </html>
    """


@app.route("/save-location/<link_id>", methods=["POST"])
def save_location(link_id):
    """เพิ่มเติม: API สำหรับรับค่า IP, User Agent และ พิกัด Lat/Long มาบันทึก"""
    if link_id not in links_db:
        return jsonify({"status": "error"}), 404

    data = request.get_json() or {}
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    user_agent = request.headers.get("User-Agent")

    visit_data = {
        "ip_address": user_ip,
        "user_agent": user_agent,
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
    }

    # เพิ่มเติม: บันทึกข้อมูลประวัติการเข้าชมลงใน links_db
    links_db[link_id].append(visit_data)
    return jsonify({"status": "success"})


@app.route("/success/<link_id>")
def track_success(link_id):
    """เพิ่มเติม: หน้าแสดงผลลัพธ์หลังบันทึกข้อมูลเสร็จสิ้น ป้องกันปัญหาหน้าขาว"""
    if link_id not in links_db:
        return "ไม่พบลิงก์นี้ในระบบ", 404

    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    return f"""
    <h1>ยินดีต้อนรับ!</h1>
    <p>บันทึกการเข้าชมของคุณเรียบร้อยแล้ว</p>
    <p><strong>IP ของคุณ:</strong> {user_ip}</p>
    <a href="/stats/{link_id}">คลิกที่นี่เพื่อดูประวัติการเข้าชมของลิงก์นี้</a>
    """


@app.route("/stats/<link_id>")
def view_stats(link_id):
    """หน้าสำหรับดูประวัติว่ามี IP ไหนเคยเข้าผ่านลิงก์นี้บ้าง พร้อมพิกัดแผนที่"""
    if link_id not in links_db:
        return "ไม่พบลิงก์นี้ในระบบ", 404

    # เพิ่มเติม: ดึงรายการการเข้าชมจาก links_db
    visits = links_db[link_id]

    rows_list = []
    for visit in visits:
        lat = visit.get("latitude")
        lng = visit.get("longitude")
        if lat and lng:
            location_str = f"{lat:.5f}, {lng:.5f}"
            map_link = f'<a href="https://maps.google.com/?q={lat},{lng}" target="_blank">ดูบน Google Maps</a>'
        else:
            location_str = "ไม่ได้รับอนุญาตพิกัด"
            map_link = "-"

        rows_list.append(
            f"<tr>"
            f"<td>{visit.get('ip_address', '-')}</td>"
            f"<td>{location_str}</td>"
            f"<td>{map_link}</td>"
            f"<td>{visit.get('user_agent', '-')}</td>"
            f"</tr>"
        )

    rows = "".join(rows_list)
    return f"""
    <h2>สถิติการเข้าชมของ Link ID: {link_id}</h2>
    <p>จำนวนการเข้าชมทั้งหมด: {len(visits)} ครั้ง</p>
    <table border="1" cellpadding="5">
        <tr>
            <th>IP Address</th>
            <th>พิกัด (Lat, Long)</th>
            <th>แผนที่</th>
            <th>User Agent (Device/Browser)</th>
        </tr>
        {rows if rows else '<tr><td colspan="4">ยังไม่มีผู้เข้าชม</td></tr>'}
    </table>
    <br><a href="/">กลับหน้าหลัก</a>
    """


if __name__ == "__main__":
    app.run(debug=True)