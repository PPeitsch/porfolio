import abc
import json
import logging
from typing import Any, Dict, List, Optional, Tuple, Type, Union, cast

import anthropic
import openai
import requests
from flask import current_app
from google import genai
from google.genai import types

logger = logging.getLogger(__name__)


class LLMService(abc.ABC):
    """Abstract base class for Large Language Model services.

    This class defines a common interface for interacting with different LLM
    providers. Each concrete implementation must provide a method to get a
    chat response.
    """

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError(
                f"{self.__class__.__name__} requires an API key, but none was provided."
            )
        self.api_key = api_key
        self.client = self._initialize_client()

    @abc.abstractmethod
    def _initialize_client(self) -> Any:
        """Initializes and returns the specific client for the LLM provider."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_chat_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
        """
        Sends a request to the LLM and returns the chat response.

        The response can be a simple string or a list of tool use requests.

        Args:
            messages: A list of message dictionaries, including user, assistant,
                      and tool messages.
            system_prompt: The system-level instructions for the model.
            tools: An optional list of tool definitions available to the model.

        Returns:
            - A string containing the model's text response.
            - A list of dictionaries, where each dict is a tool call request.
        """
        raise NotImplementedError


class AnthropicService(LLMService):
    """LLM Service implementation for Anthropic's Claude models."""

    def _initialize_client(self) -> anthropic.Anthropic:
        logger.info("Initializing Anthropic client.")
        return anthropic.Anthropic(api_key=self.api_key)

    def get_chat_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
        try:
            model_name = current_app.config.get("ANTHROPIC_MODEL")
            response = self.client.messages.create(
                model=model_name,
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
                tools=tools or [],
                tool_choice={"type": "auto"},
            )

            # Check if the model wants to use a tool
            if response.stop_reason == "tool_use":
                tool_calls = []
                for content_block in response.content:
                    if content_block.type == "tool_use":
                        tool_calls.append(
                            {
                                "id": content_block.id,
                                "name": content_block.name,
                                "input": content_block.input,
                            }
                        )
                return tool_calls

            # Otherwise, return the text content
            text_content = ""
            for content_block in response.content:
                if content_block.type == "text":
                    text_content += content_block.text
            return text_content.strip()

        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service (Anthropic)."
        except Exception as e:
            logger.error(f"An unexpected error occurred with AnthropicService: {e}")
            return "An unexpected error occurred while processing your request."


class OpenAIService(LLMService):
    """LLM Service implementation for OpenAI's GPT models."""

    def _initialize_client(self) -> openai.OpenAI:
        logger.info("Initializing OpenAI client.")
        return openai.OpenAI(api_key=self.api_key)

    def get_chat_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
        all_messages = [{"role": "system", "content": system_prompt}] + messages
        try:
            model_name = current_app.config.get("OPENAI_MODEL")
            response = self.client.chat.completions.create(
                model=model_name,
                messages=all_messages,
                tools=tools,
                tool_choice="auto" if tools else None,
                max_tokens=1024,
            )
            response_message = response.choices[0].message

            # Check if the model wants to call a tool
            if response_message.tool_calls:
                return [
                    {
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "input": tool_call.function.arguments,
                    }
                    for tool_call in response_message.tool_calls
                ]

            return str(response_message.content or "")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service (OpenAI)."
        except Exception as e:
            logger.error(f"An unexpected error occurred with OpenAIService: {e}")
            return "An unexpected error occurred while processing your request."


