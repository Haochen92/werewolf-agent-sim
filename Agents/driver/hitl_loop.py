"""The HITL resume driver — collect a validated human action for a pending interrupt.

``collect_human_response`` is the retry loop between the graph's ``HumanTurnRequest`` and a
``HumanTurnResponse`` that passes ``validate_human_response``: a rejected attempt surfaces its error
back to the human with the SAME still-pending request (no graph round-trip), and only a validated
response reaches ``Command(resume=...)`` — main.py owns the actual invoke loop.

``_send_request`` is the transport, currently the local CLI (print + ``input()``) for smoke runs.
The Phase-5 server driver replaces it with an SSE push + awaited action POST; this retry loop stays
unchanged. It returns a RAW dict on purpose — all judgment lives in ``validate_human_response``.
"""

import re
import sys
import textwrap
from typing import Any

from Agents.schemas.human_player import HumanTurnRequest, HumanTurnResponse
from Agents.turn.human_turn import HumanTurnContractError, validate_human_response

MAX_ATTEMPTS = 5

# ANSI styling for the CLI render (TTY only). Verbose seats (deepseek-v4-pro) make the raw
# transcript hard to scan — the speaker gets a colored bold label on its own line, the message is
# wrapped/indented under it, and everything already shown at the previous prompt renders dim so
# only the new tail draws the eye.
_BOLD_CYAN = "\033[1;36m"
_BOLD_YELLOW = "\033[1;33m"
_DIM = "\033[2m"
_RESET = "\033[0m"
_WRAP_WIDTH = 100

# Dialogue text as of the previous render, per (day, phase-group) — lets the next render dim the
# already-seen prefix. Process-local by design: the CLI driver and the game share one process.
_seen_dialogue: dict[int, str] = {}


def collect_human_response(request: HumanTurnRequest) -> HumanTurnResponse:
    err: str | None = None
    for _ in range(MAX_ATTEMPTS):
        response = _send_request(request, err)
        try:
            return validate_human_response(request, response)
        except HumanTurnContractError as e:
            err = str(e)

    # Placeholder abandonment policy for the CLI smoke driver: give up and abort the game. The real
    # transport replaces this with a turn timeout -> agent-seat fallback / game expiry.
    raise RuntimeError(f"failed to receive validated inputs from human after {MAX_ATTEMPTS} attempts")


def _send_request(request: HumanTurnRequest, err_message: str | None) -> Any:
    """CLI transport: render the pending request in the terminal, read one action, return it raw
    (a dict in ``HumanTurnResponse`` field shape) — validation happens in the caller's loop."""
    if err_message:
        print(f"\n!! {err_message}")
    else:
        _render_request(request)

    if request.phase == "day_channel":
        hint = " (or 'pass')" if request.can_pass else ""
        message = input(f"say{hint}> ").strip()
        if request.can_pass and message.lower() == "pass":
            return {"pass_turn": True}
        return {"message": message}

    if request.phase == "wolf_channel":
        return {"message": input("pack message> ").strip()}

    target = input("target> ").strip()
    return {"target": _resolve_target(target, request.valid_targets)}


def _render_request(request: HumanTurnRequest) -> None:
    """Print the board the way the LLM would see it — public context first, then this seat's
    private sections (non-empty only when the role has them), then the ask."""
    print(f"\n{'=' * 70}")
    print(f"Day {request.day} — you are {request.player_id} ({request.role}) — {request.phase}")
    print(f"{'=' * 70}")

    sections = [
        ("Alive roles", request.alive_roles),
        ("Dead", request.dead_roster),
        ("Previous days", request.day_summaries),
        ("Today's discussion", _format_transcript(request.dialogue, request.day, request.player_id)),
        ("Why you're up", request.firing_brief),
        ("Your pack", request.pack),
        ("Wolf channel", _format_transcript(request.wolf_channel, -request.day, request.player_id)),
        ("Your investigations", request.investigator_results),
        ("Your shots", request.vigilante_results),
        ("Your strategy note", request.previous_strategy),
    ]
    for title, body in sections:
        if body and body.strip():
            print(f"\n--- {title} ---\n{body.strip()}")

    print(f"\n>>> {request.instruction}")
    if request.valid_targets:
        menu = "  ".join(f"[{i}] {t}" for i, t in enumerate(request.valid_targets, 1))
        print(f"Targets: {menu}")


# Only real cast names start a turn — a message line like "Verdict: he lies" must not.
_SPEAKER_LINE = re.compile(r"^(player_\d+|game_master)(:| votes:)\s*", re.MULTILINE)


def _format_transcript(text: str, seen_key: int, self_id: str) -> str:
    """Re-render a 'player: message' transcript for terminal reading: the speaker becomes a bold
    colored label on its own line (yellow for you, cyan for the rest), the message is wrapped and
    indented under it, and the part already shown at this seat's previous prompt renders dim with a
    'new since your last turn' divider before the fresh tail. Plain text when stdout isn't a TTY.
    ``seen_key`` scopes the seen-tracking (day; negated for the wolf channel so the two transcripts
    never collide)."""
    if not text or not text.strip() or not _SPEAKER_LINE.search(text):
        return text  # placeholder prose ("No messages yet.") — nothing to restyle
    if not sys.stdout.isatty():
        return text

    previously_seen = _seen_dialogue.get(seen_key, "")
    if not text.startswith(previously_seen):
        previously_seen = ""  # transcript changed shape (new day/phase) — show everything fresh
    _seen_dialogue[seen_key] = text

    def styled(chunk: str, dim: bool) -> list[str]:
        out: list[str] = []
        for match, body in _split_turns(chunk):
            speaker = match.group(1)
            color = _BOLD_YELLOW if speaker == self_id else _BOLD_CYAN
            label = f"{speaker}{match.group(2).rstrip()}"
            if out:
                out.append("")
            out.append(f"{_DIM if dim else color}{label}{_RESET}")
            wrapped = textwrap.fill(body.strip(), width=_WRAP_WIDTH,
                                    initial_indent="  ", subsequent_indent="  ")
            out.append(f"{_DIM}{wrapped}{_RESET}" if dim else wrapped)
        return out

    lines = styled(previously_seen, dim=True)
    fresh = text[len(previously_seen):]
    if previously_seen and fresh.strip():
        lines.append(f"{_BOLD_YELLOW}· · · new since your last turn · · ·{_RESET}")
    lines.extend(styled(fresh, dim=False))
    return "\n".join(lines)


def _split_turns(chunk: str):
    """Yield (speaker_match, message_body) per speaker turn in a transcript chunk."""
    matches = list(_SPEAKER_LINE.finditer(chunk))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(chunk)
        yield match, chunk[match.end():end]


def _resolve_target(raw: str, valid_targets: list[str]) -> str:
    """Map a menu number to its target; pass names (and typos) through untouched — the validator is
    the sole judge of what's legal, and its error re-prompts the human."""
    if raw.isdigit() and 1 <= int(raw) <= len(valid_targets):
        return valid_targets[int(raw) - 1]
    return raw
