# Learning behavioral tells from game records

> **Scope:** the experimental tell pipeline developed in July 2026 for the nine-seat game.
> **Reviewed:** October 13, 2026. Mining, detection, fold-time curation and prompt injection were
> implemented in the research loop. The ten-seat deployment does not adopt this channel, and its
> gameplay benefit remains unestablished.
>
> **Pipeline:** finished games → candidate behaviors → role-blind detection on a fixed checklist →
> revealed-role counts → a small tell book. The [build log](experiment_log.md) preserves the
> experiments; the [design record](../../credit/read_tactic_credit_redesign.md) explains why tells
> and tactical advice need different evidence.

A tell is an observable behavior associated with a hidden role. The engineering contribution was to
separate **discovering an interesting pattern** from **measuring whether it predicts anything**.
A model proposes and detects behaviors; role counts determine the association. This makes individual
claims inspectable and allows candidates to be measured before agents receive them.

For example, the later seed book contains this behavior:

> A player asserts high confidence in an accusation while refusing to disclose the source of their information.

The book records **10 investigators among 11 detected exhibitors**, with subject-role shrunk lift
0.5486. The agent-facing line presents the behavior with its count, followed by an instruction to use
it as a prior rather than proof. These are historical observations, not a calibrated probability for
a player in today's game. Source: [the 34-entry book](../../../evaluation/frozen_eval_sets/tell_book_v2_seed.json).

## 1. What the measurement guarantees

The miner receives the public game record and a true-role header. It can use those roles to discover
candidates, but the resulting examples are selected with hindsight. A mined count cannot tell us how
often town players exhibited a supposedly wolf-like behavior and were simply overlooked.

The detector therefore receives the public transcript and a fixed behavior checklist **without the
true-role header or private night reasoning**. It checks each focus player and records detections;
completed scans are also recorded. Revealed roles are joined afterward. Only detected instances enter
the association calculation. Held-out games separate candidate discovery from this measurement.

This prevents direct use of hidden labels during detection. It does not guarantee an unbiased detector:
ambiguous descriptions, missed relational details and model behavior can produce role-correlated
errors even without the labels. Structural checks and labelled examples test those remaining risks.

A candidate must describe public behavior rather than infer a hidden relationship. “Votes for their
accuser” can be checked from the transcript; “defends their packmate” cannot be checked without knowing
roles. Public role claims and death reveals are allowed when described as claims or reveals, rather
than asserted hidden truth.

## 2. The mechanism

### Mine descriptions, measure exhibitors

The final mining prompt split each game-day into two calls. The discussion call omitted that day's
vote tally so the compact voting block would not dominate attention. The vote call retained discussion
because patterns such as voting without previously expressing suspicion require both. Each candidate
carried an exhibitor, channel and evidence quote.

Detection used the union of two views, one full and one with vote tallies removed from discussion
inputs. The selected historical configuration used cached prefixes and low thinking. Temperature zero
did not make its outputs exactly repeatable; evaluations therefore retain the actual detected rows.

For scoring, each distinct game/player pair counts once per tell, even if detected on several days.
If `c` of `n` exhibitors have the subject role and that role's cast prior is `p`:

```text
shrunk lift = (c + 5 × p) / (n + 5) − p
```

The adjustment dampens small samples. It does not correct discovery selection, correlated games or
multiple comparisons. The [credit reference](../../credit/report.md) explains why tell association
scores remain separate from strategy outcomes and agent read accuracy.

### Bound the work without discarding the archive

The corpus need not fit into every detector call or agent prompt. Three tiers serve different uses:

| Tier | What membership permits | Bound |
|---|---|---|
| Book | Injection into an agent's prompt | Up to three entries per subject-role/channel group |
| Active checklist | Detection in subsequent games, including candidates not yet injected | 48 per channel: incumbent, probation and rotation capacity |
| Archive | Retention and possible re-entry, without scanning every entry each game | Not capped by the checklist budget |

Probation gives new candidates time to collect support before ranking can exclude them. Archive
rotation gives some older entries another measurement opportunity. Selection policy and a finite
budget still affect which hypotheses are tested; “off-policy” means not dependent on injection, not
that every archived tell is continuously measured.

