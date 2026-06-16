"""Memory-data validators / coercions applied at store-write (not prompt text).

Kept separate from prompt composition: these guard the EXTRACTED data before it lands in the
store (e.g. an anti-hindsight check on consensus_direction), they do not build any prompt.
"""

from __future__ import annotations


# Prose markers of an unformed consensus — used to validate consensus_direction against the prose
# (the user's "validate them against each other"): if the room has no consensus, a directional enum is
# a contradiction (often a hindsight leak), so coerce it to no_clear_direction. Catches the clear
# cases the prompt rule still misses (~7% residual); subtler hindsight cases need an LLM relabel.
_NO_CONSENSUS_MARKERS = (
    "fractured", "no clear consensus", "no consensus", "no real consensus",
    "deadlock", "splintered", "no consensus has formed",
)


def coerce_consensus_direction(situation_text: str, consensus_direction: str | None) -> str | None:
    """If the situation prose says there is no consensus but the enum is directional, return
    no_clear_direction; otherwise return the enum unchanged."""
    if consensus_direction in ("aligns_with_my_read", "opposes_my_read"):
        low = (situation_text or "").lower()
        if any(m in low for m in _NO_CONSENSUS_MARKERS):
            return "no_clear_direction"
    return consensus_direction
