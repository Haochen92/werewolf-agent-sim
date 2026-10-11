# Memory for the ten-seat cast: seeding plan and retrieval redesign

Written 2026-10-10 for the agent that runs this work in parallel with the frontend pass.
The owner rules the two open decisions in §2 before any game is paid for.

## 0. Why now, and what this is not

- The Phase 3 cast (ten seats drawn from a twelve-role pool, `evidence/game_play_enhancement/role_sheet.md`)
  has no memory: the pipeline silently skips every new role (census §5,
  `evidence/game_play_enhancement/phase3_wiring_census.md`). Live ships memory off for it.
- The Google Cloud credit has about $120 left and expires around 2026-10-16. It pays for games
  once. Everything that changes what a game WRITES to the store must be decided before the
  first seeding game; everything that changes how a store is READ can wait.
- This is NOT a benefit experiment. The memory research is closed (owner concedes no certified
  current-epoch benefit; `evidence/memory_system/effectiveness/report.md` and the v7 campaign
  record). The goal is a store with real content for all twelve roles so the demo's memory
  toggle and X-ray show something true for the ten-seat game, at a per-turn cost the demo can
  afford. Nothing here is a claim about win rates.
- The old stores (`memory_stores/v5_*`, `demo_snapshots/demo_gen1`) describe a different game
  (nine seats, old investigator, villagers, plain wolves, old prompt epochs, zero reasoning
  tokens). Seed a FRESH store. Do not merge the old one in.

## 1. The owner's proposal (as stated 2026-10-10)

1. Retrieval cadence. Today every AI turn with memory on runs the situation-summary call
   (`Agents/memory/retrieval/situation_agent.py`) and the retrieval behind it. Change to once
   per round: retrieve at the day's first action-phase round (the opening round) and inject the
   same lessons for the rest of that round's turns; retrieve once for the vote; at night the
   pack retrieves once per ROLE, not per wolf per turn.
2. Possibly drop the situation summary entirely. Retrieval becomes a metadata lookup: the
   role, the phase and the deterministic regime key, no embedding query, no LLM call. If this is
   approved the extraction prompt is adjusted so the stored items carry what the lookup needs.
3. Spend the remaining credit seeding a decent number of memories for every role.

## 2. Two decisions the owner rules first (they change what the games write)

D1. Metadata-only retrieval: yes or no. Recommendation: YES.
- The regime key already exists. `Agents/memory/dedup_gate.py::gate_key` is
  (is_swing, alive bucket, consensus_direction), all derived from the board census, no LLM.
  Strategy points are synthesized per gate-key cluster (`strategy_synthesis.py`), so a lookup
  "this role, this phase, this gate key, top-k strategy points by credit" is the design the
  store already has. Proven-first tiering (`plan_gating.py::_sp_proven_tiering_enabled`) is the
  ranking.
- Embedding similarity was measured blind to applicability (`retrieval/dimension_gating.py`
  header: 0.827 vs 0.828). Dropping the query embed loses little that was measured.
- Served games already retrieve strategy points only (`server/game/run_config.py`,
  `retrieval_types_config`), so observations need not be retrievable at all; they remain the
  extraction's raw material for synthesis.
- Consequence for extraction: the semantic dims (`exposure_class`, `info_landscape_class`) stop
  mattering for retrieval. Keep the gate-key dims mandatory and reliable in the extraction
  output; the free-text `situation` becomes documentation for the X-ray, not a retrieval key.
  Decide the extraction-prompt change under D1, then freeze it for the whole seeding run.

D2. What the twelve roles' memory cells look like.
- Today the cells are six roles by phase (`Agents/schemas/memory.py` `_CELL_REGISTRY` around
  line 528, `_SITUATION_CELL_REGISTRY`, the SP registry around line 755; `extraction/cell_units.py`
  `ROLE_UNITS`; `extraction_agent.py` `EXTRACTION_ROLES`). A new role extracts nothing.
- Recommendation: ONE generic cell schema per phase (day, night) shared by all twelve roles,
  with `perspective` taking the role name, instead of twelve hand-written role schemas. The role
  sheet's night rules differ, but the memory dims (gate key, target landscape, exposure) are
  role-agnostic, and `CellStrategyMixin` is already "the single universal payload". The old
  six keep their schemas only if a test depends on them; otherwise retire them with the game.
- Day-only roles (none now; every seat acts at night except by roleblock) still get both units.
  The neutral roles (speculator, fortune teller) get a day cell and a night cell like the rest;
  their "night action" is a pick or a bet, which the sheet says is not a visit.

