# The Tell Ledger — Build Journey

> **Scope:** July 11–14, 2026 experiments on the nine-seat game, from candidate mining to an
> implemented tell-book channel. Later entries supersede earlier decisions. Historical costs,
> models and validation limits belong to those runs, not today's deployment.
> **Editorial review:** October 13, 2026. This revision preserves the experiment sequence while
> correcting claims against saved artifacts and distinguishing build status from demonstrated benefit.
> The [reference report](report.md) explains the resulting mechanism; the
> [design record](../../credit/read_tactic_credit_redesign.md) explains the read/tactic separation.

## 1. Motivation — measure behavioral claims separately from tactics

The existing memory system stored examples and tactical instructions. A tell added a different kind
of knowledge: an observable behavior associated with a hidden role. The proposed pipeline would mine
candidates from finished games, detect their occurrence in public transcripts, then join revealed roles
to estimate whether the behavior distinguished players. A compact book would supply selected tells
before agents formed their reads.

The miner could use revealed roles to find candidates, but its selection would be affected by hindsight.
Its examples therefore could not establish accuracy. A separate role-blind detector and held-out games
were needed for measurement. Both the descriptions and the detector could fail: “defends their packmate”
requires hidden knowledge, while “plays suspiciously” is too vague to count consistently. The first
experiments tested whether mining could produce observable, reusable descriptions with evidence quotes.

---

## 2. Decisions before the first call

The initial miner would work one game-day at a time, carrying earlier public discussion as context.
That kept the focus narrow without losing cross-day behavior. Its input included revealed roles for
discovery, but excluded private night actions and reasoning. Output still needed inspection: absent
private evidence does not stop a model inventing a hidden relationship.

Each entry would name an exhibitor and carry a verbatim evidence quote. Roles would be joined from
the game record rather than transcribed by the model. The description had to be a recurring observable
behavior, not a verdict that someone “acted wolfish.” Role association would be measured later on
held-out games; mining counts were for discovery only.

The first probe used Gemini 2.5 Pro, the existing extraction model. Cheap deterministic screens checked
role words, player IDs and quote presence; readers assessed meaning and generality. Those screens were
triage instruments, not substitutes for semantic review.

Provenance: frozen `scripts/tell_mining_probe.py`, versioned files in `prompt_versions/`, and mined
rows in `outputs/`. Rows retain game, day, exhibitor, description, quote, role and screen flags.

---

## 3. First prompt: inspect candidates and check the screens

The first prompt ran on five games, producing 177 entries from 25 day-calls. No role-word or player-ID
violations were found in the descriptions. Among 91 rows read, villagers were the largest exhibitor
group at 28, so the miner was not simply listing evil players. Validity still required later detection.
Two examples from `outputs/mining_v1.jsonl` show the intended grain:

> Casts a solitary vote for a player when all other players vote to abstain.

> Votes for the player the room has already converged on without having voiced any suspicion of them during discussion.

**The quote check itself needed repair.** It initially flagged 54/177 quotes as absent. Normalizing
Unicode punctuation and stripping edge ellipses reduced that to 11/177. Most flags had reflected
formatting rather than invented evidence.

The remaining defects motivated three prompt changes. Some quotes spliced separate passages, so the
prompt required one contiguous span. Some descriptions invented motives, such as acting “to establish
credibility,” so it distinguished a player's reported motive from the miner's inference. Others
retold the game's plot, so it asked for the recurring move type or no entry.

**Decision.** Revise the prompt using concrete bad examples and keep the repaired quote check.
Source: [v1 prompt](prompt_versions/v1.txt) and `outputs/mining_v1.jsonl`.

---

## 4. Second prompt: check the three targeted corrections

On the same five games, the revised prompt produced 184 entries. Reported quote defects fell from
about 6% to 1%. All 26 quotes still containing ellipses matched the transcript; the quoted players
had used the punctuation themselves. Six motive-clause screen hits were reported speech, and review
reported no remaining episode re-descriptions in the sample. Role/player-ID checks found no violations.

