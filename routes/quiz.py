from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from database.database import db
from database.models import Quiz, QuizQuestion, Document
from routes.auth import login_required, get_current_user
from services.quiz_generator import QuizService

quiz_bp = Blueprint('quiz', __name__, url_prefix='/quiz')

@quiz_bp.route('/', methods=['GET'])
@login_required
def quiz_home():
    user = get_current_user()
    docs = Document.query.filter_by(user_id=user.id).all()
    quizzes = Quiz.query.filter_by(user_id=user.id).order_by(Quiz.created_at.desc()).all()
    preset_topic = request.args.get('topic', '')
    return render_template('quiz.html', documents=docs, quizzes=quizzes, preset_topic=preset_topic)

@quiz_bp.route('/create', methods=['POST'])
@login_required
def create_quiz():
    user = get_current_user()
    document_id = request.form.get('document_id')
    topic = request.form.get('topic', '').strip()
    difficulty = request.form.get('difficulty', 'Medium')
    num_questions = int(request.form.get('num_questions', 5))

    doc_id_val = int(document_id) if document_id and document_id.isdigit() else None

    if not topic and not doc_id_val:
        flash('Please specify a topic or select a document for the quiz.', 'warning')
        return redirect(url_for('quiz.quiz_home'))

    try:
        service = QuizService()
        quiz = service.create_quiz_from_document(
            user_id=user.id,
            document_id=doc_id_val,
            topic=topic,
            difficulty=difficulty,
            num_questions=min(max(num_questions, 3), 15)
        )
        flash(f'Quiz created! {len(quiz.questions)} questions generated.', 'success')
        return redirect(url_for('quiz.take_quiz', quiz_id=quiz.id))
    except Exception as e:
        flash(f'Error creating quiz: {str(e)}', 'danger')
        return redirect(url_for('quiz.quiz_home'))

@quiz_bp.route('/<int:quiz_id>', methods=['GET'])
@login_required
def take_quiz(quiz_id):
    user = get_current_user()
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=user.id).first()

    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('quiz.quiz_home'))

    if quiz.completed:
        return redirect(url_for('quiz.quiz_results', quiz_id=quiz.id))

    return render_template('quiz_take.html', quiz=quiz, questions=quiz.questions)

@quiz_bp.route('/<int:quiz_id>/submit', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    user = get_current_user()
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=user.id).first()

    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('quiz.quiz_home'))

    # Gather answers from form
    answers = {}
    for q in quiz.questions:
        ans_val = request.form.get(f'question_{q.id}', '')
        answers[q.id] = ans_val

    service = QuizService()
    results = service.submit_quiz_answers(quiz_id=quiz.id, user_id=user.id, answers=answers)

    flash(f"Quiz completed! You scored {results['score']} out of {results['total_questions']} ({results['percentage']}%).", 'info')
    return redirect(url_for('quiz.quiz_results', quiz_id=quiz.id))

@quiz_bp.route('/<int:quiz_id>/results', methods=['GET'])
@login_required
def quiz_results(quiz_id):
    user = get_current_user()
    quiz = Quiz.query.filter_by(id=quiz_id, user_id=user.id).first()

    if not quiz:
        flash('Quiz not found.', 'danger')
        return redirect(url_for('quiz.quiz_home'))

    percentage = round((quiz.score / quiz.total_questions * 100) if quiz.total_questions > 0 else 0, 1)
    correct_count = sum(1 for q in quiz.questions if q.selected_answer == q.correct_answer)
    incorrect_count = quiz.total_questions - correct_count

    return render_template(
        'quiz_results.html',
        quiz=quiz,
        percentage=percentage,
        correct_count=correct_count,
        incorrect_count=incorrect_count,
        questions=quiz.questions
    )
