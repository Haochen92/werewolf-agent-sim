# Memory: what the agents carry between games, and whether it helps

**Does memory make the agents play better? Not shown for today's system; shown once, on selected town
decisions, for an earlier one.** The agents can be given lessons written from past games. Three
whole-game comparisons of memory on against memory off have been run (two in June 2026, one in July).
The first found the town's decisions improved on selected measures; the second, on a different store,
found no town effect and was not a replication of the first; the third, built to test whether a
memory that rewrites itself improves over time, detected no such benefit. All three ran on players
that answered without a reasoning step. The current memory, rebuilt for the ten-seat game in October
2026 (v8), has been checked stage by stage but has not been tested for its effect on play. In served
games it is the player's choice, and it starts off.

This page is the entry point to the memory area: what the system does today, what each version and
campaign established, and where each result is told in full. Each number below is stated with its
scope and links to its one detailed home; the reasoning and the caveats are there.

**Version.** The account of today's system describes the code at the `feature-frontend-v1` branch head
on 2026-10-26 (`59bae5f5`), checked against the code named in each statement. Every historical result
belongs to the game, store, prompts and model it ran on, named in its row; none of them was re-run on
today's code.

## The memory system today

Two kinds of thing are stored. An **observation** is a short account of one move and its effect,
written by a model from a finished game ("On Day 1 I argued for a slow pace to avoid drawing
suspicion; it worked"). A **lesson**, stored as a **strategy point**, is short advice for one role in
one kind of situation, written by a model from a cluster of observations ("Illusionist, night: spend a
conceal only on an unclaimed victim"). The store is partitioned by role and phase (day discussion, day
vote, night), each partition a **cell**.

- **Reading lessons in a game.** With memory on, every AI seat looks up lessons before its decisions
  from day 2 on (nothing on day 1 or the night after it): a short model call describes the seat's situation, the cell is searched by similarity, five lessons
  are fetched and three kept. A seat reuses one lookup through a day's discussion (refreshed when
  someone makes a new role claim) and one through a night; a vote always looks up afresh. Served games
  retrieve strategy points only, never observations, and a town seat gets no lessons on day turns:
  town day lessons are written but never served. For each lesson shown, the seat reports a verdict:
  follow, override, or not relevant. Those verdicts also add to counters on each lesson in the live
  store, in games with a human seat too, until the next publish replaces them with the credit pass's
  counts; lessons with a good credit record are placed first. Four optional retrieval stages are built
  and off: a filter that
  drops near-repeats, a model reranker, a filter that drops lessons learned at another stage of the
  game, and a tilt by matching situation fields.
- **Writing lessons after a game.** Extraction never runs inside a game. A game saves its extraction
  input when it ends, and an offline batch job extracts observations per cell. A second model (Claude
  Haiku 5.5) then re-reads each observation's verdict against the game record, because extraction's
  verdicts lean toward the side that won (the **halo**). The server itself extracts nothing: a served
  game saves its input, but no job yet extracts served games, even for their replays. The published
  store does include 16 AI-only games played through the server on 2026-10-10, extracted offline by
  hand.
- **Keeping the store.** Two passes. The **credit pass** (no model call) grades
  each decision at which a seat followed a lesson, using a fixed rule per role and action, and compares
  the lesson's grades with memory-off play of the same kind. It then prunes a lesson whose grades
  fall more than 0.15 below memory-off play over at least eight follows, and evicts one shown at least
  eight times, never followed, and overridden at least as often as judged not relevant.
  The thresholds are carried over from the nine-seat loop and not validated for ten seats. The pass
  grades only AI seats' decisions, in games with or without a human seat (since 2026-10-26;
  extraction still reads only AI-only games). The **learning tick** folds new observations in
  (duplicates are kept or discarded, never rewritten), lets old observations age out, synthesises new
  lessons with Claude Sonnet 5.5, and never prunes lessons. Both are run by hand (no schedule is in the repository), and both publish the
  store to the Postgres database the server reads.

What each stage does, why, and what its checks showed is in the [v8 report](v8/report.md).

## The versions and campaigns

Each row is one version or campaign: what changed and why, what it found, and where it is told in
full. An **arm** is one condition of a comparison (for example, memory on for the town only). A
**board** is one fixed deal of roles and random seed; a paired test plays each board twice, with
memory and without, so both copies start with the same luck.

