import json
import os
from unittest.mock import MagicMock, patch

import pytest
from anthropic import APIError as AnthropicAPIError
from httpx import Request
from openai import APIError
from requests.exceptions import RequestException

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
    """Test that ABC methods raise NotImplementedError if not correctly implemented."""

    class IncompleteService(LLMService):
        def _initialize_client(self):
            return None

        # Missing get_chat_response implementation

    class AbstractClientService(LLMService):
        def _initialize_client(self):
            return super()._initialize_client()

        def get_chat_response(self, messages, system_prompt, tools=None):
            pass

    with app.app_context():
        with pytest.raises(TypeError):
            IncompleteService(api_key="key")

        with pytest.raises(NotImplementedError):
            AbstractClientService(api_key="key")


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
    assert response == ""


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


# --- Gemini Service Tests ---

# Condition to skip tests if the proxy URL is set, as they mock the direct API
proxy_configured = os.getenv("GEMINI_PROXY_URL") is not None
skip_if_proxy = pytest.mark.skipif(
    proxy_configured, reason="Skipping direct API tests when proxy is configured"
)


@skip_if_proxy
@patch("app.common.llm_services.genai.Client")
def test_gemini_service_direct_api_success(MockGenAIClient, app):
    """Test GeminiService direct API successful text response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Hello Gemini"
    mock_response.candidates = [
        MagicMock(content=MagicMock(parts=[MagicMock(function_call=None)]))
    ]
    mock_client.models.generate_content.return_value = mock_response
    MockGenAIClient.return_value = mock_client

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert response == "Hello Gemini"


@skip_if_proxy
@patch("app.common.llm_services.genai.Client")
def test_gemini_service_direct_api_history_processing(MockGenAIClient, app):
    """Test GeminiService direct API history processing for different message types."""
    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = MagicMock(
        text="OK", candidates=[]
    )
    MockGenAIClient.return_value = mock_client

    history = [
        {"role": "user", "content": "Query"},
        {"role": "assistant", "content": [{"name": "tool_a", "input": {}}]},
        {
            "role": "user",
            "content": [
                {"tool_use_id": "tool_a", "content": json.dumps({"status": "done"})}
            ],
            "type": "tool_result",
        },
    ]

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        service.get_chat_response(messages=history, system_prompt="")

    call_args = mock_client.models.generate_content.call_args[1]
    assert len(call_args["contents"]) == 4  # System prompt + 3 history items


@skip_if_proxy
@patch("app.common.llm_services.genai.Client")
def test_gemini_service_direct_api_error(MockGenAIClient, app):
    """Test GeminiService direct API error handling."""
    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("Simulated API Error")
    MockGenAIClient.return_value = mock_client

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "Sorry" in response and "(Gemini)" in response


@patch("app.common.llm_services.requests.post")
@patch("app.common.llm_services.genai.Client")
def test_gemini_service_proxy_success(mock_genai_client, mock_post, app):
    """Test GeminiService successful response via proxy."""
    app.config["GEMINI_PROXY_URL"] = "http://fake-proxy.com/api"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"reply": "Hello from Proxy"}
    mock_post.return_value = mock_response

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(
            messages=[{"role": "user", "content": "hi"}], system_prompt="system"
        )

    assert response == "Hello from Proxy"
    mock_post.assert_called_once()
    call_args = mock_post.call_args[1]["json"]
    assert call_args["system_prompt"] == "system"
    assert call_args["messages"][0]["content"] == "hi"
    mock_genai_client.assert_not_called()  # Ensure direct client is not used


@patch("app.common.llm_services.requests.post")
@patch("app.common.llm_services.genai.Client")
def test_gemini_service_proxy_request_exception(mock_genai_client, mock_post, app):
    """Test GeminiService proxy handling of a RequestException."""
    app.config["GEMINI_PROXY_URL"] = "http://fake-proxy.com/api"
    mock_post.side_effect = RequestException("Connection timed out")

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "communicating with the AI service proxy" in response
    mock_genai_client.assert_not_called()


@patch("app.common.llm_services.requests.post")
@patch("app.common.llm_services.genai.Client")
def test_gemini_service_proxy_unexpected_error(mock_genai_client, mock_post, app):
    """Test GeminiService proxy handling of a non-RequestException."""
    app.config["GEMINI_PROXY_URL"] = "http://fake-proxy.com/api"
    mock_post.side_effect = ValueError("Unexpected error")

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "unexpected error occurred while processing" in response
    mock_genai_client.assert_not_called()


@patch("app.common.llm_services.AnthropicService")
@patch("app.common.llm_services.OpenAIService")
@patch("app.common.llm_services.GeminiService")
def test_get_llm_service_factory(MockGemini, MockOpenAI, MockAnthropic, app):
    """Test the factory function for creating LLM services."""
    service_map = {
        "anthropic": (MockAnthropic, "ANTHROPIC_API_KEY"),
        "openai": (MockOpenAI, "OPENAI_API_KEY"),
        "gemini": (MockGemini, "GEMINI_API_KEY"),
    }

    with app.app_context():
        for provider, (mock_class, key_name) in service_map.items():
            app.config["LLM_PROVIDER"] = provider
            app.config[key_name] = f"{provider}_key"
            get_llm_service()
            mock_class.assert_called_once_with(api_key=f"{provider}_key")
            mock_class.reset_mock()

        # Test unsupported provider
        app.config["LLM_PROVIDER"] = "unsupported"
        assert get_llm_service() is None

        # Test missing API key
        app.config["LLM_PROVIDER"] = "openai"
        app.config["OPENAI_API_KEY"] = None
        assert get_llm_service() is None
        MockOpenAI.assert_not_called()

        # Test instantiation failure
        app.config["LLM_PROVIDER"] = "gemini"
        app.config["GEMINI_API_KEY"] = "gemini_key"
        MockGemini.side_effect = Exception("Instantiation failed")
        assert get_llm_service() is None
