import os
import pytest
from app import create_app
from database.database import db
from database.models import User

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "test-secret"
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "test_uploads_auth")
    WTF_CSRF_ENABLED = False

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_user_registration(client, app):
    """Test user signup and password hashing."""
    response = client.post('/auth/signup', data={
        'name': 'Priyanshu',
        'email': 'priyanshu@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    assert response.status_code == 200

    with app.app_context():
        user = User.query.filter_by(email='priyanshu@example.com').first()
        assert user is not None
        assert user.name == 'Priyanshu'
        assert user.check_password('password123') is True
        assert user.check_password('wrongpassword') is False

def test_duplicate_registration_prevented(client, app):
    """Test duplicate emails are rejected."""
    client.post('/auth/signup', data={
        'name': 'User One',
        'email': 'duplicate@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    client.get('/auth/logout')
    response = client.post('/auth/signup', data={
        'name': 'User Two',
        'email': 'duplicate@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    assert b"already exists" in response.data

def test_login_and_logout(client, app):
    """Test login session creation and safe logout."""
    client.post('/auth/signup', data={
        'name': 'Test User',
        'email': 'login@example.com',
        'password': 'securepass123',
        'confirm_password': 'securepass123'
    })
    
    # Logout
    client.get('/auth/logout')

    # Valid Login
    resp = client.post('/auth/login', data={
        'email': 'login@example.com',
        'password': 'securepass123'
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b"Student Overview" in resp.data

    # Invalid Login
    client.get('/auth/logout')
    resp_bad = client.post('/auth/login', data={
        'email': 'login@example.com',
        'password': 'badpassword'
    })
    assert b"Invalid email or password" in resp_bad.data
