import os
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "studypilot-super-secret-key-2026")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'studypilot.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {"pdf", "txt", "docx"}
    
    # AI Engine settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "auto")  # auto / gemini / openai / offline
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    @classmethod
    def reload_env(cls):
        load_dotenv(override=True)
        cls.GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
        cls.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
        cls.DEFAULT_AI_PROVIDER = os.getenv("DEFAULT_AI_PROVIDER", "auto")
        cls.GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        cls.OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
