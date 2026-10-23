# Learning behavioural tells: build log (July 2026, status checked October 2026)

> **What this is.** The date-ordered path from "can a model propose role-revealing behaviours?" to a working tell pipeline in the nine-seat research loop, and what became of it. Later entries supersede earlier ones. A design that was falsified is shown where it happened, not edited away.
>
> **Companion docs.** The mechanism as it stands: [`report.md`](report.md), which also defines the terms used here (tell, read, miner, detector, checklist, book, fold). This log condenses the folder's earlier `experiment_log.md` (§1–18) and `report.md`, both in git history at `2382b34c`.

---

## ① Motivation: beliefs need evidence of their own (2026-07-10)

The memory system stored lessons: advice about what to do in a situation. Each turn, an agent also states its reads (its suspicions about who holds which hidden role). Nothing stored evidence for those beliefs. The credit redesign of 2026-07-10 split the two: lessons would be scored by outcomes, and beliefs would come from *tells*, factual claims of the form "players who do X are usually role Y" that can be checked by counting.

The natural way to find tells is to show a model finished games with the roles revealed. That is a defensible discovery method: the model sees everything and can spot patterns a human would miss. Its failure is in measurement. A model that knows the wolves notices what the wolves did and does not count the villagers who did the same thing. So the root problem was hindsight in the counts, and the plan was to separate the jobs: a miner that may see roles proposes, a detector that cannot see roles counts on other games, and code joins the roles.

## ② Mining prompt: from a word ban to a knowledge boundary (2026-07-11)

*Catches:* descriptions that leak hidden knowledge, invent motives or retell one game instead of naming a reusable behaviour. Five nine-seat games, one call per game-day, Gemini 2.5 Pro.

- **v1** gave 177 candidates with no role words or player IDs in the descriptions. Villagers were the largest exhibitor group in the 91 rows read, so the miner was not just listing evil players. The quote checker first flagged 54 of 177 quotes as absent. After normalising Unicode punctuation and edge ellipses, 11 remained: most flags had been formatting, not invented evidence. The real defects were spliced quotes, invented motives ("to establish credibility") and plot retellings.
- **v2** required one contiguous quote, separated a player's stated motive from the miner's guess, and asked for the move type or no entry. It gave 184 candidates; quote defects fell from about 6% to 1%.
- **v3.** A review against the game's knowledge rules showed the role-word ban was wrong both ways. "Justifies a past vote against a now-confirmed ally" has no role word but asserts a hidden relationship. "Claims to be the investigator" has a role word but is public. v3 allowed role words only as public events ("claims to be", "revealed on death as") and banned hidden relationships. It gave 181 candidates with no flags, including seven about claims and reveals.

*Decision:* the rule is whether a reader who cannot see the roles could check the behaviour. v3 became the base prompt.

## ③ A cheaper model, and a split input that rescued it (2026-07-11)

*Catches:* mining a larger corpus on Pro was projected at $15–30, so the cheaper model had to be tested. Same five games, v3 prompt.

Gemini 3.1 Flash-Lite gave 116 candidates and none in groups of exactly repeated wording (Pro: 181 and 24). Repeated wording matters because it lets identical behaviours merge for free. Its missing discussion candidates suggested it was attending to the compact vote list. **v4** split each day into two calls: the discussion call left out that day's votes, and the vote call kept the discussion. The split gave 213 candidates and 19 rows of repeated wording, and recovered three of four reference patterns in one inspected gap.

*Decision:* adopt v4 on Flash-Lite. The sweep estimate fell to $2–3, a figure that later billing (⑨) showed to be too low. Yield is not accuracy: review still found inferred motives in about 1–2% of rows.

## ④ Merging duplicate wordings (2026-07-11 to 07-12)

*Catches:* the same behaviour stored under several wordings, which would split its counts. Matching had to span roles within a channel, or the roles could not be compared.

A word-overlap filter over 202 wordings found only ten candidate pairs, though a manual read found about fourteen variants of "votes for own accuser". Embeddings found candidates, but their scores were compressed (median pair 0.84), so a fixed cutoff admitted 2,837 pairs. Ranking the nearest candidates and judging 400 per channel gave 166 entries from 213 rows; 1 of the 44 merges was questionable. A strong-model review of the 166 then kept 107: it found 45 more merges and dropped 14. One of its verdicts was overturned on principle: it called accuse-then-vote trivial, but a common behaviour can still separate roles, so commonness is not a reason to drop.

*Decision:* rank-based candidates, and a periodic whole-corpus review to catch what the pairwise filter misses.

## ⑤ The 30-game lifecycle simulation: no plateau (2026-07-12)

*Catches:* the plan's assumption that one mining sweep would produce a finished dictionary. Twenty-five more games were mined, and 1,109 candidates from 30 games were replayed in order through the proposed admission, probation and archive rules. There was no detector yet, so mined recurrence stood in for evidence. This tested storage, not accuracy.

