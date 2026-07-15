"""Ledger-lifecycle simulation — PROBE SCAFFOLDING (see experiment_log.md §3.8).

Replays mined games in order through the tell-ledger spec (design record §3, 2026-07-12):
drop-or-keep dedup at ingest (exact match → embedding top-k prefilter → flash-lite
extensional-equivalence judge), the admission queue, the two-lane bounded checklist
(incumbents + probation), the probation clock, singleton archival, recurrence re-entry,
and spare-slot rotation.

WHAT THIS SIMULATES vs NOT: mechanism dynamics only. There is no detector yet, so "support"
here is MINED recurrence (omniscient, salience-biased) standing in for detected counts —
fine for testing store growth, dedup behavior, queue depth, and tier occupancy; meaningless
for tell validity. The fat-null demotion rule needs detected lift and is NOT exercised.

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/ledger_sim.py \
      --inputs outputs/mining_v4_flashlite_split.jsonl outputs/mining_v4_games06_30.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import numpy as np
from pydantic import BaseModel, Field

from Agents.llm_factory import get_llm_dedup
from Agents.memory.store import embeddings as _embedding_model
from Agents.memory.vectors import embed_texts

PROBE_DIR = Path(__file__).resolve().parent.parent

# v1 defaults (design record §3 ledger spec; tunable)
N_INCUMBENT, N_PROBATION, N_ROTATION = 25, 15, 8
K_PROBATION = 12        # scanned games before a probation verdict
QUEUE_TTL = 5           # games a queued candidate survives with no new evidence
TOPK_PREFILTER = 5      # embedding neighbours judged per new wording
REQUEUE_RECURRENCE = 2  # distinct-game mined matches to re-enter an archived tell


class SameTellVerdict(BaseModel):
    same: bool = Field(description="True only if the two descriptions denote the SAME tell.")
    reason: str = Field(description="One short sentence for the call.")


JUDGE_PROMPT = """You are deduplicating behavior patterns ("tells") mined from Werewolf game
transcripts. Two descriptions are THE SAME TELL only if a reader scanning a transcript would
count the SAME moments as instances of both — same behavior, same mechanism, same trigger.
Judge strictly: a narrower sub-type, different tactic/mechanism/trigger, or different relation
to the target means DIFFERENT. Pure rephrasings are the SAME.

