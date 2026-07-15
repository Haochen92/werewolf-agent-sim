"""Metrics audit — follow-up rescue pass (2026-07-07), two pre-registered tests.

F1  Incremental validity of `town_accusation_precision` beyond `town_vote_accuracy`.
    The 2026-07-02 audit discovered the proxy (+0.340 vs town win) but flagged its coupling to the
    already-validated vote endpoint (Pearson r=+0.558, ~31% shared variance) and never asked the
    deciding question: does it carry win signal the vote endpoint doesn't? Partial r(precision,
    town_won | vote_accuracy). Pre-registered sign: +. If the partial survives (p<.05, sign-stable
    on both halves) the proxy earns its own construct seat instead of the diagnostic tier.

F2  `vigilante_correct_shot_rate` re-test at N=180. v5 left it directionally promising but
    underpowered (+0.30 pooled n=36 / +0.43 OFF n=21, defined only in shooter games); the 2026-07-02
    audit re-tested the vigilante pair (`wolf_kills_rate`, `friendly_fire_shots`) but not this rate.
    Point-biserial vs town win on the defined (shot-taken) subset. Pre-registered sign: +.
    Caveat carried with the result: conditioning on "the vigilante shot" is a behavioral selection —
    shooter games may differ systematically from hold-fire games.

Deterministic, ZERO LLM, recompute-only over the N=180 v6ab set (same loader + game_id-parity
split-half as the other Workstream-1 runners).

    poetry run python -m evaluation.src.instrument_validation.proxies.proxy_followup_rescue
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from evaluation.src.core.stats import partial_correlation, pearson, point_biserial
from evaluation.src.instrument_validation.proxies.accusation_metrics import game_metrics
from evaluation.src.instrument_validation.proxies.metrics_common import (
    REPO_ROOT,
    load_v6ab,
    split_half,
    won,
)

OUT = REPO_ROOT / "evidence/metrics/metrics_audit/data/proxy_followup_rescue.json"


def _rows() -> list[dict]:
    rows = []
    for rec in load_v6ab():
        cm = rec.get("computed_metrics") or {}
        rows.append(
            {
                "game_id": rec.get("game_id") or "",
                "town_won": won(rec, "villagers"),
                "accusation_precision": game_metrics(rec)["town_accusation_precision"],
                "vote_accuracy": cm.get("town_vote_accuracy"),
                "vigilante_correct_shot_rate": cm.get("vigilante_correct_shot_rate"),
            }
        )
    return rows


def _fmt(r: float, p: float, n: int) -> str:
    if r != r:
        return f"— (n={n})"
    return f"{r:+.3f} (p={p:.3f}, n={n})"


def _f1(rows: list[dict], half: int | None = None) -> dict:
    sub = [
        r
        for r in rows
        if (half is None or split_half(r["game_id"]) == half)
        and r["accusation_precision"] is not None
        and r["vote_accuracy"] is not None
    ]
    prec = [r["accusation_precision"] for r in sub]
    vote = [r["vote_accuracy"] for r in sub]
    win = [float(r["town_won"]) for r in sub]
    raw_r, raw_p = point_biserial([int(w) for w in win], prec)
    couple_r, couple_p = pearson(prec, vote)
    part_r, part_p, part_n = partial_correlation(prec, win, [vote])
    return {
        "n": len(sub),
        "raw": {"r": raw_r, "p": raw_p},
        "coupling_with_vote_accuracy": {"r": couple_r, "p": couple_p},
        "partial_given_vote_accuracy": {"r": part_r, "p": part_p, "n": part_n},
    }


def _f2(rows: list[dict], half: int | None = None) -> dict:
    sub = [
        r
        for r in rows
        if (half is None or split_half(r["game_id"]) == half)
        and r["vigilante_correct_shot_rate"] is not None
    ]
    r, p = point_biserial(
        [r_["town_won"] for r_ in sub], [r_["vigilante_correct_shot_rate"] for r_ in sub]
    )
    return {"n": len(sub), "r": r, "p": p}


def main() -> None:
    rows = _rows()
    result = {
        "n_games": len(rows),
        "F1_accusation_precision_beyond_vote": {
            "full": _f1(rows),
            "discover_half": _f1(rows, 0),
            "confirm_half": _f1(rows, 1),
        },
        "F2_vigilante_correct_shot_rate": {
            "full": _f2(rows),
            "discover_half": _f2(rows, 0),
            "confirm_half": _f2(rows, 1),
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2))

    f1, f2 = result["F1_accusation_precision_beyond_vote"], result["F2_vigilante_correct_shot_rate"]
    print(f"N={result['n_games']} v6ab games -> {OUT.relative_to(REPO_ROOT)}\n")
    print("F1 town_accusation_precision vs town win (pre-registered +):")
    full = f1["full"]
    print(f"  raw            {_fmt(full['raw']['r'], full['raw']['p'], full['n'])}")
    print(
        "  coupling       "
        f"{_fmt(full['coupling_with_vote_accuracy']['r'], full['coupling_with_vote_accuracy']['p'], full['n'])}"
        "  (Pearson vs town_vote_accuracy)"
    )
    pg = full["partial_given_vote_accuracy"]
    print(f"  partial|vote   {_fmt(pg['r'], pg['p'], pg['n'])}")
    for name, half in (("discover", "discover_half"), ("confirm ", "confirm_half")):
        pg = f1[half]["partial_given_vote_accuracy"]
        print(f"    {name} half  {_fmt(pg['r'], pg['p'], pg['n'])}")
    print("\nF2 vigilante_correct_shot_rate vs town win, shooter games only (pre-registered +):")
    print(f"  full           {_fmt(f2['full']['r'], f2['full']['p'], f2['full']['n'])}")
    for name, half in (("discover", "discover_half"), ("confirm ", "confirm_half")):
        h = f2[half]
        print(f"    {name} half  {_fmt(h['r'], h['p'], h['n'])}")


if __name__ == "__main__":
    main()
