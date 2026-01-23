import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///techsync.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # LLM Configuration (flexible - supports OpenAI, Anthropic, Ollama)
    LLM_PROVIDER = os.environ.get('LLM_PROVIDER') or 'openai'  # openai, anthropic, ollama
    LLM_API_KEY = os.environ.get('LLM_API_KEY') or ''
    LLM_MODEL = os.environ.get('LLM_MODEL') or 'gpt-3.5-turbo'


class TestConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
