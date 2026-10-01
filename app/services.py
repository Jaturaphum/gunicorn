import math
import re
import uuid
from datetime import datetime, timedelta, timezone
from flask import jsonify, redirect, request, url_for
from .database import execute_query, get_db_connection, get_db_cursor

def is_valid_link_id(link_id):
    res = bool(link_id and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", link_id))
    return res

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
    database_cursor = get_db_cursor(database_connection)
    execute_query(database_cursor, "SELECT id FROM links WHERE id = ?", (link_id,))
    link_exists = database_cursor.fetchone() is not None
    database_cursor.close()
    database_connection.close()
    return link_exists

def fetch_admin_dashboard_data():
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection)
    execute_query(database_cursor, "SELECT links.id, COUNT(visits.id) FROM links LEFT JOIN visits ON links.id = visits.link_id GROUP BY links.id ORDER BY links.id DESC")
    links_data = database_cursor.fetchall()
    execute_query(database_cursor, "SELECT COUNT(*) FROM visits")
    total_visits = database_cursor.fetchone()[0]
    database_cursor.close()
    database_connection.close()
    res = (links_data, total_visits)
    return res

def fetch_link_stats(link_id):
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection, dictionary=True)
    execute_query(database_cursor, "SELECT id FROM links WHERE id = ?", (link_id,))
    if not database_cursor.fetchone():
        database_cursor.close()
        database_connection.close()
        return None
    execute_query(database_cursor, "SELECT id, username, ip_address, latitude, longitude, accuracy_meters, is_sharing, user_agent, created_at FROM visits WHERE link_id = ? ORDER BY id DESC", (link_id,))
    raw_visits = database_cursor.fetchall()
    database_cursor.close()
    database_connection.close()
    visits = []
    for raw_visit in raw_visits:
        visit = dict(raw_visit)
        visit["parsed_ua"] = parse_user_agent(visit.get("user_agent"))
        visits.append(visit)
    return visits

def fetch_live_counts(link_id=None):
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection)
    if link_id:
        execute_query(database_cursor, "SELECT COUNT(*) FROM visits WHERE link_id = ?", (link_id,))
        visit_count = database_cursor.fetchone()[0]
        database_cursor.close()
        database_connection.close()
        return {"visit_count": visit_count}
    execute_query(database_cursor, "SELECT COUNT(*) FROM links")
    link_count = database_cursor.fetchone()[0]
    execute_query(database_cursor, "SELECT COUNT(*) FROM visits")
    visit_count = database_cursor.fetchone()[0]
    database_cursor.close()
    database_connection.close()
    res = {"link_count": link_count, "visit_count": visit_count}
    return res

def fetch_live_locations(link_id):
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection, dictionary=True)
    execute_query(database_cursor, "SELECT id, username, ip_address, latitude, longitude, accuracy_meters, is_sharing, created_at FROM visits WHERE link_id = ? ORDER BY id DESC LIMIT 50", (link_id,))
    live_locations = [dict(location) for location in database_cursor.fetchall()]
    database_cursor.close()
    database_connection.close()
    current_time = datetime.now(timezone(timedelta(hours=7))).replace(tzinfo=None)
    for location in live_locations:
        last_update = location.get("created_at")
        if isinstance(last_update, str):
            try:
                last_update = datetime.fromisoformat(last_update)
            except ValueError:
                last_update = None
        location["is_sharing"] = bool(location.get("is_sharing") and last_update and (current_time - last_update).total_seconds() <= 30)
    return live_locations

def handle_create_link(link_id=None):
    if link_id is None:
        link_id = str(uuid.uuid4())[:8]
    elif not is_valid_link_id(link_id):
        return redirect(url_for("router.admin_dashboard"))
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection)
    execute_query(database_cursor, "INSERT OR IGNORE INTO links (id) VALUES (?)", (link_id,))
    database_connection.commit()
    database_cursor.close()
    database_connection.close()
    res = redirect(url_for("router.admin_dashboard"))
    return res

