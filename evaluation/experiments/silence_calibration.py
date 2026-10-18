"""Silence calibration, step 1: how often does a silent turn hide a line worth hearing, and how often
is a spoken line noise? (owner, 2026-10-18: "a more principled way of calibrating the silence rule").

Record: evidence/game_play_enhancement/data/silence_calibration/ (README there). Turns come from the
persona voice games (evaluation/experiments/persona_voice_games.py), where every turn's prompt input
was captured: each discuss prompt is paired with the channel entry it produced (in order, per day and
player). Three kinds of turn are drawn, seeded:
- a voluntary pass: replayed once with one instruction added after the prompt, "do not pass this
  time", so the line it held is visible;
- a held line (the opening filter's or the echo gate's): its kept draft;
- a posted line, as spoken.
Each line goes to blind judges with what that seat saw of today's discussion and the earlier days, as
one of: (A) a new fact, (B) a new inference or a different reading of known facts, (C) a question or
test that moves the game, (D) a restatement or filler. False silence = a silent turn whose line is A,
B or C; noise = a posted line judged D.

  GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low LANGFUSE_TRACING_ENABLED=false \
    poetry run python -m evaluation.experiments.silence_calibration sample
  poetry run python -m evaluation.experiments.silence_calibration packets

Step 2 (variants): the same drawn turns resampled under the current silence rule and a variant, each
turn's value taken from step 1's verdict on its line, and the spoken lines of both arms judged blind:

  ... silence_calibration variants      # resample both arms
  ... silence_calibration variant_packets

Step 3 (levers): the later turns resampled with one other pass-pushing part of the prompt removed at a
time (the seat's note, the open floor's "a pass costs nothing", the role cards' "blend in"):

  ... silence_calibration levers
  ... silence_calibration lever_score
"""

from __future__ import annotations

import gzip
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

from langchain_core.messages import HumanMessage

GAMES = Path("evidence/game_play_enhancement/data/persona_voice_games")
OUT = Path("evidence/game_play_enhancement/data/silence_calibration")
SEED = 20261018
DRAW = {"pass:opening": 40, "pass:proactive": 40, "posted:opening": 25, "posted:proactive": 25,
        "posted:discussion": 25}
"""Turns drawn per stratum; every held line is taken."""
MAX_CALLS = 100

FORCE = ("Measurement turn: whatever the rules above say about passing, do not pass this time. Write the "
         "message you would say if you spoke now, as you would say it, and set pass_turn to false.")
SUMMARY_TAIL = 3000
"""How much of the earlier days' summaries a judge sees (the most recent part)."""


def turns() -> list[dict]:
    """Every discuss turn of the captured games, its prompt input with the entry it produced."""
    out = []
    for path in sorted(GAMES.glob("*.capture.json.gz")):
        game = path.name.removesuffix(".capture.json.gz")
        capture = json.loads(gzip.open(path, "rt").read())
        prompts, entries = defaultdict(list), defaultdict(list)
        for p in capture["prompt_log"]:
            if p["output_key"] == "day_channel":
                prompts[(p["day"], p["player_id"])].append(p)
        for e in capture["final_state"]["day_channel"]:
            if e["player"] != "game_master":
                entries[(e["day"], e["player"])].append(e)
        lineup = capture["final_state"]["lineup"]
        for key, ps in prompts.items():
            es = entries.get(key, [])
            if len(ps) != len(es):  # a retried call logs twice: the pairing is unsure, skip the seat's day
                continue
            for i, (p, e) in enumerate(zip(ps, es)):
                if e["day_round"] == "closing":
                    continue
                if e.get("gated_candidate"):
                    kind, line = "held", e["gated_candidate"]
                elif (e.get("message") or "").strip():
                    kind, line = "posted", e["message"]
                else:
                    kind, line = "pass", None
                out.append({"turn": f"{game}:{key[0]}:{key[1]}:{i}", "game": game, "day": key[0],
                            "player": key[1], "role": p["player_role"], "round": e["day_round"],
                            "kind": kind, "line": line, "pass_reason": e.get("pass_reason"),
                            "lineup": lineup, "prompt_input": p["prompt_input"]})
    return out


