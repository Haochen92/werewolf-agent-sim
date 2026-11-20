# Authoring brief: Designing fair comparisons

Page: `writeup/evaluation/fair_comparisons/fair_comparisons.skill.md` · Level 2 · started 2026-10-28 · checkpoint: approved in conversation; defaults accepted for all open questions

Authoring material, not page copy. The cold editorial reviewer never sees this file.

Trial run of the `write-portfolio-page` skill (steps 1–3 only; full rewrite). The existing page copy
was not read; its brief and sources comment were read from the supplied packet.

## Frame

- **Primary page type and level:** design decision (how to set up a comparison so its result means
  what it seems to), at Level 2.
- **Secondary mode, if needed:** the featured section (the June baseline) borrows the diagnostic
  mode: symptom → two explanations → the reanalysis that could not separate them → the rule adopted
  anyway. The closing section borrows comparative evaluation's "what is established".
- **Existing outline approval:** approved in conversation 2026-10-28 (owner reviewed the Frame and
  Argument outline; approved as proposed, with the stated default for every open question).
- **Reader's question:** when version B scores better than version A, how do you know the difference
  came from the change and not from something else?
- **Central answer:** a difference counts as evidence for the change only when the two sides differ
  in nothing else and the gap is larger than what repeating one version produces; I matched the
  inputs and the measurement by design, had code check that a run matched its declared set-up, and
  measured noise before reading results. A baseline that moved for a reason that was never found is
  why both sides now run in the same time window.
- **Distinctions the reader needs:**
  1. A difference *between* the sides (another model service, another set-up, another judge) fakes an
     effect; randomness *within* each side (sampling at temperature 1.0, games drifting apart) mimics
     or hides one. They need different tools: matching and checks for the first, noise floors and
     test size for the second.
  2. Recording a setting, enforcing it, and checking it did what it names are three different things:
     the fingerprint records, a guard stops the run, a probe found a recorded setting that did nothing.
  3. Same deal is not the same game: a matched start, then play diverges.
  4. (Inside the featured section only) reading games as independent versus reading the shared deals
     as pairs.
- **What the evidence establishes:** the June baseline moved on unchanged prompts and code (1 of 10
  fresh deals to the town against 20 of 30 earlier); on the 20 deals played in both periods the
  town's wins fell 12 → 7, a split chance produces about 18% of the time. The code-enforced controls
  work where they apply: the fingerprint stops a learning-loop run that changes mid-run; the memory
  guard refuses to start without a declaration and stops on a mismatch; a game id reproduces its
  deal. Noise was measured at three levels (re-judging, re-sampling one case, re-running a model).
  Pairing by deal bought almost no noise reduction on the nine-player game. A simulation retired a
  test that would have caught a realistic improvement about 1 time in 9.
- **What stays uncertain:** the June shift's size and cause (drift on a model name that could not be
  pinned, or chance); the same-window rule is enforced by code only in the memory-experiment driver
  and the replay tool, by hand elsewhere; across runs a person compares fingerprints; game records
  hold the configured thinking level, not what it produced; the paired design that replaced the
  retired test was never sized; pinning fixes a model's identity, not the provider's serving stack;
  the ten-player game's dealt lineup is not yet used to reduce noise.
