import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv("SECRET_KEY", "ccaps_super_secret_key_2024_banking")
    DEBUG = os.getenv("DEBUG", "True") == "True"

    # MySQL
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "credit_card_db")
    DB_PORT = int(os.getenv("DB_PORT", 3306))

    # ML
    MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "model.pkl")
    MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")

    # Upload / Export
    EXPORT_FOLDER = os.path.join(os.path.dirname(__file__), "exports")

    # Session
    SESSION_PERMANENT = False
    SESSION_TYPE = "filesystem"

    # Admin default credentials (created on first run)
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@creditcard.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin@1234")
    ADMIN_NAME = os.getenv("ADMIN_NAME", "System Administrator")
