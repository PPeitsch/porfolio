import logging
from functools import wraps

import jwt
from flask import current_app, jsonify, request

logger = logging.getLogger(__name__)


def token_required(f):
    """A decorator to protect routes with JWT authentication."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = None
        # Check for the 'Authorization' header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            # The header should be in the format 'Bearer <token>'
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                logger.warning(
                    "Malformed Authorization header. 'Bearer' token not found."
                )
                return jsonify({"error": "Malformed Authorization header."}), 401

        if not token:
            logger.warning("Authorization token is missing.")
            return jsonify({"error": "Authorization token is missing."}), 401

        secret_key = current_app.config.get("SECRET_KEY")
        if not secret_key:
            logger.error("SECRET_KEY is not configured for JWT validation.")
            return jsonify({"error": "Server configuration error."}), 500

        try:
            # Decode the token to validate it. The payload is not used in this case.
            jwt.decode(token, secret_key, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            logger.warning("Token has expired.")
            return jsonify({"error": "Token has expired."}), 401
        except jwt.InvalidTokenError:
            # Base class of every decoding error PyJWT raises.
            logger.warning("Invalid token provided.")
            return jsonify({"error": "Invalid token."}), 401

        # If the token is valid, proceed with the original function
        return f(*args, **kwargs)

    return decorated_function
