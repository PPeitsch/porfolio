from unittest.mock import MagicMock, patch

import pytest

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
    from openai import APIError

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = APIError(
        "Test error", response=MagicMock(), body=None
    )
    MockOpenAI.return_value = mock_client

    service = OpenAIService(api_key="fake_key")
    response = service.get_chat_response(messages=[], system_prompt="")

    assert "Sorry" in response
    assert "(OpenAI)" in response


# --- Test GeminiService ---
@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
def test_gemini_service_success(mock_configure, MockGenerativeModel):
    """Test GeminiService successful text response."""
    mock_model = MagicMock()
    mock_response = MagicMock()
    mock_response.candidates[0].content.parts[0].text = "Hello Gemini"
    # Ensure function_call does not exist for this test case
    del mock_response.candidates[0].content.parts[0].function_call
    mock_model.generate_content.return_value = mock_response
    MockGenerativeModel.return_value = mock_model

    service = GeminiService(api_key="fake_key")
    response = service.get_chat_response(messages=[], system_prompt="")

    assert response == "Hello Gemini"
    mock_model.generate_content.assert_called_once()


# --- Test get_llm_service Factory ---
@patch("common.llm_services.current_app")
def test_get_llm_service_factory(mock_current_app):
    """Test the factory function for creating LLM services."""
    # Test Anthropic
    mock_current_app.config = {
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "key1",
    }
    service = get_llm_service()
    assert isinstance(service, AnthropicService)

    # Test OpenAI
    mock_current_app.config = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "key2"}
    service = get_llm_service()
    assert isinstance(service, OpenAIService)

    # Test Gemini
    mock_current_app.config = {"LLM_PROVIDER": "gemini", "GEMINI_API_KEY": "key3"}
    service = get_llm_service()
    assert isinstance(service, GeminiService)

    # Test unsupported provider
    mock_current_app.config = {"LLM_PROVIDER": "unsupported"}
    service = get_llm_service()
    assert service is None

    # Test missing API key
    mock_current_app.config = {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": None}
    service = get_llm_service()
    assert service is None
