"""Freeze the day turns that report or argue a night sighting, for the visit-wording replay A/B.

Owner's complaint (2026-10-21): in game 2b29bfe8 (DeepSeek V4.1 Flash) day 2 spent ~15 lines on what
"came to" / "went to" / "at my door" mean after a Trailseer said its followed target "came to visit
me". Suspected cause: the physical metaphor of a night "visit". Arm A replays these turns on the
current wording (tag ``visit-wording-baseline``); arm B on the same rules worded as "targeting"
("X targeted Y", Trailseer tracks, Sentinel watches), from a worktree on that tag. Judged afterwards
by chat subagents on the blind file, not by the bench's judge, so the cases carry no golden.

Two slices: ``report`` (a seat with a watch or follow result giving it, its first report turn) and
``react`` (turns answering a sighting claim). Each case is the state just before the original line,
read read-only from the game's LangGraph checkpoint (``haiku_game_turn_cases.day_states``). Turn seqs
below are the events table's ``seq``; the day and channel seq come from that event.

  poetry run python evaluation/experiments/visit_wording_cases.py           # cases
  poetry run python evaluation/experiments/visit_wording_cases.py blind [A C dir]  # samples -> blind file
  poetry run python evaluation/experiments/visit_wording_cases.py score [dir]  # judged -> rates

Record and result: evidence/gameplay/data/visit_wording_ab/README.md.
"""

from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from math import comb
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.experiments.haiku_game_turn_cases import day_states, state_before  # noqa: E402
from evaluation.src.data.builders.hallucination_bench import _case_id  # noqa: E402

OUT = Path("evidence/gameplay/data/visit_wording_ab")

G_2B29 = "2b29bfe8-714d-4aa8-a4c2-f92b08d02aa5"   # DeepSeek V4.1 Flash, the owner's complaint
G_2500 = "25003626-2d0f-4150-9e3b-1f828d53a149"   # Claude Haiku 5.5
G_64E0 = "64e0f58b-69de-4a1f-bb33-5812b6b7db2b"   # DeepSeek V4.1 Flash
# 140610ad (DeepSeek V4.1 Flash) was searched too: its lineup has no Sentinel or Trailseer.

TURNS = {
    "report": [(G_2B29, 125), (G_2B29, 223), (G_2500, 550), (G_2500, 556), (G_2500, 691),
               (G_2500, 802), (G_64E0, 127), (G_64E0, 320)],
    "react": [(G_2B29, 144), (G_2B29, 172), (G_2B29, 181), (G_2B29, 199), (G_2B29, 239),
              (G_2B29, 248), (G_2B29, 266), (G_2500, 566), (G_2500, 572), (G_2500, 605),
              (G_2500, 708)],
}


def _events(game: str, seqs: list[int]) -> dict[int, dict]:
    import psycopg
    from dotenv import dotenv_values

    dsn = dotenv_values(".env")["WW_POSTGRES_DSN"]
    with psycopg.connect(dsn, options="-c default_transaction_read_only=on") as conn:
        rows = conn.execute("select seq, payload from events where game_id=%s and seq = any(%s)",
                            (game, seqs)).fetchall()
    return {s: p for s, p in rows}


