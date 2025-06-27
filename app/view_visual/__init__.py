from flask import Blueprint

# Define the blueprint for the Visual Overview view
visual_bp = Blueprint(
    "visual",
    __name__,
    template_folder="templates",
    static_folder="static",  # Define location for static files
    static_url_path="/visual-static",  # Define unique URL prefix
)

# Import routes after blueprint definition
from . import routes
