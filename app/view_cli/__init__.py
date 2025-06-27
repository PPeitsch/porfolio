from flask import Blueprint

from . import routes  # noqa: F401

cli_bp = Blueprint(
    "cli",
    __name__,
    template_folder="templates",
    static_folder="static",
)
