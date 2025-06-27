from flask import Blueprint

from . import routes  # noqa: F401

visual_bp = Blueprint(
    "visual",
    __name__,
    template_folder="templates",
    static_folder="static",
)
