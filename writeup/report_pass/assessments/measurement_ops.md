# Assessment: measurement and operations

Folders: `evidence/metrics/` (+ `design/`, `metrics_audit/`), `evidence/model_drift/`, `evidence/tracing/`
(+ `fingerprinting/`, `implementation_notes/`), `evidence/model_selection/`, `evidence/refactor/`,
`evidence/cross_project_synthesis/`. Code spot-checks were run against the working tree on
`feature-frontend-v1`, 2026-10-25.

## Summary table

| Folder / document | Editorial condition | Structural recommendation | Main issue | Proposed action |
|---|---|---|---|---|
| `tracing/report.md` | rewrite | keep | Describes only the batch runner (June 2026). It says nothing of served games, which today leave a different record: replay events, prompt captures and LangGraph checkpoints in Postgres, and eval cases that exist only in Langfuse. Several names are stale | Rewrite approach-first around the two run paths (batch and served); cut §4 to verdict plus pointer; move the SDK internals in §2.1 to the log |
| `tracing/fingerprinting/report.md` | light edit | keep | Gap list (audited 2026-07-23) understates today's gaps: `prompts/roles/` is unhashed, the Claude default is mislabelled as `google`/`vertex`, and served games carry no fingerprint | Re-verify and update §1, §2, §3.2, §3.3, §4, §7, §9 against the code |
| `tracing/fingerprinting/experiment_log.md` | matches (log) | keep | — | None |
| `tracing/implementation_notes/` (log, ISSUE, explained, smoke logs) | n/a (log material) | merge the ISSUE record and its plain companion into the folder log | The same 422 incident is told three times (ISSUE, explained, report §4) | One chronological log for tracing; report §4 points at it |
| `metrics/report.md` | rewrite | keep as the nine-seat design record that `evaluation/metrics/` already names it as (relocation under `evaluation/metrics/` optional) | Titled "how it works today", but it describes the nine-seat basket and the June win-check gate. The ten-seat game scores through `ten_seat_metrics.py` and trusts rules first; §5 and §7 (credit, tagger) are superseded twice | Rewrite as a dated decision record of how the nine-seat basket was chosen; replace §5 and §7 with pointers; drop the "today" framing |
| `metrics/README.md` | light edit | keep | "Status per basket (verbatim)" no longer matches `evaluation/metrics/report.md`; stale test paths | Update the map rows and status lines, or cut the status block to a pointer |
| `metrics/candidate_ledger.md`, `proxy_win_monotonicity.md`, `design/*.md`, `metrics_audit/*` | historical, sound as records | keep | Stale code pointers (moved runners) | Fix pointers only |
| `model_drift/drift_surfaces_and_guards.md` | missing report (one design note); light edit for one violation | merge into `evaluation/experimental_controls/` as a dated record | Its "Internal-variation audit" concludes "endpoint drift by elimination", which states drift as established; most of the note is restated in `experimental_controls` §1 and §3 | Rescope that conclusion to suspected drift; move the note beside `variance_reduction_levers.md` |
| `model_selection/report.md` | light edit | relocate to `evaluation/model_admission/` as a dated record | "Current selection (2026-07-26)" names Gemini 3.5 flash-lite; the default is now Claude Haiku 5.5 | Re-head as the July 2026 nine-seat choice, with a one-line pointer to model_admission |
| `refactor/` (3 decision records) | missing report (not warranted) | keep | `node_factory_pattern.md` describes files that no longer exist; `eval_architecture_convention.md` §4 (freeze) was overruled by the owner on 2026-10-23, but `CLAUDE.md` still states the freeze | Add a dated status line to each; leave the freeze conflict to the owner |
| `cross_project_synthesis/` (README + 2 lessons) | missing report (not warranted) | relocate to `writeup/` | It is write-up drafting material (draft paragraphs, "where it goes in the write-up"), not an evidence record | Move it; fix one stale "Live: not yet" line |

## Per folder

### tracing/

