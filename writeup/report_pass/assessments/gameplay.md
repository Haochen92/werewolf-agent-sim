# Assessment: gameplay

## Summary table

| Folder / document | Editorial condition | Structural recommendation | Main issue | Proposed action |
|---|---|---|---|---|
| `game_play_enhancement/report.md` | light edit (unfinished) | relocate → `gameplay/report.md` (the hub) | Problem 1 is close to exemplar quality. Problems 2–5 are one-line stubs. The thinking-budget row does not name the model it was measured on | Write problems 2–5 from the index below. Name the model in the thinking row |
| `game_play_enhancement/discussion_evidence.md` | journey log, keep whole | relocate → `gameplay/discussion_evidence.md` | 27,500 words with no map to the reports it feeds. §9 open questions are frozen at 2026-10-03 | Add the section index below as a header block. Mark the answered §9 items in place |
| `game_play_enhancement/role_sheet.md` | authoritative ruling; light edit | relocate → `gameplay/roles/` | Change log stops at R10 (2026-10-17). Its 2026-10-09 entry says "unclaimed is a valid cover", which R11 reversed in the cards | Add an R11 change-log entry |
| `game_play_enhancement/phase3_wiring_census.md` | historical build record | relocate → `gameplay/roles/` | Status line ("Nothing is committed") reads as current | Add a one-line "historical, 2026-10-09" banner |
| `reasoning_failures/report.md` | light edit | relocate → `gameplay/deduction/` | §4 "The evil side" credits a result mostly caused by role-card text to the engine's section. §3 gives a test count | Move the card-text result to the roles report and keep the engine's increment here. Drop the count |
| `reasoning_failures/deduction_catalogue.md` | authoritative specification | keep with deduction | Build-status slice 2 lists the modes as off/record/full. The code also has `public` | Correct the one row |
| `deduction_catalogue_review{,_v2,_v3}.md` | superseded (historical) | keep, in `deduction/reviews/` | None as records. Their corrections are folded into the catalogue | Move only |
| `reasoning_failures/experiment_log.md` | log | keep with deduction | Its case register also holds non-deduction cases (R2, R10–R14) | Index those cases from the hub |
| `sequential_discussion/report.md` | rewrite | relocate → `gameplay/discussion/` | Describes a design the code no longer has. The current day is stated nowhere in this folder | Rewrite as the day discussion today. Keep the June decision as the case study |
| `generation_prompt/` | missing report (warranted) | relocate → `gameplay/turn_prompt/` | Its "as it stands today" section (§0) describes the July nine-seat flash-lite prompt | Write a reference report for the turn prompt and the record a seat reads |
| `role_set/` | missing report (not warranted alone) | relocate log → `gameplay/roles/` as history | June nine-seat decision, superseded by the role sheet | Fold into one roles report with the role sheet and the balance batches |
| `agent_boundaries/report.md` | matches (one light edit) | keep in place; link from the hub | Silent on the deduction engine, a new payload consumer since 2026-10-16 | Add one sentence in §1 linking `deduction/report.md` §1 |

## Per folder

### game_play_enhancement/
- **Documents:**
  - `report.md`: ~1,000 words, authoritative but unfinished.
  - `discussion_evidence.md`: ~27,500 words, the journey log. It is authoritative as the record; its §1 premise (nine seats, novelty gate) is historical.
  - `role_sheet.md`: ~7,300 words, the authoritative roles ruling.
  - `phase3_wiring_census.md`: ~2,000 words, historical (the build plan and census of 2026-10-09).
  - `data/`: 33 subfolders, listed only.
