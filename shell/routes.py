from flask import Blueprint, render_template, current_app
import logging
from common.utils import load_cv_data

logger = logging.getLogger(__name__)

shell_bp = Blueprint(
    "shell",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/shell-static",
)


@shell_bp.route("/")
def selector():
    """Serves the initial view selector page."""
    logger.info("Serving view selector page.")
    cv_data = load_cv_data()
    return render_template("selector.html", cv=cv_data)


# --- Route to serve HTML partials ---
@shell_bp.route("/view/<view_name>")
def get_view_partial(view_name):
    """Serves the HTML partial for a requested view."""
    logger.info(f"Serving partial for view: {view_name}")
    if view_name == "cli":
        # Render the template from the 'view_cli' blueprint's template folder
        # Note: The actual template path is relative to the blueprint's template_folder
        return render_template("cli_view.html")
    elif view_name == "recruiter":
        # Placeholder for future step
        return render_template("recruiter_view.html")
    elif view_name == "visual":
        # Placeholder for future step
        return render_template("visual_view.html")
    else:
        logger.warning(f"Partial requested for unknown view: {view_name}")
        return '<p class="text-red-500 p-4">Error: View not found.</p>', 404
