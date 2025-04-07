from flask import Blueprint

# Define the blueprint for the CLI view
cli_bp = Blueprint(
    "cli",
    __name__,
    template_folder="templates",
    # static_folder='static',
    # static_url_path='/cli-static'
)

# Import routes after blueprint definition
from . import routes
