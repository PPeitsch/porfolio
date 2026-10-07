import json
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.common import llm_usage
from app.common.exceptions import LLMServiceError
from app.common.llm_services import LLMService


@pytest.fixture()
def usage_dir(app, tmp_path):
    """Turns the usage log on, in a temporary folder."""
    app.config["LLM_USAGE_DIR"] = str(tmp_path)
    with app.app_context():
        yield tmp_path
    app.config["LLM_USAGE_DIR"] = ""


def lines(folder):
    return [
        json.loads(line)
        for path in sorted(folder.glob("llm_usage_*.jsonl"))
        for line in path.read_text().splitlines()
    ]


def response(content="Hola", tool_calls=None, cost=0.0004):
    message = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(
        choices=[SimpleNamespace(message=message)],
        model="qwen/qwen3.7-flash",
        usage=SimpleNamespace(prompt_tokens=900, completion_tokens=40, cost=cost),
    )


def test_a_call_is_logged_without_the_conversation(usage_dir):
    service = LLMService(model="openrouter/qwen/qwen3.7-flash")
    with patch("litellm.completion", return_value=response()):
        service.get_chat_response(
            [{"role": "user", "content": "mi CBU es 0000003100012345678901"}],
            "system",
            visitor="abc",
        )

    [line] = lines(usage_dir)
    assert line["model"] == "qwen/qwen3.7-flash"
    assert (line["input_tokens"], line["output_tokens"]) == (900, 40)
    assert line["cost"] == pytest.approx(0.0004)
    assert line["visitor"] == "abc"
    assert line["error"] is None
    assert line["tool_calls"] == 0
    assert "CBU" not in json.dumps(line) and "Hola" not in json.dumps(line)


def test_a_failed_call_is_logged_with_its_kind(usage_dir):
    service = LLMService(model="anthropic/claude-haiku-4-5")
    with patch("litellm.completion", side_effect=TimeoutError("slow")):
        with pytest.raises(LLMServiceError):
            service.get_chat_response([], "system")

    [line] = lines(usage_dir)
    assert line["error"] == "TimeoutError"
    assert line["model"] == "anthropic/claude-haiku-4-5"
    assert line["cost"] is None


def test_the_cost_litellm_keeps_is_used(usage_dir):
    estimated = response(cost=None)
    estimated._hidden_params = {"response_cost": 0.002}
    with patch("litellm.completion", return_value=estimated):
        LLMService(model="gemini/gemini-2.5-flash").get_chat_response([], "system")

    assert lines(usage_dir)[0]["cost"] == pytest.approx(0.002)


def test_turned_off_writes_nothing(app, tmp_path):
    app.config["LLM_USAGE_DIR"] = ""
    with app.app_context(), patch("litellm.completion", return_value=response()):
        LLMService(model="openrouter/x").get_chat_response([], "system")
    assert not list(tmp_path.iterdir())


def test_a_log_that_cannot_be_written_does_not_stop_the_reply(app, tmp_path):
    blocked = tmp_path / "file"
    blocked.write_text("")
    app.config["LLM_USAGE_DIR"] = str(blocked / "llm_usage")  # under a file
    with app.app_context(), patch("litellm.completion", return_value=response()):
        reply = LLMService(model="openrouter/x").get_chat_response([], "system")
    app.config["LLM_USAGE_DIR"] = ""
    assert reply.content == "Hola"


def test_old_days_are_removed_when_a_new_day_starts(usage_dir, app):
    app.config["LLM_USAGE_KEEP_DAYS"] = 30
    today = datetime.now(timezone.utc)
    old = usage_dir / f"llm_usage_{today - timedelta(days=31):%Y-%m-%d}.jsonl"
    recent = usage_dir / f"llm_usage_{today - timedelta(days=29):%Y-%m-%d}.jsonl"
    old.write_text("{}\n")
    recent.write_text("{}\n")

    llm_usage.record("m", None, time.monotonic())

    assert not old.exists()
    assert recent.exists()


def test_visitor_id_is_stable_and_hides_the_ip(app):
    with app.app_context():
        first = llm_usage.visitor_id("203.0.113.25")
        assert first == llm_usage.visitor_id("203.0.113.25")
        assert first != llm_usage.visitor_id("203.0.113.26")
        assert "181" not in first and len(first) == 12
        assert llm_usage.visitor_id(None) is None
