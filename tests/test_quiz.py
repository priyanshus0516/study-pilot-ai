import pytest
from app import create_app
from database.database import db
from database.models import User, Quiz, QuizQuestion
from services.quiz_generator import QuizService

import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret"
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "test_uploads_quiz")

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_quiz_generation_and_scoring(app):
    with app.app_context():
        # Setup user
        user = User(name="Quiz Student", email="quiz@example.com")
        user.set_password("pass123")
        db.session.add(user)
        db.session.commit()

        service = QuizService()
        quiz = service.create_quiz_from_document(
            user_id=user.id,
            document_id=None,
            topic="Operating Systems",
            difficulty="Medium",
            num_questions=5
        )

        assert quiz is not None
        assert len(quiz.questions) == 5
        assert quiz.completed is False

        # Simulate answers: 4 correct, 1 incorrect
        answers = {}
        for idx, q in enumerate(quiz.questions):
            if idx == 0:
                # Intentionally wrong
                answers[q.id] = 'D' if q.correct_answer != 'D' else 'C'
            else:
                answers[q.id] = q.correct_answer

        results = service.submit_quiz_answers(quiz.id, user.id, answers)
        assert results['score'] == 4
        assert results['total_questions'] == 5
        assert results['percentage'] == 80.0
        assert results['correct_count'] == 4
        assert results['incorrect_count'] == 1
        assert quiz.completed is True
