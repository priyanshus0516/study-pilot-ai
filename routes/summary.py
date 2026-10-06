from flask import Blueprint, render_template, request, jsonify
from database.models import Document
from routes.auth import login_required, get_current_user
from services.summary_generator import SummaryService

summary_bp = Blueprint('summary', __name__, url_prefix='/summary')

@summary_bp.route('/', methods=['GET'])
@login_required
def summary_view():
    user = get_current_user()
    docs = Document.query.filter_by(user_id=user.id).all()
    selected_doc_id = request.args.get('doc_id', type=int)
    return render_template('summary.html', documents=docs, selected_doc_id=selected_doc_id)

@summary_bp.route('/generate', methods=['POST'])
@login_required
def generate_summary():
    user = get_current_user()
    data = request.get_json() or {}

    document_id = data.get('document_id')
    mode = data.get('mode', 'medium').lower()

    if not document_id:
        return jsonify({'error': 'Please select a document to summarize.'}), 400

    if mode not in ['short', 'medium', 'detailed']:
        mode = 'medium'

    try:
        service = SummaryService()
        result = service.generate_document_summary(
            user_id=user.id,
            document_id=int(document_id),
            mode=mode
        )
        return jsonify(result)
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 404
    except Exception as e:
        return jsonify({'error': f'Failed to generate summary: {str(e)}'}), 500
