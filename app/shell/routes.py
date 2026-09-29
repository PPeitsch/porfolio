import logging
import os

from flask import Blueprint, abort, current_app, render_template, send_from_directory

from app.common.utils import get_welcome_message, load_cv_data

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
    """Serves the initial view selector page.

    This is the main entry point of the application. It loads necessary CV
    data and configuration flags to display on the selector screen and
    renders the main selector template.

    Returns:
        Response: The rendered selector.html template.
    """
    logger.info("Serving view selector page.")
    cv_data = load_cv_data()
    banner_enabled = current_app.config.get("BANNER_ENABLED", False)
    banner_message = current_app.config.get("BANNER_MESSAGE", "")

    return render_template(
        "selector.html",
        cv=cv_data,
        banner_enabled=banner_enabled,
        banner_message=banner_message,
    )


@shell_bp.route("/view/<view_name>")
def get_view_partial(view_name):
    """Serves the HTML partial for a requested view.

    This endpoint is called by the frontend JavaScript (`selector.js`) to
    dynamically load the HTML structure for the CLI, Recruiter, or Visual
    views into the main container without a full page reload.

    Args:
        view_name (str): The name of the view to render ('cli', 'recruiter',
                         'visual').

    Returns:
        Response: An HTML fragment for the requested view, or a 404 error
                  message if the view name is not recognized.
    """
    logger.info(f"Serving partial for view: {view_name}")
    view_template_map = {
        "cli": "cli_view.html",
        "recruiter": "recruiter_view.html",
        "visual": "visual_view.html",
    }
    template_name = view_template_map.get(view_name)

    if template_name:
        try:
            return render_template(
                template_name, welcome=get_welcome_message(view_name)
            )
        except Exception as e:
            logger.error(
                f"Error rendering template {template_name} for view {view_name}: {e}"
            )
            error_html = (
                '<div class="p-8 text-center"><p class="text-red-500">'
                f"Error rendering view template: {e}</p></div>"
            )
            return error_html, 500
    else:
        logger.warning(f"Partial requested for unknown view: {view_name}")
        error_html = (
            '<div class="p-8 text-center"><p class="text-red-500">'
            f'Error: View "{view_name}" not found.</p></div>'
        )
        return error_html, 404


@shell_bp.route("/content/images/<path:filename>")
def content_image(filename):
    """Serves a project image from the images/ folder of the content directory.

    Args:
        filename (str): The image path relative to <DATA_DIR>/images.

    Returns:
        Response: The image file, or 404 if it does not exist.
    """
    images_dir = os.path.join(current_app.config["DATA_DIR"], "images")
    if not os.path.isfile(os.path.join(images_dir, filename)):
        abort(404)
    return send_from_directory(images_dir, filename)
