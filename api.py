import os
import re
import sqlite3
import uuid
import urllib.request
import json
from datetime import datetime, timezone, timedelta
from flask import jsonify, redirect, request, url_for

base_directory = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(base_directory, "database.db")

def get_db_connection():
    database_connection = sqlite3.connect(database_path)
    return database_connection

def init_db():
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("CREATE TABLE IF NOT EXISTS links (id TEXT PRIMARY KEY)")
    database_cursor.execute(
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
    database_connection.commit()
    database_connection.close()

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

def ensure_link_exists(link_id):
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    if not database_cursor.fetchone():
        database_cursor.execute("INSERT INTO links (id) VALUES (?)", (link_id,))
        database_connection.commit()
    database_connection.close()

def fetch_admin_dashboard_data():
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute(
        """
        SELECT links.id, COUNT(visits.id)
        FROM links LEFT JOIN visits ON links.id = visits.link_id
        GROUP BY links.id ORDER BY links.id DESC
        """
    )
    links_data = database_cursor.fetchall()
    database_cursor.execute("SELECT COUNT(*) FROM visits")
    total_visits = database_cursor.fetchone()[0]
    database_connection.close()
    return links_data, total_visits

def fetch_link_stats(link_id):
    database_connection = get_db_connection()
    database_connection.row_factory = sqlite3.Row
    database_cursor = database_connection.cursor()
    database_cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    if not database_cursor.fetchone():
        database_connection.close()
        return None
    database_cursor.execute(
        """
        SELECT id, username, ip_address, latitude, longitude, user_agent, created_at 
        FROM visits WHERE link_id = ? ORDER BY id DESC
        """,
        (link_id,),
    )
    raw_visits = database_cursor.fetchall()
    database_connection.close()
    visits = []
    for row in raw_visits:
        item = dict(row)
        item["parsed_ua"] = parse_user_agent(item.get("user_agent"))
        visits.append(item)
    return visits

def handle_create_link():
    unique_id = str(uuid.uuid4())[:8]
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("INSERT INTO links (id) VALUES (?)", (unique_id,))
    database_connection.commit()
    database_connection.close()
    return redirect(url_for("router.admin_dashboard"))

def handle_delete_link(link_id):
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("DELETE FROM visits WHERE link_id = ?", (link_id,))
    database_cursor.execute("DELETE FROM links WHERE id = ?", (link_id,))
    database_connection.commit()
    database_connection.close()
    return redirect(url_for("router.admin_dashboard"))

def handle_delete_visit(visit_id):
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("SELECT link_id FROM visits WHERE id = ?", (visit_id,))
    record = database_cursor.fetchone()
    if record:
        link_id = record[0]
        database_cursor.execute("DELETE FROM visits WHERE id = ?", (visit_id,))
        database_connection.commit()
        database_connection.close()
        return redirect(url_for("router.admin_stats", link_id=link_id))
    database_connection.close()
    return redirect(url_for("router.admin_dashboard"))

def handle_save_location(link_id):
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("SELECT id FROM links WHERE id = ?", (link_id,))
    if not database_cursor.fetchone():
        database_cursor.execute("INSERT INTO links (id) VALUES (?)", (link_id,))

    request_data = request.get_json() or {}
    user_ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
    if user_ip_address and "," in user_ip_address:
        user_ip_address = user_ip_address.split(",")[0].strip()

    username = request_data.get("username") or "ไม่ระบุตัวตน"
    latitude = request_data.get("latitude")
    longitude = request_data.get("longitude")

    if latitude is None or longitude is None:
        try:
            lookup_url = f"http://ip-api.com/json/{user_ip_address}"
            response = urllib.request.urlopen(lookup_url, timeout=3)
            location_data = json.loads(response.read().decode("utf-8"))
            if location_data.get("status") == "success":
                latitude = location_data.get("lat")
                longitude = location_data.get("lon")
        except Exception:
            pass

    bangkok_timezone = timezone(timedelta(hours=7))
    current_time_bangkok = datetime.now(bangkok_timezone).strftime("%Y-%m-%d %H:%M:%S")

    database_cursor.execute(
        """
        INSERT INTO visits (link_id, username, ip_address, user_agent, latitude, longitude, created_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            link_id,
            username,
            user_ip_address,
            request.headers.get("User-Agent"),
            latitude,
            longitude,
            current_time_bangkok,
        ),
    )
    database_connection.commit()
    database_connection.close()

    return jsonify({"status": "success"})