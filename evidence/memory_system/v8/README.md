# v8 memory: the ten-seat game

v8 is the memory system from the ten-seat iteration on (2026-10-11): extraction, synthesis and
retrieval rebuilt for the twelve-role pool, a fresh store seeded from AI-only games, and a launch of
memory in the demo as a mechanism to inspect. It is not a new effectiveness experiment: the research
closure stands (`evidence/credit/blindspot_fix/experiment_log.md` §⑥), and nothing here claims that
memory improves play.

| File | What it holds |
|---|---|
| `plan.md` | The current plan. §9 is the final plan and wins over earlier sections |
| `decisions.md` | How the rulings were reached, with the commit that carried each out |
| `experiment_log.md` | What was run: the pilot, the extraction model comparison, the day split |
| `data/` | Run outputs kept for the record: the model comparisons' re-extractions, the de-halo comparison, and the seeding's coverage, per-game table, strategy points and rule screen |
| `prompt_versions/` | The memory prompts as they stood for the seeding |

**Status (2026-10-11).**
- Done:
  - the pilot;
  - the extraction model (gemini-3.8-flash);
  - the day split;
  - provenance;
  - the metrics port.
- Next: the bulk seeding, 12 games (plan §9.5).
- After seeding: synthesis and review, retrieval cadence, the gate, launch.
- After launch: the credit port (plan §9.6).

**Code.** The authoritative code is in `Agents/memory/` (extraction, synthesis, retrieval,
consolidation), `Agents/ten_seat_metrics.py` and `scripts/run_batch.py`. Each run's manifest
carries the git commit that produced it. Run outputs live in `batch_results/` and `memory_stores/`
(both gitignored).
