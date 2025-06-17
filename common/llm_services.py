import abc
import logging
from typing import Dict, List

import anthropic
import google.generativeai as genai
import openai

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
            return response.content[0].text
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
            return response.choices[0].message.content or ""
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
        # Gemini expects the system prompt and history differently.
        # It's managed via the chat session.
        chat_session = self.client.start_chat(
            history=[{"role": "user", "parts": [system_prompt]}]
        )
        # The last message is the current user prompt.
        user_prompt = messages[-1]["content"] if messages else ""

        if not user_prompt:
            return "Error: No user message provided."

        try:
            response = chat_session.send_message(user_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Google Gemini API error: {e}")
            return "Sorry, I'm having trouble connecting to the AI service (Gemini)."
