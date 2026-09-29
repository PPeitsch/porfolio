import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration variables."""

    # Core Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-should-be-changed"
    RECRUITER_ACCESS_CODE = os.environ.get("RECRUITER_ACCESS_CODE") or "default-code"

    # UI Feature Flags
    BANNER_ENABLED = os.environ.get("BANNER_ENABLED", "false").lower() in (
        "true",
        "1",
        "t",
    )
    BANNER_MESSAGE = os.environ.get(
        "BANNER_MESSAGE",
        (
            "Please note: This site is under active configuration. "
            "Final updates are planned by July 21st."
        ),
    )

    # LLM Provider Configuration
    # Determines which LLM service to use ('anthropic', 'openai', 'gemini')
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    # API Keys for different LLM providers
    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

    # Optional HTTP proxy for Gemini (e.g. a Cloud Run service that holds the
    # key). When set, Gemini requests go through it instead of the genai client.
    GEMINI_PROXY_URL = os.environ.get("GEMINI_PROXY_URL")

    # LLM Model Name Configuration
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-3.5-turbo")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
