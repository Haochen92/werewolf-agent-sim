# Memory: the pipeline, the design decisions, and whether it helps

The memory system gives agents advice drawn from earlier games. It turns game records into observations,
condenses observations into lessons, retrieves those lessons during play, and uses recorded decisions to
help decide which lessons to keep. The engineering problem is broader than storing and retrieving text:
a useful memory must describe the right situation, preserve what actually happened, offer applicable
advice and avoid accumulating misleading or repetitive lessons.

This report is the entry point to that whole system. It explains the current pipeline, the decisions
that shaped it and what the experiments established. The component reports own the detailed mechanisms,
measurements and implementation references.

Three points frame the story:

- **The pipeline is built; its benefit in today's game is unmeasured.** The ten-seat system, v8, has
  component checks and one demonstration of credit and pruning. No ten-seat comparison tests memory
  on against memory off. Served memory is optional and starts off.
- **Earlier experiments gave mixed results.** A June test reported improvements on selected town
  decision measures, with multiple-comparison and baseline caveats. A later test on a different store
  found no town effect. The July learning experiment found no benefit from the finished memory;
  its estimate leaned toward harm. These are different comparisons, not successive confirmations.
- **The main engineering work was controlling what entered, survived and reached the prompt.**
  Situation-specific retrieval replaced whole-role documents. Dedup became conservative about deleting
  or rewriting advice. Credit and synthesis were separated so recorded outcomes could be processed
  without paying to regenerate lessons. These choices address observed failure modes; they do not,
  by themselves, establish better play.

**Scope.** This hub summarises the component reports' snapshots of 2026-10-26. Their version lines
identify the implementation each describes; their studies retain their original game, store and model
settings.

## The pipeline today

An **observation** records a move and its effects in one finished game. A **lesson**, called a
**strategy point** in code, recommends an action for a role in a particular situation. Both are stored
in **cells** organised by role and phase: discussion, vote or night action. Observations supply the
material for synthesis; served agents retrieve lessons only.

There are two connected paths. During a game, the system retrieves existing lessons. After games,
offline jobs can build and curate the store used by future games. Finishing a served game does not
by itself update that store.

| Stage | What it does | Important boundary |
|---|---|---|
| Save and extract | A finished game saves its extraction input; an offline model writes observations from it | The server saves input but does not run extraction. The published store includes manually extracted AI-only server games; no routine extraction job for served games is recorded |
| Review the outcome | A second model revisits outcome verdicts that may reward the winning side regardless of the move; decision tags also allow rule-based grading | The second model changes verdict labels, not all observation text. Both model verdicts and rule-based grades have limits |
| Fold and synthesise | Dedup keeps or discards observations; synthesis groups them into lessons | Stored text is not merged in the active dedup paths. The published store received a one-off rule review; later learning ticks have no equivalent automatic screen |
| Retrieve during play | Describe the seat's situation, search its cell, fetch five candidates and keep up to three per situation | Up to two situations means up to six lessons. No retrieval on day 1 or its night, for human seats, or for town seats' discussion turns |
| Record adoption | For each shown lesson, the agent reports follow, override or not relevant | These are the agent's reports of use, not independent proof of what caused its decision |
| Credit and publish | Grade decisions associated with followed lessons, compare with memory-off play, apply retention rules and publish to Postgres | Credit and learning are separate, manually run passes. The ten-seat learning tick has no recorded run |

Retrieval reuses a lookup across a seat's discussion turns until a new role claim, and within a night;
wolves use separate lookups for pack discussion and action. Votes look up afresh. This reduces repeated
calls, but its effect on the relevance of later-turn advice has not been measured. Optional filtering,
reranking, field matching and stage filtering are off in served games. Follow-outcome counts can affect
ordering and reserve a slot for an unproven lesson; that is a heuristic, not evidence that the lesson helps.

The [v8 report](v8/report.md) owns the complete current-system account, including the published store,
model choices, deployment record and component checks.

## How the design evolved

### From whole-role advice to situation-specific retrieval

Early agents received a complete strategy document for their role. Transcript review found advice being
applied where it did not fit, so the project moved to retrieving a few entries for the current situation.
That introduced two separate problems: selecting useful entries and ensuring the store contained them.

The May retrieval studies explored filtering near-repeats, reranking with a model and showing more
observations. Filtering and reranking produced mixed results on five cases; the capacity study found
small judge-score differences across 120 replayed decisions. Neither established a whole-game gain.
Some situations had no suitable lesson to retrieve at all. That remains an important distinction:
better ranking cannot supply missing advice. The [retrieval report](../retrieval/report.md) explains
these studies alongside the current read path.

### From removing duplicates to preserving meaning and evidence

Repeated entries occupy scarce prompt slots. Once lessons also received credit, duplicates split their
follows across several records, making each harder to assess. Dedup therefore became part of evidence
management as well as storage cleanup.

More aggressive cleanup was not consistently better. In a 40-scenario study, conservative dedup gave
slightly more distinct retrieved lessons, while aggressive dedup lost relevance. Rewriting merges also
introduced unsupported content in reviewed examples. The active paths now keep or discard, preserve
surviving text and carry duplicate keys forward so credit can recover their follows. Incremental guards
protect old entries from repeatedly being judged against one another; the October fix passes explicit
new-entry keys from the learning tick. The [dedup report](../dedup/report.md) owns that mechanism and its
validation limits.

### From a fixed store to an outcome-guided learning loop

