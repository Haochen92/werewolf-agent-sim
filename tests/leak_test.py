"""Private-information leak checks for live game transcripts.

NOT pytest unit tests: these checkers need a live game's ``prompt_log``
(the global populated in ``Agents.nodes``) plus the role assignment, and
they return leak lists instead of asserting. Drive them through
``run_leak_tests(prompt_log, roles, **leak_inputs(result))`` after ``run_game(...)``:
``leak_inputs`` lifts the dead roster, the held lines and the night records out of the
final game state, so every checker that needs more than the prompt log is fed (before
2026-10-14 the batch runner passed none of them, and those checkers were no-ops on live
games). Functions are named ``check_*`` (not ``test_*``) precisely so pytest's collector
skips them; renaming them back re-breaks the full suite with fixture errors.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.roles import ROLE_SPECS

NO_WOLF_MESSAGES = "No messages yet."
NO_INVESTIGATIONS = "No investigations yet."
NO_VIGILANTE_RESULTS = "Nothing learned from your shots yet."


def _is_wolf(role: str) -> bool:
    """A role of the pack: the chanteuse and the illusionist (and the nine-seat wolf, for old logs)."""
    spec = ROLE_SPECS.get(role)
    return spec is not None and spec.pack


def _record_leak(leaks: list[str], message: str) -> None:
    leaks.append(message)
    print(message)


def check_wolf_identity_isolation(
    prompt_log: list[dict[str, Any]], roles: dict[str, str]
) -> list[str]:
    """Wolf names should only appear in wolf agents' private prompt fields."""
    leaks: list[str] = []
    wolf_names = [player for player, role in roles.items() if _is_wolf(role)]

    for entry in prompt_log:
        if _is_wolf(entry["player_role"]):
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


# The output_keys a WOLF player's decision produces: wolf_channel (the pack's chat), kill_target
# (the carrier's kill), each wolf's skill field (block_target, conceal), day_channel (day
# discussion), day_votes (day elimination vote); wolf_vote is the nine-seat pack vote, kept for
# old logs. The wolf channel rides all of them; any other pairing carrying it is a leak.
_WOLF_OUTPUT_KEYS = frozenset({
    "wolf_channel", "wolf_vote", "kill_target", "day_channel", "day_votes",
    *(spec.target_field for spec in ROLE_SPECS.values() if spec.pack and spec.target_field),
})


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
        if _is_wolf(entry["player_role"]) and entry["output_key"] in _WOLF_OUTPUT_KEYS:
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
    """Investigation results should only appear in investigator prompts. A nine-seat field: the
    ten-seat game keeps every result in the night record (check_night_record_isolation)."""
    leaks: list[str] = []
    for entry in prompt_log:
        if entry["player_role"] == "investigator":
            continue

        results = entry["prompt_input"].get("investigator_results", "")
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
    """Vigilante shot feedback (SK confirmations) should only appear in vigilante prompts. A
    nine-seat field, like investigator_results (see check_night_record_isolation)."""
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


