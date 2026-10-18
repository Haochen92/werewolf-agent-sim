"""Evil covers, replay screen (owner, 2026-10-18, ruling R11 in the deduction catalogue): when an
evil seat is accused or a player says it saw the seat's visit, does it claim a cover that fits, or
deny? Arm "before" is the cards as they were ("Unclaimed is a fine cover; do not invent a role
until you need one", "or deny it"); arm "card" is R11's card text. Slice 14's covers (the night
stories that fit) come later as a third arm.

Record: evidence/game_play_enhancement/data/evil_cover_screen/ (README there). Turns: every discuss
turn of an evil seat with no role claim yet, on a day when an earlier line accused it or claimed a
sighting of its visit (the first such turn of each seat's day), from the persona voice games and the silence calibration games (captured
prompt inputs). Each turn is replayed SAMPLES times per arm; the lines then go to blind judges.

  GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low LANGFUSE_TRACING_ENABLED=false \\
    poetry run python -m evaluation.experiments.evil_cover_screen sample
  poetry run python -m evaluation.experiments.evil_cover_screen packets
  poetry run python -m evaluation.experiments.evil_cover_screen score
"""

from __future__ import annotations

import gzip
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from evaluation.experiments import silence_calibration

SOURCES = {
    "persona": Path("evidence/game_play_enhancement/data/persona_voice_games"),
    "silence": Path("evidence/game_play_enhancement/data/silence_calibration/games"),
}
OUT = Path("evidence/game_play_enhancement/data/evil_cover_screen")
EVIL = {"chanteuse", "illusionist", "serial_killer", "necromancer"}
SEED = 20261018
SAMPLES = 2
MAX_CALLS = 200

# The cards before R11, as (R11's text, the text it replaced) per card; "before" swaps them back.
_PACK_REAL = "a block, a conceal or the pack's kill names your role."
_SK_REAL = "your attack names your role."
_R11_VISIT = """
Never deny it either: a denied sighting reads as a lie and gets you voted out. Claim a role
whose night action explains the visit, and keep that story the same every time you are asked.

Plan your cover before you need it. Your worked-out lines list the roles you can claim without
contradicting the public record, and a role no living player holds, or one whose holder died with
its role hidden, cannot be counter-claimed truthfully. Choose one and claim it when it helps you:
when someone says you visited a player, when an information role is close to exposing you, or to
discredit a real claimant. Rarely, revealing your true role to bargain with a neutral player is the
better play.
"""
_NOTE_SWAPS = [
    ("""in four parts:
- Public cover: the role you have claimed in public, or unclaimed.
- Planned cover: the role you will claim next and your story for each night, or the one you hold.
""", """in three parts:
- Public cover: the role you have claimed in public, or unclaimed.
"""),
    ("Never let what you plan to claim blur with what you have already said.",
     """Unclaimed is a fine cover; do not invent a role until you need one, and never let what you plan to
claim blur with what you have already said."""),
]
_NECRO = (""" Your visits show your bodies' names,
not yours, so no sighting names you; but a player with no role is the one the town votes out, and
a player who denies a sighting is read as lying. Plan a cover before you need it: your worked-out
lines list the roles you can claim without contradicting the public record, and a role no living
player holds, or one whose holder died with its role hidden, cannot be counter-claimed truthfully.
Claim it when it helps you, and keep the story the same every time you are asked. Rarely,
revealing your true role to bargain with a neutral player is the better play.""", "")


def before_swaps(role: str) -> list[tuple[str, str]]:
    if role == "necromancer":
        return [_NECRO]
    real = _SK_REAL if role == "serial_killer" else _PACK_REAL
    return [(f"{real}\n" + _R11_VISIT.lstrip("\n"), f"""{real} Explain the visit as a town role
would, or deny it, and keep that story the same every time you are asked.
""")] + _NOTE_SWAPS


def arm_template(role: str, arm: str):
    from langchain_core.prompts import ChatPromptTemplate

    from Agents.nodes.day.actors import DISCUSS_PROMPTS

    template = DISCUSS_PROMPTS[role]
    if arm == "card":
        return template
    system, human = template.messages
    text = human.prompt.template
    for new, old in before_swaps(role):
        assert text.count(new) == 1, (role, new[:60])
        text = text.replace(new, old)
    return ChatPromptTemplate.from_messages([("system", system.prompt.template), ("human", text)])


