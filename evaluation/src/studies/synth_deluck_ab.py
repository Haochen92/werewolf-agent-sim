"""v7 synthesis A/B — does CREDIT-AWARE (de-luck) synthesis beat halo-synthesis AND pure prune?

Three arms per deceiver cell, READ side-by-side (semantic eval → read, not a parser):
  H  halo-synthesis      — current CELL_SP_SYNTHESIS_PROMPT (weights by per-obs net_verdict = halo)
  D  credit-synthesis    — CREDIT_SYNTH_PROMPT, weights by the REALIZED de-luck track record, asked for
                           a CONDITIONED directive integrating the credit gradient
  S  pure-prune survivor — just the highest-lift credited SP for the cell (no synthesis at all)

If D ≈ S, synthesis-beyond-prune adds nothing (answer: just prune (b)). D only wins if it produces a
better-CONDITIONED rule than S. Synthesis model = pro-2.5 (justified: low-frequency + binding lever).

  poetry run python evaluation/src/studies/synth_deluck_ab.py
"""

from __future__ import annotations

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from Agents.memory.batch_deduplication.config import BatchDedupRunConfig
from Agents.memory.persistence import memory_store_paths, seed_memory_from_json_files_cached
from Agents.memory.store import store
from Agents.memory.strategy_synthesis import cluster_observations_for_synth, synthesize_cluster_sps

OBS_DIR = "memory_stores/v6_1"
LEDGER = "evidence/v7_final/credit_backfill_ledger.json"
OUT = Path("evidence/v7_final/synth_deluck_ab")
CELLS = [("serial_killer", "day_vote"), ("wolf", "day_vote"), ("serial_killer", "night_action")]
MIN_FOLLOW = 5


def _credited_for_cell(cell: str):
    """Sorted [(lift, follow, action)] for credited per-game SPs in this cell."""
    led = json.load(open(LEDGER))
    pg = json.load(open(f"{OBS_DIR}/strategy_points.json"))["namespaces"]
    meta = {}
    for c, recs in pg.items():
        rp = "/".join(c.split("/")[1:])
        for r in recs:
            meta[r["key"]] = (rp, r["value"].get("action", ""))
    rows = [(led[k]["shrunk_lift"], led[k]["follow"], meta[k][1])
            for k in led if k in meta and meta[k][0] == cell and led[k]["follow"] >= MIN_FOLLOW]
    return sorted(rows, reverse=True)


def _track_record(rows) -> str:
    return "\n".join(f"- realized lift {lift:+.2f} (followed {fol}x): {act}" for lift, fol, act in rows)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", nargs="+", default=[f"{r}/{p}" for r, p in CELLS],
                    help="role/phase cells to run (default: the 3 deceiver cells)")
    ap.add_argument("--max-clusters", type=int, default=3, help="cap clusters per cell (bound spend)")
    ap.add_argument("--max-workers", type=int, default=12, help="concurrent synthesis calls")
    ap.add_argument("--tag", default="", help="output subdir suffix (e.g. 'flite' to not overwrite pro run)")
    args = ap.parse_args()
    cells = [tuple(c.split("/")) for c in args.cells]
    out_dir = Path(f"{OUT}_{args.tag}") if args.tag else OUT
    out_dir.mkdir(parents=True, exist_ok=True)

    obs_path, sp_path = memory_store_paths(Path(OBS_DIR))
    print("seeding store (cached)...", flush=True)
    seed_memory_from_json_files_cached(observations_path=obs_path, strategy_points_path=sp_path,
                                       target_store=store, cache_dir=Path(OBS_DIR))
    print("seeded.", flush=True)
    config = BatchDedupRunConfig(similarity_threshold=0.70, cluster_mode="bounded", max_cluster_size=15)

    # pass 1 (no LLM): gather clusters + track record per cell, build the concurrent task list
    cell_data: dict = {}
    tasks: list = []  # (cell, ci, ckeys, arm, tr)
    for role, phase in cells:
        cell = f"{role}/{phase}"
        rows = _credited_for_cell(cell)
        if not rows:
            print(f"{cell}: no credited SPs >= {MIN_FOLLOW} follows — skip", flush=True)
            continue
        tr = _track_record(rows)
        items, clusters = cluster_observations_for_synth(store, ("observations", role, phase), config)
        live = [c for c in ([k for k in cl if k in items] for cl in clusters) if c]
        if args.max_clusters:
            live = live[: args.max_clusters]
        cell_data[cell] = {"rows": rows, "tr": tr, "items": items, "live": live, "role": role, "phase": phase}
        print(f"{cell}: {len(items)} obs, {len(live)} clusters (capped={args.max_clusters}), "
              f"{len(rows)} credited SPs", flush=True)
        for ci, ckeys in enumerate(live, 1):
            tasks += [(cell, ci, ckeys, "H", ""), (cell, ci, ckeys, "D", tr)]

    # pass 2 (LLM, concurrent): synthesize every (cluster, arm) task in parallel
    print(f"synthesizing {len(tasks)} calls concurrently (workers={args.max_workers})...", flush=True)

    def _run(t):
        cell, ci, ckeys, arm, tr = t
        d = cell_data[cell]
        sps = synthesize_cluster_sps(d["role"], d["phase"], ckeys, d["items"],
                                     max_retries=1, track_record=tr)
        return (cell, ci, arm, sps)

    results: dict = {}
    with ThreadPoolExecutor(max_workers=args.max_workers) as pool:
        for cell, ci, arm, sps in pool.map(_run, tasks):
            results[(cell, ci, arm)] = sps

    # assemble + write per cell
    for cell, d in cell_data.items():
        role, phase, live = d["role"], d["phase"], d["live"]
        survivor = d["rows"][0]
        lines = [f"# Synthesis A/B — {cell}\n",
                 f"**Pure-prune survivor (arm S, highest realized lift {survivor[0]:+.2f}):**",
                 f"> {survivor[2]}\n",
                 "## Realized track record fed to the credit arm\n", "```", d["tr"], "```\n"]
        for ci, ckeys in enumerate(live, 1):
            h = results.get((cell, ci, "H"), [])
            dd = results.get((cell, ci, "D"), [])
            lines.append(f"## Cluster {ci} ({len(ckeys)} obs)\n")
            lines.append("**H — halo-synthesis:**")
            lines += [f"- ({sp.direction}/{sp.honesty}) {sp.action}" for sp in h] or ["- (none)"]
            lines.append("\n**D — credit-aware synthesis:**")
            lines += [f"- ({sp.direction}/{sp.honesty}) {sp.action}" for sp in dd] or ["- (none)"]
            lines.append("")
        (out_dir / f"{role}_{phase}.md").write_text("\n".join(lines))
        print(f"  -> wrote {out_dir}/{role}_{phase}.md", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