The probe also found useful wording recurrence: 22/184 rows belonged to exact-wording duplicate groups,
including one phrase used for four exhibitors across games. Exact matching could resolve those rows
without semantic judgment.

**Decision.** Keep v2 as the review candidate. Description review, duplicate handling and later
role-blind detection could still expose problems not covered by these checks.
Source: [v2 prompt](prompt_versions/v2.txt) and the corresponding mining outputs.

---

## 5. Third prompt: replace a word ban with a knowledge boundary

Review against the game's knowledge rules exposed two problems with banning every role word.
“Justifies a past vote against a now-confirmed ally” used no role name, but still asserted a hidden
relationship. Conversely, a public claim to be the investigator was observable behavior even though
it contained a role word. The first two prompts had produced no claim- or reveal-conditioned family.

The revision allowed role terms with explicit public status, such as “claims to be” or “revealed on
death as,” while prohibiting ungrounded hidden relationships. It also used the earlier “ally” example
to explain the distinction.

**Result.** On the same five games, v3 produced 181 entries, with no bare-role or hidden-relation
flags and a 1.6% quote-flag rate. Seven entries described claims or reveals, including publicly
claiming to be the investigator. Review considered those descriptions consistent with the public
record. The lexical screen alone could not establish that conclusion.

**Decision.** Use v3 as the next candidate. The governing rule was whether a role-blind reader could
check the behavior, not whether the sentence contained a role name.
Source: [v3 prompt](prompt_versions/v3.txt) and the corresponding mining outputs.

---

## 6. A cheaper model loses repeated wording

The projected cost of mining a larger corpus on 2.5 Pro was $15–30. A same-five-game comparison held
the v3 prompt and backend fixed while changing the model. The cheaper models produced fewer candidates,
but the more consequential result was their loss of exact repeated wording.

| Measure | 2.5 Pro | 3.5 Flash | 3.1 Flash-Lite |
|---|---|---|---|
| Entries | 181 | 103 | 116 |
| Role/relationship screen flags | 0 | 4 | 3 |
| Quote flags | 3 | 0 | 1 |
| Rows in exact-wording duplicate groups | 24 | 3 | 0 |

Some screen flags were borderline reported speech. The zero exact-wording recurrence on Flash-Lite
was less ambiguous: its output would depend more on paid semantic matching. This did not prove it
could never reuse wording, only that it failed to do so in this comparison.

**Initial decision.** Retain Pro and limit the mining volume to about sixty games, then test the
cheaper model on detection. The next experiment revisited the input design instead.

---

## 7. Split the input to recover cheap-model coverage

Flash-Lite's missing discussion candidates suggested that it was attending to the compact vote block.
The proposed fix split each day into two calls. The discussion call omitted that day's votes; the
vote call kept discussion, because many voting patterns refer to what was said beforehand.

On the same five games, the split recovered discussion coverage and repeated wording:

| Measure | Pro, single call | Flash-Lite, single call | Flash-Lite, split calls |
|---|---|---|---|
| Entries | 181 | 116 | 213 |
| Role/relationship flags | 0 | 3 | 1 |
| Quote flags | 3 | 1 | 4 |
| Rows in exact-wording duplicate groups | 24 | 0 | 19 |
| Discussion candidates in the inspected game-1/day-2 gap | 4 | 0 | 3 |

The split used 50 calls and recovered three of the four reference patterns in the inspected gap.
Higher yield was not itself an accuracy result. Review still found occasional inferred motives
(about 1–2%), and the vote prompt's example families could influence what it discovered.

**Decision.** Adopt v4 split mining on Flash-Lite. The contemporary sweep estimate fell to $2–3
from $15–30; later billing corrections in §14 qualified the initial cost assumptions. The measured
engineering finding was that a more focused input recovered coverage on this sample without using
the larger model.

---

## 8. Duplicate detection — candidate selection limited recall

