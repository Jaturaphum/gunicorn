import os
import re
import sqlite3
import uuid
from datetime import datetime
from flask import jsonify, redirect, request, url_for
import requests

BASE_DIRECTORY = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIRECTORY, "database.db")

def get_db_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    return connection

def init_db():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS links (id TEXT PRIMARY KEY)")
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            link_id TEXT,
            username TEXT,
            ip_address TEXT,
            user_agent TEXT,
            latitude REAL,
            longitude REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(link_id) REFERENCES links(id)
        )
        """
    )
    try:
        cursor.execute("ALTER TABLE visits ADD COLUMN username TEXT")
    except sqlite3.OperationalError:
        pass
    try:
        cursor.execute("ALTER TABLE visits ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
    except sqlite3.OperationalError:
        pass
    connection.commit()
    connection.close()

def parse_user_agent(user_agent_string):
    if not user_agent_string or user_agent_string == "-":
        return {}
    parsed_data = {}
    operating_system_match = re.search(r"\((.*?)\)", user_agent_string)
    if operating_system_match:
        parsed_data["OS / Platform"] = operating_system_match.group(1)
    tokens = re.findall(r"([a-zA-Z0-9\-_]+)/([0-9\.]+)", user_agent_string)
    for key, value in tokens:
        parsed_data[key] = value
    return parsed_data

def get_location_from_ip(ip_address):
    if (
        not ip_address
        or ip_address in ["127.0.0.1", "localhost"]
        or ip_address.startswith(("10.", "172.", "192.168."))
    ):
        return None, None
    try:
        response = requests.get(f"http://ip-api.com/json/{ip_address}", timeout=3).json()
        if response.get("status") == "success":
            return response.get("lat"), response.get("lon")
    except Exception:
        pass
    return None, None

def ensure_link_exists(link_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO links (id) VALUES (?)", (link_id,))
        connection.commit()
    connection.close()

def fetch_admin_dashboard_data():
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT links.id, COUNT(visits.id)
        FROM links LEFT JOIN visits ON links.id = visits.link_id
        GROUP BY links.id ORDER BY links.id DESC
        """
    )
    links_data = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM visits")
    total_visits = cursor.fetchone()[0]
    connection.close()
    return links_data, total_visits

def fetch_link_stats(link_id):
    connection = get_db_connection()
    connection.row_factory = sqlite3.Row
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    if not cursor.fetchone():
        connection.close()
        return None
    cursor.execute(
        """
        SELECT id, username, ip_address, latitude, longitude, user_agent, created_at 
        FROM visits WHERE link_id = ? ORDER BY id DESC
        """,
        (link_id,),
    )
    raw_visits = cursor.fetchall()
    connection.close()
    visits = []
    for row in raw_visits:
        item = dict(row)
        item["parsed_ua"] = parse_user_agent(item.get("user_agent"))
        visits.append(item)
    return visits

def handle_create_link():
    unique_id = str(uuid.uuid4())[:8]
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("INSERT INTO links (id) VALUES (?)", (unique_id,))
    connection.commit()
    connection.close()
    return redirect(url_for("router.admin_dashboard"))

def handle_delete_link(link_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("DELETE FROM visits WHERE link_id = ?", (link_id,))
    cursor.execute("DELETE FROM links WHERE id = ?", (link_id,))
    connection.commit()
    connection.close()
    return redirect(url_for("router.admin_dashboard"))

def handle_save_location(link_id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    if not cursor.fetchone():
        connection.close()
        return jsonify({"status": "error", "message": "Link not found"}), 404

    request_data = request.get_json() or {}
    user_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip and "," in user_ip:
        user_ip = user_ip.split(",")[0].strip()

    username = request_data.get("username", "ไม่ระบุตัวตน")
    latitude = request_data.get("latitude")
    longitude = request_data.get("longitude")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if latitude is None or longitude is None:
        latitude, longitude = get_location_from_ip(user_ip)

    cursor.execute(
        """
        INSERT INTO visits (link_id, username, ip_address, user_agent, latitude, longitude, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            link_id,
            username,
            user_ip,
            request.headers.get("User-Agent"),
            latitude,
            longitude,
            current_time,
        ),
    )
    connection.commit()
    connection.close()

    return jsonify({"status": "success"})