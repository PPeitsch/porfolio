import yaml
import os
from flask import current_app
import logging

logger = logging.getLogger(__name__)


# Placeholder - Will add YAML loading logic in a later step
def load_yaml_data(filename):
    """Placeholder for loading YAML data."""
    logger.info(f"Pretending to load data from {filename}")
    if filename == 'cv.yaml':
        return {'name': 'Placeholder Name', 'title': 'Placeholder Title'}
    elif filename == 'projects.yaml':
        return [{'id': 'proj1', 'title': 'Placeholder Project'}]
    return None


def load_cv_data():
    """Loads CV data."""
    return load_yaml_data('cv.yaml')


def load_projects_data():
    """Loads projects data."""
    return load_yaml_data('projects.yaml')
