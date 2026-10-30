# Authoring brief: Designing fair comparisons

Page: `writeup/evaluation/fair_comparisons/fair_comparisons.skill_2.md` · Level 2 · started 2026-10-29 · checkpoint: approved in conversation 2026-10-29; defaults accepted for all open questions

Authoring material, not page copy. The cold editorial reviewer never sees this file.

Trial run of the `write-portfolio-page` skill (second version, 2026-10-29): steps 1–3 only, stopping at the
checkpoint. Written without reading the owner's version, the earlier trial or any other brief in this folder.
Inputs read: the skill and its references (voice, examples A–C, page types, brief template); the general and
Level 2 prompts; `writeup/map.md` "Chapter outline: Evaluation" with its Handle-with-care list; the chapter
content plan; the chapter page and the parent excerpt (`parent_context.py`); the Level 3 page
`paired_baseline.md`; the packet's historical brief and sources comment. Sources read directly:
`evidence/evaluation/experimental_controls/report.md` (all), `variance_reduction_levers.md`;
`evidence/memory_system/effectiveness/paired_ab/experiment_log.md` lines 1–80;
`evidence/evaluation/deterministic_audits/report.md` case 5; `evidence/evaluation/evaluation_scopes/game/report.md`
"How a whole-game comparison is set up", "Choosing…", cases 1–2; `evaluation_scopes/turn/report.md` (single-case
noise); `evidence/memory_system/v7/report.md` "Testing the test before paying for it";
`Agents/run_fingerprint.py`; `evaluation/src/loop/invariants.py`; `evaluation/src/loop/driver.py` (guard call
sites). The evaluation chapter has no `editorial_notes.md`.

## Frame

- **Primary page type and level:** approach/technique explanation (what a fair comparison needs and why),
  Level 2. The opening follows the "approach" pattern: what a controlled comparison does and the two kinds of
  problem it faces, before any incident.
- **Secondary mode, if needed:** the featured section ("A baseline that moved") borrows the incident mode:
  observed shift → competing explanations (drift, chance) → the paired re-test → what was decided. Its
  uncertain cause is what motivates the time-window rule; the page never claims to diagnose it.
- **Existing outline approval:** approved in conversation 2026-10-29 (Frame, Core argument and Argument
  outline as proposed; the stated default accepted for every open question).
- **Reader's question:** When a new version scores differently from the old one, how do you know the change
  caused the difference?
- **Central answer:** Two different things can produce a false difference, and they need different tools.
  Any other difference between the two sides (inputs, set-up, the model service underneath, the way they were
  scored) can fake an effect, so I hold those fixed, record them on every game and let code stop a run where
  it can. Randomness within each side can fake or hide an effect, so a difference is read against a measured
  noise floor, with a test sized and fixed before the games. A baseline that shifted on unchanged prompts and
  code showed why both matter: chance and a change in the hosted model could not be told apart, so the two
  sides of a comparison now run in the same time window.
- **Reader starting point:** the parent summary has defined confounding factors, named matched deals,
  unchanged settings and one evaluator, said that sampling variability remains and that re-running or
  re-judging measures it, and summarised the June case (fewer town wins; paired analysis did not rule out
  chance; cause unresolved; same-window rule; some runners enforce it). This page must still define: a deal
  and why the same deal is not the same game; what "paired" means here; what a fingerprint records versus
  what a guard enforces; what a noise floor is, by what was repeated; why win rate needs so many games. The
  game itself is introduced only as far as the June case needs (town vs evil sides; the town wins or loses).
- **Opening choice:** a short definition-led opening (about 120–150 words) that splits the parent's two ideas
  into the two kinds of problem and says how each is handled. A reader arriving directly needs that split
  before the table of controls, and the June case reads as the proof of why "the same time" belongs in the
  list. Opening with the incident was considered; it would make one control (time) look like the whole page.
- **Claim level:** practical choice and mechanism (which controls exist, what each guards against, where code
  enforces them), plus one diagnosed-but-unexplained observation (the June shift). No measured-improvement
  claim: the page does not claim the controls improved any result, only that they remove named differences
  or make a difference interpretable. Evidence needed: the code/record for each enforced control, the June
  numbers as re-tested, the noise and sample-size figures with their units.
