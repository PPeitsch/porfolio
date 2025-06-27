from flask import Blueprint

cli_bp = Blueprint(
    "cli",
    __name__,
    template_folder="templates",
    static_folder="static",
)

from . import routes