Before mining more games, the next check asked whether descriptions of the same behavior could be
consolidated. Matching had to span roles within a channel: the same behavior in a villager and a wolf
must share an identity for their frequencies to be compared. Discussion and vote descriptions stayed
in separate channels.

**The lexical prefilter missed known paraphrases.** TF-IDF similarity over 202 distinct wordings
produced only ten candidate pairs and three merges, despite a manual read finding about fourteen
votes-own-accuser variants. Shared vocabulary was too weak a filter for these short descriptions.

**Embeddings found candidates, but the similarity scale required a tighter budget.** The median
vote-channel pair scored 0.84 and the 99th percentile 0.93; a 0.80 cutoff admitted 2,837 pairs.
Capping the judged candidates at 400 per channel produced 166 canonical tells from 213 rows, with
44 merges. Review of all 44 found one questionable pronoun-dependent match. Missed candidates remained
a separate source of duplicate entries.

**Decision.** Use ranked nearby candidates rather than rely on the original absolute cutoff, retain
ambiguous relational wording for review, and test growth on more games before choosing a mining budget.
The risk was both wrong merges and missed matches; reviewing accepted merges checked only the former.

---

## 9. Review the 166-entry corpus before expanding it

The next review asked whether five games had produced 166 distinct reusable behaviors or mostly
fragments. A strong-model reviewer examined each channel for merges, episode descriptions, trivial
entries and vague wording. A separate pass checked every vote merge and drop, plus a sample of the
discussion merges. About 17/20 vote merges were accepted; discussion agreement was about 90%.

One important correction was conceptual. The reviewer called accuse-then-vote trivial because it was
ordinary follow-through. Common behavior can still discriminate between roles, so commonness alone
was not a reason to discard a measurable candidate. Its six mined exhibitors were all town; that was
a reason to measure it on other games, not evidence that it was already a validated tell.

**Result.** The review retained 107 entries: 45 additional merges and 14 drops from the 166-entry
corpus. Roughly two-thirds of the retained entries had only one mined instance. The vote-own-accuser
family had 18 mined exhibitors, nine evil. These were discovery counts, not detector-based validity.

**Decision.** A checklist detector was preferable to a separate call for every candidate. Periodic
review could also recover duplicates outside the pairwise prefilter's candidate budget. The next
experiment would test whether that burden diminished as the corpus grew.

---

## 10. Simulate the lifecycle over 30 games (2026-07-12)

The proposed lifecycle needed a growth and cost check before using its counts. Twenty-five more games
were mined with the split flash-lite prompt, then 1,109 mined instances across all thirty games were
replayed in order. No detector was yet available: mined recurrence stood in for support. This tested
admission, probation and archiving, not whether a tell predicted a role.

**New entries did not plateau.** The simulation reached 740 canonical entries. New-entry yield fell
from about 43 per game early to about 22 per game in games 21–30, without a further downward trend in
that window. This provided no clear stopping point for a one-time mining sweep.

**Repeated behaviors were split across wordings.** One leading behavior appeared at support 18, 11
and 10 under separate descriptions. Adding such supports suggested a much stronger recurring core,
but could double-count the same exhibitor; consolidated support remained an upper bound until
instance identities were deduplicated.

**The lifecycle bounded the queue, but judging remained expensive in calls.** At game 30 there were
40 incumbents, 30 probation entries, 168 queued and 502 archived. The queue stayed around 150 entries
with expiry, and probation admitted about 12% of inflow. Duplicate judging made 5,350 calls, about
178 per game.

The initial all-in estimate was $0.02–0.03 per game. July 13 billing later showed the unit-cost
estimate was too low (§14), especially for long detector prompts. The call counts remain useful;
that original dollar estimate should not be reused.

**Decision.** Before accepting continued growth, review the full corpus to distinguish genuinely new
patterns from duplicates missed by the online matcher.

---

## 11. Batch review: a recurring core within a growing tail (2026-07-12)