The store reached 740 entries. New ones still arrived at about 22 a game in games 21–30. One leading behaviour sat under three wordings, seen 18, 11 and 10 times. The per-game duplicate judge had made 5,350 calls, about 178 a game.

*Decision:* before accepting the growth as real, review the whole corpus to separate new behaviour from missed duplicates.

## ⑥ Batch review: a recurring core and a long tail (2026-07-12)

*Catches:* growth that is really the online judge missing duplicates. A strong model reviewed each channel whole (in Claude sessions, outside the metered API). Two descriptions matched only if a reader would count the same moments as examples of both.

The review found a bug: 24 entries were identical strings, because the simulation had not refreshed its exact-match index within a batch. That was fixed. The store fell from 740 to 596, and new entries still arrived at about 16 a game. But the share of each batch of new entries ever seen again fell from 37% (games 1–10) to 19% (11–20) to 11% (21–25). Later batches had less time to recur, so this does not prove the core had stopped growing.

*Decision:* keep an archive, cap the checklist the detector scans, and seed the checklist from the reviewed corpus. A finite vocabulary was no longer needed to make the design affordable.

## ⑦ Duplicate judgment moves to a periodic fold (2026-07-12)

The online judge was the most frequent call and still split the leading behaviours. No agent needs a newly mined tell in the same game. So mining and detection stay per game against a frozen checklist, and every ten games a *fold* matches new wordings to existing entries, recomputes counts, reviews probation and publishes the next checklist. Existing entries' text is never rewritten, so their counts keep describing the same sentence. A stronger audit every ~30 games, to merge or split established entries, was proposed. The fold was built (⑫); the audit never was.

## ⑧ The role-blind detector (2026-07-12)

*Catches:* whether a cheap model without the roles can recognise checklist behaviours consistently across players and days. Flash-Lite, up to 48 behaviours per channel, five games, 90 scans, 317 detections.

Evaluation used 40 labelled cases: 20 from the detector's detections and 20 from cases where it found nothing on leading behaviours. Five Claude Opus adjudicators, one per game, labelled them without seeing the detector's answers. Picking half the cases from the detector's own output limited how independent the check was.

| Variant | Result on the 40 cases | What it taught |
|---|---|---|
| First detector | Precision 10/11 discussion, 7/10 vote; recall 67% and 54% | Relationship mistakes ("voted the accused" read as "voted the accuser") and multi-day behaviours were missed |
| Day by day, with relationship rules | Vote precision 1.00, but discussion recall fell | A prompt fix could help one channel and hurt the other |
| Full view combined with a view that strips vote tallies from the discussion | Discussion 0.93 / 87%; vote 0.77 / 77% | Removing the tally recovered a missed multi-day pattern |

*Decision:* combine two views, about 36 calls per nine-seat game, and seek a human check. One rerun that matched byte for byte was first read as proof of deterministic output; ⑩ corrected that.

## ⑨ Associations on games the miner never saw (2026-07-12)

*Catches:* whether behaviours found in 30 mined games also separate roles elsewhere. The detector scanned 60 games: 12 deals, each played under five memory settings (2,160 calls).

A counting bug came first: game IDs were shared across the five settings, so keying on the ID alone merged distinct games. Adding the setting to the key fixed it. It restored distinct games, not independent ones.

The 5,151 detections showed strong associations. Evil players held a third of the seats. "Counter-accuses an accuser of using a role claim as a distraction": 27 of 30 exhibitors evil. "Discourages relying on voting records": 41 of 48. "Calls accusations a diversion": 60 of 76. Public role claiming: 0 of 28 evil. "Asserts high confidence while refusing to give the source": 10 of 11 were the investigator.

*Decision:* keep the table as provisional. About 96 behaviours were scanned and the games share deals, so the leading results are not tested for significance. The 0-of-28 role claim describes these agents, not Werewolf.

*Cost correction (2026-07-13):* billing for the pass was $13, against an estimated $1.50–2.50. Input volume was about as expected; thinking tokens and stale price assumptions were the likely causes. This prompted ⑩.

## ⑩ Caching the detector (2026-07-13)

*Catches:* whether caching the shared transcript and checklist changes what the detector finds. 94% of input came from cache. Identical cached runs agreed on fewer rows (0.56–0.83) than uncached ones (0.90–1.00), and the uncached detector was not exactly repeatable either, which corrected ⑧'s determinism reading. Cutting thinking to the minimum was rejected: it found 0 of the labelled days against 2, on six cases. On the 40 cases the cached detector scored vote 0.83 / 77% and discussion 0.93 / 87%, as good as uncached.

*Decision:* cached with low thinking became the default. Every evaluation keeps the detector's stored output; a rerun is a new sample. Detail: [caching report](../../caching/report.md) §4.7.

## ⑪ Human review narrows the validation plan (2026-07-13)