def check_night_record_isolation(
    prompt_log: list[dict[str, Any]], records: Iterable[Any], roles: dict[str, str]
) -> list[str]:
    """A night record's result is its actor's alone: its outcome text may reach only the actor's
    own prompts, and a pack record (actor "wolves") only the wolves'. ``records`` is the game's
    night_actions (NightActionRecord objects or their dicts); the ten-seat successor of the
    investigator_results / vigilante_results checks."""
    leaks: list[str] = []
    for record in records:
        actor = record["actor"] if isinstance(record, dict) else record.actor
        outcome = record["outcome"] if isinstance(record, dict) else record.outcome
        if not outcome or not outcome.strip():
            continue
        for entry in prompt_log:
            if actor == PACK_ACTOR:
                allowed = _is_wolf(roles.get(entry["player_id"], entry["player_role"]))
            else:
                allowed = entry["player_id"] == actor
            if allowed:
                continue
            if outcome in entry["prompt_input"].get("night_actions", ""):
                _record_leak(
                    leaks,
                    f"LEAK: {entry['player_id']} ({entry['player_role']}) received "
                    f"{actor}'s night record: {outcome!r}",
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
         the v7 run. A match inside recipient-authored prose is convergence, not receipt. The pack's
         chat (``wolf_channel``) is excluded the same way: only wolves write it and only wolves read
         it, so a why a wolf also wrote there was shared with its packmate on purpose (2026-10-11, a
         ten-seat pilot game flagged the chanteuse's own chat line in the illusionist's prompt)."""
    leaks: list[str] = []
    blobs = [(entry, repr(entry.get("prompt_input", {}))) for entry in prompt_log]
    # Recipient-authored-by-construction fields: excluded from the PROSE pass only (the structural
    # pass still sees the full prompt_input — a rendered read OBJECT anywhere stays a leak).
    _OWN_PROSE_FIELDS = ("previous_strategy", "wolf_channel")
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


# A prompt whose output key is not a day turn is a night turn: the pack's chat and kill, and every
# role's own night field.
_DAY_OUTPUT_KEYS = frozenset({"day_channel", "day_votes"})


def check_eliminated_players_excluded(
    prompt_log: list[dict[str, Any]], deaths: Iterable[Any]
) -> list[str]:
    """A dead player gets no prompt after its death. ``deaths`` is the game's dead roster
    (DeathRecord objects or their dicts): a player lynched on day D may not be prompted that night
    or later; a player killed on night D may not be prompted from day D+1 on. (Before 2026-10-14
    this check read the elimination day out of the game master's prose, which the ten-seat game
    no longer writes in that form.)"""
    leaks: list[str] = []
    for death in deaths:
        player = death["player"] if isinstance(death, dict) else death.player
        day = death["day"] if isinstance(death, dict) else death.day
        phase = death["phase"] if isinstance(death, dict) else death.phase
        for entry in prompt_log:
            if entry["player_id"] != player:
                continue
            after_death = entry["day"] > day or (
                phase == "day" and entry["day"] == day and entry["output_key"] not in _DAY_OUTPUT_KEYS
            )
            if after_death:
                _record_leak(
                    leaks,
                    f"LEAK: dead player {player} ({phase} {day}) received a prompt on day "
                    f"{entry['day']} ({entry['output_key']})",
                )
    return leaks


def check_held_lines_reach_only_their_author(
    prompt_log: list[dict[str, Any]], held_lines: Iterable[tuple[str, str]]
) -> list[str]:
    """A line held back by the echo gate or the opening filter (Phase 2) was never said: its text
    is shown to its author, marked as unheard, and must reach no other player's prompt.
    ``held_lines`` is (author, held text) pairs, the gated_candidate of each held pass marker.
    (check_gated_candidate_isolation predates the author seeing their own held line and flags
    the author too; this is the check for the current rule.)"""
    leaks: list[str] = []
    for author, text in held_lines:
        if not text or not text.strip():
            continue
        for entry in prompt_log:
            if entry["player_id"] == author:
                continue
            if text in repr(entry.get("prompt_input", {})):
                _record_leak(
                    leaks,
                    f"LEAK: {entry['player_id']} ({entry['player_role']}) received "
                    f"{author}'s held line in prompt_input: {text!r}",
                )
    return leaks


def check_round_players_are_seat_ids(
    round_player_lists: Iterable[Any], roles: dict[str, str]
) -> list[str]:
    """The players of a round (``round_players`` on the state, ``round_opened.players`` on the
    wire, public) must be bare seat ids: anything else, a role, a faction label, a dict with a
    role in it, would tell every viewer something private."""
    leaks: list[str] = []
    for players in round_player_lists:
        if not isinstance(players, list):
            _record_leak(leaks, f"LEAK: round players are not a list of seat ids: {players!r}")
            continue
        for player in players:
            if not isinstance(player, str) or player not in roles:
                _record_leak(leaks, f"LEAK: round players hold something other than a seat id: {player!r}")
    return leaks


def leak_inputs(result: dict[str, Any]) -> dict[str, Any]:
    """The checker inputs a finished game's state holds: the dead roster, the text of every held
    line (a gated or filtered pass marker's candidate), and the night records. Pass as
    ``run_leak_tests(prompt_log, roles, **leak_inputs(result))``."""
    held = []
    for entry in result.get("day_channel") or []:
        candidate = entry["gated_candidate"] if isinstance(entry, dict) else entry.gated_candidate
        if candidate and candidate.strip():
            held.append(candidate)
    return {
        "deaths": result.get("dead_roster") or [],
        "gated_candidates": held,
        "night_records": result.get("night_actions") or [],
    }


def run_leak_tests(
    prompt_log: list[dict[str, Any]],
    roles: dict[str, str],
    deaths: Iterable[Any] = (),
    gated_candidates: Iterable[str] = (),
    reads_log: Iterable[dict[str, Any]] = (),
    public_text: str = "",
    night_records: Iterable[Any] = (),
) -> list[str]:
    print("=== Running Leak Tests ===")
    leaks = [
        *check_wolf_identity_isolation(prompt_log, roles),
        *check_wolf_channel_isolation(prompt_log),
        *check_investigator_results_isolation(prompt_log),
        *check_vigilante_results_isolation(prompt_log),
        *check_night_record_isolation(prompt_log, night_records, roles),
        *check_healer_target_absent(prompt_log),
        *check_eliminated_players_excluded(prompt_log, deaths),
        *check_gated_candidate_isolation(prompt_log, gated_candidates),
        *check_reads_isolation(prompt_log, reads_log, public_text),
    ]
    print("=== Leak Tests Complete ===")
    return leaks
