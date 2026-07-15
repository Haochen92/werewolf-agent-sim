"""v7 — windowed (delayed) credit test (zero spend). Does crediting a decision over a FUTURE window
carry signal the immediate de-luck proxy misses, or does it just drift into the outcome halo?

The clean⊥delayed⊥free triangle, made empirical. For each FOLLOWED SP we compute per-SP lift under
four credit definitions and cross-correlate them:
  - immediate : the de-luck proxy of that decision (k=0, current — CLEAN, myopic)
  - surv@1 / surv@2 : did the acting player AVOID elimination in the next 1 / 2 days (delayed,
                      deterministic, but luckier — the "blend today -> caught tomorrow" signal)
  - terminal : did the player's faction win the game (k=inf = the full HALO)
Each signal is baselined against its memory-OFF per-cell mean (lift), shrunk by follow count.

Reading: if immediate barely correlates with terminal -> immediate isn't halo (good). If surv@k
correlates with terminal MORE as k grows -> the window is the myopia->halo dial. If surv@k diverges
from immediate while NOT being pure terminal -> delay carries extra clean signal (the hypothesis).
If surv@k just tracks terminal -> the only free delayed signal is halo -> delayed credit needs the
(paid) LLM or stays out.

  poetry run python -m evaluation.src.instrument_validation.credit.windowed_credit
"""

import glob
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from evaluation.src.loop.credit_backfill import VERDICT_VALUE, _decision_credit  # noqa: E402

DUMPS = "batch_results/*v6ab*.jsonl"
SHRINK_K = 5
MIN_FOLLOW = 5

ROLE_FACTION = {"villager": "town", "healer": "town", "investigator": "town", "vigilante": "town",
                "wolf": "wolves", "serial_killer": "serial_killer"}


def _norm_winner(w: str | None) -> str | None:
    if not w:
        return None
    w = w.lower()
    if "wolf" in w or "wolves" in w:
        return "wolves"
    if "serial" in w or w == "sk":
        return "serial_killer"
    if "town" in w or "villag" in w:
        return "town"
    return w


def _elim_day(game: dict) -> dict[str, int]:
    elim: dict[str, int] = {}
    for dr in game.get("day_resolutions", []):
        vp = dr.get("voted_player")
        if vp:
            elim.setdefault(vp, dr.get("day", 0))
    for nr in game.get("night_resolutions", []):
        for d in nr.get("deaths", []):
            pid = d if isinstance(d, str) else (d.get("player") or d.get("player_id") or d.get("target"))
            if pid:
                elim.setdefault(pid, nr.get("day", 0))
    return elim


def _signals(case: dict, game: dict, elim: dict, winner: str | None) -> tuple[float, float, float]:
    """(surv@1, surv@2, terminal) for the acting player, each in {-1,+1}."""
    pid, n = case["player_id"], case["day"]
    fac = ROLE_FACTION.get(game["roles"].get(pid, ""))
    won = 1.0 if (fac is not None and fac == winner) else -1.0
    ed = elim.get(pid)

    def surv(k: int) -> float:
        return -1.0 if (ed is not None and n < ed <= n + k) else 1.0

    return surv(1), surv(2), won


def _iter(dumps_glob: str):
    for dump in sorted(glob.glob(dumps_glob)):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not os.path.exists(path):
                continue
            elim, winner = _elim_day(g), _norm_winner(g.get("winner"))
            for cl in open(path):
                if not cl.strip():
                    continue
                env = json.loads(cl)
                if env.get("kind") != "agent_action_eval":
                    continue
                ec = (env.get("output") or {}).get("eval_case")
                if ec:
                    yield g, elim, winner, ec


def _values(ec: dict, g: dict, elim: dict, winner: str | None):
    """The four raw credit values for this decision, or None if not creditable."""
    verdict = _decision_credit(ec, g["roles"])
    if verdict not in VERDICT_VALUE:  # None, or the v1 read-partition's "read_excluded" sentinel
        return None
    s1, s2, term = _signals(ec, g, elim, winner)
    return {"imm": VERDICT_VALUE[verdict], "surv1": s1, "surv2": s2, "terminal": term}


def _pearson(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    mx, my = sum(xs) / n, sum(ys) / n
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    vx = sum((x - mx) ** 2 for x in xs) ** 0.5
    vy = sum((y - my) ** 2 for y in ys) ** 0.5
    return cov / (vx * vy) if vx and vy else float("nan")


SIGNALS = ("imm", "surv1", "surv2", "terminal")


def main() -> int:
    # pass 1: memory-OFF per-cell baselines for each signal
    base_sum = {s: defaultdict(float) for s in SIGNALS}
    base_n = defaultdict(int)
    for g, elim, winner, ec in _iter(DUMPS):
        if ec.get("memory_enabled"):
            continue
        vals = _values(ec, g, elim, winner)
        if vals is None:
            continue
        cell = f"{ec['player_role']}/{ec['action_phase']}"
        base_n[cell] += 1
        for s in SIGNALS:
            base_sum[s][cell] += vals[s]
    base = {s: {c: base_sum[s][c] / base_n[c] for c in base_n} for s in SIGNALS}

    # pass 2: per-SP baselined sums over followed (memory-on) decisions
    led = defaultdict(lambda: {"follow": 0, **{s: 0.0 for s in SIGNALS}})
    for g, elim, winner, ec in _iter(DUMPS):
        if not (ec.get("memory_enabled") and ec.get("strategy_verdicts")):
            continue
        vals = _values(ec, g, elim, winner)
        if vals is None:
            continue
        cell = f"{ec['player_role']}/{ec['action_phase']}"
        idx = ec.get("strategy_index_to_key") or {}
        for sv in ec["strategy_verdicts"]:
            if sv.get("verdict") != "follow":
                continue
            key = idx.get(str(sv.get("strategy_index")))
            if not key:
                continue
            led[key]["follow"] += 1
            for s in SIGNALS:
                led[key][s] += vals[s] - base[s].get(cell, 0.0)

    def shrunk(rec, s):
        f = rec["follow"]
        return (rec[s] / f) * f / (f + SHRINK_K) if f else 0.0

    deep = [r for r in led.values() if r["follow"] >= MIN_FOLLOW]
    print(f"SPs with >= {MIN_FOLLOW} follows: {len(deep)} (of {len(led)} credited)\n")
    lifts = {s: [shrunk(r, s) for r in deep] for s in SIGNALS}

    print("=== per-SP lift CORRELATION MATRIX (Pearson) ===")
    print(f"{'':9}" + "".join(f"{s:>10}" for s in SIGNALS))
    for a in SIGNALS:
        print(f"{a:9}" + "".join(f"{_pearson(lifts[a], lifts[b]):>+10.2f}" for b in SIGNALS))

    print("\nreading:")
    print(f"  imm vs terminal     = {_pearson(lifts['imm'], lifts['terminal']):+.2f}  "
          "(low => immediate is NOT just halo)")
    print(f"  surv1 vs terminal   = {_pearson(lifts['surv1'], lifts['terminal']):+.2f}")
    print(f"  surv2 vs terminal   = {_pearson(lifts['surv2'], lifts['terminal']):+.2f}  "
          "(rising toward 1 with window => the myopia->halo dial)")
    print(f"  imm vs surv1        = {_pearson(lifts['imm'], lifts['surv1']):+.2f}  "
          "(if low AND surv tracks terminal => delayed signal is mostly halo, not clean)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