- **Documents:**
  - `report.md`, ~5,700 words. Authoritative in intent but partly stale.
  - `fingerprinting/report.md`, ~2,300 words. Authoritative, needs re-verifying.
  - `fingerprinting/experiment_log.md`, ~2,000 words. Historical log.
  - `implementation_notes/experiment_log.md`, ~1,400 words. Historical log (Phase A#3 night coverage and
    the 2026-06-06 sufficiency audit).
  - `implementation_notes/ISSUE_frozen_set_fetch.md`, ~1,400 words. Historical: a resolved incident.
  - `implementation_notes/frozen_set_fetch_explained.md`, ~870 words. Historical: a plain retelling of
    the same incident.
  - `smoke_*.log` files: raw data.
- **Reader question:** what does each game run leave behind for evaluation, where is it stored, and
  which store is the source of truth for building test sets?
- **Scope and primary sources:** the capture contract (four case types, two sinks, frozen sets), the
  Langfuse wiring, provenance stamping, and the 422 incident. Evidence: `implementation_notes/`. Code:
  `Agents/observability/`, `Agents/tracing.py`, `Agents/main.py`, `Agents/schemas/evaluation.py`,
  `evaluation/src/data/`.
- **Condition (rewrite).**
  - **The design is only half described.** §1 states the contract as "each game run produces, in one
    Langfuse trace…" plus a local sidecar. That holds for `run_batch` only. A served game follows
    different rules today:
    - It opens one trace per run of its task, so a game resumed after a restart is two traces in one
      session (`server/game/game_session.py` ~L336–360).
    - It creates an `EvalCaseSink` (L277) but never writes it out. Nothing in `server/` reads
      `.records`, so a served game's eval cases exist only inside Langfuse spans.
    - Its durable records sit elsewhere: the replay events, which `evaluation/src/data/sources/replay_api.py`
      rebuilds into batch-record shape; a gzip prompt capture in `prompt_captures`
      (`server/storage/prompt_captures.py`, written by `_save_capture`); LangGraph checkpoints in Postgres
      (`server/graph_runtime.py`, `AsyncPostgresSaver`, keyed by game id); and `extraction_input` for the
      offline extraction job.
  - **The headline rule now has exceptions.** The rule "the tracer is the secondary archive" (§1, §4,
    Key decisions) has two live exceptions the report never mentions. Stage fit
    (`evaluation/experiments/stage_fit.py`, 2026-10-24) reads served games' Langfuse spans for event
    timing. And served eval cases live in Langfuse alone.
  - **Prose.** It is a reference doc in the right order (orientation, contract, mechanism, verification,
    case study), but dense: em-dash chains in most paragraphs, stacked modifiers ("frozen,
    self-describing", "drift-evident"), and a two-page SDK walk-through in §2.1 (the "label-printer"
    analogy, `resource_manager.py:453` anchors) that belongs in the log.
  - **Duplication.** §4 retells the 422 incident in full, which the ISSUE file and the explained file
    already do.
- **Suspected stale mechanisms:**
  - §2.1 "`build_game_config()` hands LangGraph a fresh `CallbackHandler`": that function is gone.
    `Agents/main.py` L96–100 calls `build_runnable_config(run, callbacks=[create_langfuse_handler()],
    metadata={"runtime_fingerprint": …})`.
  - §2.1, §2.7: "the same config also tucks the full `runtime_fingerprint()` into the trace's metadata".
    True for the batch path only. The server calls `build_runnable_config(run)` with no metadata
    (`game_session.py` L270), and its trace metadata holds model / byok / recovered, with no fingerprint
    and no `push_scores_to_langfuse`.
  - §2.5 and §2.6 cite `evaluation/src/data/langfuse.py`. It is now `evaluation/src/data/sources/langfuse.py`
    (beside `sidecar.py`, `batch_records.py` and `replay_api.py`).
  - §2.3 lists the `EvalPrivateContext` fields as of June. The schema now also has `night_actions`,
    `dead_roster` and `cast_role_counts` (`Agents/schemas/evaluation.py` L29–52), and its investigator and
    vigilante fields are the nine-seat roles.
  - §5, wolf-night gap ("open, verified 2026-06-27"): still plausibly open. `freeze_case` is called from
    `turn/pipeline.py`, `nodes/day/flow.py`, `nodes/orchestrator.py` and dedup, but not from
    `nodes/night/pack.py`. Re-date it.
  - §2.7 says the 96.7%→73.3% swing was "not from sampling noise but a quiet store/namespace change".
    This is stated more strongly than its source supports: `memory_system/effectiveness/report.md` (~L127–133)
    says two variables changed at once and draws no causal conclusion.
  - Checked and current: the Langfuse 3.14.6 pin (`server/requirements-server.txt`), the `LANGFUSE_RELEASE`
    setdefault before `get_client()` (`Agents/tracing.py`), the span-name single source
    (`Agents/observability/span_names.py`), `push_scores_to_langfuse` with the `dnu_` prefix
    (`Agents/compute_metrics.py` L742–755).
