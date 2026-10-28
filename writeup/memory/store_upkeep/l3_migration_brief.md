# Store upkeep: L3 migration handoff

Prepared 2026-10-28. Editorial instructions, not public page copy.

**Status 2026-10-28 (later):** carried out. `store_upkeep_revised.md` replaced `store_upkeep.md` (the earlier
text kept as `store_upkeep_pre_revision.md`); both L3 pages written (`dedup_judge.md`, with
`#where-the-lesson-judge-failed`; `merge_fabrication.md`); the lesson dedup now groups by stage before the
judge. Not approved for publication.

## Files and replacement sequence

- Original: [store_upkeep.md](store_upkeep.md). Preserve its detailed prose and source comments while drafting L3.
- Shorter L2 candidate: [store_upkeep_revised.md](store_upkeep_revised.md).
- Follow [the L3 rubric](../../portfolio-level-3-writing-rubric.md) and [claim boundaries](../../memory_presented_set.md).
- Draft the two L3 pages below. Do not create separate pages for clustering, incremental stability or the lesson trial.
- Once the L3 samples are ready for integration, check their findings and limitations against the candidate, replace its planned-link markers with real links, and use the candidate to replace `store_upkeep.md`. Carry forward the original source comment and these verification notes where relevant; do not lose provenance during replacement. Update the memory content plan if titles or scope change. No publication approval is implied.

## 1. `dedup_judge.md` — How the dedup judge was built

**Reader question:** How was the keep-or-discard judgement developed, and why was it still inadequate for lessons?

**Added value:** Explain candidate selection and judgement as separate sources of error, then show how labelled cases, embedding checks and prompt/model comparisons informed the design. End with the unresolved lesson failure rather than implying the early calibration validated today's judge.

**Why separate:** The datasets, comparison conditions and error analysis require more attention than the L2 mechanism walkthrough.

**L2 anchors:** Link after “How an observation is judged” to the page; link after “Preserving lesson history” to the heading `Where the lesson judge failed` (`#where-the-lesson-judge-failed`). These are two entry points to one investigation.

**What stays in L2:** Metadata, embedding and judge roles; one opposite-advice example; the seed-based clustering rationale; lesson-history safeguards; the finding that relaxed labels did not fix the lesson judge; disabled status.

### Material to migrate or develop

| Material | Original location / source lead | Purpose in L3 |
|---|---|---|
| 65 hand-labelled cases, eleven prompt versions, action before situation, reported 72% → 84%, no neutral lean | Memory `content_plan.md`, dedup report and experiment records | Explain what changed and what the evaluation actually measured; do not present prompt iterations as independent confirmation |
| 232-case recheck; opposite-advice case 155; embedder-specific thresholds and stale configuration | Original source comment; `evidence/dedup/report.md` | Show where similarity can and cannot decide equivalence; separate observation and lesson paths |
| 916 of 919 observations in maximum-size clusters | Original “How a pair is judged”; dedup report and clustering plan | Diagnose candidate grouping; distinguish measured behaviour from the proposed explanation involving repeated section labels |
| Cluster construction, neighbour limit and reported 80–100% versus 26–74% accuracy | Original “Clustering the batch pass”; batch experiment log | Explain the tested grouping choice; establish denominators, models and conditions before quoting ranges |
| 694 → 605 lessons; 65 remaining duplicate groups; 37 crossed labels; relaxed-filter trial caught 16 groups and made 25 cross-stage drops | Original “Deduplicating lessons” and its source comment; dedup report layer 5 | Separate filter exclusion from judge failure. Groups and discarded lessons are different units |
| Model-selection evidence, including October addendum | Original source comment; batch experiment log | Distinguish historical winners from current configuration and current validation |

**Verification needed:** Read the records named in the original source comment, not just the shortened candidate. Confirm which labels were relaxed, historical versus current stage safeguards, exact model identities and datasets, and whether current judges have any ten-seat evaluation. Resolve the apparent tension between the original final section (“not tested on ten-seat content”) and the described ten-seat trial by naming the relevant version and kind of evaluation. Do not silently infer that the trial evaluated today's configuration.

Keep this page bounded: candidate formation and judge reliability. The retrieval-impact experiment and protection of old entries remain short L2 explanations; they need not become additional experimental chapters here.

## 2. `merge_fabrication.md` — When merging memories invented facts

