# Situation dimensions: how a lesson and a memory query describe the board

**Scope:** the structured fields that describe the game situation on every stored lesson and on every
memory query: what they are, who fills them, what reads them today, how far their values can be
trusted, and the attempt to use them to choose lessons, which found no benefit and stays off. The
design and its tests were built on the nine-seat game in June and July 2026; the ten-seat game reuses
the same fields.
**Revised against the code:** 2026-10-22 at `c0732f88` (working tree; the files cited here carry no
uncommitted edits that touch the fields).
**Companion docs:** the journey in date order, [`experiment_log.md`](experiment_log.md) ·
the ten-seat memory record, [`../../memory_system/v8/experiment_log.md`](../../memory_system/v8/experiment_log.md)
(the stage filter and the read of served lessons) · [`../../credit/report.md`](../../credit/report.md)
(how lessons are scored) · [`../../agent_boundaries/report.md`](../../agent_boundaries/report.md)
(why memory is keyed by role). The earlier report and log are in git history at `2382b34c`; the build spec, `v6_full_store.md` and the two sub-folder logs stay in this folder.

> **Orientation: where the fields sit.**
>
> **a finished game → offline extraction writes lessons, each with its situation in fields → the
> text fields are joined into one labelled string and embedded → at a decision, the seat's model
> writes its own situation in the same fields → that string is embedded and the nearest lessons are
> shown to the seat**
>
> The agents keep a memory of short lessons from past games. An *observation* is an account of one
> play and its effect, written by a model after a game. A *strategy point* (here simply a *lesson*) is
> a piece of advice for one role, distilled from several observations. Both carry a *situation*: a
> description of the board at the moment the lesson applies. The *situation dimensions* are the
> separate fields that situation is written in. Everything below hangs on this path.

---

## 1. What the fields are for

Two writers describe situations, and they never meet. After a game, an extraction model reads the
whole finished game and writes lessons, each filed under the situation it applies to. During a later
game, a seat about to decide writes a description of its own situation as a search query. The query
and every stored situation are turned into vectors by an embedding model, and the lessons whose
vectors sit closest to the query's (by cosine similarity) are shown to the seat.

That match only works if both writers describe a board the same way. A free paragraph lets each
writer choose its own words, order and emphasis, and lets either one silently leave something out. So
both writers fill the same fields, and the same code joins the text fields into one string in the
same order with the same labels. The query and the lessons it should find then share their wording
and structure by construction, not because two prompts agree to follow a style.

Three rules govern every field:

- **The agent's own knowledge level.** A stored situation that named the hidden wolves could never be
  matched by a seat that cannot see them. So both sides write only what a player in that seat could
  know.
- **State, never advice.** A field says what is true on the board. The advice lives in the lesson's
  separate `action` field and is never matched against. If advice sat in a matching field, every
  query would land near the same general counsel whatever the board.
- **Numbers stay out of the searched text.** An embedding blurs exact numbers and near-opposites
  ("the room agrees with me" against "the room opposes me"). So counts, yes/no flags and short
  category labels are stored as separate fields and are never embedded. Their meaning is written into
  the prose instead, as board reality: "one elimination from a wolf win", not "is_swing: true".

## 2. What one looks like

Both examples come from the Sentinel, a town role that watches one player's door at night, a limited
number of times, and learns who visited.

**A stored lesson.** This is a Sentinel's night lesson from the ten-seat store `ten_seat_v2` (built
2026-10-13 from 40 games). The embedded string is the lesson's situation, as the code
composed it from the text fields:

> "Mid-game, night 3 or later. One or more evil killers (wolf pack plus a serial killer or
> necromancer) are still active, and town's key information asset is the obvious kill target. The
> Sentinel has to decide where to spend its last watch, or whether to keep it. **Information
> landscape:** Moderate to rich. Some roles are confirmed by flips or reveals and an earlier
> investigator result is known. … **Stakes:** Town can still afford to lose a role, but each lost
> information role makes the wolf and lone-killer hunt harder. This is the Sentinel's last watch, so
> a wasted one leaves town with no door-watching for the rest of the game. **Target landscape:** The
> most validated or claimed information-role player (investigator or trailseer, already attacked or
> clearly threatening to wolves), versus an unconfirmed claimant (e.g. sigilist), a soft-cleared quiet
> player, and a roleblocked healer. …"