- **Overlap:**
  - `evaluation/README.md` "Data plane" and `evaluation/source_map.md` (the data flow).
  - `agent_boundaries/report.md` §3, §5 (prompt captures and the leak audit; `server/README.md` points
    there, not here).
  - §2.7 and `fingerprinting/report.md` (the provenance terms are described twice).
  - `evaluation/experimental_controls/report.md` §1 and §5 use the fingerprint and the manifests.
- **Proposed action:**
  - Rewrite §1–2 approach-first as "two run paths, what each records, which store a builder reads". Add a
    short served-game section (replay events, prompt capture, checkpoints, Langfuse-only cases).
  - Keep the vocabulary to the terms used.
  - Reduce §2.7 to a pointer to `fingerprinting/`.
  - Cut §4 to its verdict paragraph and lessons.
  - Move the §2.1 SDK internals and the §4 forensics to a single tracing log.

### tracing/fingerprinting/

- **Documents:** `report.md` (~2,300 words, authoritative); `experiment_log.md` (~2,000 words, historical,
  in the journey-log genre).
- **Reader question:** for any result, how do I tell which code, prompts and model produced it, and
  what can that record not prove?
- **Scope and primary sources:** `RunConfig`, `runtime_fingerprint`, artifact manifests. Code:
  `Agents/run_fingerprint.py`, `evaluation/src/core/manifest.py`.
- **Condition (light edit).** The structure is close to the exemplars: a three-line mental model, the
  contract, the mechanism, what it can and cannot prove, and verification. The prose is plain. The
  problems are currency only:
  - §9's severity labels and the "verified open 2026-07-23" stamps predate the ten-seat roles and the
    move to Claude.
  - §8 ("Maintenance guide") and §10 (target pseudocode) are reasonable, but §10 restates §8.
- **Suspected stale mechanisms:**
  - §3.2 and §9 name only `extraction/` and `memory/` as unhashed nested packages. `Agents/prompts/roles/`
    (13 files, the ten-seat role instructions) and `prompts/goldens/` are also outside
    `_PROMPTS_DIR.glob("*.py")` (`run_fingerprint.py` L78). The gap now covers most role-specific prompt
    text.
  - §3.3 says the backend gap is "NIM and Mistral". Today `DEFAULT_GAME_MODEL = "anthropic/claude-haiku-5-5"`
    (`Agents/llm_factory/accessors.py` L24), but `llm_backend` still resolves only `vertex`/`google`, and
    model fields read `GOOGLE_GENAI_*` variables. A Claude game is labelled with a Google backend. The
    rescue/fallback model and per-game server selection (`GAME_LLM`, BYOK) are not recorded.
  - §2 ("Langfuse receives the fingerprint through metadata") holds for the batch path only; served games
    carry none (see tracing above).
  - §4 says "`Agents.tracing.build_game_config()` remains as a compatibility wrapper". It no longer exists.
  - §7 test paths: these now sit in `tests/engine/` and `tests/evaluation/`
    (e.g. `tests/engine/test_run_config_contract.py`).
- **Overlap:** `evaluation/experimental_controls/report.md` §1 ("fingerprint check within a run") and §5
  (manifests) describe how the mechanism is used. That is a distinct angle, and it already cites this
  report as the contract. Not a merge.
