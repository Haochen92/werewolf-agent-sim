"""Private-information leak checks for live game transcripts.

NOT pytest unit tests: these checkers need a live game's ``prompt_log``
(the global populated in ``Agents.nodes``) plus the role assignment, and
they return leak lists instead of asserting. Drive them through
``run_leak_tests(prompt_log, roles)`` after ``run_game(...)`` — see
``exercise_7_minimal.ipynb``. Functions are named ``check_*`` (not
``test_*``) precisely so pytest's collector skips them; renaming them back
re-breaks the full suite with fixture errors.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

NO_WOLF_MESSAGES = "No messages yet."
NO_INVESTIGATIONS = "No investigations yet."
NO_VIGILANTE_RESULTS = "Nothing learned from your shots yet."


def _record_leak(leaks: list[str], message: str) -> None:
    leaks.append(message)
    print(message)


def check_wolf_identity_isolation(
    prompt_log: list[dict[str, Any]], roles: dict[str, str]
) -> list[str]:
    """Wolf names should only appear in wolf agents' private prompt fields."""
    leaks: list[str] = []
    wolf_names = [player for player, role in roles.items() if role == "wolf"]

    for entry in prompt_log:
        if entry["player_role"] == "wolf":
            continue

        prompt_input = entry["prompt_input"]
        if prompt_input["surviving_wolves"]:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                f"received surviving_wolves: {prompt_input['surviving_wolves']}",
            )

        leaked_names = [
            wolf_name for wolf_name in wolf_names if wolf_name in prompt_input["surviving_wolves"]
        ]
        if leaked_names:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                f"received wolf identities: {', '.join(leaked_names)}",
            )

    return leaks


# The output_keys a WOLF player's decision produces: wolf_channel (night discussion+vote),
# day_channel (day discussion), day_votes (day elimination vote). As of 2026-07-05 the wolf
# channel rides all three (day exposure added); any other pairing carrying it is a leak.
_WOLF_OUTPUT_KEYS = frozenset({"wolf_channel", "day_channel", "day_votes"})


def check_wolf_channel_isolation(prompt_log: list[dict[str, Any]]) -> list[str]:
    """Wolf channel content may appear only in a WOLF player's own prompts.

    Re-scoped 2026-07-05 when wolves gained day-turn visibility of their channel (was:
    night-only, keyed on output_key == "wolf_channel"). The true invariant is by *player*,
    not by phase: the channel is the wolves' own information, so it may reach any wolf
    prompt (night discussion + day discuss/vote) but NEVER a non-wolf player's prompt.
    Kept strict — a wolf entry is only exempt on a known wolf output_key.
    """
    leaks: list[str] = []
    for entry in prompt_log:
        if entry["player_role"] == "wolf" and entry["output_key"] in _WOLF_OUTPUT_KEYS:
            continue

        wolf_channel = entry["prompt_input"]["wolf_channel"]
        if wolf_channel and wolf_channel != NO_WOLF_MESSAGES:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                f"received wolf_channel in {entry['output_key']} phase",
            )

    return leaks


def check_investigator_results_isolation(prompt_log: list[dict[str, Any]]) -> list[str]:
    """Investigation results should only appear in investigator prompts."""
    leaks: list[str] = []
    for entry in prompt_log:
        if entry["player_role"] == "investigator":
            continue

        results = entry["prompt_input"]["investigator_results"]
        if results and results != NO_INVESTIGATIONS:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                "received investigator_results",
            )

    return leaks


def check_healer_target_absent(prompt_log: list[dict[str, Any]]) -> list[str]:
    """Healer target should never be included in prompt input."""
    leaks: list[str] = []
    for entry in prompt_log:
        prompt_input = entry["prompt_input"]
        if "healer_target" in prompt_input and prompt_input["healer_target"]:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                "received healer_target",
            )
    return leaks


def check_vigilante_results_isolation(prompt_log: list[dict[str, Any]]) -> list[str]:
    """Vigilante shot feedback (SK confirmations) should only appear in vigilante prompts."""
    leaks: list[str] = []
    for entry in prompt_log:
        if entry["player_role"] == "vigilante":
            continue

        results = entry["prompt_input"].get("vigilante_results", "")
        if results and results != NO_VIGILANTE_RESULTS:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                "received vigilante_results",
            )

    return leaks


def check_gated_candidate_isolation(
    prompt_log: list[dict[str, Any]], gated_candidates: Iterable[str]
) -> list[str]:
    """A novelty-gated candidate message was SILENCED — its text must never reach any agent's
    prompt. The day-channel formatters drop passed markers (where gated_candidate lives), so a
    correctly-behaving pipeline never surfaces it; this scans every recorded prompt_input for any
    gated candidate substring as a standing guard against a formatter/template regression."""
    leaks: list[str] = []
    needles = [c for c in gated_candidates if c and c.strip()]
    for entry in prompt_log:
        blob = repr(entry.get("prompt_input", {}))
        for needle in needles:
            if needle in blob:
                _record_leak(
                    leaks,
                    f"LEAK: {entry['player_id']} ({entry['player_role']}) received a "
                    f"novelty-gated candidate in prompt_input: {needle!r}",
                )
    return leaks


