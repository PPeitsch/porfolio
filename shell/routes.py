import logging

from flask import Blueprint, render_template

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
    view_map = {
        "cli": "cli_view.html",
        "recruiter": "recruiter_view.html",  # Add recruiter template
        "visual": "visual_view.html",  # Add visual template (placeholder)
    }
    template_name = view_map.get(view_name)

    if template_name:
        # Render template. Blueprints need correct template_folder setup.
        # For simplicity here, assume templates are found relative to *their* blueprint.
        # Flask searches blueprint folders then application folder.
        # We might need to specify blueprint name if templates clash: 'recruiter/recruiter_view.html'
        try:
            # This relies on Flask finding the template in the correct blueprint's folder
            return render_template(template_name)
        except Exception as e:
            logger.error(
                f"Error rendering template {template_name} for view {view_name}: {e}"
            )
            return (
                f'<p class="text-red-500 p-4">Error rendering view template: {e}</p>',
                500,
            )
    else:
        logger.warning(f"Partial requested for unknown view: {view_name}")
        return '<p class="text-red-500 p-4">Error: View not found.</p>', 404
