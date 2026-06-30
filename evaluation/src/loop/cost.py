"""Compounding loop — COST CAPTURE: realized USD per run from Langfuse (post-hoc, best-effort).

Sums Langfuse ``trace.total_cost`` (its realized token accounting — the SAME source as the manual $65
reconciliation) two ways: a COMPLETE window total (every trace between run start and now → games +
in-driver dedup/synth/tagger) and a per-generation GAME breakdown by session_id. Read-only + fail-soft:
a Langfuse hiccup yields a null number, never a crashed run. There is NO auto-abort — this surfaces the
spend; a human watches and intervenes. Poll mid-run anytime:

    poetry run python -m evaluation.src.loop.cost --run-dir <dir>

The driver also calls it at run end → ``cost_report.json``. The window total can undercount the final
minutes (Langfuse ingestion lag); re-run this a few minutes after the run for the settled total.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def _gen_of(fname: str) -> int | None:
    m = re.search(r"gen(\d+)_(on|off)\.jsonl$", fname)
    return int(m.group(1)) if m else None


def run_cost(run_dir: str | Path) -> dict:
    """Realized cost report for a loop run dir. Returns per-gen GAME cost (by session), the games total,
    the COMPLETE window total (run_meta start → now), and the overhead = complete − games (the in-driver
    dedup/synth/tagger). Any field is None when Langfuse couldn't answer (best-effort)."""
    from evaluation.src.data.sources.langfuse import (
        read_session_ids_from_batch_results, session_cost, window_cost,
    )

    run_dir = Path(run_dir)
    per_gen: dict[int, dict] = {}
    for f in sorted(glob.glob(str(run_dir / "gen*_on.jsonl")) + glob.glob(str(run_dir / "gen*_off.jsonl"))):
        gen, arm = _gen_of(f), ("on" if f.endswith("_on.jsonl") else "off")
        if gen is None:
            continue
        usd = 0.0
        for sid in read_session_ids_from_batch_results(Path(f)):
            c, _ = session_cost(sid)
            if c is not None:
                usd += c
        g = per_gen.setdefault(gen, {"on": 0.0, "off": 0.0})
        g[arm] = round(g[arm] + usd, 4)
    games_total = round(sum(g["on"] + g["off"] for g in per_gen.values()), 2) if per_gen else None

    grand = None
    meta_path = run_dir / "run_meta.json"
    if meta_path.exists():
        started = json.loads(meta_path.read_text()).get("run_started_at")
        if started:
            grand_raw, _ = window_cost(datetime.fromisoformat(started), datetime.now(timezone.utc))
            grand = round(grand_raw, 2) if grand_raw is not None else None

    overhead = round(grand - games_total, 2) if (grand is not None and games_total is not None) else None
    return {"per_gen_games_usd": dict(sorted(per_gen.items())),
            "games_total_usd": games_total, "grand_total_usd": grand, "overhead_usd": overhead}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--out", default=None, help="report path (default: <run-dir>/cost_report.json)")
    args = ap.parse_args()
    rep = run_cost(args.run_dir)
    out = Path(args.out) if args.out else Path(args.run_dir) / "cost_report.json"
    out.write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))
    print(f"\n-> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