class GeminiService(LLMService):
    """
    LLM Service implementation for Google's Gemini models.

    Supports direct API calls via the `genai` library and can route requests
    through a configurable HTTP proxy for environments where direct access
    is restricted.
    """

    def _initialize_client(self) -> Optional[genai.Client]:
        # Defer client initialization to the chat response method, as it's not
        # needed if we are using the proxy.
        if not current_app.config.get("GEMINI_PROXY_URL"):
            logger.info("Initializing Google Gemini client (genai library).")
            return genai.Client(api_key=self.api_key)
        logger.info(
            "Google Gemini client configured to use proxy. Skipping genai init."
        )
        return None

    def get_chat_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
        proxy_url = current_app.config.get("GEMINI_PROXY_URL")

        if proxy_url:
            # --- Proxy Logic ---
            logger.info(f"Routing Gemini request through proxy: {proxy_url}")
            payload = {
                "messages": messages,
                "system_prompt": system_prompt,
                "tools": tools,
            }
            try:
                response = requests.post(proxy_url, json=payload, timeout=120)
                response.raise_for_status()  # Raise an exception for bad status codes
                # Cast the JSON response to the expected type to satisfy mypy
                result = cast(
                    Union[str, List[Dict[str, Any]]],
                    response.json().get("reply", "Error: No reply from proxy."),
                )
                return result
            except requests.exceptions.RequestException as e:
                logger.error(f"Gemini proxy request failed: {e}")
                return (
                    "Sorry, there was an error communicating with the AI service proxy."
                )
            except Exception as e:
                logger.error(f"An unexpected error occurred with Gemini proxy: {e}")
                return (
                    "An unexpected error occurred while processing your proxy request."
                )

        # --- Direct API Logic (genai library) ---
        if not self.client:
            logger.error("Gemini client is not initialized for direct API call.")
            return "Error: Gemini client is not configured."

        gemini_tools = None
        if tools:
            function_declarations = [
                types.FunctionDeclaration(
                    name=tool_def["name"],
                    description=tool_def["description"],
                    parameters=tool_def.get("input_schema"),
                )
                for tool_def in tools
            ]
            gemini_tools = [types.Tool(function_declarations=function_declarations)]

        gemini_history = [
            types.Content(role="user", parts=[types.Part(text=system_prompt)])
        ]
        for msg in messages:
            role = "user" if msg["role"] == "user" else "model"
            content = msg.get("content")

            if msg.get("type") == "tool_result":
                tool_results = msg.get("content", [])
                tool_response_parts = [
                    types.Part.from_function_response(
                        name=tool_result["tool_use_id"],
                        response={"result": json.loads(tool_result["content"])},
                    )
                    for tool_result in tool_results
                ]
                gemini_history.append(
                    types.Content(role="user", parts=tool_response_parts)
                )
            elif isinstance(content, list):
                tool_call_parts = [
                    types.Part(
                        function_call=types.FunctionCall(
                            name=c["name"], args=c["input"]
                        )
                    )
                    for c in content
                ]
                gemini_history.append(
                    types.Content(role="model", parts=tool_call_parts)
                )
            else:
                gemini_history.append(
                    types.Content(role=role, parts=[types.Part(text=str(content))])
                )

        config = (
            types.GenerateContentConfig(tools=gemini_tools) if gemini_tools else None
        )

        try:
            model_name = current_app.config.get("GEMINI_MODEL")
            response = self.client.models.generate_content(
                model=model_name,
                contents=gemini_history,
                config=config,
            )

            # Type guard to ensure response has the expected structure
            if not isinstance(response, types.GenerateContentResponse):
                logger.error(f"Unexpected response type from Gemini: {type(response)}")
                return "An unexpected error occurred with the AI service."

            if not response.candidates:
                logger.error("No response candidates received from Gemini.")
                return "An error occurred while communicating with the AI service."

            candidate_parts = response.candidates[0].content.parts
            tool_calls = []
            has_function_call = False
            for part in candidate_parts:
                if part.function_call:
                    has_function_call = True
                    fc = part.function_call
                    tool_calls.append(
                        {
                            "id": fc.name,
                            "name": fc.name,
                            "input": dict(fc.args),
                        }
                    )

            if has_function_call:
                return tool_calls

            return str(response.text).strip()

        except Exception as e:
            logger.error(f"Google Gemini API error (genai lib): {e}", exc_info=True)
            return "Sorry, I'm having trouble connecting to the AI service (Gemini)."


def get_llm_service() -> Optional[LLMService]:
    """
    Factory function to get the configured LLM service instance.
    Uses a map for cleaner, more scalable provider selection.
    """
    provider = current_app.config.get("LLM_PROVIDER", "").lower()

    service_map: Dict[str, Tuple[Type[LLMService], str]] = {
        "anthropic": (AnthropicService, "ANTHROPIC_API_KEY"),
        "openai": (OpenAIService, "OPENAI_API_KEY"),
        "gemini": (GeminiService, "GEMINI_API_KEY"),
    }

    if provider not in service_map:
        logger.error(f"Unsupported or missing LLM_PROVIDER configured: '{provider}'")
        return None

    service_class, api_key_name = service_map[provider]
    api_key = current_app.config.get(api_key_name)

    if not api_key:
        logger.error(
            f"LLM_PROVIDER is set to '{provider}', but the corresponding API key "
            f"'{api_key_name}' is missing."
        )
        return None

    try:
        # At this point, api_key is guaranteed to be a str, satisfying mypy.
        return service_class(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to instantiate LLM service for '{provider}': {e}")
        return None
