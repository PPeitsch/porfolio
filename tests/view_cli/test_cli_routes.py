import datetime

import jwt

MOCK_CV_DATA_CLI = {"name": "Test User", "title": "Test Pro"}
MOCK_PROJECTS_DATA_CLI = [{"id": "p1", "title": "Project 1"}]


def generate_test_token(app):
    """Helper function to generate a valid JWT for tests."""
    payload = {
        "sub": "test_access",
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(minutes=5),
    }
    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")


# The 'client' and 'app' fixtures are provided by conftest.py
def test_cli_command_unauthorized(client):
    """Test that accessing the CLI command endpoint without a token fails."""
    response = client.get("/cli/api/command/whoami")
    assert response.status_code == 401


def test_cli_command_whoami(client, app):
    """Test the 'whoami' command."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    # Patch the data loaders for this specific test
    with patch(
        "view_cli.routes.get_cached_data", return_value=MOCK_CV_DATA_CLI
    ) as mock_data:
        response = client.get("/cli/api/command/whoami", headers=headers)
        response_data = response.get_json()

        assert response.status_code == 200
        assert "output" in response_data
        assert "Name:    Test User" in response_data["output"]


def test_cli_command_ls_projects(client, app):
    """Test the 'ls projects' command."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    with patch(
        "view_cli.routes.get_cached_data",
        return_value=(MOCK_PROJECTS_DATA_CLI, {"p1": MOCK_PROJECTS_DATA_CLI[0]}),
    ) as mock_data:
        response = client.get("/cli/api/command/ls projects", headers=headers)
        response_data = response.get_json()

        assert response.status_code == 200
        assert any("p1" in line for line in response_data["output"])


def test_cli_command_unknown(client, app):
    """Test an unknown command returns an error."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    with patch("view_cli.routes.get_cached_data", return_value=({}, {})) as mock_data:
        response = client.get("/cli/api/command/foo bar", headers=headers)
        response_data = response.get_json()

        assert response.status_code == 200  # Endpoint itself doesn't fail
        assert "error" in response_data
        assert "Command not found" in response_data["error"]