def _context(case: dict) -> str:
    """The situation a judge needs: the true roles, who targeted whom each night (the private
    records), the claims on record, and the last lines before the turn."""
    st, day = case["state"], case["day"]
    lines = [f"## {case['case_id']} ({case['slice']})",
             f"Game {case['game_id']}, day {day}, speaker {case['speaker']} (true role: {case['role']}).", "",
             "True roles: " + ", ".join(f"{p}={r}" for p, r in sorted(st["roles"].items(),
                                                                      key=lambda x: int(x[0].split('_')[1]))), ""]
    lines.append("Night records (ground truth, private to each actor):")
    for r in sorted(st.get("night_actions") or [], key=lambda r: r["day"]):
        lines.append(f"- night {r['day']}: {r['actor']} {r['action']} {r.get('target') or '-'}: {r['outcome']}")
    own = [r for r in st.get("night_actions") or [] if r["actor"] == case["speaker"]]
    if not own:
        lines.append(f"(the speaker has no night record of its own)")
    claims = [m for m in st.get("day_channel") or [] if m.get("claim", "none") != "none" or m.get("claimed_night_actions")]
    lines += ["", "Claims on record (in order):"]
    for m in claims:
        acts = "; ".join(f"n{a['night']} {a['action']} {a.get('target') or '-'} -> {a.get('result')}"
                         + (f" saw {', '.join(a['seen'])}" if a.get("seen") else "")
                         for a in m.get("claimed_night_actions") or [])
        lines.append(f"- day {m['day']} #{m['seq']} {m['player']} claims {m.get('claim', 'none')}"
                     + (f" [{acts}]" if acts else ""))
    today = [m for m in st.get("day_channel") or [] if m["day"] == day and not m.get("passed")
             and m["player"] != "game_master"]
    lines += ["", f"Last lines today before the turn ({len(today)} so far):"]
    for m in today[-6:]:
        lines.append(f"- #{m['seq']} {m['player']}: {m['message']}")
    lines += ["", f"Original line: {case['original'][0]}", ""]
    return "\n".join(lines)


def main() -> None:
    cases, skipped, context = [], [], []
    states: dict[str, list[dict]] = {}
    for slice_, turns in TURNS.items():
        for game, seq in turns:
            ev = _events(game, [seq]).get(seq)
            if not ev or ev.get("type") != "speech":
                skipped.append(f"{game[:8]} seq {seq}: no speech event")
                continue
            if game not in states:
                states[game] = day_states(game)
            try:
                state, entry = state_before(states[game], ev["day"], ev["channel_seq"])
            except (SystemExit, StopIteration, ValueError) as e:
                skipped.append(f"{game[:8]} seq {seq}: no checkpoint just before it ({e})")
                continue
            assert entry["player"] == ev["player"], (game, seq, entry["player"], ev["player"])
            firing = entry.get("firing_reason") or {"tier": "proactive", "owes": []}
            case = {
                "case_id": _case_id(f"visit_{slice_}", game[:8], ev["day"], ev["player"], ev["channel_seq"]),
                "source": "live_checkpoint", "kind": "positive", "slice": slice_, "context": "",
                "game_id": game[:8], "game_arm": "live", "phase": "day_discussion", "day": ev["day"],
                "speaker": ev["player"], "role": state["roles"][ev["player"]],
                "state": state, "firing_reason": firing,
                "memory": {"observations": [], "strategy_points": []},
                "facts": {}, "golden": None, "event_seq": seq,
                "original": [entry.get("message") or "(passed)"], "original_round": entry["day_round"],
            }
            cases.append(case)
            context.append(_context(case))
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "cases.jsonl").write_text("\n".join(json.dumps(c) for c in cases) + "\n")
    (OUT / "case_context.md").write_text(
        "# Visit-wording A/B: case context\n\nPer case: the true roles, the night records (who targeted "
        "whom, as each actor was told), the claims on record and the last lines before the turn. "
        "Records are quoted in the original game's (arm A) wording.\n\n" + "\n".join(context))
    for s in skipped:
        print("skipped:", s)
    print({k: sum(c["slice"] == k for c in cases) for k in TURNS}, f"-> {OUT / 'cases.jsonl'}")


