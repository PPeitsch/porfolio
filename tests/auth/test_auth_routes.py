import json
from unittest.mock import patch

import jwt
import pytest


def test_verify_access_code_success(client, app):
    """
    Test that a valid access code returns a 200 status and a valid JWT.
    """
    access_code = app.config["RECRUITER_ACCESS_CODE"]
    payload = {"code": access_code}

    response = client.post(
        "/auth/verify", data=json.dumps(payload), content_type="application/json"
    )
    response_data = response.get_json()

    assert response.status_code == 200
    assert "token" in response_data
    assert "prompt" in response_data

    # This try-except block is for test validation, not part of the SUT
    try:
        token = response_data["token"]
        decoded_payload = jwt.decode(
            token, app.config["SECRET_KEY"], algorithms=["HS256"]
        )
        assert decoded_payload["sub"] == "recruiter_access"
    except jwt.PyJWTError as e:
        pytest.fail(f"JWT validation failed: {e}")


def test_verify_access_code_success_invalid_token(client, app):
    """Test that the test helper itself fails on an invalid token."""
    with pytest.raises(jwt.PyJWTError):
        jwt.decode("an-invalid-token", app.config["SECRET_KEY"], algorithms=["HS256"])


def test_verify_access_code_invalid_code(client):
    """
    Test that an invalid access code returns a 401 Unauthorized status.
    """
    payload = {"code": "this-is-a-wrong-code"}

    response = client.post(
        "/auth/verify", data=json.dumps(payload), content_type="application/json"
    )
    response_data = response.get_json()

    assert response.status_code == 401
    assert "error" in response_data
    assert response_data["error"] == "Invalid access code."


def test_verify_access_code_missing_code_key(client):
    """
    Test that a request with a missing 'code' key returns a 400 Bad Request.
    """
    payload = {"not_a_code": "some_value"}

    response = client.post(
        "/auth/verify", data=json.dumps(payload), content_type="application/json"
    )
    response_data = response.get_json()

    assert response.status_code == 400
    assert "error" in response_data
    assert response_data["error"] == "Access code is required."


def test_verify_access_code_server_config_error(client, app, monkeypatch):
    """
    Test 503 error when server keys are not configured.
    """
    monkeypatch.setitem(app.config, "RECRUITER_ACCESS_CODE", None)
    payload = {"code": "any-code"}

    response = client.post(
        "/auth/verify", data=json.dumps(payload), content_type="application/json"
    )
    response_data = response.get_json()

    assert response.status_code == 503
    assert "Authentication system is not configured" in response_data["error"]


@patch("app.auth.routes.jwt.encode")
def test_verify_access_code_jwt_exception(mock_jwt_encode, client, app):
    """Test the exception handler for JWT generation errors."""
    mock_jwt_encode.side_effect = Exception("JWT generation failed")
    access_code = app.config["RECRUITER_ACCESS_CODE"]
    payload = {"code": access_code}

    response = client.post(
        "/auth/verify", data=json.dumps(payload), content_type="application/json"
    )
    response_data = response.get_json()

    assert response.status_code == 500
    assert "Could not generate access token" in response_data["error"]


def test_verify_access_code_unsupported_media_type(client):
    """
    Test that a request with an incorrect content type returns a 415 status.
    """
    response = client.post("/auth/verify", data="not json", content_type="text/plain")
    assert response.status_code == 415