The concern was concrete: about 22 new entries per game would exceed 2,000 entries by game 100 if it
continued. Either the vocabulary was still expanding or the capped online matcher was increasingly
missing duplicates. A strong-model review of each full channel tested the second explanation.

The reviewers used a behavioral criterion: two descriptions match only if a reader would count the
same moments as examples of both. The work ran in Claude-side sessions rather than the project's
metered API runner; “$0 API” describes that accounting boundary, not zero computational cost.
Creation order and simulation records allowed the fresh-entry curve to be reconstructed after review.

**The review found both a bug and a matching limitation.** Twenty-four entries were identical strings:
the simulation had not refreshed its exact-match index between rows within one game batch. That bug
was fixed. Broader review also reunited paraphrases the online candidate filter had missed, especially
in the voting channel. The retaliation-vote family alone had 27 wordings and summed support around 69,
still subject to instance-level double counting.

**Growth remained after consolidation.** The retained store contained 596 entries rather than 740,
and fresh-entry yield was still around 16 per game in the observed window. The share of entries later
seen again fell from 37% for the first ten-game cohort to 19% for the next and 11% for games 21–25.
Later cohorts had less time to recur, so these rates do not establish convergence. They did show that
many newly added entries were singletons while a smaller set carried recurring behavior.

**Decision.** Keep an archive, bound active detection, and seed the detector from the consolidated
corpus. A finite vocabulary was no longer an assumption needed to make the design affordable.
Source: `outputs/consolidated_store.json` and the frozen consolidation inputs and cluster outputs.

---

## 12. Move semantic deduplication to periodic folds (2026-07-12)

The online judge had made about 178 calls per game yet missed duplicates that a broader batch review
reunited. Newly mined tells also had no same-game consumer. These findings favored delaying semantic
admission rather than paying for immediate pairwise decisions with limited context. Call count was
the demonstrated overhead; calling it the largest dollar cost would ignore the detector's longer
prompts and the later billing correction.

The adopted proposal kept mining and detection per game, with a frozen checklist between updates.
Every ten games, a *fold* would resolve new wordings against the existing registry, recompute counts,
review probation and publish the next checklist. Canonical text would remain unchanged so accumulated
measurements still described the same claim.

A separate strong-model audit approximately every thirty games was proposed for merging or splitting
existing entries. It was not the same operation as admitting new wording. The fold would delay
candidate admission by up to one interval; the audit would remain an additional operational obligation.
The fold was later implemented (§17); the broader audit was not automatically scheduled.

The proposal also limited the duplicate-comparison index so an ever-larger archive would not overwhelm
matching. These bounds applied to computation, not deletion of the historical instance records.

---

## 13. Detect behaviors without revealed roles (2026-07-12)

The detector's risk was whether a cheap model could recognize the same behavior consistently across
players and days. It received a public transcript, a focus player and up to 48 checklist entries per
channel, without the true-role header used by mining. The first run covered five games and 90 scans,
with 317 detections and a 4% quote-flag rate. Completed scans were stored alongside detections.

**Evaluation used 40 selected, provisionally labelled cells.** Twenty came from detector positives
and twenty from zero-detection cases on leading tells. Five Opus adjudicators, one per game, saw the
cases and role-blind transcripts without detector answers. A subsequent read upheld all ten cases
where adjudicator and detector disagreed. Withholding answers reduced anchoring, but selecting cases
from the detector's own output limited independence and coverage. Human review remained planned.

The variants exposed different errors:

| Variant | Finding on the labelled set | Interpretation |
|---|---|---|
| Initial detector | Discussion precision 10/11, vote precision 7/10; recall 67% discussion and 54% vote | Relational mistakes and multi-day/absence-defined behaviors needed attention |
| Day-by-day scan with relation and absence instructions | Vote precision rose to 1.00 and a silent-abstain miss was recovered, but discussion recall fell | A prompt refinement could improve one channel while harming another |
| Union of the first two variants | Vote precision/recall 0.77/77%; discussion 0.85/73% | Combining views recovered misses at additional cost |
| Full-view plus vote-tally-stripped discussion view | Discussion precision/recall 0.93/87%; vote 0.77/77% | Removing the compact tally from discussion inputs recovered a previously missed multi-day pattern |

