from unittest.mock import MagicMock, patch

import pytest
from httpx import Request
from openai import APIError

from common.llm_services import (
    AnthropicService,
    GeminiService,
    LLMService,
    OpenAIService,
    get_llm_service,
)


# --- Test Abstract Base Class ---
def test_llm_service_abc_requires_api_key():
    """Test that instantiating a service without an API key raises ValueError."""
    with pytest.raises(ValueError, match="requires an API key"):
        # Create a dummy concrete class for testing the ABC
        class DummyService(LLMService):
            def _initialize_client(self):
                return None

            def get_chat_response(self, messages, system_prompt, tools=None):
                return "dummy"

        DummyService(api_key=None)


# --- Test AnthropicService ---
@patch("anthropic.Anthropic")
def test_anthropic_service_success(MockAnthropic):
    """Test AnthropicService successful text response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="Hello Anthropic")]
    mock_response.stop_reason = "end_turn"
    mock_client.messages.create.return_value = mock_response
    MockAnthropic.return_value = mock_client

    service = AnthropicService(api_key="fake_key")
    response = service.get_chat_response(messages=[], system_prompt="")

    assert response == "Hello Anthropic"
    mock_client.messages.create.assert_called_once()


@patch("anthropic.Anthropic")
def test_anthropic_service_tool_use(MockAnthropic):
    """Test AnthropicService tool use response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="tool_use", id="t1", name="n1", input={})]
    mock_response.stop_reason = "tool_use"
    mock_client.messages.create.return_value = mock_response
    MockAnthropic.return_value = mock_client

    service = AnthropicService(api_key="fake_key")
    response = service.get_chat_response(messages=[], system_prompt="")

    assert isinstance(response, list)
    assert response[0]["id"] == "t1"


# --- Test OpenAIService ---
@patch("openai.OpenAI")
def test_openai_service_success(MockOpenAI):
    """Test OpenAIService successful text response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "Hello OpenAI"
    mock_response.choices[0].message.tool_calls = None
    mock_client.chat.completions.create.return_value = mock_response
    MockOpenAI.return_value = mock_client

    service = OpenAIService(api_key="fake_key")
    response = service.get_chat_response(messages=[], system_prompt="")

    assert response == "Hello OpenAI"
    mock_client.chat.completions.create.assert_called_once()


@patch("openai.OpenAI")
def test_openai_service_api_error(MockOpenAI):
    """Test OpenAIService API error handling."""
    mock_client = MagicMock()
    # The APIError requires a request object.
    mock_client.chat.completions.create.side_effect = APIError(
        "Test error", request=Request(method="POST", url="http://test.url"), body=None
    )
    MockOpenAI.return_value = mock_client

    service = OpenAIService(api_key="fake_key")
    response = service.get_chat_response(messages=[], system_prompt="")

    assert "Sorry" in response
    assert "(OpenAI)" in response


# --- Test GeminiService ---
@patch("common.llm_services.genai.Client")
def test_gemini_service_success(MockGenAIClient):
    """Test GeminiService successful text response."""
    # Setup the nested mock structure: Client -> models -> generate_content
    mock_client_instance = MagicMock()
    mock_models_object = MagicMock()
    mock_response = MagicMock()
    mock_part = MagicMock()

    # Configure the part to represent a text-only response.
    # The .function_call attribute must be explicitly set to a falsy value (e.g., None)
    # so that the `if part.function_call:` check in the implementation fails as expected
    mock_part.text = "Hello Gemini"
    mock_part.function_call = None

    # Configure the full response object to contain the text-only part
    mock_response.text = "Hello Gemini"
    mock_response.candidates = [MagicMock()]
    mock_response.candidates[0].content.parts = [mock_part]

    # Configure the mock client hierarchy
    mock_models_object.generate_content.return_value = mock_response
    mock_client_instance.models = mock_models_object
    MockGenAIClient.return_value = mock_client_instance

    # Now, instantiate the service. It will use the mocked client.
    service = GeminiService(api_key="fake_key")
    response = service.get_chat_response(messages=[], system_prompt="")

    # Assert that the correct text response is returned
    assert response == "Hello Gemini"
    mock_models_object.generate_content.assert_called_once()


# --- Test get_llm_service Factory ---
@patch("common.llm_services.AnthropicService")
@patch("common.llm_services.OpenAIService")
@patch("common.llm_services.GeminiService")
def test_get_llm_service_factory(MockGemini, MockOpenAI, MockAnthropic, app):
    """Test the factory function for creating LLM services."""
    # Test Anthropic
    with app.app_context():
        app.config["LLM_PROVIDER"] = "anthropic"
        app.config["ANTHROPIC_API_KEY"] = "key1"
        get_llm_service()
        MockAnthropic.assert_called_once_with(api_key="key1")

    # Reset mocks for the next case
    MockAnthropic.reset_mock()

    # Test OpenAI
    with app.app_context():
        app.config["LLM_PROVIDER"] = "openai"
        app.config["OPENAI_API_KEY"] = "key2"
        get_llm_service()
        MockOpenAI.assert_called_once_with(api_key="key2")

    MockOpenAI.reset_mock()

    # Test Gemini
    with app.app_context():
        app.config["LLM_PROVIDER"] = "gemini"
        app.config["GEMINI_API_KEY"] = "key3"
        get_llm_service()
        MockGemini.assert_called_once_with(api_key="key3")

    MockGemini.reset_mock()

    # Test unsupported provider
    with app.app_context():
        app.config["LLM_PROVIDER"] = "unsupported"
        service = get_llm_service()
        assert service is None

    # Test missing API key
    with app.app_context():
        app.config["LLM_PROVIDER"] = "openai"
        app.config["OPENAI_API_KEY"] = None
        service = get_llm_service()
        assert service is None
        MockOpenAI.assert_not_called()  # Ensure constructor was not called