- **Distinctions the reader needs:**
  1. A difference **between the sides** (fakes an effect; removed by controls) vs randomness **within each
     side** (fakes or hides one; only sample size and a measured noise floor deal with it).
  2. **Recording** a setting (the fingerprint) vs **enforcing** a rule about it (a guard that stops the run)
     vs **verifying** that the setting did what it names (the thinking level that produced no reasoning tokens).
  3. **The same deal** vs **the same game**: the game id fixes who holds which role; players sample at
     temperature 1.0, so two games on one deal part ways at the first different line.
  4. **A shifted baseline** (observed) vs **provider drift** (one suspected cause, alongside chance).
  5. **Enforced in code** (the memory-experiment driver; turn replays in one session) vs **manual** (the
     general batch tool, comparisons across runs).
- **What the evidence establishes:** the controls exist and what each checks (code and tests cited); the
  within-run fingerprint stop and the arm guard are code-enforced in the memory-experiment driver; the arm
  guard was built after a real mis-set arm and held in the one run since; the June baseline moved (12 → 7 town
  wins on 20 shared deals; 7 win→loss, 2 loss→win) without an established size or cause; the requested
  thinking level produced no reasoning tokens on both sides of every earlier comparison; re-judging moved
  totals by 1–2 of 267; one saved vote turn gave 8 of 10 and then 1 of 10 with nothing changed; at 30 games a
  side only large effects are detectable (~36 points of win rate, ~0.18 vote accuracy); a size simulation
  retired one planned test before money was spent; on the nine-player game the deal explained almost none of
  the variation in decision scores.
- **What stays uncertain:** the cause and size of the June shift; whether pinning would have prevented it
  (that model had no dated version); same-window enforcement outside the memory driver and replays (manual);
  game records still store only the configured thinking level; the paired design that replaced the trend test
  was not size-checked; the pairing finding is nine-player only; the ten-player lineup is not yet adjusted for.
  Each goes beside its claim, not in a closing disclaimer; the closing section groups the manual steps.
- **Stays off the page:** the endpoint test's missing final-number script, its git-ignored per-game data, and
  its result (Memory chapter); untracked reanalysis script / any "records outside git"; "+17pp, p = 0.013";
  the 0.14% rate; the 2026-06-12 overnight canary (27% → 51%, never re-tested); "the test suite is largely
  AI-written and unaudited" and "no CI"; runs from uncommitted trees; costs (the $3 baseline check, per-game
  cost); code and folder names (`run_batch.py`, `invariants.py`, `_run_arms_parallel`, "nine-seat"); model
  family and provider names; "drift" asserted as fact; "every comparison runs side by side"; research labels
  ("pre-registration", "power analysis", "MDE") per the applied-rigour ruling (sources comment may keep them).

## Evidence selection

**Core argument, before examples or numbers:**
A comparison is fair when the two sides differ only in the change under test. Two things break that, and
they need different tools. (1) **Other differences between the sides**: inputs, set-up, the conditions
underneath (the hosted model can change with no code change), and how the outputs were scored. These are
removed by matching, and because a mismatch is silent, the set-up is recorded on every game and code stops
the run where a rule can be checked. Recording is not enforcing, and a recorded setting is not proof of what
the model did. (2) **Randomness within each side**: at temperature 1.0 a single case or a small batch moves
a lot with nothing changed. Matching does nothing for this; it needs a measured noise floor, enough games,
and a test whose measure and size are fixed before the games. The June baseline joins the two: something
moved with no code change, and with these sample sizes chance and a model change could not be separated, so
the defensible response was a rule about **when** both sides run, not a claim about **why** it moved.

