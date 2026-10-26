"""Screen: a second model pass that rewrites a seat's spoken line in a persona's voice, keeping the
argument (owner's idea, 2026-10-18). Does it read better, and how often does it change the facts?

Record: evidence/gameplay/data/voice_rewrite/ (README there). Generation and the
deterministic fact gate only; naturalness and argument fidelity are judged blind, separately.

Thirty real lines: twenty AI lines from the two captured Haiku games (645228e7, 88aee4e4; the human
seat's lines left out) and ten from the deduction placement screen (the new prompts). Each is
rewritten once per persona by the game model. The rewriter sees the line and the persona only, never
the game, so it cannot leak anything. The gate passes a rewrite only when it names the same players,
the same nights and the same role words as the original; a live pass would post the original instead.

  GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low GAME_LLM_ATTEMPTS=1 \
    LANGFUSE_TRACING_ENABLED=false poetry run python evaluation/experiments/voice_rewrite_screen.py \
    --captures <dir with the two <id>.json.gz exports>
"""

from __future__ import annotations

import argparse
import gzip
import json
import random
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from evaluation.src.replay.hallucination_bench import _usage_totals

OUT = Path("evidence/gameplay/data/voice_rewrite")
SCREEN = Path("evidence/gameplay/deduction/data/deduction_placement_n10/samples.jsonl")
GAMES = {"645228e7-a75b-4a57-a6e2-1a569838bf31": 6, "88aee4e4-8cd0-4031-b5e7-d8dc7a770abe": 14}
"""Each captured game and how many of its AI lines to draw."""
SCREEN_LINES = 10
SEED = 20261018
MAX_CALLS = 110

PERSONAS = {
    "blunt": "Blunt and brief. Short sentences, no pleasantries, gets straight to the point.",
    "warm": "Warm and chatty. Talks to the others like friends at a table, with a little humour.",
    "dry": "Dry and understated, with a wry, slightly sarcastic edge.",
}

REWRITE_SYSTEM = """You rewrite one line a player said aloud in a game of Werewolf, so that it sounds \
like this player's own voice and like a person talking at a table, not a report.

The player's voice: {persona}

Rules:
- Keep every fact and claim exactly: the same players, the same nights, the same roles and results, \
who did what, and how sure the speaker is. Add nothing and drop nothing.
- Keep who the line is addressed to and what it asks for.
- Write player names exactly as given (player_6), and refer to each night the way the line does \
("night 2" stays "night 2", "last night" stays "last night").
- About the same length or shorter. One message, no quotation marks around it, no stage directions."""


class Rewrite(BaseModel):
    message: str = Field(description="The line, rewritten in the player's voice.")


# --- the lines -------------------------------------------------------------------------------------

def game_lines(captures: Path) -> list[dict]:
    rng = random.Random(SEED)
    lines = []
    for game, n in GAMES.items():
        capture = json.loads(gzip.open(captures / f"{game}.json.gz").read())
        humans = set(json.loads((captures / f"{game}.meta.json").read_text())["human_players"])
        roles = capture["final_state"]["roles"]
        spoken = [e for e in capture["final_state"]["day_channel"]
                  if e["player"] not in humans and e["player"] != "game_master" and (e.get("message") or "").strip()]
        for e in sorted(rng.sample(spoken, n), key=lambda e: (e["day"], e["seq"])):
            lines.append({"source": f"game:{game[:8]}", "day": e["day"], "speaker": e["player"],
                          "role": roles.get(e["player"]), "message": e["message"]})
    return lines


def screen_lines() -> list[dict]:
    rng = random.Random(SEED)
    rows = [json.loads(line) for line in SCREEN.read_text().splitlines() if line.strip()]
    spoken = [r for r in rows if r.get("message")]
    return [{"source": f"screen:{r['case']}:{r['arm']}:{r['sample']}", "day": None, "speaker": r["speaker"],
             "role": r["role"], "message": r["message"]} for r in rng.sample(spoken, SCREEN_LINES)]


# --- the gate --------------------------------------------------------------------------------------

_NUMBER_WORDS = {"one": "1", "two": "2", "three": "3", "four": "4", "five": "5", "six": "6", "first": "1",
                 "second": "2", "third": "3", "fourth": "4", "fifth": "5"}
_ROLE_WORDS = ["investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer", "chanteuse",
               "illusionist", "serial killer", "necromancer", "speculator", "fortune teller", "wolf",
               "wolves", "town", "pack", "suspicious"]


