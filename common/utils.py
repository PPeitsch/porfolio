import yaml
import os
from flask import current_app, g
import logging

logger = logging.getLogger(__name__)


def _get_data_filepath(filename):
    """Constructs the full path to a data file."""
    if current_app:
        base_path = os.path.dirname(current_app.root_path)
    else:
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
    """Loads project data from projects.yaml, caching it in the application context."""
    if "projects_data" not in g:
        logger.info("Loading projects.yaml into context g")
        loaded_data = load_yaml_data("projects.yaml")
        if isinstance(loaded_data, list):
            g.projects_data = loaded_data
            # Ensure projects_dict is always created/updated when projects_data is loaded
            g.projects_dict = (
                {p.get("id", f"proj_{i}"): p for i, p in enumerate(g.projects_data)}
                if g.projects_data
                else {}
            )
        else:
            logger.warning("projects.yaml did not load as a list. Using empty list.")
            g.projects_data = []
            g.projects_dict = {}
    # Ensure projects_dict exists even if projects_data was loaded in a previous request context?
    # This might be needed if g persists across requests in some server configs, though typically it shouldn't.
    # For safety, we can ensure it's populated if projects_data exists.
    elif "projects_data" in g and "projects_dict" not in g:
        g.projects_dict = (
            {p.get("id", f"proj_{i}"): p for i, p in enumerate(g.projects_data)}
            if g.projects_data
            else {}
        )

    # Always return both, even if projects_dict had to be recreated
    return g.get("projects_data", []), g.get("projects_dict", {})


def load_recruiter_story_data():
    """Loads the recruiter story structure from recruiter_story.yaml."""
    if "recruiter_story" not in g:
        logger.info("Loading recruiter_story.yaml into context g")
        loaded_data = load_yaml_data("recruiter_story.yaml")
        if (
            isinstance(loaded_data, dict) and loaded_data
        ):  # Ensure it's a non-empty dict
            g.recruiter_story = loaded_data
        else:
            logger.warning(
                "recruiter_story.yaml did not load as a dictionary or is empty. Using default error step."
            )
            # Provide a minimal fallback structure
            g.recruiter_story = {
                "start": {"text": "Error: Story could not be loaded.", "choices": []},
                "step_not_found": {
                    "text": "Error: Story could not be loaded.",
                    "choices": [],
                },
            }
    return g.recruiter_story
