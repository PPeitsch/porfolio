from unittest.mock import MagicMock, patch

import pytest
import yaml

from common.utils import (
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
def test_load_yaml_data_success(mock_safe_load, mock_open):
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
def test_load_yaml_data_file_not_found(mock_open):
    """Test handling of FileNotFoundError."""
    # Act
    data = load_yaml_data("non_existent.yaml")
    # Assert
    assert data == {}


@patch("builtins.open")
@patch("yaml.safe_load", side_effect=yaml.YAMLError)
def test_load_yaml_data_yaml_error(mock_safe_load, mock_open):
    """Test handling of YAML parsing errors."""
    # Act
    data = load_yaml_data("malformed.yaml")
    # Assert
    assert data == {}


# --- Tests for Data Access Functions (get_*) ---


@pytest.fixture
def mock_app_context():
    """Fixture to mock the Flask application context (g)."""
    app = MagicMock()
    app.app_context.return_value.__enter__.return_value = True
    app.app_context.return_value.__exit__.return_value = None
    with patch("common.utils.g", new_callable=MagicMock) as mock_g:
        yield mock_g


# Sample data to be returned by mocked loaders
MOCK_CV_DATA = {
    "name": "Test User",
    "summary": "A test summary.",
    "skills": ["Python", "Flask"],
}

MOCK_PROJECTS_DATA = [
    {"id": "proj1", "title": "Project One", "description": "First project."},
    {"id": "proj2", "title": "Project Two", "short_description": "Second project."},
]


@patch("common.utils.load_cv_data", return_value=MOCK_CV_DATA)
def test_get_professional_summary(mock_load_cv):
    """Test that get_professional_summary returns the correct summary."""
    summary = get_professional_summary()
    assert summary == "A test summary."


@patch("common.utils.load_cv_data", return_value=MOCK_CV_DATA)
def test_get_skills(mock_load_cv):
    """Test that get_skills returns the list of skills."""
    skills = get_skills()
    assert skills == ["Python", "Flask"]


@patch("common.utils.load_projects_data", return_value=(MOCK_PROJECTS_DATA, {}))
def test_get_project_list(mock_load_projects):
    """Test that get_project_list returns a correctly formatted list."""
    project_list = get_project_list()
    assert len(project_list) == 2
    assert project_list[0]["id"] == "proj1"
    assert project_list[0]["title"] == "Project One"
    assert project_list[1]["short_description"] == "Second project."


@patch("common.utils.load_projects_data")
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


@patch("common.utils.load_projects_data")
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


def test_load_cv_data_caching(mock_app_context):
    """Test that CV data is loaded once and then cached in 'g'."""
    # Arrange
    mock_app_context.cv_data = None
    with patch("common.utils.load_yaml_data", return_value=MOCK_CV_DATA) as mock_load:
        # First call: should load data
        load_cv_data()
        # Second call: should use cache
        load_cv_data()
    # Assert
    assert mock_load.call_count == 1


def test_load_projects_data_caching(mock_app_context):
    """Test that projects data is loaded once and then cached in 'g'."""
    # Arrange
    mock_app_context.projects_data = None
    with patch(
        "common.utils.load_yaml_data", return_value=MOCK_PROJECTS_DATA
    ) as mock_load:
        # First call
        load_projects_data()
        # Second call
        load_projects_data()
    # Assert
    assert mock_load.call_count == 1