- **Reader question:** what went wrong in how the AI players play, what caused each problem, and which interventions worked?
- **Scope and primary sources:** problems and interventions. The evidence is `discussion_evidence.md` §2–§8, the READMEs under `data/` (`evil_cover_screen/`, `evil_cover_games/`, `counter_claim_votes/`, `phase3_*`, `haiku_*`, `night1_target_bias/`), and the factual_errors detailed record.
- **Condition, with justification:**
  - `report.md` follows the factual_errors exemplar's split: measurement links out, interventions stay here. Problem 1 states the symptom, why it matters, the causes, a table split into "telling" and "giving the fact", and why telling failed.
  - Two edits. First, the "A higher thinking budget" row (82 → 27 of 267) is gemini-3.5-flash-lite at minimal against medium (discussion_evidence §6.7). "Where it stands" then discusses Haiku 5.5 at low against medium. A reader will conflate the two models; name the model in the row.
  - Second, "Other problems, to be written" is the whole remainder of the report. The report cannot answer its reader question until those are written.
  - `role_sheet.md` is current except for R11: the code has "Never deny it either" in `Agents/prompts/roles/pack.py:27` and `serial_killer.py:38`, but no change-log entry records it.
- **Suspected stale mechanisms:**
  - Checked `report.md`'s live-fix claims. The claim ledger is the `claim` and `claimed_night_actions` fields in `Agents/schemas/lineup_output.py`. The deduction engine is `Agents/deduction/`. Both match.
  - `role_sheet.md` is stale on R11, as above.
  - `phase3_wiring_census.md` line 5 says "Nothing is committed", which is no longer true.
- **Overlap:**
  - Problem 1 repeats the fix rows of `evaluation/factual_errors/report.md` step 3 ("Fix" column). The split is intended: measurement there, interventions here. Keep each number's full statement in one place.
  - The "Evil never contesting" stub points at `reasoning_failures/report.md` §4.
- **Proposed action:**
  1. Write problems 2–5 (thin talk, reasoning failures, silence, evil never contesting), each as a short pointer section over its component report.
  2. Name the model in the thinking row.
  3. Add an R11 change-log entry to the role sheet.
  4. Put a historical banner on the census.

### game_play_enhancement/discussion_evidence.md: proposed index
Keep it whole. Add this as a header block. The "Feeds" column names the component report each section supplies under the proposed layout (§Area-level).

| Section | Content | Feeds |
|---|---|---|
| §1, §2.1–2.3, §2.5 | Premise check: accusations rest on votes. The investigator is not hiding. Talk is flat because one source of truth is never contested | hub Problem 2 (thin talk); roles (why Phase 3) |
| §2.4 | Most "silence" is the scheduler's doing | discussion |
| §3 P1, P2, P5; §4; §5; §6.1; §6.3 | Phase 1 prompt changes to turn-taking, the summary and message length; measurement plan; build; the two v2 games | discussion (Phase 1); judge method → `evaluation/llm_judge` |
| §3 P3 | Tell evil players that claiming is an option | roles (evil contest, step 1) |
| §3 P4 | Voting instructions deliberately unchanged | turn_prompt |
| §6.2 | The invented investigator result; the results reworded | hub Problem 1; turn_prompt (results wording); measurement → factual_errors step 3 |
| §6.4–6.5 | Game won on a fabricated premise; the code audit; the fidelity pass on the bench | turn_prompt (what a seat is given); factual_errors log §8–9 |
| §6.6 | Day summary v4: the summariser transcribes, code keeps the claim ledger | turn_prompt (the record); hub Problem 1 |
| §6.7 | Turns ran with zero reasoning tokens; thinking budget | hub Problem 1 and decisions; `model_selection` |
| §7.1–7.4 | Phase 2: game-record counts, then the day redesign (opening round, sweep, echo gate, opening filter, closing defence) | discussion (the current day design). Steps 6–7 (wire, stage) → frontend docs |
| §7.5 | List-order and example-seat bias; night-1 lot | turn_prompt |
| §8 R1–R7, §8.1–8.3 | Phase 3 role plan, build order, wiring, four balance batches and the hold | roles |
| §8.4–8.5 | Ten-seat hallucination kinds and what fixed what; learnings | hub Problem 1; factual_errors log §6. §8.5 item 5 → roles; item 7 → turn_prompt |
| §8.6 | First Haiku game: visits read backwards, repeated replies, votes without reasons | turn_prompt (rules text); discussion (repeats); deduction (AC3/AC4 source) |
| §8.7 | Comparative reads; vote-history tag tried and removed | turn_prompt (reads and decisions) |
| §9 | Open questions as of 2026-10-03 (items 1, 3, 6 partly overtaken by Phase 2/3) | hub "what is unresolved" |