def facts(text: str) -> dict[str, list[str]]:
    """What the gate compares: the players named, the nights referred to, the role and result words."""
    low = text.lower()
    players = sorted(set(re.findall(r"\bplayer_\d+\b", low)))
    nights = set()
    for m in re.finditer(r"\bnight\s+(\d+|one|two|three|four|five|six)\b", low):
        nights.add("night " + _NUMBER_WORDS.get(m.group(1), m.group(1)))
    for m in re.finditer(r"\b(first|second|third|fourth|fifth)\s+night\b", low):
        nights.add("night " + _NUMBER_WORDS[m.group(1)])
    for phrase in ("last night", "tonight", "yesterday", "today"):
        if re.search(rf"\b{phrase}\b", low):
            nights.add(phrase)
    roles = sorted({"wolf" if w == "wolves" else w for w in _ROLE_WORDS if re.search(rf"\b{w}\b", low)})
    return {"players": players, "nights": sorted(nights), "roles": roles}


def gate(original: str, rewrite: str) -> list[str]:
    """The differences that would make a live pass post the original instead; [] = passes."""
    a, b = facts(original), facts(rewrite)
    return [f"{k}: {a[k]} -> {b[k]}" for k in a if a[k] != b[k]]


# --- generation ------------------------------------------------------------------------------------

def main() -> None:
    from langchain_core.callbacks import UsageMetadataCallbackHandler

    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.llm_factory.pricing import cost_usd

    parser = argparse.ArgumentParser()
    parser.add_argument("--captures", type=Path, required=True)
    args = parser.parse_args()

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    lines = game_lines(args.captures) + screen_lines()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "lines.jsonl").write_text("".join(json.dumps({"line": i, **l}) + "\n" for i, l in enumerate(lines)))

    prompt = ChatPromptTemplate.from_messages([("system", REWRITE_SYSTEM), ("human", "{line}")])
    chain = prompt | get_llm().with_structured_output(Rewrite)
    calls, total = 0, 0.0
    with (OUT / "rewrites.jsonl").open("w") as fh:
        for i, line in enumerate(lines):
            for persona, voice in PERSONAS.items():
                if calls >= MAX_CALLS:
                    raise SystemExit(f"call cap {MAX_CALLS} reached")
                calls += 1
                usage, started, out, err = UsageMetadataCallbackHandler(), time.monotonic(), None, ""
                try:
                    out = chain.invoke({"persona": voice, "line": line["message"]}, config={"callbacks": [usage]})
                except Exception as e:  # recorded; counts as a failed rewrite
                    err = str(e)[:300]
                seconds = time.monotonic() - started
                tokens = _usage_totals(usage, seconds)
                cost = cost_usd(model.removeprefix("anthropic/"), datetime.now(timezone.utc), input=tokens["input"],
                                cached=tokens["cached"], output=tokens["output"], written=0) or 0.0
                total += cost
                rewrite = out.message if out is not None else None
                row = {"line": i, "persona": persona, "rewrite": rewrite, "error": err,
                       "gate": gate(line["message"], rewrite) if rewrite else ["no rewrite"],
                       "seconds": round(seconds, 2), "usage": {**tokens, "cost_usd": round(cost, 6)}}
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"line {i} {persona}: gate={'pass' if not row['gate'] else row['gate']} {seconds:.1f}s", flush=True)
    print(f"{calls} calls, ${total:.4f}")


def packets(judges: int = 2) -> None:
    """The judging packets from the rewrites, split between `judges`: naturalness blind (original and
    rewrite as X and Y in a seeded order; the key in blind_key.json), fidelity labelled."""
    rng = random.Random(SEED)
    lines = [json.loads(line) for line in (OUT / "lines.jsonl").read_text().splitlines()]
    rows = [json.loads(line) for line in (OUT / "rewrites.jsonl").read_text().splitlines()]
    rng.shuffle(rows)
    key, natural, fidelity = {}, [[] for _ in range(judges)], [[] for _ in range(judges)]
    for n, row in enumerate(rows):
        pair = f"p{n:02d}"
        original, rewrite = lines[row["line"]]["message"], row["rewrite"]
        x_is_rewrite = rng.random() < 0.5
        key[pair] = {"line": row["line"], "persona": row["persona"], "x": "rewrite" if x_is_rewrite else "original"}
        x, y = (rewrite, original) if x_is_rewrite else (original, rewrite)
        natural[n % judges].append(f"### {pair}\nX: {x}\n\nY: {y}\n")
        fidelity[n % judges].append(f"### {pair}\nORIGINAL: {original}\n\nREWRITE: {rewrite}\n")
    (OUT / "blind_key.json").write_text(json.dumps(key, indent=1))
    for j in range(judges):
        (OUT / f"naturalness_packet_{j + 1}.md").write_text("\n".join(natural[j]))
        (OUT / f"fidelity_packet_{j + 1}.md").write_text("\n".join(fidelity[j]))


if __name__ == "__main__":
    import sys

    if sys.argv[1:] == ["--packets"]:
        packets()
    else:
        main()
