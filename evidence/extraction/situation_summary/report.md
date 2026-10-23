# The situation query: how a seat describes its game to search its memory

**Scope:** the one model call that, before a seat's decision, writes a description of the seat's current situation so that the memory can be searched for lessons learned in similar situations. It covers what the call writes, when it runs in the ten-seat game, how it is built, how it has been checked, and one case from the nine-seat research of May 2026 where a labelled test overturned a design intuition.
**Revised against the code:** 2026-10-22 at `c0732f88` (the working tree's only edit in `Agents/memory/retrieval/` is a code comment in `pipeline.py`).
**Companion docs:** [the journey log](experiment_log.md) (how the design got here) · [situation dimensions](../situation_dimensions/report.md) (the field schema the query shares with stored lessons) · [the v8 log](../../memory_system/v8/experiment_log.md) (the ten-seat reads of real queries, 2026-10-12 and 2026-10-13) · [credit](../../credit/report.md) (how followed lessons are scored) · [the judge apparatus](../../evaluation/llm_judge/agent_decision.md) (Stage 1: how query quality was measured).

> **Orientation: one seat's memory lookup.**
>
> **a seat's turn → should this turn look up lessons? → the situation call writes 1–2 situations → each is searched against the seat's own shelf of lessons → the best 3 per situation go into the seat's prompt → the seat says, for each, whether it followed it**
>
> A *lesson* (stored as a *strategy point*) is a short piece of advice for one role at one kind of decision, written by a model from finished games. Each lesson is stored with a description of the situation it was learned in. Lessons sit on shelves, one per role and kind of decision (day discussion, day vote, night action). The project calls a shelf a *cell*. The situation call is the front door of this read path: the search can only find what the query describes.

---

## 1. What the call does, and why it exists

Lessons are written offline, after a game ends, by a model that can see the whole record. A seat in a live game sees only its own role's knowledge. For an embedding search to match the two, the live seat has to describe its situation in the same structure and vocabulary the stored lesson used, and from what the seat can actually know.

The situation call does that translation. It reads the same game record the seat's turn prompt reads, plus the seat's private knowledge, and fills a structured form: what is happening, what is known, how much is at stake, where the room stands, how exposed the seat is. The form is the same per-cell schema that offline extraction fills when it stores a lesson. One function joins the filled fields into the text that gets embedded, for queries and lessons alike. So a query and a lesson about the same kind of moment land near each other in embedding space because they are written in the same shape, not because a model remembered a house style.

**Who writes it:** the seat's own game model, in one extra call before the decision. **Who reads it:** the embedding search, and the turn's record (each decision's record keeps the situations it searched with, so a lookup can be replayed and read later).

## 2. What a query looks like

This is a real query, lifted from a memory-on game played on Claude Haiku 5.5 on 2026-10-14 (game `22c1c19e`, seat `player_4`, the Chanteuse, one of the two wolves, at its first discussion turn of day 2). Line breaks are added at each label, and two fields are cut where marked:

> Day 2 opens with ten players alive and no information public beyond a night where a wolf-and-serial-killer attack on one player was saved by the healer. No one has claimed a role, and the village has no vote history to work from. The pack's night-1 kill failed, and the chanteuse's block on another player is unknown to the village.
> **Information landscape:** Information-starved: one saved attack announced, no claims, no checks, no watches, no eliminations.
> **Stakes:** Ten alive with six eliminations needed before the leading evil faction can win; no single vote is decisive now, so early mistakes can be absorbed, but the wolves' numbers are not yet threatened by any one result.
> **Consensus:** The village has no consensus yet; day 1 discussion produced no accusations and no claims.
> **My position:** Holding out, unclaimed, blending in as one of the town players while the room has nothing to argue from.
> **Heat:** Low: no accusations have been made in the discussion and no vote has occurred; suspicion on you is at baseline.
> **Forward exposure:** […] **Target landscape:** […]
> **Public vs private:** Privately you are the chanteuse and your wolf partner (the illusionist or the other wolf) is still unrevealed; you know the pack's night-1 kill on the healer-saved player and your block on another player, but the village has only seen a night where one player was attacked and saved, with no roles revealed. Publicly you are an unclaimed player in a board with no claims yet.

The search's closest lesson on the Chanteuse's day shelf (similarity 0.84) was stored with a situation written in the same labelled form:

> An early day (day 2 or 3) with several role claims on the table, no hard confirmations, and the chanteuse's wolf side unsuspected while the town works through contradictions. **Information landscape:** Starved: unverified claims, partial cross-confirmation, one or two rules inconsistencies, and little else. **Stakes:** Wolves are still several eliminations from parity, …
>
> *Advice:* "When you are a low-heat chanteuse in an info-starved early day and the room is sorting through unverified claims, make one short rules-based or procedural point, such as asking a named visitor to explain or noting what a claimed result would imply under the rules. …"

The seat marked it *follow*: "Early day with no confirmations; a neutral rules point keeps my heat low." The lesson was written for a day with several claims, and this seat's day had none. The match is close on the labelled fields and loose on the events, which is the fit problem described in §5.

Later that day another player claimed to be the Trailseer and named the Chanteuse's partner. The same seat's next discussion turn made a fresh lookup and wrote two situations: one about its partner being implicated, one about whether its night block on a town player would come out. (Source: `batch_results/v8_demo_0/eval_cases/v8_demo_0_all_enabled/22c1c19e-….jsonl`, gitignored.)

## 3. When it runs today

**On the live site, only when a player switches memory on.** Each new game's memory switch starts off. The deployment has its own switch as well (`WW_MEMORY_ENABLED`, off unless the deployment sets it), and a memory-on game is refused while the lesson store is unpublished. With memory off, no seat makes this call.

With memory on, the call runs for one decision and is skipped for others:

| Decision | Situation call? | Why |
|---|---|---|
| Any decision on day 1 | No | Nothing has happened yet that a lesson could match. |
| A town seat's day discussion or day vote | No | Town day lessons are extracted for the project owner to review. Advice the owner approves becomes fixed text in the role prompt instead of being retrieved (ruled 2026-10-11). |
| A town seat's night action | Yes | |
| A wolf's, lone killer's or neutral's discussion, vote or night action | Yes | |
| A human seat's own decision | No | A human decides without the agent pipeline. If the human hands a turn to its agent, the agent looks up as any seat would. |

**One lookup can serve several decisions.** A lookup is the situation call plus its search. In the owner's first ten-seat game, a lookup at every decision came to about 60 a game. The owner ruled on 2026-10-12 that lookups are reused:

- **Day discussion:** a seat looks up once per day, at its first turn, and reuses that lookup for its later turns. A new role claim that day (a new player and role pair) triggers a fresh lookup, as in §2.
- **Votes:** every vote looks up afresh, since it comes after the whole discussion.
- **Night:** one lookup per seat per night. A wolf makes two: one for the pack's chat, one for the kill and its own ability, because the talk moves from candidate targets to a plan.

On that first game this cut about 60 lookups to about 38, plus one per new claim. The reuse is a cache inside the server process; a restart just means a fresh lookup.

**The served game searches strategy points only.** The store also holds *observations* (accounts of a single play and its effect), but the served configuration turns their retrieval off: the town half of the store never had observations, so serving them would give the two sides different memory.

To give a sense of scale (recomputed for this doc from the turn records of the 20 memory-on demo games of 2026-10-14): of 3,118 recorded decisions, 1,496 carried a lookup, fresh or reused; 1,106 were town day decisions and 516 were day-1 decisions, both skipped.

## 4. How the call is built

**Inputs.** The prompt opens with the same system message and public record as the seat's own turn prompt, so the two share a cached prefix. After that come the game state (survivors, the public dead), the seat's private knowledge, its night record, the wolves' chat if it is a wolf, and its own strategy note. The private part states the seat's exact values where its role has them: uses of a limited ability left, a Fortune Teller's points, a Speculator's pick, a Necromancer's usable bodies, the pack's carrier and target.

**Numbers are computed, not estimated.** Some fields are facts the seat can know exactly: players alive, uses left, whether a wolf partner has been revealed, how many eliminations until the leading evil side can win, and whether one more elimination could decide the game. The code computes these from the game state and hands them to the model as "known board facts", so the stakes sentence is written from true numbers. After the reply, it overwrites those fields with the computed values in case the model ignored them. When a dead player's role was concealed, the counts are the worst case for the town and the prompt says so.

**The form.** Each role and kind of decision has its own schema, generated from shared field groups. A night form has no consensus or heat fields, and a role with limited uses gets a "uses left" field. Every role in the twelve-role pool has a form for each decision it makes. The rules in the prompt are the ones the labelled tests in §6 arrived at: describe the board's state and never give advice, write in the seat's own knowledge (never as an all-seeing narrator), and write a second situation only for a genuinely separate decision.

**From form to search.** The filled fields are joined into one labelled text by the same function that composes stored lessons. Each situation is searched against the seat's own shelf: strategy points for its role and kind of decision. A seat can only search its own role's shelf. The search fetches 5 per situation and keeps the best 3, and a lesson found by both situations appears once.

**When the call fails.** A reply that breaks the schema is retried once, with the schema enforced by the provider. If that also fails, the query falls back to a generic line ("Day 2 as chanteuse, round 0"), which still searches the right shelf. A failure degrades that turn's search; it never blocks the decision.

**Which model.** The call uses the game's own model at the game's thinking level: on the live site the model the player chose, and otherwise the house default, Claude Haiku 5.5 since 2026-10-15.

**Built, off by default.** Several retrieval steps after the search are switchable per game and off in the served configuration: a model reranker, duplicate filtering, a score tilt by matching labels, and a *stage filter* that drops lessons learned at a different stage of the game (players alive, partner lost, uses left) and refills from same-stage lessons. The stage filter was on in the October demo run.

## 5. How it has been checked

**Unit tests (76 pass at `c0732f88`).** They pin when a turn looks up (day 1, town day turns and a switched-off role skip; town nights and evil days look up), the reuse rules, the private-state lines each role gets, the dropping of unused labels, the overwrite of computed numbers, and the enforced-schema retry.

**A read of 96 real ten-seat queries (2026-10-12).** Seven memory-on games (four on Claude Haiku 5.5, three on GPT-6 Luna) made 352 lookups. A sample of 96, spread across model, role and phase, was read by four Claude subagents against the rules and the games' true roles.

- **The queries:** 37 of the 96 had at least one error. Eight came from the prompt's own swing line: it said the game could end within one more elimination beside a count of five or six eliminations to go, because it counted the town's possible win without saying so. It was reworded the same day. The rest were the model misreading a rule (a Necromancer believing it is invisible to checks, a "no effect" sigil read as clearing someone) or miscounting. No query stated a concealed role as fact.
- **Replayable:** searching again from the situations the seats wrote reproduced the lessons they had been shown in 91 of the 96 lookups.
- **The search was the weaker link.** Only 39 of 268 lessons shown fit the decision (15%). The readers all saw the same pattern: retrieval matched the role but not the stage of the game. Lessons about a dead partner or the last few players reached seats on day 2 with seven to nine alive, and the similarity score did not track fit. The seats' verdicts on the lessons were sound in 65 of the 96 lookups and mixed in 25, so the cost was mostly prompt room rather than misplays.
- **What helped was a retrieval change.** On a larger store built from 40 games, leaving out lessons from another stage raised fit from 15% to 24–27%. With the gap refilled from same-stage lessons, the lookups with at least one fitting lesson rose from 36 to 52 of the 96 (2026-10-13; different readers from the first read, so the comparison is approximate). The query's part is that it carries exact stage numbers to filter on.

**Why the numbers are computed.** A July 2026 audit of nine-seat queries compared each number the model wrote with the true value from the board. Players alive was exact in 97% of 6,099 cases, but the vigilante's shots left was exact in only 16% of 1,109, systematically too low. A wrong count also leaked into the stakes sentence that gets embedded. That is why the code now states these numbers to the model and then overwrites them.

**Earlier evidence (nine-seat, May 2026).** Two studies shaped the prompt before the ten-seat game existed:

- **A model comparison on 15 frozen cases** kept the cheap model of the time (Gemini 3.1 Flash-Lite). Its lasting finding was a failure mode a generic quality score would miss: a model can be factually accurate and still write from the wrong point of view. In one wolf case the seat *was* `player_6`, and Gemini 2.5 Flash wrote "My wolf ally, player_6, is currently under direct scrutiny". That query would retrieve advice for defending a teammate, not for being under suspicion yourself. The rule to write in the seat's own voice comes from here.
- **A human-labelled ranking test** of 20 cases, built to check whether the queries retrieved the right lessons rather than whether a judge liked them. It is the case study below.

## 6. Case study: the field that felt right and lowered retrieval

**Verdict.** In May 2026 a fifth field, the seat's "core dilemma", was added to the query form because it seemed obviously useful. Tested against human relevance labels, the queries written with it ranked worse on the cases that could be scored fairly. It was removed, and by that round's scores removing it was the largest single gain of the prompt changes. The test also caught its own artifact: an early headline gap was inflated by lessons nobody had labelled.

**The test.** For each of 20 frozen cases across four nine-seat roles, the owner wrote an ideal query from the exact inputs the call saw. The lessons and observations it retrieved from a fixed store (up to 10 of each) were each labelled 2 (highly relevant), 1 (partly) or 0 (not relevant): 340 labels in all. Each query was then scored by how well its search ranked the labelled items.

> **The score (NDCG@k).** A ranking score from 0 to 1 over the top *k* results. It is 1 when the search orders the results the way the labels would (most relevant first), and lower when relevant items sit below less relevant ones. An item the labels never covered counts as 0.

The hand-written queries scored 0.83 over the top 10. Retrieval was already reasonable when the query was good, so the question became how far the pipeline's own queries fell short.

**What happened.** While labelling, the four existing fields (information landscape, consensus, the seat's exposure, game phase) seemed to describe the board but not the choice. Two seats on similar boards can face different decisions: whether to follow a vote, or how to share a private result without exposing the role. So a fifth field, the core dilemma, was added in one sentence.

The queries regenerated with it looked better on average, but that average was not trustworthy. A new query retrieves some lessons the labels never covered, and each of those scores 0 whatever its real relevance. On the six cases where few results were unlabelled, so the score could be trusted, the new form scored lower: 0.79 against 0.87 for the queries it replaced (top 5). The reading at the time was that the dilemma field pushed the model toward abstract framing and away from the concrete events the stored lessons describe.

**The fix.** Three changes followed, each scored on the same labels: write the query in the store's own labelled fields rather than free prose; remove the core dilemma; and tell the investigator to lead with how its private findings relate to the public story. The 108 results that the final queries retrieved but nobody had labelled were then labelled too, by a model (Claude Opus 4.6), so every result had a label. On that full set the final form scored 0.06 above the pipeline's original queries over the top 5 (0.76 against 0.70), and the investigator, which had looked worse, turned out to have improved.

**What it shows.** A design that is plausible on reflection can lower retrieval, and a judge rating queries for quality would not have caught it; a labelled ranking did. The same labels exposed how an unlabelled item scored as zero can make a change look better or worse than it is.

**Limits.**
- 20 cases and six fairly scorable ones. They show the direction of each change, not its size.
- The first comparison changed more than the one field: the regenerated queries were also capped at two and written with the model's thinking on. The field's own effect was isolated only in the later step that removed it.
- The 108 extra labels came from a model and were never checked by a person.
- The labels belong to a nine-seat store of May 2026 and the prompts of that time. The ten-seat query keeps the conclusions (labelled fields, no dilemma field, own point of view), but the score has never been re-run on the ten-seat game; the scorer still points at the old store.
- The score cannot tell a weak query from a thin shelf. The largest per-role gain, for the villager, came mostly from the store lacking good villager voting lessons, not from the query.

## 7. What is not established

- **That the query, or memory as a whole, improves play.** No such result exists for the ten-seat memory, which has not been tested at scale. Memory is off unless a player switches it on.
- **How good the ten-seat queries are, beyond the one read.** The 96-query read is the only check on ten-seat queries. The labelled ranking test has not been rebuilt for the ten-seat store, and the model judges used in May grade query content with no ground truth.
- **Whether reusing a lookup within a day costs fit.** The reuse rule was ruled on cost and on the shape of a day's talk; whether a reused set fits later turns as well as a fresh one has not been measured.
- **What the call costs now.** In the seven gate games, lookups were 20–28% of a game's model cost on GPT-6 Luna and about 40% on Haiku. Two fixes followed (the situation prompt laid out for the prompt cache, and cache accounting), and the share has not been re-measured since.
- **The query is outside the automatic leak checks.** Its prompt is built from the same game data the seat's turn receives, which is limited to what the seat's role may know. But the call does not log its prompt where the leak checks look, so the checks cannot confirm it (see [agent boundaries](../../agent_boundaries/report.md) §5).

## Sources and implementation

| What | Where |
|---|---|
| The situation call: inputs, computed facts, overwrite, retry, fallback | `Agents/memory/retrieval/situation_agent.py` |
| When a turn looks up (day 1, town day, role switch, store) | `Agents/memory/retrieval/plan_gating.py` |
| Lookup reuse within a day and a night | `Agents/memory/retrieval/lookup_cache.py` |
| The read path: search, caps, optional filters, the turn record | `Agents/memory/retrieval/pipeline.py`, `accessors.py` |
| The query prompt | `Agents/prompts/memory/situation_summary.py` (`V6_SITUATION_SUMMARY`); shared guidance `compose_cell_guidance` in `Agents/prompts/prompt_inputs.py` |
| The per-cell forms and the shared composer | `Agents/schemas/memory.py` (`cell_situation_schema_for`, `compose_situation_embed`, the ten-seat cell table) |
| The served configuration (strategy points only; memory switch) | `server/game/run_config.py`; `server/config.py` (`WW_MEMORY_ENABLED`); `server/routes/_shared.py` |
| Tests | `tests/memory/test_memory_plan_gating.py`, `test_lookup_reuse.py`, `test_situation_query_inputs.py`, `test_situation_dim_override.py`, `test_stage_filter.py`; `tests/engine/test_enforced_retry.py` |
| The §2 example | `batch_results/v8_demo_0/eval_cases/` (game `22c1c19e`; fingerprint `c38d9ef2`, dirty tree), gitignored |
| The reuse ruling, the outside review of the query | [v8 decisions](../../memory_system/v8/decisions.md) §10 |
| The 96-query read and the stage-filter replays | [v8 log](../../memory_system/v8/experiment_log.md), 2026-10-12 and 2026-10-13; runners `evaluation/experiments/v8_gate_lookups.py`, `v8_stage_filter_replay.py` |
| The number audit (July 2026) | [`../situation_dimensions/dimension_accuracy_audit/`](../situation_dimensions/dimension_accuracy_audit/experiment_log.md) |
| Model comparison (2026-05-24) | `model_comparison/` (outputs, pairwise and rubric judge results); runner archived at `evaluation/src/archive/situation_summary_model_comparison.py`; judges in `evaluation/src/judges/situation_summary*.py` |
| The labelled ranking test (2026-05-27) | `outputs/retrieval_golden_labels.json` (also read by reranker training; do not move), `staging/case_*.json`, `outputs/regenerated_situations_*.json`, `prompt_versions/`; scorer `evaluation/src/labeling/label_scorer/situation_retrieval_ndcg.py` (pinned to `memory_stores/v4_deduped_v2`); labeller `evaluation/src/labeling/manual_labelers/situation_retrieval_labeler.py` |
