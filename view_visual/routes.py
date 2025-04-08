import logging
import os

from flask import abort, jsonify, send_from_directory

from common.utils import load_projects_data  # May need projects later

from . import visual_bp  # Import the blueprint

logger = logging.getLogger(__name__)


# --- Route to serve static files for this blueprint ---
@visual_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serves static files specific to the Visual blueprint."""
    static_dir = os.path.join(visual_bp.root_path, "static")
    logger.debug(f"Serving Visual static file: {filename} from {static_dir}")
    try:
        return send_from_directory(static_dir, filename)
    except FileNotFoundError:
        logger.error(
            f"Visual Static file not found: {os.path.join(static_dir, filename)}"
        )
        abort(404)


# --- Placeholder API Route (Optional - maybe needed later for dynamic data) ---
# Example: If we want to lazy-load project details on click
@visual_bp.route("/api/projects")
def get_projects_for_visual():
    logger.info("Visual API requested project data.")
    # Use the common utility function (accesses 'g' context)
    projects_data, _ = load_projects_data()
    # Select only the necessary fields for the visual view display
    simple_projects = [
        {
            "id": p.get("id"),
            "title": p.get("title"),
            "image": p.get(
                "image"
            ),  # Ensure image paths are correct relative to static folders
            "short_desc": p.get("short_description", p.get("description", ""))[:100]
            + "...",  # Truncate desc
            "live_url": p.get("live_url"),
            "github_url": p.get("github_url"),
            "type": p.get("type"),
            "technologies": p.get("technologies", [])[:4],  # Limit techs shown maybe
        }
        for p in projects_data
    ]
    return jsonify(simple_projects)
