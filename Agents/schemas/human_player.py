"""DTOs for the human seat — the interrupt() request/response contract.

``HumanTurnRequest`` is what the backend surfaces to the human (the ``interrupt()`` value);
``HumanTurnResponse`` is what the human sends back (the ``Command(resume=...)`` payload). Both are
internal records — never sent to a model — so they carry class/attribute docstrings for IDE hover
and exist to validate the frontend<->backend boundary. They are deliberately seat-agnostic: one
request/response shape covers discussion, votes, and night actions, with ``phase`` naming which.
"""

from pydantic import BaseModel, ConfigDict
from typing import Optional


class HumanTurnRequest(BaseModel):
    """Backend -> human: everything needed to act on this turn. Surfaced as the interrupt() value."""

    player_id: str
    role: str
    phase: str
    """The output_key this turn decides: day_channel | day_votes | wolf_channel | <role>_target."""
    day: int
    instruction: str
    """Human-readable ask for this phase."""
    valid_targets: list[str]
    """The legal vote/action targets to offer; empty for pure discussion."""
    can_pass: bool
    """Day discussion on a non-reactive turn — the human may decline to speak (a reactive turn must answer)."""
    dialogue: str
    """Today's public discussion so far."""
    day_summaries: str
    """Summaries of prior days."""
    surviving_players: list[str]
    dead_roster: str
    alive_roles: str
    """Public role census still in play."""
    firing_brief: str
    """Why the human is up this turn / whom they owe a response to (reactive)."""
    wolf_channel: str
    """Wolf-pack night transcript (non-empty only for a wolf seat)."""
    pack: str = ""
    """The wolf roster, comma-joined (non-empty only for a wolf seat — the payload is role-gated
    upstream, so other seats never carry it). Without it a night-1 wolf can only infer their own
    partner from the kill menu's exclusions."""
    investigator_results: str
    """Past investigation results (investigator seat only)."""
    vigilante_results: str
    """Past shot outcomes (vigilante seat only)."""
    previous_strategy: str
    """The human's own strategy note from last turn."""


class HumanTurnResponse(BaseModel):
    """Human -> backend: the chosen action. The Command(resume=...) payload, validated on the way in."""

    model_config = ConfigDict(extra="forbid")  # reject a malformed/unknown-field frontend payload

    message: str | None = None
    """Discussion text, or the wolf-night message; None/empty = said nothing."""
    target: str | None = None
    """The chosen vote/action target; must be one of the request's valid_targets."""
    pass_turn: bool = False
    """Day discussion only: decline to speak."""
    delegate: bool = False
    """Hand this turn to the agent path: the seat's LLM plays it instead (the server's
    AFK-timeout default). A delegate response carries nothing else — no message,
    target, or pass — and is legal for every phase."""
