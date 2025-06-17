import abc
import logging
from typing import Dict

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
        self, system_prompt: str, messages: list[Dict[str, str]]
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
