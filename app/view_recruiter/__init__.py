from flask import Blueprint

recruiter_bp = Blueprint(
    "recruiter",
    __name__,
    template_folder="templates",
    static_folder="static",
)

from . import routes
