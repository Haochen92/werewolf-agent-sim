# Authoring brief: Measuring play quality beyond win rate

Page: `writeup/evaluation/play_metrics/play_metrics.skill.md` · Level 2 · started 2026-10-28 · checkpoint: approved in conversation; defaults accepted for all open questions

Authoring material, not page copy. The cold editorial reviewer never sees this file.

Trial run of the `write-portfolio-page` skill (steps 1–3, then the owner checkpoint). The baseline page
(`play_metrics.md`) was not read; its brief and sources comment were read from the trial packet.

## Frame

- **Primary page type and level:** design decision (what to measure instead of the win, and why), Level 2.
- **Secondary mode, if needed:** comparative evaluation for sections 3–5 (checking scores against
  winning and testing whether they transferred). The check is how the design decision was tested, so it
  stays inside the one line of argument rather than becoming a separate methods section.
- **Existing outline approval:** approved by the owner in conversation, 2026-10-28, as proposed, with
  the stated default for every open question.
- **Reader's question:** When the win is too noisy to tell two versions apart on the number of games you
  can afford, what do you measure instead, and how do you know that measure means anything?
- **Central answer:** Code grades each decision against the true roles by the game's rules, as a rate
  over the chances a player had. A separate check then asks whether games with higher scores are games
  that side won. The two answer different questions. When the game expanded from nine to ten players,
  the check showed that the town's lynch scores still went with winning, while the healer's save rate no
  longer did, although a save is still a good move.
- **Distinctions the reader needs:**
  1. *An accurate count vs a useful proxy.* Code reads a score exactly from the record. That does not show
     that more of it goes with winning.
  2. *A move that is good by the rules vs a move whose rate predicts winning.* The healer is the case
     where the two come apart. The grade stays, and the rate's use as evidence that one version wins more
     goes.
  3. *Many decisions per game vs many independent observations.* The game stays the unit. The gain is a
     per-game number that varies less than one win/loss, not 150 extra samples per game.
  (Also kept beside the claims, though not one of the main distinctions: association is not cause, and a
  null on few games means "not yet tested", not "fails".)
- **What the evidence establishes:** On the nine-player game (50 games, then 180), the town's lynch and
  vote scores went clearly with town wins, and the check caught scores whose meaning looked obvious and was
  wrong: the investigator's find rate did not track winning, but turning a find into a lynch did. On 78
  ten-player games the core town scores kept their direction over all games, within batches and with
  memory off. The healer's save rate showed no association (−0.03, interval −0.26 to +0.20), and the
  healer's records show why that is plausible.
- **What stays uncertain:** These are associations, not effects. Why the healer's association changed is
  untested, and the comparison crosses both the game version and the models. Most new roles' scores rest
  on too few games to read. New-role directions were not written down before the run, so those rows are
  exploratory. With 32 scores examined, one or two could pass by chance. The per-decision grade table as
  a whole has never been tested against winning; the check tested per-game scores.
- **Stays off the page:** AI-written, unaudited tests (the grade table is "pinned by tests", so cite no
  tests). The ten-player runner being uncommitted at the time. No CI. Records outside git. No "memory
  helps" claim: the vote-accuracy memory/model split stays on the Level 3 page, and the memory outcome stays
  in the Memory chapter. Also left off: the three scorers switched to the role registry on the morning of
  the check. This is bookkeeping, it is already on the Level 3 page, and the check's own scorers were not
  affected.

## Evidence selection

