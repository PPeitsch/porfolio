import json

import jwt
import pytest


# The 'client' and 'app' fixtures are provided by conftest.py
def test_verify_access_code_success(client, app):
    """
    Test that a valid access code returns a 200 status and a valid JWT.
    """
    # Arrange
    access_code = app.config["RECRUITER_ACCESS_CODE"]
    payload = {"code": access_code}

    # Act
    response = client.post(
        "/auth/verify", data=json.dumps(payload), content_type="application/json"
    )
    response_data = response.get_json()

    # Assert
    assert response.status_code == 200
    assert "token" in response_data

    # Verify the token is a valid JWT
    try:
        token = response_data["token"]
        decoded_payload = jwt.decode(
            token, app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        assert decoded_payload["sub"] == "recruiter_access"
    except jwt.PyJWTError as e:
        pytest.fail(f"JWT validation failed: {e}")


def test_verify_access_code_invalid_code(client):
    """
    Test that an invalid access code returns a 401 Unauthorized status.
    """
    # Arrange
    payload = {"code": "this-is-a-wrong-code"}

    # Act
    response = client.post(
        "/auth/verify", data=json.dumps(payload), content_type="application/json"
    )
    response_data = response.get_json()

    # Assert
    assert response.status_code == 401
    assert "error" in response_data
    assert response_data["error"] == "Invalid access code."


def test_verify_access_code_missing_code(client):
    """
    Test that a request with a missing 'code' key returns a 400 Bad Request.
    """
    # Arrange
    payload = {"not_a_code": "some_value"}

    # Act
    response = client.post(
        "/auth/verify", data=json.dumps(payload), content_type="application/json"
    )
    response_data = response.get_json()

    # Assert
    assert response.status_code == 400
    assert "error" in response_data
    assert response_data["error"] == "Access code is required."


def test_verify_access_code_no_json(client):
    """
    Test that a request without a JSON body returns a 400 Bad Request.
    """
    # Act
    response = client.post("/auth/verify", data="not json", content_type="text/plain")
    response_data = response.get_json()

    # Assert
    assert response.status_code == 400
    assert "error" in response_data
    assert response_data["error"] == "Access code is required."
