import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.common.exceptions import LLMConfigurationError, LLMServiceError
from app.common.llm_services import (
    LLMService,
    _parse_arguments,
    get_llm_service,
    resolve_model,
)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_skills",
            "description": "Skills.",
            "parameters": {"type": "object", "properties": {}},
        },
    }
]


def completion_result(content=None, tool_calls=None):
    """Shapes a value like the ModelResponse that litellm.completion returns."""
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def tool_call(call_id, name, arguments):
    return SimpleNamespace(
        id=call_id, function=SimpleNamespace(name=name, arguments=arguments)
    )


@pytest.fixture()
def completion():
    with patch("app.common.llm_services.litellm.completion") as mock:
        yield mock


# --- LLMService ---


def test_text_response(completion):
    completion.return_value = completion_result(content="Hello")
    service = LLMService(model="openrouter/anthropic/claude-haiku-4.5")

    response = service.get_chat_response(
        [{"role": "user", "content": "Hi"}], "Be brief.", TOOLS
    )

    assert response.content == "Hello"
    assert response.tool_calls == []
    assert response.message == {"role": "assistant", "content": "Hello"}
    kwargs = completion.call_args.kwargs
    assert kwargs["model"] == "openrouter/anthropic/claude-haiku-4.5"
    assert kwargs["messages"][0] == {"role": "system", "content": "Be brief."}
    assert kwargs["messages"][1] == {"role": "user", "content": "Hi"}
    assert kwargs["tools"] == TOOLS
    assert kwargs["tool_choice"] == "auto"
    assert "api_key" not in kwargs and "api_base" not in kwargs


def test_tool_call_response(completion):
    completion.return_value = completion_result(
        tool_calls=[tool_call("call1", "get_project_details", '{"project_id": "p1"}')]
    )

    response = LLMService(model="m").get_chat_response([], "sys", TOOLS)

    assert response.content == ""
    assert len(response.tool_calls) == 1
    call = response.tool_calls[0]
    assert (call.id, call.name, call.arguments) == (
        "call1",
        "get_project_details",
        {"project_id": "p1"},
    )
    assert response.message["tool_calls"] == [
        {
            "id": "call1",
            "type": "function",
            "function": {
                "name": "get_project_details",
                "arguments": json.dumps({"project_id": "p1"}),
            },
        }
    ]


def test_no_tools_means_no_tool_choice(completion):
    completion.return_value = completion_result(content="ok")

    LLMService(model="m").get_chat_response([], "sys")

    assert "tools" not in completion.call_args.kwargs
    assert "tool_choice" not in completion.call_args.kwargs


def test_explicit_key_base_and_limits_are_passed(completion):
    completion.return_value = completion_result(content="ok")
    service = LLMService(
        model="ollama/llama3.1",
        api_key="k",
        api_base="http://localhost:11434",
        timeout=12,
        max_tokens=256,
    )

    service.get_chat_response([], "sys")

    kwargs = completion.call_args.kwargs
    assert kwargs["api_key"] == "k"
    assert kwargs["api_base"] == "http://localhost:11434"
    assert kwargs["timeout"] == 12
    assert kwargs["max_tokens"] == 256


def test_reasoning_and_fallbacks_are_passed_only_when_set(completion):
    completion.return_value = completion_result(content="ok")

    LLMService(model="m").get_chat_response([], "sys")
    kwargs = completion.call_args.kwargs
    assert "reasoning_effort" not in kwargs
    assert "fallbacks" not in kwargs

    LLMService(
        model="m", reasoning_effort="none", fallbacks=[("f1", "low"), ("f2", None)]
    ).get_chat_response([], "sys")
    kwargs = completion.call_args.kwargs
    assert kwargs["reasoning_effort"] == "none"
    assert kwargs["allowed_openai_params"] == ["reasoning_effort"]
    # A fallback without its own effort does not inherit the main model's.
    assert kwargs["fallbacks"] == [
        {
            "model": "f1",
            "reasoning_effort": "low",
            "allowed_openai_params": ["reasoning_effort"],
        },
        {"model": "f2", "reasoning_effort": None, "allowed_openai_params": []},
    ]


def test_provider_errors_become_llm_service_error(completion):
    completion.side_effect = RuntimeError("503 Service Unavailable")

    with pytest.raises(LLMServiceError, match="503"):
        LLMService(model="m").get_chat_response([], "sys")


@pytest.mark.parametrize(
    "raw, expected",
    [
        ('{"a": 1}', {"a": 1}),
        ({"a": 1}, {"a": 1}),
        ("", {}),
        (None, {}),
        ("not json", {}),
        ("[1, 2]", {}),
    ],
)
def test_parse_arguments(raw, expected):
    assert _parse_arguments(raw) == expected