| Essential concept | Selected evidence (source), if needed | Why this example earns space | Alternatives omitted / destination |
|---|---|---|---|
| Two kinds of problem need different tools | Controls report, "When does a comparison need a fresh baseline?" ¶2 | The page's organising split; parent mentions both but does not separate their remedies | The three meanings of "pairwise" table → notes (one sentence survives as "paired design vs paired test") |
| What has to match: inputs, set-up, conditions, measurement | Controls §1–§2 control table; same deal from the game id; turn rebuilt from saved state; old versions run from a tagged checkout; one judge from main | A compact table lets the reader see the whole set before the featured story deepens one row | Prompt golden, provenance manifests, run graduation, "judge from neither side" → evidence link / notes |
| Same deal ≠ same game | Controls §1 "Same deal from the same game id"; levers audit correction 2026-10-23 | Needed to read the June pairs and the pairing finding correctly | crc32 mechanism, scheduler tie-break history → notes |
| Measurement must match too | Controls §2: rubric split moved another label 74% → 63% on the same messages; old games re-read with the new rubric | Shows measurement can differ even with "the same judge"; one sentence | Self-preference judge case → LLM-judges page |
| The baseline that moved (featured) | Controls "The case that set the rules"; paired_ab log 5–38, 61–67; L3 page | Lead story per the content plan; motivates the time-window rule; shows the observation-vs-cause discipline | Transition table, winners by side, test names, the two independent readings in full → L3 `paired_baseline.md` |
| Why not just pin the model | Controls §1 "Pin the model where the provider allows it"; paired_ab log "Can we pin or detect the drift?" | Answers the obvious objection; gives the general guarantee (identity behind a name) and its limit (serving can still change; some names have no dated version) | Per-provider list (four providers, dates) → notes |
| Where the same-window rule is enforced | Controls control table; driver.py runs both arms in one pool, pairing by game id | Scope beside the rule (Handle-with-care: not "every comparison") | — |
| Record vs enforce (exhibit FC-record) | `Agents/run_fingerprint.py` fields; driver `assert_fingerprint_consistent` on both arms | The exhibit spec in `exhibits/source_map.md`; shows what is matched, changed, configured and measured in one artefact | Fingerprint coverage gaps (prompt subfolders) → notes |
| A guard that stops a mis-set run | Deterministic audits case 5; `invariants.py` `assert_arm_declared` / `assert_arm_factions`; controls §1 (held in one run since, 2026-07-19, four town roles) | A real caught fault, told as caught and changed; shows "plausible wrong number, no error" | Embedding check at batch start → one clause in the pinning paragraph (default include) or notes |
| A setting that did not do what it names | Controls §4 (2026-10-04 probe) | Distinction 2; Handle-with-care "tell what was caught"; scope of earlier results narrows, fairness holds | Model-admission thinking-budget results → model admission page |
| Noise: measure it by repeating nothing | Turn report §2 item 1 (8 of 10 → 1 of 10; ~1 in 3 at 25 per arm, shuffled); scoring/controls §3 (re-judging moved totals 1–2 of 267) | One generation-noise example and one measurement-noise example; parent says the two are measured separately | Model admission's ~6 points at 70 samples → model admission page (one-clause cross-reference at most) |
| What pairing bought | Controls §3; game report "What pairing turned out to buy" (0.249 within vs 0.21–0.26 across; nine-player) | Corrects a natural assumption (matching deals reduces noise); says what pairing still buys | Numbers in notes; words on page |
| How many games a test needs | Controls §3 (30 a side: ~36 points of win rate, ~0.18 vote accuracy; ~100 a side for ~0.10); v7 report "Testing the test" (planted +0.15 found ~1 in 9 at 24 games; false alarm 2–3%) | Why decision scores and replays exist; a check that retired a test before spending | Simulation steps and table → evidence (and a possible Level 3 if the owner wants it) |
| Fix the measure, size and reporting before the games | Game report case 2 "What and why", "How it works" (method only) | Packet brief (added 2026-10-25); guards against choosing the luckiest of many measures | Result, the missing script, git-ignored data → off page / Memory |
| What still depends on a person | Controls "Bottom line", "What we would do differently" rows 1–4; levers audit correction (ten-player lineup) | Limits grouped by purpose, as next steps | — |