def draw(all_turns: list[dict]) -> list[dict]:
    rng = random.Random(SEED)
    strata = defaultdict(list)
    for t in all_turns:
        strata["held" if t["kind"] == "held" else f"{t['kind']}:{t['round']}"].append(t)
    picked = list(strata["held"])
    for name, n in DRAW.items():
        pool = strata.get(name, [])
        picked += rng.sample(pool, min(n, len(pool)))
    return picked


def sample() -> None:
    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.nodes.day.actors import DISCUSS_PROMPTS
    from Agents.schemas import day_discuss_output

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    OUT.mkdir(parents=True, exist_ok=True)
    items, calls = [], 0
    for t in draw(turns()):
        item = {k: v for k, v in t.items() if k not in ("prompt_input", "lineup")}
        item["forced"] = False
        if t["kind"] == "pass":
            if calls >= MAX_CALLS:
                raise SystemExit(f"call cap {MAX_CALLS} reached")
            calls += 1
            chain = (DISCUSS_PROMPTS[t["role"]] + HumanMessage(content=FORCE)) | get_llm().with_structured_output(
                day_discuss_output(t["lineup"]))
            try:
                result = chain.invoke(t["prompt_input"])
                item |= {"line": result.message, "forced": True}
            except Exception as e:  # recorded; the item drops out of judging
                item |= {"line": None, "error": str(e)[:200]}
            print(f"{t['turn']} forced: {(item['line'] or '')[:80]}", flush=True)
        pi = t["prompt_input"]
        item["context"] = {"earlier_days": (pi.get("day_summaries") or "")[-SUMMARY_TAIL:],
                           "today": pi.get("day_channel") or ""}
        items.append(item)
    (OUT / "items.jsonl").write_text("".join(json.dumps(i) + "\n" for i in items))
    print(f"{len(items)} items, {calls} forced calls")


SILENCE_RULE_V1 = """
Silence rule:
If you were directly addressed (asked a question or accused), you MUST respond this turn:
set pass_turn=false and answer or defend.
Otherwise, speak when your line adds at least one of:
1. A fact the table does not have yet: a claim, or your own night action or result, when you choose
   to share it.
2. A different reading of what is already known: an inference, a consequence or a point of view
   nobody has put today, with your reason. It is worth saying even if the table leans the other way.
3. A question or a test nobody has asked today that would move the game: who should explain what, or
   what to check.
Set pass_turn=true when your line would only restate a point already made, agree without a new
reason, repeat a request someone already made, or say there is little to go on.
When there is no concrete information yet, don't manufacture suspicion out of how talkative, quiet,
aggressive, or cautious someone is; passing is fine then. If you want to move things forward, prefer
information-generating moves: propose a concrete test, point to a specific contradiction, or track
the voting record once there is one.
"""
"""Variant 1 (2026-10-18): the reasons to speak are step 1's kinds A, B and C, the reason to pass is D."""
VARIANTS = {"current": None, "v1": SILENCE_RULE_V1}
VARIANT_CALLS = 340


def variant_template(role: str, rule: str | None):
    """The role's discuss template with the general silence rule swapped for ``rule`` (None = as is)."""
    from langchain_core.prompts import ChatPromptTemplate

    from Agents.nodes.day.actors import DISCUSS_PROMPTS
    from Agents.prompts.day_discuss import DISCUSSION_SILENCE_RULE

    template = DISCUSS_PROMPTS[role]
    if rule is None:
        return template
    system, human = template.messages
    text = human.prompt.template
    assert text.count(DISCUSSION_SILENCE_RULE) == 1, "the silence rule moved"
    return ChatPromptTemplate.from_messages([("system", system.prompt.template),
                                             ("human", text.replace(DISCUSSION_SILENCE_RULE, rule))])


