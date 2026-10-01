from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for
from . import services

router = Blueprint("router", __name__)

@router.route("/favicon.ico")
def favicon():
    res = "", 204
    return res

@router.route("/")
def home():
    res = render_template("index.html")
    return res

@router.route("/<link_id>")
@router.route("/track/<link_id>")
def track_page(link_id):
    if link_id == "favicon.ico":
        return "", 204
    if not services.is_valid_link_id(link_id) or not services.ensure_link_exists(link_id):
        return "Link not found", 404
    res = render_template("tracker.html", link_id=link_id)
    return res

@router.route("/success")
def success_page():
    res = render_template("success.html")
    return res

@router.route("/api/save-location/<link_id>", methods=["POST"])
@router.route("/api/save_location/<link_id>", methods=["POST"])
def save_location(link_id):
    if link_id == "favicon.ico":
        return "", 204
    res = services.handle_save_location(link_id)
    return res

@router.route("/api/stop-location/<link_id>", methods=["POST"])
def stop_location(link_id):
    res = services.handle_stop_location(link_id)
    return res

@router.route("/login", methods=["GET", "POST"])
@router.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin123":
            session["admin_logged_in"] = True
            session["admin_username"] = username
            return redirect(url_for("router.admin_dashboard"))
        return render_template("login_admin.html", error="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    res = render_template("login_admin.html")
    return res

@router.route("/logout")
@router.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    res = redirect(url_for("router.admin_login"))
    return res

@router.route("/admin")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("router.admin_login"))
    links_data, total_visits = services.fetch_admin_dashboard_data()
    res = render_template("admin.html", links_data=links_data, total_visits=total_visits, current_username=session.get("admin_username"))
    return res

@router.route("/admin/stats/<link_id>")
def admin_stats(link_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("router.admin_login"))
    visits = services.fetch_link_stats(link_id)
    if visits is None:
        return "Link not found", 404
    res = render_template("admin_stats.html", link_id=link_id, visits=visits)
    return res

@router.route("/api/admin/updates")
def admin_updates():
    if not session.get("admin_logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    link_id = request.args.get("link_id")
    if link_id and not services.ensure_link_exists(link_id):
        return jsonify({"error": "not_found"}), 404
    res = jsonify(services.fetch_live_counts(link_id))
    return res

@router.route("/api/admin/live-locations/<link_id>")
def admin_live_locations(link_id):
    if not session.get("admin_logged_in"):
        return jsonify({"error": "unauthorized"}), 401
    if not services.ensure_link_exists(link_id):
        return jsonify({"error": "not_found"}), 404
    res = jsonify(services.fetch_live_locations(link_id))
    return res

@router.route("/api/create-link", methods=["POST"])
@router.route("/admin/create_link", methods=["POST"])
def create_link():
    if not session.get("admin_logged_in"):
        return redirect(url_for("router.admin_login"))
    res = services.handle_create_link(request.form.get("link_id") or None)
    return res

@router.route("/api/delete-link/<link_id>", methods=["POST"])
@router.route("/admin/delete_link/<link_id>", methods=["POST"])
def delete_link(link_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("router.admin_login"))
    res = services.handle_delete_link(link_id)
    return res

@router.route("/api/delete-visit/<int:visit_id>", methods=["POST"])
def delete_visit(visit_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("router.admin_login"))
    res = services.handle_delete_visit(visit_id)
    return res