# Replay screens: the working record

*This is the full trust write-up as it stood on 2026-10-23, kept whole: every screen's or read's
mechanism, numbers, corrections and code paths. The plain summary is [report.md](report.md), written
2026-10-24 from this text. Since then, the Haiku vote replay's runners, config and data were committed (`516318c9`, 2026-10-24), so the "untracked" notes below are out of date.*

*Widened 2026-10-23 to every frozen-turn replay in the project, for memory and for play. The first
version (2026-07-02) covered only the memory decision-replay screen and the per-day replay design.
Those two sections are kept below as the record of how the instrument was built. Where a line is now
wrong, a dated correction sits next to it.*

**What this page covers.** Replays of single moments from recorded games. A *frozen-turn replay*
takes one recorded decision, such as a vote, a spoken line, a night choice or a memory lookup. It
rebuilds that moment from the game record and runs it again with exactly one thing changed: the
memory block, the memory store, a prompt sentence, a line from the deduction engine, or a card's
text. Everything else stays as recorded. A typical October screen cost from under $0.01 to about $0.25. For
comparison, one 30-game arm of whole games cost about $15–30 in June (nine-seat, Gemini flash-lite), and
one ten-seat game on Haiku 5.5 costs about $0.08–0.26.

There are four groups:

1. **Memory replays** (nine-seat game, June–July 2026, plus one ten-seat replay from October 2026).
   At one frozen moment, does memory change the decision, and which way?
2. **Play replays** (mostly ten-seat, October 2026). Does a prompt sentence, a card's text or a
   choice of wording fix a failure seen in a live game, without breaking the turns that were right?
3. **Deduction-engine replays** (ten-seat, October 2026). The deduction engine is code that writes
   conclusions into each player's prompt. Does one of its lines change what a seat says or how it
   votes?
4. **The per-day replay** (design only, 2026-07-02). Could we re-run a whole day of a recorded game,
   not just one turn?

This page rates **how far each replay can be trusted**. It does not say what a replay led to, such
as which fix shipped or which idea was dropped. That is answered in the design folders:
[memory decision replay](../../../memory_system/effectiveness/decision_replay/),
[credit blind-spot fix](../../../credit/blindspot_fix/experiment_log.md),
[tell extraction](../../../extraction/tell_extraction/report.md),
[ten-seat memory (v8)](../../../memory_system/v8/experiment_log.md),
[discussion evidence](../../../game_play_enhancement/discussion_evidence.md) and its `data/` folders,
and [reasoning failures](../../../reasoning_failures/experiment_log.md). How all the evaluation reports
fit together: [the hub](../../report.md). The list of every source behind these reports:
[the source map](../../source_map.md).

| Check | Trust | Main limit |
|---|---|---|
| Memory decision-replay screen, nine-seat (Memory replays: the first two parts) | ✅ | Finds direction and cause at one frozen moment; cannot measure size, win rate, or what happens later in the game |
| Night-1 target check (Play replays) | ✅ | Code counts the targets and the effect is large; nine-seat boards and one model only |
| October prompt and engine screens on Haiku 5.5, ten-seat: evil cover, Haiku vote, visit wording, persona line, voice rewrite (Play replays); deduction injection R1, placement and AC2 (Deduction-engine replays) | 🟡 | One case sampled ten times swung from 8 in 10 to 1 in 10 on the same prompt; a frozen transcript hides effects later in the day |
| Stage-filter replay, ten-seat (Memory replays) | 🟡 | One store and 96 lookups; the fit labels come from readers nobody calibrated |
| Checkpoint replay (Memory replays) | 🟡 | Caught the v7 store's harm only on cases from the same games; missed it on older ones; never used for the job it was built for |
| Tell-book screen (Memory replays), private-note screen (Play replays), counter-claim vote screen (Deduction-engine replays) | ⚠️ | Smoke tests only: too few cases, or too noisy, to show more than direction |
| Per-day replay | ⏸ | A design only; still not built |

**Bottom line.** A replay can be trusted for one thing: whether a change reaches a turn, and which
way it pushes. How large the effect is needs many cases or a measured noise floor, and anything that
plays out later in the day needs whole games.

## Objective the apparatus targets

A whole-game paired arm costs ~$15–30 and is exposed to overnight model drift, so it cannot cheaply
answer *why* memory helped or *which* of a dozen candidate fixes is worth building. The replay layer
answers that at a fraction of the cost: freeze one recorded decision, swap only the retrieved-memory
block, regenerate that one action, and score it against the true roles. It is paired at the decision
so role-luck cancels, and it is drift-immune because both arms run in one sitting.

**From October 2026 the same idea carried most of the play-quality work.** The memory research
closed on 2026-07-21. After that, replays tested prompt sentences, deduction-engine lines, card text
and wording on the ten-seat game. A typical October screen cost from under $0.01 to about $0.25, against the
cost of new games. The question also changed: no longer "does memory help?", but "does this change
fix the failure seen in a live game, without breaking the turns that were right?"

## How a frozen-turn replay is built

**Four case sources.** A *case* is one recorded decision point, stored as the state the engine held
just before it.

