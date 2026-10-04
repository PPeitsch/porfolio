import json
import logging
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional, Tuple

from flask import current_app

from app.common.exceptions import LLMConfigurationError, LLMServiceError

# LiteLLM downloads its model price map at import time unless told to use the
# copy it ships with. The app does not need live prices, and startup should not
# depend on the network.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import litellm  # noqa: E402

logger = logging.getLogger(__name__)

# LiteLLM logs every call at INFO and prints a help banner on each error;
# keep only its warnings and errors.
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
litellm.suppress_debug_info = True

# Model settings of the provider-specific configuration used before LLM_MODEL.
LEGACY_MODEL_SETTINGS = {
    "anthropic": "ANTHROPIC_MODEL",
    "openai": "OPENAI_MODEL",
    "gemini": "GEMINI_MODEL",
}


@dataclass
class ToolCall:
    """A tool the model asked to run, with its arguments already parsed."""

    id: str
    name: str
    arguments: Dict[str, Any]


@dataclass
class ChatResponse:
    """One model turn: either text or tool calls.

    `message` is the assistant turn in OpenAI format, ready to be appended to
    the conversation before the tool results.
    """

    content: str = ""
    tool_calls: List[ToolCall] = field(default_factory=list)
    message: Dict[str, Any] = field(default_factory=dict)


def _parse_arguments(raw: Any) -> Dict[str, Any]:
    """Tool arguments arrive as a JSON string; anything unusable becomes {}."""
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(raw or "{}")
    except (TypeError, ValueError):
        logger.warning(f"Could not parse tool arguments: {raw!r}")
        return {}
    return parsed if isinstance(parsed, dict) else {}


class LLMService:
    """Chat completions through LiteLLM, for any provider it supports.

    The model string selects the provider, e.g. "anthropic/claude-haiku-4-5",
    "openrouter/anthropic/claude-haiku-4.5", "gemini/gemini-2.5-flash" or
    "ollama/llama3.1". Messages and tools use the OpenAI format; LiteLLM
    translates them for each provider.
    """

    def __init__(
        self,
        model: str,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: float = 30.0,
        max_tokens: int = 1024,
        reasoning_effort: Optional[str] = None,
        fallbacks: Optional[List[Tuple[str, Optional[str]]]] = None,
    ):
        self.model = model
        self.api_key = api_key
        self.api_base = api_base
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.reasoning_effort = reasoning_effort
        self.fallbacks = fallbacks or []

    def get_chat_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> ChatResponse:
        """Sends the conversation to the model and returns its next turn.

        Args:
            messages: The conversation in OpenAI format (user, assistant and
                      tool messages), without the system prompt.
            system_prompt: The system-level instructions for the model.
            tools: Optional tool definitions in OpenAI format.

        Returns:
            ChatResponse: The text of the reply, or the tool calls to run.

        Raises:
            LLMServiceError: If the provider call fails.
        """
        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "system", "content": system_prompt}] + messages,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
        }
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"
        if self.api_key:
            kwargs["api_key"] = self.api_key
        if self.api_base:
            kwargs["api_base"] = self.api_base
        if self.reasoning_effort:
            # Reasoning tokens count against max_tokens; "none" turns it off
            # in the models that allow it. LiteLLM translates it per provider.
            kwargs["reasoning_effort"] = self.reasoning_effort
            kwargs["allowed_openai_params"] = ["reasoning_effort"]
        if self.fallbacks:
            # Tried in order when the model fails (down, rate-limited, error),
            # each with its own reasoning effort: a fallback must not inherit
            # the main model's, since some models cannot turn reasoning off.
            kwargs["fallbacks"] = [
                {
                    "model": name,
                    "reasoning_effort": effort,
                    "allowed_openai_params": ["reasoning_effort"] if effort else [],
                }
                for name, effort in self.fallbacks
            ]

        # LiteLLM surfaces provider failures with many unrelated exception
        # types (its own, the provider SDK's, network errors), so all of them
        # are turned into LLMServiceError here, at the boundary.
        try:
            response = litellm.completion(**kwargs)
            message = response.choices[0].message
        except Exception as e:
            logger.error(f"LLM request to '{self.model}' failed: {e}")
            raise LLMServiceError(str(e)) from e

        content = message.content or ""
        tool_calls = [
            ToolCall(
                id=call.id,
                name=call.function.name,
                arguments=_parse_arguments(call.function.arguments),
            )
            for call in (message.tool_calls or [])
        ]

        assistant_message: Dict[str, Any] = {"role": "assistant", "content": content}
        if tool_calls:
            assistant_message["tool_calls"] = [
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.name,
                        "arguments": json.dumps(call.arguments),
                    },
                }
                for call in tool_calls
            ]
        return ChatResponse(
            content=content, tool_calls=tool_calls, message=assistant_message
        )


def parse_fallbacks(setting: Any) -> List[Tuple[str, Optional[str]]]:
    """Parses LLM_FALLBACK_MODELS: comma-separated models, each optionally
    with "@<reasoning effort>", e.g. "openrouter/deepseek/deepseek-v4-flash@none".
    """
    fallbacks: List[Tuple[str, Optional[str]]] = []
    for entry in str(setting or "").split(","):
        name, _, effort = entry.strip().partition("@")
        if name.strip():
            fallbacks.append((name.strip(), effort.strip() or None))
    return fallbacks


def resolve_model(config: Mapping[str, Any]) -> Optional[str]:
    """Returns the LiteLLM model string from the app configuration.

    LLM_MODEL wins. Without it, the older LLM_PROVIDER + <PROVIDER>_MODEL
    settings are turned into "<provider>/<model>".
    """
    if config.get("LLM_MODEL"):
        return str(config["LLM_MODEL"])
    provider = str(config.get("LLM_PROVIDER") or "").lower()
    model_setting = LEGACY_MODEL_SETTINGS.get(provider)
    if model_setting and config.get(model_setting):
        return f"{provider}/{config[model_setting]}"
    return None


def get_llm_service() -> LLMService:
    """Builds the LLM service from the app configuration.

    Raises:
        LLMConfigurationError: If no model is configured or the provider's
                               API key is missing.
    """
    config = current_app.config
    if config.get("GEMINI_PROXY_URL"):
        logger.warning(
            "GEMINI_PROXY_URL is no longer supported and is ignored; "
            "set LLM_MODEL instead (e.g. an 'openrouter/...' model)."
        )

    model = resolve_model(config)
    if not model:
        raise LLMConfigurationError(
            "No LLM model configured. Set LLM_MODEL in the environment."
        )

    fallbacks = parse_fallbacks(config.get("LLM_FALLBACK_MODELS"))
    api_key = config.get("LLM_API_KEY")
    api_base = config.get("LLM_API_BASE")
    if not api_key:
        for name in [model] + [fallback for fallback, _ in fallbacks]:
            missing = litellm.validate_environment(model=name, api_base=api_base).get(
                "missing_keys", []
            )
            if missing:
                raise LLMConfigurationError(
                    f"LLM model '{name}' needs {', '.join(missing)} in the "
                    "environment (or LLM_API_KEY)."
                )

    return LLMService(
        model=model,
        api_key=api_key,
        api_base=api_base,
        timeout=float(config.get("LLM_TIMEOUT", 30)),
        max_tokens=int(config.get("LLM_MAX_TOKENS") or 1024),
        reasoning_effort=config.get("LLM_REASONING_EFFORT") or None,
        fallbacks=fallbacks,
    )
