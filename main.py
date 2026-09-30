import uuid
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

# เก็บข้อมูลไว้ในหน่วยความจำ (Memory Storage)
links_db = {}


# ==========================================
# 1. PUBLIC PAGES
# ==========================================


@app.route("/")
def index():
    """หน้าหลักแบบ Blank Page"""
    return render_template("index.html")


@app.route("/track/<link_id>")
def track_session(link_id):
    """หน้าสำหรับขออนุญาตและบันทึกพิกัด"""
    if link_id not in links_db:
        return render_template("index.html"), 404
    return render_template("track.html", link_id=link_id)


@app.route("/success")
def success():
    """หน้าปลายทางหลังบันทึกข้อมูลเสร็จสิ้น"""
    return render_template("success.html")


# ==========================================
# 2. ADMIN PAGES
# ==========================================


@app.route("/admin")
def admin_dashboard():
    """หน้า Admin Dashboard"""
    return render_template("admin_dashboard.html", links_db=links_db)


@app.route("/admin/stats/<link_id>")
def admin_view_stats(link_id):
    """หน้าแสดงสถิติการเข้าชม"""
    if link_id not in links_db:
        return "ไม่พบลิงก์นี้ในระบบ", 404

    visits = links_db[link_id]
    return render_template("admin_stats.html", link_id=link_id, visits=visits)


# ==========================================
# 3. API ENDPOINTS
# ==========================================


@app.route("/api/create-link", methods=["POST"])
def api_create_link():
    """API สร้าง Unique Link ใหม่"""
    unique_id = str(uuid.uuid4())[:8]
    links_db[unique_id] = []
    return redirect(url_for("admin_dashboard"))


@app.route("/api/save-location/<link_id>", methods=["POST"])
def api_save_location(link_id):
    """API บันทึกข้อมูล IP, User Agent และ GPS"""
    if link_id not in links_db:
        return jsonify({"status": "error", "message": "Link not found"}), 404

    data = request.get_json() or {}
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    user_agent = request.headers.get("User-Agent")

    visit_data = {
        "ip_address": user_ip,
        "user_agent": user_agent,
        "latitude": data.get("latitude"),
        "longitude": data.get("longitude"),
    }

    links_db[link_id].append(visit_data)
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(debug=True)