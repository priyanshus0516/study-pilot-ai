from flask import Blueprint, render_template, session, redirect, url_for, flash
from routes.auth import login_required, get_current_user
from services.progress_service import ProgressService

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def root():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))
    return render_template('landing.html')

@dashboard_bp.route('/landing')
def landing():
    return render_template('landing.html')

@dashboard_bp.route('/dashboard')
@login_required
def index():
    user = get_current_user()
    if user is None:
        session.clear()
        flash('Your session has expired. Please log in again.', 'warning')
        return redirect(url_for('auth.login'))
    stats = ProgressService.get_user_dashboard_stats(user.id)
    return render_template('dashboard.html', user=user, stats=stats)