## 3. Order of work (the credit clock sets it)

Day 1 (no games yet):
1. Rule D1 and D2 with the owner.
2. Extend the pipeline to the pool: cell registries, `ROLE_UNITS`, `EXTRACTION_ROLES` (already
   `tuple(roles)`, so it follows the registry), the situation agent's fallback (census §5 says it
   falls back to the VILLAGER prompt for a role without a cell; under D1 the situation agent
   is retired for retrieval, but extraction still composes cells), `Agents/config/run.py`
   `DEFAULT_MEMORY_CONFIG` and friends (four roles listed; a role not listed is memory-off),
   credit and scoring role sets (`consolidation/credit_rules.py`, `decision_scoring.py`,
   `credit.py`), `tell_book.py`, `compute_metrics.py`.
3. Adjust the extraction prompt per D1. Snapshot it to `prompt_versions/` here.
4. One extraction-on game on the current default model (gemini-3.5-flash-lite, medium
   thinking: the Phase 3 games' setting) and read the output by hand for every role present.
   Fix, then freeze.

Days 2 to 5 (games):
5. Seed. The procedure and footguns are in `evidence/memory_system/effectiveness/v5_seeding_plan.md`
   and the memory note `project-v5-seeding-and-seedability`; the parts that still bite:
   - play memory OFF, extraction ON, dump ON: the store is pure output.
   - a DISTINCT `--output` file per batch (the JSONL appends; a reused file co-mingles records).
   - the dump overwrites the store JSON from the in-process store: batch 2 onward must load the
     accumulated store (no `--no-memory-seed`), and checkpoint the store dir before each batch.
   - seeding games write a shared store, so run them sequentially, or dump each game to its own
     dir (`--dump-store-dir`) and merge afterwards. Never more than two games in parallel on the
     Vertex shared pool regardless (five at once produced 429s everywhere in the balance run).
   - lineups vary per game (lone killer and neutral seat are drawn), so count games per ROLE,
     not games. The necromancer and fortune teller appear in roughly half the games each.
6. Budget. Phase 3 flash-lite games cost about $0.72 each in play; extraction on top was about
   $0.5 a game in the v5 era with a bigger extractor and six roles. Expect $1.5 to $2 a game
   with twelve roles. That is 60 to 80 games on $120, call it 40 to 50 appearances of each
   always-present role and 20 to 30 of each drawn role. Watch net-new `kept` per batch and stop
   growth at the knee; the credit is the ceiling, not the target.
7. Freeze the store as `memory_stores/ten_seat_v1` (name it once; stores are not git-tracked, so
   also snapshot under `memory_stores/_checkpoints/`) and write the per-role counts into this
   folder's README.

After the credit (no clock):
8. The read side: cadence (once per round, once per role at night) and the metadata lookup.
   Retrieval lives in `Agents/memory/retrieval/pipeline.py::enrich_payload_with_memory`, called
   per turn from `Agents/turn/pipeline.py` (day at line 196, night at line 385). Once-per-round
   means caching the enriched lessons per (player, day, round, phase) across the round's turns;
   the natural place is the day-channel state that the scheduler already recomputes from.
9. Served games: point `WW_MEMORY_STORE_DIR` at the frozen store, keep strategy points only,
   and re-run the leak checks (`evidence/agent_boundaries/`) because the wire events now carry
   twelve roles' memory.

## 4. What the frontend pass depends on, and the rule between the two agents

- The wire is untouched by this plan. `server/schemas/events.py::MemoryConsulted` carries the
  retrieved lessons and verdicts per (player, day, round, phase) and no query text, so dropping
  the situation summary changes nothing on the wire. Once-per-round retrieval only means fewer
  memory-consulted events; the frontend folds them per player and appends.
- RULE: do not edit `server/schemas/events.py`, `server/translate.py`, or regenerate the OpenAPI
  contract (`frontend/src/types/contracts/`) during this work. A regenerated contract fails the
  frontend typecheck mid-pass. If a wire change becomes necessary, write it down here and hand
  it over; the frontend pass applies it.
- The ticket's memory toggle and the landing's memory copy belong to the frontend pass. They
  stay; the toggle reads "off until the ten-seat store ships".

## 5. What this folder will hold

`experiment_log.md` (chronological: rulings, the extraction read of game 1, each batch's counts
and net-new), `prompt_versions/` (the frozen extraction prompt), `data/` (manifests and records
per game, like `evidence/game_play_enhancement/data/phase3_balance/`), `README.md` at the end
with the per-role store counts and the store name. Not a report: there is no claim to defend.
