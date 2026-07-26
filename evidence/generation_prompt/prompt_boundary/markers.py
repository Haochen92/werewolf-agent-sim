"""Deterministic pathology markers for the prompt-boundary cleanup (pre/post).

No LLM. Counts two pathologies the prompt change targets, over day-discussion
messages:

  STOCK   (goal 1, naturalness): canned formulas / mirroring openers that flood
          the logs and read as parallel monologue filler.
  POLICE  (goal 2, degenerate pseudo-strategy): manufacturing suspicion out of
          tone / talkativeness / silence / "evasiveness" rather than concrete
          information.

These are *lower bounds* (substring match misses paraphrase) and a regression
anchor only — the verdict is by eyeball against excerpts. Run identical on the
pre-change (gate) and post-change transcripts so the delta is apples-to-apples.

Usage:
  poetry run python evidence/generation_prompt/prompt_boundary/markers.py PRE.jsonl POST.jsonl
  (each arg: path[:config_name]; config_name filters records, default all_disabled)
"""
from __future__ import annotations
import json, re, sys
from collections import Counter

STOCK = [
    "i agree with", "i agree", "fair point", "good point", "valid point",
    "that's a fair", "thats a fair", "exactly what the wolves want",
    "classic wolf", "let's not let them divide", "lets not let them divide",
    "divide and conquer", "playing both sides", "throw", "under the bus",
    "couldn't agree more", "couldnt agree more", "well said", "to your point",
    "as you said", "like you said", "building on", "to add to that",
]

POLICE = [
    "too quiet", "so quiet", "very quiet", "being quiet", "staying quiet",
    "stayed quiet", "been quiet", "remained quiet", "awfully quiet",
    "defensive", "evasive", "evading", "evasion", "deflect", "dodging",
    "dodge the question", "avoiding the question", "avoid the question",
    "not contributing", "isn't contributing", "isnt contributing",
    "fence-sitting", "fence sitting", "on the fence", "sitting on the fence",
    "wishy-washy", "non-committal", "noncommittal", "vague answer",
    "vague response", "being vague", "too vague", "just agreeing",
    "merely agreeing", "echoing", "going along with", "fly under the radar",
    "flying under the radar", "lying low", "laying low", "too passive",
    "overly cautious", "suspiciously quiet", "your tone", "the way you",
]


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").lower()).strip()


def dc_of(rec):
    r = rec.get("result")
    d = r.get("day_channel") if isinstance(r, dict) else None
    return d or rec.get("day_channel") or []


def real_msgs(dc):
    return [m for m in dc if not m.get("passed")]


def load(path, config_name):
    out = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        rec = json.loads(line)
        if rec.get("status") == "error":
            continue
        if config_name and rec.get("config_name") != config_name:
            continue
        dc = real_msgs(dc_of(rec))
        if dc:
            out.append((rec, dc))
    return out


def hits(text, lexicon):
    t = norm(text)
    return [m for m in lexicon if m in t]


def report(label, games):
    n_msgs = 0
    stock_msgs = police_msgs = 0
    stock_hits = Counter()
    police_hits = Counter()
    examples = {"STOCK": [], "POLICE": []}
    for rec, dc in games:
        for m in dc:
            n_msgs += 1
            msg = m.get("message", "")
            s = hits(msg, STOCK)
            p = hits(msg, POLICE)
            if s:
                stock_msgs += 1
                stock_hits.update(s)
                if len(examples["STOCK"]) < 8:
                    examples["STOCK"].append((m.get("player"), m.get("day"), s, msg[:160]))
            if p:
                police_msgs += 1
                police_hits.update(p)
                if len(examples["POLICE"]) < 8:
                    examples["POLICE"].append((m.get("player"), m.get("day"), p, msg[:160]))
    print(f"\n{'='*74}\n{label}   ({len(games)} games, {n_msgs} discussion messages)\n{'='*74}")
    if not n_msgs:
        print("  (no messages)")
        return
    print(f"  STOCK  msgs: {stock_msgs:3d} / {n_msgs}  ({stock_msgs/n_msgs:5.1%})   total marker hits: {sum(stock_hits.values())}")
    print(f"  POLICE msgs: {police_msgs:3d} / {n_msgs}  ({police_msgs/n_msgs:5.1%})   total marker hits: {sum(police_hits.values())}")
    print(f"  top STOCK : {stock_hits.most_common(8)}")
    print(f"  top POLICE: {police_hits.most_common(8)}")
    for cat in ("STOCK", "POLICE"):
        print(f"  -- {cat} examples --")
        for player, day, ms, txt in examples[cat]:
            print(f"    d{day} {player} {ms}: {txt!r}")


def by_phase(label, games):
    """Day-1 (zero-info on every board, so board-independent) vs day >=2."""
    msgs = [m for _, dc in games for m in dc]
    print(f"\n  {label} — phase split:")
    for tag, grp in [
        ("day 1 (zero-info)", [m for m in msgs if m.get("day") == 1]),
        ("day >=2", [m for m in msgs if m.get("day") and m["day"] > 1]),
    ]:
        n = len(grp)
        if not n:
            continue
        s = sum(1 for m in grp if hits(m.get("message", ""), STOCK))
        p = sum(1 for m in grp if hits(m.get("message", ""), POLICE))
        print(f"    {tag:18s} n={n:3d}  STOCK {s:2d} ({s/n:5.1%})  POLICE {p:2d} ({p/n:5.1%})")


if __name__ == "__main__":
    args = sys.argv[1:] or ["evidence/sequential_discussion/quality_gate/data/gate_sequential.jsonl"]
    loaded = []
    for a in args:
        path, _, cfg = a.partition(":")
        cfg = cfg or "all_disabled"
        games = load(path, cfg)
        report(f"{path}  [{cfg}]", games)
        loaded.append((f"{path} [{cfg}]", games))
    print(f"\n{'#'*74}\n# PHASE SPLIT (defuses easy-board confound: day 1 is zero-info everywhere)\n{'#'*74}")
    for label, games in loaded:
        by_phase(label, games)
