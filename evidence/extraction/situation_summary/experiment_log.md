# The situation query — journey log (May to October 2026)

> **What this is.** The dated path from "is the cheap model good enough to write memory queries?" to
> today's ten-seat query: one call per lookup, in the same form as the stored lessons, with exact
> numbers computed from the game, reused within a day, and skipped where memory is not served. Later
> entries supersede earlier ones; a design that was later dropped is shown where it happened.
>
> **Companion docs.** The current design, stated destination-first: [`report.md`](report.md).
> This log condenses the folder's `experiment_log.md` (its curated arc and the two original records in
> its Appendices A and B) and `report.md`, both in git history at `2382b34c`, plus the ten-seat entries
> of [`../../memory_system/v8/`](../../memory_system/v8/experiment_log.md) that concern the query. Terms
> (lesson, observation, cell or shelf, lookup, the ranking score) are defined in the report's
> orientation and §6.

---

## ① Motivation: the front door of memory had never been checked

**May 2026, the starting point.** In the nine-seat game, every agent decision with memory on began
with one call that turned the game state into 1–3 search queries. The search then fetched stored
memories by embedding similarity. The design was reasonable: one cheap call, free-text queries, and a
shared block of prose ("situation standards") placed in both the extraction prompt and the query
prompt so the two would describe situations alike.

Two things were unknown. Was the cheap production model (Gemini 3.1 Flash-Lite, no thinking) leaving
quality on the table? And did the queries retrieve the *right* memories at all? Every earlier check
had been an AI judge scoring retrieval with no human reference. The root issue: the query bounds what
retrieval can find, and nothing measured it against ground truth.

## ② The first question: is the cheap model good enough? (2026-05-24)

*Catches:* the risk that the per-turn query was weak because the model was too small.

Four set-ups were compared on 15 frozen cases: Flash-Lite with no thinking (production), Flash-Lite
with medium thinking, Gemini 2.5 Flash and Gemini 3.5 Flash. Two judges (Gemini 3.1 Pro) graded
them: a pairwise judge picking the better of two queries, and a rubric judge scoring each query 1–5 on
faithfulness, specificity, usefulness for retrieval, non-redundancy and role perspective.

- 3.5 Flash won 14 of 15 pairwise comparisons, yet its rubric average tied Flash-Lite's (3.92 each).
  Side by side, the judge saw a small consistent edge that separate scoring missed.
- Thinking hurt Flash-Lite: medium thinking averaged 3.59 against 3.92 without.
- 2.5 Flash was the most faithful (4.93) but scored 2.73 on role perspective. In one wolf case the
  seat *was* `player_6`, and it wrote "My wolf ally, player_6, is currently under direct scrutiny".
  A query from the wrong point of view retrieves the wrong advice even when every fact in it is true.

*Decision:* keep Flash-Lite. The gain was modest for six times the price and about three times the
latency (2.6 s to 7.0 s a case) on a call made every turn. The lasting result was the role-perspective
failure. All of it rested on an ungrounded judge, which set up the next step.

## ③ A human-labelled ranking test, and what it overturned (2026-05-27)

**Design.** For each case, write the ideal query by hand from the exact inputs the call saw, run it
against a frozen store, and label every retrieved item 2 (highly relevant), 1 (partly) or 0 (not). The
graded labels allow a ranking score (NDCG, defined in the report §6). Searching from a hand-written
query was preferred over labelling the whole store, because a relevant stored item should appear in
the top results of a good query. Labelling rule, set while labelling: grade the match of situations,
not whether the advice would transfer.

**Baseline.** 20 cases across four roles and both day phases, 340 labels. The hand-written queries
scored 0.83 over the top 10. Retrieval was reasonable given a good query; the headroom was in the top
three, and in strategy points, which are written more generically than observations.

**Structured beats prose (one case).** *Catches:* whether a query in the store's own labelled fields
matches stored entries better than natural prose. On one healer case both forms retrieved the same
items in the same order, but every similarity was higher for the structured form (by 0.003 to 0.046).
*Decision:* write the hand queries in the labelled form, and test the same for the production prompt.

**Two changes made during labelling.**
- *At most two queries.* The pipeline never produced three useful ones and often filled the second
  slot with another angle on the first. The prompt went from 1–3 to 1–2, with a second query only for
  a genuinely separate decision.
