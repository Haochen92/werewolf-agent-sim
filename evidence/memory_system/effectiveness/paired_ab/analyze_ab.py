"""Paired memory A/B analysis — full: off / raw / reranked / all-on + called-shot scoring.

Reuses evaluation/src/core/stats.py (binomial_ci, mcnemar_exact, wilcoxon_paired).

All baseline games are run FRESH in the SAME epoch as the arms (the original baseline
was a different model epoch — Fisher p=0.0028 — so it is NOT used). Every game (baseline
and arm) carries game_id + winner + computed_metrics, and every arm uses the same 30
game_ids, so EVERY comparison pairs on game_id (identical role draw, verified).

Conditions: raw arms (rerank off), reranked arms (--reranking observations), raw all-on.
Win rate is reported but underpowered; the powered signal is the monotonicity-validated
proxy basket (chosen independently, before any A/B result). The reranked/all-on arms are
scored against the PRE-REGISTERED called shots (see experiment_log.md) — confirmatory if a
called shot hits, otherwise exploratory.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from evaluation.src.core.stats import binomial_ci, mcnemar_exact, wilcoxon_paired  # noqa: E402

HERE = Path(__file__).resolve().parent
BR = REPO / "batch_results"

BASELINE_FILES = [BR / "ab_baseline.jsonl", BR / "ab_baseline_recovered.jsonl"]
FACTION = {"wolf_only": "wolves", "serial_killer_only": "serial_killer", "town_only": "villagers"}
RAW = {"wolf_only": BR / "ab_arms_wolf.jsonl", "serial_killer_only": BR / "ab_arms_sk.jsonl",
       "town_only": BR / "ab_arms_town.jsonl"}
RERANK = {"wolf_only": BR / "ab_rr_wolf.jsonl", "serial_killer_only": BR / "ab_rr_sk.jsonl",
          "town_only": BR / "ab_rr_town.jsonl"}
ALLON = BR / "ab_allon.jsonl"

VALIDATED = [("town_vote_accuracy", "+"), ("town_mislynch_rate", "-"), ("mislynches", "-"),
             ("correct_elimination_rate", "+"), ("serial_killer_lynched", "+"),
             ("sk_nights_survived", "+"), ("healer_town_save_rate", "+"),
             ("vigilante_friendly_fire_shots", "-")]


def load(path):
    if not Path(path).exists():
        return []
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def by_gid(records):
    return {r["game_id"]: r for r in records if r.get("game_id")}


def metric(rec, k):
    return (rec.get("computed_metrics") or {}).get(k)


def arm_vs_baseline(label, faction, arm_recs, baseline, lines):
    """Paired off(baseline) vs on(arm) by game_id: McNemar win + validated-proxy Wilcoxon."""
    arm = [r for r in arm_recs if r.get("game_id") in baseline]
    if not arm:
        lines.append(f"### {label}: no matched games yet\n"); return
    off = [int(baseline[r["game_id"]].get("winner") == faction) for r in arm]
    on = [int(r.get("winner") == faction) for r in arm]
    n = len(on)
    mc = mcnemar_exact(off, on)
    oc, nc = binomial_ci(sum(off), n), binomial_ci(sum(on), n)
    lines.append(f"### {label} (faction={faction}), N={n}")
    lines.append(f"- win: off {sum(off)/n:.0%}[{oc[0]:.0%},{oc[1]:.0%}] -> on {sum(on)/n:.0%}"
                 f"[{nc[0]:.0%},{nc[1]:.0%}] (Δ{(sum(on)-sum(off))/n:+.0%}, McNemar p={mc.p_value:.3f})")
    for p, sign in VALIDATED:
        ov, nv = [], []
        for r in arm:
            a = metric(baseline[r["game_id"]], p); b = metric(r, p)
            if a is not None and b is not None:
                ov.append(a); nv.append(b)
        if len(nv) < 3:
            continue
        _, wp = wilcoxon_paired(ov, nv)
        star = " *" if wp < 0.05 else ""
        lines.append(f"  - {p} ({sign}): {sum(ov)/len(ov):.3f} -> {sum(nv)/len(nv):.3f} "
                     f"(Δ{(sum(nv)-sum(ov))/len(nv):+.3f}, p={wp:.3f}){star}")
    lines.append("")


def called_shot_rerank(label, raw_recs, rr_recs, proxies, predict, lines):
    """Paired raw-arm vs reranked-arm on the same game_ids: did reranking shift the proxy?"""
    raw_g, rr_g = by_gid(raw_recs), by_gid(rr_recs)
    common = sorted(set(raw_g) & set(rr_g))
    lines.append(f"### {label} — paired raw vs reranked, N={len(common)} (predict: {predict})")
    if len(common) < 3:
        lines.append("  (insufficient matched games)\n"); return
    for p in proxies:
        rv, kv = [], []
        for g in common:
            a = metric(raw_g[g], p); b = metric(rr_g[g], p)
            if a is not None and b is not None:
                rv.append(a); kv.append(b)
        if len(kv) < 3:
            continue
        _, wp = wilcoxon_paired(rv, kv)
        d = (sum(kv) - sum(rv)) / len(kv)
        lines.append(f"  - {p}: raw {sum(rv)/len(rv):.3f} -> rerank {sum(kv)/len(kv):.3f} "
                     f"(Δ{d:+.3f}, Wilcoxon p={wp:.3f})")
    lines.append("")


def main():
    baseline = by_gid([r for f in BASELINE_FILES for r in load(f)])
    L = ["# Paired memory A/B — FULL report", "",
         f"Same-epoch baseline: {len(baseline)} games. * = Wilcoxon p<0.05 (uncorrected; "
         f"Bonferroni over the ≤3 pre-registered primaries = 0.017).", ""]

    L.append("## RAW arms (rerank off) — off vs on")
    for cfg, fac in FACTION.items():
        arm_vs_baseline(f"raw {cfg}", fac, load(RAW[cfg]), baseline, L)

    L.append("## RERANKED arms (observations reranking) — off vs on")
    for cfg, fac in FACTION.items():
        arm_vs_baseline(f"rerank {cfg}", fac, load(RERANK[cfg]), baseline, L)

    L.append("## ALL-ON arm (all roles, raw) — off vs on")
    arm_vs_baseline("all_enabled", "villagers", load(ALLON), baseline, L)

    L.append("## PRE-REGISTERED CALLED SHOTS")
    called_shot_rerank("rerank-town", load(RAW["town_only"]), load(RERANK["town_only"]),
                       ["town_vote_accuracy"], "town_vote_accuracy UP vs raw", L)
    called_shot_rerank("rerank-wolf", load(RAW["wolf_only"]), load(RERANK["wolf_only"]),
                       ["town_vote_accuracy", "mislynches"], "town detection DOWN vs raw", L)
    L.append("### all-on — predict NO town collapse vs baseline (contra pilot)")
    L.append("  (see ALL-ON arm above: villager win + town_vote_accuracy vs baseline)\n")

    out = HERE / "report.md"
    out.write_text("\n".join(L))
    print("\n".join(L))
    print(f"\nWritten to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
