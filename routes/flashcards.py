from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.models import Flashcard, Document
from routes.auth import login_required, get_current_user
from services.flashcard_generator import FlashcardService

flashcards_bp = Blueprint('flashcards', __name__, url_prefix='/flashcards')

@flashcards_bp.route('/', methods=['GET'])
@login_required
def flashcards_home():
    user = get_current_user()
    docs = Document.query.filter_by(user_id=user.id).all()
    selected_topic = request.args.get('topic', '')
    
    query = Flashcard.query.filter_by(user_id=user.id)
    if selected_topic:
        query = query.filter_by(topic=selected_topic)
    cards = query.order_by(Flashcard.created_at.desc()).all()

    # Collect distinct topics
    all_cards = Flashcard.query.filter_by(user_id=user.id).all()
    topics = sorted(list(set(c.topic for c in all_cards if c.topic)))

    total_count = len(cards)
    learned_count = sum(1 for c in cards if c.is_learned)

    return render_template(
        'flashcards.html',
        documents=docs,
        flashcards=cards,
        topics=topics,
        selected_topic=selected_topic,
        total_count=total_count,
        learned_count=learned_count
    )

@flashcards_bp.route('/generate', methods=['POST'])
@login_required
def generate_cards():
    user = get_current_user()
    document_id = request.form.get('document_id')
    topic = request.form.get('topic', '').strip()
    count = int(request.form.get('count', 6))

    doc_id_val = int(document_id) if document_id and document_id.isdigit() else None

    if not topic and not doc_id_val:
        flash('Please specify a topic or select a document to generate flashcards.', 'warning')
        return redirect(url_for('flashcards.flashcards_home'))

    try:
        service = FlashcardService()
        cards = service.generate_cards_from_document(
            user_id=user.id,
            document_id=doc_id_val,
            topic=topic,
            count=min(max(count, 3), 15)
        )
        flash(f'Successfully generated {len(cards)} flashcards!', 'success')
    except Exception as e:
        flash(f'Error generating flashcards: {str(e)}', 'danger')

    return redirect(url_for('flashcards.flashcards_home'))

@flashcards_bp.route('/create-manual', methods=['POST'])
@login_required
def create_manual():
    user = get_current_user()
    topic = request.form.get('topic', '').strip() or 'General'
    question = request.form.get('question', '').strip()
    answer = request.form.get('answer', '').strip()

    if not question or not answer:
        flash('Please provide both the front question and back answer.', 'warning')
        return redirect(url_for('flashcards.flashcards_home'))

    service = FlashcardService()
    service.create_card_manually(user_id=user.id, topic=topic, question=question, answer=answer)
    flash('Flashcard added manually!', 'success')
    return redirect(url_for('flashcards.flashcards_home'))

@flashcards_bp.route('/<int:card_id>/toggle', methods=['POST'])
@login_required
def toggle_status(card_id):
    user = get_current_user()
    service = FlashcardService()
    try:
        new_status = service.toggle_learned_status(card_id=card_id, user_id=user.id)
        return jsonify({'success': True, 'is_learned': new_status})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@flashcards_bp.route('/<int:card_id>/delete', methods=['POST'])
@login_required
def delete_card(card_id):
    user = get_current_user()
    service = FlashcardService()
    try:
        service.delete_card(card_id=card_id, user_id=user.id)
        flash('Flashcard removed.', 'info')
    except Exception as e:
        flash(f'Error removing card: {str(e)}', 'danger')
    return redirect(url_for('flashcards.flashcards_home'))