For the existing L3: "After L2, the interested reader may ask *did the shifted baseline show that the model
service changed?*; `paired_baseline.md` answers it by laying out the two readings, the 20-deal transition
table and why the readings differ." L2 keeps the finding, the shared-deal numbers in words, the unresolved
cause and the rule. No new L3 proposed. (Content-plan "possible" candidates: "Testing the test before paying
for it" has no anchor yet; the outline below gives it one in section 6 if the owner later wants it. "How
noisy is one replayed case?" is anchored in section 5's noise paragraph.)

## Argument outline

Structure: **frame, then parts, then the featured case, then the second problem.** The opening names the two
kinds of problem; sections 1–4 handle differences between the sides (what must match → the case that added
time to the list → how the set-up is recorded and enforced → checking what actually ran); sections 5–6 handle
randomness within a side (reading against noise → planning the test before the games); section 7 groups what
still depends on a person. This follows the page's own distinction rather than the order the work was done
(the June case happened first, but it is placed where the concept it teaches, "same conditions underneath",
is already defined). Like example A, the featured failure sits inside the concept it exposes.

| # | Section | Reader understands afterwards | Selected example, if needed | Omitted / linked | Why the next follows |
|---|---|---|---|---|---|
| 0 | Opening (no heading) | A fair comparison changes one thing; other differences between the sides fake effects and are removed by matching and checks; randomness within a side fakes or hides effects and is handled by noise floors and sample size; a baseline that moved with nothing changed is why "the same time" is one of the controls | — | Project intro (parent has it) | Names the first problem, so the page lists what must match |
| 1 | What has to match | The four things that must be the same (inputs, set-up, conditions underneath, measurement) and the control for each; a deal is the role assignment the game id fixes, and the same deal is not the same game | Table of four rows; one judge example (74% → 63% when a rubric changed, so both sides are re-scored in one run) | Prompt golden, manifests, "judge from neither side" → evidence | The "conditions underneath" row is the least obvious: nothing in the code changes, yet the result can |
| 2 | A baseline that moved with nothing changed (featured) | On identical prompts and code a fresh baseline gave the town far fewer wins (1 of 10 fresh deals vs 20 of the earlier 30); tested as pairs on the 20 deals played in both, wins fell 12 → 7, a split chance alone produces about one time in five; size and cause not established; drift on an unpinnable model name and chance both open; so both sides run in the same time window and never against historical runs; pinning helps where offered but fixes identity, not serving, and that model had no dated version; enforced in the memory-experiment driver and in replays, by hand for other batches | June case; pinning paragraph; (default) one clause on the embedding check as detection where pinning is impossible | Transition table, test names, winners by side → **Level 3 link: What the paired baseline reanalysis changed** | The rule assumes we know what each side actually ran with; that needs a record |
| 3 | Recording the set-up, and enforcing it | A fingerprint on every game records commit, prompt hash, backend, model, temperature, thinking levels, embedding model; recording only shows a change, a guard stops the run: within one run any fingerprint change stops it; across runs a person compares | **Exhibit FC-record**: an annotated game record (matched input: game id → deal; intended change: which roles have memory; configuration: the fingerprint; measurement: decision scores from the record), each field labelled "recorded" or "enforced by …" | Fingerprint coverage gaps → notes | A matching fingerprint can still hide a wrong experiment: the record says what was configured, not what the arm did |
| 4 | Checking the experiment that actually ran | Two caught faults, at two levels. A memory run's treatment side gave memory to every side instead of only the town, with no error; now a run must declare its memory arm (or knowingly waive the check), and each round of games reads back the actual settings and stops on a mismatch (held in the one run since). A requested thinking level produced no reasoning tokens on the player model; both sides always matched, so comparisons stayed fair, but earlier results describe players that produced no reasoning tokens; replays of the test set now record reasoning tokens, game records still only the setting | Arm guard incident; thinking-level probe | Embedding check (if not in §2) → notes; model-admission thinking results → that page | The remaining risk is not a different set-up but chance: both sides can be identical and still differ |
| 5 | Reading a difference against noise | Noise is measured by repeating with nothing changed: re-judging the same outputs (measurement noise, 1–2 of 267) and re-running the same version (generation noise: one saved vote turn, 8 of 10 then 1 of 10; about one in three at 25 per arm shuffled into one schedule); smaller differences than the floor mean nothing; matching deals barely reduced the noise (the deal explained almost none of the variation in decision scores, nine-player game), but it is still the default because it rules out easier deals and allows paired reading; what made the June comparison fair was the shared time window | Single-case noise; pairing finding in words | Model admission's 6-point spread → that page; judge consistency → LLM-judges page | If noise is that large, the number of games and the measure must be decided before paying for them |
| 6 | Planning the test before the games | With 30 games a side, only large win-rate gaps (~36 points) are detectable, which is why decision scores carry the verdict; a free simulation planted a known improvement into resampled real games and found that the planned trend test would catch it about 1 time in 9, retiring it before any money was spent; the memory endpoint test fixed its main measure, its number of games and how a null result would be reported before any game, and changed its plan once, in writing, before data; its result is in the Memory chapter | Size simulation; endpoint method | Result, script, data → off page; Memory chapter link (planned) | What remains is where the controls depend on a person |
| 7 | What still depends on a person | Strong where code enforces (fingerprint stop, deal from game id, rebuilt turn, arm guard, size check before the trend test); weaker where a person must remember: interleaving whole-game batches outside the memory driver, comparing across runs, checking a setting's effect in games; next steps: interleave in every batch tool, record reasoning tokens per game, size-check the exact design before each paid run (the paired design that replaced the trend test was not), adjust for the dealt lineup on the ten-player game | Controls "Bottom line" and "do differently" rows | Evidence links | — |

**Outline check (main points only, in order):** a fair comparison changes one thing; four things must match;
one of them, the time, failed silently and its cause is unknown, so both sides now run together; the set-up is
recorded on every game and code stops a run within it; records show what was configured, so a guard reads
back what ran, and a setting's effect needs its own check; with the set-up matched, chance remains and is
measured by repeating nothing; so the size and measure of a test are fixed before the games; what still
relies on a person. This answers the frame's question. Term order holds: "deal" (§1) precedes the June pairs
(§2); "fingerprint" (§3) precedes "matching fingerprint can still hide" (§4); "noise floor" (§5) precedes
sizing (§6). One forward dependency: §1's table mentions "same time window" before §2 explains why; the row
points to §2 rather than explaining it.

**Length plan:** ~1,800–2,000 words including the table and the exhibit. If over, cut in this order: the
embedding-check clause, the 74% → 63% sentence, the single-case "one in three at 25 per arm" clause, then
merge §6's two examples into one paragraph each. Do not compress §2 or §4.

## Open questions

1. **Size check not run for the paired design (§6/§7).** The controls report lists it as a "would do
   differently" row; it bears on the endpoint test, whose result is on the Memory page. Not on the
   Handle-with-care list. Default: one clause in §7 as a next step, not tied to the endpoint result.
2. **First person.** The records do not say who ran the June reanalysis or wrote the guards (orchestration is
   ~90% the owner's; evaluation code authorship unknown). Default: "I" for decisions and rules (the
   same-window rule, requiring a declared arm); neutral wording for the reanalysis and for who ran checks.
3. **Statistics on Level 2.** Default: no test names (Fisher, McNemar) on this page; give the independent
   reading as counts and the paired reading as "a split that uneven happens by chance about one time in five
   (p = 0.18)". The first reading's p = 0.0028 stays on Level 3.
4. **Keep the "decide the analysis before the games" passage?** The applied-rigour ruling (2026-10-28) came
   after the packet brief asked for it (2026-10-25). Default: keep it as one plain-words paragraph inside §6,
   no "pre-registration" label.
5. **Embedding check.** Default: one clause in §2 as the detection used where a model name cannot be pinned
   (memory runs only); drop first if over length.
6. **Single-case noise as a Level 3 later?** The content plan lists it as "possible" with page 7 as a
   candidate anchor. Default: anchored in §5's noise paragraph; no page proposed now.

Questions 1–6 above: owner accepted the defaults, 2026-10-29. Added after review (step 6), for the owner:

7. **Records conflict on the arm fault.** `deterministic_audits/report.md` case 5 says the mis-set run
   "gave memory to every side while it was believed to be town-only, so its 'control' was really a
   treatment"; `invariants.py` (`assert_arm_factions` docstring) says the memory-on arm ran with memory for
   every faction when town-only was intended. The page now reads "a memory run meant to give memory only
   to the town … gave memory to every faction, the wolves and the serial killer included", which holds
   under either record, but does not say which arm was affected. Owner to settle which record is right
   (and fix the other); the page needs no change unless the owner wants the arm named.
8. **Fingerprint gaps as a stated limit?** The model-service field is wrong for every non-Google model
   (the default since 2026-10-15), and the prompt hash skips subfolders such as the role cards
   (`tracing/fingerprinting/report.md` §4.2–§4.3). The page now avoids both claims ("a hash of the main
   prompt files"; the service field dropped) but does not name the gaps. Scope ruling for the owner.
   Default: leave them off the page as fixes to make, not limits on a result the page reports.
9. **The rule was not always followed.** One June memory arm (reranked town) ran after its baseline,
   leaving a timing confound (`memory_system/effectiveness/report.md` §2). The page now says "the rule has
   been", not "the sides run", so it is not wrong either way. Scope ruling: whether this page should say
   so. Default: off this page; the reranked arm is a Memory-chapter result.
10. **Current practice.** The page describes the fingerprint stop and the arm guard in the
    memory-experiment driver, as the controls report does. Whether today's ten-player comparisons go
    through that driver, or through the general batch tool by hand, is not stated in the sources I read.
    Wording on the page is limited to what the driver does. Owner to confirm if the page should say which
    comparisons currently use it.

## Draft notes (step 4, 2026-10-29)

- **Length:** 2,159 words of page copy, tables and captions included (not counting the exhibit spec line
  or the evidence list), against a guide of 1,200–2,000. The first draft had 2,302. Cut, following the
  length plan: the embedding check (moved to a supporting note), the 25-samples clause (moved to a note),
  and a paragraph on running old versions from a checkout of the old code (moved to a note; it was not in
  the outline). The 74% → 63% sentence stays: it is the only concrete example in the measurement row.
  Further cuts would come from the June section (456 words), which is the featured story.
- **Changes from the outline:** §2 has no embedding-check clause (open question 5's default allowed
  dropping it first; it is no longer listed in §7 either). §6 now names the final memory test as the
  paired test that replaced the dropped one, so the size-check gap in §7 points at it (default 1). The
  exhibit is a four-row table with a caption, plus a spec line in case it is rendered as an annotated
  record. No other structural change.
- **Skim (headings, opening sentences, captions):** the argument can be followed from these alone. Fixed
  after the skim: the exhibit caption had said "only the last column acts", which the table contradicts
  (it also lists what is only recorded); "Either way" in §2 came before chance had been named as the
  alternative; §7's "the paired design that replaced the dropped test" did not connect to §6. Still
  open: the June section's first sentence sets the scene and the shift arrives in its second sentence.
  §1 ends with a one-sentence bridge paragraph.

## Step 7 (trial: not performed)

Anticipated, to confirm after drafting: the chapter has no `editorial_notes.md`, so the entry would need the
owner's call on creating one (default: create `writeup/evaluation/editorial_notes.md` with this page's dated
entry). The parent L1 section ("Designing fair comparisons") already matches the central answer; likely no
edit, unless the draft's wording of "some runners enforce it" changes. `exhibits/source_map.md` FC-record row:
update its spec to the exhibit actually drafted. `paired_baseline.md`: its return link text ("Return to the
same-window rule and the other controls") stays valid; no change expected.

Added after review (2026-10-29), still not performed:
- `writeup/evaluation/editorial_notes.md` (create, pending the owner's call): dated entry recording the
  explanatory path, what moved out (embedding check, old-version checkout, 25-samples clause, rubric
  mechanism, exhibit spec), the claim changes from the claims review (thinking scope to memory
  comparisons, pairing to one score, rule wording, fingerprint fields), and that "editorially revised" is
  not "factually verified".
- `writeup/evaluation/evaluation.md`, "Designing fair comparisons": "That uncertainty established the
  requirement to run compared versions in the same time window. Some runners enforce it; others still
  require manual scheduling." Consistent with the page; no edit needed.
- `paired_baseline.md` "Why the readings differ" and "What it does not show": consistent with the revised
  June section (both readings, fresh games few and on different deals, cause open); no edit needed.
- `writeup/evaluation/exhibits/source_map.md` row FC-record: note that the drafted exhibit is a four-row
  table with a record/enforce column, and that the fingerprint row omits the model-service field.
- Evidence (outside this task's scope; for the owner): `deterministic_audits/report.md` case 5 wording vs
  the `invariants.py` docstring (Q7).

## Review resolution

Reviews: `fair_comparisons.skill_2.review-editorial.claude.20261029T030531Z.9eQdQc.md` and
`fair_comparisons.skill_2.review-claims.claude.20261029T030847Z.P3EPAS.md`. Claims findings checked
against `tracing/fingerprinting/report.md` §4.2–§4.3, `drift_surfaces_and_guards.md` "Variance constants"
and `memory_system/effectiveness/report.md` §2 before acting.

| Reviewer | Finding (passage) | Action: explained / relocated / removed / corrected / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| Editorial 1 (blocking) | June: "too large to be chance", then chance as the alternative, then p = 0.18 from a different comparison | **Explained.** "Read as unrelated games" marks the first reading. The reanalysis is placed on the 20 replayed deals, "the only comparison that held the starting roles fixed", counting only deals whose result changed. A sentence says what the 10 new games still show and why they are weaker (few, dealt differently). The conclusion follows: outcomes moved, size and cause not established. Consistent with L3 "Why the readings differ" | Done: the opening and the rule paragraph still match |
| Editorial 2 / Claims 5 | "What made the June comparison fair was the shared time window" (reads as a contradiction; fairness vs noise) | **Corrected.** Replaced with a general statement: shared deals do not protect against a change underneath; running both sides in the same window does. The June label is gone, which also avoids implying every June arm followed the rule (open question 9) | No |
| Editorial 3 | Exhibit spec line read as page copy; the caption described a record that isn't shown | **Relocated + corrected.** The spec line moved into an HTML comment; the caption now describes the table ("What each part of a … game record does in a comparison"). Kept the table rather than a mock record (the brief's FC-record choice) | No |
| Editorial 4 | Ten-player game appears only as a passing caveat | **Explained.** One parenthesis where the nine-player game is first named: "the current game has ten players, dealt from a cast of twelve roles". The §7 repeat of that definition was removed | No |
| Editorial 5 | Factual-error test set undefined; "the totals" unclear | **Explained.** Defined in one clause at first use (§4). §5 now says what the count is: "the number judged to contain an error", of the same 267 responses | No |
| Editorial 6 / Claims 9 | One vote turn carries "far larger"; floor used as a threshold | **Corrected.** "Can be far larger for a single case"; "In one example"; "each figure comes from a single check, so it gives a scale rather than a fixed threshold". Whether the 8-of-10 and 1-of-10 runs shared a session is not in the source, so the page makes no claim either way | No |
| Editorial 7 | 74% → 63%: labels, judge, mechanism and "the discussion redesign" undefined | **Corrected (reduced).** Now one sentence: one rubric change moved a label's rate on unchanged messages, so old games are re-scored with the new ones. The judge, mechanism and redesign name moved to the sources comment | No |
| Editorial 8 (taste) | Table describes the arm guard before its story; "round of games" undefined | **Accepted.** Row points forward ("next section"); "round" replaced throughout by "batch of games" | No |
| Editorial 9 (taste) | Two superlatives in a row | **Accepted.** "Easiest to miss" replaced with "Scoring can shift even with the same judge" | No |
| Editorial 10 (taste) | Opening's fourth paragraph repeats the parent and says "why both matter" | **Partly accepted.** Kept as a one-sentence pointer; the parent is not visible to a reader arriving directly, and the case does involve both problems (a shift that could not be told from chance). Reworded to "the two problems met in one baseline …" | No |
| Claims 1 | "The two sides … run in the same time window"; "is interleaved by hand" | **Corrected.** "The rule has been that …"; "has to be interleaved by hand". Handle-with-care line respected. Timing-confounded June arm flagged (Q9) | No |
| Claims 2 | Fingerprint stop catches "a prompt edit" | **Corrected.** "A hash of the main prompt files"; the stop covers "another model or commit, or an edit to the hashed prompt files". Gap itself flagged (Q8) | No |
| Claims 3 | "Both sides of every comparison" used the same thinking level | **Corrected.** "Every memory comparison", which the record supports | No |
| Claims 4 | Pairing finding generalised to "decision scores", "almost all" | **Corrected.** One decision score (town vote accuracy), eight deals each played twice; "came mainly from" | No |
| Claims 6 | "The memory tests rested their verdicts on decision scores" | **Corrected.** "The final memory test rested its verdict on a decision score" | No |
| Claims 7 | Wrong mechanism: the fingerprint holds no memory setting; "every side" ambiguous | **Corrected.** §4 opener: the fingerprint "records only part of the set-up, and only as configured". The arm fault reads "gave memory to every faction, the wolves and the serial killer included". The two records disagree on which arm was affected: flagged (Q7) | Owner |
| Claims 8 | "Model service and region" wrong for current non-Google games | **Corrected.** Field dropped from the list and from the exhibit row; reason in the sources comment. Whether to name the gap: flagged (Q8) | No |
| Claims 10 | "Matching does nothing" contradicts "very little" | **Corrected.** "Matching does little for this" | No |
| Claims 11 | Lineup adjustment would "remove real variation" | **Corrected.** "Could adjust for it without bias, which may reduce noise" | No |
| Claims, not checked | Turn replay runs all versions in one session | **Kept** as the controls report states it; replay code not inspected. Low risk | — |

**Length after revision:** 2,188 words of page copy including tables and captions (2,159 before review;
guide 1,200–2,000). The additions with a reason: the June reconciliation (blocking finding, about 55
words), the ten-player and test-set definitions the reader needed (about 35), and the single-check scope
on the noise figures (about 20). They were offset by trimming the rubric example, the pinning paragraph,
the final-test paragraph and the driver detail. Further cuts would take explanation out of the featured
June section (490 words) or the guards, so I stopped here. If the owner wants the page at 2,000, the
next cut is the decision-score example in the exhibit row and the second sentence of §5's opener.

**Second review:** not needed. The section order, the central answer and the featured story's
conclusion are unchanged. The edits rescope claims and add definitions; none changes the argument.

<!-- Source notes for the brief (not page copy):
June numbers: controls report "The case that set the rules"; paired_ab log lines 5–22 (byte-identical play
prompts; play-path code unchanged since the baseline commit), 24–38 (not pinnable; served version echoes the
alias), 61–67 (20 recovered ids + 10 fresh). Re-test 12 → 7, 7 W→L, 2 L→W, p = 0.18: controls report and the
L3 page's verified script output.
Pinning: controls §1 (provider pages checked 2026-10-25). Embedding check: controls §1 (12 pairs, 0.02, stops
before spending; memory runs; no record of it firing).
Same-window enforcement: controls control table; driver.py `_run_arms_parallel`, guard calls at lines 257,
326, 343–345.
Fingerprint fields: Agents/run_fingerprint.py `runtime_fingerprint`.
Arm guard: invariants.py `assert_arm_declared` (declare or waive), `assert_arm_factions` (read-back);
deterministic audits case 5; controls §1 (2026-07-19 run, four town roles). "Round of games" = the loop's
"generation".
Thinking level: controls §4 (2026-10-04; "minimal" → no reasoning tokens; reasons from "low"; both sides
same; test-set runner records reasoning tokens since 3e05e8a7; game records carry the configured level).
Noise: turn report §2 item 1 and "biggest limit"; scoring/controls §3 (1–2 of 267).
Pairing: controls §3; game report "What pairing turned out to buy" (0.249 within, 0.21–0.26 across; nine-seat).
Sample size: controls §3 (0.18 / 36 points / ~100 games for 0.10). Simulation: v7 report "Testing the test"
(24 games, six generations, +0.15 found ~1 in 9; false alarm 2–3%).
Endpoint method: game report case 2 "What and why", "How it works" (method only).
Measurement: controls §2 (74% → 63%).
Next steps: controls "What we would do differently" rows 1–4; levers audit Lever 2 correction 2026-10-23. -->
