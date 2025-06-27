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

# Mocking the google.genai library at the top level for Gemini tests
# This is because it might not be installed in all test environments.
# We also mock the specific error class we want to raise.
google_genai_mock = MagicMock()
try:
    from google.genai.errors import ClientError

    google_genai_mock.errors.ClientError = ClientError
except ImportError:
    google_genai_mock.errors.ClientError = type("ClientError", (Exception,), {})


# --- Test Abstract Base Class ---
def test_llm_service_abc_requires_api_key():
    """Test that instantiating a service without an API key raises ValueError."""
    with pytest.raises(ValueError, match="requires an API key"):

        class DummyService(LLMService):
            def _initialize_client(self):
                return None

            def get_chat_response(self, messages, system_prompt, tools=None):
                return "dummy"

        DummyService(api_key=None)


# --- Test AnthropicService ---
@patch("anthropic.Anthropic")
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


@patch("anthropic.Anthropic")
def test_anthropic_service_tool_use(MockAnthropic, app):
    """Test AnthropicService tool use response."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    tool_call = MagicMock(type="tool_use", id="t1", name="get_weather", input={})
    mock_response.content = [tool_call]
    mock_response.stop_reason = "tool_use"
    mock_client.messages.create.return_value = mock_response
    MockAnthropic.return_value = mock_client

    with app.app_context():
        service = AnthropicService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert isinstance(response, list)
    assert response[0]["name"] == "get_weather"


@patch("anthropic.Anthropic")
def test_anthropic_service_api_error(MockAnthropic, app):
    """Test AnthropicService API error handling."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("Anthropic general error")
    MockAnthropic.return_value = mock_client

    with app.app_context():
        service = AnthropicService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "An unexpected error occurred" in response


# --- Test OpenAIService ---
@patch("openai.OpenAI")
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


@patch("openai.OpenAI")
def test_openai_service_tool_use(MockOpenAI, app):
    """Test OpenAIService tool use response."""
    mock_client = MagicMock()
    mock_function = MagicMock(name="get_weather", arguments='{"location": "Boston"}')
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


@patch("openai.OpenAI")
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

    assert "Sorry" in response
    assert "(OpenAI)" in response


# --- Test GeminiService ---
@patch("common.llm_services.genai.Client")
def test_gemini_service_success(MockGenAIClient, app):
    """Test GeminiService successful text response."""
    mock_client_instance, mock_models_object, mock_response, mock_part = (
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    mock_part.text = "Hello Gemini"
    mock_part.function_call = None
    mock_response.text = "Hello Gemini"
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    mock_models_object.generate_content.return_value = mock_response
    mock_client_instance.models = mock_models_object
    MockGenAIClient.return_value = mock_client_instance

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert response == "Hello Gemini"


@patch("common.llm_services.genai.Client")
def test_gemini_service_tool_use(MockGenAIClient, app):
    """Test GeminiService tool use response based on PDF examples."""
    mock_client_instance, mock_models_object, mock_response, mock_part = (
        MagicMock(),
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    # Replicating the function_call structure from the PDF
    mock_function_call = MagicMock(
        name="get_project_details", args={"project_id": "portfolio"}
    )
    mock_part.function_call = mock_function_call
    mock_response.candidates = [MagicMock(content=MagicMock(parts=[mock_part]))]
    mock_models_object.generate_content.return_value = mock_response
    mock_client_instance.models = mock_models_object
    MockGenAIClient.return_value = mock_client_instance

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="", tools=[{}])

    assert isinstance(response, list)
    assert response[0]["name"] == "get_project_details"
    assert response[0]["input"]["project_id"] == "portfolio"


@patch("common.llm_services.genai.Client")
def test_gemini_service_api_error(MockGenAIClient, app):
    """Test GeminiService API error handling using the observed ClientError."""
    mock_client_instance, mock_models_object = MagicMock(), MagicMock()
    mock_models_object.generate_content.side_effect = (
        google_genai_mock.errors.ClientError("API key not valid")
    )
    mock_client_instance.models = mock_models_object
    MockGenAIClient.return_value = mock_client_instance

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "Sorry" in response
    assert "(Gemini)" in response


@patch("common.llm_services.genai.Client")
def test_gemini_service_no_candidates(MockGenAIClient, app):
    """Test GeminiService handling of a response with no candidates."""
    mock_client_instance, mock_models_object, mock_response = (
        MagicMock(),
        MagicMock(),
        MagicMock(),
    )
    mock_response.candidates = []  # Simulate an empty candidates list
    mock_models_object.generate_content.return_value = mock_response
    mock_client_instance.models = mock_models_object
    MockGenAIClient.return_value = mock_client_instance

    with app.app_context():
        service = GeminiService(api_key="fake_key")
        response = service.get_chat_response(messages=[], system_prompt="")

    assert "An error occurred" in response


# --- Test get_llm_service Factory ---
@patch("common.llm_services.AnthropicService")
@patch("common.llm_services.OpenAIService")
@patch("common.llm_services.GeminiService")
def test_get_llm_service_factory(MockGemini, MockOpenAI, MockAnthropic, app):
    """Test the factory function for creating LLM services."""
    with app.app_context():
        app.config["LLM_PROVIDER"] = "anthropic"
        app.config["ANTHROPIC_API_KEY"] = "key1"
        get_llm_service()
        MockAnthropic.assert_called_once_with(api_key="key1")
    MockAnthropic.reset_mock()

    with app.app_context():
        app.config["LLM_PROVIDER"] = "openai"
        app.config["OPENAI_API_KEY"] = "key2"
        get_llm_service()
        MockOpenAI.assert_called_once_with(api_key="key2")
    MockOpenAI.reset_mock()

    with app.app_context():
        app.config["LLM_PROVIDER"] = "gemini"
        app.config["GEMINI_API_KEY"] = "key3"
        get_llm_service()
        MockGemini.assert_called_once_with(api_key="key3")
    MockGemini.reset_mock()

    with app.app_context():
        app.config["LLM_PROVIDER"] = "unsupported"
        service = get_llm_service()
        assert service is None

    with app.app_context():
        app.config["LLM_PROVIDER"] = "openai"
        app.config["OPENAI_API_KEY"] = None
        service = get_llm_service()
        assert service is None
        MockOpenAI.assert_not_called()