def blind(seed: int = 20261021, arms: tuple[str, ...] = ("A", "B"), folder: Path = OUT) -> None:
    """samples_<arm>.jsonl of ``arms`` → blind.jsonl (public lines, arm hidden, shuffled) + key.jsonl,
    written to ``folder``."""
    cases = {json.loads(line)["case_id"]: json.loads(line)
             for line in (OUT / "cases.jsonl").read_text().splitlines() if line.strip()}
    rows = []
    for arm in arms:
        for line in (OUT / f"samples_{arm}.jsonl").read_text().splitlines():
            s = json.loads(line)
            if not s.get("valid"):
                continue
            text = next((u["text"] for u in s["units"] if u["unit"] == "message"), None)
            c = cases[s["case_id"]]
            rows.append({"arm": arm, "case_id": s["case_id"], "slice": c["slice"], "seat": c["speaker"],
                         "sample": s["sample"], "message": text if text is not None else "(passed)"})
    random.Random(seed).shuffle(rows)
    folder.mkdir(exist_ok=True)
    with open(folder / "blind.jsonl", "w") as b, open(folder / "key.jsonl", "w") as k:
        for i, r in enumerate(rows):
            oid = f"v{i:03d}"
            b.write(json.dumps({"id": oid, "case_id": r["case_id"], "slice": r["slice"], "seat": r["seat"],
                                "message": r["message"]}) + "\n")
            k.write(json.dumps({"id": oid, "arm": r["arm"], "case_id": r["case_id"], "sample": r["sample"]}) + "\n")
    print(f"{len(rows)} lines -> {folder / 'blind.jsonl'}")


def score(folder: Path = OUT) -> None:
    """Join the judges' verdicts (judged_*.jsonl) to key.jsonl: rates per arm and slice, and a sign
    test over the cases whose rate differs between the arms."""
    key = {r["id"]: r for r in map(json.loads, (folder / "key.jsonl").read_text().splitlines())}
    blind_rows = {r["id"]: r for r in map(json.loads, (folder / "blind.jsonl").read_text().splitlines())}
    verdicts = {v["id"]: v for p in sorted(folder.glob("judged_*.jsonl"))
                for v in map(json.loads, filter(str.strip, p.read_text().splitlines()))}
    print(f"{len(verdicts)} verdicts, {len(set(blind_rows) - set(verdicts))} missing")
    rows = [{**verdicts[i], **key[i], "slice": blind_rows[i]["slice"]} for i in verdicts]
    first, second = sorted({r["arm"] for r in rows})  # the baseline arm sorts first (A before B, C)

    def rate(sub: list[dict], label: str) -> str:
        vals = [r[label] for r in sub if r.get(label) is not None]
        return f"{sum(vals)}/{len(vals)} ({100 * sum(vals) / len(vals):.0f}%)" if vals else "-"

    for sl in ("all", "report", "react"):
        for arm in (first, second):
            sub = [r for r in rows if r["arm"] == arm and sl in ("all", r["slice"])]
            print(f"{sl:7} {arm}: n={len(sub):3}  mech {rate(sub, 'mech'):14} chew {rate(sub, 'chew'):14} "
                  f"clear {rate(sub, 'clear')}")
    for label in ("mech", "chew", "clear"):
        by: dict[str, dict[str, list[int]]] = defaultdict(lambda: {first: [], second: []})
        for r in rows:
            if r.get(label) is not None:
                by[r["case_id"]][r["arm"]].append(r[label])
        sign = -1 if label == "clear" else 1  # a higher clear rate is the better one
        diffs = [sign * (sum(c[second]) / len(c[second]) - sum(c[first]) / len(c[first]))
                 for c in by.values() if c[first] and c[second]]
        better, worse = sum(d < 0 for d in diffs), sum(d > 0 for d in diffs)
        n = better + worse
        p = min(1.0, 2 * sum(comb(n, k) for k in range(min(better, worse) + 1)) / 2 ** n) if n else 1.0
        print(f"sign test {label}: {second} better on {better} cases, worse on {worse}, p={p:.3f}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["blind"]:  # blind [arm arm folder]: e.g. blind A C <dir>
        blind(arms=tuple(sys.argv[2:4]) or ("A", "B"), folder=Path(sys.argv[4]) if len(sys.argv) > 4 else OUT)
    elif sys.argv[1:2] == ["score"]:
        score(Path(sys.argv[2]) if len(sys.argv) > 2 else OUT)
    else:
        main()
