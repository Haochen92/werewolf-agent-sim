# Authoring brief: Measuring play quality beyond win rate

Page: `writeup/evaluation/play_metrics/play_metrics.skill_2.md` · Level 2 · started 2026-10-29 · checkpoint: approved in conversation 2026-10-29; defaults accepted for all open questions

Authoring material, not page copy. The cold editorial reviewer never sees this file.

Trial run (skill version 2, 2026-10-29): steps 1–3 only, stopped at the checkpoint. Inputs read: the
skill and its references (voice, page types, brief template, examples; example C's page copy read as
the closest model: an approach introduced before it is evaluated), the general and Level 2 writing
prompts, `content_plan.md`, the map's Evaluation outline and Handle-with-care list, the parent excerpt
(`parent_context.py`), the Level 3 page `metric_transfer.md`, the baseline packet (original brief +
sources comment), `evidence/evaluation/metrics/report.md`, its `experiment_log.md` (Part A, B1, the
2026-10-24 entry), `data/ten_seat_win_check/README.md`, `scoring/report.md` (Layer 3),
`experimental_controls/drift_surfaces_and_guards.md` (per-game spread, detectable effect at N=30),
`evaluation_scopes/game/experiment_log.md` (the recomputed detectable effects), and
`Agents/ten_seat_metrics.py` (the healer rate). The Evaluation chapter has no `editorial_notes.md`.
Not read, per the fair-comparison rule: `play_metrics.md`, `play_metrics.skill.md`, other `_authoring/` files.

## Frame

- **Primary page type and level:** design decision / approach explanation (how to measure play
  quality when the win is too noisy, and why the measure is built this way). Level 2.
- **Secondary mode, if needed:** comparative evaluation in sections 3–4 (checking scores against
  winning; the transfer to the expanded game, which is the featured story). The check is how the
  approach is validated, so it stays inside the one question rather than becoming a second page.
- **Existing outline approval:** approved in conversation 2026-10-29 (Frame, Core argument and
  Argument outline as proposed; the stated default accepted for every open question).
- **Reader's question:** If winning is too noisy to tell two agent versions apart at an affordable
  number of games, what can you measure instead, and how do you know it measures good play?
- **Central answer:** Grade individual decisions by the game's rules against the true roles, as rates
  over the chances each player had, which removes much of the luck a win carries; then check, one
  number per game, whether those scores go with winning before relying on them. The two answer
  different questions, and the expanded game showed it: lynch scores still tracked winning, the
  healer's save rate did not, although a save is still a good move.
- **Reader starting point:** the parent says wins need more games than affordable, decision-level
  scores are "candidate proxy metrics", code checks e.g. whether a vote hit an enemy or a protection
  saved a townsperson, and that the healer's save rate stopped separating wins from losses on ten
  players. This page must still define: what a decision score is (a rule grade, as a rate over
  opportunities), what "less luck" means and does not mean, what the check against winning computes
  and why the game is its unit, why the two questions are kept apart, and why a null on few games is
  "untested" rather than "fails". Game roles used (healer, investigator, vigilante) need one clause
  each; the expanded game needs one sentence (ten seats dealt from twelve roles).
- **Opening choice:** an approach page (page types: "what it does, why it is needed, when to choose
  it"). Open with the cost of the win as a measure, made concrete (about 35 points of win rate as the
  smallest difference 30 games a version could reliably detect), then name the alternative and its two
  questions. The healer is previewed in one sentence only; its explanation needs the check first.
- **Claim level:** a practical measurement choice plus a diagnosed transfer result. Evidence needed:
  that the rule grades are exact counts (by construction), that the check found which scores track
  winning on each game, and the scope of each correlation. Not needed: a causal claim, a validated
  decision table, or a power study of the proxies.
- **Distinctions the reader needs:**
  1. A good move by the rules (an exact count) vs a score that tracks winning (a validated proxy).
  2. Less luck than the win vs luck-free: a blind vote that hits a wolf scores like a reasoned one.
  3. Many decisions per game make a steadier per-game number, not extra independent games; the check
     uses one score and one result per game.
  4. Not reproduced / untested vs failed: a weak correlation on few games leaves a score untested.
