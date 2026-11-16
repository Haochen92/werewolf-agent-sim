"""A local copy of every evaluation case a game produces.

An evaluation case is the record of one thing to be judged later: one decision a player made
(EvalCase), one game's lesson extraction (ExtractionCase), one duplicate check (DedupCase) or one
day summary (DaySummaryCase). The game builds each case as it runs and saves it to Langfuse as
the output of a span.

Reading the cases back from Langfuse is unreliable for a large game: fetching the whole trace
can fail with a 422 error, and a large output can come back cut short. So each case is also
added to a list kept in memory for the game. That list is the sink.

A record in the list has exactly the shape the evaluation code gets when it reads the same span
from Langfuse, so the same code reads either source. ``scripts/run_batch.py`` writes the list
to a file beside each game's results.
"""

from __future__ import annotations

from typing import Any


class EvalCaseSink:
    """Per-game accumulator of locally-emitted eval cases (lives on GraphContext)."""

    def __init__(self) -> None:
        self.records: list[dict[str, Any]] = []
        """Normalized span dicts, one per frozen case, in emission order."""


def freeze_case(
    span: Any,
    case: Any,
    *,
    kind: str,
    case_key: str,
    sink: EvalCaseSink | None,
) -> dict[str, Any]:
    """Stamp the live span's identity onto *case*, dump it once, tee it to *sink*.

    Returns the json-safe payload for the producer's ``span.update(output=
    {case_key: payload})`` — the local record and the Langfuse copy are the
    same dump, with real ``trace_id``/``observation_id`` on both (so
    ``case_id = {trace_id}:{observation_id}`` and judge score push-back work
    identically for either source). ``sink=None`` skips the tee (offline
    callers). ``input`` is deliberately ``None`` in the record: converters
    never read it, and the case already embeds its inputs.
    """
    case.trace_id = str(getattr(span, "trace_id", "") or "")
    case.observation_id = str(getattr(span, "id", "") or "")
    payload = case.model_dump(mode="json")
    if sink is not None:
        sink.records.append(
            {
                "kind": kind,
                "id": case.observation_id,
                "name": case.span_name,
                "trace_id": case.trace_id,
                "parent_observation_id": None,
                "metadata": {},
                "input": None,
                "output": {case_key: payload},
            }
        )
    return payload
