from flask import jsonify, current_app, g
from . import recruiter_bp

# from common.utils import load_cv_data, load_projects_data # Import later when needed
import logging

logger = logging.getLogger(__name__)


@recruiter_bp.route("/api/step/<step_id>")
def get_step_data(step_id):
    logger.info(f"Recruiter API received request for step: {step_id}")
    # TODO: Implement logic to fetch data for a specific step
    # based on step_id (e.g., from a YAML story file or database)
    return jsonify(
        {
            "step_id": step_id,
            "text": f"This is the placeholder text for step '{step_id}'.",
            "choices": [
                {"text": "Placeholder Choice 1", "next_step": "step_2"},
                {"text": "Placeholder Choice 2", "next_step": "step_3"},
            ],
        }
    )