*Catches:* whether model labels hold up against a human. The bundle sampled six games on distinct deals, two players and two channels each (24 cases), with detector rows and model labels shuffled together. The sampler first picked a player killed before speaking, and its seeded choice shifted when the code changed, so the chosen players were written into the bundle explicitly.

The owner reviewed one game end to end: 7 of 8 detections upheld. The rejected one said "at the last moment", implying a change of heart the transcript did not show. Four behaviour IDs described one silent-bandwagon event.

*Decision:* the model labels were accepted as provisional for the first build. The six-game human benchmark was relaxed, not completed.

A granularity check the same day found seven broad behaviours with near-zero association that contained narrower ones with a real association. *Rule:* never merge a narrower, informative behaviour into a broad, uninformative parent.

## ⑫ Integration, and does the book reach decisions? (2026-07-13)

**Build.** Mining and detection moved to `evaluation/src/loop/tells.py`, scoring to `tell_credit.py`, the fold to `tell_fold.py`. `Agents/memory/tell_book.py` added a block above the reads instruction in day and night prompts, switched on only by the `WW_TELL_BOOK` environment variable. 653 tests passed; that verifies the build, not any benefit.

**Replay screen.** *Catches:* whether the book changes a decision through the real prompt path. Forty recorded day votes from older nine-seat games were replayed with and without a book, with no other memory. A vote was correct if a town player voted for an evil one, or an evil player for a town one.

- **First book:** 7 of 40 votes changed; correct votes went from 18 to 17. Inspection found that high-scoring discussion behaviours had filled the book, leaving no vote behaviours.
- **Fix:** reserve slots per role and channel. **Balanced 12-entry book:** 11 of 40 changed; correct went from 20 to 24 (five wrong to right, one right to wrong; one-sided p about 0.11).

*Decision:* the channel reaches decisions; no improvement was claimed. The no-book baseline also moved between runs (18 and 20), so the two screens do not isolate the effect of balancing.

## ⑬ Select by the role a behaviour points at (2026-07-14)

The first book left out behaviours that expose town power roles. The owner ruled that out: inferring roles from public behaviour is the point, and a shared book cuts both ways (a wolf can hunt the investigator; the investigator can see what gives it away). Removing the exclusion revealed a second one: the book had reused the "points to evil" score, which also shut out town-role behaviours. Selection moved to the concentration of the subject role over its seat share.

*Build:* a 34-entry book covering all six nine-seat roles, at least eight exhibitors and up to three per role and channel. The investigator entry led at 0.5486. 655 tests passed. This book was never replay-screened, and some healer and vigilante entries sat only about +0.03–0.06 above their seat share.

## ⑭ The learning run and its test (2026-07-16 to 07-21)

The July learning loop ran with the tell pipeline on: seeded with the 34-entry book and the reviewed checklist, it mined, detected, folded and rebuilt the book in each of four generations. The 30-deal test on 2026-07-20 played each deal with and without the learned memory. Memory-on games carried the final 33-entry book, which every seat saw, alongside the town's lessons. Before the test the design was amended to drop the condition that would have separated tells from lessons ([amendment](../../../batch_results/v7_endpoint_ab/PREREG_AMENDMENT.md)).

*Result:* the town's decision score was lower with memory (by 0.147, p ≈ 0.06), as reported in the [execution-plan report](../../execution_plan/report.md) §5. The tells' own effect is unknown. On 2026-07-21 the memory research closed with no memory promoted.

## ⑮ Status against the ten-seat game (2026-10-13, rechecked 2026-10-22)

The hook is still in the prompts and renders nothing unless `WW_TELL_BOOK` is set. Nothing in the server sets it, and the loop's `tells` switch defaults to off. The v1 book uses field names the current hook cannot read. The v2 book names "wolf" and "villager", which are not ten-seat role names, so 12 of its 34 entries would never show in a ten-seat game. No ten-seat game has been mined or scanned. The ten-seat plan leaves tells out of the deployed game.

## Remaining questions

- Whether tells help play at all, separately from lessons. No test isolated them.
- Whether any July association holds for the ten-seat roles and today's models.
- Whether the detector's accuracy holds beyond 40 model-labelled cases and one human-reviewed game.
- How fast duplicates accumulate without the merge-and-split audit, which was never wired.

---

**Sources.** Original log [`experiment_log.md`](experiment_log.md) §1–18 · prompts [`prompt_versions/`](prompt_versions/) · mined rows `outputs/mining_v*.jsonl` · simulation and review `outputs/ledger_sim_*`, `outputs/consolidated_store.json` · detector rows `outputs/detector_*.jsonl` · held-out table `outputs/heldout/provisional_lift_table.json` · human verdicts `outputs/owner_golden/owner_verdicts.json` · replay screens `outputs/book_screen*.json` · frozen probe scripts [`scripts/`](scripts/) · the learning run `batch_results/v7_compound_town5/` and its test `batch_results/v7_endpoint_ab/` · caching probes [`../../caching/experiment_log.md`](../../caching/experiment_log.md).
