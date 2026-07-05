"""Diagnostic ladder step 1 + 4 (experiment_log.md "Interpreting the wolf/SK null"):
wolf/SK proxy revalidation on the full paired-A/B corpus (N=240) + SK harm-channel check.

Promoted from /tmp 2026-06-12 after the first run; read-only over batch_results/ab_*.jsonl.
Method follows evidence/metrics/proxy_win_monotonicity.py (point-biserial vs own-faction win),
reported pooled AND baseline-only to bound treatment confounds.

Findings on first run (2026-06-12):
- wolf_power_role_targeting_rate VALIDATES (+0.18 p=0.006 pooled n=240; +0.35 p=0.060
  baseline-only, same sign) — first validated wolf proxy.
- wolf_blending/dissent_rate ~0 at n=100 (no longer degenerate, just null — but see
  diagnose_wolf_blending.py: the conditioned definition is the artifact).
- wolf_killed_healer/investigator_day WRONG SIGN — kill-timing metrics are length-confounded
  (same trap as investigator_found_wolf_day). Excluded from any basket.
- sk_nights_survived re-validates strongly (+0.48 p<0.001 n=240).
- SK harm channel: night survival UNCHANGED (3.43 off vs 3.32 on) but exit_method shifts
  lynched 63%->78% (Fisher p=0.070) — the harm is day-social, not night-targeting.
- Wolf night skill rises with memory (power_targeting 0.459 -> 0.544 raw / 0.511 rr; town-arm
  negative control 0.448) while detectability rises too (wolf_elim_rate 0.227 -> 0.292 / 0.340).

    poetry run python -m evaluation.src.instrument_validation.proxies.diagnose_wolf_sk_proxies
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))
from evaluation.src.core.stats import point_biserial  # noqa: E402

FILES = [
    "ab_baseline", "ab_baseline_recovered",
    "ab_arms_wolf", "ab_arms_town", "ab_arms_sk",
    "ab_rr_wolf", "ab_rr_town", "ab_rr_sk",
    "ab_allon",
]

PROXIES = {
    "wolf_blending_rate": ("wolves", "+"),
    "wolf_dissent_rate": ("wolves", "-"),
    "wolf_steering_rate": ("wolves", "+"),
    "wolf_power_role_targeting_rate": ("wolves", "+"),
    "wolf_killed_healer_day": ("wolves", "-"),
    "wolf_killed_investigator_day": ("wolves", "-"),
    "sk_nights_survived": ("serial_killer", "+"),
    "sk_kills_landed": ("serial_killer", None),
}


def load(name: str) -> list[dict]:
    path = REPO_ROOT / "batch_results" / f"{name}.jsonl"
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("status") == "success":
            r["_arm"] = name
            out.append(r)
    return out


def correlate(records, proxy, faction):
    wins, values = [], []
    for r in records:
        v = r["computed_metrics"].get(proxy)
        if isinstance(v, bool):
            v = int(v)
        if not isinstance(v, (int, float)):
            continue
        wins.append(int(r["winner"] == faction))
        values.append(float(v))
    if len(set(wins)) < 2 or len(set(values)) < 2:
        return float("nan"), float("nan"), len(values)
    r_, p = point_biserial(wins, values)
    return r_, p, len(values)


def fmt(r, p, n):
    if r != r:
        return f"— (n={n})"
    return f"{r:+.2f} (p={p:.3f}, n={n})"


def verdict(expected, r, p):
    if expected is None:
        return "context"
    if r != r:
        return "degenerate"
    if ("+" if r > 0 else "-") != expected:
        return "WRONG SIGN" + (" (sig.)" if p < 0.05 else "")
    return "ok (SIG.)" if p < 0.05 else "ok (weak)"


def main() -> None:
    arms = {name: load(name) for name in FILES}
    for name, recs in arms.items():
        w = Counter(r["winner"] for r in recs)
        print(f"{name:25s} n={len(recs):3d}  winners={dict(w)}")

    # Arms SHARE game_ids with baseline (the pairing key!) — dedupe by (arm, game_id),
    # treating the two baseline files as one arm.
    ids: set = set()
    pooled: list[dict] = []
    for recs in arms.values():
        for r in recs:
            arm_key = "baseline" if r["_arm"].startswith("ab_baseline") else r["_arm"]
            gid = (arm_key, r.get("game_id") or id(r))
            if gid in ids:
                continue
            ids.add(gid)
            pooled.append(r)
    off = [r for r in pooled if r["_arm"].startswith("ab_baseline")]
    print(f"\npooled unique n={len(pooled)}, baseline n={len(off)}")

    print("\n| proxy | expected | pooled | baseline-only | verdict (pooled) |")
    print("|---|---|---|---|---|")
    for proxy, (faction, expected) in PROXIES.items():
        rp, pp, np_ = correlate(pooled, proxy, faction)
        ro, po, no = correlate(off, proxy, faction)
        print(f"| `{proxy}` | {expected or '·'} | {fmt(rp, pp, np_)} | {fmt(ro, po, no)} "
              f"| {verdict(expected, rp, pp)} |")

    # --- Step 4: SK harm channel. Pools chosen to dodge the town-skill confound on lynchings
    # (town-memory arms lynch the SK more because town hunts better, not because SK leaks).
    print("\n=== SK harm channel: SK-mem-on (arms_sk+rr_sk) vs no-SK-no-town-mem "
          "(baseline+arms_wolf+rr_wolf) ===")
    sk_on = arms["ab_arms_sk"] + arms["ab_rr_sk"]
    sk_off = off + arms["ab_arms_wolf"] + arms["ab_rr_wolf"]
    rows = []
    for label, recs in [("SK-mem-OFF", sk_off), ("SK-mem-ON", sk_on)]:
        ex = Counter(r["computed_metrics"].get("sk_exit_method") for r in recs)
        surv = [r["computed_metrics"]["sk_nights_survived"] for r in recs]
        wins = sum(r["winner"] == "serial_killer" for r in recs)
        rows.append((ex["lynched"], len(recs) - ex["lynched"]))
        print(f"{label:11s} n={len(recs):3d} sk_win={wins}/{len(recs)} "
              f"lynched={ex['lynched']} ({ex['lynched']/len(recs):.0%}) exits={dict(ex)} "
              f"nights_survived={sum(surv)/len(surv):.2f}")
    from scipy.stats import fisher_exact
    print("Fisher (lynched, on vs off):", fisher_exact(rows))

    # --- Wolf two-edged sword: validated night skill vs detectability, per arm ---
    print("\n=== Wolf per-arm: power_targeting (validated, night skill) vs wolf_elim_rate "
          "(detectability) ===")
    groups = {"baseline": off}
    for n in ["ab_arms_wolf", "ab_rr_wolf", "ab_arms_town", "ab_allon"]:
        groups[n] = arms[n]
    for name, recs in groups.items():
        pt = [r["computed_metrics"].get("wolf_power_role_targeting_rate") for r in recs]
        pt = [v for v in pt if isinstance(v, (int, float))]
        we = [r["computed_metrics"].get("wolf_elimination_rate") for r in recs]
        we = [v for v in we if isinstance(v, (int, float))]
        ww = sum(r["winner"] == "wolves" for r in recs)
        print(f"{name:14s} power_targeting={sum(pt)/len(pt):.3f}  "
              f"wolf_elim_rate={sum(we)/len(we):.3f}  wolf_wins={ww}/{len(recs)}")


if __name__ == "__main__":
    main()
