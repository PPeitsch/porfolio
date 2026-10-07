import json
import logging
import os
from typing import Any, Dict, List

from flask import abort, current_app, jsonify, request, send_from_directory

from app.common.decorators import token_required
from app.common.exceptions import LLMConfigurationError, LLMServiceError, PortfolioError
from app.common.i18n import get_locale, language_name, t
from app.common.llm_services import ToolCall, get_llm_service
from app.common.llm_tools import TOOL_MAP, get_tool_definitions
from app.common.llm_usage import visitor_id
from app.common.rate_limit import client_ip, get_limiter
from app.common.utils import load_cv_data, load_system_prompt

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


# Only this many earlier messages are sent back to the model.
MAX_HISTORY_MESSAGES = 20
# Each of them cut to this many characters. The history comes from the
# browser, so without a cap it could carry any amount of text to the model;
# this leaves room for the longest replies (max_tokens 1024).
MAX_HISTORY_MESSAGE_CHARS = 8000


def _clean_history(history: Any) -> List[Dict[str, str]]:
    """Keeps the last user/assistant text turns of the client's history.

    The history comes from the browser, so anything else (system prompts,
    tool messages, other fields) is dropped.
    """
    if not isinstance(history, list):
        return []
    cleaned = [
        {"role": item["role"], "content": item["content"][:MAX_HISTORY_MESSAGE_CHARS]}
        for item in history
        if isinstance(item, dict)
        and item.get("role") in ("user", "assistant")
        and isinstance(item.get("content"), str)
    ]
    return cleaned[-MAX_HISTORY_MESSAGES:]


def _run_tool(call: ToolCall) -> str:
    """Runs a tool the model asked for and returns its result as JSON."""
    tool_function = TOOL_MAP.get(call.name)
    if tool_function is None:
        return json.dumps({"error": f"Tool '{call.name}' not found."})
    try:
        return json.dumps(tool_function(**call.arguments), default=str)
    except TypeError as e:
        # The model sent arguments the tool does not take.
        logger.warning(f"Bad arguments for tool '{call.name}': {e}")
        return json.dumps({"error": f"Invalid arguments for tool '{call.name}'."})
    except PortfolioError as e:
        logger.error(f"Error executing tool '{call.name}': {e}")
        return json.dumps({"error": f"Error executing tool: {e}"})


@recruiter_bp.route("/api/chat", methods=["POST"])
@token_required
def handle_chat():
    """API endpoint to handle chat messages using function calling.

    The model may ask for tools several times before answering; each round's
    tool results are sent back to it, up to LLM_MAX_TOOL_ROUNDS rounds. The
    history returned to the client only holds the user/assistant text turns.
    """
    if not request.json or "message" not in request.json:
        logger.warning("Chat API called with invalid payload.")
        return jsonify({"error": "Invalid request. 'message' key is required."}), 400

    user_message = request.json["message"]
    if not isinstance(user_message, str) or not user_message.strip():
        return jsonify({"error": "Message must be a non-empty string."}), 400

    max_chars = int(current_app.config.get("CHAT_MAX_MESSAGE_CHARS", 2000))
    if len(user_message) > max_chars:
        return (
            jsonify(
                {
                    "error": f"Message is longer than {max_chars} characters.",
                    "error_code": "message_too_long",
                    "max_chars": max_chars,
                }
            ),
            413,
        )

    ip = client_ip()
    limiter = get_limiter("CHAT_RATE_LIMITS")
    wait = limiter.retry_after(ip)
    if wait:
        logger.warning(f"Chat message from {ip} refused: rate limit reached.")
        response = jsonify(
            {
                "error": "Too many messages.",
                "error_code": "rate_limited",
                "retry_after": wait,
            }
        )
        response.headers["Retry-After"] = str(wait)
        return response, 429
    limiter.hit(ip)

    try:
        llm_service = get_llm_service()
    except LLMConfigurationError as e:
        logger.error(f"LLM service could not be initialized: {e}")
        return jsonify({"reply": t("chat.reply_not_configured")}), 503

    owner_name = load_cv_data().get("name", "the portfolio owner")
    system_prompt = load_system_prompt().replace("{name}", owner_name)
    system_prompt += "\n\n" + t(
        "chat.language_hint", language=language_name(get_locale())
    )
    tools = get_tool_definitions(owner_name)

    messages: List[Dict[str, Any]] = _clean_history(request.json.get("history")) + [
        {"role": "user", "content": user_message}
    ]
    conversation: List[Dict[str, Any]] = list(messages)
    max_rounds = int(current_app.config.get("LLM_MAX_TOOL_ROUNDS", 5))

    visitor = visitor_id(ip)
    for _ in range(max_rounds + 1):
        try:
            response = llm_service.get_chat_response(
                messages=conversation,
                system_prompt=system_prompt,
                tools=tools,
                visitor=visitor,
            )
        except LLMServiceError:
            return jsonify({"reply": t("chat.reply_unavailable")}), 502

        if not response.tool_calls:
            reply = response.content.strip() or t("chat.reply_empty")
            return jsonify(
                {
                    "reply": reply,
                    "history": messages + [{"role": "assistant", "content": reply}],
                }
            )

        conversation.append(response.message)
        for call in response.tool_calls:
            conversation.append(
                {"role": "tool", "tool_call_id": call.id, "content": _run_tool(call)}
            )

    logger.warning(f"The model kept asking for tools after {max_rounds} rounds.")
    reply = t("chat.reply_too_many_rounds")
    return jsonify(
        {
            "reply": reply,
            "history": messages + [{"role": "assistant", "content": reply}],
        }
    )
