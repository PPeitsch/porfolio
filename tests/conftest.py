import pytest

from shell import create_app


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
    yield app


@pytest.fixture()
def client(app):
    """A test client for the app."""
    return app.test_client()
