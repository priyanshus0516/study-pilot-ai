import os
from flask import Flask, render_template, session
from config import Config
from database.database import init_db, db
from database.models import User
from services.ai_service import AIService

# Import Blueprints
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.documents import documents_bp
from routes.qa import qa_bp
from routes.quiz import quiz_bp
from routes.summary import summary_bp
from routes.flashcards import flashcards_bp
from routes.progress import progress_bp
from routes.settings import settings_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize Database
    init_db(app)

    # Register Blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(documents_bp)
    app.register_blueprint(qa_bp)
    app.register_blueprint(quiz_bp)
    app.register_blueprint(summary_bp)
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(settings_bp)

    @app.context_processor
    def inject_globals():
        current_user = None
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
        
        # Live AI Status info for header badge
        ai_service = AIService()
        ai_status = ai_service.get_status_info()
        return dict(current_user=current_user, ai_status=ai_status)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('base.html', error_title="404 - Page Not Found", error_msg="The study module or resource you requested could not be found."), 404

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return render_template('base.html', error_title="500 - Server Error", error_msg="An internal processing error occurred. Please try again or check logs."), 500

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
