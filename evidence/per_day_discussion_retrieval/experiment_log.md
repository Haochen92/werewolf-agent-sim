# Per-Day Discussion Retrieval — Design Analysis + $0 Pre-Test

> **What this is.** The record of a design question that has not been built: should discussion memory be
> retrieved **once per day** for each agent, instead of **once per discussion turn** as it is today? It runs
> from the thought experiment through a first-principles analysis of the trade to a $0 pre-test that gated the
> idea against existing retrieval traces before any code was written. The pre-test falsified one branch of the
> argument (a "free lunch" cost cut) and, in the same pass, surfaced an independent finding about the live
> retrieval query. Later entries supersede earlier ones; the one measuring instrument that got falsified is
> shown in its place (§3.3) rather than edited away.
>
> **Companion docs.** The two artifacts this log documents are colocated:
> [`scripts/within_day_retrieval_diversity.py`](scripts/within_day_retrieval_diversity.py) (the study,
> a FROZEN RECORD) and [`data/within_day_retrieval_diversity.json`](data/within_day_retrieval_diversity.json)
> (every number below is lifted from here). The mediation finding §2.2 leans on lives in
> [`../metrics/report.md`](../metrics/report.md) §3; the deceiver-discussion numbers in
> [`../discussion_tagger/report.md`](../discussion_tagger/report.md). No `report.md` exists yet — the
> log-first convention holds until the variant graduates. Guiding principle throughout: **gate a behavior
> change on a $0 recompute before spending on a live A/B.**

---

## 1. Motivation — the per-turn cost, and the per-day thought experiment (2026-07-07)

**What runs on every discussion turn today.** A day's discussion is a sequence of single-speaker **turns**:
the sequential scheduler picks one agent to speak at a time, that agent generates one utterance, and the loop
repeats. Every one of those turns runs the full memory-retrieval pipeline. In code, each turn calls
`enrich_payload_with_memory` (`Agents/turn/pipeline.py`, the day path at line ~99 and the night path at
~281). The retrieval query is not a cheap embed of the raw transcript — it is *itself* an LLM call. The
situation agent (`Agents/memory/retrieval/situation_agent.py`, ~lines 186–212) runs
`get_llm().with_structured_output(...)` to compose a per-cell situation summary; that composed string is then
embedded and matched against the store, and the top 3 memories after reranking are injected. So per-turn
discussion retrieval costs one extra situation-summary LLM call on top of the turn's own generation call.

**The variant.** Retrieve once per agent per day, at day-open, and reuse that memory block for the agent's
whole day of discussion. The framing shifts from "given the transcript so far, what memory fits *this*
moment" to "given yesterday's outcome and today's board, how should I guide my discussion today." Night
actions and the day **vote** are untouched — each keeps its own per-decision retrieval.

**The trade the owner stated, up front.** Pros: cheaper (one retrieval per agent-day, not per turn); a
coherent day-long stance instead of a possibly-shifting one; easier wolf-pack coordination around a shared
plan. Cons: it loses mid-day adaptation. If an investigator reveals a hard result against a wolf in the
middle of the day, that wolf must deflect *now*, and a stance retrieved at dawn may not carry the counter.
The credit implications were unclear, and the whole thing was unexplored.

**Root cause of the uncertainty.** The idea has two independent justifications — it is *cheaper* and it is
*more coherent* — and they are only worth acting on if the per-turn granularity it removes is not buying real
adaptation. That is an empirical question about existing games, not a matter of taste, so it can be answered
before writing a line of the variant. Everything below aims at it.

---

## 2. First-principles design analysis

Four consequences of the grain change, worked out before the pre-test. Each is a design argument, stated as a
proposal; none is a validated result. The numbers that later ground §2.1 and §2.3 come from the §3 pre-test
and are cross-referenced, not imported early.

### 2.1 Economics — larger than "one fewer call," and partly a power lever

The naive statement is "save one situation-summary call per turn." The precise statement is: per-day grain
saves `(turns-per-agent-day − 1)` situation-LLM calls per agent-day, because the first turn still retrieves
and the rest reuse. The pre-test measured turns per retrieving agent-day at **2.38–3.24** across all cells
(§3.4), so the cut is `(T−1)/T` of the retrieval-side LLM calls — roughly **58–69%** of them. That is the
retrieval query cost, not the turn-generation cost, which is unaffected.

