"""Which decision each extracted observation describes (owner, 2026-10-13; decisions §13).

The deterministic grade of a decision (consolidation/grading.py) can stand beside the extraction
judge's verdict only when an observation names its decision. Extraction from now on fills the
fields itself (``decision_day``, and ``pack_turn`` on a wolf's night); observations extracted before
are tagged by a model pass over the game's saved extraction input (this module, run by
scripts/tag_observation_decisions.py).

Every tag is checked against the decisions the saved input shows the role making: the engine's
night-action lines, the vote results, the wolves' talk and the day discussion. These lines are
written by code, so reading them is a structural parse. A declined night action leaves no line, so a
tag that matches nothing is "not_recorded", not necessarily wrong; the accuracy check is a read of a
sample against the record.
"""

from __future__ import annotations

import json
import re
from typing import Any

from Agents.prompts.compose import rules_block
from Agents.prompts.extraction.decision_tags import DECISION_TAG_PROMPT

PACK_ROLES = ("chanteuse", "illusionist")
_DISCUSSION = re.compile(r"^\[Day (\d+)\] (player_\d+) \(")
_VOTE_HEADER = re.compile(r"vote result for day (\d+)", re.I)
_VOTER = re.compile(r"^\s+(player_\d+) voted")
_NIGHT = re.compile(r"^Night (\d+): (player_\d+) \(")
_WOLF_TALK = re.compile(r"^\[Day (\d+), Round (\d+)\] (player_\d+)( votes)?:")
_STATED = {"night_action": re.compile(r"\bnight\s+(\d+)\b", re.I),
           "day_discussion": re.compile(r"\bday\s+(\d+)\b", re.I),
           "day_vote": re.compile(r"\bday\s+(\d+)\b", re.I)}


def recorded_decisions(formatted_discussions: str) -> set[tuple[str, str, int, str]]:
    """(player, phase, day, pack turn) for every decision the saved input shows: who spoke on which
    day, who voted, whose night action the engine resolved, and each wolf's chat and carrier turns."""
    found: set[tuple[str, str, int, str]] = set()
    section, vote_day = "", None
    for line in formatted_discussions.splitlines():
        if line.startswith("=== "):
            section, vote_day = line, None
            continue
        if "Day Discussions" in section:
            if (m := _VOTE_HEADER.search(line)):
                vote_day = int(m.group(1))
            elif vote_day is not None and (m := _VOTER.match(line)):
                found.add((m.group(1), "day_vote", vote_day, ""))
            elif (m := _DISCUSSION.match(line)):
                vote_day = None
                found.add((m.group(2), "day_discussion", int(m.group(1)), ""))
        elif "Wolf Night" in section and (m := _WOLF_TALK.match(line)):
            turn = "kill" if m.group(4) else "chat"
            found.add((m.group(3), "night_action", int(m.group(1)), turn))
        elif "Night Actions" in section and (m := _NIGHT.match(line)):
            found.add((m.group(2), "night_action", int(m.group(1)), "skill"))
    return found


def tag_status(roles: dict[str, str], perspective: str, phase: str, day: int, pack_turn: str,
               recorded: set) -> str:
    """'several' (day 0), 'recorded' (the role made that decision per the saved input), or
    'not_recorded' (no line shows it: a declined night action, or a wrong tag)."""
    if day == 0:
        return "several"
    holder = next((p for p, r in roles.items() if r == perspective), None)
    if phase != "night_action":
        turns = ("",)
    elif perspective in PACK_ROLES:
        turns = ("chat", "kill", "skill") if pack_turn == "several" else (pack_turn,)
    else:
        turns = ("skill",)  # every other role's night action is its own line
    return "recorded" if any((holder, phase, day, t) in recorded for t in turns) else "not_recorded"


def stated_day(observation: dict) -> int | None:
    """The one day or night number the observation's own text states for its phase (approach first,
    then situation), or None when it states none or several."""
    pattern = _STATED.get(observation.get("action_phase", ""))
    if pattern is None:
        return None
    for text in (observation.get("approach", ""), observation.get("situation", "")):
        days = {int(d) for d in pattern.findall(text or "")}
        if len(days) == 1:
            return days.pop()
        if days:
            return None
    return None


def _lessons(observations: list[dict]) -> str:
    return "\n".join(f"[{i}] {o['perspective']} / {o['action_phase']}\n  situation: {o.get('situation', '')}\n"
                     f"  did: {o.get('approach', '')}" for i, o in enumerate(observations, 1))


def tag_prompt(case: dict) -> str:
    """The tagger's prompt for one game's observations (``case``: the extraction case as stored)."""
    from Agents.memory.extraction.inputs import extraction_inputs_from_frozen_case

    inputs = extraction_inputs_from_frozen_case(case)
    return DECISION_TAG_PROMPT.format(rules=rules_block(inputs.get("lineup") or []),
                                      record=case.get("formatted_discussions", ""),
                                      roles=json.dumps(case.get("roles", {})),
                                      lessons=_lessons(case["observations"]))


def tag_rows(case: dict, tags: Any) -> list[dict]:
    """One row per observation: its tag, the tag's status against the saved input, and the day its
    own text states (the free check)."""
    recorded = recorded_decisions(case.get("formatted_discussions", ""))
    by_index = {t.index: t for t in (tags.tags if tags is not None else [])}
    rows = []
    for i, o in enumerate(case["observations"], 1):
        t = by_index.get(i)
        pack_turn = (t.pack_turn if o["perspective"] in PACK_ROLES and o["action_phase"] == "night_action"
                     else "none") if t else None
        row = {"game_id": case["game_id"], "index": i, "perspective": o["perspective"],
               "action_phase": o["action_phase"], "approach": o.get("approach", ""),
               "decision_day": t.decision_day if t else None, "pack_turn": pack_turn,
               "stated_day": stated_day(o)}
        row["status"] = (tag_status(case.get("roles", {}), o["perspective"], o["action_phase"], t.decision_day,
                                    pack_turn, recorded) if t else "untagged")
        rows.append(row)
    return rows