- **What the evidence establishes:** on the original nine-player game, town lynch and vote scores
  went with town wins (about +0.6 over 50 games, held on 180); the investigator's find rate did not,
  its find-to-lynch rate did. On the expanded game (78 games, mixed models), the lynch share still did
  (+0.49, interval +0.30 to +0.64), within batch and with memory off; the healer's save rate did not
  (−0.03, interval −0.26 to +0.20, 75 games). The healer still made real saves at the same rate in won
  and lost games.
- **What stays uncertain:** why the healer's association changed (game version and models both
  changed; the owner's reading fits the records but is untested); most new and rare roles' scores
  (too few games); the decision table as a whole (never checked against winning); chance among 32
  scores; new-role directions were not written in advance (exploratory). Correlation, not cause.
- **Stays off the page:** runner uncommitted at the time of the check; tests pinning the grade table
  (AI-written, unaudited); the first count of 119 games; the three scorers that mis-sided new evil
  roles until the check's morning (outside this check's code path; not needed here); live-dashboard
  name and code identifiers (`VALIDATED_ON_TEN_SEAT_METRICS` etc.); memory results (Memory chapter:
  no "memory helps" claim; the memory-off reading is described as a guard only); model names unless
  a result would be ambiguous without them.

## Evidence selection

**Core argument, before examples or numbers:**

1. A win is one result per game carrying the deal, everyone else's play and coin-flip votes, so
   telling versions apart by wins takes more games than the project could run.
2. A game contains many decisions, and each can be graded against the true roles by the game's own
   rules. Averaged per game, that gives a number with less luck in it than the win. It is still one
   number per game: decisions in one game share its deal and history.
3. To be fair across players, a score is a rate over the chances a player had; no chance, no score.
   What remains is the luck inside a single decision, which only averages out over games.
4. A rule says a move is good; it does not say that making more such moves wins games. That is a
   separate question, answered by checking each per-game score against its side's win, with guards
   against memory and batch differences producing a false link.
5. The check catches scores whose meaning looked obvious and was wrong (finding wolves vs turning
   finds into lynches), which is why the check, not the rule alone, licenses a score as a proxy.
