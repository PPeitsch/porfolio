import logging
import os
from typing import Any, Dict, List, Optional, cast

import yaml
from flask import current_app, g

from app.common.exceptions import DataFileError, DataFileNotFoundError
from app.common.i18n import localize

logger = logging.getLogger(__name__)

# Texts and logos of the engine itself. The content folder's text_config.yaml
# and logo/ only add to them or override them.
DEFAULTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "defaults"
)


def _get_data_filepath(filename):
    """Constructs the full, absolute path to a data file.

    Inside the app, files are read from the configured DATA_DIR
    (PORTFOLIO_DATA_DIR); standalone scripts read from the project's data/.

    Args:
        filename (str): The name of the data file (e.g., 'cv.yaml').

    Returns:
        str: The absolute path to the data file.
    """
    if current_app and current_app.config.get("DATA_DIR"):
        return os.path.join(current_app.config["DATA_DIR"], filename)
    if current_app:
        # The 'instance_path' is outside the 'app' package, in the project root.
        project_root = os.path.dirname(current_app.instance_path)
    else:
        # For standalone scripts, go up from app/common/
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    return os.path.join(project_root, "data", filename)


def read_data_file(filename: str) -> str:
    """Reads a text file from the data directory.

    Args:
        filename (str): The name of the file in the data directory.

    Returns:
        str: The file's content.

    Raises:
        DataFileNotFoundError: If the file does not exist.
        DataFileError: If the file exists but cannot be read.
    """
    filepath = _get_data_filepath(filename)
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError as e:
        raise DataFileNotFoundError(f"Data file not found: {filepath}") from e
    except (OSError, UnicodeDecodeError) as e:
        raise DataFileError(f"Could not read data file {filepath}: {e}") from e


def parse_yaml_data(filename: str) -> Any:
    """Reads and parses a YAML file from the data directory.

    Args:
        filename (str): The name of the YAML file in the data directory.

    Returns:
        The parsed data, or an empty dictionary if the file is empty.

    Raises:
        DataFileNotFoundError: If the file does not exist.
        DataFileError: If the file cannot be read or is not valid YAML.
    """
    content = read_data_file(filename)
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        raise DataFileError(f"Error parsing YAML file {filename}: {e}") from e
    return data if data else {}


def load_yaml_data(filename):
    """Loads and parses data from a YAML file, never failing.

    The views keep working with defaults when a data file is missing or
    broken; the reason is logged.

    Args:
        filename (str): The name of the YAML file in the /data directory.

    Returns:
        dict | list: The parsed data, or an empty dictionary on error.
    """
    logger.debug(f"Attempting to load YAML data from: {_get_data_filepath(filename)}")
    try:
        return parse_yaml_data(filename)
    except DataFileError as e:
        logger.error(str(e))
        return {}


def load_cv_data():
    """Loads CV data from cv.yaml, caching it in the application context.

    Bilingual texts are resolved to the language of the current request.

    Provides default values if the file is missing or malformed.

    Returns:
        dict: A dictionary containing the CV data.
    """
    if "cv_data" not in g:
        logger.info("Loading cv.yaml into context g")
        loaded_data = localize(load_yaml_data("cv.yaml"))
        defaults = {
            "name": "Default Name",
            "title": "Default Title",
            "summary": "CV data could not be loaded.",
            "skills": [],
            "social_links": {},
        }
        if isinstance(loaded_data, dict):
            defaults.update(loaded_data)
        else:
            logger.warning("cv.yaml did not load as a dictionary. Using defaults.")
        g.cv_data = defaults
    return g.cv_data


def load_projects_data():
    """Loads project data from projects.yaml, caching it in the context.

    Bilingual texts are resolved to the language of the current request.

    Returns both a list of projects and a dictionary of projects keyed by ID.

    Returns:
        tuple[list, dict]: A tuple containing the list of project dicts
                           and a dictionary of projects keyed by ID.
    """
    if "projects_data" not in g:
        logger.info("Loading projects.yaml into context g")
        loaded_data = localize(load_yaml_data("projects.yaml"))
        if isinstance(loaded_data, list):
            g.projects_data = loaded_data
            g.projects_dict = (
                {p.get("id", f"proj_{i}"): p for i, p in enumerate(g.projects_data)}
                if g.projects_data
                else {}
            )
        else:
            logger.warning("projects.yaml did not load as a list. Using empty list.")
            g.projects_data = []
            g.projects_dict = {}
    elif "projects_data" in g and "projects_dict" not in g:
        g.projects_dict = (
            {p.get("id", f"proj_{i}"): p for i, p in enumerate(g.projects_data)}
            if g.projects_data
            else {}
        )

    return g.get("projects_data", []), g.get("projects_dict", {})


