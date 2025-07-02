import datetime
import hmac
import logging

import jwt
from flask import current_app, jsonify, request

from app.common.utils import load_text_config

from . import auth_bp

logger = logging.getLogger(__name__)


@auth_bp.route("/verify", methods=["POST"])
def verify_access_code():
    """Verifies the access code and returns a token and prompt config if valid."""
    if not request.json or "code" not in request.json:
        return jsonify({"error": "Access code is required."}), 400

    submitted_code = request.json.get("code", "")
    access_code = current_app.config.get("RECRUITER_ACCESS_CODE")
    secret_key = current_app.config.get("SECRET_KEY")

    if not access_code or not secret_key:
        logger.error("RECRUITER_ACCESS_CODE or SECRET_KEY is not configured.")
        return jsonify({"error": "Authentication system is not configured."}), 503

    # Use hmac.compare_digest for safe, constant-time string comparison
    # to mitigate timing attacks.
    is_valid = hmac.compare_digest(
        submitted_code.encode("utf-8"), access_code.encode("utf-8")
    )

    if not is_valid:
        logger.warning(f"Invalid access code attempt: '{submitted_code}'")
        return jsonify({"error": "Invalid access code."}), 401

    try:
        # Create the token payload
        payload = {
            "sub": "recruiter_access",
            "iat": datetime.datetime.now(datetime.timezone.utc),
            "exp": datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=1),
        }

        # Encode the token
        token = jwt.encode(payload, secret_key, algorithm="HS256")
        logger.info("Successfully generated JWT for recruiter access.")

        # Also send initial prompt configuration
        text_config = load_text_config()
        prompt_config = text_config.get("cli", {}).get("prompt", {})

        return jsonify({"token": token, "prompt": prompt_config}), 200

    except Exception as e:
        logger.error(f"Error generating JWT: {e}", exc_info=True)
        return jsonify({"error": "Could not generate access token."}), 500
