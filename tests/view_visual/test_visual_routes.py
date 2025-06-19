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
    }
]


# The 'client' and 'app' fixtures are provided by conftest.py
@patch("view_visual.routes.load_projects_data", return_value=(MOCK_PROJECTS, {}))
def test_get_projects_for_visual_success(mock_load_projects, client):
    """
    Test that the /visual/api/projects endpoint returns correctly
    formatted and simplified project data.
    """
    # Act
    response = client.get("/visual/api/projects")
    response_data = response.get_json()

    # Assert
    assert response.status_code == 200
    assert isinstance(response_data, list)
    assert len(response_data) == 1

    project = response_data[0]
    # Check that keys are correct for the visual view
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
        "technologies",
    ]
    for key in expected_keys:
        assert key in project

    # Check data transformation
    assert project["id"] == "proj1"
    assert project["title"] == "Project One"
    assert project["image_url"] == "/shell-static/images/projects/proj1.png"
    assert project["short_desc"].endswith("...")
    assert len(project["short_desc"]) <= 103  # 100 chars + "..."
    assert len(project["technologies"]) == 4  # Should be truncated to 4


@patch("view_visual.routes.load_projects_data", return_value=(None, None))
def test_get_projects_for_visual_failure(mock_load_projects, client):
    """
    Test the endpoint's failure case when project data cannot be loaded.
    """
    # Act
    response = client.get("/visual/api/projects")
    response_data = response.get_json()

    # Assert
    assert response.status_code == 500
    assert "error" in response_data