At a fold, the periodic curation pass, new wording is either mapped to an existing same-behavior entry
or admitted as a new candidate. Canonical wording is preserved so old counts keep their meaning.
Semantic matching uses an embedding prefilter followed by a model judgment. It is shared across roles
within a channel: splitting the same behavior by role would destroy the comparison it needs.

The implemented fold is distinct from the proposed strong-model audit of existing canonical entries.
The latter would merge or split already-established behaviors; it was exercised offline but is not an
automatically scheduled part of the loop. The fold can flag candidates for that review. An optional
book-level duplicate filter removes repeated behaviors from the prompt without pooling their evidence.
The [curation reference](../../store_curation/tells.md) records those boundaries.

### Deliver a book before the agent forms its reads

The July 14 book ranks supported tells by concentration of their subject role, including town power
roles. It requires at least eight exhibitors and positive subject lift. Separate discussion and vote
slots prevent one channel from filling every position. This differs from the older credit-eligibility
rule that selects only positive evil-lift; a town-role association can inform a read without satisfying
that credit rule.

At runtime the loader removes entries whose subject role has been fully revealed dead, then inserts
text before the reads instruction in day discussion, day voting and night prompts. The hook reads
`WW_TELL_BOOK`; without it, the block is empty. This environment switch is independent of the ordinary
memory toggle, so activation must be controlled explicitly in an experiment or deployment.

The current loader expects `subject_count` and `subject_role`. The historical 12-entry v1 artifact
instead carries `evil` counts. It remains evidence of the July replay, not a drop-in book for the
current loader. The later 34-entry v2 artifact has the subject-role fields, but still reflects the
older game and model distribution.

## 3. What was tested

The work established a usable extraction/detection path and showed that injecting tells could change
decisions. Each result answers a narrower question than whether tells improve full games.

| Question | Evidence | Conclusion and boundary |
|---|---|---|
| Could a cheap miner recover discussion patterns? | Same five games: single-call flash-lite produced 116 tells and no exact-wording convergence rows; split calls produced 213 tells and 19 convergence rows | Input separation recovered coverage and repeat wording on that sample; counts alone are not accuracy |
| Could the detector recognize checklist behaviors? | Five games and 40 provisionally labelled cells; cached union: discussion precision 0.93 / recall 87%, vote precision 0.83 / recall 77% | Supported using the detector experimentally; the small, selected, largely model-adjudicated set is not broad certification |
| Did a human check support the detector? | One independently reviewed game: 7 of 8 detector judgments upheld | Useful spot-check, too small to replace the provisional benchmark |
| Did discovered behaviors recur on other games? | 60 held-out arm-games, comprising 12 paired boards × five memory arms; 5,151 unioned detections | Several strong historical associations; correlated boards and scanning about 96 tells limit inferential strength |
| Did the balanced book affect decisions? | 40 frozen old-epoch votes, book absent versus present: 11 changed; correct votes 20 → 24 | The channel affected outputs; six correctness-discordant pairs do not establish a reliable benefit |

The provisional labels were accepted for the July build after the human spot-check. This was a decision
to proceed with bounded evidence, not completion of the originally proposed six-game human benchmark.

The held-out sample found an investigator association at 10/11 exhibitors and role claiming at 0/28
evil exhibitors. The latter illustrates the transfer risk: fake-claiming behavior can change with a
prompt or model. These are observations from the sampled agents, not general Werewolf rules.

**Replay versions matter.** An initial, discussion-heavy book changed 7/40 votes and had correctness
18/40 without it versus 17/40 with it. After balancing channels, the 12-entry book changed 11/40, with
five wrong-to-right changes and one right-to-wrong change. The no-book result also changed between runs;
this was not an isolated test of composition alone. The later 34-entry, all-role book was built after
that screen and did not receive the same replay check.

**Cost and repeatability were tested separately.** Historical billing put uncached detection near
$0.22 per nine-seat game. Prefix caching brought estimated mining-plus-detection overhead to roughly
$0.17–0.20 per game, with comparable precision and recall on the 40 labelled cells. Cached row agreement
varied more between repeated runs (Jaccard 0.56–0.83, versus 0.90–1.00 uncached). Keeping stored outputs
makes the evaluated run inspectable; it does not make a rerun identical. These are July costs and probe
results, not current pricing or ten-seat performance. [Caching evidence](../../caching/experiment_log.md).

