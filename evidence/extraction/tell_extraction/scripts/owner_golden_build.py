"""Owner-golden bundle builder — PROBE SCAFFOLDING (experiment_log.md §13/§15; the owner's
detector-blind adjudication is the run-gating golden the temp golden stood in for).

Builds everything the owner needs for the certifying golden, in two blindness layers:

- OWNER-VISIBLE (outputs/owner_golden/): role-blind full-view transcripts, the two channel
  checklists, a blank phase-1 answer sheet, and README.md with the protocol. Nothing in this
  layer reveals roles, detector output, or which cells have detections.
- SEALED (outputs/owner_golden/SEALED_do_not_open/): the selected game records (roles
  inside), the stored CACHED detector runs being certified, and the phase-2 candidate pool.
  The owner opens ONLY phase2_sheet.md, and only after committing phase-1 answers.

Cell design: 6 held-out games (distinct boards; the five v6ab memory arms cycled, so no two
cells share a board — sidesteps the paired-arms hazard), 2 focus players per game (one
guaranteed to carry >=1 union detection so precision is measurable, one drawn at random),
both channels each -> 24 cells. Recall is bounded by POOLING (phase 2), not by trusting the
blind read to be exhaustive.

Stages (run in order; --detect is the only paid one, ~$0.8 at observed billing):
  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/owner_golden_build.py --select
  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/owner_golden_build.py --detect
  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/owner_golden_build.py --bundle
  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/owner_golden_build.py --pool
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

PROBE_DIR = Path(__file__).resolve().parent.parent
ROOT = PROBE_DIR.parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tell_mining_probe import _game_days, _render_day, load_games

OG = PROBE_DIR / "outputs" / "owner_golden"
SEALED = OG / "SEALED_do_not_open"
# arms cycled so all six boards are distinct (the v6ab arms replay the SAME 12 boards, so
# distinct game_ids <=> distinct boards); 6th pick wraps to the first arm
ARMS = ["townobs", "townsp", "skobs", "sksp", "skboth", "townobs"]
rng = random.Random(20260713)


def _load_selected() -> list[dict]:
    return [json.loads(l) for l in open(SEALED / "games.jsonl")]


def stage_select() -> None:
    SEALED.mkdir(parents=True, exist_ok=True)
    used, sel = set(), []
    for arm in ARMS:
        games = load_games(str(ROOT / f"batch_results/v6ab_{arm}.jsonl"), 999)
        pool = sorted((g for g in games if g["game_id"] not in used),
                      key=lambda g: g["game_id"])
        pick = rng.choice(pool)
        pick["_arm"] = arm
        used.add(pick["game_id"])
        sel.append(pick)
    with open(SEALED / "games.jsonl", "w") as f:
        for g in sel:
            f.write(json.dumps(g) + "\n")
    print(f"selected {len(sel)} games (distinct boards): "
          + ", ".join(f"{g['_arm']}:{g['game_id'][:8]}" for g in sel))


def stage_detect() -> None:
    """The stored CACHED k=2 run on the six games — the artifact the golden certifies."""
    from detector_probe import run as det_run
    dumps = str(SEALED / "games.jsonl")
    det_run(dumps, 6, "det_v1", SEALED / "det_v1_cached.jsonl", cache=True)
    det_run(dumps, 6, "det_v2", SEALED / "det_v3split_cached.jsonl",
            split_view=True, cache=True)


def _union_rows() -> list[dict]:
    rows, seen = [], set()
    for fn in ("det_v1_cached.jsonl", "det_v3split_cached.jsonl"):
        for l in open(SEALED / fn):
            r = json.loads(l)
            key = (r["game_id"], r["player"], r["channel"], r["tell_id"], r["day"])
            if key not in seen:
                seen.add(key)
                rows.append(r)
    return rows


def stage_bundle() -> None:
    games = _load_selected()
    union = _union_rows()
    checklist = json.load(open(PROBE_DIR / "outputs" / "checklist_v0.json"))

    # PINNED focus map — the set published to the owner and the prelabel agents on
    # 2026-07-13 (originally rng-drawn: one detected player + one random per game), with ONE
    # swap: g5's player_1 was a night-1 death with zero day footprint (a wasted cell), so it
    # was replaced by a rng(20260714) draw from that game's day-active players -> player_2.
    # Pinned as literals because the published set is a frozen contract; the original draw
    # proved non-reproducible across script edits, so rng reproduction is not trusted here.
    focus = {1: ("player_5", "player_6"), 2: ("player_2", "player_9"),
             3: ("player_4", "player_8"), 4: ("player_6", "player_9"),
             5: ("player_2", "player_3"), 6: ("player_3", "player_6")}
    cells, sheet = [], []
    for i, rec in enumerate(games, 1):
        gid = rec["game_id"]
        f1, f2 = focus[i]
        tpath = OG / "transcripts" / f"g{i}_{gid[:8]}.txt"
        tpath.parent.mkdir(parents=True, exist_ok=True)
        tpath.write_text("\n\n".join(_render_day(rec, d) for d in _game_days(rec)))
        sheet.append(f"\n\n## Game g{i}  (transcripts/g{i}_{gid[:8]}.txt)\n")
        for p in (f1, f2):
            for ch in ("vote", "discussion"):
                cells.append({"cell_id": f"g{i}_{p}_{ch}", "game": f"g{i}",
                              "game_id": gid, "player": p, "channel": ch})
                sheet.append(
                    f"\n### {f'g{i}_{p}_{ch}'} — focus **{p}**, channel **{ch.upper()}**\n"
                    "<!-- one line per finding; copy the line below; days comma-separated; "
                    "quote verbatim <=25 words; append ? to tell id if unsure -->\n"
                    "- tell: <tell_id> | days: <d,d> | quote: \"...\"\n"
                    "- (none found)\n")

    (OG / "cells.json").write_text(json.dumps(cells, indent=1))
    (OG / "answer_sheet.md").write_text(
        "# Phase-1 answer sheet — owner golden (detector-blind)\n"
        "Fill per cell; delete the `(none found)` line if you record findings. "
        "Only claim what you can quote.\n" + "".join(sheet))
    for ch in ("vote", "discussion"):
        (OG / f"checklist_{ch}.md").write_text(
            f"# {ch.upper()} checklist (frozen v0 — the detector saw exactly these)\n\n"
            + "\n".join(f"- **[{t['tell_id']}]** {t['text']}" for t in checklist[ch]))
    print(f"{len(cells)} cells across {len(games)} games -> {OG}")

    # pool skeleton: cached run + the pre-existing UNCACHED held-out rows for the same games
    arm_of = {g["game_id"]: g["_arm"] for g in games}
    pool = defaultdict(lambda: {"days": set(), "quotes": {}, "sources": set()})
    focus = {(c["game_id"], c["player"], c["channel"]) for c in cells}

    def add(r: dict, src: str) -> None:
        if (r["game_id"], r["player"], r["channel"]) not in focus:
            return
        e = pool[(r["game_id"], r["player"], r["channel"], r["tell_id"])]
        e["days"].add(r["day"])
        e["quotes"].setdefault(r["day"], r["evidence_quote"])
        e["sources"].add(src)

    for r in union:
        add(r, "cached_union")
    for gid, arm in arm_of.items():
        for suffix in ("v1", "v3split"):
            fp = PROBE_DIR / "outputs" / "heldout" / f"{arm}_{suffix}.jsonl"
            for l in open(fp):
                r = json.loads(l)
                if r["game_id"] == gid and r["source"] == f"v6ab_{arm}.jsonl":
                    add(r, f"heldout_{suffix}")
    out = [{"game_id": g, "player": p, "channel": ch, "tell_id": t,
            "days": sorted(e["days"]), "quotes": e["quotes"],
            "sources": sorted(e["sources"])}
           for (g, p, ch, t), e in sorted(pool.items())]
    (SEALED / "pool_candidates.json").write_text(json.dumps(out, indent=1))
    print(f"pool skeleton: {len(out)} candidates (detector runs; Opus prelabels join at --pool)")


def stage_pool() -> None:
    """Merge Opus prelabels (SEALED/opus_prelabels.json, written after the agents return)
    into the candidate pool and emit the SOURCE-BLIND phase-2 sheet — candidates shuffled,
    no hint of how many instruments proposed each row."""
    cand = json.load(open(SEALED / "pool_candidates.json"))
    pre_path = SEALED / "opus_prelabels.json"
    if pre_path.exists():
        idx = {(c["game_id"], c["player"], c["channel"], c["tell_id"]): c for c in cand}
        for r in json.load(open(pre_path)):
            key = (r["game_id"], r["player"], r["channel"], r["tell_id"])
            e = idx.setdefault(key, {"game_id": r["game_id"], "player": r["player"],
                                     "channel": r["channel"], "tell_id": r["tell_id"],
                                     "days": [], "quotes": {}, "sources": []})
            e["days"] = sorted(set(e["days"]) | {r["day"]})
            e["quotes"].setdefault(str(r["day"]), r.get("evidence_quote", ""))
            if "opus" not in e["sources"]:
                e["sources"].append("opus")
        cand = list(idx.values())
        (SEALED / "pool.json").write_text(json.dumps(cand, indent=1))
    else:
        print("NOTE: no opus_prelabels.json yet — sheet built from detector rows only")

    cells = json.load(open(OG / "cells.json"))
    checklist = json.load(open(PROBE_DIR / "outputs" / "checklist_v0.json"))
    text_of = {t["tell_id"]: t["text"] for ch in checklist for t in checklist[ch]}
    by_cell = defaultdict(list)
    for c in cand:
        by_cell[(c["game_id"], c["player"], c["channel"])].append(c)
    lines = ["# Phase-2 pool sheet — open ONLY after phase-1 answers are committed\n",
             "For each candidate, mark every claimed day `[y]` (player exhibited the tell "
             "that day) or `[n]`. The quote is a pointer, not proof — reject the day if the "
             "record doesn't support the behavior. Add days the candidate missed as `+d`.\n"]
    for cell in cells:
        rows = by_cell.get((cell["game_id"], cell["player"], cell["channel"]), [])
        rng.shuffle(rows)
        lines.append(f"\n## {cell['cell_id']} — {cell['player']} / {cell['channel'].upper()}\n")
        if not rows:
            lines.append("(no pooled candidates for this cell)\n")
        for c in rows:
            lines.append(f"- **[{c['tell_id']}]** {text_of.get(c['tell_id'], '(retired id)')}")
            for d in c["days"]:
                q = c["quotes"].get(str(d)) or c["quotes"].get(d) or ""
                lines.append(f"  - `[ ]` day {d} — \"{q}\"")
        lines.append("")
    (SEALED / "phase2_sheet.md").write_text("\n".join(lines))
    n = sum(len(v) for v in by_cell.values())
    print(f"phase-2 sheet: {n} candidates over {len(cells)} cells -> SEALED/phase2_sheet.md")


def main() -> int:
    ap = argparse.ArgumentParser()
    for s in ("select", "detect", "bundle", "pool"):
        ap.add_argument(f"--{s}", action="store_true")
    a = ap.parse_args()
    if a.select:
        stage_select()
    if a.detect:
        stage_detect()
    if a.bundle:
        stage_bundle()
    if a.pool:
        stage_pool()
    if not any((a.select, a.detect, a.bundle, a.pool)):
        print(__doc__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
