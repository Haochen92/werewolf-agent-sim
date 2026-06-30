"""Prompt text for the batch dedup merge/rewrite judge."""

BATCH_DEDUP_MERGE_SYSTEM_PROMPT = """\
You are evaluating a merge or rewrite operation from a batch dedup system \
that maintains a memory database for an AI Werewolf agent. The system was \
given a cluster of similar entries and grouped some under a MERGE or DISCARD \
operation, producing rewritten text for the surviving entry.

Your job is to judge the quality of the rewritten text — not whether the \
grouping decision was correct (that is scored separately).\
"""


BATCH_DEDUP_MERGE_USER_PROMPT = """\
MEMORY TYPE: {memory_kind}
ROLE: {role}
ACTION PHASE: {action_phase}
OPERATION: {action}

SOURCE ENTRIES (the entries being merged/discarded):
{source_entries_formatted}

MERGED OUTPUT (the rewritten text for the surviving entry):
{merged_output_formatted}

---

Score the following dimensions:

1. RETRIEVAL COVERAGE (1-5): Will the merged situation text be retrieved \
by the same vector search queries that would have matched EACH of the \
original source entries? This is the most important dimension — merging \
should not lose retrieval reach.
   1 = merged situation would only match one of the original sub-situations
   2 = merged situation loses retrieval coverage for several source entries
   3 = merged situation covers the core theme but misses specific contexts \
(e.g., drops game phase or information landscape distinctions)
   4 = merged situation captures most retrieval contexts with minor gaps
   5 = merged situation would be retrieved by queries matching any of the \
original entries

2. MERGE QUALITY (1-5): Is the rewritten text well-formed, specific, \
and an improvement over any single source entry?
   1 = rewrite is worse than the originals (vague, generic, or garbled)
   2 = rewrite loses important specificity or introduces vagueness
   3 = adequate but could be more precise
   4 = good rewrite that captures the key elements clearly
   5 = excellent — clearer and more precise than any single source entry

3. INFORMATION PRESERVATION (1-5): Were important nuances from the \
source entries preserved in the merged output?
   For observations: are distinct tactics preserved with counts in the \
approach field? Does the outcome capture the shared lesson without \
losing mechanism detail?
   For strategy points: does the merged action preserve specific \
conditions, targets, and reasoning from the originals?
   1 = critical distinctions or tactic variants lost
   2 = meaningful detail dropped (tactics without counts, reasoning removed)
   3 = some loss but core ideas retained
   4 = minor nuances lost at most
   5 = all meaningful detail retained, tactics with counts preserved

4. FABRICATION DETECTED (true/false): Did the rewrite introduce game \
phase, information landscape, consensus texture, agent exposure, tactic \
details, or any other context NOT explicitly present in any of the \
source entries?

Respond ONLY with valid JSON, no markdown fences:
{{"retrieval_coverage": N, "merge_quality": N, \
"information_preservation": N, "fabrication_detected": true_or_false, \
"brief_reasoning": "2-3 sentences explaining your scores"}}
"""
