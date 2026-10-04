"""How many tokens a game spent, and how long its model calls took.

A ``UsageMeter`` rides along with the game's other callbacks and counts every model call the
game makes: its input tokens (and the part the provider served from cache), its output tokens
(and the part that was reasoning), and its wall time. Counts are kept per model and per UTC hour,
because that is what prices depend on: a model's price can change on a date, and DeepSeek bills
peak hours at twice the off-peak rate. The session saves the counts on the game's row as it goes
(``games.usage``), so a game resumed after a restart carries on from them.

The cost is not stored. ``game_cost`` works it out from the counts and the price table
(``Agents/llm_factory/pricing.py``) whenever a replay is read, so a corrected price corrects
every game it applied to. A game recorded before this existed has no counts and shows no cost.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler

from Agents.llm_factory.pricing import cost_usd

_FIELDS = ("calls", "failed", "input", "cached", "output", "reasoning", "seconds")


def _hour(at: datetime) -> str:
    return at.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0).isoformat()


class UsageMeter(BaseCallbackHandler):
    """Counts a game's model calls by model and UTC hour. Thread-safe: the engine runs seats'
    turns on worker threads. ``changed`` tells the session there is something new to save."""

    def __init__(self, saved: dict | None = None) -> None:
        self._lock = threading.Lock()
        self._started: dict[UUID, tuple[str, float]] = {}
        self._buckets: dict[tuple[str, str], dict[str, float]] = {}
        for b in (saved or {}).get("buckets", []):
            self._buckets[(b["model"], b["hour"])] = {k: b.get(k, 0) for k in _FIELDS}
        self.changed = False

    def on_chat_model_start(self, serialized: dict, messages: list, *, run_id: UUID,
                            metadata: dict | None = None, **kwargs: Any) -> None:
        model = (metadata or {}).get("ls_model_name") or (serialized.get("kwargs") or {}).get("model", "")
        with self._lock:
            self._started[run_id] = (str(model).removeprefix("models/"), time.monotonic())

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs: Any) -> None:
        with self._lock:
            started = self._started.pop(run_id, None)
        if started is None:
            return
        model, t0 = started
        usage: dict = {}
        for generations in response.generations or []:
            for g in generations:
                usage = getattr(getattr(g, "message", None), "usage_metadata", None) or usage
        self._add(model, time.monotonic() - t0, usage, failed=False)

    def on_llm_error(self, error: BaseException, *, run_id: UUID, **kwargs: Any) -> None:
        with self._lock:
            started = self._started.pop(run_id, None)
        if started is not None:
            self._add(started[0], 0.0, {}, failed=True)

    def _add(self, model: str, seconds: float, usage: dict, *, failed: bool) -> None:
        key = (model, _hour(datetime.now(timezone.utc)))
        with self._lock:
            b = self._buckets.setdefault(key, dict.fromkeys(_FIELDS, 0))
            if failed:  # no tokens come back; its time is left out of the average call time
                b["failed"] += 1
            else:
                b["calls"] += 1
                b["seconds"] = round(b["seconds"] + seconds, 3)
                b["input"] += usage.get("input_tokens", 0) or 0
                b["cached"] += (usage.get("input_token_details") or {}).get("cache_read", 0) or 0
                b["output"] += usage.get("output_tokens", 0) or 0
                b["reasoning"] += (usage.get("output_token_details") or {}).get("reasoning", 0) or 0
            self.changed = True

    def snapshot(self) -> dict:
        """The counts in the shape stored on the game row; clears ``changed``."""
        with self._lock:
            self.changed = False
            return {"buckets": [{"model": m, "hour": h, **v} for (m, h), v in sorted(self._buckets.items())]}


def game_cost(usage: dict | None) -> float | None:
    """The game's cost in USD from its stored counts, or None when it has no counts or a model
    in them has no price for that date: an unknown cost is shown as nothing, never as a guess."""
    buckets = (usage or {}).get("buckets") or []
    if not buckets:
        return None
    total = 0.0
    for b in buckets:
        cost = cost_usd(b["model"], datetime.fromisoformat(b["hour"]),
                        input=b["input"], cached=b["cached"], output=b["output"])
        if cost is None:
            return None
        total += cost
    return round(total, 4)


def average_call_seconds(usage: dict | None, model: str = "") -> float | None:
    """Mean wall time of one successful model call on ``model`` (the game's own model; empty =
    the model that made the most calls). Covers every call on it: seat turns and summaries."""
    buckets = (usage or {}).get("buckets") or []
    if not model and buckets:
        calls: dict[str, int] = {}
        for b in buckets:
            calls[b["model"]] = calls.get(b["model"], 0) + b["calls"]
        model = max(calls, key=calls.get)
    rows = [b for b in buckets if b["model"] == model.split("/", 1)[-1]]
    n = sum(b["calls"] for b in rows)
    return round(sum(b["seconds"] for b in rows) / n, 2) if n else None