There is a second, conditional saving. A memory block that is fixed for the whole day stops the prompt prefix
from churning between an agent's turns, which is the precondition for prompt-cache reuse across a day's turns.
The naive read is "so per-day grain also buys a cache win." It does not, yet: the repo's known prompt-cache
layout debt puts the role block *before* the shared prefix, so implicit caching already sits near 0%, and a
stable memory block cannot help until that layout is fixed. State the cache win as **conditional on the
cache-layout fix**, not as a benefit of this variant.

Why the economics matter beyond the invoice: the open compounding question is **power-constrained** — its
plan gates paid runs on a minimum detectable effect that a fixed budget can barely reach. Cheaper generation
is therefore more games per dollar, so a real retrieval-cost cut is partly a **power lever**, not only a cost
line. That is the strongest form of the "cheaper" argument, and it is why the idea is worth analyzing rather
than dismissing as a micro-optimization.

### 2.2 The adaptation con is faction-asymmetric — and lands where discussion matters

The stated con — losing mid-day adaptation — is not uniform across factions, and the asymmetry decides how
much the con costs. Two independent instruments agree on the shape.

For **town**, discussion carries no win signal beyond the vote. The metrics apparatus measured the town
discussion proxy (`town_accusation_precision`) partialled on vote accuracy at **partial r = +0.02** (p=.76,
n=175); the LLM discussion tagger, partialled on the same vote proxy, put town discussion merit at **+0.02**
as well (N=24) — a different instrument and sample reaching the same null (both lifted from
[`../metrics/report.md`](../metrics/report.md) §3 and [`../discussion_tagger/report.md`](../discussion_tagger/report.md)).
The structural reading is mediation: for town, the collective day vote is nearly the only actuator, so
discussion changes the game only by *becoming votes*, and the vote sits on the causal path. This is what makes
per-day near-free *for town*: its discussion value cashes out at the vote, and the vote keeps its own
per-decision retrieval, so a mid-day pivot still reaches the one decision that mediates town's discussion into
the outcome.

For **deceivers** the same tagger, same partialling, reads **+0.56 for wolves and +0.60 for the serial
killer** (N=24). A deceiver's discussion acts on *other* players' votes — a path its own vote proxy does not
mediate — so reactive deflection quality is real skill, and it is exactly the skill mid-day adaptation
protects. This is where the con bites: a wolf who retrieved a dawn stance and is then named by a
mid-day reveal is the concrete failure the owner named.

Two mitigations were designed for that case, both unbuilt:

