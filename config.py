import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration variables."""

    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-should-be-changed"