**Reader question:** Why reject the best-scoring design, and what did its evaluation fail to measure?

**Added value:** Distinguish selecting an operation from producing faithful merged content. Develop the two-pass design, label comparison and review of generated entries as separate checks.

**Why separate:** A reader needs the label definitions, output examples and review method to assess how the metric missed the failure.

**L2 anchor:** Immediately after “Why the best-scoring merge was switched off.”

**What stays in L2:** 111 entries in 11 clusters, two-pass winner, operation-versus-content distinction, 3 of 9 merges flagged, small sample and same-model review caveat, rewriting disabled and source checking required before reintroduction.

### Material to migrate or develop

- Original comparison table: best single model 96/111 (86.5%); two-pass design 99/111 (89.2%). Name models and conditions from records, and retain relevant rerun variability rather than presenting a three-entry difference as decisive evidence of general superiority.
- Label composition (77 keep / 20 discard / 14 merge in the original source notes), how entries were labelled, and how per-entry operation agreement was scored.
- Smaller models dropping the move and outcome fields; stronger model preserving fields but introducing unsupported details. Use a source-grounded example if the records provide one; do not invent an illustrative merge.
- Separate review call: how the nine merges were chosen, what the reviewer saw and what “flagged” means. Same-model review is not independent factual validation, and 3/9 is not a general fabrication rate.
- What a checked merge would require. Clearly label proposed safeguards as proposed, not implemented or validated.

**Source leads:** Original source comment; `evidence/batch_dedup/experiment_log.md`; `evidence/dedup/report.md`. Confirm actual paths and historical settings before drafting.

**Verification needed:** Dataset units and label provenance, exact model/prompt comparison, dropped-field evidence, the nine reviewed outputs and the absence of a pre-write faithfulness check at that time.

## Material reserved for interview preparation or supporting notes

No separate interview narrative is drafted here: personal motivations should come from the owner.

- Explicit new-entry keys versus timestamps that loading/saving could reset: a useful implementation follow-up.
- Running twice without changes versus stability under new arrivals: L2 keeps the mechanism; an interview can explore how it was discovered and the rejected alternatives.
- Invalid survivor IDs, exact neighbour counts and retry details: retain in evidence or discuss when asked about implementation reliability.
- Why the owner initially expected rewriting to help, what prompted the faithfulness review, and what would justify revisiting the decision: useful personal-story prompts, not facts to infer.

## Editorial changes requiring attention before replacement

The candidate is editorially revised, not freshly factually verified.

1. General statements about all agglomerative clustering have been narrowed to the approaches tested. Verify the historical configuration before naming an algorithm in L3.
2. “Nothing it recorded is lost” is now aggregate-count preservation. Observation source identity still has a known gap.
3. The 17% and 39% figures stay with the retrieval comparison; they are not safe/unsafe thresholds or measurements of the incremental experiment.
4. The filter explanation now describes the effect of rejecting a mismatched pair. It does not claim that any possible metadata error can only retain duplicates.
5. The candidate scopes the no-rewriting protection to deduplication; it does not claim every stored entry is verified.
6. The blanket statement that current judges have not been tested on ten-seat content is omitted pending version-specific verification above. Disabled lesson status and the unrun full learning cycle remain explicit.
7. Current lesson stage safeguards are described separately from historical trial failures. Verify when those safeguards were introduced so the L3 chronology does not imply the same configuration both enforced and violated them.
8. The diagram is simplified and identifies accumulated entries plus explicit new keys for the batch pass. Confirm this represents the intended automated path rather than an unrestricted manual run.
9. Owner follow-up: retain useful technical terms with explanations. The candidate now explicitly distinguishes idempotency on unchanged input from incremental convergence, and names the code-enforced invariant. The retrieval LLM's warning and the separate incremental design defect must not be presented as one discovery or as proof that deduplication improved retrieval. Source checked for this distinction: `evidence/dedup/incremental_convergence.md`.
10. The observation prefilter was checked against `Agents/memory/deduplication/prefilter.py` and `pipeline.py`: it embeds full content for all remaining candidates, computes every new-to-candidate score, and thresholds the maximum. It does not reuse situation-only retrieval vectors or compare only the first retrieval hit. The middle band passes all remaining candidates to the judge.

Keep the original source comment with the final L2, updating its claim mapping after migration. Do not mark either L3 or the replacement L2 approved solely because the prose and links are complete.