# --- Data Access Functions (Tools for LLM) ---


def get_professional_summary() -> str:
    """Retrieves the professional summary from the CV data."""
    cv_data = load_cv_data()
    # Using cast to assure mypy of the return type from .get()
    summary = cv_data.get("summary", "No professional summary is available.")
    return cast(str, summary)


def get_skills(category: Optional[str] = None) -> List[str]:
    """Retrieves the list of technical skills."""
    cv_data = load_cv_data()
    skills = cv_data.get("skills", [])
    # Using cast for type safety, as .get can return Any
    return cast(List[str], skills)


def get_experience() -> List[Dict[str, Any]]:
    """Retrieves the work experience entries from the CV data."""
    experience = load_cv_data().get("experience") or []
    return [e for e in cast(List[Any], experience) if isinstance(e, dict)]


def get_education() -> List[Dict[str, Any]]:
    """Retrieves the education entries from the CV data."""
    education = load_cv_data().get("education") or []
    return [e for e in cast(List[Any], education) if isinstance(e, dict)]


def get_project_list() -> List[Dict[str, str]]:
    """Retrieves a summary list of all available projects."""
    projects, _ = load_projects_data()
    if not projects:
        return []

    # The line causing the E501 error is broken down for readability.
    project_summaries = []
    for p in projects:
        summary = {
            "id": p.get("id", "N/A"),
            "title": p.get("title", "Untitled Project"),
            "short_description": p.get(
                "short_description", p.get("description", "No description available.")
            ),
        }
        project_summaries.append(summary)
    return project_summaries


def get_project_details(project_id: str) -> Dict[str, Any]:
    """
    Retrieves detailed information for a specific project by its ID.
    Returns a dictionary with an error message if the project is not found.
    """
    _, projects_dict = load_projects_data()
    project = projects_dict.get(project_id)

    if project is None:
        # Return a structured error message if the project is not found
        return {"error": f"Project with ID '{project_id}' not found."}

    # Cast the result to the expected return type for mypy
    return cast(Dict[str, Any], project)


def load_system_prompt() -> str:
    """Loads the system prompt from data/system_prompt.txt.

    Returns:
        str: The content of the system prompt file, or a generic prompt if
             it cannot be read.
    """
    try:
        return read_data_file("system_prompt.txt").strip()
    except DataFileError as e:
        logger.error(str(e))
        return "You are a helpful assistant."  # Fallback prompt


def get_welcome_message(view: str) -> str:
    """Returns a view's welcome text from text_config.yaml with {name} filled in."""
    template = load_text_config().get(view, {}).get("welcome", "")
    name = load_cv_data().get("name", "")
    return cast(str, template).replace("{name}", name)


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Returns base with override on top; nested mappings merge key by key."""
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_raw_text_config() -> Dict[str, Any]:
    """Returns the engine's text_config.yaml with the content's one on top.

    The content file is optional: it only needs the texts it changes. Texts
    are not localized here. The result is cached in the context.
    """
    if "raw_text_config" not in g:
        try:
            with open(
                os.path.join(DEFAULTS_DIR, "text_config.yaml"), "r", encoding="utf-8"
            ) as f:
                defaults = yaml.safe_load(f) or {}
        except (OSError, yaml.YAMLError) as e:
            logger.error(f"Could not load the engine's text_config.yaml: {e}")
            defaults = {}
        try:
            content = parse_yaml_data("text_config.yaml")
        except DataFileNotFoundError:
            content = {}
        except DataFileError as e:
            logger.error(str(e))
            content = {}
        if not isinstance(content, dict):
            logger.error("text_config.yaml must be a mapping; ignoring it.")
            content = {}
        g.raw_text_config = _deep_merge(defaults, content)
    return cast(Dict[str, Any], g.raw_text_config)


def load_text_config():
    """Returns the text configuration resolved to the request's language.

    It is the engine's texts with the content's text_config.yaml on top
    (see load_raw_text_config), cached in the context.

    Returns:
        dict: A dictionary containing the text configuration.
    """
    if "text_config" not in g:
        loaded_data = localize(load_raw_text_config())
        g.text_config = loaded_data if isinstance(loaded_data, dict) else {}
    return g.text_config
