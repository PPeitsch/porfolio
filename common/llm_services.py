import abc
import json
import logging
from typing import Any, Dict, List, Optional, Type, Union

import anthropic
import openai
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
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
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
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
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
    LLM Service implementation for Google's Gemini models, based on the `genai`
    library.
    """

    def _initialize_client(self) -> genai.Client:
        logger.info("Initializing Google Gemini client (genai library).")
        return genai.Client(api_key=self.api_key)

    def get_chat_response(
        self,
        messages: List[Dict[str, Any]],
        system_prompt: str,
        tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Union[str, List[Dict[str, Any]]]:
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

        # The chat history should ONLY contain user/model turn messages.
        gemini_history = []
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
            # Correctly use the `system_instruction` parameter instead of
            # prepending the prompt to the user message history.
            response = self.client.models.generate_content(
                model="gemini-1.5-flash",
                contents=gemini_history,
                config=config,
                system_instruction=types.Content(
                    role="system", parts=[types.Part(text=system_prompt)]
                ),
            )

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
                logger.info(
                    f"Gemini requested tool calls: {[tc['name'] for tc in tool_calls]}"
                )
                return tool_calls

            logger.info("Gemini returned a text response.")
            return str(response.text).strip()

        except Exception as e:
            logger.error(f"Google Gemini API error (genai lib): {e}", exc_info=True)
            return "Sorry, I'm having trouble connecting to the AI service (Gemini)."


def get_llm_service() -> Optional[LLMService]:
    """
    Factory function to get the configured LLM service instance.
    """
    provider = current_app.config.get("LLM_PROVIDER")
    service_class: Optional[Type[LLMService]] = None
    api_key: Optional[str] = None

    if provider == "anthropic":
        api_key = current_app.config.get("ANTHROPIC_API_KEY")
        service_class = AnthropicService
    elif provider == "openai":
        api_key = current_app.config.get("OPENAI_API_KEY")
        service_class = OpenAIService
    elif provider == "gemini":
        api_key = current_app.config.get("GEMINI_API_KEY")
        service_class = GeminiService
    else:
        logger.error(f"Unsupported LLM_PROVIDER configured: '{provider}'")
        return None

    if not service_class:
        return None

    if not api_key:
        logger.error(
            f"LLM_PROVIDER is set to '{provider}', but the corresponding API key "
            f"({provider.upper()}_API_KEY) is missing."
        )
        return None

    try:
        return service_class(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to instantiate LLM service for '{provider}': {e}")
        return None
