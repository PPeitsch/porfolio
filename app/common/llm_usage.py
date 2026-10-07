"""Usage log of the chat: one JSON line per model call, never the conversation.

Each call to the model (each tool round is one) appends to
``<LLM_USAGE_DIR>/llm_usage_<date>.jsonl``: time, model that answered, tokens,
cost in USD, latency, tool calls asked, the kind of error, and the visitor as a
pseudonym (a hash of the IP with SECRET_KEY: it counts visitors without keeping
their IP). It is what shows the daily cost of the chat and a visitor abusing it.

One file per day instead of a rotating handler: the workers are separate
processes, and an append of a short line is atomic, while rotating a shared
file is not. Files older than LLM_USAGE_KEEP_DAYS are removed when a new day
starts. ``python scripts/llm_usage_report.py`` sums them by day.
"""

import hashlib
import json
import logging
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from flask import current_app, has_app_context

logger = logging.getLogger(__name__)

PREFIX = "llm_usage_"


def usage_dir() -> Optional[str]:
    """The folder of the log, or None when it is turned off (LLM_USAGE_DIR empty)."""
    if not has_app_context():
        return None
    configured = current_app.config.get("LLM_USAGE_DIR")
    if configured is None:
        return os.path.join(current_app.instance_path, "llm_usage")
    return configured or None


def visitor_id(ip: Optional[str]) -> Optional[str]:
    """A stable pseudonym for an IP: same visitor, same id; the IP is not kept."""
    if not ip:
        return None
    secret = str(current_app.config.get("SECRET_KEY") or "")
    return hashlib.sha256(f"{secret}:{ip}".encode()).hexdigest()[:12]


def _cost(response: Any) -> Optional[float]:
    # LiteLLM asks OpenRouter for usage.include and keeps what it charged as
    # response_cost; for other providers, that is its own estimate.
    cost = getattr(getattr(response, "usage", None), "cost", None)
    if cost is None:
        hidden = getattr(response, "_hidden_params", None) or {}
        cost = hidden.get("response_cost")
    return float(cost) if isinstance(cost, (int, float)) else None


def record(
    model: str,
    response: Any,
    started: float,
    error: Optional[str] = None,
    visitor: Optional[str] = None,
    tool_calls: int = 0,
) -> None:
    """Append the call to today's file. A failure here is logged, never raised."""
    folder = usage_dir()
    if not folder:
        return
    usage = getattr(response, "usage", None)
    now = datetime.now(timezone.utc)
    line = {
        "ts": now.isoformat(timespec="seconds"),
        "model": getattr(response, "model", None) or model,
        "input_tokens": getattr(usage, "prompt_tokens", None),
        "output_tokens": getattr(usage, "completion_tokens", None),
        "cost": _cost(response),
        "latency_ms": int((time.monotonic() - started) * 1000),
        "tool_calls": tool_calls,
        "error": error,
        "visitor": visitor,
    }
    try:
        os.makedirs(folder, exist_ok=True)
        path = os.path.join(folder, f"{PREFIX}{now:%Y-%m-%d}.jsonl")
        new_day = not os.path.exists(path)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line) + "\n")
        if new_day:
            _prune(folder, now)
    except (OSError, TypeError, ValueError) as e:
        logger.warning(f"Could not write the LLM usage log: {e}")


def _prune(folder: str, now: datetime) -> None:
    keep = int(current_app.config.get("LLM_USAGE_KEEP_DAYS", 90))
    oldest = f"{PREFIX}{now - timedelta(days=keep):%Y-%m-%d}.jsonl"
    for name in os.listdir(folder):
        if name.startswith(PREFIX) and name.endswith(".jsonl") and name < oldest:
            os.remove(os.path.join(folder, name))