The evidence favored a union of two views, not a claim that one prompt solved detection. Relational
mistakes still affected vote precision, and difficult cases remained for human adjudication.

One byte-identical rerun produced identical rows and was initially taken as evidence of deterministic
serving. Later repeated probes corrected that conclusion: uncached row agreement ranged from 0.90 to
1.00. Temperature zero did not guarantee identical outputs. The separate caching check appears in §15.

**Decision.** Proceed with the full/split-view union at low thinking, approximately 36 calls per
nine-seat game. The initial cent-scale cost estimate was later corrected to about $0.22 per game
uncached. Treat the 40-cell results as provisional and seek an independent human check.
Source: frozen `scripts/detector_probe.py`, golden-scoring artifacts, and the later
[caching record](../../caching/experiment_log.md).

---

## 14. Measure associations on held-out arm-games (2026-07-12)

The next test asked whether candidates discovered in thirty baseline games also discriminated on
other game instances. Detection ran on twelve paired boards in each of five memory arms: sixty
arm-games and 2,160 flash-lite calls. The tells were not mined from those arm-games, but the paired
casts meant the sixty games were not sixty independent boards.

**The pairing exposed a counting bug.** Game IDs were shared across arms. Keying on game ID alone
collapsed distinct behavioral records and deduplicated exhibitors across arms. The join was changed
to include the arm; the role maps themselves agreed because the boards were paired. The correction
restored distinct game instances, not statistical independence.

**The retained union had 5,151 detections.** Several patterns showed strong associations in that
sample. Counts below are distinct detected exhibitors, not occurrences per day.

| Behavior family | Observed evil exhibitors | Recorded shrunk evil lift |
|---|---|---|
| Counter-accusing that an accuser's role claim is a distraction | 27/30 | +0.49 |
| Discouraging reliance on voting records | 41/48 | +0.47 |
| Reframing accusations as a diversion | 60/76 | +0.43 |
| Off-consensus voting | 52/70 | — |
| Defending one's own voting history | 61/84 | — |
| Public role claiming | 0/28 | — |

The investigator example later used in the book had ten investigator exhibitors out of eleven:
asserting confidence while withholding the source. The role-claim family was particularly vulnerable
to changes in model behavior. Zero evil exhibitors in the sampled 28 did not establish that evil
players never fake-claim or that a new claimant is certainly town.

**Decision.** Retain the provisional table and proceed to detector adjudication. About 96 tells had
been scanned, so selection among many candidates and paired-game dependence qualified the apparent
strength of the leading results. No correction in this record establishes their significance.

**July 13 cost correction.** Reported billing for the pass was $13 rather than the estimated
$1.50–2.50. Input volume was approximately as expected, around 17 million tokens; the effective
all-in cost was about $0.006 per call. Thinking-token charges and stale price assumptions were
possible explanations, not isolated causes. This prompted the caching investigation in §15.

Source: [provisional held-out table](outputs/heldout/provisional_lift_table.json), which records the
sixty-game paired-arm structure, detector convention, cast prior and shrinkage constant.

---

## 15. Remaining work and the caching decision (July 12–13, 2026)

After the held-out pass, the pending work was human adjudication, integration of credit and the
periodic fold, and a screen of the injected book. The held-out table already existed (§14); its
provisional status did not mean that no measurement had run.

Billing then changed the cost assessment. At the corrected rates, uncached mining and detection were
estimated at $0.25–0.30 per game, compared with roughly $0.28 for game generation in that setup.
Prefix caching offered savings but needed its own quality check.

**The probe tested accuracy as well as repeated-output agreement.** With 94% cached input, row
agreement across repeated cached runs was lower than uncached (Jaccard 0.56–0.83 versus 0.90–1.00).
Caching initially remained off. Reducing thinking to minimal was rejected because the labelled
sample yielded zero golden true-positives.