- **Stays off the page:**
  - Drift asserted as fact; "a model-service change" (say "a baseline that shifted"; drift only as
    suspected).
  - "Every comparison runs side by side" (enforcement varies by runner).
  - The overnight canary of 2026-06-12 (never re-tested): left off entirely.
  - Runs from uncommitted trees: the real capture stamp in the fingerprint report
    (`phase3_games/game1`) has `git_dirty: true`, so it cannot be the exhibit as is; dirty-run caveats
    and the "12 of 16 runs from uncommitted code" line stay off.
  - The endpoint test's missing final-number script and its git-ignored per-game data; its result
    (Memory chapter's).
  - "+17pp, p = 0.013" and the 0.14% rate; test counts or test authorship; no CI.
  - Research labels ("pre-registration", "power analysis") on the page: describe the practice
    (owner ruling 2026-10-28; sources comment may keep the terms).
  - The thinking-level finding is told as caught and what changed, with its scope; not grouped with the
    baseline and the arm guard as "three faults that were fixed".

## Evidence selection

| Material (source) | Role | What it helps the reader understand or assess |
|---|---|---|
| June baseline: 1/10 vs 20/30, byte-identical prompts, no play-code change, model name with no dated version, served version echoes the name (controls "The case that set the rules"; paired_ab log lines 5–38) | essential | The featured case: a difference with nothing changed, and why its cause could not be found in the records |
| Paired re-test 12 → 7, 7 W→L / 2 L→W, ~18% by chance (controls report; `june_baseline_shift_check.py`) | essential | That the dramatic reading shrinks to "moved, size and cause unknown"; the L3 anchor |
| The rule: both sides in one window, never against historical runs; the 20 deals re-played (controls; paired_ab log) | essential | The decision the case produced, and why it stands although the cause is unknown |
| Same-window enforcement: loop driver pairs both sides' games in one pool; replay tool runs versions in one session; general batch tool does not alternate (controls §1; `driver.py _run_arms_parallel`) | essential | The rule's reach; keeps "every comparison" off the page |
| Two kinds of variability need different tools (controls "When does a comparison need a fresh baseline?") | essential | The page's organising distinction |
| Same deal from the game id; same deal ≠ same game (controls §1; game report "How a whole-game comparison is set up") | essential | What "matched" means, and why pairs are two plays of one start |
| One judge, both sides in one run; rubric split moved another label 74% → 63% on the same messages (controls §2) | essential | That measurement differences can pass for play differences |
| Fingerprint fields; stops a learning-loop run within the run; across runs a person compares (`Agents/run_fingerprint.py`; `invariants.py assert_fingerprint_consistent`; fingerprinting report §1, §7) | essential | "Records" vs "enforces"; the exhibit |
| Arm guard: a June memory run gave memory to every side while believed town-only ("a plausible wrong number, no error"); declare-or-waive before start, read-back each round (deterministic audits case 5; `invariants.py`) | essential | A silent set-up error and the code check that now stops it |
| Thinking level "minimal" produced no reasoning tokens (2026-10-04 probe); both sides matched, so scope narrows; replay runner now records tokens, game records do not (controls §4) | essential | "Recorded" is not "did what it names" |
| Noise floors: re-judging 1–2 of 267; one vote prompt 8/10 then 1/10; two runs of one model ~6 points at 70 samples (controls §3; turn report §2 item 1; scoring layer 3) | essential | What "bigger than noise" means, at the judge, the case and the run |
| Pairing bought little: spread within a deal ≈ across deals (0.25 vs 0.21–0.26), nine-player only; same window was what mattered (controls §3; game report "What pairing turned out to buy") | supporting | Corrects the natural belief that pairing is the main control |
| Detectable sizes at 30 games a side: ~36 points of win rate, ~0.18 vote accuracy; ~100 a side for 0.10 (controls §3) | supporting | Why decision scores, not wins; links to play metrics |
| Sizing the test before paying: planted +0.15 found ~1 in 9 at 24 games; false alarms 2–3%; not run for the paired design that replaced it (controls §3; v7 report "Testing the test before paying for it") | essential | Deciding the test before the games: size |
| Fixing the analysis before the data: measure, number of games and reporting fixed before any game; one written change before data (game report case 2, method only) | essential | Deciding the test before the games: what counts |
| Pinning: removes a model swapped under one name, not serving-stack changes; the June model had no version to pin; backends differ even at temperature 0 (controls §1) | supporting | What pinning adds to the same-window rule, and what it cannot |
| When a fresh baseline is needed: fixed bar → no; same day → not necessarily, but interleave and read against noise; different days → yes (controls fresh-baseline table) | supporting | A practical decision rule; one paragraph or a three-row table |
| Bottom line + four "next time" rows (controls) | essential | The closing: code-enforced vs remembered; the next steps |
| Embedding check (12 pairs, 0.02, stops before spending; no record of firing) | optional | One clause among the run checks, memory runs only |
| Ten baseline games on fixed seeds before a cross-day reading | optional | "Can show something moved; a clean result does not prove nothing did" |

Left out, and where it lives instead:
- Winners by side, the transition table and the test names → [paired_baseline.md](../paired_baseline.md).
- Three meanings of "pairwise" as a list → sources comment (the page uses the distinction, not the list).
- Per-provider pinning details and dates → sources comment.
- Prompt golden, provenance manifests, run graduation, worktree-on-tag → sources comment (record-keeping, a different question from fairness); worktree-on-tag possibly one clause.
- Judge from neither side (self-preference) → LLM judges page.
- Memory A/B results, the endpoint result → Memory chapter.
- Costs → off (incomparable units).
- Fingerprint known gaps (role cards outside the prompt hash, served games unstamped) → chapter 7's fingerprint page; here only "a person compares across runs".

## Argument outline

Structure: **two sources of a false difference, with the featured case as the hinge between them.**
The page first covers what can make the two sides differ (inputs and judge, then the run's own
set-up), then the one thing matching and checks cannot hold fixed (the service over time), told
through the June baseline. That case's reanalysis could not rule out chance, which opens the second
half: randomness and how big a test must be. This fits the subject because the reader's question
splits naturally into "is the difference real" and "is it the change", and the June case is the one
place where the two could not be told apart. Execution order would scatter the June case; chronology
would bury the distinction.

| # | Section (working heading) | Question it answers | Main point | Carried by (example / finding) | Why the next section follows |
|---|---|---|---|---|---|
| 0 | Opening (no heading) | Why does a comparison need designing at all? | Comparisons here are small (about 30 games a side, or a few dozen saved turns) at temperature 1.0, and much can change with no code change. A difference means something only if the sides differ in nothing else and it beats what repeating one version produces. Two tools follow: matching and checks; noise and test size. | Plain statement of the two conditions; one line naming the June case as the case that set the main rule | Start with what can be made identical by design |
| 1 | Giving both sides the same start and the same judge | What can be held identical, and how? | The game id fixes the deal; a replay rebuilds the same turn from saved state. Same deal, not the same game. One judge scores both sides together, because judging them separately can move a score with no change in play. | Deal from game id; the rubric split that moved another label 74% → 63% on the same messages, so the old games were re-read beside the new | Matching the inputs assumes the run actually used the set-up it declares |
| 2 | Checking that the run is the one declared | How do you know the run had the set-up you think? | Recording, enforcing and checking the effect are different. The fingerprint records each game's set-up and stops a learning-loop run that changes mid-run; across runs a person compares. The memory guard exists because a run gave memory to every side while believed town-only. A setting can be recorded correctly and do nothing. | **Exhibit FC-record** (annotated record: recorded / checked in a run / compared by a person / not covered). Arm-guard incident; thinking level that produced no reasoning tokens, scope narrowed, both sides matched | Matching and checks hold what the project controls; the model service is not one of those things |
| 3 | A baseline that shifted with nothing changed (featured) | What happens when something underneath moves? | Fresh games gave the town 1 of 10 against 20 of 30 earlier, on identical prompts and code. The model had no dated version to pin, and responses reported only its name. On the 20 deals played in both periods, read as pairs, wins fell 12 → 7, which chance produces about 18% of the time. Size and cause are not established; drift is suspected. Because the records cannot tell them apart, both sides now run in one time window and new results are never compared with old runs. | Short two-row "two readings" table (independent vs paired); the decision. **Link to Level 3** beneath | The rule only helps where it is applied |
| 4 | Keeping both sides in one time window | How is the rule applied, and what does pinning add? | The memory-experiment driver runs both sides' games in one pool, paired by deal; the replay tool runs all versions in one session; the general batch tool does not alternate, so other whole-game comparisons are interleaved by hand. When a fresh baseline is needed (fixed bar / same day / different days). Pinning removes one source of drift, not all of it. | Enforcement split; the three-case decision rule; pinning's guarantee and its limit; backends differ even at temperature 0 | The June reanalysis could not rule out chance: the other half of the problem |
| 5 | Reading a difference against noise | How big must a difference be before it means anything? | Measure how far results move with nothing changed, at each level. Pairing by deal ruled out "one side got easier deals" but bought almost no precision; the window mattered more. At 30 games a side only large effects show, so the comparisons lean on decision scores. | Re-judging moves 1–2 of 267; one prompt 8/10 then 1/10 (habits: unchanged side twice, interleave); same model ~6 points apart; within-deal ≈ across-deal spread; ~36 points of win rate detectable | Knowing the noise lets you decide, before paying, whether a test can see the effect at all |
| 6 | Deciding the test before the games | How do you stop the analysis bending to the data? | Size the test before paying: a simulation planted known improvements in pretend runs from real games and showed the planned test would catch a realistic one about 1 time in 9, so it was dropped before money was spent. For the final memory test, the measure, the number of games and how a null would be reported were written down before any game; the plan changed once, in writing, before data. | Simulation (24 games, +0.15, ~1 in 9; false alarms 2–3%); endpoint method only, result linked to Memory; scope: the replacement design was never sized | Pulls together what the controls cover |
| 7 | What the controls establish, and what still depends on a person | What can a reader trust? | Strong where code enforces: deal from id, rebuilt turn, fingerprint within a run, memory guard. Weaker where a person remembers: interleaving outside the loop, comparing across runs, checking a setting did what it names. The June cause remains unknown. Next steps: interleave in every batch tool, record reasoning tokens per game, size each design before paying, use the dealt lineup on the ten-player game. | Controls report "Bottom line" and "next time" rows | — |

Outline check (main points alone, in order): two conditions → match start and judge → check the run
matches its declaration → the service moved anyway and the cause could not be found → so both sides
run together, enforced here and by hand there → randomness still needs a measured floor → decide the
test's size and reading before paying → what is enforced and what is remembered. This answers the
frame's question. No section needs a later term: "deal" is defined in 1, "pairs" in 1 (same deal on
both sides) before 3 uses it; "noise floor" arrives in 5, after 3 only says "chance".

