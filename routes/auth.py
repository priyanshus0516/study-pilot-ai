from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database.database import db
from database.models import User, StudyActivity

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        # Guard: verify user still exists in DB (handles stale sessions after restart)
        user = db.session.get(User, session['user_id'])
        if user is None:
            session.clear()
            flash('Your session has expired. Please log in again.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    if 'user_id' in session:
        return db.session.get(User, session['user_id'])
    return None

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not name or not email or not password:
            flash('Please fill in all required fields.', 'danger')
            return render_template('signup.html', name=name, email=email)

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('signup.html', name=name, email=email)

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('signup.html', name=name, email=email)

        existing = User.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email already exists.', 'warning')
            return render_template('signup.html', name=name, email=email)

        new_user = User(name=name, email=email)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Log initial registration activity
        activity = StudyActivity(
            user_id=new_user.id,
            activity_type='account_created',
            duration=0,
            details='Joined StudyPilot AI workspace'
        )
        db.session.add(activity)
        db.session.commit()

        session['user_id'] = new_user.id
        session['user_name'] = new_user.name
        session['user_email'] = new_user.email
        flash(f'Welcome aboard, {new_user.name}! Let’s get your study space ready.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('signup.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not email or not password:
            flash('Please provide both email and password.', 'warning')
            return render_template('login.html', email=email)

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'danger')
            return render_template('login.html', email=email)

        session['user_id'] = user.id
        session['user_name'] = user.name
        session['user_email'] = user.email
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('dashboard.landing'))
