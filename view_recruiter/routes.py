import json
import logging
import os
from typing import Any, Dict, List

from flask import abort, jsonify, request, send_from_directory

from common.decorators import token_required
from common.llm_services import get_llm_service
from common.llm_tools import TOOL_DEFINITIONS, TOOL_MAP

from . import recruiter_bp

logger = logging.getLogger(__name__)


@recruiter_bp.route("/static/<path:filename>")
def static_files(filename):
    """Serves static files specific to the Recruiter blueprint."""
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
    """API endpoint to handle chat messages using function calling."""
    if not request.json or "message" not in request.json:
        logger.warning("Chat API called with invalid payload.")
        return jsonify({"error": "Invalid request. 'message' key is required."}), 400

    user_message = request.json["message"]
    chat_history = request.json.get("history", [])

    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "Message must be a non-empty string."}), 400

    llm_service = get_llm_service()
    if not llm_service:
        logger.error("LLM service could not be initialized. Check configuration.")
        return jsonify({"reply": "Error: Chatbot not configured correctly."}), 503

    SYSTEM_PROMPT = (
        "You are a helpful, professional, and friendly chatbot assistant for "
        "Pablo Peitsch. Your goal is to answer questions about his skills, "
        "experience, and projects by using the available tools. Do not invent "
        "information. If a question cannot be answered with the tools, politely "
        "state that. Format responses using basic Markdown."
    )

    # Start with the current user message
    messages: List[Dict[str, Any]] = chat_history + [
        {"role": "user", "content": user_message}
    ]

    # --- Tool-use loop ---
    while True:
        response = llm_service.get_chat_response(
            messages=messages, system_prompt=SYSTEM_PROMPT, tools=TOOL_DEFINITIONS
        )

        if isinstance(response, str):
            # Final text response from LLM
            return jsonify(
                {
                    "reply": response,
                    "history": messages + [{"role": "assistant", "content": response}],
                }
            )

        if isinstance(response, list) and len(response) > 0:
            # It's a tool call request
            tool_calls = response
            # Add the assistant's tool request to the message history
            messages.append({"role": "assistant", "content": tool_calls})

            tool_outputs = []
            for tool_call in tool_calls:
                tool_name = tool_call.get("name")
                tool_input_str = tool_call.get("input", "{}")
                tool_id = tool_call.get("id")

                if tool_name in TOOL_MAP:
                    try:
                        # Some LLMs return arguments as a JSON string, others as a dict
                        tool_args = (
                            json.loads(tool_input_str)
                            if isinstance(tool_input_str, str)
                            else tool_input_str
                        )
                        tool_function = TOOL_MAP[tool_name]
                        result = tool_function(**tool_args)
                        tool_outputs.append(
                            {
                                "tool_use_id": tool_id,
                                "content": json.dumps(result),
                            }
                        )
                    except Exception as e:
                        logger.error(f"Error executing tool '{tool_name}': {e}")
                        tool_outputs.append(
                            {
                                "tool_use_id": tool_id,
                                "content": f"Error executing tool: {e}",
                                "is_error": True,
                            }
                        )
                else:
                    tool_outputs.append(
                        {
                            "tool_use_id": tool_id,
                            "content": f"Error: Tool '{tool_name}' not found.",
                            "is_error": True,
                        }
                    )
            # Add tool results to the message history for the next turn
            messages.append(
                {"role": "user", "content": tool_outputs, "type": "tool_result"}
            )
            # Continue the loop to get the final text response from the LLM
        else:
            # Unexpected response from LLM service
            logger.error(f"Unexpected LLM response type: {type(response)}")
            return jsonify({"reply": "An unexpected error occurred."}), 500
