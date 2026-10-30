# How the deduplication judge was built

This page goes one level below [Removing duplicates](store_upkeep.md), where the judge, a model that
answers keep or discard, is the last step a pair of entries can reach.

A store can keep a duplicate, or lose a distinct entry, through errors at two separate steps.
**Candidate selection** decides which entries are ever compared: the search for similar situations, the
metadata filter, and in the batch pass the clustering. A pair it keeps apart is never judged, however
alike the two are. **Judgement** decides keep or discard for the candidates that get through, made by
the judge or, for the clearest observation pairs, by a similarity threshold without a model call. Only a
discard deletes, so only judgement can lose a distinct entry. The two fail in different ways and need
different evidence, so after the labelled cases this page takes judgement first (the prompt, the model,
the thresholds), then candidate selection (the clusters and the metadata filter), and ends with the
lesson pass, where both failed.

## The labelled cases

Another model grading the judge shows only whether two models agree, so I built **golden labels**:
answers fixed by hand that every prompt version is scored against. I sampled 65 cases from 390
decisions the judge had made in 30 nine-seat games, each a new entry with its nearest stored candidates,
and two review rounds changed 14 labels. When every model got the same case "wrong", the label was
usually at fault, because a weak prompt fails differently on different models. Most disputes were
settled by one question: would a search that finds entry A also find entry B?

A broader set of 232 cases, five games' entries searched against a store built from five others, was
labelled by two models, so I used it to test the thresholds, not to score the judge.

## What moved the judge's accuracy

The prompt went through eleven versions. Four changes held.

**A "when unsure" lean has no neutral setting.** "When unsure, prefer discard" made the small model keep
only 41% of the distinct entries; removing the line made it merge far too often. A note naming one
difference that does not count ("a different wording is not a different move") fixed that failure without
tilting every other call.

**Order beat rules.** The small model discarded lessons whose situations matched but whose advice
conflicted: it read the similar situation first and explained the actions away. Extra rules did not help;
showing the action before the situation, with the same information, raised its lesson accuracy from 72%
to 84%.

**Merge left the one-at-a-time judge.** Only 5 of the 65 labels were merges, yet the small model predicted
15 and the stronger one 8, and a wrong merge rewrites an entry. With only keep or discard, the small model rose from 73.8%
to 80.0%.

**All three parts must match.** A last rule, that two observations are duplicates only when situation,
move and outcome all agree, took it to 83.1% and cut its discards of distinct entries from 9 to 4. That
matched the stronger model's best, but the tie is not why the small model stayed. I kept it for cost and
speed, about a third of the cost per case and seven times as fast, on a comparison made with an earlier
prompt, where it still trailed, 69% against 80%. Each score is one run on 65 cases, where one case is
worth 1.5 points.

Both judges, one at a time and batch, have run since mid-October on another small model, adopted when
the offline jobs moved to another provider and scored only afterwards. What that scoring shows, and what
it does not, is in the last section.

## What the similarity thresholds cannot do

I set the lines on the 65 cases and checked them on the 232; four limits came out.

**Embeddings capture topic, not stance.** Case 155 pairs "Prioritize investigating players who are
actively pushing narratives" with "Avoid investigating the most vocal leader". The advice is opposite and
the label is keep, yet the actions sit at 0.913 similarity on the embedding model of the time and 0.881 on
today's, as close as most true duplicates.

**So only a minority of cases settle without a judge.** At the May lines, about 23% of the 232 cases
needed no model call; three attempts to decide more each decided fewer. On today's
embedding model the live observation lines decide 2 of 116 observation cases.

**A small set overfits.** A lesson discard line of 0.90 made no errors on the 65 but discarded keeps on
the 232, so 0.93 shipped. Lines set for a new embedding model from the 65 alone repeated the mistake: its
lesson discard line, 0.88, would discard two labelled keeps, case 155 among them. Lessons skip the
thresholds and go to the batch judge, so no lesson was lost.

**A threshold belongs to its embedding model.** When the embedding model was upgraded in July, the lines
stayed put; the new model needed a keep line below 0.50, so for three months the thresholds kept some
labelled duplicates: extra entries, none lost.