A: {a}
B: {b}
"""


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower().rstrip(".")


class Tell:
    __slots__ = ("tid", "channel", "canonical", "status", "instances", "scanned",
                 "entered_scan", "queued_at", "last_scanned", "post_archive_games")

    def __init__(self, tid, channel, canonical, game_idx):
        self.tid, self.channel, self.canonical = tid, channel, canonical
        self.status = "queued"          # queued | probation | incumbent | archived
        self.instances = []             # (game_idx, exhibitor, role)
        self.scanned = 0                # games spent on the checklist (this stint)
        self.entered_scan = None
        self.queued_at = game_idx
        self.last_scanned = -1
        self.post_archive_games = set() # distinct games with mined recurrence since archival

    def support(self):
        """MINED-recurrence proxy: distinct (game, exhibitor) pairs."""
        return len({(g, e) for g, e, _ in self.instances})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--inputs", nargs="+", required=True)
    ap.add_argument("--out", default=str(PROBE_DIR / "outputs" / "ledger_sim_metrics.jsonl"))
    args = ap.parse_args()

    rows = [json.loads(l) for p in args.inputs for l in open(PROBE_DIR / p if not Path(p).is_absolute() and not Path(p).exists() else p)]
    game_order = list(dict.fromkeys(r["game_id"] for r in rows))
    by_game = defaultdict(list)
    for r in rows:
        by_game[r["game_id"]].append(r)
    print(f"{len(rows)} rows over {len(game_order)} games")

    llm = get_llm_dedup().with_structured_output(SameTellVerdict)
    tells: dict[str, Tell] = {}
    by_exact: dict[tuple[str, str], str] = {}   # (channel, normed wording) -> tid
    emb_cache: dict[str, np.ndarray] = {}
    judge_calls = 0
    metrics = []

    def embed(texts):
        new = [t for t in texts if t not in emb_cache]
        if new:
            for t, v in zip(new, embed_texts(new, _embedding_model)):
                v = np.array(v)
                emb_cache[t] = v / np.linalg.norm(v)
        return [emb_cache[t] for t in texts]

    with open(args.out, "w") as mf:
        for g_idx, gid in enumerate(game_order):
            fresh = matched = 0
            # ---- 1. ingest this game's mined rows (drop-or-keep) --------------------------
            for ch in ("vote", "discussion"):
                ch_rows = [r for r in by_game[gid] if r["channel"] == ch]
                canon = [t for t in tells.values() if t.channel == ch]
                new_batch = []
                for r in ch_rows:
                    key = (ch, _norm(r["behavior"]))
                    if key in by_exact:
                        tells[by_exact[key]].instances.append((g_idx, r["exhibitor"], r["exhibitor_role"]))
                        matched += 1
                    else:
                        new_batch.append(r)
                # embedding top-k + judge for non-exact newcomers, judged against current canon
                if new_batch and canon:
                    cvecs = np.array(embed([t.canonical for t in canon]))
                    tasks = {}
                    with ThreadPoolExecutor(max_workers=8) as pool:
                        for r in new_batch:
                            nv = embed([r["behavior"]])[0]
                            sims = cvecs @ nv
                            top = np.argsort(-sims)[:TOPK_PREFILTER]
                            for i in top:
                                fut = pool.submit(llm.invoke, JUDGE_PROMPT.format(a=canon[i].canonical, b=r["behavior"]))
                                tasks[fut] = (r, canon[i])
                        results = defaultdict(list)
                        for fut in as_completed(tasks):
                            r, cand = tasks[fut]
                            try:
                                if fut.result().same:
                                    results[id(r)].append(cand)
                            except Exception:
                                pass
                    judge_calls += len(tasks)
                    for r in new_batch:
                        # same-batch rows with identical wording: an earlier row in THIS loop
                        # may have updated by_exact since the batch was formed — re-check
                        # before creating a duplicate tell (§3.9 caught 24 of these leaks).
                        key = (ch, _norm(r["behavior"]))
                        if key in by_exact:
                            tells[by_exact[key]].instances.append((g_idx, r["exhibitor"], r["exhibitor_role"]))
                            matched += 1
                            continue
                        hits = results.get(id(r))
                        if hits:
                            t = hits[0]  # earliest-canon preference is implicit in list order
                            t.instances.append((g_idx, r["exhibitor"], r["exhibitor_role"]))
                            by_exact[(ch, _norm(r["behavior"]))] = t.tid  # future exact hits land here
                            matched += 1
                            if t.status == "archived":
                                t.post_archive_games.add(g_idx)
                                if len(t.post_archive_games) >= REQUEUE_RECURRENCE:
                                    t.status, t.queued_at, t.post_archive_games = "queued", g_idx, set()
                        else:
                            tid = f"{ch[:4]}_{len(tells)}"
                            t = Tell(tid, ch, r["behavior"], g_idx)
                            t.instances.append((g_idx, r["exhibitor"], r["exhibitor_role"]))
                            tells[tid] = t
                            by_exact[(ch, _norm(r["behavior"]))] = tid
                            fresh += 1
                elif new_batch:  # first game: everything is new
                    for r in new_batch:
                        key = (ch, _norm(r["behavior"]))  # same-batch identical wording
                        if key in by_exact:
                            tells[by_exact[key]].instances.append((g_idx, r["exhibitor"], r["exhibitor_role"]))
                            matched += 1
                            continue
                        tid = f"{ch[:4]}_{len(tells)}"
                        t = Tell(tid, ch, r["behavior"], g_idx)
                        t.instances.append((g_idx, r["exhibitor"], r["exhibitor_role"]))
                        tells[tid] = t
                        by_exact[(ch, _norm(r["behavior"]))] = tid
                        fresh += 1

            # ---- 2. checklist assembly + clocks (per channel) ------------------------------
            occupancy = {}
            for ch in ("vote", "discussion"):
                pool_t = [t for t in tells.values() if t.channel == ch]
                # queue hygiene
                for t in pool_t:
                    if t.status == "queued" and g_idx - t.queued_at > QUEUE_TTL and t.support() < 2:
                        t.status = "archived"
                # probation verdicts
                for t in pool_t:
                    if t.status == "probation" and t.scanned >= K_PROBATION:
                        t.status = "incumbent" if t.support() >= 2 else "archived"
                # incumbent lane: rank by support proxy, cap
                inc = sorted((t for t in pool_t if t.status == "incumbent"), key=lambda t: -t.support())
                for t in inc[N_INCUMBENT:]:
                    t.status = "archived"
                inc = inc[:N_INCUMBENT]
                # probation admissions from queue
                prob = [t for t in pool_t if t.status == "probation"]
                queue = sorted((t for t in pool_t if t.status == "queued"),
                               key=lambda t: (-t.support(), t.queued_at))
                for t in queue[: max(0, N_PROBATION - len(prob))]:
                    t.status, t.scanned, t.entered_scan = "probation", 0, g_idx
                    prob.append(t)
                # rotation: least-recently-scanned archived
                arch = sorted((t for t in pool_t if t.status == "archived"), key=lambda t: t.last_scanned)
                rot = arch[:N_ROTATION]
                # tick clocks for everything on the checklist
                for t in inc + prob + rot:
                    t.scanned += 1
                    t.last_scanned = g_idx
                occupancy[ch] = {"incumbent": len(inc), "probation": len(prob),
                                 "queue": sum(1 for t in pool_t if t.status == "queued"),
                                 "archived": sum(1 for t in pool_t if t.status == "archived"),
                                 "rotation": len(rot)}

            m = {"game": g_idx + 1, "fresh": fresh, "matched": matched,
                 "total_tells": len(tells), "judge_calls": judge_calls, **{
                     f"{ch[:4]}_{k}": v for ch, occ in occupancy.items() for k, v in occ.items()}}
            metrics.append(m)
            mf.write(json.dumps(m) + "\n")
            if (g_idx + 1) % 5 == 0:
                print(f"game {g_idx+1}: total={len(tells)} fresh={fresh} matched={matched} "
                      f"vote(inc/prob/q/arch)={occupancy['vote']['incumbent']}/{occupancy['vote']['probation']}"
                      f"/{occupancy['vote']['queue']}/{occupancy['vote']['archived']} "
                      f"disc={occupancy['discussion']['incumbent']}/{occupancy['discussion']['probation']}"
                      f"/{occupancy['discussion']['queue']}/{occupancy['discussion']['archived']}", flush=True)

    # final snapshot
    snap = [{"tid": t.tid, "channel": t.channel, "status": t.status, "support": t.support(),
             "canonical": t.canonical} for t in tells.values()]
    Path(PROBE_DIR / "outputs" / "ledger_sim_store.json").write_text(json.dumps(snap, indent=1))
    st = Counter(t.status for t in tells.values())
    print(f"\nFINAL: {len(tells)} tells | status={dict(st)} | judge_calls={judge_calls}")
    fresh_last10 = [m["fresh"] for m in metrics[-10:]]
    print(f"fresh-tell rate, last 10 games: {fresh_last10} (mean {sum(fresh_last10)/10:.1f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
