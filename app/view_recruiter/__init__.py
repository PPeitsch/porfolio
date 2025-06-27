from flask import Blueprint

# Define the blueprint for the Recruiter (CYOA) view
recruiter_bp = Blueprint(
    "recruiter",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/recruiter/static",
)

# Import routes after blueprint definition
from . import routes