## How the batch pass forms its clusters

The batch pass judges a whole cluster in one call, so the clustering decides what the judge can ever
compare. The method in use in June, hierarchical clustering on the situation text at a 0.70
similarity line, put 916 of 919 observations in a June store into clusters of the maximum size: in
effect one group per role and decision, cut into chunks by the size cap. A sweep found no stable line
either: one group up to 0.80, usable clusters only between 0.88 and 0.90, fragments by 0.92. Those
counts were measured; the explanation was a proposal. Each situation was then one block of prose under
the same section labels, and I took the labels to be what made every pair look alike, with one test in
support: stripping them gave more clusters at the same line. The structured fields, by contrast, were
well spread, so they became the metadata filter the clustering now runs inside, with the seeded
clustering described in [Removing duplicates](store_upkeep.md).

Cluster size also limits the judge. On a second labelled set, 111 entries in 11 clusters from a
nine-seat store, two stronger models did this as clusters grew:

| Entries in the cluster | Clusters | Entries judged right |
|---|---|---|
| 2–5 | 3 | 100% |
| 8–10 | 4 | 80–100% |
| 11–16 | 3 | 64–100% |
| 23 | 1 | 65–74% |

I cut the cap from 25 to 15. With one cluster above 16, the cap follows a trend, not a measured edge.

## What the metadata filter costs on lessons

The filter keeps apart lessons whose direction or honesty labels differ, so the judge never compares
them. Building the published ten-seat store, the lesson pass took 694 synthesised lessons to 605. Model
readers then found 65 groups of duplicates still among the 605, 78 surplus lessons in all, and 37 of the
65 groups crossed those labels, so no judge ever saw them. The filter's effect on accuracy has never been
scored: both labelled sets predate these fields, so on them it does nothing.

## Where the lesson judge failed

The lesson pass has run once for real, in that build, and its judge was the earlier small model, the
same one the 65 cases had scored. Besides the 37 groups the filter kept apart, 28 groups shared their
labels and survived anyway. The run kept no record of why, so I cannot say whether the clustering never
put their lessons together or the judge saw them and kept them.

A trial run without writing, on the same 605 lessons with the same judge, ran the pass under the live
filter and again with the filter relaxed to honesty alone. Relaxed, it caught 16 of the 65 groups,
against 9 under the live filter, so it still missed three quarters of them, and it did not record which
misses came from the clustering and which from the judge. Its discards, though, are the judge's alone,
and many were wrong: relaxed, 25 of the 55 lessons it would have dropped went into a lesson from a
different stage of the game, and others joined different moves. That is why I read the judge, more than
the filter, as the problem.

The trial also exposed a design error. Lessons were grouped for the judge by the direction and honesty
of the move, but not by the stage of the game, so the judge saw early-game and late-game advice side by
side. Even under the live grouping, 10 of the 30 lessons it would have dropped went into a lesson from a
different stage. Those lessons are served to different seats, so they must stay separate. My first
fix, the same day, blocked such discards after the judge, which kept the store safe but left the judge
comparing pairs it could never act on. The stage facts are now part of the grouping, so the judge only
sees lessons from one stage, and the check after the judge stays as a backstop for a pass run without the
grouping. The cost is that more lessons sit alone in their group, where nothing can be compared with them:
on the 605-lesson build, 124 instead of 22.

The hand review of the published store had the same blind spot. Of the 78 duplicates readers removed, 30
came from a different stage than the lesson they kept, so the published store lacks 30 lessons that the
stage filter would have served to seats their kept twin does not reach. I left the published store as
built rather than restore them.

None of this tests today's judge. Both runs above used the earlier small model; the one that replaced it
in mid-October has never judged ten-seat lessons. It has been scored only on the May nine-seat sets: 52
of the 65 one-at-a-time cases, within two cases of the earlier judges, and on the cluster set 11 of its
18 discards right, with all 7 wrong ones in lesson clusters. A stronger model was right on all 8 of its
discards there but caught only 8 of the 20 duplicates. A wrong discard cannot be undone, so the lesson
pass is off until it is retuned, and the stage grouping above is the only part of that retune built so far.