The follow-up compared cached and uncached union outputs on the 40 labelled cells. The cached union
scored vote precision 0.83 / recall 77%, and discussion precision 0.93 / recall 87%, comparable to or
better than uncached on that set. Cached prefixes with low thinking became the selected configuration,
with estimated all-in tell overhead of $0.17–0.20 per game.

This accepted variation between runs in exchange for cost savings supported by a small quality check.
Stored outputs preserve the exact evaluated run. They do not prove that variation averages away or
cannot correlate with roles. One-pass detection remained an optional cost reduction, not an established
replacement for the two-pass union.

Source: [caching experiment log](../../caching/experiment_log.md), July 13 probes.

---

## 16. Human review changes the validation scope (2026-07-13)

The human-review bundle sampled six held-out games on distinct boards, with two focus players and
two channels per game: 24 cells. It combined a fresh cached detector run with existing uncached rows
and model prelabels, shuffled without identifying their source. Pooling increased candidate coverage;
it did not make recall complete.

Two preparation problems were fixed before review. The sampler could choose a player killed before
having any discussion, and the seeded selection changed when the sampling code changed. The focus
players were therefore checked for activity and recorded explicitly in the published bundle.

**One game was reviewed end to end.** Seven of eight detector judgments were upheld. A rejected
“at the last moment” phrase implied a change of heart unsupported by the transcript. Four tell IDs
also described one silent-bandwagon event. The initial blind read found none of the five subsequently
ratified behaviors, which favored pooled review for this session but limited the independent recall
check. Source: [human verdicts](outputs/owner_golden/owner_verdicts.json).

**Decision.** The remaining games could use candidate adjudication rather than a complete blind read,
and the provisional labels were accepted for the first credit build. The original human-validation
requirement was relaxed; it was not completed by that decision.

**A separate granularity check asked whether detected instances could resolve near-duplicates.** At
arm/game/player/day grain with at least ten instances, it proposed no automatic merges and flagged
seven parent/child relationships. Some broad parents had near-zero lift while their narrower children
carried a role association, so collapsing a child into its parent could erase the signal.

The check also exposed a limit: duplicate descriptions competed for detector assignments. Four near-
duplicate vote entries had low co-firing Jaccard, 0.04–0.14, despite describing one event family.
Low overlap therefore could not prove distinctness. Semantic review still had to propose merges;
pooled counts were a diagnostic, not proof that the meanings matched. The accepted rule was to keep
discriminating sub-patterns distinct from broad, uninformative parents.

---

## 17. Integrate the pipeline and screen book injection (2026-07-13)

The probes had produced a detector, a registry and a provisional association table. The next risk was
whether those pieces could feed the existing memory loop and whether the resulting prompt block could
change an agent's decision.

**Build.** Mining and detection moved into `evaluation/src/loop/tells.py`, arithmetic into
`tell_credit.py`, and periodic curation into `tell_fold.py`. The research driver gained the tell path.
`Agents/memory/tell_book.py` supplied an environment-gated block before the read instruction in day and
night prompts. The recorded suite result was 653 passing tests; that was build verification, not a
measurement of gameplay benefit. The broader merge/split audit was not part of this automatic fold.

The same integration also replaced the discussion judge's credit role with deterministic strategy
grading. That work belongs to the [credit reference](../../credit/report.md), separately from tell
accuracy and injection.

**Attribution check: did a claimed strategy follow match the action?** A seeded, AI-adjudicated sample
found 13 enacted follows and two misses out of 15. One miss was an empty passed turn; the other was a
conciliatory defense contradicting aggressive advice. The new spoken-turn filter addresses the first,
not the second. The stored one-sided 95% upper bound on non-enactment is 36.3%. It does not establish
that attribution error is only harmless dilution.

