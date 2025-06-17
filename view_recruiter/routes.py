import logging
import os

from flask import abort, jsonify, request, send_from_directory

from common.decorators import token_required
from common.llm_services import get_llm_service
from common.utils import load_ai_context

from . import recruiter_bp

logger = logging.getLogger(__name__)


@recruiter_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serves static files specific to the Recruiter blueprint.

    Args:
        filename (str): The name of the file to serve from the static folder.

    Returns:
        Response: The requested static file or a 404 error if not found.
    """
    static_dir = os.path.join(recruiter_bp.root_path, "static")
    logger.debug(f"Serving Recruiter static file: {filename} from {static_dir}")
    try:
        return send_from_directory(static_dir, filename)
    except FileNotFoundError:
        logger.error(f"Static file not found: {os.path.join(static_dir, filename)}")
        abort(404)


@recruiter_bp.route("/api/chat", methods=["POST"])
@token_required
def handle_chat():
    """API endpoint to handle chat messages using a configurable LLM provider."""
    if not request.json or "message" not in request.json:
        logger.warning("Chat API called with invalid payload.")
        return jsonify({"error": "Invalid request. 'message' key is required."}), 400

    user_message = request.json["message"]
    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "Message must be a non-empty string."}), 400

    # Get the configured LLM service from the factory
    llm_service = get_llm_service()
    if not llm_service:
        logger.error("LLM service could not be initialized. Check configuration.")
        return (
            jsonify(
                {
                    "reply": "Error: The chatbot is not configured correctly. "
                    "Please check the server logs."
                }
            ),
            503,
        )

    ai_context = load_ai_context()
    if "Error:" in ai_context:
        logger.error(f"AI context could not be loaded: {ai_context}")
        return jsonify({"reply": ai_context}), 503

    SYSTEM_PROMPT = (
        "You are a helpful, professional, and friendly chatbot assistant "
        "representing Pablo Peitsch.\n"
        "Your goal is to answer questions about his skills, experience, and projects.\n"
        "Base your answers *only* on the professional context provided below.\n"
        "Do not invent information. If a question cannot be answered from the context, "
        "politely state that the information is not available in your knowledge base "
        "and suggest asking about his skills or projects.\n"
        "Keep your answers concise and to the point.\n"
        "Format your responses using basic Markdown "
        "(e.g., **bold** for emphasis, bullet points with `-`).\n\n"
        "Here is the context about Pablo Peitsch:\n"
        "---\n"
        "{context}\n"
        "---"
    ).format(context=ai_context)

    messages = [{"role": "user", "content": user_message}]

    # Use the service to get the response
    bot_reply = llm_service.get_chat_response(SYSTEM_PROMPT, messages)

    return jsonify({"reply": bot_reply})
