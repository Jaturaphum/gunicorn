from flask import Blueprint, render_template, request, session, redirect, url_for
import api

router = Blueprint('router', __name__)

@router.route('/')
def home():
    return render_template('index.html')

@router.route('/<link_id>')
@router.route('/track/<link_id>')
def track_page(link_id):
    api.ensure_link_exists(link_id)
    return render_template('tracker.html', link_id=link_id)

@router.route('/success')
def success_page():
    return render_template('success.html')

@router.route('/api/save-location/<link_id>', methods=['POST'])
@router.route('/api/save_location/<link_id>', methods=['POST'])
def save_location(link_id):
    return api.handle_save_location(link_id)

@router.route('/login', methods=['GET', 'POST'])
@router.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == 'admin123':
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('router.admin_dashboard'))
        return render_template('login_admin.html', error="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")
    return render_template('login_admin.html')

@router.route('/logout')
@router.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_username', None)
    return redirect(url_for('router.admin_login'))

@router.route('/admin')
def admin_dashboard():
    if not session.get('admin_logged_in'):
        return redirect(url_for('router.admin_login'))
    links_data, total_visits = api.fetch_admin_dashboard_data()
    return render_template('admin.html', links_data=links_data, total_visits=total_visits, current_username=session.get('admin_username'))

@router.route('/admin/stats/<link_id>')
def admin_stats(link_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('router.admin_login'))
    visits = api.fetch_link_stats(link_id)
    if visits is None:
        return "Link not found", 404
    return render_template('admin_stats.html', link_id=link_id, visits=visits, current_username=session.get('admin_username'))

@router.route('/api/create-link', methods=['POST'])
@router.route('/admin/create_link', methods=['POST'])
def create_link():
    if not session.get('admin_logged_in'):
        return redirect(url_for('router.admin_login'))
    return api.handle_create_link()

@router.route('/api/delete-link/<link_id>', methods=['POST'])
@router.route('/admin/delete_link/<link_id>', methods=['POST'])
def delete_link(link_id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('router.admin_login'))
    return api.handle_delete_link(link_id)