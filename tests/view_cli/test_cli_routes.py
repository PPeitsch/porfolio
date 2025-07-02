from typing import Any, Dict, List, Tuple
from unittest.mock import MagicMock, patch

import pytest
from flask.testing import FlaskClient

from tests.helpers import generate_test_token

MOCK_CV_DATA_CLI: Dict[str, Any] = {
    "name": "Test User",
    "title": "Test Pro",
    "skills": ["pytest", "mocking"],
    "email": "test@example.com",
    "social_links": {"github": "http://github.com/test"},
    "website": "example.com",
}
MOCK_PROJECTS_DATA_CLI: List[Dict[str, Any]] = [
    {"id": "p1", "title": "Project 1", "description": "First one"},
    {"id": "p2", "title": "Project 2", "live_url": "http://live.url"},
    {
        "id": "p3",
        "title": "Project 3",
        "technologies": ["pytest"],
        "pypi_url": "http://pypi.org/p3",
        "docs_url": "http://docs.p3.com",
    },
]
MOCK_PROJECTS_DICT_CLI: Dict[str, Any] = {p["id"]: p for p in MOCK_PROJECTS_DATA_CLI}


def test_cli_command_unauthorized(client: FlaskClient) -> None:
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
        ("show p3", "http://pypi.org/p3"),
        ("neofetch", "Projects: 3"),
        ("uname -a", "FlaskOS"),
        ("filter --tech pytest", "p3"),
        ("man show", "SYNOPSIS"),
        ("open p2", "Attempting to open"),
    ],
)
@patch("app.view_cli.routes.get_cached_data")
def test_cli_all_commands_success(
    mock_get_cached_data: MagicMock,
    client: FlaskClient,
    app: Any,
    command: str,
    expected_output: str,
) -> None:
    """Test a wide range of CLI commands with successful data loading."""
    mock_get_cached_data.side_effect = [
        MOCK_CV_DATA_CLI,
        (MOCK_PROJECTS_DATA_CLI, MOCK_PROJECTS_DICT_CLI),
    ] * 20
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get(f"/cli/api/command/{command}", headers=headers)
    response_data = response.get_json()

    assert response.status_code == 200
    assert "output" in response_data
    assert any(expected_output in line for line in response_data["output"])


@patch("app.view_cli.routes.get_cached_data")
def test_cli_commands_with_empty_data(
    mock_get_cached_data: MagicMock, client: FlaskClient, app: Any
) -> None:
    """Test commands' behavior with empty or missing data fields."""
    empty_cv: Dict[str, Any] = {"name": "No Name", "skills": []}
    empty_projects: Tuple[List[Any], Dict[Any, Any]] = ([], {})
    mock_get_cached_data.side_effect = [
        empty_cv,
        empty_projects,
        empty_cv,
        empty_projects,
        empty_cv,
        empty_cv,
    ]
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    # Test 'ls projects' with no projects
    response_ls = client.get("/cli/api/command/ls projects", headers=headers)
    response_ls_data = response_ls.get_json()
    assert isinstance(response_ls_data, dict)
    assert "(Project data could not be loaded)" in response_ls_data["output"][1]

    # Test 'show' for a project that doesn't exist in an empty list
    response_show = client.get("/cli/api/command/show p1", headers=headers)
    response_show_data = response_show.get_json()
    assert isinstance(response_show_data, dict)
    assert "not found" in response_show_data["error"]

    # Test 'contact' with no links
    response_contact = client.get("/cli/api/command/contact", headers=headers)
    response_contact_data = response_contact.get_json()
    assert isinstance(response_contact_data, dict)
    assert "(No contact details available)" in response_contact_data["output"][1]

    # Test 'skills' with no skills
    response_skills = client.get("/cli/api/command/skills", headers=headers)
    response_skills_data = response_skills.get_json()
    assert isinstance(response_skills_data, dict)
    assert "(Skills data unavailable)" in response_skills_data["output"][1]


@patch("app.view_cli.routes.COMMAND_HANDLERS")
def test_cli_internal_server_error(
    mock_handlers: MagicMock, client: FlaskClient, app: Any
) -> None:
    """Test the generic exception handler in the CLI API route."""
    mock_handler = MagicMock(side_effect=TypeError("Forced test error"))
    mock_handlers.get.return_value = mock_handler
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.get("/cli/api/command/any_command", headers=headers)
    response_data = response.get_json()

    assert response.status_code == 200
    assert "Internal server error" in response_data["error"]


@patch("app.view_cli.routes.get_cached_data", return_value=(None, None))
def test_cli_data_loading_failure(
    mock_get_cached_data: MagicMock, client: FlaskClient, app: Any
) -> None:
    """Test API response when backend data fails to load."""
    token = generate_test_token(app)
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/cli/api/command/whoami", headers=headers)
    assert response.status_code == 500
    assert "Failed to load backend data" in response.get_json()["error"]
