"""Local eval-case sink: tee each game-time eval case to an in-process accumulator.

The cases (EvalCase / ExtractionCase / DedupCase / DaySummaryCase) are built
in-process during the game and dumped into Langfuse span output. Langfuse's
read path is lossy on heavy traces (fetch-all 422s, ``trace.get`` truncates
large output), so the sink keeps a local copy of every case in the EXACT
normalized span-dict shape the eval read side produces from Langfuse — the
``*_case_from_span`` converters and frozen-set builders consume both sources
verbatim. ``run_batch`` persists the records as a per-game sidecar.
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
