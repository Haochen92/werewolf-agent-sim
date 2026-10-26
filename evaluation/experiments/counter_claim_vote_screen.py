"""Counter-claim accounts, vote replay (owner, 2026-10-18, slice 16 in the deduction catalogue): when two
living players claim a role dealt once, the seat block now says which results each claimant names
("As the Investigator, player_1 names a check of player_5 on night 1 (Not suspicious), which a reveal of
player_5's role would test; player_7 names no check result."). Does a town seat's vote move toward the
fake claimant?

Record: evidence/gameplay/data/counter_claim_votes/ (README there). Turns: every town seat's
vote on a day of the evil cover games (evidence/gameplay/data/evil_cover_games/after/) whose
re-rendered seat block has the sentence. Both arms re-render the blocks with the checked-out engine from
the turn's rebuilt payload (the block census's rebuild); arm "without" removes the sentence. The rest of
the prompt input is the captured one. No judge: the vote is the measure.

  GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low LANGFUSE_TRACING_ENABLED=false \\
    poetry run python -m evaluation.experiments.counter_claim_vote_screen sample
  poetry run python -m evaluation.experiments.counter_claim_vote_screen score
"""

from __future__ import annotations

import gzip
import json
import re
import sys
from collections import Counter
from pathlib import Path

GAMES = Path("evidence/gameplay/data/evil_cover_games/after")
OUT = Path("evidence/gameplay/data/counter_claim_votes")
ARMS = ("without", "with")
SAMPLES = 3
MAX_CALLS = 160
SLOTS = ("deduction_seat_before_note",)
ACCOUNT = re.compile(r" ?As the (\w[\w ]*?), (player_\d+) names .*?\.(?= |\n|$)")


def turns() -> list[dict]:
    """The town seats' vote turns whose re-rendered block has an account sentence."""
    from Agents.prompts.prompt_inputs import _deduction_blocks, _deduction_slots, _own_result_lines
    from Agents.schemas.roles import ROLE_SPECS
    from evaluation.experiments.deduction_block_census import _final_state, _payload_at

    out = []
    for path in sorted(GAMES.glob("*.capture.json.gz")):
        capture = json.loads(gzip.open(path, "rt").read())
        roles = capture["final_state"]["roles"]
        state = _final_state(capture["final_state"])
        for entry in capture["prompt_log"]:
            if entry["output_key"] != "day_votes" or ROLE_SPECS[entry["player_role"]].side != "town":
                continue
            payload = _payload_at(state, entry)
            slots = _deduction_slots(payload, _deduction_blocks(payload, _own_result_lines(payload)))
            found = [m for slot in SLOTS for m in ACCOUNT.finditer(slots[slot])]
            if not found:
                continue
            title = found[0].group(1).lower().replace(" ", "_")
            claimants = sorted(set(re.findall(r"player_\d+", found[0].group(0))) & {p for p, r in roles.items()})
            claimants = [p for p in claimants if re.search(rf"{p} names", found[0].group(0))]
            out.append({"game": path.name.split(".")[0], "day": entry["day"], "player": entry["player_id"],
                        "role": entry["player_role"], "claimed": title, "sentence": found[0].group(0).strip(),
                        "claimants": {p: roles[p] for p in claimants}, "lineup": capture["final_state"]["lineup"],
                        "payload": payload, "prompt_input": {**entry["prompt_input"], **slots}})
    return out


def _without(prompt_input: dict) -> dict:
    return {**prompt_input, **{slot: ACCOUNT.sub("", prompt_input[slot]) for slot in SLOTS}}


def sample(out: str = "samples.jsonl") -> None:
    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.nodes.day.actors import VOTE_PROMPTS
    from Agents.schemas import day_vote_output
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    OUT.mkdir(parents=True, exist_ok=True)
    found = turns()
    print(f"{len(found)} turns")
    calls = 0
    with (OUT / out).open("w") as fh:
        for t in found:
            legal = valid_targets_for_action(t["payload"], "day_votes")
            bound = output_schema_with_legal_targets(day_vote_output(t["lineup"]), "day_votes", legal)
            chain = VOTE_PROMPTS[t["role"]] | get_llm().with_structured_output(bound)
            for arm in ARMS:
                prompt_input = t["prompt_input"] if arm == "with" else _without(t["prompt_input"])
                assert (arm == "with") == (t["sentence"] in "".join(prompt_input[s] for s in SLOTS))
                for k in range(SAMPLES):
                    if calls >= MAX_CALLS:
                        raise SystemExit(f"call cap {MAX_CALLS} reached")
                    calls += 1
                    row = {key: t[key] for key in ("game", "day", "player", "role", "claimed", "sentence", "claimants")}
                    row |= {"arm": arm, "k": k}
                    try:
                        row["vote"] = chain.invoke(prompt_input).vote_target
                    except Exception as e:  # recorded; the sample drops out
                        row |= {"vote": None, "error": str(e)[:200]}
                    fh.write(json.dumps(row) + "\n")
                    fh.flush()
                    print(f"{t['game']} d{t['day']} {t['player']} {arm}#{k}: {row['vote']}", flush=True)
    print(f"{calls} calls")


def score(files: str = "samples.jsonl") -> None:
    """Votes for the claimant who holds the role, for the fake one, and for anyone else, per arm."""
    rows = [json.loads(line) for f in files.split(",") for line in (OUT / f).read_text().splitlines()]
    table: dict = {}
    for arm in ARMS:
        got = Counter()
        for r in rows:
            if r["arm"] != arm or r.get("vote") is None:
                continue
            role = r["claimed"]
            vote = r["vote"]
            kind = ("real" if r["claimants"].get(vote) == role else "fake" if vote in r["claimants"] else "other")
            got[kind] += 1
            got[f"{r['game']} d{r['day']} {kind}"] += 1
        table[arm] = dict(sorted(got.items()))
    print(json.dumps(table, indent=1))
    (OUT / "scores.json").write_text(json.dumps(table, indent=1) + "\n")


if __name__ == "__main__":
    {"sample": sample, "score": score}[sys.argv[1]](*sys.argv[2:])