- **Contingency-shaped day plans.** Retrieval already returns a *portfolio* (top 3), not a single lesson. A
  per-day selection can prefer conditional strategy points ("if a claim lands on you → counter-claim /
  discredit / redirect") over point-in-time ones, so the dawn block already carries the branch the wolf needs
  when the reveal comes. Naive alternative — retrieve a single best-fit lesson at dawn — fails precisely
  because it is point-in-time; the fix is to bias selection toward lessons that pre-load contingencies.
- **Hybrid event-triggered re-retrieval.** Re-run retrieval mid-day only on a deterministic trigger that the
  discussion already emits as structured output — the clearest being an accusation aimed at the agent, which
  is a `DayDiscussOutput.addressed_targets` entry with `stance == "accusation"` on the agent's own id
  (`Agents/schemas/game_events.py`). Role-claim events are structurally captured too, though in the post-day
  `DaySummaryOutput.role_claims` schema rather than per utterance, so a per-turn role-claim trigger would need
  the same speech-act tags surfaced mid-day. The design keeps the day-grain default and pays the extra
  retrieval only on the rare turns that actually changed the deceiver's situation.

### 2.3 Credit gets cleaner, at one real cost

The v7 loop credits a strategy point when an agent *followed* it and then acted well. Under per-turn
retrieval an agent may retrieve and follow several times a day, so the day's outcome is split across several
turn-level follows and attribution blurs — which stored point actually drove the day is ambiguous. Per-day
grain gives **one followed strategy point per agent-day**, so the day's decisions attribute to one stated
plan. Two further alignments fall out: the grain now matches the discussion tagger, which already scores once
per day, so the credit unit and the tagging unit agree; and it removes a quiet non-independence problem —
within-day turn verdicts are correlated, so counting per-turn follows overstates the effective sample behind a
strategy point's credit.

The cost is throughput. A strategy point can accrue at most one follow per agent-day instead of one per turn,
and agents take 2.38–3.24 discussion turns per day (§3.4), so follows accumulate roughly **2.4–3.2× slower**
per strategy point. Any `min_follow` threshold in the learning loop therefore takes proportionally more games
to clear. This is a learning-loop *throughput* hit, not a *validity* problem — the credit each follow carries
is cleaner, there is just less of it per game.

### 2.4 Taxonomy — a config-flag variant, gated like all paid runs

By the repo's versioning policy (`CLAUDE.md` → Versioning Design Variants), the choice between config-flag and
worktree-on-tag turns on whether the variants coexist, are compared repeatedly, and differ incrementally. This
one is a textbook config flag: per-turn and per-day retrieval would coexist behind one stable interface
(`retrieval_granularity: turn | day`), be compared repeatedly, and differ by *when* an existing pipeline runs,
not by a structural rewrite. So no worktree, no tag — a flag. Any *paid* comparison of the two arms is gated
behind the compounding plan like every paid run; this pre-test is the $0 step that decides whether such a run
is even worth proposing.

---

## 3. The $0 pre-test — is the per-turn churn real adaptation?

### 3.1 The gating question

The whole analysis hinges on one measurable fact: **how often do an agent's per-turn retrievals within a
single day actually differ?** Two outcomes, opposite verdicts. If within-day retrievals are mostly
*identical*, per-turn grain is paying an LLM call per turn for near-duplicate results, and per-day grain is
close to a free lunch. If they *pivot* turn-to-turn, the divergence quantifies what a per-day design would
have to preserve. The test recomputes this from traces already on disk, so it costs nothing and runs before
any build.

### 3.2 Data, units, and metrics

**Data.** Every batch already writes an eval-case sidecar per game
(`batch_results/eval_cases/<dataset>/<game>.jsonl`, schema `eval_case_v2`) — a durable per-decision record
carrying, for each turn, the retrieved observation and strategy-point `key`s, the composed `situations` query
text, `memory_enabled`, `retrieval_skipped_reason`, and the day. The study scans memory-on `day_discussion`
turns with retrieval not skipped, across **19 arm×faction cells spanning three epochs** — the v5-era `ab_*`
sets, the `ab_epochB_*` sets, and the current `v6ab_*` sets. Totals across the 19 cells: **3,916 retrieving
agent-days, 3,265 of them multi-turn, and 7,156 consecutive-turn pairs.**

**Units.** An **agent-day** is one `(game, player, day)` triple — every turn one agent took on one day. A
**multi-turn agent-day** is one where the agent spoke at least twice; it is the only unit where within-day
retrievals *can* differ, so single-turn days are counted but excluded from the divergence rates. (The
eval-case's `round` field is only the within-day ordering index used to sequence a day's turns; the sequential
scheduler replaced discussion rounds with a per-utterance `seq`, but the recorded field name persists.)

**Metrics.** Three, all deterministic. (1) **Identical-day rate** — the share of multi-turn agent-days whose
turns all retrieved the exact same combined key-set. (2) **Mean consecutive-turn Jaccard** — for each
adjacent pair of turns, the **Jaccard index** of their retrieved key-sets, meaning the size of the
intersection over the size of the union: 1.0 is identical, 0 is disjoint. It is computed separately for
observations and strategy points, with the convention `J(∅, ∅) = 1`. (3) **Turns per retrieving agent-day** —
the situation-LLM-call savings factor of §2.1.

### 3.3 A falsified instrument, recorded in place

The pre-test needed a second pass to separate *signal* churn (retrieval tracking a genuinely changed
situation) from *noise* churn (the query being reworded, or the top-3 boundary swapping among near-tied
scores). The live query is an LLM call, so both are possible. The **first** discriminator was binary: bucket
each consecutive pair by the word-set Jaccard of its two composed query strings, split at 0.8, and read
set-churn within the high-similarity bucket as noise (near-identical query, different retrieval → not
adaptation).

That instrument returned **zero pairs above 0.8 query similarity, in every cell.** The situation agent rewords
its query on essentially every turn: sit-text Jaccard sits at **0.256–0.268** across all 19 cells, near-constant
across every arm, faction, and epoch. That invariance is itself the tell — a query that tracked events would
vary its self-similarity as events varied, so a flat ~0.26 across a serial killer's endgame and a villager's
information-starved opening is paraphrase variance, not event-tracking. The binary discriminator was replaced
with a graded one: the **Pearson correlation** of (query-text similarity, retrieved-set overlap) across pairs,
plus **tercile means** of set-overlap sorted by query similarity. The falsified v1 is kept here because the
zero-pairs result *is* the finding that forced v2.

### 3.4 Results

**One inline instance, lifted (v6ab_townsp_town_only).** A real composed query string from that cell begins:

> "A player who survived a serial killer attack is among the survivors, and the village has yet to initiate
> any concrete discussion or accusations. Information landscape: The game is entirely information-starved with
> no confirmed roles or investigative results revealed. Stakes: Eight alive with a ser…"

Its top retrieved strategy point had key `f24cb58f-0bb8-4333-bc78-aa5fe55a5c5e` at similarity **score 0.837**,
matched against that same composed string. This is one lifted single instance, shown so the reader can picture
what "a retrieval" concretely is: an LLM-authored situation paragraph, embedded, matched to a stored lesson by
key and score.

**Divergence — per-day retrieval is not output-equivalent to per-turn.** Representative cells; the "active
type" column names the memory the arm actually retrieves, and the consecutive-Jaccard shown is that type's.

| Cell | Faction | Epoch | Active type | Multi-turn agent-days | Turns/day | Identical-day | Consec. J (active) |
|---|---|---|---|---|---|---|---|
| `ab_nh_town_town_only` | town | v5-era | obs | 369 | 2.90 | 2.7% | 0.381 |
| `ab_nh_wolf_wolf_only` | wolf | v5-era | obs | 148 | 3.08 | 2.0% | 0.391 |
| `ab_nh_sk_serial_killer_only` | SK | v5-era | obs | 71 | 2.91 | 7.0% | 0.513 |
| `ab_epochB_nhtown_town_only` | town | epoch B | obs | 52 | 3.12 | 5.8% | 0.375 |
| `v6ab_townsp_town_only` | town | v6ab | SP | 319 | 2.61 | 2.8% | 0.357 |
| `v6ab_skboth_serial_killer_only` | SK | v6ab | obs + SP | 76 | 2.89 | 1.3% | 0.396 / 0.337 |

*Reading the table.* Across all 19 cells the identical-day rate is **0–9%** (0.0% to 8.7%), and the
active-type consecutive Jaccard is **0.33–0.51**. So within a day an agent almost never retrieves the same set
twice, and adjacent turns typically share only a third to half of their retrieved memories. The variant is a
real behavior change, not a re-labeling of identical output. **One column artifact to state where it appears:**
in a single-type arm (obs-only or SP-only) the *inactive* type is never retrieved, so its column reads
`J(∅, ∅) = 1.0` by the convention above — that is two empty sets being trivially identical, **not** a stable
retrieval. Only the active-type column carries meaning there; the `v6ab_skboth` row, which retrieves both,
shows both types churning (obs 0.396, SP 0.337).

**Signal versus noise — the churn is mostly not situation-tracking.** Same cells, second pass:

| Cell | Sit-text J | Pearson r (sitJ, setJ) | Set-J by query tercile (lo / mid / hi) | n_pairs |
|---|---|---|---|---|
| `ab_nh_town_town_only` | 0.262 | 0.236 | 0.311 / 0.394 / 0.437 | 802 |
| `ab_nh_wolf_wolf_only` | 0.262 | 0.226 | 0.342 / 0.367 / 0.465 | 333 |
| `ab_nh_sk_serial_killer_only` | 0.267 | 0.340 | 0.389 / 0.550 / 0.600 | 162 |
| `ab_epochB_nhtown_town_only` | 0.262 | 0.281 | 0.334 / 0.300 / 0.484 | 110 |
| `v6ab_townsp_town_only` | 0.265 | 0.148 | 0.321 / 0.346 / 0.404 | 670 |
| `v6ab_skboth_serial_killer_only` | 0.263 | 0.318 | 0.285 / 0.351 / 0.393 | 176 |

*Reading the table.* The correlation between how similar two turns' queries are and how much their retrieved
sets overlap is **positive in all 19 cells but weak — r = 0.148 to 0.377.** Set overlap does rise with query
similarity, but slowly: pooled tercile means climb from ~0.30 in the least-similar-query third to ~0.47 in the
most-similar third (per-cell lows 0.236–0.393, highs 0.393–0.600). The load-bearing number is that high
tercile. Even among the pairs whose queries are *most* alike, the retrieved sets still share under half their
members — the top-3 boundary keeps swapping among near-tied scores regardless of what the query says. So the
per-turn churn is only weakly coupled to the stated situation; a large part of it is retrieval-side noise —
query paraphrase plus boundary swaps — not mid-day adaptation.

### 3.5 Verdict, scoped

- **(a) The free-lunch branch is falsified.** Within-day retrievals differ on 91–100% of multi-turn
  agent-days, so per-day retrieval is not output-equivalent to per-turn. It **cannot ship as a pure cost
  optimization**; adopting it is a design change, and a design change needs a paired A/B, not a recompute.
- **(b) The churn per-turn buys is substantially noise, which strengthens the variant's case.** The near-flat
  ~0.26 query self-similarity and the weak sitJ→setJ coupling say most of what per-day retrieval removes is
  query paraphrase and top-3 boundary jitter, not situation-tracking. Noise-churn also undercuts the
  within-day *coherence* that per-turn grain was implicitly supposed to provide, so the coherence argument for
  per-turn is weaker than assumed.
- **(c) What this test cannot say — stated, not smoothed.** Key-set churn may overstate *content* churn. The
  store carries near-duplicate memories, so a swapped key can be an almost-equivalent lesson; whether a swap
  changes the *advice* is a semantic question a string-set metric cannot answer. The house rule is explicit:
  deterministic screens measure structural properties only, and semantic questions need a read or an LLM
  judge. This pre-test does neither, so it bounds *how much the retrieved set changes*, not *how much the
  guidance changes* — and the latter is the named next step (§5), not a settled result.

---

## 4. Spinoff observation — query-wording instability is a tunable, independent of grain

The ~0.26 turn-to-turn self-similarity of the composed query is a property of the situation agent, not of the
retrieval grain. The agent rewrites its situation paragraph almost from scratch each turn even when little has
changed, and that instability is a large part of the retrieval churn measured in §3.4. It is tunable *without*
touching the turn-vs-day question: lower the decoding temperature of the situation call, or cache the day's
situation string and edit it incrementally instead of regenerating it. Stabilizing the query would reduce
retrieval churn under the **current** per-turn design too, and might recover part of the coherence the per-day
variant is reaching for without changing the grain at all. This is unexplored and flagged here as a separate
lever, not folded into the per-day decision.

---

## 5. Status, decision, and limitations

**Status.** The pre-test is **done** — 2026-07-07, $0, deterministic, recompute-only over existing sidecars.
The variant is **parked as a config-flag candidate** (`retrieval_granularity: turn | day`), gated behind the
compounding plan. It is **not** pre-registered as an A/B; the free-lunch shortcut that would have let it ship
without one is closed (§3.5a).

**Next steps, in order.**

1. **Semantic-equivalence read.** Sample consecutive within-day retrievals that swapped keys and judge whether
   the swaps are *different advice* or *paraphrases of the same advice*. This is the §3.5c question the string
   metric cannot answer, and it decides how much real adaptation per-day grain would actually sacrifice.
   Method constraint, stated up front: the judgment must be an **LLM pairwise judge or a human read** —
   embedding/cosine similarity is *not* a duplicate judgment (the project's dedup pipeline learned this
   directly: embedding similarity holds only prefilter status there, gating candidate pairs for an LLM
   duplicate classifier that makes the actual call). The existing dedup pairwise classifier is the natural
   apparatus to reuse.
2. **If built:** ship the `retrieval_granularity` flag with contingency-portfolio selection (§2.2) and
   optional event-triggered re-retrieval (§2.2), and compare per-turn vs per-day through the standard paired
   A/B, under the compounding plan's spend gate.

**Limitations.** Word-set Jaccard is a crude text metric — it ignores meaning and word order. The
consecutive-pair analysis compares only adjacent turns, so a day that drifts monotonically over four turns
registers as small step-to-step churn even though its first and last retrievals differ substantially. The 19
cells span three behavioral epochs, so the figures are reported **per cell, never pooled across epochs**. And
no part of this test makes a content-level judgment: every number bounds set membership, none bounds advice.

---

*Sources — the two colocated artifacts
([`scripts/within_day_retrieval_diversity.py`](scripts/within_day_retrieval_diversity.py),
[`data/within_day_retrieval_diversity.json`](data/within_day_retrieval_diversity.json)); the per-turn
retrieval call sites in [`../../Agents/turn/pipeline.py`](../../Agents/turn/pipeline.py) and the LLM query
composer in [`../../Agents/memory/retrieval/situation_agent.py`](../../Agents/memory/retrieval/situation_agent.py);
the town-discussion mediation reading in [`../metrics/report.md`](../metrics/report.md) §3 and the deceiver
partial-r numbers in [`../discussion_tagger/report.md`](../discussion_tagger/report.md); the config-flag-vs-worktree
policy in [`../../CLAUDE.md`](../../CLAUDE.md) → Versioning Design Variants.*
