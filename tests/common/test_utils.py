from unittest.mock import patch

import yaml

from app.common.utils import (
    get_professional_summary,
    get_project_details,
    get_project_list,
    get_skills,
    load_cv_data,
    load_projects_data,
    load_yaml_data,
)

# --- Tests for load_yaml_data ---


@patch("builtins.open")
@patch("yaml.safe_load")
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_success(mock_get_path, mock_safe_load, mock_open):
    """Test successful loading and parsing of a YAML file."""
    # Arrange
    mock_safe_load.return_value = {"key": "value"}
    # Act
    data = load_yaml_data("dummy_path.yaml")
    # Assert
    assert data == {"key": "value"}
    mock_open.assert_called_once()
    mock_safe_load.assert_called_once()


@patch("builtins.open", side_effect=FileNotFoundError)
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_file_not_found(mock_get_path, mock_open):
    """Test handling of FileNotFoundError."""
    # Act
    data = load_yaml_data("non_existent.yaml")
    # Assert
    assert data == {}


@patch("builtins.open")
@patch("yaml.safe_load", side_effect=yaml.YAMLError)
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_yaml_error(mock_get_path, mock_safe_load, mock_open):
    """Test handling of YAML parsing errors."""
    # Act
    data = load_yaml_data("malformed.yaml")
    # Assert
    assert data == {}


# --- Tests for Data Access Functions (get_*) ---


# Sample data to be returned by mocked loaders
MOCK_CV_DATA = {
    "name": "Test User",
    "title": "Test Title",
    "summary": "A test summary.",
    "skills": ["Python", "Flask"],
    "social_links": {"github": "test-url"},
}

MOCK_PROJECTS_DATA = [
    {"id": "proj1", "title": "Project One", "description": "First project."},
    {"id": "proj2", "title": "Project Two", "short_description": "Second project."},
]


@patch("app.common.utils.load_cv_data", return_value=MOCK_CV_DATA)
def test_get_professional_summary(mock_load_cv):
    """Test that get_professional_summary returns the correct summary."""
    summary = get_professional_summary()
    assert summary == "A test summary."


@patch("app.common.utils.load_cv_data", return_value=MOCK_CV_DATA)
def test_get_skills(mock_load_cv):
    """Test that get_skills returns the list of skills."""
    skills = get_skills()
    assert skills == ["Python", "Flask"]


@patch("app.common.utils.load_projects_data", return_value=(MOCK_PROJECTS_DATA, {}))
def test_get_project_list(mock_load_projects):
    """Test that get_project_list returns a correctly formatted list."""
    project_list = get_project_list()
    assert len(project_list) == 2
    assert project_list[0]["id"] == "proj1"
    assert project_list[0]["title"] == "Project One"
    assert project_list[1]["short_description"] == "Second project."


@patch("app.common.utils.load_projects_data")
def test_get_project_details_found(mock_load_projects):
    """Test finding an existing project's details."""
    # Arrange
    projects_dict = {p["id"]: p for p in MOCK_PROJECTS_DATA}
    mock_load_projects.return_value = (MOCK_PROJECTS_DATA, projects_dict)
    # Act
    details = get_project_details("proj1")
    # Assert
    assert details is not None
    assert details["title"] == "Project One"


@patch("app.common.utils.load_projects_data")
def test_get_project_details_not_found(mock_load_projects):
    """Test returning None for a non-existent project."""
    # Arrange
    projects_dict = {p["id"]: p for p in MOCK_PROJECTS_DATA}
    mock_load_projects.return_value = (MOCK_PROJECTS_DATA, projects_dict)
    # Act
    details = get_project_details("nonexistent")
    # Assert
    assert details is None


# --- Tests for Context-Caching Functions (load_*) ---


@patch("app.common.utils.load_yaml_data")
def test_load_cv_data_caching(mock_load_yaml, app):
    """Test that CV data is loaded once and then cached in 'g'."""
    # Arrange: Mock the return value of the YAML loader
    mock_load_yaml.return_value = MOCK_CV_DATA

    with app.app_context():
        # Act: Call the function twice
        data1 = load_cv_data()
        data2 = load_cv_data()

    # Assert: Check the final merged data and call count
    assert data1 == MOCK_CV_DATA
    assert data2 == MOCK_CV_DATA
    mock_load_yaml.assert_called_once()


@patch("app.common.utils.load_yaml_data")
def test_load_projects_data_caching(mock_load_yaml, app):
    """Test that projects data is loaded once and cached in 'g'."""
    # Arrange
    mock_load_yaml.return_value = MOCK_PROJECTS_DATA
    with app.app_context():
        # Act
        list1, dict1 = load_projects_data()
        list2, dict2 = load_projects_data()

    # Assert
    assert list1 == MOCK_PROJECTS_DATA
    assert len(dict1) == 2
    assert dict1["proj1"]["title"] == "Project One"
    mock_load_yaml.assert_called_once()
