import logging
import os

from flask import (
    Blueprint,
    abort,
    current_app,
    make_response,
    redirect,
    render_template,
    send_from_directory,
    url_for,
)
from jinja2 import TemplateError
from markupsafe import escape

from app.common.i18n import (
    LANG_COOKIE,
    get_languages,
    get_locale,
    get_ui_texts,
    language_name,
    t,
)
from app.common.utils import get_welcome_message, load_cv_data

logger = logging.getLogger(__name__)

shell_bp = Blueprint(
    "shell",
    __name__,
    template_folder="templates",
    static_folder="static",
    static_url_path="/shell-static",
)


# The language chosen with the switcher is remembered for a year.
LANG_COOKIE_MAX_AGE = 365 * 24 * 60 * 60


@shell_bp.app_context_processor
def inject_language():
    """Makes the language and the interface texts available to every template."""
    return {
        "lang": get_locale(),
        "languages": [(code, language_name(code)) for code in get_languages()],
        "ui_texts": get_ui_texts(),
        "t": t,
    }


@shell_bp.route("/lang/<code>")
def set_language(code):
    """Remembers the visitor's language in a cookie and goes back home.

    Args:
        code (str): A language code from LANGUAGES, e.g. 'es'.

    Returns:
        Response: A redirect to the selector, or 404 for an unknown language.
    """
    if code not in get_languages():
        abort(404)
    response = make_response(redirect(url_for("shell.selector")))
    response.set_cookie(
        LANG_COOKIE, code, max_age=LANG_COOKIE_MAX_AGE, samesite="Lax", httponly=True
    )
    return response


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
        except TemplateError as e:
            logger.error(
                f"Error rendering template {template_name} for view {view_name}: {e}"
            )
            error_html = (
                '<div class="p-8 text-center"><p class="text-red-500">'
                f"{escape(t('view.render_error'))}</p></div>"
            )
            return error_html, 500
    else:
        logger.warning(f"Partial requested for unknown view: {view_name}")
        error_html = (
            '<div class="p-8 text-center"><p class="text-red-500">'
            f'Error: View "{escape(view_name)}" not found.</p></div>'
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


@shell_bp.route("/p/<path:filename>")
def content_page(filename):
    """Serves a standalone page, or one of its files, from the pages/ folder.

    A page is a complete HTML document kept with the content, such as a
    services or "hire me" page: ``pages/services.html`` is served at
    ``/p/services``, and the files it links relatively (``eicosane.png``)
    at ``/p/eicosane.png``.

    Args:
        filename (str): A page name without extension, or a file path
                        relative to <DATA_DIR>/pages.

    Returns:
        Response: The page or file, or 404 if it does not exist.
    """
    pages_dir = os.path.join(current_app.config["DATA_DIR"], "pages")
    if not os.path.splitext(filename)[1]:
        filename += ".html"
    if not os.path.isfile(os.path.join(pages_dir, filename)):
        abort(404)
    return send_from_directory(pages_dir, filename)
