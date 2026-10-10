import logging
import os

from flask import abort, current_app, jsonify, send_from_directory

from app.common.i18n import t
from app.common.utils import load_projects_data

from . import visual_bp

logger = logging.getLogger(__name__)


@visual_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serves static files specific to the Visual blueprint.

    Handles requests for files like visual.css and visual.js.

    Args:
        filename (str): The name of the file to serve from the static folder.

    Returns:
        Response: The requested static file or a 404 error if not found.
    """
    static_dir = os.path.join(visual_bp.root_path, "static")
    logger.debug(f"Serving Visual static file: {filename} from {static_dir}")
    try:
        return send_from_directory(static_dir, filename)
    except FileNotFoundError:
        logger.error(
            f"Visual Static file not found: {os.path.join(static_dir, filename)}"
        )
        abort(404)


def _type_label(project_type):
    """The project type as shown on the card, or "" for an unknown type."""
    key = f"visual.type_{project_type}"
    label = t(key)
    return "" if label == key else label


@visual_bp.route("/api/projects")
def get_projects_for_visual():
    """Gets and formats project data for the visual overview display.

    This API endpoint retrieves all project data, then formats it into a
    simplified structure suitable for rendering project cards in the UI.
    It constructs full image URLs and labels the project type.

    Returns:
        Response: A JSON response containing a list of simplified project
                  dictionaries.
    """
    logger.info("Visual API requested project data.")
    projects_data, _ = load_projects_data()

    if projects_data is None:
        logger.error("Visual API failed: Projects data not loaded into context.")
        return jsonify({"error": "Failed to load backend project data."}), 500

    simple_projects = []
    for p in projects_data:
        image_filename = p.get("image")
        # No image: the card draws its own placeholder.
        image_url = None
        if image_filename:
            # Images live in <DATA_DIR>/images; the bundled shell static folder
            # is kept as a fallback for images added there before.
            content_image = os.path.join(
                current_app.config.get("DATA_DIR", ""), "images", image_filename
            )
            if os.path.isfile(content_image):
                image_url = f"/content/images/{image_filename}"
            else:
                image_url = f"/shell-static/images/projects/{image_filename}"

        # Whole: the card cuts it at three lines.
        description = str(
            p.get("short_description")
            or p.get("description")
            or t("visual.no_description")
        )
        project_type = p.get("type", "unknown")

        simple_projects.append(
            {
                "id": p.get("id", f"unknown_{len(simple_projects)}"),
                "title": p.get("title") or t("visual.untitled"),
                "image_url": image_url,
                "short_desc": description,
                "live_url": p.get("live_url"),
                "github_url": p.get("github_url"),
                "pypi_url": p.get("pypi_url"),
                "docs_url": p.get("docs_url"),
                "type": project_type,
                "type_label": _type_label(project_type),
                "technologies": p.get("technologies", []),
            }
        )

    return jsonify(simple_projects)