<!-- Sources and verification, 2026-10-28:
Where the lesson judge failed: evidence/memory_system/v8/experiment_log.md 2026-10-13 (readers' 65 groups, 37 across
labels; dry run 9 of 65 / 16 of 65 caught, 10 of 30 / 25 of 55 drops across stages); evidence/dedup/report.md
layers 2 and 5 notes 2026-10-28 (stage added to the lesson partition; singletons 22 -> 124 on
memory_stores/v8_reextract_synth; 30 of the 78 hand drops cross stages); evaluation/experiments/
sp_dedup_stage_partition_check.py; operations.py backstop; commits 08dea470 (after-judge check).
L3 pass 2026-10-28 (version honesty and the two error sources):
- Framing (candidate selection vs judgement): l3_migration_brief.md §1; the error split is editorial,
  each half sourced below. "Only a discard deletes": a filter or cluster that keeps a pair apart can only
  leave both entries; the prefilter's top line auto-discards observations, so thresholds count as judgement.
- Which judge ran the ten-seat lesson pass: gemini-3.1-flash-lite, both the build of ten_seat_v2
  (2026-10-12/13; report.md layer 5 "Flash-Lite as judge") and the 2026-10-13 dry run (v8 log: "the judge
  synthesis uses (gemini-3.1-flash-lite)"); the same small model the 65 cases chose. The switch to Haiku
  5.5 came 2026-10-15 (commit d839e6f3: offline jobs default to Claude after the Gemini credits ran out;
  written on the page as "the offline jobs moved to another provider"). No ten-seat run of the lesson pass
  since (report.md layer 5: "the judge has since changed to Haiku 5.5 without a re-run").
- 28 groups that shared labels and were kept "with no record of why": v8 log 2026-10-13 and report.md
  layer 5. Dry run records only the groups it would collapse (v8_sp_dedup_dry_run.py writes survivor and
  dropped keys, not cluster membership), so misses cannot be split between clustering and judge. Judge-as-
  problem reading and "others merge different moves": v8 log dry-run entry. 10 of 30 / 25 of 55 are
  lessons dropped (units: lessons), 9 / 16 of 65 are readers' groups (units: groups); 78 = surplus
  lessons the readers would drop, not lessons in the 65 groups.
- After-judge stage rule 08dea470 dated 2026-10-13, the dry run's day. Stage in the partition: committed
  2026-10-28 (372e46c0, "the lesson dedup groups by game stage before the judge"), so the page's "now" holds.
- Retune status: TickConfig.sp_dedup docstring (honesty + stage facts, stronger judge); report.md layer 5
  note 2026-10-28 (stage half built; dropping direction and the stronger judge not).
- Model choice: per_extraction log §③ "Supporting analyses" compares on v8 D/M/K figures (flash-lite 69.2%
  vs 3.5-flash 80%, Google AI backend) and keeps flash-lite for cost/latency (~3x cheaper per case, ~7x
  faster). The same note also cites its v9d/v11b gains and the batch pass as a safety net, so the record
  does not show the choice was made strictly before the scores levelled; the page says only that the tie
  was not the reason. Current config: Agents/llm_factory/accessors.py DEFAULT_DEDUP_MODEL
  "anthropic/claude-haiku-5-5", DEFAULT_DEDUP_THINKING_LEVEL "low"; Agents/memory/consolidation/config.py
  TickConfig.dedup_model "anthropic/claude-haiku-5-5", sp_dedup False.
- 916 of 919: evidence/dedup/dedup_clustering_and_sp_extraction_plan.md (2026-06-15) "Why this is needed
  now" items 1-3 (memory_stores/v6_0; agglomerative at 0.70; max_cluster_size 15; sweep blob through 0.80,
  2 clusters at 0.85, reasonable 0.88-0.90, fragments by 0.92). The plan states the label scaffolding as
  the cause; its only cited test is "stripping the labels in a test increased cluster counts at the same
  threshold", so the page presents it as the explanation proposed at the time. Gate-partitioned
  clustering: batch log "Forming the clusters" (2026-06-16); report.md §2 "Why". The page does not say
  seeded clustering replaced hierarchical because of this finding: the record does not date that switch.