- *A fifth field, the "core dilemma".* The four fields described the board but not the choice, and two
  seats on similar boards can face different decisions. A one-sentence dilemma field was added to the
  shared standards.

**The pipeline against the hand-written queries.** *Catches:* how far production queries fall short.
The hand-written queries led by 0.11 over the top 5 (0.78 against 0.67). But each query retrieved
items the labels never covered, scored 0 by default, and the largest gaps were in the cases with the
most unlabelled items. The true gap was smaller.

**The dilemma field, falsified.** *Catches:* whether the new form improved retrieval. Regenerated with
Flash-Lite (dilemma field, two-query cap, medium thinking), the overall score rose by 0.03, but on the
six cases with few unlabelled items it fell: 0.79 against 0.87. The healer regressed most. The reading
at the time: the field pulled the model toward abstract framing and away from concrete events.

**Iterating on the labels.** Each version was scored the same way.
- v3: the query became a structured object with the store's fields, joined into the store's labelled
  format.
- v4: the dilemma field removed from the shared standards. By the round's scores, this was the largest
  single gain.
- v4b: the investigator told to lead with how its private findings relate to the public story, which
  recovered its regression.
- Gemini 2.5 Pro was no better than Flash-Lite on most versions; the prompt's form mattered more than
  the model. Flash-Lite also failed to produce structured output with optional fields, so every field
  became required.

**Union labelling.** *Catches:* the unlabelled-item bias. The 108 results v4b retrieved that nobody had
labelled were labelled by Claude Opus 4.6. On the full set, v4b beat the original production queries
by 0.06 over the top 5 (0.76 against 0.70). The investigator flipped from a small loss to a small
gain, and the wolf's apparent gain shrank. The villager gained most, but mostly because the store
lacked good villager voting lessons, which the ranking score cannot separate from query quality.

*Decision:* ship v4b (structured, no dilemma field, investigator lens first). Keep the labelled set as
the one ground-truth anchor for the query. Its limits were known: 20 cases, model-made extra labels
never checked by a person, and tied to that store and those prompts.

## ④ The query takes the store's own form (mid-June 2026)

**Problem.** The memory was rebuilt around structured *situation dimensions*: each stored observation
filled a per-role, per-phase form (situation, information landscape, stakes, consensus, heat,
exposure, and numbers such as players alive). A query written to the old shared prose would no longer
match the new stored entries' structure.

**Design.** The live query fills the *same* per-cell form as extraction, and one function joins the
filled fields into embedding text for both. A single prompt builder supplies the field list and
guidance to both prompts. Alignment is then a property of shared code, not of two prompts that must be
kept in step. A fallback to the old per-role prompt remained for any role without a form.

*Decision:* the owner adopted the rebuilt memory on the quality of its extracted entries (2026-06-15).
A replay screen pointing the same way measured memory against no memory in a single run near its noise
floor, so it is not cited as evidence for the query.

## ⑤ Numbers computed, labels dropped (July 2026)

**Problem.** The form asks for numbers the seat can know exactly. A $0 audit compared the numbers the
model wrote in nine-seat queries with the true board: players alive was exact in 97% of 6,099 cases,
but the vigilante's shots left only in 16% of 1,109, systematically too low. A wrong count also shaped
the stakes sentence that gets embedded.

**Fix.** Players alive, shots or uses left and "partner revealed" are computed from the seat's own
game data and overwrite the model's values. On 2026-07-11 the owner pointed out that the cast is public
and every death reveals the role, so eliminations-to-parity and the swing flag can be computed from
public counts too; they joined the computed set. The computed values are also stated in the prompt, so
the stakes sentence is written from them.

**A dropped consumer.** Four coarse labels in the query fed a retrieval step that tilted scores by
matching labels. Screened on a replay of 24 decisions, it came back flat, so it stayed off. The labels
remained in the query until 2026-10-12 (§⑦).

**2026-07-21.** The owner closed the nine-seat memory research. The live game ran with memory off.

## ⑥ The ten-seat game (2026-10-11)

The game moved to ten seats dealt from twelve roles. Each new role's form reuses the field groups of
the old role it plays like, with a "uses left" group for limited abilities. So every role has a form
for every decision it makes, and the old fallback prompt is no longer reached by any role in the pool.

**Ruled the same day:** town day lessons are extracted for the owner to review and never retrieved in
play; advice the owner approves becomes fixed prompt text. So a town seat's day discussion and vote
make no lookup.

