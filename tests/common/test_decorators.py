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
def test_token_required_other_decode_error(mock_decode, client, app):
    """Any PyJWT decoding error is reported as an invalid token."""
    mock_decode.side_effect = jwt.InvalidAudienceError("Wrong audience")
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/protected", headers=headers)
    assert response.status_code == 401
    assert response.get_json()["error"] == "Invalid token."


def test_token_required_no_secret_key(app):
    """Test protected route when server has no SECRET_KEY configured."""
    # Generate a token with a temporary key, as the app's key will be removed
    temp_key = app.config["SECRET_KEY"]
    payload = {
        "sub": "test_access",
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=15),
    }
    token = jwt.encode(payload, temp_key, algorithm="HS256")

    # Set the app's key to None to simulate the configuration error
    app.config["SECRET_KEY"] = None

    # Create a test client from this specific app state
    with app.test_client() as client:
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/protected", headers=headers)

    # Restore the key to not affect other tests
    app.config["SECRET_KEY"] = temp_key

    assert response.status_code == 500
    assert "Server configuration error" in response.get_json()["error"]