- **Proposed action:** re-verify §9 item by item; update §2, §3.2, §3.3, §4, §7. Replace severity labels
  with the consequence (the style guide's rule for reader-facing reports).

### tracing/implementation_notes/

- **Documents:** see tracing above. All historical.
- **Condition:** log material; no report expected. `ISSUE_frozen_set_fetch.md` and
  `frozen_set_fetch_explained.md` tell the same incident in two registers. The explained file's
  "Generalizable pattern" duplicates the report's §4 lessons.
- **Proposed action:** fold both into one tracing `experiment_log.md` in date order, with the
  sufficiency-audit and Phase A#3 entries. Keep the smoke logs as data.

### metrics/

- **Documents:**
  - `README.md`, ~600 words. Folder map; partly stale.
  - `report.md`, ~6,800 words. Historical, though it presents itself as current.
  - `experiment_log.md`, ~4,700 words. Historical journey, with a supersession banner.
  - `candidate_ledger.md`, ~3,100 words. Historical: the full field of 48 candidates; authoritative as a
    record.
  - `proxy_win_monotonicity.md`, ~940 words. Historical, dated 2026-06-11.
  - `design/town_metric_refinement.md`, `deceiver_metric_refinement.md`, `score_tier_design.md`,
    `discussion_scoring_plan.md`, ~620–1,200 words each. Historical design notes. `score_tier_design` is
    still unbuilt: no `GameScore` class exists in `Agents/` or `evaluation/`.
  - `metrics_audit/proxy_discovery_log.md` (~4,300 words) and `scheduler_bias_log.md` (~6,200 words).
    Historical journey logs.
  - `metrics_audit/data/`: data.
- **Reader question:** how was the nine-seat score basket chosen, and why were those 11 scores kept out
  of 48?
- **Scope and primary sources:** the June–July 2026 nine-seat proxy design and its two validation
  campaigns (N=50/30, N=180). Evidence: `proxy_win_monotonicity.md`, `metrics_audit/data/*.json`,
  `candidate_ledger.md`.
- **Condition (rewrite).**
  - **It claims to be current and is not.** The title and orientation say "how it works today" and "the
    ruler the whole eval rests on". §1 says "a proxy is trusted only after it is shown to track its own
    faction's win". The authoritative page (`evaluation/metrics/report.md`, "How the approach changed")
    now records that the ten-seat game trusts the rules first and uses the win check as support (owner
    ruling 2026-10-24). A reader of this report gets the retired policy as today's.
  - **It is nine-seat only.** It never says that ten-seat games score through `Agents/ten_seat_metrics.py`,
    whose module docstring says none of its scores pushes as "validated".
  - **Two of its sections are superseded, one twice.** §5 and §7 (the tagger family and v7 credit) each
    open with a 2026-07-11 "superseded, wiring pending" banner. Credit has since graduated to
    `Agents/memory/consolidation/`, and v7 closed negative. Those sections describe a design twice
    removed.
  - **Prose.** Long single-clause paragraphs, many em-dashes, and the in-house term "de-lucked", glossed
    only in §1.
  - The §2 and §3 content itself (basket, constructs, tiers) is a sound record of a historical decision,
    and `evaluation/metrics/report.md` §3 already summarises it plainly.
- **Suspected stale mechanisms:**
  - §2 cites `compute_metrics.py` "line 622" and §3 "line 642" / "line 612". The frozensets are now at
    L688 (`DO_NOT_USE`), L698 (`VALIDATED_BASKET`) and L718 (`DIAGNOSTIC`).
  - §6 says "63 fields". The schema has since gained the ten-seat role fields (`Agents/schemas/metrics.py`
    ~L299), and `compute_game_metrics` now merges `ten_seat_metrics` (L612–625).
  - §7 and §9 point credit at `evaluation/src/loop/{credit,credit_backfill,decision_scoring}.py`. The live
    path is `Agents/memory/consolidation/{credit,grading,decision_scoring}.py`.
  - §9 and the README cite `tests/test_metrics_audit_proxies.py` etc. These now sit in `tests/evaluation/`
    and `tests/engine/`.
  - `proxy_win_monotonicity.md` L13–14 still gives `poetry run python evidence/metrics/proxy_win_monotonicity.py`.
    `metrics_audit/data/README.md` cites `evaluation/src/experiments/proxy_rescue.py`. Both moved to
    `evaluation/src/instrument_validation/proxies/`.
- **Constraint check:** the retracted "+17pp p=0.013" figure does not appear. But §2 (L102) and
  `candidate_ledger.md` (L43, L50) refer to "the static-memory proof". Given the retraction and the v6
  non-replication, "proof" states more than the record supports. Flag it for rewording; it is not a
  number to fix.
- **Overlap:**
  - `evaluation/metrics/report.md` §3 restates this report's §2–3 verdicts.
  - `evaluation/metrics/experiment_log.md` Part A summarises `experiment_log.md` and `metrics_audit/`.
  - §5 overlaps `discussion_tagger/` and `evaluation/llm_judge/discussion_tagger.md`.
  - §7 overlaps `credit/report.md`.
  - `metrics_audit/scheduler_bias_log.md` overlaps `sequential_discussion/` and
    `evaluation/deterministic_audits` (the speaking-order audit, log §3a).
- **Proposed action:**
  - Rewrite `report.md` as a dated decision record ("How the nine-seat basket was chosen, June–July
    2026"): the tension (the win is luck-heavy), the method (grade, normalise, check against win), the
    48→11 selection, the constructs rule, and why the policy later changed (one paragraph pointing to
    `evaluation/metrics/`).
  - Replace §5 and §7 with one-line pointers to `credit/` and `discussion_tagger/`.
  - Keep §8 only as dated history, or drop it.
  - Fix the code pointers in the README and the data README.

### model_drift/

- **Documents:** `drift_surfaces_and_guards.md` (~1,400 words). It explains historical decisions (the
  interleave rule, the embedding canary) and holds a historical audit.
- **Reader question:** which components can a provider change underneath us, and what guards each one?
- **Scope and primary sources:** the June 2026 Gemini-era drift map, the internal-variation audit, and
  the variance constants. Evidence lives in `memory_system/effectiveness/paired_ab/experiment_log.md`.
  The 2026-10-25 correction cites `evaluation/experiments/june_baseline_shift_check.py`.
- **Condition:** no report. One is not warranted: the authoritative account of drift controls is now
  `evaluation/experimental_controls/report.md` §1 and §3. The note needs one fix:
  - **Constraint violation.** The correction added 2026-10-25 rescopes the 67%→27% shift. But the
    "Internal-variation audit" section (L84–101) still concludes "the Jun-12 shift has **no surviving
    internal explanation** — endpoint drift by elimination, not by assumption". That asserts drift as
    established, which the area's rule forbids. A shifted baseline can be named as suspected provider
    drift only.
  - **Guards now built.** The embedding canary (`evaluation/src/audits/embedding_canary.py`) and the
    embedding id in the fingerprint now exist. The note still lists them as near-term guards ("verify
    it's there"). The run_batch interleave TODO and the dirty-file-list gap are still open, per
    `experimental_controls` §1 and `run_fingerprint.py`.
- **Suspected stale mechanisms:** see the guards above. The Gemini flash-lite pinning context is
  historical; current pinning per provider is in `experimental_controls` §1.
- **Overlap:**
  - The interleave and never-compare-historical rule: `experimental_controls` §1.
  - The variance constants (seed sd 0.249 vs 0.211–0.262; MDE 0.18 vote accuracy / 36pp win at N=30):
    `experimental_controls` §3 and `variance_reduction_levers.md`.
  - The embedding exposure: `experimental_controls` §1 and `deterministic_audits` Case 5.
- **Proposed action:** reword the L99–101 conclusion to "no internal explanation was found; provider
  drift is suspected, not established". Then move the note into `evaluation/experimental_controls/` as a
  dated record beside `variance_reduction_levers.md` (which set the precedent on 2026-07-07). Update the
  link in `experimental_controls` §1.

### model_selection/

- **Documents:** `report.md` (~1,400 words). Explains a historical decision (the July 2026 seat model,
  nine-seat).
- **Reader question:** how was the seat model chosen in July 2026, and what does that teach about
  choosing models (measure on the game; public benchmarks only shortlist)?
- **Scope and primary sources:** single measured HITL games per model, unblinded owner reads, and
  EQ-Bench priors. Sources: Langfuse usage, prices entered 2026-07-26.
- **Condition (light edit).**
  - The scope note already states N and blinding plainly ("1–2 full games per model … not a blind eval";
    "single-game measurements with game length varying ±2×"). The tables are interpreted.
  - **Stale heading.** "Current selection (2026-07-26)" presents Gemini 3.5 flash-lite as the production
    default. The default is now Claude Haiku 5.5 (`accessors.py` L24). `evaluation/model_admission/report.md`
    already treats this file as "the July 2026 seat-model choice".
  - **One overstated phrase.** "v4-pro … Clearly the strongest table" rests on 1–2 unblinded games.
    "Strongest in the owner's reads" is what the sample supports.
- **Suspected stale mechanisms:** none in code. The selection table is the stale part.
- **Overlap:** `evaluation/model_admission/report.md` §1 ("Earlier and lighter choices") summarises it and
  keeps its method note.
- **Proposed action:** re-head §"Current selection" as "July 2026 selection (nine-seat; superseded)" with
  a one-line pointer to model_admission. Move the file to `evaluation/model_admission/` as a dated record.

### refactor/

- **Documents:**
  - `structure_audit.md`, ~1,800 words. Historical (2026-06-06 repo map and test-gap scoping). The folders
    it maps (`eval_sets/`, `eval_configs/`, `configs/eval/`) and the flat `Agents/` layout are gone.
  - `eval_architecture_convention.md`, ~1,350 words. A decision record. Authoritative for the
    code/record/data split; its §4 "freeze" decision is superseded.
  - `node_factory_pattern.md`, ~900 words. Historical: the files it describes (`nodes/night/factory.py`,
    `night/healer.py`, `engine/actions.py`) no longer exist. `Agents/nodes/night/` now holds `pack.py`,
    `solo.py` and `resolution.py`.
- **Reader question:** how was the codebase reorganised, and on what principles (evaluation code vs
  evidence record; behaviour-neutral refactors verified by fingerprint)?
- **Condition:** no report, and none is warranted. These are three independent decision records, already
  named as the decision-record exemplars in the style guide.
  - `eval_architecture_convention.md` §4 ("freeze the existing archive") conflicts with the owner's
    2026-10-23 ruling that evidence is no longer frozen. `CLAUDE.md` ("Existing `evidence/`: FREEZE")
    still carries the old rule. The owner must decide which text changes; this assessment does not
    resolve it.
  - §2 and §7 call the provenance manifest "the data-plane reorg's Wave 2 … until it lands". It has
    landed (`evaluation/src/core/manifest.py`).
- **Suspected stale mechanisms:** listed above.
- **Overlap:** `eval_architecture_convention.md` restates `CLAUDE.md` "Eval Architecture" and
  `evaluation/README.md`. That is acceptable: the record holds the reasoning, `CLAUDE.md` the rule.
- **Proposed action:** add a one-line dated status under each title: superseded layout
  (`structure_audit`); describes the pre-role-registry night nodes (`node_factory_pattern`); manifest
  landed, freeze decision under review (`eval_architecture_convention`). No rewrite.

### cross_project_synthesis/

- **Documents:** `README.md` (~660 words, an index and a candidate list); `deterministic_where_reliable.md`
  (~1,760 words); `separating_generation_from_checking.md` (~1,250 words). Each lesson file ends in a
  draft paragraph for the write-up.
- **Reader question:** which engineering judgments recur across subsystems, with the evidence for each
  instance?
- **Condition:** no report, and none is warranted. These are write-up staging documents: the README says
  each file "drafts the paragraph the write-up's engineering-lessons section will use". The instances
  are well sourced and kept apart, and they state "Not fixed" and "Live" for each instance.
- **Suspected stale mechanisms:**
  - `deterministic_where_reliable.md` §8: "**Live.** Not yet: uncommitted on 2026-10-14". This was
    committed in `94304a22`; `tests/leak_test.py` `check_eliminated_players_excluded` reads the dead
    roster.
  - Checked and present: `Agents/turn/echo_gate.py`, `Agents/memory/extraction/dehalo.py`,
    `Agents/rules/claim_ledger.py`, `Agents/rules/night_record.py`, `night_one_lot`
    (`prompt_inputs.py` L157). Line anchors such as `echo_gate.py:70-109` were not re-checked.
- **Constraint check:** the v8 references describe credit on 7 gate games with "no play benefit measured".
  That does not call v8 negative. Compliant.
- **Overlap:** `deterministic_where_reliable.md` §7 (credit) and `deterministic_audits` Case 3 touch the
  same grading rule from different sides (runtime design vs an evaluation check). They are distinct, so
  no merge. The README's "Grade the decision, not the result" candidate points at `metrics/`.
- **Proposed action:** move the folder to `writeup/` (e.g. `writeup/lessons/`) and fix §8's status line.

## Area-level structure

**This is not one topic.** The six folders fall into three groups. Each is better placed by the
intervention it records than gathered under "measurement and operations".

1. **Records that belong beside the evaluation method pages they feed:**
   - `metrics/` is, by its own README (2026-10-24), the design record behind
     `evaluation/metrics/report.md`.
   - `model_drift/` is the origin record of the controls in `evaluation/experimental_controls/`.
   - `model_selection/` is the earliest model choice that `evaluation/model_admission/` already cites.

   Recommended:
   - `model_drift/drift_surfaces_and_guards.md` → `evaluation/experimental_controls/` (dated record).
   - `model_selection/report.md` → `evaluation/model_admission/` (dated record).
   - `metrics/` → either keep in place (the evaluation pages link to `../../metrics/`, and the
     link churn is the cost) or relocate whole to `evaluation/metrics/nine_seat_design/`. Recommend
     keeping it in place until the report rewrite; relocating is optional and low value.
2. **Engineering infrastructure:** `tracing/` (capture, provenance, incident log) and `refactor/` (code
   layout decisions). If grouped, one folder `evidence/infrastructure/` with the purpose "how runs are
   recorded and how the codebase is organised so results stay traceable", laid out as:
   - `infrastructure/tracing/report.md` + `experiment_log.md` (implementation_notes merged)
   - `infrastructure/tracing/fingerprinting/` (unchanged)
   - `infrastructure/refactor/` (three decision records)

   Grouping is optional. The two can stay as they are without loss.
3. **Write-up material:** `cross_project_synthesis/` → `writeup/`.

**What I would not move:**
- `tracing/fingerprinting/` stays with tracing, not with `experimental_controls`. It is the mechanism,
  and the controls page already links to it as the contract.
- `metrics_audit/` stays with the metrics design record, even though `scheduler_bias_log.md` is about
  the discussion scheduler. Its question was whether metric nulls were scheduler artifacts.
- `candidate_ledger.md` and `proxy_win_monotonicity.md` stay with `metrics/`.

**Placement unclear:**
- `metrics_audit/scheduler_bias_log.md`: by intervention it could sit in `sequential_discussion/`.
  `evaluation/deterministic_audits` (log §3a) already catalogues its result.
- The variance constants in `model_drift` (seed vs gameplay variance, minimum detectable effects) are A/B
  power methodology rather than drift. If the note is split rather than moved whole, they belong in
  `experimental_controls/variance_reduction_levers.md`.
- The served-game record (prompt captures, checkpoints, replay events) is today described only in
  `server/README.md` and `agent_boundaries/`. The tracing rewrite should own the "what a run leaves
  behind" view and point to `agent_boundaries` for the leak audit's use of the captures.

**Known-constraint findings in this area:**
- One violation: `model_drift` L99–101 ("endpoint drift by elimination").
- One wording risk: "the static-memory proof" in `metrics/report.md` §2 and `candidate_ledger.md`.
- No "+17pp p=0.013", no 0.14%, no v8-negative claim found (grep over all six folders).
- v7 is described as a credit consumer, not as a positive result.
