# Explanation prototype: Cost and latency

Page: `writeup/cost_and_latency/_authoring/cost_and_latency.claude-draft-2026-10-30.md` · Level 1 · Purpose: chapter overview written as a
self-sufficient page (design decision and trade-off mode; a cost-or-performance opening) · Date: 2026-10-30
Checkpoint: waived for this trial. Outcome 2026-10-30: the owner chose the Codex draft (`../cost_and_latency_codex.md`) and took three segments from this one (the input-versus-output example, the shared-output argument for the summary, the seat-id reason for extraction). This draft is kept as `cost_and_latency.claude-draft-2026-10-30.md`; its evidence entry (`evidence/caching/experiment_log.md` §17), script and rates file remain in use. The owner asked for a sample Level 1 written as if the chapter had no
Level 2 pages, to judge whether the sections are too long for one page (conversation of 2026-10-30). The
arrangement is the owner's: the problem's size, the budget, then the levers with their trade-offs.

Authoring material, not page copy. The content plan (`../content_plan.md`) keeps the source disposition,
the bridges and the full "claims to handle with care" list; this brief does not repeat them.

## Reader and explanation

- **Reader outcome:** the reader can say why an agent game of this kind is expensive and slow, what one
  game costs on the site's model and what the budget rules out, how much of a human's time the model
  actually makes them wait, and which of six levers paid off, which did not, and what each gave up.
- **Starting knowledge:** the overview page has told them the game has ten AI seats and a human can take
  one. New concepts, in order: a turn is a model call with a long input; reasoning is billed as output;
  the stage runs ahead of the browser (so latency is not waiting); a prompt cache and a batch API, one
  clause each.
- **Concept order:** calls × input size → bill → where the money goes (output, not input) → what other
  models would cost (budget sets the class) → waiting is a gap, not a latency → levers in the order a
  builder meets them: model tier, thinking, caching, bounding the work, offline, local models; a
  table at the top of the levers section gives each lever's two ends (or its limit) and today's setting.
- **Likely confusion:** reading "input-heavy" as "input is the cost". The page says it twice: tokens are
  mostly input, dollars are mostly output. Second: reading the repricing table as a measured comparison.
  It is labelled as repriced tokens and its caveats sit under it.
- **Section order:**
  1. Intro: the size of the problem, the owner's budget (own bar, not market), the wait as a gap.
  2. What a game costs: measured (memory off, 16 games), where the money goes, memory on as a labelled
     supporting case, the repricing table on both bases.
  3. How long a person waits: the stage mechanism, the measured 3–5%, where it waits, the trade-offs.
  4. The levers, one paragraph each, each with its checked result and what it gave up.

## Sample passage

The repricing paragraph and table in section 1 (the hardest: an estimate that must not read as a
measurement, on two bases the owner asked for). See the page.

## Evidence and scope

- **Sources:** `evidence/gameplay/data/persona_voice_games/*.manifest.json` (16 memory-off games, usage
  buckets and `cost_usd`); `evidence/caching/report.md` §1, §2, §4.1, §4.3–4.6, §5;
  `evidence/caching/experiment_log.md` §11; `frontend/docs/stage_fit/README.md`;
  `evidence/evaluation/model_admission/report.md` §3; `evidence/gameplay/deduction/experiment_log.md` §2;
  `evidence/extraction/post_game/report.md` §4, "Cost"; `evidence/extraction/day_summary/report.md` §8;
  `evidence/gameplay/data/silence_calibration/README.md`; `evidence/fine_tuning/report.md`;
  `Agents/llm_factory/pricing.py`, `accessors.py`; `evidence/gameplay/data/phase3_luna_games/README.md`.
- **Re-derived 2026-10-30, now recorded in `evidence/caching/experiment_log.md` §17** (script
  `evaluation/experiments/game_cost_reprice.py`, rates `evaluation/config/reprice_rates_2026_10_30.json`):
  - The 16 memory-off games aggregated from their manifests: 104–254 calls; mean 172 calls, 1.44M input
    tokens of which 53% cached, 160k output of which 75k reasoning; mean $0.16. Output ≈ $0.08 of $0.16.
  - The repricing table: the mean memory-off game and the memory-on game of 2026-10-13 (1,754,420 input,
    870,186 cached, ≈232k output from $0.116 at $0.50/M) at the catalogue's list rates
    (`pricing.py`, cache write premium applied where the catalogue has one; Opus 5.5 at $4 / $20 / $0.20
    per million, cited in the rates file). Memory off → on: Haiku 0.16 / 0.21; Luna 0.16 / 0.21; DeepSeek
    V4.1 Flash 0.20 / 0.27; Gemini 3.5 Flash-Lite 0.63 / 0.87; Gemini 3.6 Flash 2.33 / 3.20; Sonnet 5.5
    3.03 / 4.18; Opus 5.5 6.05 / 8.35.
  - The memory-on bill by call type is the content plan's re-derivation (`game_cache_share.py`).
- **Claim and limits:** measured costs (model calls only); an estimate (repricing) labelled as such; a
  measurement of waits from seven games played by the owner while building (two backlog readings); the
  paired-game caching result (two games per arm); the thinking-level replay (frozen cases, enforced
  output mode; a live-mode rerun agrees in direction); the extraction overrun (one run; retry fix
  unmeasured); fine-tuning (trained, not wired).
- **Elsewhere:** admission (Evaluation); the node cache (chapter 1); the summary's design (chapter 3);
  what extraction writes (chapter 4); stalls and the rescue model (chapter 7); stage holds (chapter 8).
  Handle with care, applied: no credits or plans named; no "best model"; costs from different runs never
  in one ranked list (the repricing table is one method on one token set, so it is not that); the
  Flash-Lite "cheapest per token" hook not used; Sonnet "$2.30 vs $0.12" not used; the undercounted
  one-hour writes not told.
- **Open questions:** (1) settled: Opus 5.5 rates cited to Anthropic's first-party rates via the Claude
  API reference (read 2026-10-30), recorded in the rates file; (2) settled: the aggregate and the table
  are §17 of the caching log; (3) settled 2026-10-30: the served-game costs are recorded in `evidence/caching/experiment_log.md`
  §17 with counts and dates (Haiku 7 games $0.08–0.20; DeepSeek 3 games; Luna's $0.11 mixes four
  AI-only batch games with four served games at $0.04–0.08; GLM one game; the meter misses the 25%
  write premium, about 2%); (4) "about 150 seat
  calls a game" is from `discussion_evidence.md`; the 16 games average 172 calls in all. Fine as
  "about", or recount.

- **Second draft, 2026-10-30 (owner's notes on the first):** the stated $0.30 bar dropped as arbitrary;
  "as low as play allows" with the achieved range instead. Served-game costs lead, AI-only games as the
  larger sample. Each section opens on the mechanism and its trade-off, the project's measurement
  follows as the illustration; first person kept for decisions only. A call table carries why input is
  heavy and which calls write more. Thinking level now uses the live-mode vote replay (§9), with the
  discussion replay's mode named.

## Review resolution

Not run. This is a length trial; the editorial and claims reviewers run once the owner settles the
page's shape (one page, or one page plus depth pages).

## Trial record

Draft snapshots: `cost_and_latency.first-draft.md` (first draft, 2026-10-30, with the $0.30 bar and example-first sections); the page file holds the second draft.
Model and owner interventions: owner supplied the arrangement and the budget; checkpoint waived.

| Owner change | Kind | Explanation redesigned or local edit? |
|---|---|---|
| | | |