# Tokens that only appear in a prompt_input if a PlayerRead OBJECT was rendered into it (the field
# name is schema vocabulary, not game prose). prompt_input holds template VARIABLES only, so the JSON
# response examples in the templates — which legitimately contain "suspected_role" — never trip this.
_READ_STRUCT_TOKENS = ("suspected_role", "'reads':", '"reads":')

def check_reads_isolation(
    prompt_log: list[dict[str, Any]],
    reads_log: Iterable[dict[str, Any]],
    public_text: str = "",
) -> list[str]:
    """Reads are PRIVATE — an agent's honest role suspicions (a wolf's read labels its packmate
    "wolf") must never reach another agent's prompt_input. Reads never enter graph state by
    construction (they live on typed TurnEffects and actor nodes do not commit them), so this is a standing
    regression guard against a formatter/template regression.

    Two passes, tuned by the 2026-07-09 smoke (the naive why-substring scan false-positived on
    shared game vocabulary — "confirmed healer" lives in public discussion, store memories, and the
    author's own strategy note all at once):
      1. STRUCTURAL (primary): any prompt_input containing a read-object token (`suspected_role`, a
         `reads` key) means read objects were rendered somewhere — the realistic regression vector.
      2. PROSE (secondary): long whys (>=40 chars — short ones are generic game vocabulary) are
         scanned as substrings, but only against OTHER players' prompts (the author's own strategy
         note legitimately echoes its own reads) and only when the why does not itself appear in
         ``public_text`` (the game's public channel + summaries — shared vocabulary can't be
         attributed to a leak). The prose pass also EXCLUDES the recipient's own-prose fields
         (``previous_strategy``): text the recipient authored can independently converge on the
         same phrasing of a public event as someone else's why — 2026-07-17, this exact case
         (needle at the 40-char floor, "abstained during the serial killer lynch") false-halted
         the v7 run. A match inside recipient-authored prose is convergence, not receipt."""
    leaks: list[str] = []
    blobs = [(entry, repr(entry.get("prompt_input", {}))) for entry in prompt_log]
    # Recipient-authored-by-construction fields: excluded from the PROSE pass only (the structural
    # pass still sees the full prompt_input — a rendered read OBJECT anywhere stays a leak).
    _OWN_PROSE_FIELDS = ("previous_strategy",)
    prose_blobs = [
        (entry, repr({k: v for k, v in entry.get("prompt_input", {}).items()
                      if k not in _OWN_PROSE_FIELDS}))
        for entry in prompt_log
    ]

    for entry, blob in blobs:
        for token in _READ_STRUCT_TOKENS:
            if token in blob:
                _record_leak(
                    leaks,
                    f"LEAK: {entry['player_id']} ({entry['player_role']}) has a rendered "
                    f"read object in prompt_input (token {token!r})",
                )
                break

    for rec in reads_log:
        author = rec.get("player_id", "")
        needles = [
            why.strip()
            for why in (r.get("why", "") for r in rec.get("reads", []))
            if why and len(why.strip()) >= 40 and why.strip() not in public_text
        ]
        if not needles:
            continue
        for entry, blob in prose_blobs:
            if entry["player_id"] == author:
                continue
            for needle in needles:
                if needle in blob:
                    _record_leak(
                        leaks,
                        f"LEAK: {entry['player_id']} ({entry['player_role']}) received "
                        f"{author}'s private read why-text in prompt_input: {needle!r}",
                    )
    return leaks


def check_eliminated_players_excluded(
    prompt_log: list[dict[str, Any]], eliminated_players: Iterable[str]
) -> list[str]:
    """Eliminated players should receive no prompts after their elimination day."""
    leaks: list[str] = []
    elimination_day_by_player: dict[str, int] = {}

    for player in eliminated_players:
        for entry in prompt_log:
            day_channel = entry["prompt_input"]["day_channel"]
            if f"Player {player} has been voted out" in day_channel or (
                f"{player} was killed by the wolves last night" in day_channel
            ):
                elimination_day_by_player[player] = entry["day"]
                break

    for entry in prompt_log:
        player = entry["player_id"]
        elimination_day = elimination_day_by_player.get(player)
        if elimination_day is not None and entry["day"] > elimination_day:
            _record_leak(
                leaks,
                f"LEAK: eliminated player {player} received prompt on day {entry['day']}",
            )

    return leaks


def run_leak_tests(
    prompt_log: list[dict[str, Any]],
    roles: dict[str, str],
    eliminated_players: Iterable[str] = (),
    gated_candidates: Iterable[str] = (),
    reads_log: Iterable[dict[str, Any]] = (),
    public_text: str = "",
) -> list[str]:
    print("=== Running Leak Tests ===")
    leaks = [
        *check_wolf_identity_isolation(prompt_log, roles),
        *check_wolf_channel_isolation(prompt_log),
        *check_investigator_results_isolation(prompt_log),
        *check_vigilante_results_isolation(prompt_log),
        *check_healer_target_absent(prompt_log),
        *check_eliminated_players_excluded(prompt_log, eliminated_players),
        *check_gated_candidate_isolation(prompt_log, gated_candidates),
        *check_reads_isolation(prompt_log, reads_log, public_text),
    ]
    print("=== Leak Tests Complete ===")
    return leaks
