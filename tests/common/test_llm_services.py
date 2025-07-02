import json
from unittest.mock import MagicMock, patch

import pytest

# Import the actual Anthropic APIError to be caught correctly
from anthropic import APIError as AnthropicAPIError
from httpx import Request
from openai import APIError

from app.common.llm_services import (
    AnthropicService,
    GeminiService,
    LLMService,
    OpenAIService,
    get_llm_service,
)

google_genai_mock = MagicMock()
try:
    from google.genai.errors import ClientError

    google_genai_mock.errors.ClientError = ClientError
except ImportError:
    google_genai_mock.errors.ClientError = type("ClientError", (Exception,), {})


def test_llm_service_abc_methods(app):
    """Test that ABC methods raise NotImplementedError."""

    class BadService(LLMService):
        # Missing _initialize_client implementation
        def get_chat_response(self, messages, system_prompt, tools=None):
            pass

    class AnotherBadService(LLMService):
        def _initialize_client(self):
            return None  # Implemented

        # Missing get_chat_response implementation

    with app.app_context():
        with pytest.raises(TypeError, match="Can't instantiate abstract class"):
            BadService(api_key="key")

        service = AnotherBadService(api_key="key")
        with pytest.raises(NotImplementedError):
            service.get_chat_response(messages=[], system_prompt="")


@patch("app.common.llm_services.anthropic.Anthropic")
def test_anthropic_service_success(MockAnthropic, app):
    """Test AnthropicService successful text response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="text", text="Hello Anthropic")]
    mock_response.stop_reason = "end_turn"
    mock_client.messages.create.return_value = mock_response
    MockAnthropic.return_value = mock_client

    with app.app_context():
        service = AnthropicService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert response == "Hello Anthropic"


@patch("app.common.llm_services.anthropic.Anthropic")
def test_anthropic_service_tool_use(MockAnthropic, app):
    """Test AnthropicService tool use response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    tool_call = MagicMock(type="tool_use", id="t1", input={})
    tool_call.name = "get_weather"
    mock_response.content = [tool_call]
    mock_response.stop_reason = "tool_use"
    mock_client.messages.create.return_value = mock_response
    MockAnthropic.return_value = mock_client

    with app.app_context():
        service = AnthropicService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert isinstance(response, list)
    assert response[0]["name"] == "get_weather"


@patch("app.common.llm_services.anthropic.Anthropic")
def test_anthropic_service_api_error(MockAnthropic, app):
    """Test AnthropicService API error handling."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = AnthropicAPIError(
        "Anthropic error", request=Request("POST", "http://test"), body=None
    )
    MockAnthropic.return_value = mock_client

    with app.app_context():
        service = AnthropicService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "Sorry" in response and "(Anthropic)" in response


@patch("app.common.llm_services.anthropic.Anthropic")
def test_anthropic_service_unexpected_response(MockAnthropic, app):
    """Test AnthropicService with an unexpected response structure."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.content = [MagicMock(type="unexpected_type")]
    mock_response.stop_reason = "end_turn"
    mock_client.messages.create.return_value = mock_response
    MockAnthropic.return_value = mock_client

    with app.app_context():
        service = AnthropicService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")
    assert response == ""  # Should return empty string if no text content


@patch("app.common.llm_services.anthropic.Anthropic")
def test_anthropic_service_general_exception(MockAnthropic, app):
    """Test AnthropicService with a generic exception."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("Generic Error")
    MockAnthropic.return_value = mock_client
    with app.app_context():
        service = AnthropicService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")
    assert "An unexpected error occurred" in response


@patch("app.common.llm_services.openai.OpenAI")
def test_openai_service_success(MockOpenAI, app):
    """Test OpenAIService successful text response."""
    mock_client = MagicMock()
    mock_message = MagicMock(content="Hello OpenAI", tool_calls=None)
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response
    MockOpenAI.return_value = mock_client

    with app.app_context():
        service = OpenAIService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert response == "Hello OpenAI"


@patch("app.common.llm_services.openai.OpenAI")
def test_openai_service_tool_use(MockOpenAI, app):
    """Test OpenAIService tool use response."""
    mock_client = MagicMock()
    mock_function = MagicMock(arguments='{"location": "Boston"}')
    mock_function.name = "get_weather"
    mock_tool_call = MagicMock(id="t1", function=mock_function)
    mock_message = MagicMock(content=None, tool_calls=[mock_tool_call])
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response
    MockOpenAI.return_value = mock_client

    with app.app_context():
        service = OpenAIService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert isinstance(response, list)
    assert response[0]["name"] == "get_weather"


@patch("app.common.llm_services.openai.OpenAI")
def test_openai_service_api_error(MockOpenAI, app):
    """Test OpenAIService API error handling."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = APIError(
        "Test error", request=Request(method="POST", url="http://test.url"), body=None
    )
    MockOpenAI.return_value = mock_client

    with app.app_context():
        service = OpenAIService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "Sorry" in response and "(OpenAI)" in response