Length plan: about 1,700–1,950 words including the exhibit and the small table. If it runs long,
section 4's decision rule and the embedding clause are the first to move to notes.

## Open questions

Questions that would change the outline (default if no answer):

1. **Statistical test names on the page.** Default: none on Level 2 ("reading the games as
   independent" vs "comparing each shared deal with itself"); Fisher and McNemar stay on the Level 3
   page, per the 2026-10-28 applied-rigour ruling.
2. **Featured case placement.** Default: section 3, as the hinge between the two halves, with one
   line in the opening. Alternative: open the page with it (the Level 1 summary already leads with it).
3. **Thinking-level finding here or on "Evaluating models before switching".** The Level 1 challenge
   table points to both. Default: here, short, as the "recorded is not done" example; the models page
   cross-links.
4. **The endpoint test (method only).** Default: one paragraph of method plus a link to the Memory
   chapter for the result; no number from it on this page.
5. **Exhibit record.** The real stamp in the fingerprint report is from a modified working tree.
   Default: find a clean batch record while drafting; if none, show the field list with annotations
   and no values, labelled as the record's structure, not a real game.

Raised by the review (2026-10-28), for the owner:

6. **The trend test and money.** The v7 report says both that "the June runs had been read this way"
   (a paid run) and that the test was "dropped … before any paid run used it"; the controls report says
   "retired before any money was spent on it". The page says only "the trend test was dropped, and the
   next paid run used a different design", which is true either way. Which statement should the records
   keep?
7. **(Closed 2026-10-29: the criterion is recorded, 80% power at p < 0.05 for two arms of 30, in
   `drift_surfaces_and_guards.md` line 136; the page now says "would be detected four times in five".)**
   What "show reliably" means for 36 points / 0.18 / 100 games. The controls report gives the sizes
   without the criterion (power level, test). The page says "show reliably"; give the criterion if it is
   recorded somewhere, or keep the soft wording.
8. **Length.** (2026-10-29: now 2,387 after the revision pass; see "Revision pass 2026-10-29" for the
   reasons per long section.) Was about 3,040 words of page copy before the evidence list, against the guide's 2,000; the
   review added definitions a cold reader needed. If it must shorten, the first candidates are: section
   6's simulation paragraph (a "possible" Level 3 candidate in the content plan, "Testing the test before
   paying for it"), and section 4 merged into section 3's end. Default: leave as is; the guide is not a cap.
9. **Naming a provider.** (2026-10-29: the pinning paragraph moved to the supporting notes for length;
   this applies only if it is restored.) Section 4 named Anthropic as the source of the pinning statement (the reviewer
   asked for attribution). Default: keep it; replace with "one provider" if a company name is unwanted.
10. **The plan change after the learning games.** The page now states that the change came after the
    store-building games, whose memory-on and memory-off scores existed by then, and that the main
    measure and the reading of a null were unchanged. Confirm this framing is how you want to defend it.

Raised by the round-2 review (2026-10-29):

11. **Did the final memory test's main comparison change?** `PREREG_AMENDMENT.md` says "Primary
    readout unchanged: final-store ON vs OFF"; the v7 report says the signed main comparison was the
    final store against the first-round store and that the change "changes the question". The page says
    only that the three versions became two and that every comparison against the first-round store
    went with it, which is true either way. If the v7 report is right, add "the main comparison changed
    with it" (this also bears on question 10).
12. **First person.** The opening says "I matched … and had code check …". These are design decisions,
    and the wording doesn't claim who wrote the loop code (`evaluation/src/loop/`). Confirm you want to
    claim the decisions in the first person.

Factual questions (affect claims, not the outline):

- The fresh-baseline table says the replay baseline "costs cents, re-run by default"; that is a
  practice statement. Kept as "re-run by default" only if confirmed as current practice; default
  phrasing: "cheap enough to re-run alongside".
- "Same window" enforcement for replays: the controls report says "both sides run in one session";
  not re-checked against the replay tool's code in this pass (the claims reviewer could not check it
  either).