| Source | What is frozen | Used by |
|---|---|---|
| Batch records (`batch_results/*.jsonl`, nine-seat `EvalCase` rows) | the agent payload at a vote or night action | decision-replay screen, checkpoint replay, tell-book screen |
| LangGraph checkpoints of live games (read-only from the server's Postgres; `haiku_game_turn_cases.day_states`) | the day's state just before a line or a vote | R1 injection, deduction placement and AC2, private-note screen, Haiku vote replay, visit wording |
| Captured prompt logs of AI-only games (`*.capture.json.gz`) | the prompt input each seat received | evil cover screen, counter-claim screen |
| Recorded lookups and lines | a memory search, or a spoken line | stage-filter replay, voice rewrite |

**The prompt comes from the checked-out code, not from the record.** For live-game cases, the
replay half of the hallucination bench (`evaluation/src/replay/hallucination_bench.py`:
`turn_payload`, `turn_template`) rebuilds the payload with the engine's own builders. It then renders
today's template. Engine-written text in an old state, such as ballot lines or the closing call, is
updated to today's wording (`_engine_wording`). Text that players and the summariser wrote stays as it
was. The capture-based screens re-render the seat's deduction blocks from the rebuilt payload. That
rebuild reproduced all 41 captured seat blocks exactly on the evil cover turns
([`evil_cover_screen/README.md`](../../../game_play_enhancement/data/evil_cover_screen/README.md), step 2).

**An arm is a process.** Prompt versions are switches read when the code loads. So each arm runs in
its own process, and usually from its own git worktree on a tag or commit (`visit-wording-baseline`,
`prompt-layout-baseline`, `phase2-baseline`). The shared bench mechanics are written up in
[`../../factual_errors/report.md`](../../factual_errors/report.md).

**Three kinds of measure, and they carry different trust.**
1. **Deterministic.** The vote target or night target is read from a structured field limited to legal
   targets, and scored against the true roles. No judge is involved.
2. **Pattern counts.** A regex over the free-text reads counts what a vote cites. It finds mentions; it
   does not judge whether the reasoning is sound.
3. **Blind reads.** Claude subagents launched from the chat read shuffled samples with the arm hidden,
   against a rubric fixed before the run, and the result is unblinded with a key file. These readers
   are uncalibrated. The packet-and-key method is catalogued in
   [`../../labeling/sampled_reads/report.md`](../../labeling/sampled_reads/report.md).

**Where neighbouring spokes take over.** Replays whose measure is a factual-error count are catalogued
in [`../../factual_errors/report.md`](../../factual_errors/report.md): the July T1b, T1c and T2
replays, the invented-check replay, the summary-claim replay and the Phase 3 and first-Haiku turn
cases. The thinking-effort replay belongs to model choice ([`../../model_admission/`](../../model_admission/)).
Paired whole games on shared deals belong to [`../game/report.md`](../game/report.md).

## What the whole family can and cannot claim

The October screens kept enough records to measure their own noise. Four limits apply to every replay
below.

- **One case sampled ten times shows the spread of answers to one prompt, not ten situations.** The
  same AC2 vote prompt went to the real Healer in 8 of 10 samples on one run and 1 of 10 on the next
  ([`deduction_placement_n10/results.md`](../../../reasoning_failures/data/deduction_placement_n10/results.md)).
  At n = 25 per arm, with all arms shuffled into one schedule, the rate was about one in three in
  every arm ([`deduction_ac2_2x2/results.md`](../../../reasoning_failures/data/deduction_ac2_2x2/results.md)).
  In the Haiku vote replay, adding only true facts to earlier ballots moved single cases from 4 to 9
  and from 6 to 2 of 10. That is more than any effect the replay was testing
  ([`discussion_evidence.md`](../../../game_play_enhancement/discussion_evidence.md) §8.7). The tell-book
  screen's no-book arm scored 18 and then 20 of 40 on the same cases. **What follows:** a difference of
  a few samples on one case is noise. The two habits that addressed this were running the unchanged arm
  twice (the persona line's plain-against-plain baseline) and interleaving all arms in one shuffled
  schedule (the AC2 2×2).
- **A frozen transcript cannot show what a change does later in the day.** The replayed turn inherits
  a discussion that was generated without the change. The checkpoint replay could not reproduce the
  v7 store's abstain cascade, which lived in the discussion. The visit-wording fix could not stop
  replies to a denial that was already in the transcript. The evil cover turns carried notes written
  under the old card. A replay measures the direct effect at one turn; only live games measure the
  trajectory.
- **The exam must come from the same epoch as the change.** An *epoch* here is the combination of
  prompts and model that produced the games. The checkpoint replay drawn from older v6 games showed no
  harm from the v7 store. Drawn from the v7 endpoint games themselves, it put the full store last on
  every readout ([`credit/blindspot_fix/experiment_log.md`](../../../credit/blindspot_fix/experiment_log.md)
  ④, ④b).
- **The record is not always complete under version control.** Several runs used a working tree with
  uncommitted changes. The placement and AC2 READMEs record a hash of that diff; the checkpoint replay
  marks itself `git_dirty`. Some raw samples existed only in the gitignored `evaluation/eval_results/`.
  The ones cited below were copied into the record on 2026-10-23. Each section below states what is kept.

## Memory replays

### L1 — the per-turn decision-replay screen ✅ (nine-seat, June–July 2026)

- **Mechanism.** For a frozen board it regenerates a single action under memory-ON vs memory-OFF and
  scores it deterministically (`hit_threat` against the true roles). Judge-free wherever the target is
  a role lookup; two off-headline judges (adherence, coherence) run only on side probes.
- **What it can claim.** Direction + mechanism only. It sees *local* decision quality at a fixed
  history, never trajectory, magnitude, or win rate. Findings are reported tiered as
  direction-plus-mechanism, and the win-rate headline always stays with the paired A/B. A screen
  p-value is never headlined; per-cell N is small (±5–9pp), so a claim earns its keep two ways, both
  N-robust: the cell-level mechanism decomposition, and convergence with an independent cut.
- **Coverage after the 2026-07-02 fix.** The screen was structurally blind to the deceiver side: wolf
  day-votes were excluded, and the action specs lacked vigilante and serial-killer day-votes. The
  hardening pass added those specs, added a `REPLAYABLE_DECEIVER_ROLES` set plus a deceiver lens
  (`wolf_vote_is_good` = a vote that induces a town mislynch, the mirror of town `hit_threat`), and a
  `--lens {town,wolf}` flag so a wolf/SK run scores on its own win condition. One assumption was
  corrected in place: night-kill replay, listed as an open frontier, was already fully wired — only
  the day-vote side was missing.
- **Two apparatus corrections shipped alongside.** Diverse-case selection was rewritten to round-robin
  across days, removing a day-2-first weighting that early-loaded pooled aggregates; and the lexical
  echo proxy was formally retired (it tracked its judge at only Spearman rho=0.14, and is kept runnable
  only so that invalidation stays reproducible).

### L2 — trust (the screen)

- **✅ Validated as a screen, by convergence.** Built independently of the paired A/B, the two agree:
  town memory helps and deceiver memory is null on *both*. Whole-game (N=30): +17 / +23pp town win,
  wolf/SK null. Per-decision: +0.078 net-value day-2 and +0.117 endgame for town, wolf/SK null. Both
  also contradict an earlier −40pp "town collapse" that later proved to be model drift, not memory —
  the convergence is the validity anchor, not the small per-cell N.

  > **Correction (2026-10-23).** The two whole-game figures are win-rate arms, and neither was
  > significant: +17 points on the raw arm (p = 0.267) and +23 points with everything on (p = 0.167).
  > What the June A/B did establish is better town *decisions* on the raw arm. On 30 paired boards the
  > healer saved the real target 37% → 60% (p = 0.005), and town lynches hit an enemy 47% → 64%
  > (p = 0.028) ([`memory_system/store_progression.md`](../../../memory_system/store_progression.md),
  > correction of 2026-10-22). So the screen converges with June's decision measures, not with a
  > win-rate gain. Both anchors belong to one June epoch. The v6 store did not repeat the town gain
  > (+6 points, p = 0.77), and the July v7 endpoint was 0.147 lower with memory (19 of 30 boards,
  > p ≈ 0.06; [`execution_plan/report.md`](../../../execution_plan/report.md) §5). The screen was
  > validated as a direction-finder on one epoch; it says nothing about whether memory helps today.
- **The cheap-lever ladder screened clean.** Every cheap way to make the agent *use* memory better
  came back null-or-harmful, tier *suggestive*: emitting reasoning before the vote synced
  vote↔reasoning 75%→92.5% (N=40) but moved engagement ≈0 (echo, N=150); a forced per-memory
  "does this apply?" verdict showed the model genuinely *can* reason applicability (N=20) yet *hurt*
  the vote via over-caution (0.75→0.55); outcome framing was situation-dependent.
- **An assumption that flipped, surfaced as a finding.** Outcome framing first read as a clean null
  (pooled N=40, immediate − net = +0.025, p=1.0) — but that sample sat in the day≥3 prompt-ceiling
  zone where memory ≈ no-memory for everything. Stratified, it flips: day-2 info-starved (N=30) shows
  immediate − net = **−0.167** (4 worse / 0 better, p=0.125), the cautious net framing converting
  would-be mislynches into abstains (mislynch 0.23→0.07). This is direction + mechanism at N=30,
  p=0.125 — a **suggestive** claim, not proven; the strata are reported, never pooled to manufacture
  significance.
- **Bounds to state plainly.** Off-policy (a frozen context, one decision, no propagation); small
  per-cell N; a triage tool, not a verdict. Its role is to kill dead levers for ~$1 before any reaches
  a ~$20 powered arm — which is what it did (all cheap levers screened out, graduating the question to
  conditioned-content extraction).
- **Runs on nine-seat records only (noted 2026-10-23).** The screen's replay code
  (`evaluation/src/replay/decision_screen/replay.py`) now builds night turns from ten-seat role
  cards and refuses nine-seat ones. The checkpoint replay, which shares that code, says in its
  docstring that the ten-seat prompts refuse nine-seat villager and wolf turns, so a rerun on those
  records goes through a checkout of the `phase2-baseline` tag.

### Checkpoint replay and the blind-spot replays 🟡 (nine-seat, July 2026)

- **What it is.** A fixed exam of frozen town decisions, re-answered once against each memory store
  in a list. Built 2026-07-05 (`cc005e5e`) to read the v7 learning loop's compounding as a curve:
  an empty store, then each generation's snapshot. Console entry `eval-checkpoint-replay`.
- **How it works.** The board, the visible discussion and the retrieval query are frozen. Per case and
  arm, only the search against that arm's store and the decision call are live. Retrieval is pinned to
  the loop's production read path (top_k 5, three per situation, no reranking or filtering). Votes are
  scored with the town or deceiver lens. Night actions are scored with the loop's own credit lens
  (`_night_credit`, imported from `loop/credit_backfill.py`, not copied). Two traps are designed out.
  Drift is handled by running every arm in one process and one day, case by case, so time cannot line
  up with the store. Leakage is handled by a guard that refuses to run if an exam game appears in a
  store's provenance.
- **What it was used for.** It never ran on generation snapshots. The compounding test was redesigned
  as a final-store against no-memory A/B (`execution_plan/report.md` §3). Its only recorded runs are
  three sweeps on 2026-07-21 for the credit blind-spot fix, which compared four or five stores: empty,
  the full 168-point store, and pruned or re-synthesised variants.
- **How far it was checked.** This is the replay's most informative trust result.
  - On 100 held-out cases from the older v6 games, every arm scored within a few points of the others.
    The fixed-pruned store tied the full store at 7 helped and 7 hurt (p = 1.0). The full store's live
    deficit of about 15 points in threat hits showed as 4 points here. The record reads this as an
    instrument limit, not an exoneration: those cases carry a discussion generated without the
    store's advice, so the conditions the harmful lessons respond to were mostly absent.
  - On 100 cases from the v7 endpoint games themselves (zero game overlap with the store's 40 source
    games, checked in the log), the full store came last on every readout. Its mean decision value was
    +0.04 against +0.13 for an empty store, and it voted for a town player 46% of the time against 36%.
    This agrees in direction with the live endpoint A/B. The differences rest on 2 to 6 discordant
    pairs per comparison (McNemar p 0.5–1.0), so they are direction only.
  - The live harm's abstain half did not appear at all: abstains were 12–18% here against 31% live.
    The record attributes that half to the trajectory, which a frozen turn cannot show.
- **Known gaps.** The leakage guard reads source game ids from the stores, and synthesised strategy
  points carry none. Every SP-only arm recorded `n_source_games: 0`, so the guard had nothing to
  compare, and the overlap check was done by hand. The manifest records the commit (`a010dc6`, marked
  dirty), the case-set hash and the retrieval settings, but not the model. The summary file labels
  every comparison "gen-final vs gen-1", whatever the arms; the log notes this.
- **Code and record.** `evaluation/src/replay/decision_screen/checkpoint_replay.py`;
  [`credit/blindspot_fix/experiment_log.md`](../../../credit/blindspot_fix/experiment_log.md) ④–④d,
  sweeps in `replay/`, `replay_onepoch/`, `replay_obs/`, stores in `replay_arms/`.

### Tell-book screen ⚠️ (nine-seat, July 2026)

- **What it is.** A check that the *tell book* reaches decisions at all. The tell book is a short
  prompt block of public behaviours that hint at a hidden role.
- **How it works.** Forty recorded day votes from the older v6 games are replayed twice on a bare
  memory block, once with the book switched on (`WW_TELL_BOOK`) and once without. The replay goes
  through the live injection path. A vote is correct if a town player votes for an evil one, or an
  evil player for a town one. Before replaying, the screen rebuilds the role counts and dead roster
  that these old cases lack, because the book's filter needs them.
- **What it can claim.** That the channel reaches decisions, and nothing about benefit. Run 1 changed
  7 of 40 votes, with correct votes going from 18 to 17. That book turned out to hold no vote
  behaviours. Run 2, with slots reserved per role and channel, changed 11 of 40, and correct votes went
  from 20 to 24 (5 wrong to right, 1 right to wrong; one-sided p ≈ 0.11).
- **How far it was checked.** The no-book arm moved from 18 to 20 between runs on the same cases. So
  the two runs cannot separate the effect of balancing from noise, which the log says itself. The
  34-entry book was never replayed. The rows do not record the model.
- **Code and record.** `evaluation/src/replay/decision_screen/tell_book_screen.py`;
  [`extraction/tell_extraction/experiment_log.md`](../../../extraction/tell_extraction/experiment_log.md)
  ⑫; `outputs/book_screen.json`, `outputs/book_screen_v2_balanced.json`.

### Stage-filter replay 🟡 (ten-seat, October 2026)

- **What it is.** A replay of memory *retrieval* only. No decision is regenerated. It asks whether
  leaving out lessons learned at a different stage of the game improves what a seat is shown.
- **How it works.** The v8 gate's 96 read lookups are searched again from the situation text each
  seat wrote, with one embedding call per lookup. A lesson is dropped when its stored board differs
  from the seat's on the alive bucket (8+, 5–7, 4 or fewer), on whether the pack has lost a partner,
  or on whether a limited ability has uses left. This uses the live filter's own test
  (`dimension_gating.stage_mismatch`). The fit of each lesson comes from a rubric read: the gate's
  earlier read, plus one Sonnet subagent for the 28 newly promoted lessons.
- **What it can claim.** How a filter changes the lessons shown, on one store and 96 lookups. Fit rose
  from 15% of 264 lessons shown to 25% of 114, at the cost of 25 empty lookups.
- **How far it was checked.** The unfiltered top three reproduced what the seats were actually shown
  in 91 of 96 lookups. That is the replay's fidelity check. Separately, 165 of 196 stored use counts
  matched the engine's spending rule exactly (84%). The fit labels come from uncalibrated readers.
  2026-10-13 rerun the lookups on the 40-game store (`--store`).
- **Code and record.** `evaluation/experiments/v8_stage_filter_replay.py`;
  [`memory_system/v8/experiment_log.md`](../../../memory_system/v8/experiment_log.md) (2026-10-12, the
  gate part two; the 40-game fit section); `data/gate/stage_filter/`, `data/gate/stage_filter_40games/`.

## Play replays

### Night-1 target check ✅ (nine-seat, October 2026)

- **What it is.** A count of where the investigator, healer and serial killer aim on night 1, when
  nothing in the record points anywhere.
- **How it works.** Night 1 is replayed on 32 recorded boards (the roles of the 28 June games and the
  four Phase 2 step-8 games), through the real prompts and `run_agent`, on `gemini-3.5-flash-lite`.
  That is one call per board, role and arm, or 96 per arm. The target is a structured field, so no
  judge is used.
- **What it can claim.** Which seat an unguided night-1 choice falls on. Without help, seat 1 took 78
  of 96 actions, and on 16 of 32 boards the check, the protection and the kill all fell on one player.
  With a lot drawn by the engine and offered in the prompt, the agents took it in 95 of 96 calls, and
  every seat received 6 to 16 actions.
- **How far it was checked.** It falsified the first fix before any game ran. Shuffling the player
  lists left the target on the lowest-numbered other seat in 95 of 96 calls. The model follows the
  seat number, not the list order. The effect is far larger than any sampling noise. It was measured on
  the nine-seat boards and one model, and has not been re-run on the ten-seat game.
- **Code and record.** `evaluation/experiments/night1_target_bias_check.py`;
  [`data/night1_target_bias/README.md`](../../../game_play_enhancement/data/night1_target_bias/README.md);
  [`discussion_evidence.md`](../../../game_play_enhancement/discussion_evidence.md) §7.5.

### Evil cover screen 🟡 (ten-seat, 2026-10-18)

- **What it is.** A test of what an accused evil seat says: does it claim a role that fits, deny, or
  deflect? It compares the evil cards before and after ruling R11 ("claim, never deny"), then three
  versions of the deduction engine's cover line.
- **How it works.** The source is 41 turns from the captured persona-voice and silence-calibration
  games: the first discussion turn of an evil seat's day after it was accused or a visit of its was
  reported. Each turn is replayed twice per arm on Haiku 5.5 at low thinking. The `before` arm swaps
  R11's text back into the cards word for word. Each step is judged blind by four to eight Sonnet
  subagents on the line and the public record.
- **What it can claim.** How often a seat claims, denies or deflects, and whether a claim fits the
  public record. With R11's card, claims rose from 13 to 33 of 82 samples and denials fell from 21
  to 3. With the final cover line, 1 of 42 claims could be shown false by a careful town player.
- **How far it was checked.** The rebuild of the deduction blocks reproduced all 41 captured blocks
  exactly. The limits are stated in the record. Different judges labelled each step, and the step-1
  and pooled step-2 labels differ for the same arm (21 against 19 denials). The judges see only the
  public record, so a claim that contradicts the sighting it answers was added as a label only in
  step 2. The seats' notes in the captured inputs were written under the old card.
- **Code and record.** `evaluation/experiments/evil_cover_screen.py`;
  [`data/evil_cover_screen/README.md`](../../../game_play_enhancement/data/evil_cover_screen/README.md)
  (packets, keys, verdicts per step). The paired games that followed are in
  [`../game/`](../game/report.md).

### Private-note screen ⚠️ (ten-seat, October 2026)

- **What it is.** The current wording of the private strategy note against a rewrite in three parts
  (Changed, Reasoning, Plan).
- **How it works.** 14 frozen cases are taken unchanged from earlier sets, so the previous note is
  identical in both arms: R1's healer turns, controls where passing was right, and known failures.
  Haiku 5.5 at low thinking, 4 samples a case. The current wording runs from a worktree. Two Claude
  subagents judged every sample with the arms relabelled X and Y per case, on the owner's rubric.
- **What it can claim.** A screen that found no gain. Across 56 samples per arm, fact or rule errors
  rose from 15 to 27, and the healer still passed in 7 of 8 samples under both wordings.
- **How far it was checked.** The blinding was partial: the new note's layout is visible, and both
  judges noticed it. No significance test. The generations were copied on 2026-10-23 from the gitignored
  `eval_results/` into [`reasoning_failures/data/note_prompt/generations/`](../../../reasoning_failures/data/note_prompt/generations/README.md);
  the cases, packets and verdicts are in the record.
- **Code and record.** `evaluation/experiments/note_prompt_cases.py`;
  [`reasoning_failures/experiment_log.md`](../../../reasoning_failures/experiment_log.md) §6;
  `reasoning_failures/data/note_prompt/`.

### Haiku vote replay 🟡 (ten-seat, 2026-10-16)

- **What it is.** Eleven day votes from live game `403f4dbc` replayed under up to five code versions,
  to test one sentence asking reads to compare the living players.
- **How it works.** The cases are frozen from the game's checkpoints at the vote fan-out: the four
  ballots that went wrong, and seven controls that were right. Each case gets 10 samples per arm on
  Haiku 5.5 at low thinking, memory off. Each arm is a worktree. Right means the vote names the actual
  threat, read from the structured field. A regex counts what each read cites. A Sonnet judge checks
  facts only and is not the measure.
- **What it can claim.** On the target ballot the sentence made things worse: 7 of 10 right on the
  current code, 0 of 10 with the sentence (Fisher p = 0.003). The replay also found a drop in the
  day-4 controls across code versions, from 25 to 13 of 30 (p = 0.003), with the reads citing the
  decisive ballot 19 times in 30 before and 2 after.
- **How far it was checked.** The replay measured its own noise floor, as a by-product. An arm that
  only added true facts to earlier ballots moved single cases by more than the effects under test (see
  *What the whole family can and cannot claim*). That weakens the day-4 reading, and the record says
  so. One game; the samples of a case are answers to one prompt. The judge's day-4 flags came from an
  ambiguous expectation and were discarded as false positives.
- **Code and record.** `evaluation/experiments/haiku_vote_cases.py`, `haiku_vote_score.py`; configs
  `evaluation/config/hallucination_bench_haiku_vote_compare.json`, `_haiku_game_vote_v2.json`;
  [`discussion_evidence.md`](../../../game_play_enhancement/discussion_evidence.md) §8.7;
  `data/haiku_vote_replay/` (every sample's vote and reads in `votes.jsonl`),
  `data/haiku_sentinel_vote/`. As of 2026-10-23 the two runners, the vote-compare config and both data
  folders are untracked in git.

### Visit-wording A/B 🟡 (ten-seat, 2026-10-21)

- **What it is.** A test of whether the physical "visit" metaphor (came to, went to, at my door)
  causes arguments about definitions. Arm A keeps the wording; arm B words the same rules as
  "targeting". Arm C keeps the wording and adds two deduction-engine lines.
- **How it works.** 19 turns from three live games, read from checkpoints: 8 that report a watch or
  follow result, and 11 that answer a sighting claim. Arm B changes only words a model reads. A shim
  rewrites the engine's stored prose into the new wording, but player-written text keeps the old
  words. Five samples per case on DeepSeek V4.1 Flash, then on Haiku 5.5. The lines go into one
  shuffled blind file, judged by eight subagents against a fixed rubric.
- **What it can claim.** That the wording is not the cause. Errors about the mechanics stayed at about
  one line in four on DeepSeek, and rose slightly on Haiku (19 to 28 of 95; sign test p = 0.51).
- **How far it was checked.** Arm A was judged twice by different judge sets, giving 19 and 23 of 95
  errors. That gap is about the size of arm C's gain (23 to 19), so C's sign test (6 better, 2 worse,
  p = 0.29) is direction only. The record notes that the reply slice understates the fix, because the
  original denial is still in every replayed transcript.
- **Code and record.** `evaluation/experiments/visit_wording_cases.py`;
  [`data/visit_wording_ab/README.md`](../../../game_play_enhancement/data/visit_wording_ab/README.md)
  (`arm_b.diff`, `judge_rubric.md`, `key.jsonl`, `deepseek/`, `deduction_ac/`).

### Persona line screen 🟡 (ten-seat, 2026-10-18)

- **What it is.** One sentence of voice in the seat's own prompt, tested for whether it makes lines
  read more like people without changing what the seat argues.
- **How it works.** 15 discussion turns from the frozen Haiku turn set, rebuilt by the replay bench.
  The plain prompt is sampled twice, and each of three voices once. Four blind Sonnet subagents judged
  naturalness (voiced against plain) and stance (would a listener take the same position).
- **What it can claim.** Voiced lines were judged more natural in 25 of 30 pairs. They differed in
  stance from a plain line in 9 of 30 pairs, the same 30% rate as two plain lines differed (3 of 10).
- **How far it was checked.** This is the one October screen that built a noise baseline into the
  design: the plain-against-plain pairs. The baseline is only 10 pairs, so a modest content effect
  could hide in it.
- **Code and record.** `evaluation/experiments/persona_line_screen.py`;
  [`data/persona_line/README.md`](../../../game_play_enhancement/data/persona_line/README.md).

### Voice rewrite screen 🟡 (ten-seat, 2026-10-18)

- **What it is.** A second model call that rewrites a recorded line in a persona's voice, behind a
  deterministic fact gate. Strictly, it replays recorded output rather than a turn: the rewriter sees
  only the line and the voice.
- **How it works.** 30 real AI lines, each rewritten once in three voices on Haiku 5.5. The gate
  requires the same players, nights and role words. Blind Sonnet subagents judged naturalness, and
  fidelity as same, minor or changed.
- **What it can claim.** The rewrite reads better (74 of 90 preferred), but 19 of 90 rewrites change
  something a listener could act on.
- **How far it was checked.** All 19 "changed" verdicts were read and confirmed against the originals.
  That check also measured the gate: it caught 1 of the 19.
- **Code and record.** `evaluation/experiments/voice_rewrite_screen.py`;
  [`data/voice_rewrite/README.md`](../../../game_play_enhancement/data/voice_rewrite/README.md).

## Deduction-engine replays

These screens test lines that the deduction engine writes into a seat's prompt. They use the four
acceptance cases (AC1–AC4) from two ten-seat Haiku games, as listed in
[`reasoning_failures/deduction_catalogue.md`](../../../reasoning_failures/deduction_catalogue.md). The
engine's own correctness is checked by code, not by replay; see
[`../../deterministic_audits/`](../../deterministic_audits/).

### Deduction injection, case R1 🟡 (ten-seat, October 2026)

- **What it is.** A test of whether a healer reasons through to a conclusion once its night record
  states the roleblock's certain consequence ("the Chanteuse, a wolf, visited you that night").
- **How it works.** The healer's three passed turns on day 2 of game `2f19d908` are each frozen twice:
  as played, and with the injected line. Ten samples per turn at low and medium thinking, run through
  the bench (`eval-hallucination-bench`, configs `hallucination_bench_deduction_injection.json`,
  `_healer_silence.json`). The measures were fixed before the run: whether it spoke, whether it
  claimed healer, and whether its structured read names player_7 as the Chanteuse. A follow-up 2×2
  varied the seat's own note and the healer card, the card coming from a worktree.
- **What it can claim.** The fact was taken up in all 10 low-thinking notes, but the healer still
  spoke 0 of 10 times. The carried-forward note, not the card, kept it silent: it spoke 3 of 30 times
  with the note as played, against 9 of 20 with a neutral note (Fisher p = 0.007, pooling this run
  with the earlier same cell).
- **How far it was checked.** Whether a message ties player_7 to the block was read by hand. One case,
  one game. The frozen cases are in the record. The samples (judged files and summaries) were graduated
  on 2026-10-23 from the gitignored `eval_results/` into
  [`reasoning_failures/data/deduction_injection/runs/{deduction_injection,healer_silence}/`](../../../reasoning_failures/data/deduction_injection/runs/README.md).
- **Code and record.** `evaluation/experiments/deduction_injection_{cases,score}.py`;
  [`reasoning_failures/experiment_log.md`](../../../reasoning_failures/experiment_log.md) §4–§5;
  `reasoning_failures/data/deduction_injection/`.

### Deduction placement and the AC2 series 🟡 (ten-seat, 2026-10-17 to 18)

- **What it is.** A test of whether the seat's deduction block works better before or after its
  carried-forward note, followed by three runs on the one case (AC2) whose vote would not settle.
- **How it works.** All runs share one runner, which rebuilds the turn with the replay bench but does
  not use the bench's judge. Haiku 5.5 at low thinking, temperature 1.0, memory off.
  - Before any model call, the runner checks that the arms differ only where intended. It checks that
    the seat block is byte-identical between placements, and that each removed sentence occurs
    exactly once and accounts for the whole change in length. These checks are saved in
    `prompt_check.json`.
  - The measures were fixed in the README before sampling. Placement samples were judged blind by
    subagents. AC2 votes were counted by code.
- **What it can claim.** At n = 25 per arm, with all four arms shuffled into one schedule, about a
  third of AC2's votes went to the real Healer in every arm (33 of 100 pooled). Neither the placement
  nor the two sentences changed the vote reliably. With today's closing call, which no longer counts
  the accusers, the rate was 5 of 25 against 9 of 25 (suggestive). The owner kept `before_note`.
- **How far it was checked.** The series is the clearest record of the single-case noise problem. The
  n = 3 run's 0 of 6 was luck, and the n = 10 split of 8 against 1 on an identical prompt was noise.
  Only the shuffled n = 25 design gave a stable rate. Every run used an uncommitted working tree. The
  READMEs record a hash of the diff, but not of the untracked files. One rerun pass (5 rows) started
  after another session had begun editing `Agents/`; the human message was checked byte-identical, the
  system message was not.
- **Code and record.** `evaluation/experiments/deduction_placement_screen.py`,
  `deduction_ac2_{ablation,2x2,closing_fixed}.py`; `reasoning_failures/data/deduction_placement/`,
  `deduction_placement_n10/`, `deduction_ac2_ablation/`, `deduction_ac2_2x2/`,
  `deduction_ac2_closing_fixed/` (prompts, samples, verdicts, keys).

### Counter-claim vote screen ⚠️ (ten-seat, 2026-10-18)

- **What it is.** A test of whether a line that says what each of two rival claimants names as its
  results moves town votes off the real claimant.
- **How it works.** Every town vote turn in the eight evil-cover games whose re-rendered block carries
  the line: 10 turns on 3 days. Three samples per arm, with and without the line, on Haiku 5.5 at low
  thinking. The vote is the measure.
- **What it can claim.** A direction only. Overall the votes did not move (12 fake and 16 real
  without the line; 12 and 17 with it). In the case it was built for, the line made things worse (7
  votes for the fake and 4 for the real claimant without it, against 5 and 7 with it).
- **How far it was checked.** 10 turns, 3 samples, one model. The engine change was never committed,
  so at HEAD the runner finds no turns and cannot be rerun.
- **Code and record.** `evaluation/experiments/counter_claim_vote_screen.py`;
  [`data/counter_claim_votes/README.md`](../../../game_play_enhancement/data/counter_claim_votes/README.md).

## L1/L2 — the per-day replay (design only)

- **Status: ⏸ DESIGN — NOT BUILT (2026-07-02).** An execution-ready spec; no `day_replay.py` exists.
  It fills the ladder rung between the off-policy per-turn screen and the full paired A/B: re-run a
  *single* day k≥2 of a recorded game under a swapped condition, **on-policy within the day** (real
  scheduler, real utterances, live votes), with the prior days frozen as history. It reuses the
  production day subgraph, so replay drift can only come from the reconstructed entry state, never a
  divergent harness. *(Still not built, 2026-10-23.)*
- **Cost + niche.** ~$0.10–0.15 per day-replay ≈ 20–30% of a full game; a 30-pair campaign plus the
  acceptance gate is a ~$10–17 decision, not ~$60. Sourced from memory-OFF recordings so the OFF arm
  is on-policy by construction; day 2 is the primary stratum; no multi-day chaining in v1.
- **The honest part is the acceptance gate.** Before any ON-vs-OFF number is trusted, an
  unchanged-condition replay of 10–15 game-days must be statistically indistinguishable from the
  recorded days (distributional, never transcript-equality, because the scheduler is content-reactive).
  The measured self-agreement *becomes* the harness's cited noise floor, and any later effect inside
  that floor is "not distinguishable from replay noise." A hard-fail survivor-set cross-assert guards
  state fidelity (never warn-and-continue).
- **What it can and cannot answer.** It answers the within-day causal effect of a condition given a
  fixed prefix. It explicitly **cannot** answer the game-outcome or compounding effect — that stays
  with the paired A/B. The open v7 compounding question is not something a day replay can close.
  *(2026-10-23: that question was closed by the paired endpoint A/B in July 2026, leaning negative.
  The October screens repeatedly hit the gap this design targets: effects that live in the rest of
  the day, which a frozen turn cannot show.)*
- **Corrections the code-verification forced on the design** (kept in place, not laundered):
  `vigilante_results` is sidecar-only (absent from the batch record top level); the utterance cap is
  `max(min, ceil(3·N))` (cap(9)=27), not the ~25-flat first estimated — dollar figures survive, the
  constant is corrected; night deaths are stamped with the *concluding* day, so the naive `day < k`
  prefix filter is correct only for a non-obvious reason, now documented. All of this describes the
  nine-seat record.

## Verdict + cheapest upgrade

Per the header. Across the family, a replay is trustworthy for one thing: whether a change reaches a
turn, and which way it pushes. Size needs either many cases or a measured noise floor. Anything that
plays out later in the day needs games.

> *Original (2026-07-02), kept as the record.* **Cheapest upgrades, both HELD (spend not yet
> approved):** a wolf replay screen (~$3–5), enabled by the deceiver-coverage fix, to de-risk a
> wolf-direct A/B; and a gating re-screen (~$10–15) substituting deterministic dimensions into the
> frozen cases (see [`../../deterministic_audits/experiment_log.md`](../../deterministic_audits/experiment_log.md) §5).
>
> *Correction (2026-10-23):* neither ran before the memory research closed on 2026-07-21, and no
> record of either was found. Both are moot.

**Cheapest upgrade now: give every screen a noise floor and keep its samples.**
- Run the unchanged arm twice, as the persona line did, or interleave all arms in one shuffled
  schedule, as the AC2 2×2 did. A difference smaller than the gap between two unchanged runs is not a
  finding.
- Copy raw samples into the evidence folder, as the visit-wording and AC2 runs did, rather than
  leaving them in the gitignored `eval_results/`.
- Record the model in the manifest. The checkpoint replay and the tell-book screen do not.

The per-day harness's cheapest first step is fixed by its own design: build the acceptance gate before
trusting a single ON-vs-OFF number.

## Sources

| Instrument | Code | Record |
|---|---|---|
| Decision-replay screen | `evaluation/src/studies/decision_replay.py` (`--lens`, `--night`); engine `evaluation/src/replay/decision_screen/` (`cases`, `replay`, `schemas`, `screens`, `stats`); lenses defined in `Agents/memory/consolidation/decision_scoring.py`, re-exported by `evaluation/src/loop/decision_scoring.py` | [`decision_replay/report_screening_layer.md`](../../../memory_system/effectiveness/decision_replay/report_screening_layer.md), [`experiment_log.md`](../../../memory_system/effectiveness/decision_replay/experiment_log.md), JSONs colocated; `gemini-3.1-flash-lite` @ temp 1.0, commits `d335d2c`→`b332550`; hardening [`../../hardening_pass/experiment_log.md`](../../hardening_pass/experiment_log.md) §2.2, §3, §4.5–4.7 |
| Checkpoint replay | `evaluation/src/replay/decision_screen/checkpoint_replay.py` (`eval-checkpoint-replay`) | [`credit/blindspot_fix/experiment_log.md`](../../../credit/blindspot_fix/experiment_log.md) ④–④d; `replay/`, `replay_onepoch/`, `replay_obs/` |
| Tell-book screen | `evaluation/src/replay/decision_screen/tell_book_screen.py` | [`tell_extraction/experiment_log.md`](../../../extraction/tell_extraction/experiment_log.md) ⑫; `outputs/book_screen*.json` |
| Stage-filter replay | `evaluation/experiments/v8_stage_filter_replay.py` | [`memory_system/v8/experiment_log.md`](../../../memory_system/v8/experiment_log.md); `data/gate/stage_filter{,_40games}/` |
| Night-1 target check | `evaluation/experiments/night1_target_bias_check.py` | [`data/night1_target_bias/`](../../../game_play_enhancement/data/night1_target_bias/README.md); `discussion_evidence.md` §7.5 |
| Evil cover screen | `evaluation/experiments/evil_cover_screen.py` | [`data/evil_cover_screen/`](../../../game_play_enhancement/data/evil_cover_screen/README.md) |
| Private-note screen | `evaluation/experiments/note_prompt_cases.py` | `reasoning_failures/experiment_log.md` §6; `reasoning_failures/data/note_prompt/` |
| Haiku vote replay | `evaluation/experiments/haiku_vote_{cases,score}.py` (untracked) | `discussion_evidence.md` §8.7; `data/haiku_vote_replay/`, `data/haiku_sentinel_vote/` (untracked) |
| Visit-wording A/B | `evaluation/experiments/visit_wording_cases.py` | [`data/visit_wording_ab/`](../../../game_play_enhancement/data/visit_wording_ab/README.md) |
| Persona line screen | `evaluation/experiments/persona_line_screen.py` | [`data/persona_line/`](../../../game_play_enhancement/data/persona_line/README.md) |
| Voice rewrite screen | `evaluation/experiments/voice_rewrite_screen.py` | [`data/voice_rewrite/`](../../../game_play_enhancement/data/voice_rewrite/README.md) |
| Deduction injection (R1) | `evaluation/experiments/deduction_injection_{cases,score}.py` | `reasoning_failures/experiment_log.md` §4–§5; `data/deduction_injection/` |
| Placement and AC2 series | `evaluation/experiments/deduction_placement_screen.py`, `deduction_ac2_{ablation,2x2,closing_fixed}.py` | `reasoning_failures/data/deduction_placement{,_n10}/`, `deduction_ac2_*/` |
| Counter-claim vote screen | `evaluation/experiments/counter_claim_vote_screen.py` | [`data/counter_claim_votes/`](../../../game_play_enhancement/data/counter_claim_votes/README.md) |
| Per-day replay (design) | none | [`day_replay/design.md`](../../../memory_system/effectiveness/day_replay/design.md) |
| Shared replay engine (October screens) | `evaluation/src/replay/hallucination_bench.py` (`turn_payload`, `turn_template`, `hydrate_state`); checkpoint reader `evaluation/experiments/haiku_game_turn_cases.py` (`day_states`); capture rebuild `evaluation/experiments/deduction_block_census.py` (`_payload_at`) | [`../../factual_errors/report.md`](../../factual_errors/report.md) |

*Written 2026-07-02 from the hardening pass and the decision-replay evidence; widened 2026-10-23 from
the October screens' READMEs and logs, checked against the code at the working tree of that date.
Whether memory or any prompt change actually works belongs to the design folders linked above.*