ARMS = ("before", "card", "card_now", "covers", "covers2")
"""before / card: the captured prompt input (its deduction blocks as the game rendered them). card_now /
covers (step 2, slice 14): the blocks re-rendered by the checked-out engine from the turn's rebuilt
payload, without and with the covers line; the card text is R11's in all after "before". covers2 (step 3):
covers again after its fix (a check of a revealed role carries its reading; no watch story on a player
attacked that night)."""


def rendered_input(t: dict, covers: bool) -> dict:
    """The turn's prompt input with both deduction blocks rendered now from its rebuilt payload (the
    block census's rebuild: evaluation/experiments/deduction_block_census.py)."""
    import Agents.deduction.comparisons.covers as covers_module
    from Agents.prompts.prompt_inputs import _deduction_blocks, _deduction_slots, _own_result_lines
    from evaluation.experiments.deduction_block_census import _final_state, _payload_at

    source, game = t["turn"].split("/", 1)[0], t["game"]
    capture = json.loads(gzip.open(SOURCES[source] / f"{game}.capture.json.gz", "rt").read())
    entry = {"day": t["day"], "player_id": t["player"], "player_role": t["role"], "output_key": "day_channel",
             "prompt_input": t["prompt_input"]}
    payload = _payload_at(_final_state(capture["final_state"]), entry)
    real = covers_module.cover_items
    if not covers:
        covers_module.cover_items = lambda view, today: []
    try:
        blocks = _deduction_blocks(payload, _own_result_lines(payload))
    finally:
        covers_module.cover_items = real
    return {**t["prompt_input"], **_deduction_slots(payload, blocks)}


def _pressure(entries: list[dict], player: str) -> list[str]:
    """What earlier lines today did to the seat: accused it, or said they saw its visit."""
    why = []
    for e in entries:
        if e["player"] in ("game_master", player) or not (e.get("message") or "").strip():
            continue
        if any(t["target"] == player and t.get("stance") == "accusation" for t in e.get("addressed_targets", [])):
            why.append(f"{e['player']} accused")
        for a in e.get("claimed_night_actions", []):
            if player in a.get("seen", []) or (a.get("action") in ("follow", "watch") and a.get("target") == player):
                why.append(f"{e['player']} reported a {a['action']} on night {a['night']}")
    return why


def pressured_turns() -> list[dict]:
    out, seen = [], set()
    for source, games in SOURCES.items():
        channels = {}
        for t in silence_calibration.turns(games):
            if t["role"] not in EVIL or t["round"] == "opening":
                continue
            if t["game"] not in channels:
                capture = json.loads(gzip.open(games / f"{t['game']}.capture.json.gz", "rt").read())
                channels[t["game"]] = capture["final_state"]["day_channel"]
            today = [e for e in channels[t["game"]] if e["day"] == t["day"] and e["seq"] < t["seq"]]
            earlier = [e for e in channels[t["game"]] if e["day"] < t["day"] or e in today]
            if any(e["player"] == t["player"] and e.get("claim", "none") != "none" for e in earlier):
                continue  # already claimed: the screen is about choosing a cover, not keeping one
            why = _pressure(today, t["player"])
            seat_day = (source, t["game"], t["day"], t["player"])
            if why and seat_day not in seen:  # the first pressured turn of a seat's day: where a cover is chosen
                seen.add(seat_day)
                out.append(t | {"turn": f"{source}/{t['turn']}", "pressure": sorted(set(why))})
    return out