- Whether the 20 "recovered" baseline results are the original 30 games' own records (they came from
  an extraction batch file when the seed set was built); the page's "20 of those games" depends on it.
- Whether the declare-or-waive gate existed when the July run started (2026-07-17): inferred from
  `unchecked_arm: false` in that run's config; git history was not checked (the command needed
  approval).

## Drafting notes (step 4, 2026-10-28)

- Open question 5 resolved: the exhibit uses a clean record, the July learning-loop build run
  (`evidence/memory_system/v7/execution_plan/data/v7_compound_town5/`: fingerprint with no uncommitted
  changes, the declared town-only memory roles, the roles read back in all four rounds; ten games a side
  per round, checked in `summary.json`). Its player thinking level is "minimal", so the exhibit also
  carries the "recorded but did nothing" point.
- Changes from the outline: section 4 lost its fresh-baseline decision rule and the cross-day check
  (moved to the supporting notes in the page's sources comment, as the length plan named); the
  embedding check was not used. Section 6 ends on its own scope line (the paired design was never
  sized) instead of leaving that to the closing. No change to section order or main points.
- Length: about 2,600 words of page copy before the evidence list, over the 1,700–1,950 plan and
  the guide's 2,000. The longest sections are 2 (run checks, with the exhibit) and 3 (the featured
  case). Section 4 is now short (about 160 words) and could merge into section 3's end if the editorial
  reviewer finds it thin.
