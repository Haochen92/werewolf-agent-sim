"""A lesson's structured situation fields reach the wire, next to the one-line situation.

The store keeps each v6 record's labelled parts (`dimensions`: the separate descriptions, the
counts, and categories like info_starved / exposed). The replay shows them, so the two memory
announces copy them onto the stream and the translator carries them into the wire events.
Records stored before the parts were kept, and the legacy extraction models, give None. Nothing
here touches what the model sees: the prompt golden (tests/engine/test_draft_preview.py) pins that.
"""
from __future__ import annotations

from datetime import datetime

from Agents.nodes import orchestrator
from Agents.schemas.memory import (
    HealerNightObservation,
    HealerNightStrategyPoint,
    Observation,
    RetrievedObservation,
    RetrievedStrategyPoint,
    StoredObservation,
    StoredStrategyPoint,
    StrategyPoint,
)
from Agents.schemas.output import MemoryVerdict, StrategyVerdict
from Agents.schemas.turn import TurnEffects
from Agents.turn import pipeline
from server.game.translate import Translator
from server.schemas import events as ev

_SITUATION = {
    "situation": "A claimed investigator is loud about player_4.",
    "information_landscape": "One investigation result, nothing else confirmed.",
    "players_alive": 7,
    "distance_to_parity": 2,
    "is_swing": True,
    "criticality_stakes": "Losing the claimant tonight hands the wolves the day.",
    "info_landscape_class": "info_rich",
    "exposure_class": "safe",
    "target_landscape": "The claimant is the obvious kill target.",
}
_STORE_DIMS = {**_SITUATION, "perspective": "healer", "action_phase": "night_action"}


def _written(monkeypatch, module) -> list[dict]:
    """Capture what `module` streams: its get_stream_writer hands back a list's append."""
    chunks: list[dict] = []
    monkeypatch.setattr(module, "get_stream_writer", lambda: chunks.append)
    return chunks


def _consulted(monkeypatch, *, sp_dims: dict, ob_dims: dict) -> dict:
    chunks = _written(monkeypatch, pipeline)
    now = datetime(2026, 1, 1)
    enriched = {
        "strategy_points": [RetrievedStrategyPoint(
            key="sp-1", matched_situation="q", strategy_point=StoredStrategyPoint(
                observation_count=1, last_observed=now, situation="composed sp situation",
                action="Protect the claimant.", dimensions=sp_dims))],
        "retrieved_observations": [RetrievedObservation(
            key="ob-1", matched_situation="q", observation=StoredObservation(
                observation_count=1, last_observed=now, situation="composed ob situation",
                outcome="The claimant survived.", dimensions=ob_dims))],
    }
    effects = TurnEffects(
        strategy_verdicts=[StrategyVerdict(strategy_index=1, verdict="follow", why="claim today")],
        memory_verdicts=[MemoryVerdict(memory_index=1, verdict="fully_applies", why="same board")],
    )
    pipeline._announce_memory_consulted(
        player_id="player_5", role="healer", day=2, round_num=0, action_phase="night_action",
        enriched_payload=enriched, retrieval_meta={"memory_enabled": True}, effects=effects)
    [chunk] = chunks
    return chunk


def _to_wire(data: dict) -> ev.DurableEvent:
    [event] = Translator().translate({"type": "custom", "ns": [], "data": data})
    return event


def test_consulted_lesson_carries_the_store_dimensions_verbatim(monkeypatch):
    chunk = _consulted(monkeypatch, sp_dims=_STORE_DIMS, ob_dims=_STORE_DIMS)
    event = _to_wire(chunk)
    assert isinstance(event, ev.MemoryConsulted)
    assert event.lessons[0].dimensions == _STORE_DIMS
    assert event.observations[0].dimensions == _STORE_DIMS
    # the composed one-line situation the agent read stays on the wire alongside
    assert event.lessons[0].situation == "composed sp situation"
    assert event.observations[0].situation == "composed ob situation"


def test_consulted_legacy_record_without_dimensions_gives_none(monkeypatch):
    event = _to_wire(_consulted(monkeypatch, sp_dims={}, ob_dims={}))
    assert event.lessons[0].dimensions is None
    assert event.observations[0].dimensions is None


def test_old_consulted_payload_without_the_key_still_translates():
    from tests.fixtures.translator_golden import _memory_consulted

    event = _to_wire(_memory_consulted("player_5", "healer", 2)["data"])
    assert event.lessons[0].dimensions is None


def _v6_cells() -> tuple[HealerNightObservation, HealerNightStrategyPoint]:
    obs = HealerNightObservation(
        **_SITUATION, perspective="healer", action_phase="night_action",
        approach="Protected the claimant.", impact_on_final_game_outcome="Positive.",
        immediate_response="The kill failed.", net_verdict="positive")
    sp = HealerNightStrategyPoint(
        **_SITUATION, perspective="healer", action_phase="night_action",
        direction="defensive", honesty="honest", action="Protect the loud claimant.")
    return obs, sp


class _Output:
    def __init__(self, observations, strategy_points):
        self.observations, self.strategy_points = observations, strategy_points


def test_extracted_v6_cells_carry_their_structured_fields(monkeypatch):
    chunks = _written(monkeypatch, orchestrator)
    obs, sp = _v6_cells()
    orchestrator._announce_memory_extracted(_Output([obs], [sp]), day=3)
    event = _to_wire(chunks[0])
    assert isinstance(event, ev.MemoryExtracted)
    # the same dump the store write keeps (store_ops: dimensions=model_dump)
    assert event.observations[0].dimensions == obs.model_dump(mode="json")
    assert event.strategy_points[0].dimensions == sp.model_dump(mode="json")
    assert event.observations[0].dimensions["info_landscape_class"] == "info_rich"
    assert event.strategy_points[0].dimensions["exposure_class"] == "safe"


def test_extracted_legacy_models_give_none(monkeypatch):
    chunks = _written(monkeypatch, orchestrator)
    legacy = Observation(perspective="healer", action_phase="night_action", situation="s",
                         information_landscape="i", game_phase="early", consensus_texture=None,
                         agent_exposure=None, approach="a", impact_on_final_game_outcome="o",
                         immediate_response="r", net_verdict="unclear")
    legacy_sp = StrategyPoint(perspective="healer", action_phase="night_action", situation="s",
                              information_landscape="i", game_phase="early",
                              consensus_texture=None, agent_exposure=None, action="act")
    orchestrator._announce_memory_extracted(_Output([legacy], [legacy_sp]), day=3)
    event = _to_wire(chunks[0])
    assert event.observations[0].dimensions is None
    assert event.strategy_points[0].dimensions is None