def variants() -> None:
    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.schemas import day_discuss_output

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    calls = 0
    with (OUT / "variant_samples.jsonl").open("w") as fh:
        for t in draw(turns()):
            for arm, rule in VARIANTS.items():
                if calls >= VARIANT_CALLS:
                    raise SystemExit(f"call cap {VARIANT_CALLS} reached")
                calls += 1
                chain = variant_template(t["role"], rule) | get_llm().with_structured_output(day_discuss_output(t["lineup"]))
                row = {"turn": t["turn"], "round": t["round"], "original": t["kind"], "arm": arm}
                try:
                    out = chain.invoke(t["prompt_input"])
                    row |= {"pass_turn": out.pass_turn, "line": out.message if not out.pass_turn else ""}
                except Exception as e:  # recorded; the turn drops out of that arm
                    row |= {"pass_turn": None, "error": str(e)[:200]}
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"{t['turn']} {arm}: pass={row['pass_turn']}", flush=True)
    print(f"{calls} calls")


def variant_packets(judges: int = 4) -> None:
    """The spoken lines of both arms, mixed and blind, with each turn's context from step 1."""
    rng = random.Random(SEED + 1)
    items = {json.loads(line)["turn"]: json.loads(line) for line in (OUT / "items.jsonl").read_text().splitlines()}
    rows = [json.loads(line) for line in (OUT / "variant_samples.jsonl").read_text().splitlines()]
    spoken = [r for r in rows if r.get("pass_turn") is False and (r.get("line") or "").strip() and r["turn"] in items]
    rng.shuffle(spoken)
    key, packs = {}, [[] for _ in range(judges)]
    for n, r in enumerate(spoken):
        name = f"v{n:03d}"
        item = items[r["turn"]]
        key[name] = {"turn": r["turn"], "arm": r["arm"], "round": r["round"]}
        stage = "the opening round (each player speaks once, before seeing the others)" if r["round"] == "opening" \
            else "the day's discussion"
        packs[n % judges].append(
            f"### {name}\nSpeaker: {item['player']}, during {stage}.\n\nEarlier days (summary, most recent part):\n"
            f"{item['context']['earlier_days']}\n\nToday's discussion so far, as the speaker saw it:\n"
            f"{item['context']['today']}\n\nTHE LINE:\n{r['line']}\n")
    (OUT / "variant_blind_key.json").write_text(json.dumps(key, indent=1))
    for j, pack in enumerate(packs):
        (OUT / f"variant_packet_{j + 1}.md").write_text("\n".join(pack))
    print({f"variant_packet_{j + 1}": len(p) for j, p in enumerate(packs)})


def _verdicts(prefix: str, key_file: str) -> dict[str, dict]:
    """The judges' verdicts (``<prefix>_N.jsonl``) joined to their blind key, by item name."""
    key = json.loads((OUT / key_file).read_text())
    out = {}
    for path in sorted(OUT.glob(f"{prefix}_*.jsonl")):
        for line in path.read_text().splitlines():
            if line.strip():
                v = json.loads(line)
                out[v["item"]] = {**key[v["item"]], **v}
    return out


