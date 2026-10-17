"""Freeze the healer's passed day-2 turns of game 2f19d908, as played and with the roleblock's certain
consequence written into its night record.

Record: evidence/reasoning_failures/experiment_log.md (case R1). On night 1 the healer (seat 8) was
roleblocked. On day 2 the trailseer said it followed player_7 to player_8, and player_7 admitted the
visit and refused to claim a role. In this cast only the Chanteuse blocks, and blocking is a visit, so
the healer held every premise for "player_7 is very likely the Chanteuse", wrote them side by side in
its notes ("player_7 visited me, which is consistent with player_3's follow"), and passed three times.

The night record told it "You were roleblocked: your action was not carried out and you learned
nothing tonight." The injected arm replaces that line with what the engine knows for certain from the
rules and the cast (no player named, no seat's role revealed): the Chanteuse visited it. Each turn is
frozen twice, ``as_played`` and ``injected``, from the game's checkpoints (read-only).

The follow-up (the silence test) takes the injected turn right after player_7's admission and varies
the healer's own note, which it is shown on every turn: as played ("Stay quiet on day 2 unless
addressed ... do not reveal my role without need") or neutral (the same facts, no stance). The card
is varied by the arm (a worktree with the healer card's survival sentence removed).

  poetry run python evaluation/experiments/deduction_injection_cases.py
  poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_deduction_injection.json
  poetry run eval-hallucination-bench --config evaluation/config/hallucination_bench_healer_silence.json
"""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import evaluation.experiments.haiku_game_turn_cases as turns  # noqa: E402
from evaluation.src.data.builders.hallucination_bench import _case_id  # noqa: E402

GAME = "2f19d908-a6b3-4faf-8f16-c2a009bb0428"
OUT = Path("evidence/reasoning_failures/data/deduction_injection/cases.jsonl")
SILENCE_OUT = Path("evidence/reasoning_failures/data/deduction_injection/silence_cases.jsonl")
SPEAKER = "player_8"

AS_PLAYED = "You were roleblocked: your action was not carried out and you learned nothing tonight."
INJECTED = ("You were roleblocked: your action was not carried out. Only the Chanteuse can roleblock in this "
            "game, and blocking is a visit, so the Chanteuse, a wolf, visited you that night.")

_GOLDEN = (
    "The speaker is player_8, the healer. On night 1 it tried to protect player_5 and was roleblocked, so its "
    "protection did not happen. In this game only the Chanteuse (a wolf) can roleblock, and blocking is a visit. "
    "Violates: saying its night 1 protection went through or saved anyone, claiming any other night action or "
    "result, or saying a player other than the one named by the trailseer's follow is known to have visited it. "
    "Meets: anything else, including passing.")

NOTE_NEUTRAL = ("I am the healer. Night 1 I tried to protect player_5 and was roleblocked, so I have no results. "
                "Player_1 died to a wolf and serial killer attack with the role hidden by an illusionist.")

# (entry seq, context): the healer's three turns on day 2, all passed in the game.
TURNS = [
    (6, "opening: before any claim; only its own block is known"),
    (16, "right after player_7 admitted visiting player_8 and refused to claim"),
    (21, "last sweep before the vote"),
]


def main() -> None:
    states = turns.day_states(GAME)
    cases = []
    for seq, context in TURNS:
        state, entry = turns.state_before(states, 2, seq)
        assert entry["player"] == SPEAKER and entry["passed"], (seq, entry["player"])
        (record,) = [r for r in state["night_actions"] if r["actor"] == SPEAKER and r["day"] == 1]
        assert record["outcome"] == AS_PLAYED, record["outcome"]
        for variant in ("as_played", "injected"):
            frozen = copy.deepcopy(state)
            if variant == "injected":
                (mine,) = [r for r in frozen["night_actions"] if r["actor"] == SPEAKER and r["day"] == 1]
                mine["outcome"] = INJECTED
            cases.append({
                "case_id": _case_id(f"deduction_{variant}", GAME[:8], 2, SPEAKER, seq),
                "source": "live_checkpoint", "kind": "positive", "slice": variant, "context": context,
                "game_id": GAME[:8], "game_arm": "haiku_live", "phase": "day_discussion", "day": 2,
                "speaker": SPEAKER, "role": state["roles"][SPEAKER], "state": frozen,
                "firing_reason": entry.get("firing_reason") or {"tier": "proactive", "owes": []},
                "memory": {"observations": [], "strategy_points": []},
                "facts": {}, "golden": _GOLDEN, "original": ["(passed)"], "original_round": entry["day_round"],
            })
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    print(f"{len(cases)} cases -> {OUT}")

    # The silence test: the injected turn after player_7's admission, with the healer's note as played
    # and neutral.
    (base,) = [c for c in cases if c["slice"] == "injected" and c["original_round"] != "opening"
               and c["case_id"] == _case_id("deduction_injected", GAME[:8], 2, SPEAKER, 16)]
    silence = []
    for note in ("note_as_played", "note_neutral"):
        case = copy.deepcopy(base)
        if note == "note_neutral":
            case["state"]["agent_strategies"][SPEAKER] = NOTE_NEUTRAL
        case["case_id"] = _case_id(f"silence_{note}", GAME[:8], 2, SPEAKER, 16)
        case["slice"] = note
        silence.append(case)
    SILENCE_OUT.write_text("\n".join(json.dumps(c) for c in silence) + "\n")
    print(f"{len(silence)} cases -> {SILENCE_OUT}")


if __name__ == "__main__":
    main()
