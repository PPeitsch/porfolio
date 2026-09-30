import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration variables."""

    # Core Flask settings
    SECRET_KEY = os.environ.get("SECRET_KEY") or "dev-secret-key-should-be-changed"
    RECRUITER_ACCESS_CODE = os.environ.get("RECRUITER_ACCESS_CODE") or "default-code"

    # Portfolio content (CV, projects, prompt, texts, project images).
    # A relative PORTFOLIO_DATA_DIR is resolved from the project root.
    DATA_DIR = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        os.environ.get("PORTFOLIO_DATA_DIR", "data"),
    )

    # Languages the site is offered in, the first being the fallback. Texts in
    # the data files can give one translation per language; see README.
    LANGUAGES = [
        code.strip().lower()
        for code in os.environ.get("PORTFOLIO_LANGUAGES", "en,es").split(",")
        if code.strip()
    ] or ["en"]
    # Used when the browser asks for none of LANGUAGES.
    DEFAULT_LANGUAGE = os.environ.get("PORTFOLIO_DEFAULT_LANGUAGE", LANGUAGES[0])

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

    # LLM configuration (LiteLLM). LLM_MODEL picks provider and model, e.g.
    # "anthropic/claude-haiku-4-5-20251001", "openrouter/anthropic/claude-haiku-4.5",
    # "gemini/gemini-2.5-flash", "openai/gpt-4.1-mini" or "ollama/llama3.1".
    # The provider's key is read from its usual variable (ANTHROPIC_API_KEY,
    # OPENROUTER_API_KEY, GEMINI_API_KEY, OPENAI_API_KEY...) unless LLM_API_KEY
    # is set. LLM_API_BASE points at a custom endpoint (e.g. a local Ollama).
    LLM_MODEL = os.environ.get("LLM_MODEL")
    LLM_API_KEY = os.environ.get("LLM_API_KEY")
    LLM_API_BASE = os.environ.get("LLM_API_BASE")
    LLM_TIMEOUT = float(os.environ.get("LLM_TIMEOUT", "30"))
    # How many rounds of tool calls the chat allows before giving up on a question.
    LLM_MAX_TOOL_ROUNDS = int(os.environ.get("LLM_MAX_TOOL_ROUNDS", "5"))

    # Older settings, used only when LLM_MODEL is not set: the model becomes
    # "<LLM_PROVIDER>/<provider>_MODEL".
    LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4.1-mini")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    # No longer supported (Gemini goes through LiteLLM); read only to warn.
    GEMINI_PROXY_URL = os.environ.get("GEMINI_PROXY_URL")
