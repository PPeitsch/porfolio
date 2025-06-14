import logging

from flask import jsonify, request

from . import auth_bp

logger = logging.getLogger(__name__)


@auth_bp.route("/verify", methods=["POST"])
def verify_access_code():
    """Verifies the access code and returns a token if valid."""
    # This is a placeholder for now.
    # The full logic will be implemented in the next step.
    logger.info("Auth API: Received request to /verify")

    if not request.json or "code" not in request.json:
        return jsonify({"error": "Access code is required."}), 400

    code = request.json.get("code")
    logger.info(f"Auth API: Verification attempt with code: '{code}'")

    # Placeholder logic
    if code == "test-code":
        return (
            jsonify(
                {
                    "message": "Verification successful (placeholder).",
                    "token": "placeholder-jwt-token",
                }
            ),
            200,
        )
    else:
        return jsonify({"error": "Invalid access code."}), 401