6. When the game changes, the link must be re-checked: a score can stay correctly counted and stop
   tracking winning. The expanded game showed both outcomes (lynch share held, healer save rate
   didn't), and the healer's records show what a good move that decides fewer games looks like.
7. A weak result on few games leaves a score untested, not failed; rare actions stay graded but
   cannot decide a comparison. Correlations do not show cause, and the full decision table is untested.

| Essential concept | Selected evidence (source), if needed | Why this example earns space | Alternatives omitted / destination |
|---|---|---|---|
| 1. Win too noisy | Win-rate detectable difference ≈35 points at 30 games per version (evaluation_scopes/game/experiment_log.md MDE table; drift_surfaces_and_guards.md) | A count a reader can picture; makes "too noisy" concrete | Vote-accuracy detectable effect (0.18–0.21; units differ from win points, comparison would need explaining) → sources comment; memory A/B outcomes → Memory chapter |
| 2. Per-game score, game as unit | Report §1; check code correlates one score with one win per game (ten_seat_win_check.py) | The brief's required point; prevents the "more observations" misreading | Seed-vs-gameplay variance split (drift_surfaces) → evidence |
| 3. Rule grade as an opportunity-adjusted rate | Worked healer definition: a four-row table of night outcomes and whether each counts as a save, a chance, or neither (ten_seat_metrics.py healer_town_save_rate; night.py verdict; Chanteuse block counts neither way). Rule examples: vote on a threat, save, vigilante shot on evil (report §2). The owner's table grades every kind of turn good/neutral/bad | Definitional table, no invented numbers; the healer is the featured score later, so defining it here pays off twice | A worked vote score (simpler, but the healer carries the story) → omitted; Fortune Teller/Sigilist grades → evidence |
| 3b. Residual luck, and why it stays | Blind vote scores like a reasoned one; rejected design: weight votes by how sure the voter could be, but the only uncertainty signal existed in memory-on games, which would bias the comparison (report §1) | Shows a real trade-off, and explains a limit instead of just stating it | Forced belief output (changes play; circular) → evidence |
| 4. The check | Point-biserial per game vs own side's win; town lynch/vote scores ≈ +0.6 on 50 nine-player games, held on 180 (report §2–3); memory-off and within-batch readings | Establishes what a validated proxy means here | Wolf night-kill dilution (77 of 180 games), survival tautology → L3/evidence |
| 4b. Why rules come first now | June: check chose 11 of 48 candidates; expanded game: twelve roles for ten seats leave too few games per role, so the table defines good moves first and the check confirms or questions (report §2 "How the approach changed") | Explains the current division of labour between rule and check; a practical judgement under data limits | July exceptions in detail → evidence |
| 5. Check catches a wrong-looking score | Investigator: find rate −0.09/−0.14 (not tracking), find-to-lynch +0.40 over 180 games (report §3) | Recurs on the expanded game (60% of named evil players later lynched; per-game named count +0.09, share lynched +0.19, p = 0.12), so it connects sections 3 and 4 | Wolves accusing townspeople (expected +, came out −0.33) → omitted, one surprise suffices; early-alarm +0.38 → +0.15 → evidence |
| 6. Transfer (featured) | Table: lynch share +0.65 (50) → +0.49 (+0.30 to +0.64; within batch +0.55; memory off +0.48); healer +0.36 (50) → −0.03 (−0.26 to +0.20, 75). Healer records: 1.07 vs 1.03 saves per game; 3.25 vs 2.48 protection nights; 220 protections = 79 saves + 141 unattacked; 36 saved died later; 23 saves where someone else died. Owner's reading, labelled. Scope: crosses game version and models | The parent's promised story; shows a correct count that is no longer a proxy | Vote-accuracy batch split, other carried-over scores, Chanteuse, Fisher-z comparison number, scorer rewrite detail → L3 (`metric_transfer.md`) |
| 7. Untested ≠ failed; limits | +0.12 over 78 games has interval ≈ −0.10 to +0.33; ≈190 games to see 0.2 reliably; 17 wolf wins; vigilante fired in 19 games (16 of 22 shots on evil). Rare scores may report on their own decision, not decide a comparison (report §2). 32 scores, chance; new-role directions read after the run; check tested per-game scores, not the grade table | One interval example teaches the reading rule; the vigilante shows "accurate but rare" | Sentinel/Trailseer/Sigilist rows → L3 |

**Level 3:** "After this page, the interested reader may ask how the ten-player check separated scores
that carried over from those that didn't, given a mixed pool of games; `metric_transfer.md` answers it
with the three readings (all games, within batch, memory off), the interval rule, the full results
table and the healer's records." It already exists; this page keeps the lynch/healer contrast, the
healer mechanism in brief, the cross-game caveat and the rare-action limit, and stays consistent with
it (notably: the earlier healer estimate also has uncertainty; the drop is not explained).

## Argument outline

Structure: successive questions, each section answering what the previous one left open. An approach
page (define the measure and its purpose before its results), with the transfer check as the featured
story near the end, because the healer contrast only makes sense once the reader knows both the rule
grade and the check. Not chronological: the June gate appears only as the reason the check's role changed.

| # | Section | Reader understands afterwards | Selected example, if needed | Omitted / linked | Why the next follows |
|---|---|---|---|---|---|
| 0 | Opening (no heading) | Play metrics are code-computed grades of decisions against the true roles; they answer two questions, "was it a good move" and "do such moves win"; the healer shows the two can split | Win-rate detectable difference ≈35 points at 30 games per version | Rejected judge-based scoring (one clause at most) | Why decisions help needs explaining before how they are graded |
| 1 | Why decisions, not wins | A per-game average of graded decisions has less luck than the win, but it is still one number per game; decisions in one game share its deal and history | Luck sources of a win (deal, others' play, coin-flip votes) | Seed-vs-gameplay variance → evidence | If decisions are the unit of grading, what makes a decision good? |
| 2 | Grading a decision by the rules | Rules define a good move; every kind of turn has a ruled grade; rates divide by chances; no chance, no score; residual luck stays, and weighting by certainty was rejected because its signal existed on one side only | Healer definition table (four outcomes); vote and vigilante rule examples | Forced belief output; grade coverage counts → evidence | A rule says a move is good, not that more of them win games |
| 3 | Checking that good moves go with winning | The check: one score vs its side's win per game, read with memory off and within batch; it confirmed town lynch/vote scores and caught the investigator's find rate; the check's role changed from choosing scores to confirming rule-defined ones | Lynch share ≈ +0.65 (50 games); find rate vs find-to-lynch | Wolf dilution, survival tautology, wolves' accusations → evidence/L3 | The check was made on one version of the game; does it hold when the game changes? |
| 4 | When the game expanded (featured) | A score can stay correctly counted and stop tracking winning: lynch share held, healer save rate did not; the healer's saves were real and equally frequent in wins and losses, its survival differed; the reading is offered, not tested; the comparison crosses game and models; consequence: a save stays graded good, its rate is no longer evidence that one version wins more | Two-row exhibit table (nine vs ten players, with interval and game counts); healer records | **Link:** L3 `metric_transfer.md` beneath this section. Vote-accuracy batch split, Chanteuse, other scores, direct-comparison p → L3 | Most new and rare roles gave no clear answer at all: how should that be read? |
| 5 | When a result is too weak to read | A weak correlation on few games leaves a score untested, not failed; how wide the interval is at 78 games; evil sides and rare actions need more games; untested scores still report on their own kind of decision but do not decide a comparison | +0.12 → −0.10 to +0.33; ≈190 games for 0.2; vigilante 19 games, 16 of 22 shots; (drafting) the investigator pattern's weak echo among the information roles, placed here as an example of "too weak to confirm" | Per-role rows → L3 | What, beyond sample size, do these checks not establish? |
| 6 | What the checks do not establish | Correlation, not cause; 32 scores invite chance results; new-role directions were read after the run; the check tested per-game scores, not the full decision table; next step: check each new version's first batch, with ranges and directions written in advance | — | Recording full night outcomes from the first game; scorers written against sides → evidence ("What we would do differently") | — |

Outline check: reading only the main points in order answers the frame's question (what to measure →
how it is graded → how it is validated → what happened when the game changed → how to read weak
results → limits). No section needs a later term: "interval" first appears in section 4's table and
must be explained there in one clause (section 5 then develops it); "within batch" and "memory off"
are introduced in section 3 before the table uses them.

Expected length: about 1,500–1,800 words including the two tables.

## Open questions

1. **Direct comparison of the healer correlations.** `metric_transfer.md` reports a Fisher-z test
   (p ≈ 0.03 against the 50-game estimate) computed for that page, not in the evidence record (owner
   approved it there). Default: state it in words on this page ("a direct comparison makes chance an
   unlikely explanation, but cannot say why"), leave the number on Level 3.
2. **The opening number.** Use the win-rate detectable difference (≈35 points at 30 games per
   version; from the June-era nine-player harness) to make "too noisy" concrete? It is from the
   game-scope record, not the metrics report, and from the earlier game. Default: use it, with "on the
   original game" beside it; do not quantify the proxies' own advantage (their detectable effect is in
   other units, and "far less variable" in the report is not quantified there).
3. **First person.** Records name the owner for the decision table, the "run first, read after"
   call and the healer reading; they do not say who wrote the scoring code or the check runner.
   Default: "I" for those decisions and readings; neutral voice ("code grades", "the check
   correlates") for computation.
4. **The June selection history (48 tried, 11 kept).** Default: one or two sentences in section 3, as
   the reason the check moved from choosing scores to confirming rule-defined ones. Alternative: drop
   it and state today's division of labour only.
5. **The scorer rewrite before the ten-player check** (scores read zero on the first 28 ten-player
   games until rewritten to read the new night records and sides from the role list). A caught fault
   relevant to "a count must first be correct". Default: one sentence in section 4 told as caught and
   changed; full story on Level 3.

## Drafting notes (step 4, 2026-10-29)

- Page copy about 1,940 words including the two tables and the Level 3 link line (Evidence list
  excluded), inside the 1,200–2,000 guide.
- Changes from the outline: section 4 opens with its finding (the skim showed its first sentence was
  setup only); section 3's first sentence now answers its heading; the information-role echo of the
  investigator pattern sits in section 5, not 3 or 4; the healer table leaves out the "protected an evil
  player who was attacked" row (a chance, not a town save), which the caption covers; "36 of the saved
  died later" omitted (kept on Level 3).
- Open questions resolved by the accepted defaults: the direct healer comparison is in words only; the
  35-point figure carries "on the original nine-player game"; "I" only for the ruled table and the
  healer reading; the weighting rejection is impersonal (no record of who rejected it); the 48/11
  history is one paragraph; the scorer rewrite is two sentences.

### Open questions raised by the review (2026-10-29, for the owner)

6. **The healer's denominator explanation is mine, not the record's.** The page now says the same
   number of saves over more protection nights pulls the rate down in won games, so the rate removed
   survival, the part of the healer's record that went with winning. This is arithmetic on recorded
   figures (1.07/1.03 saves over 3.25/2.48 nights; nights +0.29 with town wins), not a statement in
   the log or report, and it was not re-derived from the data (a per-game average of rates is not
   exactly the ratio of averages). Worded as "pulls the rate down", not "explains the drop". Owner to
   accept, or reduce to the recorded facts only.
7. **The owner's healer reading was trimmed.** The recorded reason "two killers a night" is dropped
   because the nine-player game also had two killing sides (and the necromancer does not attack
   every night), so it cannot explain the change. The page keeps "whom to guard became a harder guess,
   and one save decided the game less often" as my reading, untested. Owner to confirm the trimmed
   reading is still theirs, and should the log's reading be corrected with a dated note?
8. **Whether a healer save on the expanded game is "counted correctly".** The only record is a hand
   check of the metrics against one pilot game. The page now says "counted by the same rule" / "by its
   rule" rather than "correctly". Owner to say whether a stronger statement is supported.
9. **"28 ten-seat balance games" read zero.** The source does not place them among or outside the 78;
   they are likely the 2026-10-09/10 games without night outcomes, but that is not recorded. The page
   leaves the count off. Owner to confirm if the count should return.
10. **Report §2's sentence about too few games per role** ("deals ten seats from twelve roles, which
    leaves too few games per role") is loose: eight seats are fixed (`Agents/schemas/roles.py`). The
    page now gives the actual reasons (rare actions, few evil wins). The report wording may need a
    dated correction (step 7 list).

## Step 7 in this trial

Skipped by instruction. What I would have changed:

- **`writeup/evaluation/editorial_notes.md`** (does not exist; would create, or use the owner's chosen
  place): dated entry for 2026-10-29: explanatory path (why decisions → grading by rules → the check →
  the expanded game, healer featured → weak results → limits); moved out (certainty weighting,
  information-role echo, surplus healer counts, scorer-port count); claim changes (deal composition,
  scores not all rates, per-game scores separate from the decision table, owner's reading trimmed,
  healer denominator reading added); checked by one claims review, not a full factual verification.
- **`evidence/evaluation/metrics/report.md` §2** "How the approach changed": the "ten seats from twelve
  roles … too few games per role" reason, and §4's "The range rules out the nine-seat size … a real
  difference between the games, not a small sample" (Level 3 already qualifies this): dated
  corrections, if the owner agrees. Also §2's Sentinel interval "−0.10" vs §4/summary.json "−0.11".
- **`evidence/evaluation/metrics/experiment_log.md`** 2026-10-24 "Owner's reading": a dated note that
  "two killers a night" was also true on nine seats (owner's call, open question 7).
- **`writeup/evaluation/play_metrics/metric_transfer.md`**: "Why the earlier check could not be
  assumed" says "a given role is absent from some games"; only the two drawn seats vary. Same fix as
  this page. Its owner's-reading paragraph keeps "two killers acting at night" (its completion note
  already hedges it); align with open question 7.
- **`writeup/evaluation/evaluation.md`** (Level 1 summary): no change needed; it stays consistent.
- The page's italic header line: updated on this page; nothing else.

## Review resolution

Reviews: editorial `play_metrics.skill_2.review-editorial.claude.20261029T030537Z.YB8bXj.md`; claims
`play_metrics.skill_2.review-claims.claude.20261029T030739Z.sHBEJM.md`. Both read in full.

| Reviewer | Finding (passage) | Action: explained / relocated / removed / corrected / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| Editorial 1 (blocking) | Healer lifespan figures not connected to the rate's denominator | **Explained.** New paragraph: same saves over more nights pulls the rate down in won games; the rate removed survival, which is what went with winning; the "harder guess" reading follows as the separate, unsettled question of why saves did not differ. Flagged (OQ 6): the interpretation is mine | Yes: claims recheck of the healer paragraphs |
| Editorial 2 | Original game's scores chosen by correlation revealed late; selection flatters the original estimates | **Relocated + explained.** Grading section now says the original game had no table and its scores were chosen by tracking winning (next section). Healer paragraph acknowledges selection and adds the out-of-selection +0.40 on 180 games | Covered by the healer recheck |
| Editorial 3 | "Direct comparison makes chance unlikely" unsupported on page | **Explained, within the owner's accepted default.** Now points to the Level 3 page where the test is shown, and the 180-game replication carries the claim on this page. No p-value added (default 1 kept) | No |
| Editorial 4 | Rejected certainty weighting: side branch, introduces memory and "situation summary" undefined | **Removed** (kept in the sources note). Memory on/off is now introduced where the readings need it | No |
| Editorial 5 | "Passed" undefined | **Explained.** One sentence before the first result: moves with wins in the predicted direction, beyond chance, in each reading | No |
| Editorial 6 | Expanded-game paragraph does three jobs; 28 games unclear | **Corrected + split.** Roles in one paragraph; the scoring-code rewrite in the next; count of 28 dropped; the check used only games with full night outcomes, so all were scored by the rewritten code | No |
| Editorial 7 | Save definition shifts; eight numbers, unclear numerator | **Removed** 220/79/141/56/23 (sources note); kept only the figures the argument uses (saves per game, protection nights, +0.29) | No |
| Editorial 8 (taste) | Blocking role used in the table before introduced | **Explained**: row now says "a wolf-side role … (possible on the expanded game)". Agreed | No |
| Editorial 9 | "Batch" and "setup" undefined | **Explained**: "run in batches, each on one model and set-up" | No |
| Editorial 10 (taste) | 75 vs 78 games unexplained | **Explained** in the caption: games with at least one protection that went ahead. Agreed | No |
| Editorial 11 (taste) | Information-role echo is a third branch with a p-value | **Removed** (on Level 3 and in the sources note). Agreed: the vigilante makes the point | No |
| Editorial 12 (taste) | What testing "the table as a whole" means | **Explained**: whether decisions graded good, across every kind of turn, go with winning; per-game scores cover only some turns. Agreed | No |
| Editorial 13 (taste) | "Reliably" and "points" unstated | **Explained**: percentage points; found four times in five at the 5% level. Agreed | No |
| Claims 1 | Lone killer presented as new; the nine-player game had the serial killer | **Corrected** from `roles.py`: eight fixed seats; the lone-killer seat (serial killer as before, or a new necromancer) and a new neutral seat are drawn | No |
| Claims 2 | Owner's reading: two night killers cannot explain the change | **Corrected + flagged** (OQ 7): clause dropped; trimmed reading kept as mine and untested | Owner |
| Claims 3 | "Each role absent from some games": wrong mechanism | **Corrected**: rare actions and few evil wins leave too few games per score. Also removed the healer table's wrong "not dealt" row (healer is a fixed seat) | No |
| Claims 4 | Not every score is a rate | **Corrected**: "where a score depends on how long a player stayed in the game, it is a rate" | No |
| Claims 5 (needs owner) | Per-game scores read as averages of the table's grades | **Explained** where the table is introduced: per-game scores are computed separately from the same kinds of outcomes; "averaging grades" in section 1 changed to "counting outcomes". What the table is used for elsewhere is not named (memory credit belongs to the Memory chapter) | No |
| Claims 6 | "First 28 ten-player games" not in source | **Removed** the count (OQ 9) | No |
| Claims 7 | Investigator figures mix 50- and 180-game samples | **Corrected**: 50 games for the find rates, "still near zero over 180" | No |
| Claims 8 | "Applies that table exactly" rests on unaudited tests | **Corrected**: "the same way every time" | No |
| Claims 9 | Sentinel interval −0.10 vs −0.11 | **Corrected** to −0.11 (summary.json) | No |
| Claims, not checked | "Steadier number" not measured; "counted correctly" rests on one pilot hand check | **Reworded**: "a number with less of that luck in it"; "counted by the same rule" (OQ 8) | Owner |

**Length after revision:** about 2,100 words of page copy (Evidence list excluded), against the
1,200–2,000 guide; it was about 1,940 before review. Removals (certainty weighting ≈70, information-role
echo ≈60, surplus healer counts ≈70) roughly offset the additions; the net growth of ≈160 comes from
fixes the argument needs: the healer denominator paragraph (editorial 1, blocking, ≈80), the deal
composition (claims 1 and 3, ≈50), the selection caveat with the 180-game replication (editorial 2–3,
≈40), the pass criterion (editorial 5, ≈30), memory and batch definitions (editorial 4 and 9, ≈30),
per-game scores vs the table (claims 5, ≈35). The opening's significance clause (≈15) is taste and is
the first cut if the owner wants the page under 2,000.

**Second review:** the structure is unchanged, but a central claim changed: the healer explanation now
includes the denominator reading. Recommend a claims recheck of the "When the game expanded" section
only; no second editorial pass needed.