### reasoning_failures/
- **Documents:**
  - `report.md`: ~3,900 words. Authoritative: the engine's current contract.
  - `deduction_catalogue.md`: ~32,000 words. Authoritative as the row-level specification, owner rulings R1–R11 and build record. Its pass-history header and resolved open questions are historical.
  - `deduction_catalogue_review.md` (v1, ~2,400), `_v2` (~1,900) and `_v3` (~1,400): all superseded, all three dated 2026-10-16. Each one's corrections were taken into the catalogue and marked inline ("(review §k)", "(review v2 §k)", "(review v3 §k)"). v1 reviewed a file name that no longer exists (`deduction_catalogue_draft.md`). Reviews v4 and v5, which the catalogue cites for Table F, Rendering and the acceptance cases, were never saved as files. None of the three should be read as current; keep them as the dated record of external review.
  - `experiment_log.md`: ~4,800 words, the log (case register R1–R14 and experiments §1–§7).
  - `live_e79f21d7/review.md`: historical, one game's claim-safety review.
- **Reader question:** how does the harness hand each seat the conclusions it could draw, and how do we know no line is false?
- **Scope and primary sources:** the deduction engine. Evidence: `data/deduction_*`, `data/solver_census/`, `data/haiku_effort_replay/`, `tests/engine/deduction/`.
- **Condition, with justification:**
  - A reference doc with an orientation path, contract (§1), mechanism (§2), verification (§3), evidence verdict-first (§4) and limits (§5). It already meets most of the exemplars' habits.
  - Light edits:
    - §3 opens with "372 tests". The deterministic_audits exemplar names tests and never counts them, because the suite is AI-written and unaudited.
    - §4 "The levers tried before code" welds four experiments into one paragraph. Split it per lever.
    - §4 "The evil side": the report's own numbers show that the card text alone moved claims from 13 to 33 and denials from 21 to 3, and the engine's lines added 33 → 44 and 3 → 0. The 8 paired games bundle both. As placed, the reader credits the engine with a role-card intervention.
  - `writeup/map.md` line 635 says record inconsistencies are "listed in the report's review note". The report has no review note.
- **Suspected stale mechanisms:**
  - Checked `DeductionMode = Literal["off","record","public","full"]` (`Agents/schemas/deduction.py:20`), the per-side override (`Agents/config/run.py:71`), `verified.py` and `render.py` in `Agents/deduction/`, and the `{deduction_seat_before_note}` slot ahead of memory in `Agents/prompts/memory/context.py`. The report matches all of them.
  - The catalogue's Build status slice 2 ("off / record / full") is stale against the code and the report.
- **Overlap:**
  - The log's §2 thinking budget overlaps discussion_evidence §6.7 (a different model, flash-lite) and the hub.
  - The case register's R2 (closing line), R10–R11 (rule recitation), R12 (silence) and R13 (wolf chat) are discussion problems, not deduction.
  - `evaluation/deterministic_audits` Case 2 summarises §3 and links back, correctly.
- **Proposed action:**
  1. In §4, cut "The evil side" to the engine's share and a pointer to the roles report.
  2. Drop the test count.
  3. Split the levers paragraph.
  4. Fix catalogue slice 2.
  5. Move the reviews to `reviews/` with a one-line note that the catalogue absorbed them.

### Evil covers and counter-claims: placement by intervention
- **Evil covers.** The intervention is role-card text: owner ruling R11, "claim, never deny", in `Agents/prompts/roles/pack.py` and `serial_killer.py`. It continues a thread that is all role instructions: Phase 1 P3 (discussion_evidence §3), the batch-4 cover story (§8.3, 2026-10-09) and then R11. The engine's evil-seat lines (catalogue slices 13, 13b and 14) are a second, smaller intervention.
  - **Home:** the roles report, as the "evil contest" thread, with the 41-turn screen and the 8 paired games.
  - **Deduction report:** keeps a short paragraph on what the engine adds and links to the roles report.
  - **Data:** `data/evil_cover_screen/` and `evil_cover_games/` go with roles.
