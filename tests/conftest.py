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
            "SECRET_KEY": "test-secret-key",
        }
    )

    # Add a dummy protected route for testing the decorator
    @app.route("/protected")
    @token_required
    def protected_route():
        return jsonify(message="access granted")

    yield app


@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()