## 4. Case study — a growing vocabulary changed the storage design

**The 30-game probe showed no saturation in new wordings, but recurring behaviors were concentrated in
a smaller core.** The design response was to bound active measurement rather than assume a one-time
mining sweep would produce a finished dictionary. It also moved semantic deduplication to periodic
batches. The experiment changed how the system spent work, not just a similarity threshold.

### Test whether growth was real or missed deduplication

The simulation replayed 1,109 mined instances through the proposed lifecycle and produced 740 canonical
entries. Support here meant mined recurrence, not role-blind detection; it tested storage dynamics,
not tell accuracy. Its strongest behaviors were split across several wordings, so apparent novelty
might have been poor duplicate recall rather than genuinely new candidates.

A strong-model batch review consolidated the corpus to 596 entries. The fresh-entry rate still stayed
around 16 per game in the observed window. Recurrence among successive birth cohorts fell from 37% to
19% to 11%; later cohorts also had less time to recur. The result supported a recurring core plus a
large one-off tail, not a proof that the vocabulary grows forever or that the core had fully converged.

### Move judgment to where it can use more context

The online duplicate judge had made 5,350 calls across 30 games, about 178 per game, yet fragmented
important behaviors that the batch review reunited. Call count was a clear overhead signal; it did
not establish the judge as the largest dollar cost, because detector prompts were much longer.

No agent needed a newly mined tell during that same game. The design could therefore delay semantic
admission until a fold and keep the checklist fixed between folds. The tradeoff was slower admission
of new candidates in exchange for fewer per-game judgment steps and a stable measurement list.
Preserving canonical text also prevented a rewritten claim from inheriting evidence for a different one.

## 5. What remains unestablished

The available evidence supports an implemented experimental channel and several measured engineering
choices. It does not establish improved gameplay, transfer to the ten-seat role set, or reliability
under today's model and prompts. Nor does the replay certify the later 34-entry book.

The unscheduled merge/split audit matters because duplicate or overly broad canonical entries can
fragment evidence or hide discriminating sub-patterns. The current fold and optional prompt-level
filter address parts of that problem, not the full audit. Detector fallibility and sample selection
remain relevant even for apparently strong associations.

These boundaries explain why the [v8 plan](../../memory_system/v8/plan.md) treats tells as an
experimental channel outside its deployment scope. The build remains useful portfolio evidence:
separating discovery from measurement, testing detection, and revising the lifecycle when the corpus
did not behave as expected.

## Evidence and implementation

| Artifact | What it preserves |
|---|---|
| [Build log](experiment_log.md) §§3–7 | Mining prompts, same-five-game comparisons and decisions |
| [Consolidated store](outputs/consolidated_store.json) and log §§10–12 | Corpus/lifecycle simulation and batch-review outcome |
| [Held-out lift table](outputs/heldout/provisional_lift_table.json) | 60 arm-games, detector convention, shrinkage and provisional status |
| [Human adjudications](outputs/owner_golden/owner_verdicts.json) and log §16 | The completed human spot-check and changed validation scope |
| [Initial replay](outputs/book_screen.json), [balanced replay](outputs/book_screen_v2_balanced.json) | Separate 40-decision screens and per-decision outputs |
| [12-entry v1 book](../../../evaluation/frozen_eval_sets/tell_book_v1_seed.json) | The balanced historical replay book, in its original schema |
| [34-entry v2 book](../../../evaluation/frozen_eval_sets/tell_book_v2_seed.json) | Later subject-role book; [frozen builder](scripts/build_seed_book.py) records its derivation |
| [Research-loop module map](../../../evaluation/src/loop/README.md) | Implementations: `tells`, `tell_credit`, `tell_fold`; prompt loader: `Agents/memory/tell_book.py` |

The probe scripts and saved prompts in this folder are frozen records. Current code inspection can
establish what is implemented; it cannot retroactively validate an old result under a new runtime.

Implementation pointers were checked against repository revision `d206680d` and the October 13, 2026
working tree. Historical measurements retain their linked run artifacts; this is an editorial review,
not a new experimental run.
