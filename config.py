import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    DEV_KEY = os.environ.get("DEV_KEY", "bb-huge-dev-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'bb_huge.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.path.join(BASE_DIR, "app", "static", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "pdf", "txt", "md", "xml", "json", "html", "zip"}

    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # MCP server settings
    MCP_HOST = os.environ.get("MCP_HOST", "127.0.0.1")
    MCP_PORT = int(os.environ.get("MCP_PORT", "5001"))
    FLASK_PORT = int(os.environ.get("FLASK_PORT", "5000"))
