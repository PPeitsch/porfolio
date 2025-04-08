import logging
import os

from flask import abort, jsonify, send_from_directory

from common.utils import load_projects_data  # Use common loader

from . import visual_bp  # Import the blueprint

logger = logging.getLogger(__name__)


# --- Route to serve static files for THIS blueprint (visual.css, visual.js) ---
@visual_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serves static files specific to the Visual blueprint."""
    # Construct path relative to the blueprint's root path
    static_dir = os.path.join(visual_bp.root_path, "static")
    logger.debug(f"Serving Visual static file: {filename} from {static_dir}")
    try:
        return send_from_directory(static_dir, filename)
    except FileNotFoundError:
        logger.error(
            f"Visual Static file not found: {os.path.join(static_dir, filename)}"
        )
        abort(404)


# --- API Endpoint to provide formatted project data for the visual view ---
@visual_bp.route("/api/projects")
def get_projects_for_visual():
    """Gets and formats project data suitable for the visual overview display."""
    logger.info("Visual API requested project data.")
    # Use the common utility function (accesses 'g' context)
    projects_data, _ = load_projects_data()  # Ignore the projects_dict for now

    if projects_data is None:  # Check if loading failed in utils
        logger.error("Visual API failed: Projects data not loaded into context.")
        return jsonify({"error": "Failed to load backend project data."}), 500

    simple_projects = []
    for p in projects_data:
        # --- Define Image URL Logic ---
        # Assumes images are central in shell/static/images/projects/
        # and shell blueprint serves its static files via '/shell-static/'
        image_filename = p.get("image")
        # Define a default placeholder image URL (also served by shell)
        placeholder_image_url = (
            "/shell-static/images/placeholder.svg"  # Adjust if placeholder name differs
        )
        image_url = placeholder_image_url  # Default to placeholder
        if image_filename:
            # Construct URL using the shell's static path prefix
            image_url = f"/shell-static/images/projects/{image_filename}"
        # --- End Image URL Logic ---

        # Basic description truncation
        description = p.get(
            "short_description", p.get("description", "No description available.")
        )
        short_desc = (
            (description[:100] + "...") if len(description) > 100 else description
        )

        # Build the simplified dictionary for this project
        simple_projects.append(
            {
                "id": p.get(
                    "id", f"unknown_{len(simple_projects)}"
                ),  # Provide fallback id
                "title": p.get("title", "Untitled Project"),
                "image_url": image_url,  # Use the final URL path
                "short_desc": short_desc,
                "live_url": p.get("live_url"),
                "github_url": p.get("github_url"),
                "pypi_url": p.get("pypi_url"),
                "docs_url": p.get("docs_url"),
                "type": p.get("type", "unknown"),  # Provide fallback type
                "technologies": p.get("technologies", [])[:4],  # Limit techs shown
            }
        )

    # Optional: Sort projects before returning, e.g., by title
    # simple_projects.sort(key=lambda x: x['title'].lower())

    return jsonify(simple_projects)
