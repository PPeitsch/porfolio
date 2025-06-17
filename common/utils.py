import logging
import os

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
        base_path = os.path.dirname(current_app.root_path)
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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


def load_ai_context():
    """Loads the AI context from ai_context.md, caching it in g.

    Returns:
        str: The content of the AI context file, or a default error message.
    """
    if "ai_context" not in g:
        logger.info("Loading ai_context.md into context g")
        filepath = _get_data_filepath("ai_context.md")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                g.ai_context = f.read()
        except FileNotFoundError:
            logger.error(f"AI context file not found: {filepath}")
            g.ai_context = "Error: AI context file could not be found."
        except Exception as e:
            logger.error(f"An unexpected error occurred loading {filepath}: {e}")
            g.ai_context = "Error: Could not load AI context."
    return g.ai_context