The June static-memory test froze the store to keep the treatment consistent. Selected town measures
improved, but neither wolves nor the lone killer showed a detectable benefit. A later test on a rebuilt
store found no town effect. Prompt and retrieval screens also failed to produce a clear general fix.
The project then prioritised improving lesson content, without establishing that retrieval was solved.

v7 played games in generations, scored decisions associated with followed advice, synthesised lessons
and pruned the store. Two June runs were invalid for their intended questions: one used a distorted
credit baseline, and the other gave memory to the wrong factions. They led to paired controls and
checks of the arm that actually ran. A power simulation also showed that the planned trend test was
unlikely to detect the expected improvement at the available budget.

The July endpoint instead compared the finished memory with no memory on 30 paired boards. It found
no benefit. Investigation identified a credit blind spot: abstention advice could score neutral and
survive pruning even when it contributed to passive play. Re-scoring recorded games with corrected
rules removed the example lesson, but the corrected loop was never played. This explains a retention
failure; it does not establish that the fix would reverse the experiment. The [v7 report](v7/report.md)
owns the experiment; the [credit report](../credit/report.md) owns the scoring and correction.

### From the research loop to separate operational passes

v8 adapted the pipeline to the ten-seat game. Extraction moved offline to keep lesson-building calls
out of gameplay. Saved extraction inputs allow later processing; lookup reuse reduces repeated reads;
Postgres publishing gives the server a persistent store rather than rebuilding one for every game.

Curation now separates **credit**, which recounts and grades existing decisions without model calls,
from **learning**, which adds observations and pays for synthesis. The distinction allows credit to run
without regenerating advice. Growth controls limit synthesis to cells and groups with new material,
age out observations and cap unproven lessons. No measured run has established that the stores reach
a stable size, and no ten-seat learning tick is recorded. The [store curation report](../store_curation/report.md)
explains these controls and their failure history; v8 explains their place in the full pipeline.

## What the experiments establish

A **paired board** uses the same initial role deal and seed for both conditions. This controls the
starting setup, not model sampling or the later course of the game.

| Comparison | Finding | What limits it |
|---|---|---|
| June fixed store, 30 paired boards | Healer saves 37% → 60% (p = 0.005); correct town eliminations 47% → 64% (p = 0.028). Town wins 27% → 43% (p = 0.27) | Selected raw-arm measures; that arm was not pre-registered. None clears correction across all 24 raw-arm tests. The baseline may have drawn low |
| Later v6 store, 30 paired boards with its own baseline | No town effect detected; town win difference +6 percentage points (p = 0.77) | Different store, prompts and run period; not a replication of June and not proof of no effect |
| July v7 endpoint, 30 paired boards | Town decision score lower by the reported 0.147; worse on 19 boards. Paired t-test p = 0.065; Wilcoxon p = 0.105 | Final memory against none, not a direct test of improvement between generations. Treatment included lessons and tells. Reported as “no compounding detected” |
| October v8 component checks | Retrieval-fit review, rule-error review, outcome-verdict analysis, decision-tag check and one credit demonstration | No memory-on versus memory-off comparison; stage-filter findings concern a setting off in served games |

The June, v6 and v7 experiments used the player model at its minimal thinking setting. A later probe
reported zero reasoning tokens for that configuration; this does not establish an absence of internal
reasoning or predict results at other settings. Small samples, changing stores and possible provider
drift further limit comparisons across campaigns. The [effectiveness report](effectiveness/report.md)
owns the June and v6 results, including the low-baseline concern.

## Where to read next

The reports are organised by reader question, not by folder chronology. Read **v8** for the architecture,
then the component involved in the decision you want to understand. Read **effectiveness** and **v7** for
the experimental history. Fine-tuning is a supporting research branch, not a stage in today's pipeline.

| Report | Its distinct job |
|---|---|
| [v8](v8/report.md) | Current end-to-end pipeline, operational decisions, checks and deployment status |
| [Effectiveness](effectiveness/report.md) | Whether a fixed store helped; June and v6 comparisons and replay screens |
| [v7](v7/report.md) | The learning-loop experiment, power analysis, amended endpoint and negative result |
| [Extraction](../extraction/post_game/report.md) and [observation quality](../extraction/observation_quality/report.md) | What is extracted and how outcome bias affects it |
| [Situation query](../extraction/situation_summary/report.md) and [situation fields](../extraction/situation_dimensions/report.md) | How the read path describes the seat's current situation |
| [Retrieval](../retrieval/report.md) | Candidate selection, caps, reuse and optional ranking/filtering studies |
| [Dedup](../dedup/report.md) | Duplicate identity, conservative removal, survivor history and incremental guards |
| [Credit](../credit/report.md) | Decision grades, memory-off comparisons and the abstention blind spot |
| [Store curation](../store_curation/report.md) | Retention, growth controls, synthesis triggers and publishing passes |
| [Fine-tuning](../fine_tuning/report.md) | Four attempts to replace model calls; trained artifacts, none integrated |
| [Strategy adoption](strategy_adoption/report.md) and [ablation](ablation/report.md) | Historical checks of reported memory use and observations versus lessons |
| [Caching](../caching/report.md) | Provider prompt caching, including extraction's shared prefix |

For the writeup, these form three connected subjects: **building and retrieving memory**, **keeping its
contents trustworthy and manageable**, and **testing whether it helps**. The existing folders can stay:
combining them physically would add link churn without clarifying these questions. Detailed logs remain
provenance; they need not become separate portfolio pages.