- **Counter-claim accounts.** The intervention is an engine line (slice 16), screened on 10 vote turns and dropped. It belongs to deduction: one paragraph in the report as a dropped line, the detail in the log, `data/counter_claim_votes/` beside it.

### sequential_discussion/
- **Documents:**
  - `report.md`: ~2,800 words, superseded in part, and its banner says so.
  - `experiment_log.md`: ~8,600 words, historical journey log (the genre exemplar named by the style guide).
  - `quality_gate/experiment_log.md`: historical; the concurrent-vs-sequential A/B, N=4 per arm.
- **Reader question:** how does the day discussion decide who speaks, when a day ends, and why?
- **Scope and primary sources:** the scheduler and day flow. Evidence: `tests/engine/test_scheduler.py`, `quality_gate/`, discussion_evidence §7.
- **Condition, with justification: rewrite.** The report describes a design the code no longer has, and the current day design is stated nowhere in this folder.
  - The banner (2026-10-07) says the proactive tier was replaced. But §1–§2 and §4 still present quietest-first picks, the novelty gate and trailing-pass termination as the mechanism.
  - Today's day (opening round → reactive obligations → sequential sweeps → closing defence; discussion_evidence §7.4 steps 4b–4c) exists only inside the 27,500-word log.
  - §5's gaps are mostly closed or changed. The human gap is closed and the persona work was built.
  - Confidence is graded with shorthand ("HIGH confidence", "[medium]") instead of being stated with its N.
- **Suspected stale mechanisms** (checked against `Agents/turn/` and `Agents/config/game.py`):
  - §2 "Where it lives" names `Agents/turn/decision.py` and `Agents/turn/novelty_agent.py`. Neither exists. The per-line gate is now `Agents/turn/echo_gate.py`, and the opening filter is `round_filter.py`.
  - The knobs moved to `Agents/config/game.py`. `reengagement_cooldown_multiplier` is still 1.0 and `per_pair_reengagement_cap` still 2. `proactive_budget` and `opener_floor` are replaced by `max_proactive_sweeps`.
  - §3 cites `tests/test_scheduler.py`; it is now `tests/engine/test_scheduler.py`.
  - §5 "Human speech-act extraction is not built" is false: `Agents/turn/addressing_agent.py` tags human turns.
  - The scheduler's own docstring (`scheduler.py` lines 5–11) confirms the reactive → sweep → terminate order.
- **Overlap:** discussion_evidence §2.4, §3 (P1, P2) and §7.1–7.4 are the later half of the same component.
- **Proposed action:** rewrite the report as "The day discussion today":
  - the reactive layer, which is unchanged, plus the Phase 2 rounds;
  - the June concurrent → sequential decision and the quality gate as the case study, with N stated;
  - the novelty-gate falsification kept as the case study's lesson, and removed as a current mechanism.

### generation_prompt/
- **Documents:**
  - `experiment_log.md`: ~4,900 words, historical. A reconstruction up to 2026-07-08, with a freshness stamp.
  - `validation_plan.md`: ~3,500 words, historical. The pre-registered July tests. The ship test's method has graduated to `eval-hallucination-bench`.
  - `prompt_boundary/experiment_log.md`: historical (June; "prompt = how-to + facts").
  - `prompt_claims_audit/experiment_log.md`: historical (nine-seat; one tactic falsified, one supported).
  - `validation/`: data.
