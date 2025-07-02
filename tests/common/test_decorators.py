import datetime
from unittest.mock import patch

import jwt

from tests.helpers import generate_test_token


def test_token_required_success(client, app):
    """Test accessing a protected route with a valid token."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 200
    assert response.get_json()["message"] == "access granted"


def test_token_required_no_header(client):
    """Test protected route without Authorization header."""
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.get_json()["error"] == "Authorization token is missing."


def test_token_required_malformed_header(client):
    """Test protected route with a malformed 'Bearer' header."""
    headers = {"Authorization": "BearerTokenWithoutSpace"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert response.get_json()["error"] == "Malformed Authorization header."


def test_token_required_invalid_token(client):
    """Test protected route with an invalid token."""
    headers = {"Authorization": "Bearer an-invalid-token"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token."


def test_token_required_expired_token(client, app):
    """Test protected route with an expired token."""
    payload = {
        "sub": "test_access",
        "iat": datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(minutes=10),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        - datetime.timedelta(minutes=5),
    }
    expired_token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
    headers = {"Authorization": f"Bearer {expired_token}"}

    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert response.get_json()["error"] == "Token has expired."


@patch("app.common.decorators.jwt.decode")
def test_token_required_generic_decode_error(mock_decode, client, app):
    """Test protected route with a generic token decoding error."""
    mock_decode.side_effect = Exception("A generic decoding error")
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert "Token processing error" in response.get_json()["error"]


@patch("app.common.decorators.current_app")
def test_token_required_no_secret_key(mock_current_app, client, app):
    """Test protected route when server has no SECRET_KEY configured."""
    # Simulate the config having no secret key when the decorator accesses it
    mock_current_app.config.get.return_value = None
    token = generate_test_token(app)  # Generate token with the real app
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/protected", headers=headers)

    assert response.status_code == 500
    assert "Server configuration error" in response.get_json()["error"]