| When | What changed, and why | What it found (N and scope) | Home |
|---|---|---|---|
| Before June 2026 | A single strategy document per role, injected whole, was replaced by lessons retrieved by situation, after transcript reading found agents applying old advice where it did not fit. Duplicate lessons were then removed from the store | On the earlier game, memory for every role raised the villagers' win rate from 70% to 96.7% in one unpaired batch of about 30 games a condition (Fisher p = 0.012, the best of six comparisons); the same condition fell back to 73.3% (p = 1.0) on the next store and layout. Removing duplicates did not reduce the repetition among strategy points shown (about 59% across stores), which read as missing lessons for some situations | [Effectiveness](effectiveness/report.md), the pre-rebuild batches; [dedup](../dedup/report.md) |
| May 2026 | Can an agent say which lessons it acted on? A field listing the followed lessons, placed before the action | With the chosen prompt, the agents' claims were judged accurate on 72% of turns and over-claimed on 8% (120 replayed turns, one model judge). In June, a screen asking for one verdict per lesson found the instruction ignored while it sat only in the output schema (168 of 300 verdicts given) and followed once it was also stated in the prompt (302 of 300); today's follow / override / not relevant field descends from that screen | [Strategy adoption](strategy_adoption/report.md); [forced-verdict screen](strategy_adoption/forced_schema_screen/experiment_log.md) |
| May 2026 | Do strategy points add anything beyond observations? | On 120 replayed turns under three conditions (both, observations only, strategy points only), the judge's scores differed by at most 0.17 on a 1–5 scale: no condition was better. Observations alone were chosen then; served games now retrieve strategy points only | [Ablation](ablation/report.md) |
| June 2026 | The game was rebuilt (nine seats, three sides, turn-by-turn discussion) and extraction rebuilt per role, so earlier numbers no longer compare. An early pilot with a growing store suggested memory hurt the villagers (−32 points, p = 0.043, unpaired), so a clean test followed | **The June static A/B.** On a frozen store (`v5_0`) and 30 paired boards with plain retrieval, selected town decision measures improved: the healer saved the real target 37% → 60% (p = 0.005); town eliminations hit an enemy 47% → 64% (p = 0.028). Town win rate rose 27% → 43%, not significant (p = 0.27). Wolves and the lone killer gained nothing. The pilot's harm did not reappear | [Effectiveness](effectiveness/report.md) |
| June 2026 | v6: the store rebuilt around structured situation fields (players alive, how close a side is to winning), to test whether finding better-fitting lessons was the lever | Ranking lessons by those fields showed no reliable effect (125 held-out votes), and a field-matching tilt was screened with no benefit and left off. A paired A/B on the v6 store (30 boards, its own baseline) found no town effect (+6 points, p = 0.77); it was not a replication of the June test: a different store, changed prompts, and a no-memory baseline that had risen (town win 27% → 37%). On its decisions, agents followed about 99% of the lessons they judged applicable | [Situation fields](../extraction/situation_dimensions/report.md); [effectiveness](effectiveness/report.md), "Why the v6 A/B found no town effect" |
| June–July 2026 | v7: a loop that plays games in generations, credits each followed lesson by the decisions it led to, rewrites and prunes the store, to ask whether memory improves over time | Two June loop runs were invalid (a biased memory-off baseline; then every side given memory instead of the town only). The July test was pre-registered: after four learning generations, 30 boards played with the final memory and without. The town's decision score was 0.147 lower with memory, worse on 19 of 30 boards (p ≈ 0.06). As committed, it was reported as "no compounding detected" | [v7](v7/report.md) |
| October 2026 | v8: memory rebuilt for the ten-seat game; extraction moved offline; the halo re-read; lessons tagged with their decision; credit ported to the new roles | Checks of the mechanism, not of play: lessons shown that fitted the decision rose from 15% to 24–27% (96 lookups, model readers; a larger store and the stage filter together, readers not the same, so approximate); lessons stating a wrong rule fell from 11% to 6.1%; a demonstration credit pass over 20 memory-on games credited 148 of 498 lessons, pruned 4 and evicted 4, a demonstration of the pass, not estimates. No memory-on vs memory-off run | [v8](v8/report.md) |

**How the campaigns connect.** Each version answered a question the last one left. Retrieval by
situation replaced a document that overfit; the unstable pre-rebuild batches led to the paired,
frozen-store design of June. The June result showed nothing for the lone killer and the wolves, and
reranking gave no measured advantage over plain retrieval, so v6 tried structured fields to find
better-fitting lessons; that showed no benefit either. With lessons followed almost whenever judged
applicable and still no town effect on the v6 store, the project read the limit as the lessons'
content, and v7 built a loop to improve content from results. The July test found no improvement.
Its cause was traced to credit: town abstentions were graded neutral and a lesson without a memory-off
comparison was compared with zero, so a lesson telling the vigilante to abstain scored 0.00 and was
never pruned. The scoring was fixed and checked on recorded games; the fixed loop was never played.
v8 carries the fixed scoring into the ten-seat game. The reading that content was the limit is the
reason v7 was built, not a tested finding: on the v6 A/B's own decisions, seats judged 30–62% of the
lessons shown not relevant, and v8's fit checks still find about three in four lessons shown do not fully fit
the decision. Finding the right lesson remained a limit too.

