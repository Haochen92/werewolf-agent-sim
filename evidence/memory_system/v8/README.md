# v8 memory: the ten-seat game

v8 is the memory system from the ten-seat iteration on (2026-10-11): extraction, synthesis and
retrieval rebuilt for the twelve-role pool, a fresh store seeded from AI-only games, and a launch of
memory in the demo as a mechanism to inspect. It is not a new effectiveness experiment: the research
closure stands (`evidence/credit/blindspot_fix/experiment_log.md` §⑥), and nothing here claims that
memory improves play.

| File | What it holds |
|---|---|
| `report.md` | **Start here.** What the memory system does today, why, what has been checked about it, and what is not known |
| `plan.md` | The current plan. §9 is the final plan and wins over earlier sections |
| `decisions.md` | How the rulings were reached, with the commit that carried each out |
| `experiment_log.md` | What was run: the pilot, the extraction model comparison, the day split, the smoke game and de-halo, the bulk seeding |
| `data/` | Run outputs kept for the record: the model comparisons' re-extractions, the de-halo comparison, and the seeding's coverage, per-game table, strategy points and rule screen |
| `prompt_versions/` | The memory prompts as they stood for the seeding |

**Status (2026-10-26).** The current account is [`report.md`](report.md); this line only dates the
milestones.

- **2026-10-11:** the pilot, the extraction model, the day split, the de-halo pass and the 12-game
  seeding.
- **2026-10-12:** synthesis on Claude Sonnet 5.5; extraction moved offline; the gate's read of 96
  lookups (relevance not met: one lesson in seven fit); the stage filter built, off by default.
- **2026-10-13:** 40 games re-extracted and the store `ten_seat_v2` published (498 lessons); the
  credit port; the verdict halo measured; observations tagged with their decision.
- **2026-10-14:** the demonstration run (20 memory-on games, one credit pass: 4 pruned, 4 evicted);
  the lessons published to the server's database (490); memory available on the live site as the
  player's switch, off by default.
- **Not done:** a memory-on vs memory-off comparison (about 35–60 games per arm); validating the
  prune and evict thresholds for ten seats; a learning tick on ten-seat games; extracting served
  games' lessons for their replays.

**Code.** The authoritative code is in `Agents/memory/` (extraction, synthesis, retrieval,
consolidation), `Agents/ten_seat_metrics.py` and `scripts/run_batch.py`. Each run's manifest
carries the git commit that produced it. Run outputs live in `batch_results/` and `memory_stores/`
(both gitignored).
