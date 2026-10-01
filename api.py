import math
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone
import mysql.connector
from flask import jsonify, redirect, request, url_for

def get_db_connection():
    required_settings = ("MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE")
    missing_settings = [setting for setting in required_settings if not os.environ.get(setting)]
    if missing_settings:
        missing_names = ", ".join(missing_settings)
        raise RuntimeError(
            f"Missing MySQL environment variables: {missing_names}. "
            "Set them in the Render web service Environment settings."
        )

    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "127.0.0.1"),
        port=int(os.environ.get("MYSQL_PORT", "3306")),
        user=os.environ["MYSQL_USER"],
        password=os.environ["MYSQL_PASSWORD"],
        database=os.environ["MYSQL_DATABASE"],
        charset="utf8mb4",
    )

def init_db():
    for connection_attempt in range(12):
        try:
            database_connection = get_db_connection()
            break
        except mysql.connector.Error:
            if connection_attempt == 11:
                raise
            time.sleep(5)

    database_cursor = database_connection.cursor()
    database_cursor.execute(
        "CREATE TABLE IF NOT EXISTS links (id VARCHAR(64) PRIMARY KEY) ENGINE=InnoDB"
    )
    database_cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS visits (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            link_id VARCHAR(64),
            username VARCHAR(100),
            ip_address VARCHAR(45),
            user_agent TEXT,
            latitude DOUBLE,
            longitude DOUBLE,
            accuracy_meters DOUBLE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(link_id) REFERENCES links(id)
        ) ENGINE=InnoDB
        """
    )
    database_cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = 'visits' AND column_name = 'accuracy_meters'
        """
    )
    if database_cursor.fetchone()[0] == 0:
        database_cursor.execute("ALTER TABLE visits ADD COLUMN accuracy_meters DOUBLE")
    database_cursor.execute("DELETE FROM visits WHERE link_id = %s", ("{{ link_id }}",))
    database_cursor.execute("DELETE FROM links WHERE id = %s", ("{{ link_id }}",))
    database_connection.commit()
    database_cursor.close()
    database_connection.close()


def is_valid_link_id(link_id):
    return bool(link_id and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", link_id))


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
    database_cursor.execute("SELECT id FROM links WHERE id = %s", (link_id,))
    link_exists = database_cursor.fetchone() is not None
    database_cursor.close()
    database_connection.close()
    return link_exists


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
    database_cursor.close()
    database_connection.close()
    return links_data, total_visits


def fetch_link_stats(link_id):
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor(dictionary=True)
    database_cursor.execute("SELECT id FROM links WHERE id = %s", (link_id,))
    if not database_cursor.fetchone():
        database_cursor.close()
        database_connection.close()
        return None
    database_cursor.execute(
        """
        SELECT id, username, ip_address, latitude, longitude, accuracy_meters, user_agent, created_at
        FROM visits WHERE link_id = %s ORDER BY id DESC
        """,
        (link_id,),
    )
    raw_visits = database_cursor.fetchall()
    database_cursor.close()
    database_connection.close()
    visits = []
    for row in raw_visits:
        row["parsed_ua"] = parse_user_agent(row.get("user_agent"))
        visits.append(row)
    return visits


def fetch_live_counts(link_id=None):
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    if link_id:
        database_cursor.execute("SELECT COUNT(*) FROM visits WHERE link_id = %s", (link_id,))
        visit_count = database_cursor.fetchone()[0]
        database_cursor.close()
        database_connection.close()
        return {"visit_count": visit_count}

    database_cursor.execute("SELECT COUNT(*) FROM links")
    link_count = database_cursor.fetchone()[0]
    database_cursor.execute("SELECT COUNT(*) FROM visits")
    visit_count = database_cursor.fetchone()[0]
    database_cursor.close()
    database_connection.close()
    return {"link_count": link_count, "visit_count": visit_count}


def handle_create_link(link_id=None):
    if link_id is None:
        link_id = str(uuid.uuid4())[:8]
    elif not is_valid_link_id(link_id):
        return redirect(url_for("router.admin_dashboard"))

    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("INSERT IGNORE INTO links (id) VALUES (%s)", (link_id,))
    database_connection.commit()
    database_cursor.close()
    database_connection.close()
    return redirect(url_for("router.admin_dashboard"))


def handle_delete_link(link_id):
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("DELETE FROM visits WHERE link_id = %s", (link_id,))
    database_cursor.execute("DELETE FROM links WHERE id = %s", (link_id,))
    database_connection.commit()
    database_cursor.close()
    database_connection.close()
    return redirect(url_for("router.admin_dashboard"))


def handle_delete_visit(visit_id):
    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("SELECT link_id FROM visits WHERE id = %s", (visit_id,))
    record = database_cursor.fetchone()
    if record:
        link_id = record[0]
        database_cursor.execute("DELETE FROM visits WHERE id = %s", (visit_id,))
        database_connection.commit()
        database_cursor.close()
        database_connection.close()
        return redirect(url_for("router.admin_stats", link_id=link_id))
    database_cursor.close()
    database_connection.close()
    return redirect(url_for("router.admin_dashboard"))


def handle_save_location(link_id):
    if not is_valid_link_id(link_id):
        return jsonify({"status": "not_found"}), 404

    # เพิ่มเติม: บันทึกเฉพาะข้อมูลที่ผู้ใช้ยินยอมและส่งจาก browser geolocation
    request_data = request.get_json(silent=True) or {}
    if request_data.get("consent") is not True:
        return jsonify({"status": "consent_required"}), 400

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
    if any(
        isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value)
        for value in coordinate_values
    ):
        return jsonify({"status": "invalid_location"}), 400
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180 or accuracy_meters < 0:
        return jsonify({"status": "invalid_location"}), 400

    database_connection = get_db_connection()
    database_cursor = database_connection.cursor()
    database_cursor.execute("SELECT id FROM links WHERE id = %s", (link_id,))
    if not database_cursor.fetchone():
        database_cursor.close()
        database_connection.close()
        return jsonify({"status": "not_found"}), 404

    bangkok_timezone = timezone(timedelta(hours=7))
    current_time_bangkok = datetime.now(bangkok_timezone).strftime("%Y-%m-%d %H:%M:%S")
    database_cursor.execute(
        """
        INSERT INTO visits (
            link_id, username, ip_address, user_agent, latitude, longitude, accuracy_meters, created_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            link_id,
            username,
            None,
            request.headers.get("User-Agent"),
            latitude,
            longitude,
            accuracy_meters,
            current_time_bangkok,
        ),
    )
    database_connection.commit()
    database_cursor.close()
    database_connection.close()
    return jsonify({"status": "success"})