Source: [frozen attribution sample](../../credit/attribution_spot_check.json). Earlier prose incorrectly
said both misses were passes; the individual rows support the distinction above.

**Injection screen: could the book affect output through the actual prompt path?** Forty frozen
nine-seat voting decisions from the older memory A/B archive were replayed with and without a book,
without other memory content. The initial book changed 7/40 decisions. Correct votes were 18/40
without it and 17/40 with it, with two wrong-to-right and three right-to-wrong changes.

Inspection found that higher-lift discussion entries had filled the book, leaving no vote tells.
The selection cap was changed to reserve slots per subject role and channel. The balanced 12-entry
book was replayed on the same 40 decisions: 11 changed; correct votes were 20/40 without the book and
24/40 with it. Five changed from wrong to right and one from right to wrong. The recorded one-sided
exact p was about .11 across those six correctness-discordant pairs.

**Decision.** The screen supported continuing with a channel that affected outputs, not claiming an
improvement in decision quality. The no-book result also differed between the two runs, so their
contrast does not isolate the effect of balancing alone. Current-epoch transfer remained unmeasured.

Sources: [initial screen](outputs/book_screen.json),
[balanced screen](outputs/book_screen_v2_balanced.json), and
[12-entry book](../../../evaluation/frozen_eval_sets/tell_book_v1_seed.json). Both result files name
the v1 book path; the initial book's composition is recorded here, while the retained v1 file is the
balanced version. Do not treat that path alone as an immutable input fingerprint for both runs.

---

## 18. Select by subject role, including town power roles (2026-07-14)

The first book excluded role-revealing town tells. The revised decision removed that exclusion:
inferring a role from public behavior was the purpose of the channel, and the same knowledge would
be available to all factions. A wolf might use it to hunt an investigator; the investigator might
use it to recognize an exposed pattern.

This revealed another selection problem. The book had reused positive *evil-lift* eligibility, which
excluded town-role associations even without an explicit role filter. Selection was therefore changed
to the subject role's concentration above its cast prior. Credit eligibility and useful read evidence
became separate choices.

**Build.** The book ranked tells by subject-role shrunk lift, required at least eight exhibitors, and
kept up to three per subject-role/channel group. The new 34-entry seed covered all six historical role
types. Its leading investigator example had 10 investigators among 11 exhibitors and lift 0.5486.
The recorded suite result was 655 passing tests.

The 12-entry book remained the artifact behind §17's balanced replay. The larger book was not
re-screened, and some healer/vigilante entries had lift only about +0.03–0.06 above prior. Whether
those weak entries added useful information was not established.

Source: [34-entry v2 book](../../../evaluation/frozen_eval_sets/tell_book_v2_seed.json), generated by
the [frozen builder](scripts/build_seed_book.py) from the provisional held-out table.

**October 13 implementation check.** The prompt hook still exists, separately controlled by
`WW_TELL_BOOK`. The current loader expects subject-role counts, matching v2's schema; v1's `evil`
count field belongs to the old interface and is not directly compatible. The ten-seat plan leaves
tells outside deployment scope. Neither current code inspection nor the July functional tests
establishes transfer to that game or a gameplay benefit.

---

*Sources — this log absorbs the probe's working notes in place; the frozen prompts are in
[`prompt_versions/`](prompt_versions/), per-run outputs and store snapshots in `outputs/`, and the probe
scripts under [`scripts/`](scripts/) (`tell_mining_probe.py`, `dedup_v0.py`, `ledger_sim.py`,
`consolidation_prep.py` / `consolidation_apply.py`, `detector_probe.py`, `golden_sampler.py` /
`golden_score.py`, `heldout_lift.py`, `owner_golden_build.py`, `granularity_screen.py`) alongside. The pipeline
graduated to `evaluation/src/loop/` (§17); the scripts here stay as frozen records of how each
result was produced.*

Implementation pointers were checked against repository revision `d206680d` and the October 13, 2026
working tree. Historical measurements retain their linked run artifacts; this is an editorial review,
not a new experimental run.
