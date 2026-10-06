from flask import Blueprint, render_template, request, jsonify
from database.database import db
from database.models import Document, DocumentChunk, QuestionHistory, StudyActivity
from routes.auth import login_required, get_current_user
from services.document_processor import DocumentProcessor
from services.ai_service import AIService

qa_bp = Blueprint('qa', __name__)

@qa_bp.route('/chat', methods=['GET'])
@login_required
def chat_view():
    user = get_current_user()
    docs = Document.query.filter_by(user_id=user.id).all()
    history = QuestionHistory.query.filter_by(user_id=user.id)\
        .order_by(QuestionHistory.created_at.asc()).limit(30).all()
    return render_template('chat.html', documents=docs, history=history, user=user)

@qa_bp.route('/api/chat', methods=['POST'])
@login_required
def ask_question():
    user = get_current_user()
    data = request.get_json() or {}

    question = data.get('question', '').strip()
    document_id = data.get('document_id')

    if not question:
        return jsonify({'error': 'Please enter a question to ask.'}), 400

    # Retrieve candidate chunks
    if document_id:
        doc = Document.query.filter_by(id=document_id, user_id=user.id).first()
        if not doc:
            return jsonify({'error': 'Selected document not found.'}), 404
        chunks_pool = doc.chunks
        doc_label = doc.filename
    else:
        # Search all documents owned by user
        user_docs = Document.query.filter_by(user_id=user.id).all()
        chunks_pool = []
        for d in user_docs:
            chunks_pool.extend(d.chunks)
        doc_label = "Uploaded Study Notes"

    if not chunks_pool:
        return jsonify({
            'answer': "You haven't uploaded any study materials yet! Please upload your PDF, notes, or documents first in the 'My Materials' section so I can answer questions grounded in your course content.",
            'source': "No documents uploaded",
            'chunks': []
        })

    # Semantic/keyword retrieval
    top_chunks = DocumentProcessor.search_relevant_chunks(chunks_pool, question, top_k=4)

    # Invoke AI Service
    ai_service = AIService()
    result = ai_service.answer_question(
        question=question,
        chunks=top_chunks,
        doc_name=doc_label
    )

    # Save to QuestionHistory
    qh = QuestionHistory(
        user_id=user.id,
        document_id=int(document_id) if document_id else None,
        question=question,
        answer=result['answer'],
        source_reference=result.get('source', '')
    )
    db.session.add(qh)

    # Log study activity
    activity = StudyActivity(
        user_id=user.id,
        activity_type='qa',
        duration=3,
        details=f"Asked: {question[:50]}..."
    )
    db.session.add(activity)
    db.session.commit()

    chunk_previews = [
        {
            'page_number': ch.page_number,
            'text': (ch.chunk_text[:120] + '...') if len(ch.chunk_text) > 120 else ch.chunk_text
        }
        for ch in top_chunks
    ]

    return jsonify({
        'id': qh.id,
        'question': question,
        'answer': result['answer'],
        'source': result.get('source', ''),
        'chunks': chunk_previews,
        'created_at': qh.created_at.strftime("%I:%M %p")
    })

@qa_bp.route('/api/chat/history', methods=['GET'])
@login_required
def get_history():
    user = get_current_user()
    history = QuestionHistory.query.filter_by(user_id=user.id)\
        .order_by(QuestionHistory.created_at.desc()).limit(20).all()
    return jsonify([h.to_dict() for h in history])
