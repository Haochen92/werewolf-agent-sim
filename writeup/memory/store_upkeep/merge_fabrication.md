# What the merge score did not measure

A Level 3 page for [Removing duplicates](store_upkeep.md#why-the-best-scoring-merge-was-switched-off):
what the best-scoring design's evaluation measured, and what it missed.

## Two jobs in one merge

A merge does two jobs. It chooses an operation: which entries in a cluster are copies, and which to
keep apart. Then it writes one entry to replace several. A merged entry is **faithful** when every detail
in it can be found in one of its sources. My evaluation scored the first job, not the second.

## The labelled set

The test set came from a nine-seat store before deduplication: 522 entries in 34 clusters of similar
ones. Seventeen clusters were labelled by hand. Each label is a decision about a group: keep the
entries apart, discard copies into one survivor, or merge entries into one rewritten entry. The test used
eleven clusters, nine with real discards or merges and two where everything should be kept, 111 entries
in all.

Each design's answer was turned into one action per entry and compared with the label. The score counts
the entries whose action matched. It does not check which entries were grouped together, which one
survived, or what the merged text says.

## The designs compared

| Design | Entries matching the label |
|---|---|
| Best single model, one pass | 96 of 111 (86.5%) |
| Two passes, sort then merge | 99 of 111 (89.2%) |

In the two-pass design, a small, cheap model sorts every cluster first, a step called **triage**. Its keeps
and discards stand, because on this set they were right about nine times in ten; its merges were right
only one time in three. So every entry it proposed to merge, 28 of the 111, went to a stronger model,
which decided again and wrote the merged text.

The three-entry lead is small. Each design ran once, and the best single model, rerun with the same
prompt, scored 81 of 100 (one cluster's answer could not be read). The score did not settle which design
was better; the merged text settled who should write it.

## What the score did not see

The cheaper models, the best single model among them, almost never wrote a complete merge. They returned the merged situation and dropped
the move and the outcome, which are the lesson. Three prompt changes meant to fix this each broke the
structured output on several clusters. Only the stronger model kept all three fields.

So I reviewed its text with a separate call, taking every operation that rewrote text in a run of the
stronger model alone on the same 111 entries: five observation merges and four lesson discards that
rewrote their survivor. For each, the reviewer saw the source entries' text and the rewritten
entry, scored them, and answered yes or no to whether the rewrite added context not present in any
source. That yes is what "flagged" means. It flagged three of nine. The reviewer was the same model that
wrote the merges, so this is not an independent check, and three of nine is not a rate. The two-pass
run's own merges were never reviewed.

Rereading the three flags for this page, all concern tactic counts such as "(3x)". In two, the counts
match how often the source entries had been observed, a number the writer was shown and the reviewer was
not. Those flags say more about the review than about the merge.

The third shows what neither check measured. The stronger model merged six investigator
observations into one. The labels said two pairs of copies and two distinct entries. One distinct entry
recorded an investigator whose checks had cleared only villagers, and who led the vote on a public voting
record alone. The merged situation reads:

> "In the mid-to-endgame, when strong public evidence (like voting records or contradictory behavior)
> implicates a wolf that the Investigator has also privately identified or strongly suspects, and a
> village consensus is forming or can be formed around this public evidence."

That source's situation was rewritten into the others'. The reviewer flagged the counts and gave the merged
situation full marks for being retrievable by every source's searches.

The same pattern appeared on a whole store. Run a second time on a store it had already deduplicated,
the two-pass design absorbed 30 more observations into 22 entries it rewrote. Some joined distinct situations, such as
an early-game investigator accusation with an endgame lead on the final wolf: different searches would
find them, and they teach different lessons.

## The decision

I switched rewriting off. Since 2026-06-22 the observation fold runs triage only: the cheap model's keeps
and discards stand, and a merge it proposes becomes a keep. Since 2026-10-13 lessons are only kept or
discarded, and the survivor keeps its own text.

The reason is what each mistake costs. A duplicate kept by mistake costs a retrieval slot. A wrong merge
deletes its sources and leaves text that players read as advice, with nothing to show which parts came
from a game and which did not.

## What a checked merge would require

This is proposed, not built or tested:

- Code, not the model, writes anything countable, by summing the sources' observation counts.
- Before the store write, each merged entry is checked against its sources by a reviewer that sees
  everything the writer saw and is not the writer's model. Every detail must trace to a source, and no
  source's situation may be rewritten into another's.
- A failed or missing check leaves the sources unmerged.
- The check is trusted only after it is scored on merges labelled faithful or unfaithful, for misses and
  false flags. The three flags above would be its first cases.

<!-- Sources and verification, 2026-10-28:
Data set: evidence/dedup/batch_dedup/experiment_log.md "Dataset" (batch_dedup_clusters_v4.json: 34 clusters,
522 items, v4 store pre-dedup; golden labels 17 clusters / 149 items; eval set 11 clusters / 111 keys, 9 with
DISCARD/MERGE + 2 pure-KEEP controls; KEEP 77 / DISCARD 20 / MERGE 14). Nine-seat: addendum 2026-10-26 ("nine-seat
May content"); dedup/report.md layer 5 ("nine-seat v4 store"). Labels by hand: evaluation/frozen_eval_sets/
batch_dedup_golden_labels.json records labeler "human", created 2026-05-26, group operations with survivor and
notes; labelling tool evaluation/experiments/batch_dedup_labeler.py (commit 7a64dbcc). Labeller identity is not
recorded beyond "human".
Scoring: evaluation/experiments/batch_dedup_eval.py score_cluster at 7a64dbcc (per-key action match; group
membership, survivor and merged text unscored).
Table: batch log "Model comparison (v3 prompts, indexed keys)" (gemini-3.5-flash 96/111) and "Two-pass golden
eval results (v3 prompts)" (gemini-3.1-flash-lite at medium thinking triage -> gemini-2.5-pro verify, v3 default
prompt, 99/111, 28/111 keys escalated; data/eval_two_pass_lite_pro_20260527_042221.json). Other single models:
2.5-pro 93/111, flash-lite 80/111.
Triage precision "nine in ten" / "one in three": batch log "Two-pass pipeline" (flash-lite KEEP 56/61 91.8%,
DISCARD 13/15 86.7%, MERGE 11/34 32.4%).
Rerun variability: batch log "Merge Rewrite Quality" > Analysis ("Worst same-prompt re-run: 81.0% (81/100, 1
cluster failed)"; C14 40-100%). One run per design: batch log tables; one two-pass result file.
Dropped fields and the three failed prompt fixes: batch log "Merge Rewrite Quality" > Analysis and "Key findings"
5. Recounted 2026-10-28 from data/eval_*.json MERGE operations: 3.5-flash runs 1 of 26 merges with approach and
outcome, flash-lite runs 5 of 43 (hence "almost never").
Review: batch log "Merge Rewrite Quality" (judge gemini-2.5-pro; dimensions; 3 of 9; restated note 2026-10-28);
data/merge_quality_gemini_2.5_pro_20260526_140255.json (source run eval_gemini_2.5_pro_20260526_133120.json,
single-pass 2.5-pro; 5 observation MERGEs in C4, C11, C14 x2, C16; 4 strategy DISCARD-with-rewrite in C21, C25 x2,
C33; flagged C4, C14 [4 keys], C16). Selection = every operation with merged text in that run
(evaluation/src/studies/batch_dedup_merge_eval.py _extract_merge_cases). Reviewer input: evaluation/src/judges/
batch_dedup.py _format_source_entries (situation, approach/outcome or action; no observation_count); fabrication
definition: evaluation/src/judges/prompts/batch_dedup.py item 4. No merge_quality file exists for the two-pass run.
Reread of the flags, 2026-10-28 (this page; not in the evidence log): writer saw observation_count (batch_dedup_eval
format_entries at 7a64dbcc). C14 [55ad1ead + 3 keys]: "(3x)" = 55ad1ead observation_count 3, others 1x each. C16:
"(6x)" = 3 + 3; the reviewer's own reasoning calls it "likely a valid aggregation from the larger cluster". C4
merge (6 keys, survivor a5db9f55): golden DISCARD pairs de5ab922+01348533 and 13891db7+a032bec1, KEEP 3d9a71f0 and
a5db9f55; 3d9a71f0 situation "had not yet found a wolf ... private information had only cleared villagers",
approach "leading the charge ... public evidence"; merged situation quoted from the source run; merged tactic counts
5+4+3 = 12 against summed observation counts 13; reviewer scores retrieval 5, preservation 2, fabrication true.
Second run: batch log "Idempotency Test" and "Analysis of second-pass changes" (two-pass on v4_deduped_v2, 432 ->
387; 30 observations merged, 22 survivors rewritten, 22/22 all fields; early-game vs endgame investigator example).
Decision: batch log status note (2026-10-28); dedup/report.md "The rewriting merge" and layer 5; triage-only:
commit 970bddf6 2026-06-22 (TwoPassConfig.skip_verify), Agents/memory/batch_deduplication/cluster_agent.py
(MERGE downgraded to KEEP), Agents/memory/consolidation/obs_fold.py (no_merge=True default); lessons: commit
2036f83a 2026-10-13. Merge deletes absorbed entries: operations.py module docstring; v3 prompt
(evidence/dedup/batch_dedup/prompt_versions/batch_v3_no_keep_bias.py). No pre-write check: dedup/report.md "The
rewriting merge" (fabrication judge only in evaluation code); batch log "Open risk".
Per-entry judge: merge was also removed from the one-at-a-time judge (per_extraction/experiment_log.md v11).
Checked merge: proposal only; not in code or evidence. -->