| Material (source) | Role | What it helps the reader understand or assess |
|---|---|---|
| Win is one outcome per game, carrying the luck of the deal and everyone's play; decisions graded against true roles vary less (metrics report §1) | essential | Why the page exists |
| Detectable sizes at 30 games a side: about 36 points in win rate vs about 0.18 in vote accuracy; ~100 a side for 0.10 (experimental_controls report §3) | supporting (one sentence, link to Fair comparisons) | What "too noisy" means in game counts; the full sample-size explanation lives on Fair comparisons |
| Decisions within a game share one history; the game is the unit (replays_and_games page; `ten_seat_win_check.py` correlates one per-game score with one per-game win) | essential | Stops the reader taking "many decisions" as "many samples" |
| Early model judges ran only in memory-on games, so they could not compare on vs off (report §1) | optional (one clause at most) | Why code rather than a judge |
| Rejected: making every agent state a belief about each player, because it changes play and is circular (report §1) | optional (one or two sentences; see open question 2) | A transferable rule: the measurement must not change the thing measured |
| A good move is defined by the rules; graded against true roles (report §2; `grading.py` healer and vote grades) | essential | The scoring method itself |
| Opportunity-adjusted rate: saves ÷ protections that went ahead; a blocked night counts neither way; no chance → no score, not zero (report §2; `ten_seat_metrics.py` healer block) | essential (the worked exhibit) | Fairness across players who lived different lengths; and it defines the healer rate before section 5 relies on it |
| Luck inside one decision remains: a blind vote that hits a wolf scores like a reasoned one (report §2) | essential (one or two sentences) | Scope of "graded"; less lucky than the win, not luck-free |
| Check: per-game score correlated with own side's win, read on all games and on memory-off games (report §2; proxy_win_monotonicity) | essential | The second question and how it is asked |
| Nine-player result: town lynch share +0.65 (50 games), held at 180; investigator find rate −0.09/−0.14 vs find-to-lynch +0.40 (180) (report §3) | essential (lead example of the check catching a surprise) | Shows why the check is needed even when the rule looks obvious |
| Wolves accusing townspeople, expected + and came out −0.33 (report §3; log 2026-07-02) | optional | A second surprise; one is enough on Level 2 |
| Wolf night kills diluted by games the wolves could not win (+0.31 within 103 of 180) (report §2) | optional | A guard detail; Level 3 / evidence |
| How the approach changed: June check as the gate (48 tried, 11 kept); ten seats from twelve roles leaves too few games per role; credit needed a grade for every decision from game one; so rules first, check confirms or questions (report §2 "How the approach changed") | essential (the bridge to section 4) | Explains why a failed check removes a score's use as win evidence but not its grade |
| Port before the check: old scorers read fields the new game never fills, which gave zeros in the 28 balance games; rewritten to read the night record and to take sides from the role list (report §6; log B1) | supporting (two sentences, told as caught and fixed) | A score must compute before it can be checked; leads to the "write against sides" lesson |
| Ten-player check: 78 games, mixed models, 49 memory off; three readings (all, within batch, memory off) (report §4; data README) | essential | The sample and its guards, in brief; full method on Level 3 |
| Contrast table: lynch share +0.65 (50) → +0.49 (+0.30 to +0.64; 78), within batch +0.55, memory off +0.48; healer +0.36 (50) → −0.03 (−0.26 to +0.20; 75) (report §3–4; summary.json; exhibit PM-contrast) | essential (the page's main exhibit) | The finding |
| Healer records: ~1 save/game in won (1.07) and lost (1.03) games; protection nights 3.25 vs 2.48; 220 protections = 79 saves + 141 unattacked; 36 saved died later; 23 saves with another death that night (log 2026-10-24) | essential (featured story) | Why a good move can stop separating wins from losses |
| Owner's reading: harder guess with more information roles; one save decides less often (log 2026-10-24) | essential, labelled as a reading the check does not test | Interpretation kept apart from observation |
| Direct comparison of the two healer correlations (p ≈ 0.03 vs the 50-game estimate, ≈ 0.001 vs 180) | supporting, in words; the numbers stay on Level 3 (open question 4) | Shows the drop is unlikely to be chance alone, without claiming a cause |
| Cross-model caveat: nine-player Gemini models vs ten-player mostly Haiku (report §3 vs §4) | essential, beside the healer finding | Scope |
| Rare roles: vigilante fired in 19 games; investigator conversion 20 games; Sentinel +0.12 (−0.11 to +0.33); a null on few games = not yet tested (log; report §2) | supporting (one paragraph) | The "unvalidated, not failed" reading |
| New-role directions not written down in advance; 32 scores examined (report §4) | essential, beside the results | Scope |
| Grade table untested as a whole against winning (report §6) | essential (closing) | What the check did not cover |
| None promoted to "validated" in the live labels; the owner's decision (report §4) | supporting (one clause) | Current status |
| Next-version practice: write scorers against sides; record full night outcomes from game one; write directions before the first check; run the check on the first batch (report "What we would do differently" 1–4) | essential (closing) | What the finding changed |

Left out, and where it lives instead:
- Read Brier score (how well players' guesses matched roles) answers a different question, about guesses rather than decisions → evidence/metrics report §6; credit records.
- Counts used to judge prompt and rule changes (discussion census, the Phase 2 counts, balance batches) are a different question → Game design chapter / evidence.
- The keyword-count lesson (32 → 4 of 124) → factual errors or judge pages, if anywhere.
- Scheduler-starvation ruled out (58/58) and the whiff visibility finding → evidence (other questions).
- The vote-accuracy batch split, the within-batch method in detail, the full 32-score table, the information roles' 134 named / 81 lynched, and the necromancer survival tautology → Level 3 page.
- Leverage anchor, blend-tactic check, investigator transmission, the batch-summary tool → evidence.
- Statistics glossary (point-biserial, Fisher z) → named once on Level 3; this page says "correlation" and "95% interval".

## Argument outline

Structure: **successive questions**, the shape of example B. Each finding is the reason for the next
step: the win is too noisy → score decisions instead → but a rule-good move might not matter → so check
the scores against winning → the game changed, so did the check still hold? → one score that is still a
good move stopped predicting wins → what the scores can now support. Execution order (A's shape) does not
fit: there is no pipeline to walk. A methods-then-results layout would separate the healer story from
the distinction it teaches.

| # | Section (working heading) | Question it answers | Main point | Carried by (example / finding) | Why the next section follows |
|---|---|---|---|---|---|
| 0 | Opening (no heading) | Why does this page exist, and what is its answer? | The win is one noisy result per game. I grade decisions by the rules from the record, and check separately whether those grades go with winning. The two questions can give different answers, as the healer showed when the game expanded. | Central answer in plain words; no methods list | Sets up the first question: why not just count wins |
| 1 | Why the win alone is not enough | Why not compare versions on win rate? | One win/loss per game carries the luck of the deal and of every other player. At 30 games a side only a gap of about 36 points in win rate shows reliably. A per-game score built from graded decisions varies less, but the game is still the unit, because its decisions share one history. | Detectable sizes (one sentence, link to Fair comparisons); the "many decisions ≠ many samples" distinction | If not the win, what exactly gets scored? |
| 2 | Grading a decision by the rules | What counts as a good move, and how is it scored? | The rules define a good move (a town vote on an evil player, a protection that saves a townsperson). Code grades each one against the true roles from the engine's record, and divides by the chances the player had. Luck inside a single decision remains. *(Optional: one or two sentences on the rejected alternative, making agents state beliefs, which would change play.)* | **Exhibit:** one protection worked through to a per-game save rate (protected → attacked → lived → townsperson → good; saves ÷ protections that went ahead; a blocked night counts neither way) | An exact grade still does not show that doing more of it wins games |
| 3 | Does a good move go with winning? | How do you know a score means something? | Correlate each game's score with whether that side won; read it on memory-off games too, since memory can raise both. On the nine-player game the town's lynch scores passed clearly. The check also caught a surprise: the investigator's find rate did not track winning, but turning a find into a lynch did. Bridge: on the nine-player game the check chose among candidates. On the expanded game the rules come first (a table covers every kind of turn) and the check confirms a score or questions it. | Lynch share +0.65 (50 games), held at 180; find rate −0.09/−0.14 vs find-to-lynch +0.40 (180); why the approach changed (ten seats from twelve roles; credit needs a grade from the first game) | The game then changed. Did the scores still track winning? |
| 4 | When the game expanded (L3 link beneath) | Did the scores transfer to the ten-player game? | First the scorers had to compute: they were rewritten to read the night record and to take sides from the role list (caught when they read zero). On 78 games the core town scores kept their direction over all games, within batches and with memory off. The healer's save rate did not reproduce its earlier association. Most new roles' scores have too few games, which reads as untested, not failed. New-role directions were not written down in advance. | **Exhibit:** two-row contrast table (lynch share; healer save rate; nine → ten players, with games and intervals); vigilante in 19 games as the rare-role example; one sentence on the 95% interval | Why would a good move stop separating wins from losses? |
| 5 | A good move that decides fewer games (featured story) | What do the healer's records show? | The healer made about one save a game whether the town won or lost. What differed was how long the healer survived. Many protections guarded unattacked players, and some saved players died later or someone else died that night. My reading (untested) is that whom to protect is a harder guess and one save decides the game less often. A direct comparison makes chance alone unlikely, but it crosses game version and models, so it cannot say why. | 1.07 vs 1.03 saves; 3.25 vs 2.48 protection nights; 220 = 79 + 141; 36 died later; 23 with another death; cross-model caveat | So what is the save rate, and the other scores, still good for? |
| 6 | What the scores can support | What did the check change, and where does it stop? | A save is still graded good, and the grade still feeds memory's credit. Its rate no longer counts as evidence that one version wins more. The core town scores are supported in this sample; none has been promoted to "validated" in the live game's labels. Limits stated once and kept short: associations, not causes; 32 scores, so some passes by chance; one pool of games; the grade table as a whole untested against winning. For the next game version: write scorers against sides, record full night outcomes from the first game, write expected directions before the first check. | Report "What we would do differently" 1–4; report §6 | — |

Outline check (main points read in order): the win is too noisy → grade decisions by rules, as rates →
check grades against winning; the check catches surprises; on the new game rules come first → on the new
game the core held and the healer's rate did not → the healer still saves people, but saves no longer
decide which games are won → the grade stays, the rate's use as win evidence goes, and here are the
limits. This answers the reader's question. Term order: "rate over chances" (2) comes before the healer
rate (4–5); "memory-off reading" (3) comes before "within batch" (4, new there); "95% interval" is
introduced in 4 at its first use; "proxy" is introduced in the opening or 1. No section needs a later
result.

Length plan: about 1,500–1,800 words with two exhibits (worked score; contrast table).

**Drafting notes (2026-10-28, step 4).** Drafted from this outline with no change to its sections or
order. Local changes: (a) the game's cast (town, wolves, lone killer; "threat" defined) moved from the
opening into section 2, where grading first needs it; (b) the worked exhibit is an illustrative
three-night healer, labelled as such, not a recorded game; (c) in section 4 the port is in the passive
voice, because who rewrote the scorers is not recorded; (d) models are left unnamed on the page ("an
earlier set of models"), with the names in the sources comment; (e) one supporting town score was
added beside the lynch score in section 4 (power roles lost at night; −0.55 in the source, given in words on the page) to show "several other
town scores" carried over. Skim fixes: section 2 now opens on its point (the rules define a good
move) rather than on background; a repeated "steadier measurement" sentence in section 1 was cut.

## Open questions

1. **How strongly to claim that decision scores are more sensitive than wins.** The sources give the
   detectable sizes in different units (0.18 in vote accuracy vs 36 points in win rate at 30 a side), and
   no source puts them on a common scale or shows that a realistic version change moves vote accuracy by
   0.18. *Default:* state both detectable sizes and link Fair comparisons. Say that a per-game score varies
   less, as the metrics report does. Make no "N times more sensitive" claim.
2. **Rejected designs.** Keep one or two sentences on the rejected "make every agent state its beliefs"
   design (it changes play and is circular)? It is a transferable lesson but answers a slightly different
   question. *Default:* keep it, as two sentences at the end of section 2. Drop the uncertainty-weighted
   vote design.
3. **First person on the grade table and the code.** The record says the table is "the owner's ruling",
   so "I set out a table…" is supported. Who wrote the scorer code is not recorded on this subject.
   *Default:* "I defined what counts as a good move; code applies it", with no claim about who wrote the
   scorers.
4. **The healer's direct-comparison p-values** were computed for the Level 3 page (owner-approved there),
   not in the evidence record. *Default:* on this page, state the result in words ("a direct comparison of
   the two correlations makes chance alone an unlikely explanation") and keep the numbers on Level 3.
5. **"Two killers a night" in the owner's reading.** The nine-player game also had two killing sides, so
   the number of killers is not a difference between the games. *Default:* follow the Level 3 page. Use
   the 23 saves where someone else died as the observation, and avoid presenting the number of killers as
   what changed.
6. **Nine-player investigator numbers.** The find-rate figures (−0.09, −0.14) are from the 50-game June
   check and the find-to-lynch +0.40 is from the 180-game July audit. *Default:* name the game count beside
   each figure, or give the finding in words without the find-rate numbers.

Added at step 6 (2026-10-28), each worded on the page so it is not wrong either way:

7. **Who designed the June per-game scores.** The record attributes the ten-player grade table and the
   method reading to the owner, but not the June per-game score design. *On the page:* "the evaluation
   measures decisions as well" (neutral). "I set out a table" stays, since the table is the owner's
   ruling. Owner: may the opening say "I"?
8. **The sensitivity argument (central claim of section 1).** The fair-comparisons sizes (36 points in
   win rate, 0.18 in vote accuracy at 30 games a side) fit the same formula with spreads of about 0.5
   and 0.25. That is the same fraction of each measure's own spread, so they cannot show that a decision
   score detects changes with fewer games. This is my inference; the report's spread figure does not
   name its metric. The metrics report's "many graded decisions vary far less than one win bit" is
   therefore unshown in like-for-like units. *On the page:* the score "sits closer to the behaviour a
   change is meant to improve", and how many fewer games it needs "has not been measured". Owner: is
   there a record that settles it (e.g. a planted-effect power run on a decision score versus the
   win)? If so, section 1 can say more. If not, the metrics report's §1 sentence may want the same
   softening (a step 7 item).
9. **The rejected belief-output design.** Since July, agents do write a read of every other player
   before each decision, and the reads are scored (read Brier). The June rejection's reason ("it would
   change how agents play") therefore needs a date and scope the page could not give cleanly. *On the
   page:* the paragraph is removed. This overrides the accepted default for open question 2. Owner:
   restore it with a date and scope, or leave it out?
10. **Current status: no score marked validated for the ten-player game.** It was verified in code by
    the claims reviewer on 2026-10-28, and it is the owner's decision. *On the page:* "a separate
    decision, not taken at the time of writing". Owner: confirm, or drop the sentence.
11. **Length.** *Resolved 2026-10-29 by the revision pass (about 1,990 words); the candidate cut below
    was taken.* The page copy was about 2,490 words (the guide is 1,200–2,000, not a cap). Section 4
    (about 710) carries the cast change, the change of method, the scorer rewrite, the check's setup and
    the results. *Default:* leave it. A candidate cut, if the owner wants one, is the change-of-method
    paragraph. It explains a separate decision (grades for memory credit), and the Memory chapter could
    hold it, leaving one sentence here.

Added at review round 2 (2026-10-29):

12. **Do the nine- and ten-player healer rates measure the same thing?** The nine-player denominator is
    "healer action-nights"; the ten-player one is protections that went ahead (blocked nights
    excluded). The nine-player game had no blocker, so they probably match, but this has not been
    traced. The direct comparison (p ≈ 0.03 against the 50-game estimate, ≈ 0.001 against the
    180-game one, both on Level 3) depends on it. *On the page:* the row label is "per protection
    night", which is true of both, and the caption says blocked nights are not counted on ten players.
    Owner or verifier: confirm.
13. **Nine-player healer counts.** The page says "the check has no matching counts for the nine-player
    game" (true of the check). Nobody has searched the nine-player audit logs for protection counts.
    If they exist, the healer section could compare against them, and the owner's reading would gain
    a test.
(OQ8 update, claims round 2: the page's Evidence list cites metrics report §1, which says "an effect
shows at a game count the project can afford". The page now says that saving is "expected rather
than shown". The two disagree until OQ8 is settled.)

## Revision pass 2026-10-29

Owner ruling: a Level 2 page does not re-introduce the game or the project. The reader arrives from the
chapter page (`parent_context.py` excerpt: the chapter introduction and its "Measuring play quality
beyond win rate" summary). This pass also applied the Level 2 length guide.

**Page copy:** about 2,490 words before → about 1,990 after (count includes the two tables). This is
within the 1,200–2,000 guide, so no section needs a length reason.

Removed or moved (all kept verbatim as numbered supporting notes in a comment before the sources
comment; none deleted):
1. The game and project re-introduction (opening paragraph 1). The chapter gives it; memory is now
   defined at its first use in section 3.
2. Why the win is noisy (opening paragraph 2; the luck-chain sentences in section 1). The chapter
   summary says it.
3. The first form of the two-questions framing (opening paragraph 3). It was replaced by an opening
   that continues from the chapter summary: "A play score answers two separate questions…". The
   roadmap sentence was cut as carrying no fact.
4. Cast details for both games (villagers retired, the neutral seat, six town roles). These are not
   needed for the central answer. The cast change in section 4 is one sentence; section 2 defines
   "evil player" (a wolf or the lone killer) in passing.
5. The nine-player gate (48 tried, 11 kept, with its chance caveat). It answers how June chose
   scores. The chance caveat on the page stays with the 32 ten-player scores.
6. The change-of-method paragraph (section 4), resolving OQ11's candidate cut. It is condensed to two
   sentences in the last section: the grade table feeds memory credit, and the check does not change
   the grades. The reasons the approach changed are in the note.
7. The scorer-rewrite details (28 balance games, 41 unrescorable games). These are on the Level 3
   page; section 4 keeps one sentence (scorers rewritten; the 78 games are those with full night
   outcomes).
8. The vote-accuracy ten-player split (+0.37 / +0.24). This is on the Level 3 page, and section 1 no
   longer uses vote accuracy as its example. The last section still names exactly which scores carried
   over (C4 fix kept).

Other changes: section 1 retitled "What decision scores buy". A repeated definition of the elimination
score was removed from section 3. "A villager who votes at random" → "a player" (villagers exist only on
the original game). The last section's "so a save is still graded good" now rests on the table, not on
the check.

Scope kept as qualified: section 1's "has not been measured" (OQ8); the healer comparison "shows that
the link changed, not why", now also in the opening; the owner's reading labelled untested; "not taken
at the time of writing" (OQ10); the belief-output paragraph still out (OQ9); no first-person claim on
the June score design (OQ7). OQ11 (length) is resolved by this pass. A second review is still
recommended for the reasons recorded under Review resolution. The editorial reviewer should now also
receive the parent excerpt.

## Review resolution (round 2)

Reviews (2026-10-29): editorial `play_metrics.skill.review-editorial.claude.20261029T015545Z.E93Cn9.md`
(R2-E1–E14, given the chapter excerpt as known context); claims
`play_metrics.skill.review-claims.claude.20261029T015721Z.JJTMU7.md` (R2-C1–C5, plus "Not checked").

| Reviewer | Finding (passage) | Action: fixed / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| R2-E1 (blocking) | The healer section gives three accounts and then withdraws the first | Fixed: retitled "What the healer's records show". It opens by saying the records show *how* the ten-player rate comes out near zero, not *why* it differs from nine players. The counts and the owner's reading are separate paragraphs; the reading is labelled untested up front | Yes: section reorganised |
| R2-E2 | +0.40 at 180 first appears late and looks like the investigator's figure | Fixed: the healer's +0.36 / +0.40 are reported with the nine-player results and added to the table's nine-player column (elimination +0.65 at 180 too); the late reference points back to "both nine-player figures in the table" | No |
| R2-E3 | What do decision scores buy, if not fewer games? | Fixed in part: names what the score gives that the win cannot (which behaviour changed; less noise in between, "expected rather than shown"). The saving in games stays unmeasured (OQ8 unchanged). Section retitled "Why score decisions at all" | Owner (OQ8) |
| R2-E4 | The grade table and memory credit appear only in the conclusion | Fixed: the table is introduced at the end of section 2, with memory defined there and the per-game scores said to be separate; the conclusion only refers back | No |
| R2-E5 | "Version" means both agent version and game version | Fixed: "agent version" for what is compared; "version(s) of the game" / "change of game" for nine vs ten players | No |
| R2-E6 | "Both games" reads as two matches | Fixed: "in both versions of the game"; "original/expanded game" kept for the variants | No |
| R2-E7 | Healer counts arrive before their purpose; no baseline | Fixed: introduced as "how often a save mattered … with no nine-player baseline"; one count moved to the notes (supporting note 10) | No |
| R2-E8 | "Wider margin than that" is not defined; no figures for two named scores | Fixed: night losses −0.55 and lone killer +0.38 given, "both with intervals clear of zero"; the closing says "intervals well clear of zero" | No |
| R2-E9 | "Batch" undefined | Fixed: "one run of games played under the same setup" | No |
| R2-E10 | Did the nine-player game have a lone killer? | Fixed: "a lone killer, always the serial killer on nine players, that is now one of two roles" | No |
| R2-E11 (taste) | 75 vs 78 games unexplained | Fixed in the caption: the three games with no protection have no healer score | No |
| R2-E12 (taste) | Scorer-rewrite detail interrupts the method | Agreed: reduced to a clause on which records were usable | No |
| R2-E13 (taste) | "Formally validated" names an unexplained status | Reworded: "Marking any of them as a trusted proxy in the scores the system records for each game is a separate decision, not taken at the time of writing" (OQ10 still open) | Owner (OQ10) |
| R2-E14 (taste) | Section 1 answers a third question the opening does not set up | Partly fixed: the heading "Why score decisions at all" now names the question. The opening is not extended: the chapter summary already raises it | No |
| R2-C1 | The vigilante is given as a new role | Fixed: the new-role example is now the sentinel (+0.12, −0.11 to +0.33); the vigilante sentence moved to the notes (supporting note 9) | No |
| R2-C2 | "How many fewer games" presumes fewer; the page and report §1 disagree | Fixed wording ("whether it needs fewer games … has not been measured"); flagged (OQ8 update) | Owner (OQ8) |
| R2-C3 | "Each score is exact" covers one score that reads players' labels | Fixed: "The scores this page relies on read only what the engine recorded"; the accusation-tag score is noted in the sources | No |
| R2-C4 | The healer comparison assumes the two rates count the same thing | Flagged (OQ12); row label "per protection night" is true of both; caption notes the ten-player exclusion | Owner/verifier (OQ12) |
| R2-C5 | "Making saves did not" rests on two averages | Fixed: "saves per game were about the same in won and lost games" | No |
| R2-C not checked | "No matching nine-player counts" is an absence claim | Reworded to what the check holds; flagged (OQ13) | Owner (OQ13) |

**Length after round 2:** about 1,990 → about 2,120 words (including tables). Reason per addition,
otherwise trimmed:
- Section 1 (+26): the payoff sentence (R2-E3). Without it the section takes away the motivation the
  chapter gives and puts nothing in its place.
- Section 2 (+83): the grade-table paragraph moved up from the conclusion (R2-E4), so the closing
  claim rests on something already explained. The conclusion lost the same sentences.
- Section 3 (+7): the healer's nine-player figures (R2-E2). The comparison at the end needs them.
- Section 4 (+34): the batch definition, the lone-killer clause, the 180-game column, the caption's
  75-game note, and the two scores' figures with intervals (R2-E8/E9/E10/E11). It was offset by
  shortening the scorer rewrite (R2-E12) and moving the vigilante sentence to the notes (R2-C1).
- Section 5 (+10): the opening sentence that separates how from why (R2-E1, blocking). One count moved
  to the notes.
- Opening and section 6: about unchanged.

**Another review:** the editorial reviewer only, recommended for section 5. Its structure changed (the
blocking finding), and the grade table moved from the conclusion to section 2. No central claim
changed this round. Every claims fix narrowed or relabelled a claim, and the open ones are flagged, so
a claims re-run is optional.

## Step 7 (deferred in this trial): edits I would make to other files

Filled in after drafting. Anticipated so far:
- `writeup/evaluation/evaluation.md`: probably none. The Level 1 summary already matches the central
  answer. Recheck "in the analysed sample" after drafting.
- `writeup/evaluation/play_metrics/metric_transfer.md`: none expected. If open question 4's default is
  taken, its healer paragraph stays the only home of the p-values.
- Chapter `editorial_notes.md`: the evaluation chapter has none. The skill asks for a dated entry, so I
  would create `writeup/evaluation/editorial_notes.md` in the style of the game-design chapter's (or ask
  the owner where it belongs).
- `writeup/evaluation/exhibits/source_map.md`: rows PM-worked-score and PM-contrast already describe the
  two exhibits. I would update their status after drafting. PM-worked-score should say "one protection,
  illustrative, on the expanded game".
- `evidence/evaluation/metrics/report.md` §1 ("Many graded decisions per game vary far less than one win
  bit, so an effect shows at a game count the project can afford"): depending on the owner's answer to
  open question 8, flag it with a dated note. That would be an evidence edit, so the owner reviews first.
- `writeup/evaluation/fair_comparisons/fair_comparisons.md` ("Decision scores and replayed turns can make
  some comparisons more sensitive"): check it against open question 8. It already says "can".
- `writeup/evaluation/evaluation.md` Level 1 summary: still consistent. It says "candidate proxy
  metrics" and "in the analysed sample". Its "Code checks, for example, whether a vote targeted an
  enemy" is fine. No edit.

## Review resolution

Reviews: editorial `play_metrics.skill.review-editorial.claude.20261028T145754Z.Fj1i1D.md` (E1–E16);
claims `play_metrics.skill.review-claims.claude.20261028T145936Z.ji7Jgh.md` (C1–C10 in its order, then
its "Not checked" items N1–N4).

| Reviewer | Finding (passage) | Action: fixed / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| E1 (blocking) | The game, the agents and "version" are never introduced | Fixed: a new first paragraph names the game, what a version is, and memory | No |
| E2 (blocking) | 36 points vs 0.18 are on different scales; the advantage is unproven | Fixed reasoning, flagged (OQ8): the two figures are the same fraction of each measure's spread, so they show nothing about sensitivity. Section 1 now argues only that the score is closer to the play, and says the saving in games is unmeasured. 0.18 dropped. | **Yes**: central claim of section 1 changed |
| E3 (blocking) | Healer survival figures never linked to the rate; "what changed" with no nine-player figures | Fixed: extra nights without extra saves lower the rate in won games; survival (+0.29) went with winning, saves per game did not. "What changed" → "how its rate lost the link"; "ten-player records" named | Yes: new interpretive sentence |
| E4 | The model change appears only at the end | Fixed: in the opening and just before the contrast table | No |
| E5 | "Memory" undefined; why it confounds is unclear | Fixed: defined in the opening as one of the things versions differ in; the memory-off reading keeps its reason | No |
| E6 | Why wins can validate scores but not compare versions | Fixed: the check pools games across versions and asks about an association; a strong link shows over 50 games, a weak one may not | No |
| E7 | The method-change paragraph does four jobs, in the wrong section | Fixed: the gate (48/11) stays in section 3 with its chance caveat; the change of method moved to section 4 and says the grade table is separate from the per-game scores | Yes: structure moved |
| E8 | Lynch score defined per vote in one place, per elimination in another | Fixed: "elimination score" throughout; vote accuracy named as a separate score, with its weaker ten-player result | No |
| E9 | "Players killed at night" is an outcome, not a decision | Fixed: section 2 now says some scores are plain counts and others rates | No |
| E10 | Are the 28 zero-reading games among the 78? | Fixed: "28 ten-player balance games"; 41 earlier games without night outcomes could not be rescored; the 78 are later games | No |
| E11 | "What mattered" reads as cause | Fixed: "The association is with turning a find into a vote" | No |
| E12 | "Harder guess" implies an absent comparison; direct comparison given without numbers | Fixed in part: says there are no nine-player counts to compare and that the check does not test the reading; names both baselines (50 games; +0.40 on 180). P-values stay on Level 3 (accepted default OQ4) | No |
| E13 | 32 scores first appear in the closing; no chance caveat on the 48 | Fixed: 32 stated when the check is introduced; the chance caveat added for the nine-player gate | No |
| E14 | Unclear which game the rules section describes | Fixed: the cast is described for both games; the healer table is labelled "on the expanded game"; section 4 lists what changed | No |
| E15 (taste) | "Held on the later 180" gives no number; overlap unclear | Fixed: +0.65 over a separate 180 (candidate ledger) | No |
| E16 (taste) | "Level 3", "labels the live game reports", "the record" are internal terms | Partly fixed: "the record" → "the project's records"; the labels sentence reworded without internal terms. Declined for "**Level 3:**": it is the chapter's link-spec convention (like **Link:**/**Evidence**), not page copy | No |
| C1 | "Every role is missing from some games" is false | Fixed: eight seats are dealt every game and two switch; the reason now given is many new roles, several acting rarely (report's "too few games per role") | No |
| C2 | Rejected belief-output design conflicts with the later scored reads | Flagged (OQ9); paragraph removed, overriding the accepted default for OQ2 | Owner |
| C3 | "Turns those grades into scores": wrong mechanism | Fixed: scores are computed from the record; the grade table is a separate scorer that feeds memory (sections 0, 4, 6) | No |
| C4 | "Core town scores" overstated; vote accuracy (section 1's example) weak on ten players | Fixed: the scores that carried over are named; vote accuracy's +0.37/+0.24 split reported; section 1 no longer uses it as the example | No |
| C5 | "What mattered" (same as E11) | Fixed (see E11) | No |
| C6 | "A score divides by the chances": only rate scores do | Fixed (see E9) | No |
| C7 | "First 28 ten-player games" should be "28 balance games" | Fixed (see E10) | No |
| C8 | "The record names three changes", but it names five and item 3 was dropped | Fixed: "Among the changes…"; item 3 (run the check on the first batch) added | No |
| C9 | Cast: no villagers on ten players; neutral seat; necromancer kills through a body | Fixed: villagers only on the original game; "one more seat plays for a goal of its own"; "both can kill" | No |
| C10 | Detectable sizes lack sample context | Fixed: "estimated on the original nine-player games" | No |
| N1 | First person "I measured" for the June score design | Flagged (OQ7): neutral wording on the page | Owner |
| N2 | Healer p-values exist only on Level 3 | No change: the page states the result in words (accepted OQ4) | No |
| N3 | Per-score 180-game value not checked | Fixed: +0.65 at N=180 from the candidate ledger | No |
| N4 | Nine-player healer denominator (action nights) vs ten-player (protections that went ahead) | Declined for the page: the nine-player game had no blocker, so the two probably coincide (not traced); the table's row label describes the ten-player definition. Noted for the verifier | Verifier |

**Second review:** recommended. Section 1's central claim changed (E2/OQ8), the method-change
paragraph moved (E7), and a new interpretive sentence was added to the featured story (E3). The
editorial reviewer should re-read the flow from the opening to section 4. The claims reviewer should
check section 1 and the healer sentence.
