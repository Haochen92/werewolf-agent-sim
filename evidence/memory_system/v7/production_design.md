# v7 — production design considerations (post-experiment / go-live)

Forward-looking notes for **after** the experiment loop validates and we ship a live deployment. NOT part
of the experiment itself — the experiment keeps things synchronous/concurrent (turnaround pinches between
generations); production has no such constraint.

## 1. Memory-update = an async, batch-discounted, out-of-band pipeline

**Separation:** interactive game-serving stays real-time/concurrent; the memory update runs **out-of-band**.
The agent that plays never waits on memory maintenance — the store just gets richer over time.

**Pipeline (triggered after a batch of *sampled* games, not every game):**
```
sampled finished games  →  EXTRACT (obs/SPs)  →  DEDUP into the store  →  SYNTHESIZE (cluster SPs)
                           └──────────────── one async Gemini BATCH job ────────────────┘
```
All three passes are independent, latency-tolerant, high-throughput → ideal for **Gemini batch mode
(~50% token discount)**. Because it's off any critical path, the **24h batch SLA is a non-issue** — make it
**fire-and-forget**: submit the batch, let the store update whenever it completes; serving always reads the
latest committed store. A game played today gets its lessons folded in "sometime in the next day," which is
fine for a memory that compounds over many games. (Don't design around sub-SLA speed — it's variable/not
contractual; plan for 24h, treat faster as a bonus.)

**Stacking discounts:** **sampling** (extract from a fraction of games, not all) multiplies with the batch
discount; **prefix caching** (already ~97% cache-read on extraction) stacks on top.

**The one hard requirement — idempotency + retry:** batch jobs can return partial/failed results, so the
pipeline must process each game-id **exactly once** (dedup covers the obs side; credit/synthesis need a
"seen game-id" guard) and safely re-run on failure without double-counting.

**What stays real-time (NOT batchable):** game-play itself — the agents' turn-by-turn decisions are stateful
within a game. Its lever is **concurrency** (parallel independent games), not the batch API.