def sample(arms: str = "before,card", out: str = "samples.jsonl") -> None:
    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.schemas import day_discuss_output

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    OUT.mkdir(parents=True, exist_ok=True)
    turns = pressured_turns()
    print(f"{len(turns)} pressured turns")
    calls = 0
    with (OUT / out).open("w") as fh:
        for t in turns:
            for arm in arms.split(","):
                prompt_input = rendered_input(t, covers=arm != "card_now") if arm in ("card_now", "covers", "covers2") else t["prompt_input"]
                for k in range(SAMPLES):
                    if calls >= MAX_CALLS:
                        raise SystemExit(f"call cap {MAX_CALLS} reached")
                    calls += 1
                    chain = arm_template(t["role"], "before" if arm == "before" else "card") | get_llm().with_structured_output(
                        day_discuss_output(t["lineup"]))
                    row = {"turn": t["turn"], "role": t["role"], "round": t["round"], "arm": arm, "k": k,
                           "pressure": t["pressure"], "original": t["line"]}
                    try:
                        out = chain.invoke(prompt_input)
                        row |= {"pass_turn": out.pass_turn, "line": out.message, "claim": getattr(out, "claim", "none"),
                                "strategy": getattr(out, "strategy", None)}
                    except Exception as e:  # recorded; the sample drops out
                        row |= {"pass_turn": None, "error": str(e)[:200]}
                    fh.write(json.dumps(row) + "\n")
                    fh.flush()
                    print(f"{t['turn']} {arm}#{k}: claim={row.get('claim')} {(row.get('line') or '')[:70]}", flush=True)
    print(f"{calls} calls")


def _rows(files: str) -> list[dict]:
    return [json.loads(line) for name in files.split(",") for line in (OUT / name).read_text().splitlines()]


def packets(judges: str = "4", prefix: str = "", files: str = "samples.jsonl") -> None:
    """Blind packets: the public context and the line; no arm, no role, no private record. Step 2
    (prefix "v2_") pools every arm's samples, so all four are judged alike."""
    judges = int(judges)
    by_turn = {t["turn"]: t for t in pressured_turns()}
    rows = _rows(files)
    rows = [r for r in rows if r.get("pass_turn") is False and (r.get("line") or "").strip()]
    random.Random(SEED).shuffle(rows)
    key, packs = {}, [[] for _ in range(judges)]
    for n, r in enumerate(rows):
        name = f"c{n:03d}"
        t = by_turn[r["turn"]]
        pi = t["prompt_input"]
        key[name] = {"turn": r["turn"], "arm": r["arm"], "k": r["k"], "role": r["role"], "claim": r["claim"]}
        packs[n % judges].append(
            f"### {name}\nSpeaker: {t['player']}.\n\nRole line-up (public): {pi.get('alive_roles', '')}\n"
            f"Dead so far (public): {pi.get('dead_roster', '')}\n\n"
            f"Earlier days (summary, most recent part):\n{(pi.get('day_summaries') or '')[-silence_calibration.SUMMARY_TAIL:]}\n\n"
            f"Today's discussion so far, as the speaker saw it:\n{pi.get('day_channel') or ''}\n\nTHE LINE:\n{r['line']}\n")
    (OUT / f"{prefix}blind_key.json").write_text(json.dumps(key, indent=1))
    for j, pack in enumerate(packs):
        (OUT / f"{prefix}packet_{j + 1}.md").write_text("\n".join(pack))
    print({f"packet_{j + 1}": len(p) for j, p in enumerate(packs)})