@patch("app.common.llm_services.openai.OpenAI")
def test_openai_service_general_exception(MockOpenAI, app):
    """Test OpenAIService with a generic exception."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Generic Error")
    MockOpenAI.return_value = mock_client
    with app.app_context():
        service = OpenAIService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")
    assert "An unexpected error occurred" in response


@patch("app.common.llm_services.openai.OpenAI")
def test_openai_service_no_content(MockOpenAI, app):
    """Test OpenAIService when the response message has no content."""
    mock_client = MagicMock()
    mock_message = MagicMock(content=None, tool_calls=None)
    mock_choice = MagicMock(message=mock_message)
    mock_response = MagicMock(choices=[mock_choice])
    mock_client.chat.completions.create.return_value = mock_response
    MockOpenAI.return_value = mock_client
    with app.app_context():
        service = OpenAIService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")
    assert response == ""


@patch("app.common.llm_services.genai.Client")
def test_gemini_service_success(MockGenAIClient, app):
    """Test GeminiService successful text response."""
    mock_client, mock_models, mock_response, mock_part = (
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    mock_part.text = "Hello Gemini"
    mock_part.function_call = None
    mock_response.text = "Hello Gemini"
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    mock_models.generate_content.return_value = mock_response
    mock_client.models = mock_models
    MockGenAIClient.return_value = mock_client

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert response == "Hello Gemini"


@patch("app.common.llm_services.genai.Client")
def test_gemini_service_history_processing(MockGenAIClient, app):
    """Test GeminiService history processing for different message types."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(text="OK")
    MockGenAIClient.return_value = mock_client

    # A complex history to test all branches
    history = [
        {"role": "user", "content": "Initial query"},
        {"role": "assistant", "content": [{"name": "tool_a", "input": {}}]},
        {
            "role": "user",
            "content": [
                {"tool_use_id": "tool_a", "content": json.dumps({"status": "done"})}
            ],
            "type": "tool_result",
        },
        {"role": "assistant", "content": "Final message from assistant"},
    ]

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        service.get_chat_response(messages=history, system_prompt="")

    # Verify that generate_content was called
    mock_client.models.generate_content.assert_called_once()
    call_args = mock_client.models.generate_content.call_args[1]
    # Check that the history was converted correctly
    assert len(call_args["contents"]) == 5  # system_prompt + 4 history messages
    assert call_args["contents"][2].role == "model"  # assistant tool call
    assert call_args["contents"][3].role == "user"  # tool_result
    assert call_args["contents"][4].role == "model"  # final assistant message


@patch("app.common.llm_services.genai.Client")
def test_gemini_service_api_error(MockGenAIClient, app):
    """Test GeminiService API error handling."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Simulated API Error")
    MockGenAIClient.return_value = mock_client

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "Sorry" in response and "(Gemini)" in response


@patch("app.common.llm_services.genai.Client")
def test_gemini_service_no_candidates(MockGenAIClient, app):
    """Test GeminiService handling of a response with no candidates."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(candidates=[])
    MockGenAIClient.return_value = mock_client

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "An error occurred" in response


@patch("app.common.llm_services.AnthropicService")
@patch("app.common.llm_services.OpenAIService")
@patch("app.common.llm_services.GeminiService")
def test_get_llm_service_factory(MockGemini, MockOpenAI, MockAnthropic, app):
    """Test the factory function for creating LLM services."""
    with app.app_context():
        app.config["LLM_PROVIDER"] = "anthropic"
        app.config["ANTHROPIC_API_KEY"] = "key1"
        get_llm_service()
        MockAnthropic.assert_called_once_with(api_key="key1")
        MockAnthropic.reset_mock()

        app.config["LLM_PROVIDER"] = "openai"
        app.config["OPENAI_API_KEY"] = "key2"
        get_llm_service()
        MockOpenAI.assert_called_once_with(api_key="key2")
        MockOpenAI.reset_mock()

        app.config["LLM_PROVIDER"] = "gemini"
        app.config["GEMINI_API_KEY"] = "key3"
        get_llm_service()
        MockGemini.assert_called_once_with(api_key="key3")
        MockGemini.reset_mock()

        app.config["LLM_PROVIDER"] = "unsupported"
        assert get_llm_service() is None

        app.config["LLM_PROVIDER"] = "openai"
        app.config["OPENAI_API_KEY"] = None
        assert get_llm_service() is None
        MockOpenAI.assert_not_called()

        app.config["LLM_PROVIDER"] = "gemini"
        app.config["GEMINI_API_KEY"] = "key3"
        MockGemini.side_effect = Exception("instantiation failed")
        assert get_llm_service() is None
