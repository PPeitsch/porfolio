from unittest.mock import patch

import pytest

from tests.helpers import generate_test_token

MOCK_CV_DATA_CLI = {
    "name": "Test User",
    "title": "Test Pro",
    "skills": ["pytest", "mocking"],
    "email": "test@example.com",
    "social_links": {"github": "http://github.com/test"},
}
MOCK_PROJECTS_DATA_CLI = [
    {"id": "p1", "title": "Project 1", "description": "First one"},
    {"id": "p2", "title": "Project 2", "live_url": "http://live.url"},
]
MOCK_PROJECTS_DICT_CLI = {p["id"]: p for p in MOCK_PROJECTS_DATA_CLI}


# The 'client' and 'app' fixtures are provided by conftest.py
def test_cli_command_unauthorized(client):
    """Test that accessing the CLI command endpoint without a token fails."""
    response = client.get("/cli/api/command/whoami")
    assert response.status_code == 401


@pytest.mark.parametrize(
    "command, expected_output",
    [
        ("whoami", "Name:    Test User"),
        ("skills", "pytest, mocking"),
        ("contact", "test@example.com"),
        ("links", "http://github.com/test"),
        ("ls projects", "p1"),
        ("show p1", "First one"),
        ("show p2", "http://live.url"),
        ("neofetch", "Projects: 2"),
        ("uname -a", "FlaskOS"),
    ],
)
@patch("app.view_cli.routes.get_cached_data")
def test_cli_all_commands(mock_get_cached_data, client, app, command, expected_output):
    """Test a wide range of CLI commands using parameterization."""
    # Arrange
    mock_get_cached_data.side_effect = [
        MOCK_CV_DATA_CLI,
        (MOCK_PROJECTS_DATA_CLI, MOCK_PROJECTS_DICT_CLI),
    ] * 5  # Ensure mock provides data for multiple internal calls
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    # Act
    response = client.get(f"/cli/api/command/{command}", headers=headers)
    response_data = response.get_json()

    # Assert
    assert response.status_code == 200
    assert "output" in response_data
    assert any(expected_output in line for line in response_data["output"])


@patch("app.view_cli.routes.get_cached_data", return_value=({}, {}))
def test_cli_command_unknown(mock_get_cached_data, client, app):
    """Test an unknown command returns an error."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/cli/api/command/foo bar", headers=headers)
    response_data = response.get_json()

    assert response.status_code == 200
    assert "error" in response_data
    assert "Command not found" in response_data["error"]


@patch(
    "app.view_cli.routes.get_cached_data",
    return_value=(MOCK_PROJECTS_DATA_CLI, MOCK_PROJECTS_DICT_CLI),
)
def test_cli_command_show_project_not_found(mock_get_cached_data, client, app):
    """Test 'show' for a project that does not exist."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/cli/api/command/show nonexistent", headers=headers)
    response_data = response.get_json()

    assert response.status_code == 200
    assert "error" in response_data
    assert "not found" in response_data["error"]