Golden labels: evidence/dedup/per_extraction/experiment_log.md §② "Building the golden set" (50 then 65
cases from 390 dedup spans, 30 games, v4_action_phase_v2, seed 42; labelled by hand in interactive review) and §④
"Lessons (the transferable part)" (two revision rounds changed 14 labels; cross-model agreement against a
label = label smell; the retrieval test). Prior check was an LLM judge with no ground truth: §①. Frozen
labels: evaluation/frozen_eval_sets/dedup_v2_golden_labels.json.
232 cases: evidence/dedup/embedding_prefilter/experiment_log.md "Validate" (5 games searched against a
store from 5 others; labelled by gemini-3.5-flash and gemini-3.1-flash-lite with the production prompt).
Eleven versions and the four changes: per_extraction log §③ and evidence/dedup/report.md §4 "The judge".
Small model = gemini-3.1-flash-lite; stronger = gemini-3.5-flash. Lean: v6 "prefer D over M, M over K",
flash-lite K recall 41% (D recall 93%); v7 removal over-merged; v8 targeted note. Order: v9d, flash-lite
strategy 72.0% -> 84.0%; added instruction and an ACTION CHECK output field did not help / regressed.
Merge out: v11, 5 of 65 M labels, predictions 15 (flash-lite) and 8 (3.5-flash), 73.8% -> 80.0%
(3.5-flash 83.1%). All-three-fields rule: v11b, 80.0% -> 83.1%, K->D 9 -> 4. Cost/speed: §③ "Supporting
analyses" (flash-lite ~3x cheaper per case, ~7x faster). Endpoint: Google AI Studio -> Vertex AI, flash-lite
v10 76.9% vs 73.8% at temperature 0 (§③ Endgame backend caveat).
Current judge (now in the last section): Claude Haiku 5.5, low thinking, since 2026-10-15; 52 of 65
(80.0%; May judges 83.1% = 54 of 65, so "within two cases"): per_extraction log "Addendum 2026-10-26",
which states it "says nothing about today's ten-seat store". Clusters: evidence/dedup/batch_dedup/experiment_log.md "Addendum 2026-10-26"
(Haiku 5.5 low: 11 of 18 discards right, all 7 wrong in strategy-point clusters; Sonnet 5.5 low: 8 of 8
right, 8 of 20 caught); lesson dedup off since 2026-10-26 (TickConfig.sp_dedup = False, e2da5f1e).
Thresholds: embedding_prefilter log "The ceiling, explained" and "Current live state, revisited
(2026-10-14)"; report.md §3. Case 155: action_sim 0.913 on gemini-embedding-001 at 1536 dims, 0.881 on
qwen/qwen3-embedding-8b; labelled keep. ~23% auto-decided on the 232 at the May lines; three ablations
(3072 dims, SEMANTIC_SIMILARITY task type, multi-dimensional boundaries) all lower on the 232. Qwen
observation lines decide 2 of 116 (1.7%). Lesson line 0.90 on the 65 vs 0.93 shipped after the 232;
Qwen lines derived on the 65 alone (2026-10-12); 0.88 would discard cases 155 and 85; strategy-point
prefilter path dormant. Embedder moved to gemini-embedding-2 on 2026-07-16 without new lines; keep line
below 0.50 needed; until the Qwen move on 2026-10-12.
Cluster size: batch log "Accuracy by cluster size (v3)" (gemini-3.5-flash and gemini-2.5-pro; C4 = 23
entries, 74% and 65%); dataset in "Dataset" (11 clusters, 111 keys, from the v4 nine-seat store); cap
8 -> 25 -> 15 in "Forming the clusters". The "26-74%" range in report.md §1 has no visible source and is
not used.
Metadata filter on lessons: report.md §2 "Evidence and limits" and §5; evidence/memory_system/v8/
experiment_log.md 2026-10-13 entries (readers' 65 groups, 78 lessons, 37 crossed direction/honesty;
dry run with gemini-3.1-flash-lite, honesty-only partition: 16 of 65 caught, 25 cross-stage drops). Gate
never scored: report.md §2 (both labelled sets predate the structured fields).
Not on this page by owner ruling: the trained cross-encoder prefilter. -->
