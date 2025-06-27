import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration variables."""

    # Core Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-should-be-changed"
    RECRUITER_ACCESS_CODE = os.environ.get("RECRUITER_ACCESS_CODE") or "default-code"

    # LLM Provider Configuration
    # Determines which LLM service to use ('anthropic', 'openai', 'gemini')
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    # API Keys for different LLM providers
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    # LLM Model Name Configuration
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-haiku-20240307")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
