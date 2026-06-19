"""Is extraction's hindsight `net_verdict` calibrated to the actual game outcome — or noise?

Extraction (Agents/prompts/extraction/postgame.py) runs an OMNISCIENT whole-game pass: it's told
`GAME OUTCOME` and asked to judge each observation's `net_verdict` (positive/negative/mixed/unclear)
"from the END of the game." This checks whether that judgment tracks the deterministic
`role_faction_won` stamped on each stored observation.

Result (2026-06-17, store memory_stores/v6_1, n=932): STRONGLY calibrated — faction WON → 64%
positive / 25% negative; faction LOST → 21% positive / 65% negative; pos−neg separation +0.84,
positive for every role (deceivers strongest, SK/wolf +1.17). So the outcome-conditioning is REAL,
not rationalized noise.

CAVEAT — calibration is to the FACTION OUTCOME, not to per-action causal leverage. The cleanness
(+0.84 sep, ~65% concordance, only 3% "unclear" + 11% "mixed" → 87% confident-and-aligned) reads as
an OUTCOME HALO: net_verdict largely answers "did your side win?" and stamps that on every action,
not "did THIS move matter?" Because observations are not deterministically turn-anchored (the v6
criticality numbers on them are LLM-estimated, not game-state-derived), this check validates
extraction's LABELING, not its pivotalness SELECTION — they're different, and selection stays
unvalidated here. The ~22-25% within-faction minority is the only discrimination headroom and can't
be confirmed as signal vs noise from this data alone.

Implication for steering (see experiment_log.md): the halo is exactly the signal a deterministic
pivotalness anchor supplies — feed extraction the objective leverage of each turn so it can separate
a pivotal winning move from one that merely rode the win, while leaving the (trustworthy) labeling
and the multi-day causal-chain pass intact.

    PYTHONPATH=. poetry run python evidence/extraction_selection/netverdict_calibration.py
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

STORE = Path("memory_stores/v6_1/observations.json")


def _rows():
    ns = json.loads(STORE.read_text())["namespaces"]
    for nskey, recs in ns.items():
        role = nskey.split("/")[1] if "/" in nskey else "?"
        for r in recs:
            v = r.get("value", {})
            nv = (v.get("net_verdict") or "").strip().lower() or "(empty)"
            yield role, nv, v.get("role_faction_won")


def _frac(verdicts, target):
    c = Counter(verdicts)
    tot = sum(c.values())
    return f"{c.get(target,0)}/{tot} ({100*c.get(target,0)/tot:.0f}%)" if tot else "-"


def _posneg(verdicts):
    c = Counter(verdicts)
    tot = sum(c.values()) or 1
    return (c.get("positive", 0) - c.get("negative", 0)) / tot


def main() -> None:
    rows = list(_rows())
    missing = sum(1 for _, _, w in rows if w is None)
    print(f"total observations: {len(rows)}   missing role_faction_won: {missing}")
    print(f"net_verdict distribution: {dict(Counter(nv for _, nv, _ in rows))}\n")

    won = [nv for _, nv, w in rows if w is True]
    lost = [nv for _, nv, w in rows if w is False]
    print("=== net_verdict by deterministic faction outcome ===")
    print(f"{'':18}{'positive':>14}{'negative':>14}{'mixed':>12}{'unclear':>12}  n")
    for label, sub in (("faction WON", won), ("faction LOST", lost)):
        print(f"{label:18}{_frac(sub,'positive'):>14}{_frac(sub,'negative'):>14}"
              f"{_frac(sub,'mixed'):>12}{_frac(sub,'unclear'):>12}  {len(sub)}")
    print(f"\npos−neg share  |  WON: {_posneg(won):+.2f}   LOST: {_posneg(lost):+.2f}   "
          f"separation: {_posneg(won)-_posneg(lost):+.2f}")

    byrole = defaultdict(lambda: {"won": [], "lost": []})
    for role, nv, w in rows:
        if w is True:
            byrole[role]["won"].append(nv)
        elif w is False:
            byrole[role]["lost"].append(nv)
    print("\n=== per-role pos−neg separation (won vs lost) ===")
    for role in sorted(byrole):
        w_, l_ = byrole[role]["won"], byrole[role]["lost"]
        if len(w_) + len(l_) < 10:
            continue
        print(f"{role:14} WON {_posneg(w_):+.2f} (n={len(w_):3})   "
              f"LOST {_posneg(l_):+.2f} (n={len(l_):3})   sep {_posneg(w_)-_posneg(l_):+.2f}")


if __name__ == "__main__":
    main()