## What is established, and what is not

**Findings.**

- **The June static-memory A/B reported improvements on selected town decision measures.** The
  healer's saves and the town's eliminations improved; the win rate did not move significantly; wolves
  and the lone killer gained nothing.
- **A later A/B on a different store, run against a higher no-memory baseline, found no town effect;
  it was not a replication of the June test.** One plausible reading is that the no-memory town
  already played at the level June's memory had lifted it to, leaving no room to show; that is not
  established.
- **Separately, the pre-registered v7 endpoint detected no compounding benefit.** The estimate leaned
  toward harm without reaching significance. The owner closed the memory research on 2026-07-21
  without a further run: the investigation is closed, and the hypothesis was not disproved.
- **v8 has not been tested at scale for its effect on play.** Its checks show the stages working
  (fit, rule errors, halo, decision tags, one credit pass); none compares memory on with memory off. A
  test would need about 35–60 games per arm, a size taken from the nine-seat power table.

**How sure we are.**

- **Players that did not reason.** Every game behind the June, v6 and v7 results ran on
  `gemini-3.1-flash-lite` at thinking level "minimal", which produced zero reasoning tokens; the
  run fingerprints confirm the setting. Both arms ran alike, so each comparison is fair, but each is a
  result for players that answer without a reasoning step. v8's seeding games ran at a thinking
  level at which their model reasons, but no v8 game compares memory on with off.
- **Small samples.** Each whole-game test used 30 boards. At that size the win rate can only detect a
  change of about 36 points, which is why the June test leaned on decision measures.
- **The June baseline may have drawn low.** Town measures also improved in the arms where only the
  wolves or the lone killer had memory, and memory-off games on the same seeds the next day played
  near the level the town reached with memory; part of the June gain may reflect the baseline
  ([effectiveness](effectiveness/report.md), "Was the baseline a low draw?").
- **Suspected model drift.** A June memory-off baseline shifted between two runs with identical prompts
  and was discarded, and the one significant June win-rate arm ran later the same day than its
  baseline. Drift on the provider's side is suspected, not established: a paired re-test of the 20
  deals both baselines shared gave p = 0.18.
- **Not checked.** The fixed v7 credit was never played; prune and evict thresholds are unvalidated for
  ten seats; town day lessons reach no one and are checked only by the owner's reading.

## The component reports

The campaigns above test memory as a whole. These reports own the stages it is built from.

| Folder | What it covers | State today |
|---|---|---|
| [`extraction/`](../extraction/) | Writing observations from a finished game ([post-game](../extraction/post_game/report.md)), their quality and the halo ([observation quality](../extraction/observation_quality/report.md)), the situation query ([situation summary](../extraction/situation_summary/report.md)) and its fields ([situation fields](../extraction/situation_dimensions/report.md)) | Live, offline after the game, with the halo re-read on. Tells (behaviour-to-role hints) are research only and not served ([tell extraction](../extraction/tell_extraction/report.md)) |
| [`dedup/`](../dedup/report.md) | Keeping duplicate observations and lessons out of the store | Live: a rule-based gate, then keep or discard. The rewriting merge is built and off |
| [`retrieval/`](../retrieval/report.md) | The read path and the May study of filtering, reranking and wider fetches | The plain read path is live; filtering, reranking, the field tilt and the stage filter are built and off |
| [`store_curation/`](../store_curation/report.md) | How the stores grow, stay bounded and improve | Live as the two passes above; the report describes the nine-seat loop they came from. Tells are not served |
| [`credit/`](../credit/report.md) | Grading a followed lesson by its decision, and the abstention blind spot | Live in the credit pass, with the fixed rule. The model judge for discussion ([discussion tagger](../credit/discussion_tagger/)) was retired on 2026-07-13 |
| [`fine_tuning/`](../fine_tuning/report.md) | Small trained models for dedup and reranking | Trained and evaluated, not wired: no code in the game or the server loads either cross-encoder |
| [`caching/`](../caching/report.md) | Paying less for input repeated across calls, including extraction's shared prefix | Live |

*Rewritten 2026-10-26 from the June–October progression piece "Memory Store Progression", whose text
is kept whole in [experiment_log.md](experiment_log.md). No code, tests or experiments were run for
this revision; statements about today's code were checked by reading it.*
