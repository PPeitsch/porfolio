from flask import Blueprint

from . import routes  # noqa: F401

recruiter_bp = Blueprint(
    "recruiter",
    __name__,
    template_folder="templates",
    static_folder="static",
)