def handle_delete_link(link_id):
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection)
    execute_query(database_cursor, "DELETE FROM visits WHERE link_id = ?", (link_id,))
    execute_query(database_cursor, "DELETE FROM links WHERE id = ?", (link_id,))
    database_connection.commit()
    database_cursor.close()
    database_connection.close()
    res = redirect(url_for("router.admin_dashboard"))
    return res

def handle_delete_visit(visit_id):
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection)
    execute_query(database_cursor, "SELECT link_id FROM visits WHERE id = ?", (visit_id,))
    record = database_cursor.fetchone()
    if record:
        link_id = record[0]
        execute_query(database_cursor, "DELETE FROM visits WHERE id = ?", (visit_id,))
        database_connection.commit()
        database_cursor.close()
        database_connection.close()
        return redirect(url_for("router.admin_stats", link_id=link_id))
    database_cursor.close()
    database_connection.close()
    res = redirect(url_for("router.admin_dashboard"))
    return res

def handle_save_location(link_id):
    if not is_valid_link_id(link_id):
        return jsonify({"status": "not_found"}), 404
    request_data = request.get_json(silent=True) or {}
    if request_data.get("consent") is not True:
        return jsonify({"status": "consent_required"}), 400
    session_id = request_data.get("session_id")
    if not isinstance(session_id, str) or not re.fullmatch(r"[a-fA-F0-9-]{36}", session_id):
        return jsonify({"status": "invalid_session"}), 400
    username = request_data.get("username", "")
    if not isinstance(username, str):
        return jsonify({"status": "invalid_username"}), 400
    username = username.strip()
    latitude = request_data.get("latitude")
    longitude = request_data.get("longitude")
    accuracy_meters = request_data.get("accuracy")
    coordinate_values = (latitude, longitude, accuracy_meters)
    if not username or len(username) > 100:
        return jsonify({"status": "invalid_username"}), 400
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in coordinate_values):
        return jsonify({"status": "invalid_location"}), 400
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180 or accuracy_meters < 0:
        return jsonify({"status": "invalid_location"}), 400
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection)
    execute_query(database_cursor, "SELECT id FROM links WHERE id = ?", (link_id,))
    if not database_cursor.fetchone():
        database_cursor.close()
        database_connection.close()
        return jsonify({"status": "not_found"}), 404
    bangkok_timezone = timezone(timedelta(hours=7))
    current_time_bangkok = datetime.now(bangkok_timezone).strftime("%Y-%m-%d %H:%M:%S")
    execute_query(database_cursor, "SELECT id FROM visits WHERE session_id = ? AND link_id = ?", (session_id, link_id))
    existing_visit = database_cursor.fetchone()
    if existing_visit:
        execute_query(database_cursor, "UPDATE visits SET username = ?, ip_address = ?, latitude = ?, longitude = ?, accuracy_meters = ?, is_sharing = 1, created_at = ? WHERE id = ?", (username, request.remote_addr, latitude, longitude, accuracy_meters, current_time_bangkok, existing_visit[0]))
    else:
        execute_query(database_cursor, "INSERT INTO visits (link_id, username, ip_address, user_agent, latitude, longitude, accuracy_meters, session_id, is_sharing, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (link_id, username, request.remote_addr, request.headers.get("User-Agent"), latitude, longitude, accuracy_meters, session_id, 1, current_time_bangkok))
    database_connection.commit()
    database_cursor.close()
    database_connection.close()
    res = jsonify({"status": "success"})
    return res

def handle_stop_location(link_id):
    if not is_valid_link_id(link_id):
        return jsonify({"status": "not_found"}), 404
    request_data = request.get_json(silent=True) or {}
    session_id = request_data.get("session_id")
    if not isinstance(session_id, str) or not re.fullmatch(r"[a-fA-F0-9-]{36}", session_id):
        return jsonify({"status": "invalid_session"}), 400
    database_connection = get_db_connection()
    database_cursor = get_db_cursor(database_connection)
    execute_query(database_cursor, "UPDATE visits SET is_sharing = 0 WHERE link_id = ? AND session_id = ?", (link_id, session_id))
    database_connection.commit()
    database_cursor.close()
    database_connection.close()
    return jsonify({"status": "success"})