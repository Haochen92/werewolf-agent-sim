"""Guard the v6 structured-residual dedup display: hide gated fields, show non-gated, v5 fallback."""

from datetime import datetime, timezone
from types import SimpleNamespace

from Agents.memory.deduplication.formatting import (
    _format_existing_observations,
    _residual_situation,
    _situation_for_dedup,
)
from Agents.schemas.memory import StoredObservation

_DIMS = {
    "situation": "Village split over a claimed investigator", "information_landscape": "one role claim",
    "players_alive": 6, "distance_to_parity": 2, "is_swing": False, "criticality_stakes": "recoverable but costly",
    "consensus_text": "two camps", "my_position": "aligned with the claim",
    "consensus_direction": "aligns_with_my_read", "heat_now": "low", "target_landscape": "accuser vs claimant",
    "perspective": "villager", "action_phase": "day_vote", "approach": "backed the investigator",
    "impact_on_final_game_outcome": "helped", "immediate_response": "deflected", "net_verdict": "positive",
}


def test_residual_shows_nongated_hides_gated():
    out = _residual_situation(_DIMS).lower()
    for shown in ("information landscape:", "my position:", "target landscape:", "heat now:"):
        assert shown in out
    assert out.startswith("situation:")
    for hidden in ("players_alive", "is_swing", "consensus_direction", "net_verdict",
                   "criticality stakes", "consensus text", "approach", "impact", "immediate", "perspective"):
        assert hidden not in out


def test_v5_falls_back_to_composed_prose():
    assert _situation_for_dedup({"situation": "x"}, "COMPOSED") == "COMPOSED"
    assert _situation_for_dedup({}, "COMPOSED") == "COMPOSED"


def test_v6_uses_structured_residual():
    assert _situation_for_dedup(_DIMS, "COMPOSED").startswith("situation:")


def test_stored_observation_persists_dimensions_backward_compat():
    now = datetime.now(timezone.utc)
    so = StoredObservation(observation_count=1, last_observed=now, situation="composed", dimensions=_DIMS)
    assert so.dimensions["my_position"] == "aligned with the claim"
    old = StoredObservation(observation_count=1, last_observed=now, situation="composed")
    assert old.dimensions == {}


def test_candidate_formatter_uses_residual_not_blob():
    item = SimpleNamespace(key="k1", score=0.9, value={
        "observation_count": 2, "situation": "composed-blob", "approach": "A", "outcome": "O", "dimensions": _DIMS,
    })
    out = _format_existing_observations([item])
    assert "information landscape:" in out
    assert "composed-blob" not in out  # residual replaces the prose blob for v6 entries
