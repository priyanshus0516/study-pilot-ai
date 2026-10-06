from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from database.database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    documents = db.relationship('Document', backref='user', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('QuestionHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    quizzes = db.relationship('Quiz', backref='user', lazy=True, cascade='all, delete-orphan')
    flashcards = db.relationship('Flashcard', backref='user', lazy=True, cascade='all, delete-orphan')
    activities = db.relationship('StudyActivity', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, default=0) # in bytes
    file_type = db.Column(db.String(20), default='pdf')
    total_pages = db.Column(db.Integer, default=1)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    chunks = db.relationship('DocumentChunk', backref='document', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('QuestionHistory', backref='document', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'total_pages': self.total_pages,
            'chunk_count': len(self.chunks),
            'uploaded_at': self.uploaded_at.strftime("%b %d, %Y %H:%M") if self.uploaded_at else ''
        }


class DocumentChunk(db.Model):
    __tablename__ = 'document_chunks'

    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    chunk_text = db.Column(db.Text, nullable=False)
    page_number = db.Column(db.Integer, default=1)
    chunk_index = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'page_number': self.page_number,
            'chunk_index': self.chunk_index,
            'preview': self.chunk_text[:150] + '...' if len(self.chunk_text) > 150 else self.chunk_text
        }


class QuestionHistory(db.Model):
    __tablename__ = 'questions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    source_reference = db.Column(db.String(255), nullable=True) # e.g. "OOP_Unit_4.pdf – Page 12"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'answer': self.answer,
            'document_id': self.document_id,
            'source_reference': self.source_reference,
            'created_at': self.created_at.strftime("%b %d, %H:%M") if self.created_at else ''
        }


class Quiz(db.Model):
    __tablename__ = 'quizzes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    topic = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.String(50), default='Medium')
    score = db.Column(db.Integer, default=0)
    total_questions = db.Column(db.Integer, default=0)
    completed = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    questions = db.relationship('QuizQuestion', backref='quiz', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'difficulty': self.difficulty,
            'score': self.score,
            'total_questions': self.total_questions,
            'percentage': round((self.score / self.total_questions * 100) if self.total_questions > 0 else 0, 1),
            'completed': self.completed,
            'created_at': self.created_at.strftime("%b %d, %Y") if self.created_at else ''
        }


class QuizQuestion(db.Model):
    __tablename__ = 'quiz_questions'

    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quizzes.id'), nullable=False)
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.Text, nullable=False)
    option_b = db.Column(db.Text, nullable=False)
    option_c = db.Column(db.Text, nullable=False)
    option_d = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(5), nullable=False) # 'A', 'B', 'C', or 'D'
    selected_answer = db.Column(db.String(5), nullable=True)
    explanation = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'question': self.question,
            'options': {
                'A': self.option_a,
                'B': self.option_b,
                'C': self.option_c,
                'D': self.option_d,
            },
            'correct_answer': self.correct_answer,
            'selected_answer': self.selected_answer,
            'explanation': self.explanation
        }


class Flashcard(db.Model):
    __tablename__ = 'flashcards'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True)
    topic = db.Column(db.String(150), nullable=False)
    question = db.Column(db.Text, nullable=False) # Front
    answer = db.Column(db.Text, nullable=False)   # Back
    is_learned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'topic': self.topic,
            'question': self.question,
            'answer': self.answer,
            'is_learned': self.is_learned,
            'created_at': self.created_at.strftime("%b %d, %Y") if self.created_at else ''
        }


class StudyActivity(db.Model):
    __tablename__ = 'study_activity'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    activity_type = db.Column(db.String(50), nullable=False) # 'upload', 'qa', 'quiz', 'flashcard', 'summary'
    duration = db.Column(db.Integer, default=5) # in minutes
    details = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'activity_type': self.activity_type,
            'duration': self.duration,
            'details': self.details,
            'created_at': self.created_at.strftime("%b %d, %H:%M") if self.created_at else ''
        }
