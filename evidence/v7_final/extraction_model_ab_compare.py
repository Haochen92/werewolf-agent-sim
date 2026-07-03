"""v7 (c) model-capability pre-gate — compare pro / flash-3.5 / flash-lite extraction on the SAME 3-game
slice. Zero additional spend (reads the already-extracted stores).

  pro       = memory_stores/v6_1            (gemini-2.5-pro), subset to the slice game_ids
  flash-3.5 = memory_stores/_ab_f35         (gemini-3.5-flash)
  flash-lite= memory_stores/_ab_flite       (gemini-3.1-flash-lite)

Metrics: obs volume, intra-cell distinctness (token Jaccard near-restatement), de-halo
corr(net_verdict, faction_won). De-halo is THIN on 3 games (low faction-won variance) — directional only.

  poetry run python evidence/v7_final/extraction_model_ab_compare.py
"""

import json
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.studies.reextract_villager_day import DEFAULT_SOURCE, load_cases  # noqa: E402

SLICE = [str(c["game_id"]) for c in load_cases(Path(DEFAULT_SOURCE))[:3]]
OUTCOME = {str(c["game_id"]): c.get("game_outcome") for c in load_cases(Path(DEFAULT_SOURCE))[:3]}
TOWN = {"villager", "investigator", "healer", "vigilante"}
FACTION_OF = {"wolf": "wolves", "serial_killer": "serial_killer"}  # else -> villagers
VVAL = {"positive": 1.0, "negative": -1.0, "mixed": 0.0, "unclear": 0.0}
ARMS = {"pro(2.5)": "memory_stores/v6_1", "flash-3.5": "memory_stores/_ab_f35",
        "flash-lite": "memory_stores/_ab_flite"}


def _tok(s):
    return {w for w in "".join(c.lower() if c.isalnum() else " " for c in s).split() if len(w) > 2}


def _jac(a, b):
    return len(a & b) / len(a | b) if (a and b) else 0.0


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (vx * vy) if vx and vy else float("nan")


def faction_won(role, gid):
    fac = FACTION_OF.get(role, "villagers")
    return 1 if OUTCOME.get(gid) == fac else 0


def main() -> int:
    print(f"slice game_ids: {[g[:8] for g in SLICE]}  outcomes: "
          f"{[OUTCOME[g] for g in SLICE]}\n")
    print(f"{'arm':12}{'obs':>5}{'obs/cell':>9}{'cells':>6}{'meanJac':>8}{'neardup%':>9}{'deHalo r':>9}")
    for arm, path in ARMS.items():
        ns = json.load(open(f"{path}/observations.json"))["namespaces"]
        per_cell_game = defaultdict(list)   # (cell, gid) -> [value]
        verds, wons = [], []
        total = 0
        for cell, recs in ns.items():
            role = cell.split("/")[1]
            for r in recs:
                v = r["value"]
                gid = str(v.get("game_id", ""))
                if gid not in SLICE:        # subset pro store to the slice
                    continue
                per_cell_game[(cell, gid)].append(v)
                total += 1
                nv = v.get("net_verdict")
                if nv in VVAL:
                    verds.append(VVAL[nv]); wons.append(faction_won(role, gid))
        n_groups = len(per_cell_game)
        # distinctness
        sims, ndup, npair = [], 0, 0
        for vals in per_cell_game.values():
            if len(vals) < 2:
                continue
            toks = [_tok(" ".join(str(v.get(f, "")) for f in ("situation", "approach", "outcome")))
                    for v in vals]
            ms = [_jac(toks[i], toks[j]) for i, j in combinations(range(len(vals)), 2)]
            sims.append(sum(ms) / len(ms)); ndup += sum(1 for s in ms if s > 0.5); npair += len(ms)
        mj = sum(sims) / len(sims) if sims else 0.0
        r = _pearson(verds, wons)
        print(f"{arm:12}{total:>5}{total/max(n_groups,1):>9.2f}{n_groups:>6}{mj:>8.2f}"
              f"{(ndup/max(npair,1)):>8.1%}{r:>9.2f}")
    print("\nnote: de-halo r is THIN (3 games, 2 town-win / 1 SK-win) — directional, not a verdict.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