- Skim (headings, first sentences, captions): the argument follows. Two captions described their
  tables without the point; both now state it. Section 3 opens on a transition sentence and reaches the
  incident in its third paragraph; left as is, since the heading carries the point.

## Review resolution

Reviews: `fair_comparisons.skill.review-editorial.claude.20261028T145747Z.dyWBdZ.md` and
`fair_comparisons.skill.review-claims.claude.20261028T150047Z.TCV1iT.md`. Resolved 2026-10-28.

| Reviewer | Finding (passage) | Action: fixed / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| Editorial 1 (blocking) | The game is never described; "evil player" undefined | Fixed: the opening now names the game, its two sides, day and night, and both game sizes | No |
| Editorial 2 (blocking) | Memory, learning loop, round and store undefined before the guard | Fixed: "Enforcing" paragraph defines them; the exhibit caption and section 6 tie the July run to the final test | No |
| Editorial 3 + Claims 3 (blocking / overstated) | The two-readings table read as pairing undoing the 1-in-10 result | Fixed (reasoning): the table is labelled as two comparisons on different games; the 10 new deals named as the strongest sign; pairing explicitly not the source of the change; consistent with the Level 3 page | Yes, if the central claim is re-reviewed |
| Editorial 4 | "Reused 20 of those deals" read as replaying them | Fixed: "reused the recorded results of 20 of those games, without replaying them" | No |
| Editorial 5 | "Decision score" undefined; "spread" unnamed | Fixed: the pairing figure is the share of town votes against an evil player, as a standard deviation (source checked: paired_ab log line 128); the decision score is defined at its first use | No |
| Editorial 6 | "Same judge, different times" claim backed by a rubric change; 74% of what | Fixed: claim narrowed to scoring in separate runs; the label and its share of messages named | No |
| Editorial 7 | Three safeguards vs "second guard" counted inconsistently | Fixed: section restructured as Recording / Enforcing (two checks) / Checking the effect, with the third stated as mostly manual | No |
| Editorial 8 | "0.10" without unit; no detection criterion | Partly fixed: unit given (vote share). The criterion is not stated in the source; wording follows the game report ("show reliably"). Flagged (open question 7) | Owner |
| Editorial 9 | Which run was "the previous paid run"; +0.15 per round or overall | Fixed: "an earlier paid loop run in June, four games in each of six rounds"; "a rise of 0.15 in the score across the six rounds" | No |
| Editorial 10 | Factual-error test set, 267, test set, quality check undefined | Fixed: each bullet says what is scored and counted; the 70-turn set is named as its own set | No |
| Editorial 11 | Which game each experiment used | Fixed: both sizes in the opening; June, the July run and the final test marked nine-player | No |
| Editorial 12 | Temperature-0 backend claim and the provider statement unattributed | Fixed: the project's own measurement (one judge, 76.9% → 73.8%) and the provider named | No |
| Editorial 13 (taste) | "Fallen back to defaults"; was the exclusion fixed in advance | Fixed by removal: the signed plan names only halts and partial results, so whether this rule was set in advance is unclear; the claim left the page (kept in the sources comment) | No |
| Claims 1 (conflicts) | The plan "changed … before any game" | Fixed: changed after the store-building games, before any test game; the two recorded reasons given; main measure and null wording unchanged. The game report's case 2 wording is the source of the error (step-7 list) | Yes (central to section 6's argument; re-review recommended) |
| Claims 2 (wrong mechanism) | Loop "so neither side runs after the other" | Fixed: each round's games for both sides run as one block in the same hours; the final test started each deal's two games together (endpoint log checked) | No |
| Claims 4 (unclear) | Exhibit "town roles only" while tells reached every seat | Fixed: rows relabelled as per-role lesson memory; the caption states that the tell list was shown to every seat by design (v7 report "The pre-registration") | No |
| Claims 5 (overstated) | Opening generalises code checks and the same-window rule | Fixed: "in the memory experiments' multi-round runs"; "the rule has been that …" | No |
| Claims 6 (wrong status) | "Two habits followed" | Fixed: "so far used in only some replay experiments" | No |
| Claims 7 (records disagree) | "Dropped before any money was spent" | Worded to be true either way ("the next paid run used a different design"); flagged (open question 6) | Owner |
| Claims 8 (overstated) | Fingerprint on "every game record", "the prompt files" | Fixed: "every experiment game record"; "a hash of the main prompt files". Fingerprint gaps stay on chapter 7's page | No |
| Claims 9 (overstated) | "The memory runs have a second guard" | Fixed: both checks scoped to learning-loop runs, here and in the closing | No |
| Claims 10 (minor) | "Every game until then"; "the turn-replay runner" | Fixed: "every memory-experiment game"; "one turn-replay runner" | No |
| Claims, not checked | Replays run in one session; the 20 recovered deals among the original 30; the gate existed on 2026-07-17 | Kept as worded; listed in open questions. The exhibit row was softened to "Declared before the first game" (the config records the declaration and `unchecked_arm: false`) | Owner |

