import logging
import os

from flask import abort, jsonify, send_from_directory

from common.utils import load_projects_data

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


@visual_bp.route("/api/projects")
def get_projects_for_visual():
    """Gets and formats project data for the visual overview display.

    This API endpoint retrieves all project data, then formats it into a
    simplified structure suitable for rendering project cards in the UI.
    It constructs full image URLs and truncates descriptions.

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
        placeholder_image_url = "/shell-static/images/placeholder.svg"
        image_url = placeholder_image_url
        if image_filename:
            # Assumes images are central in shell/static/images/projects/
            image_url = f"/shell-static/images/projects/{image_filename}"

        description = p.get(
            "short_description", p.get("description", "No description available.")
        )
        short_desc = (
            (description[:100] + "...") if len(description) > 100 else description
        )

        simple_projects.append(
            {
                "id": p.get("id", f"unknown_{len(simple_projects)}"),
                "title": p.get("title", "Untitled Project"),
                "image_url": image_url,
                "short_desc": short_desc,
                "live_url": p.get("live_url"),
                "github_url": p.get("github_url"),
                "pypi_url": p.get("pypi_url"),
                "docs_url": p.get("docs_url"),
                "type": p.get("type", "unknown"),
                "technologies": p.get("technologies", [])[:4],
            }
        )

    return jsonify(simple_projects)
