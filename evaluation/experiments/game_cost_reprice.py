"""What a recorded game would have cost on a model that did not play it: its tokens at other rates.

A game's manifest (the batch runner's `*.manifest.json`) stores every model call's tokens in hourly
buckets: input, the part of input read from the provider's cache, the part written to it, output
(reasoning included). The game's own bill is those counts at its model's dated rates
(``server/game/usage.py``). This runner adds up the buckets of one or more games and prices the
total, or the per-game mean, at a list of other models' rates, as if each model had read and written
exactly the same tokens. That is an illustration of the step between model classes, not a measured
game: a different model writes a different amount, may not turn its reasoning off, and tokenises
differently. Read it as "the same tokens at other prices".

    poetry run python -m evaluation.experiments.game_cost_reprice \
        evidence/gameplay/data/persona_voice_games/voices-*.manifest.json \
        --rates evaluation/config/reprice_rates_2026_10_30.json

A game without a manifest (a traced game read with game_cache_share.py) can be given as one row:

    poetry run python -m evaluation.experiments.game_cost_reprice \
        --tokens 1754420 870186 0 232000 --rates evaluation/config/reprice_rates_2026_10_30.json

Record: evidence/caching/experiment_log.md (2026-10-30, per-game cost and the repricing).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

TOKEN_KEYS = ("calls", "input", "cached", "written", "output", "reasoning")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifests", nargs="*", help="batch-run game manifests (*.manifest.json)")
    ap.add_argument("--tokens", nargs=4, type=int, metavar=("INPUT", "CACHED", "WRITTEN", "OUTPUT"),
                    help="one game's tokens given by hand instead of manifests")
    ap.add_argument("--rates", required=True, help="the rate table (evaluation/config/reprice_rates_*.json)")
    args = ap.parse_args()

    if args.tokens:
        games = [dict(zip(("input", "cached", "written", "output"), args.tokens), calls=0, reasoning=0, label="given")]
    else:
        games = [game_tokens(Path(p)) for p in args.manifests]
    if not games:
        ap.error("give manifests or --tokens")

    print_games(games)
    mean = {k: sum(g[k] for g in games) / len(games) for k in TOKEN_KEYS}
    rates = json.loads(Path(args.rates).read_text())["models"]
    print(f"\nMean of {len(games)} game(s) repriced (rates read {json.loads(Path(args.rates).read_text())['read_on']}):")
    print(f"{'model':32s} {'cost':>8s} {'no cache hits':>14s}")
    for r in rates:
        print(f"{r['label']:32s} ${reprice(mean, r):7.2f} ${reprice({**mean, 'cached': 0, 'written': 0}, r):13.2f}")
    return 0


def game_tokens(manifest: Path) -> dict:
    """One game's tokens summed over its hourly buckets, with its label, call count and recorded cost."""
    m = json.loads(manifest.read_text())
    buckets = m["usage"]["buckets"]
    out = {k: sum(int(b.get(k, 0)) for b in buckets) for k in TOKEN_KEYS}
    return {**out, "label": m.get("label", manifest.stem), "days": m.get("days"), "cost_usd": m.get("cost_usd")}


def reprice(tokens: dict, rate: dict) -> float:
    """The tokens at ``rate`` (per million): plain input, cached input, written input at the write
    premium, and output."""
    plain = tokens["input"] - tokens["cached"] - tokens["written"]
    return (plain * rate["input"] + tokens["cached"] * rate["cached"]
            + tokens["written"] * rate["input"] * rate.get("write_factor", 1.0)
            + tokens["output"] * rate["output"]) / 1e6


def print_games(games: list[dict]) -> None:
    print(f"{'game':16s} {'days':>4s} {'calls':>5s} {'input':>10s} {'cached':>7s} {'output':>8s} {'reason.':>8s} {'recorded':>9s}")
    for g in games:
        share = f"{g['cached'] / g['input']:.0%}" if g["input"] else "-"
        cost = f"${g['cost_usd']:.4f}" if g.get("cost_usd") is not None else "-"
        print(f"{g['label']:16s} {str(g.get('days') or ''):>4s} {g['calls']:5d} {g['input']:10,d} {share:>7s} "
              f"{g['output']:8,d} {g['reasoning']:8,d} {cost:>9s}")


if __name__ == "__main__":
    raise SystemExit(main())
