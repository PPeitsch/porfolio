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
    "experience": [
        {
            "role": "Backend Dev",
            "company": "Acme",
            "period": "2023 - Present",
            "description": "Builds APIs.",
        },
        "not a mapping",
        {"company": "NoRole Inc"},
    ],
    "education": [{"degree": "BSc", "institution": "Uni", "period": "2017 - 2021"}],
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
        ("experience", "Backend Dev @ Acme (2023 - Present)"),
        ("experience", "    Builds APIs."),
        ("experience", "  NoRole Inc"),
        ("education", "BSc @ Uni (2017 - 2021)"),
        ("man experience", "DESCRIPTION"),
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
    # Provide enough side effects for all calls within this test function
    mock_get_cached_data.side_effect = [
        empty_cv,
        empty_projects,
        empty_cv,
        empty_projects,
        empty_cv,
        empty_projects,
        empty_cv,
        empty_projects,
        empty_cv,
        empty_projects,
        empty_cv,
        empty_projects,
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

    # Test 'experience' and 'education' with nothing in the CV
    for command in ("experience", "education"):
        response_cv = client.get(f"/cli/api/command/{command}", headers=headers)
        response_cv_data = response_cv.get_json()
        assert isinstance(response_cv_data, dict)
        assert f"(No {command} listed)" in response_cv_data["output"][1]

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
    # Force an exception inside a mocked handler
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


def test_format_project_table_with_numeric_ids() -> None:
    """IDs that YAML loads as numbers are still formatted as text."""
    from app.view_cli.routes import _format_project_table

    # The stray string checks that non-mapping entries are skipped.
    projects: List[Any] = [
        {"id": 2024, "title": "Numeric"},
        {"title": "No ID"},
        "not a project",
    ]
    table = _format_project_table(projects)
    assert table[0].startswith("  ID  ")
    assert "  2024  | Numeric" in table
    assert "  N/A   | No ID" in table
    assert len(table) == 4


def _neofetch(app: Any, args: List[str], logo: Any = None) -> Tuple[Any, Any]:
    """Runs the neofetch handler with an optional configured logo."""
    from app.view_cli.routes import _handle_neofetch

    neofetch_config = {} if logo is None else {"logo": logo}
    with app.test_request_context():
        return _handle_neofetch(
            args=args,
            cv_data=MOCK_CV_DATA_CLI,
            projects_data=MOCK_PROJECTS_DATA_CLI,
            text_config={"cli": {"neofetch": neofetch_config}},
        )


def test_neofetch_uses_configured_logo(app: Any) -> None:
    """cli.neofetch.logo picks the logo; without it, flask is used."""
    owl, _ = _neofetch(app, [], logo="owl")
    default, _ = _neofetch(app, [])
    assert any("o o" in line for line in owl)
    assert any("| o |" in line for line in default)


@pytest.mark.parametrize("logo", ["missing", "../cv", "Owl"])
def test_neofetch_falls_back_to_default_logo(app: Any, logo: str) -> None:
    """A configured logo that is missing or not a plain name falls back to flask."""
    output, error = _neofetch(app, [], logo=logo)
    assert error is None
    assert any("| o |" in line for line in output)


def test_neofetch_logo_option(app: Any) -> None:
    """--logo shows another logo; an unknown one lists the available logos."""
    output, error = _neofetch(app, ["--logo", "owl"])
    assert error is None
    assert any("o o" in line for line in output)

    _, error = _neofetch(app, ["--logo", "../cv"])
    assert "not found" in error
    assert "owl" in error and "flask" in error


@pytest.mark.parametrize("args", [["--logo"], ["--color", "red"], ["owl"]])
def test_neofetch_bad_arguments(app: Any, args: List[str]) -> None:
    """Anything other than '--logo <name>' answers with the usage."""
    output, error = _neofetch(app, args)
    assert output is None
    assert "Usage: neofetch" in error


def test_available_logos_without_folder(app: Any) -> None:
    """Without a logo/ folder there are no logos to list."""
    from app.view_cli.routes import _available_logos

    with app.test_request_context(), patch(
        "app.view_cli.routes.os.listdir", side_effect=FileNotFoundError
    ):
        assert _available_logos() == []


def test_help_aligns_descriptions(app: Any) -> None:
    """Within a group, every description starts in the same column."""
    from app.view_cli.routes import _handle_help

    items = [
        {"command": "ls", "description": "short", "group": "portfolio"},
        {
            "command": "filter --tech <name>",
            "description": "long",
            "group": "portfolio",
        },
    ]
    output, _ = _handle_help(text_config={"cli": {"commands": {"items": items}}})
    columns = {line.index(" - ") for line in output[1:3]}
    assert len(columns) == 1