## ⑦ Ten-seat lookups: how often, and how good (2026-10-12)

**How often.** *Problem:* with a lookup at every decision, the owner's first ten-seat game made about
60, 27 of them on evil or neutral discussion turns at 2 to 5 turns per seat a day. *Ruling:* one lookup
per seat per day of discussion, refreshed by a new role claim; a fresh lookup for every vote; one per
seat per night. About 60 became about 38, plus one per new claim.

**An outside review of the query** led, the same day, to three prompt changes and one amendment:
- the query now states the rules, the public dead and the seat's exact private state (uses left, a
  Fortune Teller's points, a Speculator's pick, a Necromancer's bodies, the pack's carrier and target);
- after a concealed death, the parity count is stated as the worst case for the town, not as exact;
- the four labels used only by the switched-off score tilt are no longer asked for;
- *amendment:* a wolf's night makes two lookups, one for the pack's chat and one for its kill and
  ability, because the talk moves from candidate targets to a plan.

The situation prompt was also laid out to share the seat prompt's cached prefix.

**The read of 96 lookups.** *Catches:* whether ten-seat queries describe the board correctly, and
whether the lessons they retrieve fit. Seven memory-on games (four on Claude Haiku 5.5, three on GPT-6
Luna, strategy points only) made 352 lookups; 96 sampled across model, role and phase were read by four
Claude subagents against the rules and true roles.

- Queries: 37 of 96 had at least one error. Eight came from the prompt's own swing line, which said
  one more elimination could end the game beside a count of five or six: it counted the town's
  possible win without saying so. Reworded the same day. The rest were the model misreading rules or
  miscounting. No query stated a concealed role as fact.
- Lessons: 15% fit the decision. Retrieval matched the role but not the stage of the game, and the
  similarity score did not track fit.
- Cost: lookups were 20–28% of a game's model cost on Luna and about 40% on Haiku, measured before the
  caching layout and a cache-accounting fix landed. Not re-measured since.

*Decision:* the query was not the binding constraint; the store's stage mix was. A stage filter was
built on the numbers the query already carries (players alive, partner lost, uses left). On a 40-game
store (2026-10-13), filtering by stage raised fit to 24–27%, and with the gap refilled from same-stage
lessons, the lookups with a fitting lesson rose from 36 to 52 of 96. The filter is off by default.

## ⑧ Into the served game (2026-10-14)

**The demo run.** Twenty memory-on games on Claude Haiku 5.5 (strategy points, stage filter on). One
lookup fell back to the generic "Day N as role" query after a reply broke the schema. *Fix, deployed
the same day:* a broken reply is retried with the schema enforced by the provider, in the lookup as in
seat turns.

**Served configuration.** The site's lessons now come from a database store. A served game retrieves
strategy points only, since the town half of the store never had observations. Memory is a per-game
switch that starts off, and a memory-on game is refused while the store is unpublished.

**2026-10-15.** With the Gemini credits spent, Claude Haiku 5.5 became the house default model. The
situation call has always used the game's model, so it now runs on Haiku by default, or on the model a
player chooses.

## ⑨ Remaining questions

- The labelled ranking test belongs to the nine-seat store of May 2026; its scorer still points there.
  Rebuilding it for the ten-seat store was proposed as a free first step and has not been done.
- No ground truth exists for query *content*; the May judges were never anchored.
- Whether reusing a lookup within a day loses fit on later turns has not been measured.
- The query is not captured where the leak checks look (`../../agent_boundaries/report.md` §5).
- No result shows that the ten-seat memory, or this query, improves play; it has not been tested at
  scale.

---

**Sources.** `experiment_log.md` §0–§5 and Appendices A (2026-05-24) and B (2026-05-27) ·
`report.md` (2026-07-02 snapshot) · `model_comparison/` · `outputs/retrieval_golden_labels.json`,
`outputs/regenerated_situations_*.json`, `prompt_versions/` ·
`../situation_dimensions/` (the v6 schema, the July number audit) ·
`../../v7_final/experiment_log.md` (the flat score-tilt screen) ·
`../../memory_system/v8/decisions.md` §10 and `experiment_log.md` (2026-10-12 to 2026-10-14) ·
code: `Agents/memory/retrieval/` (`situation_agent.py`, `plan_gating.py`, `lookup_cache.py`).
