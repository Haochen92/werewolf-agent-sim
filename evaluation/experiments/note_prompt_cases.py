"""Select the screening cases for the private-note rewrite: the current note wording against the new one.

Record: evidence/reasoning_failures/experiment_log.md §6. The new wording (Agents/prompts/memory/context.py,
2026-10-16) splits the note into Changed / Reasoning / Plan, treats reads as hypotheses and asks whether
an updated conclusion changes the value of speaking, voting or acting. The arms are the prompt (the current
wording runs from a worktree); the cases are taken from earlier frozen sets, unchanged, so the frozen
previous note is identical in both arms:

- R1's 2x2: the healer's turn right after player_7's admission, as played and with the injected roleblock
  line (§4), so the prompt effect is separated from the injection;
- controls where passing, or keeping the previous plan, is right;
- positives where the game's seat misreasoned;
- votes from both games: positives (the investigator voting the healer; 403f4dbc's day-5 vigilante) and
  controls (right in the game, and right because an earlier conclusion still holds).

  poetry run python evaluation/experiments/note_prompt_cases.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path("evidence/reasoning_failures/data")
OUT = DATA / "note_prompt/screen_cases.jsonl"

# (source file, game, slice, phase, day, speaker, entry seq or None for a vote, screen role, why)
PICKS = [
    ("deduction_injection/cases.jsonl", "2f19d908", "as_played", "day_discussion", 2, "player_8", 16,
     "r1", "R1: knows it was blocked, player_7 admitted visiting it; original line"),
    ("deduction_injection/cases.jsonl", "2f19d908", "injected", "day_discussion", 2, "player_8", 16,
     "r1", "R1: same turn with the injected roleblock line"),
    ("deduction_injection/cases.jsonl", "2f19d908", "as_played", "day_discussion", 2, "player_8", 6,
     "control", "healer's opening turn: only its own block known, nothing worth saying yet"),
    ("haiku_effort_replay/turn_cases.jsonl", "2f19d908", "claim_read", "day_discussion", 3, "player_4", 12,
     "positive", "listed the healer as unclaimed; argued protecting a blocked player is pointless"),
    ("haiku_effort_replay/turn_cases.jsonl", "2f19d908", "claim_read", "day_discussion", 3, "player_10", 10,
     "control", "its earlier reasoning (claims fit, player_6 unclaimed) still holds"),
    ("haiku_effort_replay/turn_cases.jsonl", "2f19d908", "claim_read", "day_discussion", 3, "player_2", 11,
     "control", "the sentinel whose watch confirmed the healer's visit"),
    ("haiku_effort_replay/turn_cases.jsonl", "403f4dbc", "visit", "day_discussion", 3, "player_4", 14,
     "positive", "turned 'I visited nobody' round against a watch"),
    ("haiku_effort_replay/turn_cases.jsonl", "403f4dbc", "visit", "day_discussion", 6, "player_10", 5,
     "control", "its original line read the empty watch right"),
    ("haiku_effort_replay/vote_cases.jsonl", "2f19d908", "vote", "day_vote", 3, "player_5", None,
     "positive", "voted out the healer who had protected it"),
    ("haiku_effort_replay/vote_cases.jsonl", "2f19d908", "vote", "day_vote", 3, "player_4", None,
     "positive", "voted player_6 in the game; on replay at low it voted the healer 10 in 10"),
    ("haiku_effort_replay/vote_cases.jsonl", "2f19d908", "vote", "day_vote", 3, "player_10", None,
     "control", "its earlier conclusion (killer among the unclaimed) still holds; right 10 in 10"),
    ("haiku_effort_replay/vote_cases.jsonl", "403f4dbc", "vote_compare", "day_vote", 3, "player_2", None,
     "control", "right in the game and 10 in 10 on replay"),
    ("haiku_effort_replay/vote_cases.jsonl", "403f4dbc", "vote_compare", "day_vote", 4, "player_9", None,
     "control", "right in the game; 3 in 10 at low on replay (the vote record went out of use)"),
    ("haiku_effort_replay/vote_cases.jsonl", "403f4dbc", "vote_compare", "day_vote", 5, "player_2", None,
     "positive", "voted out the real sentinel as 'unverified'"),
]


def main() -> None:
    cases = []
    for src, game, slice_, phase, day, speaker, seq, role, why in PICKS:
        pool = [json.loads(line) for line in (DATA / src).read_text().splitlines() if line.strip()]
        found = []
        for c in pool:
            if (c["game_id"], c["slice"], c["phase"], c["day"], c["speaker"]) != (game, slice_, phase, day, speaker):
                continue
            if seq is not None:
                # a discussion case's state ends just before its entry (or holds none of today's lines for
                # an opening turn); the original entry is the next one of today's channel
                today = [m["seq"] for m in c["state"]["day_channel"] if m["day"] == day]
                if (max(today) + 1 if today else 0) != seq and not (c.get("original_round") == "opening" and seq < 10):
                    continue
            found.append(c)
        assert len(found) == 1, (src, game, slice_, day, speaker, seq, len(found))
        case = dict(found[0])
        case["screen_role"], case["screen_why"] = role, why
        cases.append(case)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    print(f"{len(cases)} cases -> {OUT}")
    for c in cases:
        print(f"  [{c['screen_role']:8}] {c['game_id']} day {c['day']} {c['speaker']} {c['phase']} {c['slice']}")


if __name__ == "__main__":
    main()