Stored beside it, and never embedded: 7 players alive, 3 eliminations from the nearest evil win, not
a swing, 1 use left, `info_rich`, `safe`. The advice is a separate field: *"With your last watch at
night 3 or later, put it on the living player the killers are most likely to attack, usually the
validated investigator or trailseer-type information source. …"*

**A live query.** A Sentinel on night 2 of a ten-seat game played by Claude Haiku 5.5 (game
`20497d9e`, 2026-10-12) wrote this situation:

> "As a surviving Sentinel with one watch left and a private night-1 result of no visitors on the
> player watched, the village is discussing whether anyone holds a night result and is asking for
> visitor reports, while the day-2 vote abstained and no one was eliminated. … **Stakes:** Eight
> alive with four eliminations until the leading evil faction can win, so the game cannot end within
> one more elimination; a single watch spent on a weak lead costs the only remaining door-watch the
> Sentinel has … **Target landscape:** Eight players alive with no public role claims and no public
> night results; …"

Its numbers (8 alive, 4 eliminations to the nearest evil win, no swing, 1 watch left) were not
estimated by the model. They were computed from the game state and handed to it (§4).

## 3. The fields

### How they were chosen

In June 2026 the fields were rebuilt by walking through every role and phase with one question: what about the board changes the right decision here? An earlier replay had shown why the old fields fell short. A lesson written for the final three players was planted into 20 mid-game town votes, and the seat rejected it 13 times, on the numbers: "we are still at 5 players, not final-three." The seat reasons on exact counts, but the only field that carried the stage of the game was a three-way label (early, mid, late).

Two rules decided each field's form:

- **What an embedding can carry.** Free text is embedded, so a near miss still matches. Numbers, yes/no flags and opposites ("the room agrees with my read" against "opposes it") are stored as separate fields, because an embedding blurs them.
- **State, never advice.** A field says what is true on the board; how to act is the lesson's own text.

The walkthrough kept the original four fields as the spine and reshaped them:

| Before | After |
|---|---|
| Game phase (early, mid, late) | The stakes numbers: players alive, distance to the nearest evil win, whether today is a swing day; plus a sentence saying what they mean |
| Consensus | The room's alignment, the seat's own position, and a direction label |
| Exposure | Heat now, and the cost of a visible move |
| (inside the situation text) | Two fields of their own: the possible targets, and the gap between what the seat knows privately and what is public |
| (none) | Counters for the vigilante's bullets and whether a wolf's partner was revealed |

Two decisions were reversed during the same walkthrough. *Numbers fully out of the embedding* became *numbers out, their meaning in*: a lesson from the wrong stage is often the opposite lesson, and the similarity search cannot read a separate number, so the stakes sentence says "one death from a wolf win, every vote decisive", not "endgame". And *compute the numbers from game state* became *the extraction model writes them on the stored side*, because a lesson drawn from a whole game has no single board to compute from. The query side does have one board, which later let code take its numbers over (§5). The full derivation, field by field, is in [`dimension_schema_build_spec.md`](dimension_schema_build_spec.md).

### The fields today

Each role has one set of fields for the day and one for the night; the project calls each set a
*cell*. Discussion and vote share the day cell, because finding the target in discussion is the same
problem as choosing it in the vote. Night cells drop the fields about the room, which is a day
phenomenon. The ten-seat game deals ten seats from twelve roles, each with a day and a night cell, so
it has 24 cells. Its cells are
generated from one table that names each role's field groups, and the same table produces the
lesson, the observation and the query form of a cell, so the three cannot disagree. Each new role
borrows the groups of the older role it plays like: the Sentinel those of the investigator, the
Chanteuse and Illusionist those of the old wolf, the Necromancer those of the serial killer. The
eleven nine-seat cells are kept so old stores still load.

