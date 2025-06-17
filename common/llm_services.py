import abc
import logging
from typing import Dict, List, Optional, Type

import anthropic
import google.generativeai as genai
import openai
from flask import current_app

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
    def _initialize_client(self):
        """Initializes and returns the specific client for the LLM provider."""
        raise NotImplementedError

    @abc.abstractmethod
    def get_chat_response(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> str:
        """
        Sends a request to the LLM and returns the chat response.

        Args:
            system_prompt: The system-level instructions for the model.
            messages: A list of message dictionaries, e.g.,
                      [{'role': 'user', 'content': 'Hello!'}]

        Returns:
            A string containing the model's text response.
        """
        raise NotImplementedError


class AnthropicService(LLMService):
    """LLM Service implementation for Anthropic's Claude models."""

    def _initialize_client(self):
        logger.info("Initializing Anthropic client.")
        return anthropic.Anthropic(api_key=self.api_key)

    def get_chat_response(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> str:
        try:
            response = self.client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1024,
                system=system_prompt,
                messages=messages,
            )
            # Ensure the return type is explicitly a string for mypy
            return str(response.content[0].text)
        except anthropic.APIError as e:
            logger.error(f"Anthropic API error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service (Anthropic)."
        except Exception as e:
            logger.error(f"An unexpected error occurred with AnthropicService: {e}")
            return "An unexpected error occurred while processing your request."


class OpenAIService(LLMService):
    """LLM Service implementation for OpenAI's GPT models."""

    def _initialize_client(self):
        logger.info("Initializing OpenAI client.")
        return openai.OpenAI(api_key=self.api_key)

    def get_chat_response(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> str:
        # OpenAI expects the system prompt as the first message in the list
        all_messages = [{"role": "system", "content": system_prompt}] + messages
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=all_messages,
                max_tokens=1024,
            )
            # response.choices[0].message.content can be None, ensure we return a string
            return str(response.choices[0].message.content or "")
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service (OpenAI)."
        except Exception as e:
            logger.error(f"An unexpected error occurred with OpenAIService: {e}")
            return "An unexpected error occurred while processing your request."


class GeminiService(LLMService):
    """LLM Service implementation for Google's Gemini models."""

    def _initialize_client(self):
        logger.info("Initializing Google Gemini client.")
        genai.configure(api_key=self.api_key)
        # We create the model object here, which acts as the 'client'
        return genai.GenerativeModel("gemini-pro")

    def get_chat_response(
        self, system_prompt: str, messages: List[Dict[str, str]]
    ) -> str:
        gemini_messages = []
        for msg in messages:
            role = "model" if msg["role"] == "assistant" else "user"
            gemini_messages.append({"role": role, "parts": [msg["content"]]})

        if not gemini_messages:
            return "Error: No user message provided."

        try:
            model = genai.GenerativeModel(
                "gemini-pro", system_instruction=system_prompt
            )
            response = model.generate_content(gemini_messages)
            # Ensure the return type is explicitly a string for mypy
            return str(response.text)
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service (Gemini)."


def get_llm_service() -> Optional[LLMService]:
    """
    Factory function to get the configured LLM service instance.
    """
    provider = current_app.config.get("LLM_PROVIDER")
    # Explicitly type service_class to hold a type that is a subclass of LLMService
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
        # This case is redundant due to the 'else' above but makes logic clearer
        return None

    if not api_key:
        logger.error(
            f"LLM_PROVIDER is set to '{provider}', but the corresponding API key "
            f"({provider.upper()}_API_KEY) is missing."
        )
        return None

    try:
        # mypy now knows service_class is not None here
        return service_class(api_key=api_key)
    except Exception as e:
        logger.error(f"Failed to instantiate LLM service for '{provider}': {e}")
        return None