def score(prefix: str = "", files: str = "samples.jsonl") -> None:
    """Per arm: how the seat answered (the judges' kinds), and whether its claims fit the record and
    the sightings reported (step 2: contradicts_sighting)."""
    key = json.loads((OUT / f"{prefix}blind_key.json").read_text())
    verdicts = {}
    for path in sorted(OUT.glob(f"{prefix}verdicts_*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                v = json.loads(line)
                verdicts[v["item"]] = key[v["item"]] | v
    rows = _rows(files)
    report: dict = {"samples": {}, "answer": {}, "claim_fits": {}, "contested": {}, "town_would_catch": {},
                    "explains_sighting": {}, "contradicts_sighting": {}, "claimed_roles": {}}
    for arm in [arm for arm in ARMS if any(r["arm"] == arm for r in rows)]:
        mine = [r for r in rows if r["arm"] == arm and r.get("pass_turn") is not None]
        report["samples"][arm] = {"n": len(mine), "passed": sum(r["pass_turn"] for r in mine),
                                  "claim_field_set": sum((r.get("claim") or "none") != "none" for r in mine)}
        judged = [v for v in verdicts.values() if v["arm"] == arm]
        counts: dict = defaultdict(int)
        for v in judged:
            counts[v["answer"]] += 1
        report["answer"][arm] = dict(sorted(counts.items()))
        claims = [v for v in judged if v["answer"] == "claims_role"]
        report["claim_fits"][arm] = f"{sum(v['fits_record'] for v in claims)}/{len(claims)}"
        report["town_would_catch"][arm] = f"{sum(v['town_would_catch'] for v in claims)}/{len(claims)}"
        report["contested"][arm] = f"{sum(v['contested'] for v in claims)}/{len(claims)}"
        report["explains_sighting"][arm] = f"{sum(v['explains_sighting'] for v in judged)}/{len(judged)}"
        if all("contradicts_sighting" in v for v in judged):
            report["contradicts_sighting"][arm] = f"{sum(v['contradicts_sighting'] for v in claims)}/{len(claims)}"
        roles: dict = defaultdict(int)
        for v in claims:
            roles[v["claimed_role"]] += 1
        report["claimed_roles"][arm] = dict(sorted(roles.items()))
    (OUT / f"{prefix}scores.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


GAMES = Path("evidence/game_play_enhancement/data/evil_cover_games")
"""Step 4: whole games. after/: R11's card, slice 13b and 14 (deals voices-01..08, voices on). before/:
the same deals at c61fa762 (the silence build: old evil cards, no covers); deals 01-04 are the silence
calibration games (SOURCES["silence"]), run from that same code."""


def _game_record(path: Path) -> dict:
    capture = json.loads(gzip.open(path, "rt").read())
    state = capture["final_state"]
    roles = state["roles"]
    evil = {p: r for p, r in roles.items() if r in EVIL}
    deaths = {d["player"]: d for d in state["dead_roster"]}
    claims: dict = defaultdict(list)
    for e in state["day_channel"]:
        if e["player"] in evil and (e.get("message") or "").strip() and e.get("claim", "none") != "none":
            claims[e["player"]].append((e["day"], e["claim"]))
    lynched = [r["voted_player"] for r in state["day_resolutions"] if r.get("voted_player")]
    return {
        "winner": state["winner"], "days": state["current_day"],
        "evil": {p: {"role": r, "claims": sorted({c for _, c in claims[p]}),
                     "first_claim_day": min((d for d, _ in claims[p]), default=None),
                     "out": (f"{deaths[p]['phase']} {deaths[p]['day']}" if p in deaths else "alive")} for p, r in evil.items()},
        "lynches": {"evil": sum(roles[p] in EVIL for p in lynched), "other": sum(roles[p] not in EVIL for p in lynched)},
    }


def games() -> None:
    """Per arm: winners, evil seats that claimed (and when), how evil seats left the game, and whom the
    day votes removed."""
    arms = {"before": sorted([*(SOURCES["silence"]).glob("*.capture.json.gz"), *(GAMES / "before").glob("*.capture.json.gz")]),
            "after": sorted((GAMES / "after").glob("*.capture.json.gz"))}
    report = {}
    for arm, paths in arms.items():
        records = {p.name.removesuffix(".capture.json.gz"): _game_record(p) for p in paths}
        seats = [e for r in records.values() for e in r["evil"].values()]
        report[arm] = {
            "games": len(records),
            "winners": dict(sorted(defaultdict(int, {w: sum(r["winner"] == w for r in records.values())
                                                     for w in {r["winner"] for r in records.values()}}).items())),
            "evil_seats": len(seats),
            "evil_seats_that_claimed": sum(bool(e["claims"]) for e in seats),
            "evil_lynched": sum(e["out"].startswith("day") for e in seats),
            "evil_alive_at_end": sum(e["out"] == "alive" for e in seats),
            "lynches_evil_other": [sum(r["lynches"]["evil"] for r in records.values()),
                                   sum(r["lynches"]["other"] for r in records.values())],
            "per_game": records,
        }
    (GAMES / "games_scores.json").write_text(json.dumps(report, indent=1))
    print(json.dumps({arm: {k: v for k, v in r.items() if k != "per_game"} for arm, r in report.items()}, indent=1))


if __name__ == "__main__":
    {"sample": sample, "packets": packets, "score": score, "games": games}[sys.argv[1]](*sys.argv[2:])
