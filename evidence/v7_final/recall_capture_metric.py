"""v7 recall-arm — capture-rate of flagged pivotal turns, per arm. Zero additional spend.

Question: does suggestive-anchoring lift FLASH-LITE's capture of pivotal turns up toward PRO's?
Arms (same 3 slice games): pro=v6_1, flash-lite=_ab_flite, flash-lite+anchor=_ab_flite_anchor.

Capture = for each deterministic pivotal turn (recall_flags.pivotal_turns), did the arm produce >=1 obs
in a cell of that turn's PHASE whose situation references the same board stage (alive-count within +-1)?
Alive-count is parsed from the obs situation ("final four", "down to 4 players", "N players left") — more
reliable than day numbers, and applied IDENTICALLY to every arm so the comparison is fair.

Manufacture guard: also report intra-stage distinctness of the obs that land on flagged turns, so a
capture gain isn't just padding the suggested turns.

  poetry run python evidence/v7_final/recall_capture_metric.py
"""

import json
import re
import sys
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.audits.recall_flags import pivotal_turns  # noqa: E402
from evaluation.src.studies.reextract_villager_day import DEFAULT_SOURCE, load_cases  # noqa: E402

SLICE = [str(c["game_id"]) for c in load_cases(Path(DEFAULT_SOURCE))[:3]]
ARMS = {"pro-2.5": "memory_stores/v6_1", "flash-lite": "memory_stores/_ab_flite",
        "flash-lite+anchor": "memory_stores/_ab_flite_anchor",
        "flash-lite+amplify": "memory_stores/_ab_flite_amplify"}
AB_GLOB = "batch_results/ab_*.jsonl"
WORDS = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9}


def _alive(sit: str):
    """Best-effort alive-count parsed from an obs situation, else None."""
    s = sit.lower()
    for w, n in WORDS.items():
        if f"final {w}" in s:
            return n
    m = re.search(r"down to (\d+)", s) or re.search(r"(\d+)\s+players?\s*(?:alive|remaining|left|are)", s) \
        or re.search(r"with (\d+) players", s)
    return int(m.group(1)) if m else None


def _tok(s):
    return {w for w in re.sub(r"[^a-z0-9]", " ", s.lower()).split() if len(w) > 2}


def _flags_by_game():
    recs = {}
    import glob
    for rf in sorted(glob.glob(AB_GLOB)):
        for line in open(rf):
            if not line.strip():
                continue
            r = json.loads(line)
            gid = str(r.get("game_id", ""))
            if gid in SLICE and gid not in recs and r.get("day_resolutions"):
                recs[gid] = pivotal_turns(r)
    return recs


def main() -> int:
    flags = _flags_by_game()
    total_flags = sum(len(v) for g, v in flags.items() if g in flags)
    print(f"slice: {[g[:8] for g in SLICE]} | pivotal turns flagged: {total_flags}\n")
    print(f"{'arm':20}{'tot obs':>9}{'flags hit':>11}{'capture%':>10}{'obs on flags':>14}{'stageJac':>9}")
    for arm, path in ARMS.items():
        p = Path(path) / "observations.json"
        if not p.exists():
            print(f"{arm:20}  (store missing — run not complete)")
            continue
        ns = json.load(open(p))["namespaces"]
        # obs by (gid, phase) -> [(alive, text)]
        by = {}
        tot_obs = 0
        for cell, recs in ns.items():
            phase = cell.split("/")[-1]
            for r in recs:
                v = r["value"]
                gid = str(v.get("game_id", ""))
                if gid not in SLICE:
                    continue
                tot_obs += 1
                by.setdefault((gid, phase), []).append(
                    (_alive(v.get("situation", "")),
                     " ".join(str(v.get(f, "")) for f in ("situation", "approach", "outcome"))))
        hit, landed_texts = 0, []
        for gid, turns in flags.items():
            for t in turns:
                cands = by.get((gid, t["phase"]), [])
                match = [txt for a, txt in cands if a is not None and abs(a - t["alive"]) <= 1]
                if match:
                    hit += 1
                    landed_texts.extend(match)
        # manufacture guard: distinctness among obs landing on flagged turns
        sims = [len(_tok(a) & _tok(b)) / max(len(_tok(a) | _tok(b)), 1)
                for a, b in combinations(landed_texts, 2)]
        mj = sum(sims) / len(sims) if sims else 0.0
        print(f"{arm:20}{tot_obs:>9}{hit:>11}{hit/max(total_flags,1):>9.0%}{len(landed_texts):>14}{mj:>9.2f}")
    print("\nread WITH the manufacture guard: a capture gain with stageJac spiking ~ padding, not recall.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
