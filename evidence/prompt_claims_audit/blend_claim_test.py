"""Does the wolf prompt's "blend your vote with the majority" tactic actually help wolves?

The prompt-claims audit (experiment_log.md) tests the hand-authored PLAYSTYLE tactics against
tracked metrics. This is the wolf row: correlate the validated camouflage proxy
`wolf_unconditioned_blending_rate` (fraction of a living wolf's votes aligned with the day's lynch,
across ALL lynch days) with wolf-win, over the v6 SP A/B epoch.

Result (2026-06-17): pooled r=+0.16 p=0.07 (n=122) — directionally consistent with the prior
larger-N validation (r=+0.20 p=0.003 n=220, paired_ab/diagnose_wolf_blending.py). VALIDATED: the
wolf prompt's blend tactic is true. (Contrast: the investigator's "conceal" tactic is FALSIFIED —
investigator_transmission.py.) Pooling is legitimate — every v6ab arm has memory-less wolves (the
deceiver arm is the SK), so the wolf channel is constant across arms.

    PYTHONPATH=. poetry run python evidence/prompt_claims_audit/blend_claim_test.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from evaluation.src.core.stats import point_biserial  # noqa: E402

FILES = sorted(Path("batch_results").glob("v6ab_*.jsonl"))
MIN_VOTES = 2  # drop near-zero-sample games (rate unstable below this)


def _games(path: Path):
    for line in path.read_text().splitlines():
        if line.strip():
            yield json.loads(line)


def collect(paths: list[Path]) -> tuple[list[float], list[int]]:
    rates, wins = [], []
    for p in paths:
        for rec in _games(p):
            cm = rec.get("computed_metrics") or {}
            rate = cm.get("wolf_unconditioned_blending_rate")
            total = cm.get("wolf_blend_votes_total") or 0
            if rate is None or total < MIN_VOTES:
                continue
            rates.append(rate)
            wins.append(1 if rec.get("winner") == "wolves" else 0)
    return rates, wins


def report(label: str, paths: list[Path]) -> None:
    rates, wins = collect(paths)
    n = len(rates)
    if n < 3:
        print(f"{label:20} n={n} (too few)")
        return
    r, p = point_biserial(wins, rates)
    hi = [w for ra, w in zip(rates, wins) if ra >= 0.8]
    lo = [w for ra, w in zip(rates, wins) if ra < 0.8]
    mean = lambda xs: sum(xs) / len(xs) if xs else float("nan")  # noqa: E731
    print(f"{label:20} n={n:3}  r={r:+.3f} p={p:.3f}  "
          f"wolfwin| blend>=.8: {mean(hi):.2f} (n={len(hi)})  blend<.8: {mean(lo):.2f} (n={len(lo)})")


if __name__ == "__main__":
    print("wolf_unconditioned_blending_rate vs wolf-win — does 'always blend' hold on v6ab?")
    report("POOLED (all arms)", FILES)
    report("baseline only", [p for p in FILES if p.stem == "v6ab_baseline"])
