from flask import Blueprint

auth_bp = Blueprint("auth", __name__)

# This import is intentionally placed here and has its linting errors
# ignored. It must be after the blueprint is defined to avoid circular
# dependencies, and flake8 is instructed to ignore the E402 (module level
# import not at top) and F401 (imported but unused) errors.
from . import routes  # noqa: E402,F401
