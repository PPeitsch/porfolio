import os
from unittest.mock import mock_open, patch

import pytest
import yaml
from flask import g

from app.common.utils import (
    _get_data_filepath,
    get_professional_summary,
    get_project_details,
    get_project_list,
    get_skills,
    load_cv_data,
    load_projects_data,
    load_system_prompt,
    load_text_config,
    load_yaml_data,
)


@patch("app.common.utils.current_app", None)
def test_get_data_filepath_standalone():
    """Test filepath generation when running as a standalone script."""
    path = _get_data_filepath("test.txt")
    expected_fragment = os.path.join("data", "test.txt")
    assert expected_fragment in path


@patch("builtins.open")
@patch("yaml.safe_load")
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_success(mock_get_path, mock_safe_load, mock_open_):
    """Test successful loading and parsing of a YAML file."""
    mock_safe_load.return_value = {"key": "value"}
    data = load_yaml_data("dummy_path.yaml")
    assert data == {"key": "value"}


@patch("builtins.open", side_effect=FileNotFoundError)
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_file_not_found(mock_get_path, mock_open_):
    """Test handling of FileNotFoundError."""
    data = load_yaml_data("non_existent.yaml")
    assert data == {}


@patch("builtins.open")
@patch("yaml.safe_load", side_effect=yaml.YAMLError)
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_yaml_error(mock_get_path, mock_safe_load, mock_open_):
    """Test handling of YAML parsing errors."""
    data = load_yaml_data("malformed.yaml")
    assert data == {}


@patch("builtins.open", new_callable=mock_open, read_data="key: value")
@patch("yaml.safe_load", return_value=None)
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_empty_file(mock_get_path, mock_safe_load, mock_open_):
    """Test handling of an empty but valid YAML file."""
    data = load_yaml_data("empty.yaml")
    assert data == {}


@patch("builtins.open", side_effect=Exception("Unexpected error"))
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_generic_exception(mock_get_path, mock_open_):
    """Test handling of generic exceptions during file loading."""
    data = load_yaml_data("error.yaml")
    assert data == {}


MOCK_CV_DATA = {
    "name": "Test User",
    "summary": "A test summary.",
    "skills": ["Python", "Flask"],
}
MOCK_PROJECTS_DATA = [{"id": "proj1", "title": "Project One"}]


@patch("app.common.utils.load_yaml_data")
def test_load_cv_data_caching(mock_load_yaml, app):
    """Test that CV data is loaded once and then cached in 'g'."""
    mock_load_yaml.return_value = MOCK_CV_DATA.copy()
    with app.app_context():
        g.pop("cv_data", None)
        data1 = load_cv_data()
        data2 = load_cv_data()

    expected_data = MOCK_CV_DATA.copy()
    expected_data.setdefault("title", "Default Title")
    expected_data.setdefault("social_links", {})

    assert data1 == expected_data
    assert data2 == expected_data
    mock_load_yaml.assert_called_once()


@patch("app.common.utils.load_yaml_data")
def test_load_projects_data_caching(mock_load_yaml, app):
    """Test that projects data is loaded once and cached in 'g'."""
    mock_load_yaml.return_value = MOCK_PROJECTS_DATA
    with app.app_context():
        g.pop("projects_data", None)
        g.pop("projects_dict", None)
        list1, dict1 = load_projects_data()
        list2, dict2 = load_projects_data()
    assert list1 == MOCK_PROJECTS_DATA
    mock_load_yaml.assert_called_once()


@patch("app.common.utils.load_yaml_data")
def test_load_text_config_caching(mock_load_yaml, app):
    """Test that text config data is loaded once and cached in 'g'."""
    mock_load_yaml.return_value = {"key": "value"}
    with app.app_context():
        g.pop("text_config", None)
        data1 = load_text_config()
        data2 = load_text_config()
    assert data1 == {"key": "value"}
    mock_load_yaml.assert_called_once()


@patch("builtins.open", side_effect=FileNotFoundError)
@patch("app.common.utils._get_data_filepath")
def test_load_system_prompt_not_found(mock_get_path, mock_open_):
    """Test fallback when system_prompt.txt is not found."""
    prompt = load_system_prompt()
    assert "helpful assistant" in prompt


@patch("builtins.open", side_effect=Exception("Unexpected error"))
@patch("app.common.utils._get_data_filepath")
def test_load_system_prompt_generic_exception(mock_get_path, mock_open_):
    """Test fallback for generic exceptions."""
    prompt = load_system_prompt()
    assert "helpful assistant" in prompt


@patch(
    "app.common.utils.load_cv_data", return_value={"summary": "Summary", "skills": []}
)
def test_data_access_functions(mock_load_cv):
    """Test data access functions for LLM tools."""
    assert get_professional_summary() == "Summary"
    assert get_skills() == []


@patch("app.common.utils.load_projects_data")
def test_get_project_functions(mock_load_projects):
    """Test project access functions for LLM tools."""
    projects_list = [{"id": "p1", "title": "Proj 1"}]
    projects_dict = {"p1": projects_list[0]}
    mock_load_projects.return_value = (projects_list, projects_dict)

    assert get_project_list() is not None
    assert get_project_details("p1")["title"] == "Proj 1"
    assert get_project_details("nonexistent") is None