- **Reader question:** what does a seat read at its turn, in what order, what must it output, and which of those choices were tested?
- **Scope and primary sources:** the turn prompt and the output schema. Evidence: `validation/t1c_*` (48% → 30%), the prompt_boundary marker counts, discussion_evidence §6.2, §6.4–6.6 and §7.5.
- **Condition: missing report, warranted.** The decisions are consequential and tested:
  - field order is generation order;
  - all fields are required;
  - reason before act;
  - the board bundle;
  - examples must not name a seat;
  - results wording;
  - the shared-prefix layout.

  No current-state account exists in `evidence/`. `docs/generation_prompt.md` was last touched 2026-07-26, before the shared-prefix layout (`Agents/prompts/layout.py`).
- **Suspected stale mechanisms:** log §0 "as it stands today" is stale.
  - It says flash-lite at temperature 1.0. The seats now run Haiku 5.5.
  - Its private keys `investigator_results` and `vigilante_results` are now `night_actions`.
  - Its output order starts at `strategy_verdicts`. `TurnOutput` in `Agents/schemas/lineup_output.py:78` now starts with `reads`, and discuss adds `claim` and `claimed_night_actions`.
  - As a dated log this is acceptable, but the heading claims currency.
  - `validation_plan.md`'s T4 row cites `Agents/turn/decision.py`, which is gone (historical, fine).
- **Overlap:**
  - `agent_boundaries` §1 covers what is public and private; link to it, do not restate it.
  - The caching evidence covers the layout's cost side.
  - The factual_errors report covers the July test's measurement.
- **Proposed action:**
  1. Write `turn_prompt/report.md` as a reference doc: the layout, the board facts, results wording, the day summary and claim ledger as "the record", the output schema as the decision structure, and the tested choices with N.
  2. Retitle log §0 "The call as of 2026-07-08".

### role_set/
- **Documents:** `experiment_log.md`, ~3,300 words. Historical: the June nine-seat, three-faction casting decision, superseded by `role_sheet.md` (ten seats from twelve roles). Smoke logs and JSONL as data.
- **Reader question:** in a roles report, which roles the game deals and why.
- **Condition: missing report; not warranted alone.** The material belongs in one roles report together with the role sheet, discussion_evidence §8 R1–R7 and §8.1–8.3, and the evil-contest thread.
  - Its reading-guide banner ("PARKED", "no role added", "resume here") reads as current. Add a one-line "superseded 2026-10-07 by the role sheet" note.
- **Suspected stale mechanisms:** the banner is stale, as above. No code check needed for a superseded record.
- **Proposed action:** move the log into `gameplay/roles/` as history. Write `roles/report.md`:
  - the current cast and win logic, from the sheet;
  - why the cast changed, from discussion_evidence §2.5 and §8;
  - the balance batches and the hold, on flash-lite, stated with N;
  - the evil contest (P3 → batch 4 → R11, then the engine covers).

### agent_boundaries/ (boundary check only)
- **Documents:** `report.md`, ~2,900 words, authoritative; it is the style guide's named exemplar. `experiment_log.md`, ~2,300 words, the log. Two smoke logs.
- **Reader question:** how is it guaranteed that each agent's prompt holds only what its role may know?
- **Condition: matches.** One light edit. The report was revised 2026-10-14. Since then the deduction engine reads `SeatView`, built only from the payload (`Agents/deduction/seat_view.py`), and the reasoning_failures report rests its leak argument on this report. §1 should say in one sentence that the engine is a payload consumer and link `deduction/report.md` §1.
- **Suspected stale mechanisms:** none found.
  - `_private_fields` is at `Agents/nodes/day/flow.py:126` and attaches `own_night_actions`.
  - `prompt_log` is in `Agents/turn/eval.py`.
  - Memory namespaces are role-keyed in `Agents/memory/retrieval/accessors.py:26,56`.
  - `tests/leak_test.py` has the eleven `check_*` functions plus `leak_inputs`.
- **Overlap:**
  - discussion_evidence §6.4 (private facts cited as public) is a missing-input problem, not a boundary breach.
  - The turn_prompt report should link here, not restate the public/private table.
- **Proposed action:** keep it at `evidence/agent_boundaries/`, add the one sentence, and link it from the gameplay hub and from `turn_prompt/` and `deduction/`.

