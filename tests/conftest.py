import pytest
from flask import jsonify

from app.common.decorators import token_required
from app.shell import create_app


@pytest.fixture(scope="module")
def app():
    """Create and configure a new app instance for each test module."""
    app = create_app("testing")
    app.config.update(
        {
            "TESTING": True,
            # Add any other test-specific configurations here
            # For example, a test database or dummy API keys
            "RECRUITER_ACCESS_CODE": "test-code",
            "SECRET_KEY": "test-secret-key-at-least-32-bytes-long",
            # Tests must not depend on the developer's .env
            "GEMINI_PROXY_URL": None,
            # No usage log unless a test asks for one (tests/common/test_llm_usage.py)
            "LLM_USAGE_DIR": "",
        }
    )

    # Add a dummy protected route for testing the decorator
    @app.route("/protected")
    @token_required
    def protected_route():
        return jsonify(message="access granted")

    yield app


@pytest.fixture(autouse=True)
def fresh_rate_limits(request):
    """Starts every test with empty rate-limit counters."""
    if "app" in request.fixturenames:
        request.getfixturevalue("app").extensions.pop("rate_limiters", None)


@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()
