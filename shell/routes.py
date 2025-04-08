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
    # Define template mapping more cleanly
    view_template_map = {
        "cli": "cli_view.html",
        "recruiter": "recruiter_view.html",
        "visual": "visual_view.html",  # Add the visual template name
    }
    template_name = view_template_map.get(view_name)

    if template_name:
        try:
            # Flask searches blueprint folders then application folder
            # If blueprint name is needed: f'{view_name}/{template_name}'
            # But usually just the name is fine if folders are unique.
            return render_template(template_name)
        except Exception as e:
            logger.error(
                f"Error rendering template {template_name} for view {view_name}: {e}"
            )
            # Provide error HTML that fits within the view container
            return (
                f'<div class="p-8 text-center"><p class="text-red-500">Error rendering view template: {e}</p></div>',
                500,
            )
    else:
        logger.warning(f"Partial requested for unknown view: {view_name}")
        return (
            '<div class="p-8 text-center"><p class="text-red-500">Error: View "{view_name}" not found.</p></div>',
            404,
        )
