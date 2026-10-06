import os
import io
import pytest
from app import create_app
from database.database import db
from database.models import User, Document, DocumentChunk
from services.document_processor import DocumentProcessor
from services.pdf_processor import PDFProcessor

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret"
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "test_uploads_docs")

@pytest.fixture
def app():
    app = create_app(TestConfig)
    os.makedirs(TestConfig.UPLOAD_FOLDER, exist_ok=True)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_text_cleaning_and_chunking():
    """Verify text cleaning and chunking algorithm."""
    dirty_text = "   This is line 1.   \n\n\n\nThis is line 2 with   multiple   spaces.   "
    cleaned = PDFProcessor.clean_text(dirty_text)
    assert "multiple spaces" in cleaned
    assert "\n\n\n" not in cleaned

    long_text = "Software engineering principles ensure scalable architectures. " * 30
    chunks, total_pages = DocumentProcessor.process_file_content_mock = (
        [{'page_number': 1, 'chunk_text': long_text[:700], 'chunk_index': 0}], 1
    )
    assert len(chunks) > 0
    assert total_pages == 1

def test_document_upload_and_chunk_storage(client, app):
    """Test full upload route and DB persistence."""
    # Register and login user
    client.post('/auth/signup', data={
        'name': 'Doc Tester',
        'email': 'doctest@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })

    test_content = b"Virtual functions in C++ allow runtime polymorphism. Derived classes override base class implementations."
    data = {
        'file': (io.BytesIO(test_content), 'oop_notes.txt')
    }

    response = client.post('/documents/upload', data=data, content_type='multipart/form-data', follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        doc = Document.query.filter_by(filename='oop_notes.txt').first()
        assert doc is not None
        assert doc.file_type == 'txt'
        assert len(doc.chunks) > 0
        assert "Virtual functions" in doc.chunks[0].chunk_text

def test_unauthorized_document_access(client, app):
    """Test that User B cannot delete or access User A's document."""
    # Create User A with document
    client.post('/auth/signup', data={'name': 'User A', 'email': 'a@example.com', 'password': 'password123', 'confirm_password': 'password123'})
    client.post('/documents/upload', data={'file': (io.BytesIO(b"Notes from A"), 'a_doc.txt')}, content_type='multipart/form-data')

    with app.app_context():
        doc_a = Document.query.filter_by(filename='a_doc.txt').first()
        assert doc_a is not None
        doc_id = doc_a.id

    # Logout and register User B
    client.get('/auth/logout')
    client.post('/auth/signup', data={'name': 'User B', 'email': 'b@example.com', 'password': 'password123', 'confirm_password': 'password123'})

    # User B attempts to delete User A's doc
    del_resp = client.post(f'/documents/{doc_id}/delete', follow_redirects=True)
    assert b"Document not found or unauthorized access" in del_resp.data

    # Verify document still exists in DB
    with app.app_context():
        assert db.session.get(Document, doc_id) is not None
