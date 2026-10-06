from flask import Blueprint, render_template
from routes.auth import login_required, get_current_user
from services.progress_service import ProgressService

progress_bp = Blueprint('progress', __name__, url_prefix='/progress')

@progress_bp.route('/', methods=['GET'])
@login_required
def progress_view():
    user = get_current_user()
    stats = ProgressService.get_user_dashboard_stats(user.id)
    return render_template('progress.html', user=user, stats=stats)
