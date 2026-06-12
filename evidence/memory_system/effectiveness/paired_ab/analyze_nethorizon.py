"""Score the net-horizon arms against the PRE-REGISTERED predictions (see experiment_log.md
"PRE-REGISTRATION — nethorizon arms"). Each arm is compared BOTH to the same-epoch baseline (off)
and — the decisive contrast — to the v5_0 RAW-memory arm (same seeds/retrieval → isolates framing).

Unconditioned blending is RE-DERIVED from raw day_resolutions for every arm (the v5_0-raw arm and
baseline predate that metric in compute_metrics, so reading computed_metrics would be apples-to-
oranges). All comparisons pair on game_id (identical role draw)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
from evaluation.src.core.stats import binomial_ci, mcnemar_exact, wilcoxon_paired  # noqa: E402

BR = REPO / "batch_results"
HERE = Path(__file__).resolve().parent


def load(*names):
    out = []
    for n in names:
        p = BR / n
        if p.exists():
            out += [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
    return out


def by_gid(recs):
    return {r["game_id"]: r for r in recs if r.get("game_id") and r.get("status", "success") == "success"}


def cm(rec, k):
    return (rec.get("computed_metrics") or {}).get(k)


def _roles_of(rec, role):
    return {p for p, r in (rec.get("roles") or {}).items() if r == role}


def unconditioned_blend(rec):
    """Fraction of a living wolf's votes aligned with the day's lynch, ALL lynch days (re-derived)."""
    wolves = _roles_of(rec, "wolf")
    aligned = total = 0
    for day in rec.get("day_resolutions", []):
        t = day.get("voted_player")
        if t is None:
            continue
        for v in day.get("votes", []):
            if v["voter"] in wolves and v["voter"] != t:
                total += 1
                aligned += v["votee"] == t
    return aligned / total if total else None


def sk_lynched(rec):
    """1 if the serial killer was voted out on any day, else 0 (the SK harm signature)."""
    sk = _roles_of(rec, "serial_killer")
    if not sk:
        return None
    sk_id = next(iter(sk))
    return int(any(d.get("voted_player") == sk_id for d in rec.get("day_resolutions", [])))


def paired(label, treat_recs, ref_recs, faction, proxies, lines):
    """treat (on) vs ref (off/raw) by game_id: McNemar win + paired-Wilcoxon proxies."""
    treat, ref = by_gid(treat_recs), by_gid(ref_recs)
    common = sorted(set(treat) & set(ref))
    lines.append(f"### {label}  (faction={faction}, N={len(common)})")
    if len(common) < 3:
        lines.append("  (insufficient matched games yet)\n"); return
    off = [int(ref[g].get("winner") == faction) for g in common]
    on = [int(treat[g].get("winner") == faction) for g in common]
    mc = mcnemar_exact(off, on)
    oc, nc = binomial_ci(sum(off), len(on)), binomial_ci(sum(on), len(on))
    lines.append(f"- win: ref {sum(off)/len(on):.0%}[{oc[0]:.0%},{oc[1]:.0%}] -> "
                 f"nethorizon {sum(on)/len(on):.0%}[{nc[0]:.0%},{nc[1]:.0%}] "
                 f"(Δ{(sum(on)-sum(off))/len(on):+.0%}, McNemar p={mc.p_value:.3f})")
    for name, sign, fn in proxies:
        ov, nv = [], []
        for g in common:
            a, b = fn(ref[g]), fn(treat[g])
            if a is not None and b is not None:
                ov.append(a); nv.append(b)
        if len(nv) < 3:
            lines.append(f"  - {name} ({sign}): <3 paired values"); continue
        _, wp = wilcoxon_paired(ov, nv)
        star = " *" if wp < 0.05 else ""
        lines.append(f"  - {name} ({sign}): ref {sum(ov)/len(ov):.3f} -> nh {sum(nv)/len(nv):.3f} "
                     f"(Δ{(sum(nv)-sum(ov))/len(nv):+.3f}, p={wp:.3f}){star}")
    lines.append("")


def main():
    baseline = load("ab_baseline.jsonl", "ab_baseline_recovered.jsonl")
    raw_wolf, nh_wolf = load("ab_arms_wolf.jsonl"), load("ab_nh_wolf.jsonl")
    raw_sk, nh_sk = load("ab_arms_sk.jsonl"), load("ab_nh_sk.jsonl")

    WOLF = [("unconditioned_blending", "+", unconditioned_blend),
            ("wolf_elimination_rate", "-", lambda r: cm(r, "wolf_elimination_rate")),
            ("wolf_power_role_targeting_rate", "+", lambda r: cm(r, "wolf_power_role_targeting_rate"))]
    SK = [("sk_lynched", "-", sk_lynched),
          ("sk_nights_survived", "+", lambda r: cm(r, "sk_nights_survived"))]

    L = ["# Net-horizon arms — scored vs pre-registration", "",
         "* = Wilcoxon p<0.05 (uncorrected). PRIMARY wolf proxy = unconditioned_blending; the decisive",
         "contrast is nethorizon vs the v5_0 RAW arm (same retrieval → isolates framing).", "",
         "## WOLF"]
    paired("nh_wolf vs v5_0-RAW wolf  (DECISIVE — framing vs no-fix)", nh_wolf, raw_wolf, "wolves", WOLF, L)
    paired("nh_wolf vs same-epoch baseline (off)", nh_wolf, baseline, "wolves", WOLF, L)
    L.append("## SERIAL KILLER")
    paired("nh_sk vs v5_0-RAW sk  (DECISIVE)", nh_sk, raw_sk, "serial_killer", SK, L)
    paired("nh_sk vs same-epoch baseline (off)", nh_sk, baseline, "serial_killer", SK, L)

    out = HERE / "report_nethorizon.md"
    out.write_text("\n".join(L))
    print("\n".join(L))
    print(f"\nWritten to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
