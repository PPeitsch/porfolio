import yaml
import os
from flask import current_app, g  # Import g for context caching
import logging

logger = logging.getLogger(__name__)


def _get_data_filepath(filename):
    """Constructs the full path to a data file."""
    # Check if running within Flask app context
    if current_app:
        # Assumes 'data' directory is one level up from the app's root_path (e.g., shell/../data)
        # Adjust if your structure is different
        base_path = os.path.dirname(current_app.root_path)
    else:
        # Fallback for scripts or tests run outside app context
        # This assumes utils.py is in common/ which is parallel to data/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    filepath = os.path.join(base_path, "data", filename)
    return filepath


def load_yaml_data(filename):
    """Loads data from a YAML file in the data directory."""
    filepath = _get_data_filepath(filename)
    logger.debug(f"Attempting to load YAML data from: {filepath}")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            logger.debug(f"Successfully loaded data from {filename}.")
            return data if data else {}  # Return empty dict if file is empty
    except FileNotFoundError:
        logger.error(f"Data file not found: {filepath}")
        return {}  # Return empty dict on error
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML file {filepath}: {e}")
        return {}  # Return empty dict on error
    except Exception as e:
        logger.error(f"An unexpected error occurred loading {filepath}: {e}")
        return {}  # Return empty dict on error


def load_cv_data():
    """Loads CV data from cv.yaml, caching it in the application context."""
    # Use Flask's 'g' object for request context caching
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
        # Ensure loaded_data is a dictionary before updating
        if isinstance(loaded_data, dict):
            defaults.update(loaded_data)
        else:
            logger.warning("cv.yaml did not load as a dictionary. Using defaults.")
        g.cv_data = defaults
    return g.cv_data


def load_projects_data():
    """Loads project data from projects.yaml, caching it in the application context."""
    if "projects_data" not in g:
        logger.info("Loading projects.yaml into context g")
        loaded_data = load_yaml_data("projects.yaml")
        # Ensure loaded_data is a list
        if isinstance(loaded_data, list):
            g.projects_data = loaded_data
            g.projects_dict = {
                p.get("id", f"proj_{i}"): p for i, p in enumerate(loaded_data)
            }
        else:
            logger.warning("projects.yaml did not load as a list. Using empty list.")
            g.projects_data = []
            g.projects_dict = {}

    return g.projects_data, g.projects_dict