## Revision pass 2026-10-29

Owner ruling: a Level 2 page does not re-introduce the game or the project; the reader arrives from the
chapter page's introduction and its "Designing fair comparisons" section (`scripts/parent_context.py`).
Plus the length guard (about 1,200–2,000 words of page copy).

**Word count (page copy before the evidence list, tables and captions included):** 3,036 → 2,387
(3,124 → 2,475 with the evidence list).

**Removed or moved** (all kept word for word in a "Supporting notes" comment in the page file):
- The game introduction (sides, day and night, the two game sizes) and "many things can change without
  editing the code": the excerpt and earlier pages give the context. The opening now starts from the
  chapter summary's controls ("Behind the controls in the chapter summary is a two-part test") instead
  of restating them.
- The June game's town composition (game context, not needed for the argument).
- The frozen-turn replay explanation and its link (the replays page's question).
- The pinning paragraph, with the provider attribution (answers "would pinning have prevented it?").
  Open question 9 applies only if it is restored.
- The temperature-0 backend measurement (a different question: which service must match).
- The model-rerun noise bullet (the model-admission page's question).
- The link to the play-metrics page, the exhibit's temperature row, and the endpoint run check
  "a deal counted only when both had finished".
- The simulation's method (line through the scores, resampling, the false-alarm rate): kept as its
  finding only; the method is marked in the notes for a possible Level 3 page ("Testing the test before
  paying for it", a "possible" candidate in the content plan).
- Structure: "Keeping both sides in one time window" (84 words after the pinning cut) merged into the
  featured section, directly after the rule it enforces. The page now has six sections after the opening.

**Unchanged:** every claim's scope and every open question (1–10) as qualified after the review. The
same-window enforcement split, the tells caption, the plan-change timing, the "next paid run used a
different design" wording and the "show reliably" wording are as before.

**Sections still long, with reasons** (the page stays above 2,000 at 2,387):
- *Checking that the run is the one declared* (571, including the exhibit table and caption, about
  200): it carries the page's only exhibit and the three separate jobs, each with the scope line the
  claims review required (experiment records only; loop runs only; per-role lesson memory only).
- *A baseline that shifted with nothing changed* (590, including the table and caption, about 100): the
  featured case; the two comparisons on different games must be explained on the page (the editorial
  review's blocking finding), and the rule's enforcement now sits here after the merge.
- *Reading a difference against noise* (364): noise at the judge and the single-turn level, the pairing
  result that reconciles the June reanalysis, and the decision-score definition that section 6 depends
  on.
- *Deciding the test before the games* (322): the content plan assigns the final memory test's method
  to this page (the memory chapter says its method lives here), and the plan-change timing is a claims
  fix that cannot be dropped without restoring the error.

Not re-reviewed after this pass. The opening and the merged section changed; a cold editorial read
with the parent excerpt would confirm the page no longer repeats it and still opens cleanly.

## Review resolution (round 2)

Reviews: `fair_comparisons.skill.review-editorial.claude.20261029T015518Z.OVs1mO.md` (cold read, given
the parent excerpt) and `fair_comparisons.skill.review-claims.claude.20261029T015810Z.UqOJym.md`.
Resolved 2026-10-29. Page copy 2,387 → 2,558 words (evidence list excluded).

| Reviewer | Finding (passage) | Action: fixed / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| Editorial 1 | Three groups of baseline games blur; why only 20 reused | Fixed: the 10 new deals are said to be outside the earlier 30; table rows name "the 20 reused deals" and "all 30 earlier games"; caption places the 12 inside the earlier 20 wins. "Why only 20": the page says these 20 had recorded winners, which is all the records say | No |
| Editorial 2 | Why 3 in 1,000 does not settle it | Fixed: the 10 new deals are only 10 games on deals the earlier games never played, so they cannot size the change (Level 3 page); "chance remains possible" now scoped to the like-for-like deals | Yes (central claim's wording; see below) |
| Editorial 3 | "Therefore lean on decision scores" without a number | Fixed: per-game spread of a decision-level measure against a win (about 0.25 against 0.5, recorded); added that small effects stay out of reach, matching the next section | No |
| Editorial 4 + Claims 2 | Three versions unnamed; the main comparison's change hidden | Fixed: the three versions named and the two kept. The records disagree on whether the main comparison changed (amendment: "primary readout unchanged"; v7 report: signed main comparison was final vs first-round store, "changes the question"). Worded to be true either way ("every comparison against the first-round store went with it"); flagged (open question 11) | Owner |
| Editorial 5 | The ten-player game not introduced | Fixed: one clause in the opening (most evidence is nine-player; the ten-player lineup varies). Belongs here: the page cites results from both games | No |
| Editorial 6 | Tells caveat reads as reversing "town roles only" | Fixed: the caption says the list was part of the memory side by design and that the check does not cover it. Declined to call it harmless: the records do not establish that | No |
| Editorial 7 + Claims 1 | "Did not gain precision by pairing" leans forward and conflicts with the Level 3 page | Fixed: "How much pairing helps for wins was not measured"; the forward reference is gone; the noise section now scopes its pairing result to town votes | Yes (central claim's wording) |
| Editorial 8 | "Evil player" vs "wolves" | Fixed: "a wolf or the serial killer" | No |
| Editorial 9 | 8 of 10 vs 1 of 10: was anything changed? | Fixed: "the identical vote prompt, on the same model … rerun in a later experiment". Checking the source showed the 8 of 10 were votes for the original failure target, so "the right player" (copied from the controls report) was wrong; now "chose the same player" | No |
| Editorial 10 (taste) | One paragraph does too many jobs; what the wrong number measured | Fixed: the memory-experiment definition is its own paragraph; "its conclusion about town memory came out plausible but wrong"; "one June loop run" separates it from the June baseline | No |
| Editorial 11 (taste) | "Final memory test" used before defined | Fixed: glossed in the exhibit caption | No |
| Claims 3 | Rubric: order of events | Fixed: re-read with the new rubric, and the move was seen on the same older messages | No |
| Claims 4 | Pairing result's sample not stated | Fixed: "two back-to-back memory-off runs … that shared 8 deals" | No |
| Claims 5 | Opening generalises test sizing | Fixed: "for one planned test, checked by simulation whether it was large enough" | No |
| Claims 6 | Thinking row states the zero tokens as observed | Fixed: "a later probe showed this level gives this model no reasoning tokens" | No |
| Claims, section 2 | The detection criterion is recorded | Applied: "would be detected four times in five" (80% power at p < 0.05, two arms of 30). Open question 7 closed | No |
| Claims, not checked | Replays in one session; the 20 reused results vs the original 30; the gate at the July commit; first-person ownership | Kept as worded; listed in open questions (ownership added as 12) | Owner |

**Growth past the guide, one reason per addition (+171 words):**
- Opening (+33): the claims-required scope on test sizing; the game-versions clause, needed because the
  page cites results from both games.
- Run checks (+16 net): the caption gloss for "final memory test" and the reworded tells clause,
  partly offset by moving the replay-runner clause to notes. Splitting out the memory-experiment
  definition added nothing. (The judge section fell by 4 words after the reorder of events.)
- Featured case (+32): naming the groups of games and why the 3-in-1,000 figure cannot size the change.
  This was the editorial review's top finding, and the like-for-like scope protects the central claim.
- Noise (+60): the pairing sample (claims), the detection criterion (closes open question 7) and the
  decision-score backing (editorial).
- Deciding the test (+34): the three versions named, which the conflicting records make necessary to
  word the change safely.

**Second review:** the structure did not change. The featured section's central claim was reworded
twice: the pairing sentence, and "chance remains possible" scoped to the like-for-like deals. A claims
re-check of those two sentences and the plan-change passage would be enough; a full re-review is not
needed.

## Step 7 edits not made in this trial (would have made)

- `writeup/evaluation/editorial_notes.md` does not exist; would create it (or add to the chapter's
  equivalent) with a dated entry: explanatory path, what moved out, claim changes, checked vs not
  verified.
- Page header line (status and date) on the new page.
- `writeup/evaluation/exhibits/source_map.md`: FC-record row (clean record or structure-only), and a
  new small row for the two-readings table if kept.
- `paired_baseline.md`: its closing link text ("Return to the same-window rule and the other
  controls") still fits; check the anchor heading name once drafted.
- `writeup/evaluation/evaluation.md` Level 1 summary: no change expected unless the outline changes
  the main finding.
- From the review (evidence records, owner's call; not page copy):
  - `evidence/evaluation/evaluation_scopes/game/report.md` case 2: "The plan changed once, in writing,
    before any game was played" → "after the learning games but before any test game" (as the v7
    report and `PREREG_AMENDMENT.md` say). Its "a game whose decisions fell back to defaults was thrown
    out" needs a source in the signed plan, or a note that the rule was not pre-specified.
  - `evidence/evaluation/experimental_controls/report.md` §3 and `evidence/memory_system/v7/report.md`
    line 156: reconcile "retired before any money was spent" / "before any paid run used it" with
    "the June runs had been read this way" (open question 6).
  - `experimental_controls/report.md` "When does a comparison need a fresh baseline?": "one vote prompt
    went to the right player 8 of 10 times" → the 8 of 10 were votes for the original failure target
    (`deduction_placement_n10/results.md`); say "chose the same player". (Found in round 2.)
  - `PREREG_AMENDMENT.md` vs `v7/report.md` on whether the main comparison changed (open question 11):
    reconcile once the owner rules.
  - `experimental_controls/report.md` control table: "both sides in the same time window ✅ in the loop
    driver" could note that within a round the memory-on games mostly start first (one shared pool,
    on-tasks queued first).