## Area-level structure

**Does the grouping hold?** Yes. Every folder here describes what a seat is given, how it takes part in the day, or how it decides, and most of the later work was driven from one problem log (discussion_evidence). Three adjustments:

1. **The purpose leaves out roles.** Phase 3's new cast was a gameplay intervention: discussion_evidence §2.5 names "several imperfect information sources, and a real way for evil to contest them" as its target. Proposed purpose: *How the AI players are given information, take part in the day's discussion and reach decisions, the roles and rules they play under, and how each was investigated and improved; who may know what is defined in `agent_boundaries/`.*
2. **agent_boundaries stays out.** It is a guarantee cited by `evaluation/deterministic_audits` Case 1, by the deduction report and by the write-up map (topic rows 1–5). Absorbing it would create a second account of information access. Link to it instead.
3. **Measurement stays in evaluation.** `evaluation/factual_errors` keeps finding and counting errors. The gameplay hub keeps the interventions. That split is already written into both reports.

**Proposed layout:**

```
evidence/gameplay/
  report.md                 hub: problems → causes → interventions (from game_play_enhancement/report.md)
  discussion_evidence.md    the journey log, whole, with the section index
  turn_prompt/              from generation_prompt/: NEW report.md, experiment_log.md, validation_plan.md,
                            validation/, prompt_boundary/, prompt_claims_audit/
  discussion/               from sequential_discussion/: report.md (rewritten), experiment_log.md, quality_gate/,
                            scripts/, data/
  deduction/                from reasoning_failures/: report.md, deduction_catalogue.md, reviews/ (v1–v3),
                            experiment_log.md, live_e79f21d7/, data/, prompt_versions/;
                            + data/counter_claim_votes/
  roles/                    NEW report.md, role_sheet.md, phase3_wiring_census.md,
                            role_set_2026-06.md (the old log), smoke runs;
                            + data/evil_cover_screen/, evil_cover_games/, phase3_balance*/
  data/                     the rest of game_play_enhancement/data/
evidence/agent_boundaries/  unchanged, linked from gameplay/report.md
```

Moving data folders breaks the paths quoted in READMEs and runner outputs. Move the narrative first. Move data only if the paths in each README are updated in the same commit.

**What not to move:**
- `agent_boundaries/`.
- `evidence/discussion_tagger/`: despite its name, it is the memory-credit instrument.
- `evaluation/factual_errors` and `llm_judge`.
- `model_selection` and `model_admission`: the thinking-budget results are cited from there, not moved.
- Phase 2 steps 6–7 (wire and stage), which belong to frontend docs.
- discussion_evidence itself: do not split it.

**Documents whose placement is unclear:**
- **`data/persona_voice_games/`, `silence_calibration/`, `voice_rewrite/`, `line_echo_check/` and `round_echo_check/`** (2026-10-18). They have no narrative home: discussion_evidence ends at §8.7 (2026-10-16), and the hub's "Silence" stub points only at reasoning_failures R1 and R12. They probably belong to `discussion/`, but the silence ruling and the voices-off decision are recorded only in the READMEs. Someone has to decide which report states them. Resolved in the proposal (§3.1, §3.5): `discussion/report.md` is their one home, written as part of the pilot; the hub's problem 4 links to it.
- **Thinking budget.** discussion_evidence §6.7 (flash-lite) and reasoning_failures log §2 (Haiku) are a decision-quality lever, but the ruling is a model setting. Place the result in the hub (Problem 1, reasoning) and link `model_selection`. Do not give it a component of its own.
- **`validation_plan.md`.** Its method graduated to `evaluation/` (the hallucination bench). Its decision, shipping the board bundle, belongs to turn_prompt. Keep it in turn_prompt as a dated record, with a one-line "graduated to `evaluation/`" note, per the CLAUDE.md lifecycle rule.
- **`live_e79f21d7/review.md`.** It covers claim safety and repeated result requests, which touch both deduction and discussion. Leave it with deduction unless the discussion report needs it.
