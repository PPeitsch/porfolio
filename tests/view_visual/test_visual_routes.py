from unittest.mock import patch

MOCK_PROJECTS = [
    {
        "id": "proj1",
        "title": "Project One",
        "image": "proj1.png",
        "description": (
            "This is a full description that is definitely longer than one "
            "hundred characters to properly test the truncation logic we have "
            "in place."
        ),
        "type": "webapp",
        "technologies": ["Python", "Flask", "Docker", "Pytest", "React"],
        "live_url": "http://example.com/live",
        "github_url": "http://github.com/proj1",
    },
    {
        "id": "proj2",
        "title": "Project Two",
        "image": None,
        "short_description": "Short desc.",
        "description": "",
        "type": "library",
        "technologies": [],
        "pypi_url": "http://pypi.org/p2",
        "docs_url": "http://docs.p2.com",
    },
]


@patch("app.view_visual.routes.load_projects_data", return_value=(MOCK_PROJECTS, {}))
def test_get_projects_for_visual_success(mock_load_projects, client):
    """
    Test that the /visual/api/projects endpoint returns correctly
    formatted and simplified project data.
    """
    response = client.get("/visual/api/projects")
    response_data = response.get_json()

    assert response.status_code == 200
    assert isinstance(response_data, list)
    assert len(response_data) == 2

    # Test first project with full data
    project1 = response_data[0]
    expected_keys = [
        "id",
        "title",
        "image_url",
        "short_desc",
        "live_url",
        "github_url",
        "pypi_url",
        "docs_url",
        "type",
        "type_label",
        "technologies",
    ]
    for key in expected_keys:
        assert key in project1

    assert project1["id"] == "proj1"
    assert project1["title"] == "Project One"
    assert project1["image_url"] == "/shell-static/images/projects/proj1.png"
    # Whole description and every technology: the card does the cutting.
    assert project1["short_desc"] == MOCK_PROJECTS[0]["description"]
    assert len(project1["technologies"]) == 5
    assert project1["type_label"] == "Web app"

    # Test second project with missing/alternative data
    project2 = response_data[1]
    assert project2["image_url"] is None
    assert project2["short_desc"] == "Short desc."
    assert project2["type_label"] == "Library"


@patch("app.view_visual.routes.load_projects_data", return_value=(None, None))
def test_get_projects_for_visual_load_failure(mock_load_projects, client):
    """
    Test the endpoint's failure case when project data cannot be loaded.
    """
    response = client.get("/visual/api/projects")
    response_data = response.get_json()

    assert response.status_code == 500
    assert "error" in response_data


@patch("app.view_visual.routes.send_from_directory")
def test_visual_static_file_not_found(mock_send, client):
    """
    Test the except block for the static file route by simulating a
    FileNotFoundError from send_from_directory.
    """
    # Configure the mock to raise the specific error we want to catch
    mock_send.side_effect = FileNotFoundError

    # Make a request to any file; the mock will ensure the error is raised
    response = client.get("/visual/static/anyfile.css")

    # The abort(404) will be triggered by our exception handler
    assert response.status_code == 404


@patch(
    "app.view_visual.routes.load_projects_data",
    return_value=([{"id": "x", "title": "X", "type": "spaceship"}], {}),
)
def test_unknown_project_type_has_no_label(mock_load_projects, client):
    """A type without a text gets an empty label instead of the raw key."""
    project = client.get("/visual/api/projects").get_json()[0]
    assert project["type"] == "spaceship"
    assert project["type_label"] == ""