| Group | Field | What it says | Embedded? | On the query side |
|---|---|---|---|---|
| Core (every cell) | `situation` | the decision the seat faces and who is involved | yes | written by the model |
| | `information_landscape` | what is known, claimed and unknown | yes | model |
| | `info_landscape_class` | `info_rich` or `info_starved` | no | no longer asked (§6) |
| Stakes (every cell) | `players_alive` | living players | no | computed |
| | `distance_to_parity` | eliminations until the nearest evil side can win | no | computed |
| | `is_swing` | whether one elimination could end the game, for any side | no | computed |
| | `criticality_stakes` | what those numbers mean for this decision | yes | model, from the computed numbers |
| The room (day cells) | `consensus_text`, `my_position` | how the room is aligned, and where the seat stands | yes | model |
| | `consensus_direction` | the room agrees with, opposes, or has no direction relative to the seat's read | no | no longer asked |
| Exposure | `heat_now` (day) | suspicion on the seat now | yes | model |
| | `forward_exposure` (most cells) | what a visible move would commit the seat to | yes | model |
| | `exposure_class` | `safe` or `exposed` | no | no longer asked |
| Targets and private information | `target_landscape` | the candidates and the basis for each | yes | model |
| | `public_private_text`, `divergence_sign` (day cells, except the two neutral roles) | the gap between what the seat privately knows and the public read | text yes, sign no | text by the model; sign no longer asked |
| Role counters | `uses_left`, `bullets_left` | uses of a limited ability left, before acting | no | computed |
| | `ally_revealed` (wolves' day cell) | a pack partner has been revealed or killed | no | computed |

The *stakes* numbers come from three countdowns, one for the town, one for the two wolves and one for
the *lone killer* (the Serial Killer or the Necromancer, who wins alone). Each counts the eliminations
until that side's win condition is met. They need only how many players of each side are alive, never who they
are, and those counts are public: the cast is fixed and announced, and every death reveals the dead
player's role. The one exception is the Illusionist's power to conceal a body's role. After a
concealed death, the numbers are the worst case for the town over every side the body could have
come from, and the query prompt says so.

> **The stakes arithmetic** (`Agents/rules/board_clocks.py`), from live counts of town (the neutral
> roles included), wolves and the lone killer:
>
> ```text
> wolf clock        = (town + lone killer) − wolves
> lone-killer clock = (town + wolves) − 1        (only while the lone killer lives)
> town clock        = wolves + lone killer
> distance_to_parity = the smaller evil clock
> is_swing           = any clock ≤ 1
> ```

## 4. How a query is built, and what reads the fields today

**The query (live whenever memory is on).** At a decision, the seat's own game model is asked for one
or two situations in its cell's fields. Before it writes, the code computes every field it can from
the game state (players alive, uses left, partner revealed, distance to parity, swing) and puts them in
the prompt as known board facts, so the model writes the stakes prose from true numbers. After it
writes, the code overwrites those fields with the same computed values, so a model that ignored the
facts cannot change them. Both steps read one function, so the number the model is told and the
number it is overwritten with cannot differ. The text fields are then joined into the search string.
If the call fails, the turn goes on with a bare fallback string; memory never blocks a decision.

**What reads the fields:**

| Reader | Fields it uses | Status |
|---|---|---|
| The similarity search (query and stored lesson) | the embedded text fields, as one string | live when memory is on |
| The offline duplicate check while building a store | swing, the alive bucket (8 or more alive, 5 to 7, or 4 or fewer) and room direction split the store into groups; two entries that differ on verdict, information class or exposure class are never merged | offline, runs when a store is built |
| Lesson synthesis | the same groups, also split by partner lost and by uses left (some or none) | offline |
| The replay page on the website | a lesson's fields, shown as a case file | live |
| The stage filter: drops a lesson whose alive bucket, partner-lost flag or uses-left (some or none) differs from the seat's | three stage facts | built, off by default (`RunConfig.stage_filter`) |
| Dimension gating: a soft score tilt by how well a lesson's fields match the query's | alive bucket, swing, and the two class labels | built, off by default; screened with no benefit (§6) |

Two things nothing reads. The memory reranker, an optional model call that re-orders the found
lessons (off by default), sees only the embedded string, not the separate numbers. The design had
planned a small trained reranking model that would read the numbers directly; it was never built.

**Memory in the served game.** On the website, memory is a per-game choice that starts off (the
production deployment allows it through `WW_MEMORY_ENABLED`); when a player turns it on, every AI seat retrieves lessons (strategy points
only) from the published store. The observations remain the raw material that lessons are written from.

## 5. How far the fields can be trusted

Three separate questions: does the same board always become the same text, are the values the models write correct, and do the fields help pick better lessons?

### Does the same board always become the same text?

Yes, and tests pin it. The query side and the stored side join the same values into the identical string; no number or category label reaches the text that is embedded; the facts computed for the prompt equal the values written back; and a count after a concealed death is stated as a worst case. The 127 tests in the nine files covering the fields pass at `c0732f88`. They cover the nine-seat cells; a check run for this revision, at no cost, confirmed the same for all 36 ten-seat role and phase pairs.

### Are the values correct?

**On the query side, the model was right about what it was told and wrong about what it had to work out.** In July 2026, before code took over the numbers, an audit compared what the seat's model had written in 20,284 query situations (6,275 decisions, three nine-seat runs) against the true values, worked out by code from each decision's board. No AI judge was involved. A rule was fixed in advance: if any field used to choose lessons scored under 80%, the gating result in §6 would count as unproven.

| Field | How often the model had it right | Cases |
|---|---|---|
| Players alive (it was given the roster) | 97% exact; 99% in the right early, middle or late bucket | 6,099 |
| Whether a wolf's partner had been revealed | 97.5% | 439 |
| The vigilante's bullets left | 16.4%, and 0% on day 2 (it said 1 where 2 were left) | 1,109 |
| Swing day, written by wolves who know the wolf count | 60.6%, worse than always answering "no" (82.7%) | 439 |
| Distance to parity, as a number | 5–9% exact | |

The rule fired. The fix was to stop asking the model for anything code can compute: players alive, bullets and partner status from 2026-07-02, and distance to parity and swing from 2026-07-11, once it was noticed that the count of the living is public. These now come from code on every query. (The cases are decisions, not independent games, so the percentages carry less certainty than their counts suggest. The audit's true values counted only the wolves' path to a win; the computed values were widened to all three sides on 2026-07-11.)

**On the stored side, one field has been checked.** Stored lessons are still filled by the extraction model, because a lesson drawn from a whole game has no single board to compute from. In October 2026, the uses-left field on the ten-seat store was checked against the record: 165 of 196 exact (84%). Most errors (29) gave the count after the night's action instead of before; 2 were impossible. For the question the stage filter asks, "any left or none", 7 of 196 were wrong, nearly all a last use written as 0. The field's description now says "before acting". The other stored fields have only had consistency checks.

### Do the fields help pick better lessons?

Three uses were tested on replayed decisions. A *replay* freezes a real decision and asks the seat again under each arm; for town votes, a vote is scored +1 for a wolf or the lone killer, −1 for a town player, 0 for an abstain. Re-ranking by matching fields (gating) is the case study in §6.

- **Ranking by the stakes numbers (June 2026): no reliable effect.** The first run looked like a clear win near the end of the game (+0.25 over similarity alone, 16 votes). It was contaminated: 20 of its 30 games were the games the lessons came from, so a seat could see a lesson that already knew its own game's outcome. With those removed, the gain fell to +0.087 (23 votes), and on 125 held-out votes from three town roles the stakes ranking scored 0.032 *below* similarity alone. The same villager inputs run twice gave +0.061 and then −0.037, so any effect is smaller than the noise between identical runs of a replay at temperature 1.0. The numbers stayed in the store; ranking by them was never wired into play.
- **The new query against the old (June 2026): not established.** With old-style queries, lessons beat no memory by +0.088; with queries in the new fields, by +0.120 (125 votes each). The two runs were separate, and the 0.032 gap is smaller than the 0.1 swing between identical runs. Earlier records presented this as the rewrite's main retrieval gain; it is not shown.
- **Dropping lessons from another stage (October 2026, ten-seat): fit improved, offline.** Four Claude Sonnet readers judged whether lessons shown in seven memory-on games fitted the decision, with the true roles in hand. With similarity alone, on the 12-game store, 15% fitted (96 lookups). Dropping lessons written for another stage of the game (a different alive bucket, a lost partner, no uses left) raised that to 25%, but left 25 lookups with nothing to show. On the larger 40-game store, refilling from same-stage lessons, 52 of 96 lookups got at least one fitting lesson against 41 without the filter; the readers differed from the first read, so this is approximate. The filter is built and off by default. It was on in the 20 memory-on games of the credit demonstration (2026-10-14), which measured neither fit nor play.

## 6. Case study: using the fields to choose lessons found no benefit

**Verdict.** A soft re-ranking of found lessons by how well their fields matched the seat's did not
make the lessons fit better, and it was left off. A later audit showed the test could not have been
decisive, because one of its four keys was filled worse than a constant. It was not re-run, and two of
its keys are no longer written by the query. The status is "no benefit measured", not "proven useless".

**What was tried (June 2026, nine-seat).** An earlier replay had found that 58% of the lessons agents
were shown were ones they judged not relevant, and that the similarity score could not tell them
apart: on average 0.827 for not-relevant lessons and 0.828 for relevant ones. Matching on players
alive or on swing cut the not-relevant share by 5 and 6 points; matching on distance to parity cut it
by 2, which was read as no difference. That suggested the fields carried information the embedding lacked. So dimension gating was built: each
found lesson's score is multiplied by a factor between 0.7 and 1.3, by how many of four fields agree
with the query (the alive bucket, swing, and the two class labels for information and exposure). It
never drops a lesson, only re-orders.

> **The tilt** (`Agents/memory/retrieval/dimension_gating.py`):
>
> ```text
> alignment = mean over the fields both sides carry of (+1 if equal, −1 if not)
> new score = similarity × (1 + 0.3 × alignment)
> ```

**What the test showed (2026-06-18).** On 24 held-out town votes, the queries were regenerated, a wide
set of lessons was found, and a top five was built with and without the tilt. A model then judged, for
each lesson, whether it applied. The tilt changed the top five in 23 of 24 cases, but the share judged
"does not apply" moved only from 38% to 36%, the share that fully applied from 15% to 16%, and the
vote hit a real threat a third of the time either way. The per-case output was printed, not saved; the
numbers are from the plan record. The setting stayed off.

**Why the test could not settle it.** The July audit (§5) found that the swing flag the query had
written scored below a constant. Its pre-written rule therefore marked the gating verdict as
unproven: with keys that noisy, a real but small benefit would be shrunk toward zero. The audit's
authors estimated the screen would have seen about 60% of a true effect. A re-run with computed swing
values was authorized, at about $10–15, and held for spending approval; it never ran. The two class
labels were never checked against a human reading: a sampler that would pick cases for that was
built, the labelling was not done, and one of the labels is lopsided (villagers marked themselves
`safe` 2,164 times against 134 `exposed`).

**What changed.** Every number the gating used is now computed exactly on the query side (§4). In
October 2026 a review of the ten-seat query removed the four category labels that only the gating used,
so if gating were switched on today it would compare the alive bucket and swing only. The stored
lessons keep the labels, because the offline duplicate check and the replay page use them.

**What it shows.** Fields that agree with the board are not the same as a lesson that applies. The
judge in the gating test weighed preconditions finer than "safe or exposed" or "information-rich or
starved". The fields that did move fit in a later test were exact stage facts used as a hard filter
(§5), and even those miss the events a lesson depends on (§7).

**Limits.** 24 votes, one run, one judging model, the nine-seat game, and an older store. The test
measured whether lessons applied and whether one vote hit a threat, not games won.

## 7. What is not established

- **No effect on play.** Nothing here shows that memory, or any use of these fields, makes agents play
  better. The town-only memory run of July 2026 leaned negative, and the served game runs with memory
  off by default.
- **Retrieval evidence is old and small.** The retrieval measurements in §5 and §6 ran on the
  nine-seat game and earlier stores, except the stage-filter replay, which is offline and judged by
  model readers.
- **The stage facts do not record events.** The readers of the ten-seat lessons named the remaining
  misfit the same way: lessons keyed to an event the seat has not seen, such as a rival claim or a
  wolf just voted out. The Sentinel query in §2 shows it. That game read from the 12-game store, and
  the lesson ranked first of the three shown (similarity 0.859) was written for night 1, with two
  watches and ten alive: *"On
  Night 1, with no claims, deaths or reads, spend one of the two watches on a quiet, unclaimed player
  and keep the second for later."* The seat itself rejected it: "Night 1 is over and this is Night 2,
  so the blind opening watch no longer applies." The stage filter would have kept it, because both
  boards had eight or more alive and a watch left.
- **Stored values are model-written.** Only uses left has been checked against the record (§5). The
  stakes prose on a stored lesson is the extraction model's own reading.
- **The two class labels were never validated** against a human reading.

## Sources and implementation

| What | Where |
|---|---|
| The fields, the cells, the string they are joined into | `Agents/schemas/memory.py` (`BaseSituation` and the field groups, `TEN_SEAT_CELL_SHAPES`, `compose_situation_embed`, `cell_situation_schema_for`) |
| The query, the computed facts and the overwrite | `Agents/memory/retrieval/situation_agent.py` (`_computed_dims`, `_known_board_facts`, `_override_deterministic_dims`, `_query_cell`) |
| The stakes arithmetic | `Agents/rules/board_clocks.py` |
| The same arithmetic from the true roles, used to grade | `Agents/memory/consolidation/decision_scoring.py` (`query_criticality`) |
| Shared field guidance for the query and extraction prompts | `Agents/prompts/cell_prompt.py`; `compose_cell_guidance` in `Agents/prompts/prompt_inputs.py` |
| Extraction by cell | `Agents/memory/extraction/` (`extraction_agent.py`, `cell_units.py`, `offline.py`) |
| Duplicate check groups; synthesis groups | `Agents/memory/dedup_gate.py`; `Agents/memory/strategy_synthesis.py` (`synth_partition_key`) |
| Dimension gating and the stage filter (both off by default) | `Agents/memory/retrieval/dimension_gating.py`; switches in `Agents/memory/retrieval/plan_gating.py` and `Agents/config/run.py` |
| The replay page's case file | `frontend/src/stage/film/case-file.ts` (`situationOf`) |
| Tests | `tests/engine/test_v6_cells.py`, `tests/memory/test_situation_dim_override.py`, `tests/memory/test_situation_query_inputs.py`, `tests/memory/test_dimension_gating.py`, `tests/memory/test_stage_filter.py`, `tests/memory/test_dedup_gate.py`, `tests/memory/test_uses_left_cells.py`, `tests/evaluation/test_board_clocks.py`, `tests/evaluation/test_dimension_audit.py` |
| The fill audit (2026-07-02, at `4b1449e`) | runner `evaluation/src/instrument_validation/dimensions/dimension_audit.py`; [`dimension_accuracy_audit/`](dimension_accuracy_audit/experiment_log.md) and `data/dimension_audit_20260702_105203.json` |
| The stakes-conditioning screen (2026-06-15) | `evaluation/src/studies/criticality_screen.py`; [`criticality_screen/`](criticality_screen/experiment_log.md) and its JSON outputs |
| The gating screen (2026-06-18) | `evaluation/src/instrument_validation/dimensions/dimension_gating_screen.py`; result in [`../../v7_final/plan.md`](../../v7_final/plan.md) (the G3 block) |
| The stage-filter replay, the stored uses-left check, the fit reads (2026-10-12 to 13) | `evaluation/experiments/v8_stage_filter_replay.py`; [`../../memory_system/v8/experiment_log.md`](../../memory_system/v8/experiment_log.md); `data/gate/` |
| The §2 lesson and query | `memory_stores/ten_seat_v2/strategy_points.json` (Sentinel night); `../../memory_system/v8/data/gate/lookups.jsonl` (game `20497d9e`, night 2) |
