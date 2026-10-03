import os
from unittest.mock import mock_open, patch

import pytest
import yaml
from flask import g

from app.common.exceptions import DataFileError, DataFileNotFoundError
from app.common.utils import (
    _get_data_filepath,
    get_education,
    get_experience,
    get_professional_summary,
    get_project_details,
    get_project_list,
    get_skills,
    load_cv_data,
    load_projects_data,
    load_system_prompt,
    load_text_config,
    load_yaml_data,
    parse_yaml_data,
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


@patch("builtins.open", side_effect=PermissionError("Permission denied"))
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_unreadable_file(mock_get_path, mock_open_):
    """Test handling of a file that exists but cannot be read."""
    data = load_yaml_data("error.yaml")
    assert data == {}


@patch("builtins.open", side_effect=FileNotFoundError)
@patch("app.common.utils._get_data_filepath")
def test_parse_yaml_data_raises_not_found(mock_get_path, mock_open_):
    """The strict loader raises DataFileNotFoundError for a missing file."""
    with pytest.raises(DataFileNotFoundError):
        parse_yaml_data("non_existent.yaml")


@patch("builtins.open", new_callable=mock_open, read_data="key: [unclosed")
@patch("app.common.utils._get_data_filepath")
def test_parse_yaml_data_raises_on_malformed_yaml(mock_get_path, mock_open_):
    """The strict loader raises DataFileError, not a YAML error."""
    with pytest.raises(DataFileError) as excinfo:
        parse_yaml_data("malformed.yaml")
    assert not isinstance(excinfo.value, DataFileNotFoundError)


@patch("builtins.open", side_effect=RuntimeError("A bug, not a data problem"))
@patch("app.common.utils._get_data_filepath")
def test_load_yaml_data_does_not_hide_unexpected_errors(mock_get_path, mock_open_):
    """Only data file errors fall back to defaults; anything else propagates."""
    with pytest.raises(RuntimeError):
        load_yaml_data("error.yaml")


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
    assert data2 is data1
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
    assert list1 is list2
    mock_load_yaml.assert_called_once()


@patch("app.common.utils.load_yaml_data")
def test_load_projects_data_dict_repopulation(mock_load_yaml, app):
    """Test repopulating projects_dict when it's missing."""
    with app.app_context():
        g.projects_data = MOCK_PROJECTS_DATA
        g.pop("projects_dict", None)  # Ensure dict is not present
        _, projects_dict = load_projects_data()
        assert "proj1" in projects_dict
        assert projects_dict["proj1"]["title"] == "Project One"


@patch("app.common.utils.parse_yaml_data")
def test_load_text_config_caching(mock_parse_yaml, app):
    """Test that text config data is loaded once and cached in 'g'."""
    mock_parse_yaml.return_value = {"key": "value"}
    with app.app_context():
        data1 = load_text_config()
        load_text_config()
    assert data1["key"] == "value"
    mock_parse_yaml.assert_called_once()


@patch("app.common.utils.parse_yaml_data")
def test_load_text_config_merges_content_over_engine(mock_parse_yaml, app):
    """The content's text_config.yaml only overrides the keys it sets."""
    mock_parse_yaml.return_value = {"cli": {"neofetch": {"logo": "rocket"}}}
    with app.app_context():
        text_config = load_text_config()
    assert text_config["cli"]["neofetch"]["logo"] == "rocket"
    # The rest comes from the engine's texts.
    assert text_config["cli"]["neofetch"]["os_name"] == "FlaskOS 1.0"
    assert text_config["cli"]["commands"]["items"]
    assert "get_skills" in text_config["llm_tool_descriptions"]


@patch(
    "app.common.utils.parse_yaml_data",
    side_effect=DataFileNotFoundError("missing"),
)
def test_load_text_config_without_content_file(mock_parse_yaml, app):
    """Without a text_config.yaml in the content, the engine's texts are used."""
    with app.app_context():
        text_config = load_text_config()
    assert text_config["cli"]["commands"]["items"]
    assert text_config["cli"]["manuals"]


@patch("app.common.utils.load_yaml_data")
def test_loaders_with_bad_data_type(mock_load_yaml, app):
    """Test loaders handle incorrect data types from YAML files."""
    with app.app_context():
        g.pop("cv_data", None)
        g.pop("projects_data", None)
        g.pop("text_config", None)
        # Test load_cv_data with a list instead of a dict
        mock_load_yaml.return_value = []
        cv_data = load_cv_data()
        assert cv_data["name"] == "Default Name"

        # Test load_projects_data with a dict instead of a list
        mock_load_yaml.return_value = {}
        projects_data, projects_dict = load_projects_data()
        assert projects_data == []
        assert projects_dict == {}

    # A content text_config.yaml that is not a mapping is ignored: the engine's
    # texts are still used.
    with app.app_context(), patch("app.common.utils.parse_yaml_data", return_value=[]):
        text_config = load_text_config()
        assert text_config["cli"]["commands"]["items"]


@patch("builtins.open", side_effect=FileNotFoundError)
@patch("app.common.utils._get_data_filepath")
def test_load_system_prompt_not_found(mock_get_path, mock_open_):
    """Test fallback when system_prompt.txt is not found."""
    prompt = load_system_prompt()
    assert "helpful assistant" in prompt


@patch("builtins.open", side_effect=PermissionError("Permission denied"))
@patch("app.common.utils._get_data_filepath")
def test_load_system_prompt_unreadable_file(mock_get_path, mock_open_):
    """Test fallback when system_prompt.txt cannot be read."""
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

    project_list_result = get_project_list()
    assert project_list_result is not None
    assert isinstance(project_list_result, list)

    project_details_result = get_project_details("p1")
    assert project_details_result is not None
    assert project_details_result["title"] == "Proj 1"

    # Test the new behavior: expecting a dictionary with an error key
    nonexistent_project_result = get_project_details("nonexistent")
    assert nonexistent_project_result is not None
    assert "error" in nonexistent_project_result
    assert "not found" in nonexistent_project_result["error"]


@patch(
    "app.common.utils.load_cv_data",
    return_value={
        "experience": [{"role": "Dev", "company": "Acme"}, "stray text"],
        "education": None,
    },
)
def test_experience_and_education(mock_load_cv):
    """Experience keeps only mappings; a missing or empty section is an empty list."""
    assert get_experience() == [{"role": "Dev", "company": "Acme"}]
    assert get_education() == []


def test_tool_definitions_include_experience_and_education(app):
    """The chat gets the experience and education tools, mapped to callables."""
    from app.common.llm_tools import TOOL_MAP, get_tool_definitions

    with app.test_request_context():
        names = [d["function"]["name"] for d in get_tool_definitions("Alex")]
    for name in ("get_experience", "get_education"):
        assert name in names
        assert callable(TOOL_MAP[name])