# --- Configuration ---


@pytest.mark.parametrize(
    "config, expected",
    [
        ({"LLM_MODEL": "openrouter/x/y", "LLM_PROVIDER": "openai"}, "openrouter/x/y"),
        (
            {"LLM_PROVIDER": "anthropic", "ANTHROPIC_MODEL": "claude-x"},
            "anthropic/claude-x",
        ),
        ({"LLM_PROVIDER": "OpenAI", "OPENAI_MODEL": "gpt-x"}, "openai/gpt-x"),
        ({"LLM_PROVIDER": "gemini", "GEMINI_MODEL": "gemini-x"}, "gemini/gemini-x"),
        ({"LLM_PROVIDER": "gemini"}, None),
        ({"LLM_PROVIDER": "unknown", "UNKNOWN_MODEL": "x"}, None),
        ({}, None),
    ],
)
def test_resolve_model(config, expected):
    assert resolve_model(config) == expected


@pytest.fixture()
def llm_config(app, monkeypatch):
    """Sets LLM settings on the test app for one test."""

    def configure(**settings):
        defaults = {
            "LLM_MODEL": None,
            "LLM_API_KEY": None,
            "LLM_API_BASE": None,
            "LLM_PROVIDER": "",
            "LLM_TIMEOUT": 30,
            "LLM_MAX_TOKENS": 1024,
            "LLM_REASONING_EFFORT": None,
            "LLM_FALLBACK_MODELS": "",
        }
        for key, value in {**defaults, **settings}.items():
            monkeypatch.setitem(app.config, key, value)

    return configure


def test_get_llm_service_with_key_in_environment(app, llm_config, monkeypatch):
    llm_config(LLM_MODEL="openrouter/anthropic/claude-haiku-4.5", LLM_TIMEOUT=10)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    with app.app_context():
        service = get_llm_service()

    assert service is not None
    assert service.model == "openrouter/anthropic/claude-haiku-4.5"
    assert service.api_key is None  # LiteLLM reads it from the environment
    assert service.timeout == 10


def test_get_llm_service_missing_key(app, llm_config, monkeypatch):
    llm_config(LLM_MODEL="openrouter/anthropic/claude-haiku-4.5")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with app.app_context():
        with pytest.raises(LLMConfigurationError, match="OPENROUTER_API_KEY"):
            get_llm_service()


def test_get_llm_service_explicit_key_skips_environment_check(
    app, llm_config, monkeypatch
):
    llm_config(LLM_MODEL="openrouter/anthropic/claude-haiku-4.5", LLM_API_KEY="k")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    with app.app_context():
        service = get_llm_service()

    assert service is not None and service.api_key == "k"


def test_get_llm_service_without_model(app, llm_config):
    llm_config()

    with app.app_context():
        with pytest.raises(LLMConfigurationError, match="LLM_MODEL"):
            get_llm_service()


def test_get_llm_service_warns_about_gemini_proxy(app, llm_config, monkeypatch, caplog):
    llm_config(LLM_MODEL="openrouter/anthropic/claude-haiku-4.5", LLM_API_KEY="k")
    monkeypatch.setitem(app.config, "GEMINI_PROXY_URL", "https://old-proxy")

    with app.app_context():
        assert get_llm_service() is not None

    assert "GEMINI_PROXY_URL is no longer supported" in caplog.text


def test_get_llm_service_reads_tokens_reasoning_and_fallbacks(
    app, llm_config, monkeypatch
):
    llm_config(
        LLM_MODEL="openrouter/qwen/qwen3.7-flash",
        LLM_MAX_TOKENS=2048,
        LLM_REASONING_EFFORT="none",
        LLM_FALLBACK_MODELS=(
            " openrouter/deepseek/deepseek-v4-flash@none, ,openrouter/x/y "
        ),
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")

    with app.app_context():
        service = get_llm_service()

    assert service.max_tokens == 2048
    assert service.reasoning_effort == "none"
    assert service.fallbacks == [
        ("openrouter/deepseek/deepseek-v4-flash", "none"),
        ("openrouter/x/y", None),
    ]


def test_get_llm_service_checks_the_fallbacks_keys(app, llm_config, monkeypatch):
    llm_config(
        LLM_MODEL="openrouter/qwen/qwen3.7-flash",
        LLM_FALLBACK_MODELS="anthropic/claude-haiku-4-5",
    )
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    with app.app_context():
        with pytest.raises(LLMConfigurationError, match="anthropic/claude-haiku-4-5"):
            get_llm_service()
