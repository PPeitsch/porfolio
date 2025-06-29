import logging
import os
from typing import Any, Dict, List, Optional, cast

import yaml
from flask import current_app, g

logger = logging.getLogger(__name__)


def _get_data_filepath(filename):
    """Constructs the full, absolute path to a data file.

    Handles running both within a Flask application context and in standalone scripts.

    Args:
        filename (str): The name of the data file (e.g., 'cv.yaml').

    Returns:
        str: The absolute path to the data file.
    """
    if current_app:
        # The 'instance_path' is outside the 'app' package, in the project root.
        # We go one level up from the instance path to get to the project root.
        project_root = os.path.dirname(current_app.instance_path)
        base_path = project_root
    else:
        # For standalone scripts, go up from app/common/
        base_path = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
    filepath = os.path.join(base_path, "data", filename)
    return filepath


def load_yaml_data(filename):
    """Loads and parses data from a YAML file.

    Args:
        filename (str): The name of the YAML file in the /data directory.

    Returns:
        dict | list | None: The parsed data, or an empty dictionary on error.
    """
    filepath = _get_data_filepath(filename)
    logger.debug(f"Attempting to load YAML data from: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data if data else {}
    except FileNotFoundError:
        logger.error(f"Data file not found: {filepath}")
        return {}
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {filepath}: {e}")
        return {}
    except Exception as e:
        logger.error(f"An unexpected error occurred loading {filepath}: {e}")
        return {}


def load_cv_data():
    """Loads CV data from cv.yaml, caching it in the application context.

    Provides default values if the file is missing or malformed.

    Returns:
        dict: A dictionary containing the CV data.
    """
    if "cv_data" not in g:
        logger.info("Loading cv.yaml into context g")
        loaded_data = load_yaml_data("cv.yaml")
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

    Returns both a list of projects and a dictionary of projects keyed by ID.

    Returns:
        tuple[list, dict]: A tuple containing the list of project dicts
                           and a dictionary of projects keyed by ID.
    """
    if "projects_data" not in g:
        logger.info("Loading projects.yaml into context g")
        loaded_data = load_yaml_data("projects.yaml")
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


def get_project_details(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves detailed information for a specific project by its ID.
    Returns None if the project is not found.
    """
    _, projects_dict = load_projects_data()
    project = projects_dict.get(project_id)
    # Cast the result to the expected return type for mypy
    return cast(Optional[Dict[str, Any]], project)


def load_system_prompt() -> str:
    """Loads the system prompt from data/system_prompt.txt.

    Returns:
        str: The content of the system prompt file.
    """
    filepath = _get_data_filepath("system_prompt.txt")
    logger.debug(f"Attempting to load system prompt from: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read().strip()
    except FileNotFoundError:
        logger.error(f"System prompt file not found: {filepath}")
        return "You are a helpful assistant."  # Fallback prompt
    except Exception as e:
        logger.error(f"An unexpected error occurred loading {filepath}: {e}")
        return "You are a helpful assistant."


def load_text_config():
    """Loads text configuration from text_config.yaml, caching it in the context.

    Returns:
        dict: A dictionary containing the text configuration.
    """
    if "text_config" not in g:
        logger.info("Loading text_config.yaml into context g")
        loaded_data = load_yaml_data("text_config.yaml")
        g.text_config = loaded_data if isinstance(loaded_data, dict) else {}
    return g.text_config
