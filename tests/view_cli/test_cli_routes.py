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
        ("filter --tech python", "No projects found"),
        ("man show", "SYNOPSIS"),
        ("open p2", "Attempting to open"),
    ],
)
@patch("app.view_cli.routes.get_cached_data")
def test_cli_all_commands(mock_get_cached_data, client, app, command, expected_output):
    """Test a wide range of CLI commands using parameterization."""
    mock_get_cached_data.side_effect = [
        MOCK_CV_DATA_CLI,
        (MOCK_PROJECTS_DATA_CLI, MOCK_PROJECTS_DICT_CLI),
    ] * 10
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/cli/api/command/{command}", headers=headers)
    response_data = response.get_json()

    assert response.status_code == 200
    assert "output" in response_data
    assert any(expected_output in line for line in response_data["output"])
    assert "prompt" in response_data


@pytest.mark.parametrize(
    "command, expected_error",
    [
        ("foo bar", "Command not found"),
        ("show", "Usage: show <project_id>"),
        ("show nonexistent", "not found"),
        ("ls", "Unknown argument for 'ls'"),
        ("filter", "Usage: filter --tech"),
        ("open", "Usage: open <project_id>"),
        ("open nonexistent", "not found"),
        ("man", "Usage: man <command>"),
        ("man nonexistent", "No manual entry"),
    ],
)
@patch("app.view_cli.routes.get_cached_data")
def test_cli_command_errors(mock_get_cached_data, client, app, command, expected_error):
    """Test various command error conditions."""
    # Use side_effect to return correct data for each call to get_cached_data
    mock_get_cached_data.side_effect = [
        MOCK_CV_DATA_CLI,
        (MOCK_PROJECTS_DATA_CLI, MOCK_PROJECTS_DICT_CLI),
    ]
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get(f"/cli/api/command/{command}", headers=headers)
    response_data = response.get_json()

    assert response.status_code == 200
    assert "error" in response_data
    assert expected_error in response_data["error"]


@patch("app.view_cli.routes.get_cached_data")
def test_cli_neofetch_missing_logo(mock_get_cached_data, client, app):
    """Test neofetch command when the logo file is not found."""
    mock_get_cached_data.side_effect = [
        MOCK_CV_DATA_CLI,
        (MOCK_PROJECTS_DATA_CLI, MOCK_PROJECTS_DICT_CLI),
    ]
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    with patch("app.view_cli.routes._get_data_filepath", side_effect=FileNotFoundError):
        response = client.get("/cli/api/command/neofetch", headers=headers)
        response_data = response.get_json()

    assert response.status_code == 200
    assert any("(Logo not found)" in line for line in response_data["output"])


@patch("app.view_cli.routes.get_cached_data")
def test_cli_command_show_project_not_found(mock_get_cached_data, client, app):
    """Test 'show' for a project that does not exist."""
    mock_get_cached_data.side_effect = [
        MOCK_CV_DATA_CLI,
        (MOCK_PROJECTS_DATA_CLI, MOCK_PROJECTS_DICT_CLI),
    ]
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/cli/api/command/show nonexistent", headers=headers)
    response_data = response.get_json()

    assert response.status_code == 200
    assert "error" in response_data
    assert "not found" in response_data["error"]


@patch("app.view_cli.routes.get_cached_data", return_value=(None, None))
def test_cli_data_loading_failure(mock_get_cached_data, client, app):
    """Test API response when backend data fails to load."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/cli/api/command/whoami", headers=headers)
    assert response.status_code == 500
    assert "Failed to load backend data" in response.get_json()["error"]