def variant_score() -> None:
    """Per arm and round: how often a turn speaks when step 1 judged its line worth hearing (A-C) and
    when it judged it D, and, once the variant packets are judged, the kinds of the lines spoken."""
    value = {v["turn"]: v["kind"] for v in _verdicts("verdicts", "blind_key.json").values()}
    rows = [json.loads(line) for line in (OUT / "variant_samples.jsonl").read_text().splitlines()]
    table: dict = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for r in rows:
        if r.get("pass_turn") is None or r["turn"] not in value:
            continue
        group = "opening" if r["round"] == "opening" else "later"
        cls = "valuable" if value[r["turn"]] in "ABC" else "D"
        cell = table[(r["arm"], group)][cls]
        cell[0] += r["pass_turn"] is False
        cell[1] += 1
    report = {"speak_rate": {f"{arm}/{group}": {cls: f"{s}/{n}" for cls, (s, n) in cells.items()}
                             for (arm, group), cells in sorted(table.items())}}
    judged = _verdicts("variant_verdicts", "variant_blind_key.json") if (OUT / "variant_blind_key.json").exists() else {}
    kinds: dict = defaultdict(lambda: defaultdict(int))
    for v in judged.values():
        kinds[f"{v['arm']}/{'opening' if v['round'] == 'opening' else 'later'}"][v["kind"]] += 1
    report["spoken_kinds"] = {k: dict(sorted(c.items())) for k, c in sorted(kinds.items())}
    (OUT / "variant_scores.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


PASS_SENTENCE = " If you have nothing new to add, set pass_turn=true; a pass costs nothing here."
BLEND_IN = "Blend in and participate like an ordinary town player."
"""The opener of six role cards (the four town info roles', the Fortune Teller's and the Speculator's);
the evil cards' own "Blend in as an ordinary town player" is left alone, as silence can be their play."""
NO_NOTE = "(no note yet)"
LEVER_CALLS = 220


def lever_arm(t: dict, lever: str):
    """The turn's template and prompt input with one lever pulled, or None when the lever does not
    touch this turn (its answer would be the current arm's)."""
    template, pi = variant_template(t["role"], None), dict(t["prompt_input"])
    if lever == "no_note":
        pi["previous_strategy"] = NO_NOTE
    elif lever == "no_pass_sentence":
        if PASS_SENTENCE not in pi["discussion_stage_rules"]:
            return None
        pi["discussion_stage_rules"] = pi["discussion_stage_rules"].replace(PASS_SENTENCE, "")
    elif lever == "no_blend_in":
        from langchain_core.prompts import ChatPromptTemplate

        system, human = template.messages
        text = human.prompt.template
        if text.count(BLEND_IN) != 1:
            return None
        template = ChatPromptTemplate.from_messages([("system", system.prompt.template),
                                                     ("human", text.replace(BLEND_IN, "Take an active part in the discussion."))])
    return template, pi


LEVERS = ("no_note", "no_pass_sentence", "no_blend_in")
"""Step 3 (2026-10-18): the other things in the prompt that tell a seat to pass, one at a time, on the
later turns (step 2's rule rewrite moved nothing)."""


def levers() -> None:
    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.schemas import day_discuss_output

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    calls = 0
    with (OUT / "lever_samples.jsonl").open("w") as fh:
        for t in draw(turns()):
            if t["round"] == "opening":
                continue
            for lever in LEVERS:
                arm = lever_arm(t, lever)
                if arm is None:
                    continue
                if calls >= LEVER_CALLS:
                    raise SystemExit(f"call cap {LEVER_CALLS} reached")
                calls += 1
                template, pi = arm
                row = {"turn": t["turn"], "round": t["round"], "original": t["kind"], "arm": lever}
                try:
                    out = (template | get_llm().with_structured_output(day_discuss_output(t["lineup"]))).invoke(pi)
                    row |= {"pass_turn": out.pass_turn, "line": out.message if not out.pass_turn else ""}
                except Exception as e:  # recorded; the turn drops out of that arm
                    row |= {"pass_turn": None, "error": str(e)[:200]}
                fh.write(json.dumps(row) + "\n")
                fh.flush()
                print(f"{t['turn']} {lever}: pass={row['pass_turn']}", flush=True)
    print(f"{calls} calls")


def lever_score() -> None:
    """Per lever, on the turns it touches: the speak rate when step 1 judged the turn's line worth
    hearing (A-C) and when it judged it D, beside step 2's current arm on the same turns."""
    value = {v["turn"]: v["kind"] for v in _verdicts("verdicts", "blind_key.json").values()}
    current = {r["turn"]: r for r in map(json.loads, (OUT / "variant_samples.jsonl").read_text().splitlines())
               if r["arm"] == "current" and r.get("pass_turn") is not None}
    report = {}
    for lever in LEVERS:
        cells: dict = defaultdict(lambda: [0, 0, 0])  # [current spoke, lever spoke, n]
        for r in map(json.loads, (OUT / "lever_samples.jsonl").read_text().splitlines()):
            if r["arm"] != lever or r.get("pass_turn") is None or r["turn"] not in value or r["turn"] not in current:
                continue
            cell = cells["valuable" if value[r["turn"]] in "ABC" else "D"]
            cell[0] += current[r["turn"]]["pass_turn"] is False
            cell[1] += r["pass_turn"] is False
            cell[2] += 1
        report[lever] = {cls: {"current": f"{c}/{n}", lever: f"{s}/{n}"} for cls, (c, s, n) in sorted(cells.items())}
    (OUT / "lever_scores.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


GATE_V2_SYSTEM = """You read a Werewolf day discussion and one NEW line a player has just written on the
open floor, having read the lines before it. Your job is to say whether the new line adds anything,
so the table hears each point once and no filler.

A line adds something when it has at least one of:
- a fact the table does not have yet: a claim about the speaker's OWN role, night action or result,
  or a fact from the game record that no earlier line pointed out today;
- a reading of its own: an inference, a consequence or a point of view that no earlier line put,
  with its reason. It counts even when it disagrees with the table, and even when it starts from an
  earlier observation, as long as it gives a new reason or draws a different conclusion;
- a question or a test nobody has asked today: a specific player asked something no earlier line
  asked them, or a concrete check to run.
A player confirming or denying what was said about THEMSELVES always adds something.

A line adds nothing when all it does is one or more of:
- restate a point an earlier line made (the same observation, the same suspicion of the same player
  for the same reason, the same proposal), in any wording;
- agree with an earlier line without a new reason;
- repeat a request or a question an earlier line already made;
- filler: say there is little to go on, urge caution or patience, or give general advice that names
  no player, fact or test.

When in doubt, it adds something. Judge only whether it adds, never whether it is true or wise.

Answer in three steps, in order: the new line's point in one sentence; what it adds (exactly
"nothing" if it adds nothing); then, only if it adds nothing, the player whose earlier line it
restates, agrees with or repeats (the first one), or "none" if it is filler that repeats no
particular line."""
"""Candidate echo-gate bar (owner, 2026-10-18: the gate sorts, holding restatement and filler): step
1's kind D is what it holds, A-C what it keeps."""

GATE_V3_SYSTEM = """You read a Werewolf day discussion and one NEW line a player has just written on the
open floor, having read the lines before it. Your job is to say whether the new line adds anything,
so the table hears each point once and no filler.

A line adds something when it has at least one of:
- a fact the table does not have yet: the speaker's claim about their OWN role, or their own night
  action or result. Repeating what the morning report, the game master's record or an earlier line
  already says is not a new fact;
- a reading of its own: an inference, a consequence or a point of view that no earlier line put,
  with its reason. It counts even when it disagrees with the table, and even when it starts from an
  earlier observation, as long as it gives a new reason or draws a different conclusion;
- a question or a test aimed at a specific named player that no earlier line put to them, or a
  concrete check that names who should do what. A general call ("whoever has a result, post it",
  "let's hear claims", "everyone name a vote") adds something only if no earlier line made one.
A player confirming or denying what was said about THEMSELVES always adds something.

A line adds nothing when all it does is one or more of:
- restate a point an earlier line made, or what the record already says, in any wording;
- agree with an earlier line without a new reason;
- repeat a request or a question an earlier line already made, even in other words;
- filler: say there is little to go on, urge caution or patience, say the speaker will wait or hold
  their information, or give general advice that names no player, fact or test.

Judge the line part by part: if any one part adds something, the line adds something.
Judge only whether it adds, never whether it is true or wise.

Answer in three steps, in order: the new line's point in one sentence; what it adds (exactly
"nothing" if it adds nothing); then, only if it adds nothing, the player whose earlier line it
restates, agrees with or repeats (the first one), or "none" if it is filler that repeats no
particular line."""
"""Second candidate (2026-10-18): v2 kept lines that restate the morning report and repeat a general
call for claims; v3 says both are nothing new."""
GATE_CANDIDATES = {"v2": GATE_V2_SYSTEM, "v3": GATE_V3_SYSTEM}



def gate_candidate_holds(system: str, message: str, player: str, earlier: list) -> bool:
    from langchain_core.prompts import ChatPromptTemplate
    from pydantic import Field

    from Agents.llm_factory import get_llm_judge
    from Agents.schemas.output import LenientToolCallModel

    class LineEchoVerdict(LenientToolCallModel):
        new_point: str = Field(description="The new line's point in one sentence: what it says about the game.")
        adds: str = Field(description=(
            "What the new line adds that the discussion did not have: a fact, a reading with its reason, "
            "a question or test nobody asked. Write exactly 'nothing' only if it restates, agrees without a "
            "new reason, repeats a request already made, or is filler."))
        same_point_as: str = Field(description=(
            "Empty string unless adds is 'nothing'. Then the player id of the FIRST earlier line the new line "
            "restates, agrees with or repeats, or 'none' if it is filler that repeats no particular line."))

    spoken = [e for e in earlier if not e.passed and e.message and e.player != "game_master"]
    lines = "\n".join(f"{i + 1}. {e.player}: {e.message}" for i, e in enumerate(spoken)) or "(nothing yet)"
    prompt = ChatPromptTemplate.from_messages([("system", system), ("human", """The discussion so far:
{earlier}

The new line, from {player}:
{message}

First its point, then what it adds, then (only if it adds nothing) whose line it repeats, or "none".""")])
    verdict = (prompt | get_llm_judge().with_structured_output(LineEchoVerdict)).invoke(
        {"earlier": lines, "player": player, "message": message})
    return (verdict.adds or "").strip().lower().rstrip(".") == "nothing"


def _earlier_today(turn: str) -> list:
    """The day's channel before the turn's entry, as the gate would see it."""
    from Agents.schemas.game_events import DayChannel

    game, day, player, i = turn.rsplit(":", 3)
    capture = json.loads(gzip.open(GAMES / f"{game}.capture.json.gz", "rt").read())
    day_entries = [e for e in capture["final_state"]["day_channel"] if e["day"] == int(day)]
    mine = [n for n, e in enumerate(day_entries) if e["player"] == player]
    return [DayChannel(**e) for e in day_entries[:mine[int(i)]]]


def gate_check(tag: str = "") -> None:
    """The current echo gate and the candidates on step 1's judged open-floor lines (posted and forced):
    how many of the D lines each holds, and how many of the A-C lines. ``tag`` names the run's files
    (e.g. the judge thinking level it ran at)."""
    from Agents.turn.echo_gate import line_echo_of

    judged = [v for v in _verdicts("verdicts", "blind_key.json").values() if v["round"] == "proactive"]
    items = {json.loads(line)["turn"]: json.loads(line) for line in (OUT / "items.jsonl").read_text().splitlines()}
    with (OUT / f"gate_check{tag}.jsonl").open("w") as fh:
        for v in judged:
            item = items[v["turn"]]
            earlier = _earlier_today(v["turn"])
            row = {"turn": v["turn"], "kind": v["kind"], "source": item["kind"],
                   "current_holds": bool(line_echo_of(item["line"], item["player"], earlier))}
            for name, system in GATE_CANDIDATES.items():
                try:
                    row[f"{name}_holds"] = gate_candidate_holds(system, item["line"], item["player"], earlier)
                except Exception as e:  # recorded; the line drops out of that candidate's count
                    row |= {f"{name}_holds": None, f"{name}_error": str(e)[:200]}
            fh.write(json.dumps(row) + "\n")
            print(row, flush=True)
    rows = [json.loads(line) for line in (OUT / f"gate_check{tag}.jsonl").read_text().splitlines()]
    report = {}
    for gate in ["current_holds"] + [f"{n}_holds" for n in GATE_CANDIDATES]:
        cells: dict = defaultdict(lambda: [0, 0])
        for r in rows:
            if r.get(gate) is not None:
                cells["D" if r["kind"] == "D" else "A-C"][0] += r[gate]
                cells["D" if r["kind"] == "D" else "A-C"][1] += 1
        report[gate] = {k: f"{h}/{n} held" for k, (h, n) in sorted(cells.items())}
    (OUT / f"gate_check{tag}_scores.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


NEW_GAMES = OUT / "games"
"""Step 5: whole games under the step-4 build, on the deals of persona games voices-01..04 (voices on)."""


def _round_counts(path: Path) -> dict:
    channel = json.loads(gzip.open(path, "rt").read())["final_state"]["day_channel"]
    counts: dict = defaultdict(int)
    for e in channel:
        if e["player"] == "game_master" or e["day_round"] == "closing":
            continue
        kind = "held" if e.get("gated_candidate") else "spoken" if (e.get("message") or "").strip() else "passed"
        counts[f"{e['day_round']}:{kind}"] += 1
    counts["days"] = len({e["day"] for e in channel})
    return dict(sorted(counts.items()))


def games_score() -> None:
    """Per game: the open floor's spoken, passed and held lines, beside the earlier game on its deal."""
    report = {}
    for path in sorted(NEW_GAMES.glob("*.capture.json.gz")):
        label = path.name.removesuffix(".capture.json.gz")
        report[label] = {"before": _round_counts(GAMES / path.name), "after": _round_counts(path)}
    (OUT / "games_scores.json").write_text(json.dumps(report, indent=1))
    print(json.dumps(report, indent=1))


def packets(judges: int = 4) -> None:
    """Blind packets: each item's context and line, no word on whether it was spoken, held or forced."""
    rng = random.Random(SEED)
    items = [json.loads(line) for line in (OUT / "items.jsonl").read_text().splitlines()]
    items = [i for i in items if (i.get("line") or "").strip()]
    rng.shuffle(items)
    key, packs = {}, [[] for _ in range(judges)]
    for n, item in enumerate(items):
        name = f"s{n:03d}"
        key[name] = {"turn": item["turn"], "kind": item["kind"], "round": item["round"], "forced": item["forced"],
                     "pass_reason": item["pass_reason"]}
        stage = "the opening round (each player speaks once, before seeing the others)" if item["round"] == "opening" \
            else "the day's discussion"
        packs[n % judges].append(
            f"### {name}\nSpeaker: {item['player']}, during {stage}.\n\nEarlier days (summary, most recent part):\n"
            f"{item['context']['earlier_days']}\n\nToday's discussion so far, as the speaker saw it:\n"
            f"{item['context']['today']}\n\nTHE LINE:\n{item['line']}\n")
    (OUT / "blind_key.json").write_text(json.dumps(key, indent=1))
    for j, pack in enumerate(packs):
        (OUT / f"packet_{j + 1}.md").write_text("\n".join(pack))
    print({f"packet_{j + 1}": len(p) for j, p in enumerate(packs)})


if __name__ == "__main__":
    {"sample": sample, "packets": packets, "variants": variants, "variant_packets": variant_packets,
     "variant_score": variant_score, "levers": levers, "lever_score": lever_score,
     "gate_check": gate_check, "games_score": games_score}[sys.argv[1]](*sys.argv[2:])
