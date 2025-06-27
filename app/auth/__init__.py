from flask import Blueprint

from . import routes  # noqa: F401

auth_bp = Blueprint("auth", __name__)
