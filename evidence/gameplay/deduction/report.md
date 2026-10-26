# The Deduction Engine

**Version.** The implementation described here is the 2026-10-26 snapshot at
`ccaec2f64788c1d3183940dd31a4c93475c164b5`. Against it were rechecked the modes and their per-side
override, the leak boundary, the guard on unverified roles and limits, where the blocks sit, and the
test files; the rest of §2 was written against `5574bb11` (2026-10-21). Historical results belong to
the models, prompts and configurations recorded in each study; they are not all measurements of this
snapshot.

**Scope:** how the harness hands each AI seat the conclusions a careful human would draw from what
that seat knows, computed by code and injected into its prompt: what the engine may state, where its
one leak boundary sits, how it is verified, and what the screens showed.
**First written:** 2026-10-21 against `5574bb11` (the engine as deployed to the server on 2026-10-19
at `334a56e1`). The specification with every row, the owner's rulings and the slice-by-slice build
record is [`deduction_catalogue.md`](deduction_catalogue.md); the case register and the experiments
that led here are [`experiment_log.md`](experiment_log.md).
**Artifacts (the proof behind §4):** `data/deduction_injection/` (the R1 replay) · `data/deduction_block_census/`
(block sizes over 278 turns) · `data/deduction_placement/`, `data/deduction_placement_n10/`,
`data/deduction_ac2_2x2/`, `data/deduction_ac2_closing_fixed/` (the placement and vote screens) ·
`data/solver_census/` (the solver against the brute-force oracle on random games, and its cost) ·
`../data/evil_cover_screen/` and `evil_cover_games/` (the evil-seat lines) · `../data/counter_claim_votes/`
(the dropped counter-claim line).

> **Orientation: one seat's turn.** Every injected line is produced along one path:
>
> **the seat's payload → `SeatView` → items, by level → two rendered blocks → the prompt**
>
> The payload is what the information boundary already allows that seat (the public record, its own
> night records, and for a wolf its pack). `SeatView` is the only thing the engine reads. Items are
> typed conclusions with a grade and a derivation. The two blocks are the text the seat sees, one
> shared by every seat and one its own. Every identifier below (`own_results`, `candidates`,
> `deduction_mode`, the brute-force oracle) hangs somewhere on this path.

---

## 1. The guarantee (current contract)

The AI seats run Claude Haiku 5.5 at a low thinking budget. They absorb facts and do not take the
first inferential step. In the case that opened this work (R1 in the log), a healer was roleblocked on
night 1, the trailseer reported seeing player_7 go to the healer, and player_7 admitted the visit. Only
the Chanteuse, a wolf, can roleblock. The healer wrote every premise into its notes three times, never
named player_7, and passed all three turns. So the contract is:

**Each AI seat's prompt carries, written by code, every conclusion a careful human would draw from
what that seat knows, each line graded by how far it holds, and no line ever states as certain what
some legal game would make false.**

**Three grades, in the wording itself.** The grade is carried by the sentence, never by a header a
weak model may skip.

| Grade | Holds in | Reads as |
|---|---|---|
| Certain | every legal game that agrees with what the seat knows at that turn | "You were roleblocked: your protection of player_5 did not happen. Only the Chanteuse could roleblock that night, and a block is a visit, so the Chanteuse, a wolf, came to you that night." |
| Follows if named claims are true | every such game in which the named claims are also true | "If player_2's watch is true, player_8 is the Healer: no other role still in play could have come to you on night 2." |
| Possible explanations | a complete list of the branches, one of which is certain | "player_3 says player_7 came to you on night 1, and player_7 agrees. If that is true, either player_7 is the Chanteuse, or player_7 and the Chanteuse both came to you." |

A conclusion that holds on only some branches of its premises is not stated at all. The first and
third examples are the two lines the R1 healer now receives; the second is from the day-3 vote in §4.

**Why the bar is absolute.** Injected text is taken up almost every time: on the R1 turn, all ten
low-effort replays wrote the injected fact into their notes (§4). A wrong line is therefore not an
occasional error but a deterministic falsehood in every game where its conditions hold. That is why
the catalogue's rule is *never state as absolute what is not*, and why soundness, not coverage, is
what the tests prove (§3). Coverage is the owner's standing ruling: inject as much as a careful human
could deduce, including conditionals and which roles each player could still be, and let the only
bar be the false absolute.

**Where it is enforced.** The engine reads one typed object, `SeatView`, built in
`Agents/deduction/seat_view.py` from the seat's own payload and nothing else. The payload builders
already give each seat only what its role may know (the information boundary, documented in
`../../agent_boundaries/report.md`); `SeatView` selects from that payload and adds nothing. So the
injection sits inside the existing boundary rather than opening a second one, and a metamorphic test
(§3) checks that a seat's lines do not change when hidden state changes.

**How much a seat gets.** A per-game setting, `deduction_mode` on `RunConfig` (and the batch
runner's `--deductions`), chooses `off`, `record` (only the lines beside the seat's own night
records), `public` (those plus the blocks without any line that rests on a claim) or `full`, with a
per-side override so one faction can play at a lower level. A human seat gets nothing whatever the setting. A game whose dealt roles or use
limits are outside what the engine was verified for also gets nothing (`verified.py`): an unverified
role can make a line that says "only X can…" false in every game that deals it, and silence is the
safe default.

## 2. The engine: what it concludes, level by level

The engine is one package, `Agents/deduction/`, with one folder per level of reasoning. Each level
reads the `SeatView` and the levels below it and emits typed items (`DeductionItem` in
`Agents/schemas/deduction.py`: subject, night, the conclusion as facts, the text, the grade, the
premises, the sources and the derivation). The levels, in the order a seat would use them:

| Level | Folder | What it adds | Example |
|---|---|---|---|
| Own results | `own_results/` | What the seat's own night record proves, read with the morning. Shown beside the record itself. | the roleblock line in §1 |
| Public events | `public/` | What the morning announcement, the dead roster and a read-out will prove to everyone. The same for every seat. | "player_3's will shows player_7, the Chanteuse, went to player_8 on night 1. The pack's kill that night was on player_1, so that visit was her block on player_8." |
| Candidate roles | `candidates/` | Which roles each living player and each hidden body could still hold, by constraint propagation (below). | "The Serial Killer is alive and is one of player_2, player_4, player_6, player_8 and player_10." |
| Joins | `joins/` | The seat's own results set against another player's claim about the same night. | the "either player_7 is the Chanteuse, or…" line |
| Conditionals | `conditionals/` | The propagation rerun with a claim assumed true, and its contrapositive on a vote turn. | "player_8 can be the Serial Killer only if player_2's watch is false." |
| Comparisons | `comparisons/` | Today's claims against the record and against each other: which fit, which cannot both hold, and the status of every role claim. | "player_2 claims the Sentinel. Its report that player_7 came to you on night 2 is true. That does not show that player_2 is the Sentinel." |
| Explanations | `explanations/` | A claim the morning leaves open, with every branch; budgets that run out across nights. | "player_5's self-bet has saved it twice, so it has none left." |
| Evil seat lines | `evil/` | For a wolf, the Serial Killer or the Necromancer: which roles it could claim without a public contradiction, which night stories fit the record, and what its own true visits rule out. Facts, never advice. | "player_2's hidden role was the Sentinel: your pack's kill record shows it, and the public record does not. No living player holds the Sentinel, so if you claim it, no one can counter-claim you truthfully." |

**The solver, and why it is sound but not complete.** Candidate roles are computed by propagation,
not search. Each player starts with the census: the dealt roles not yet revealed, minus the seat's own
role and, for a wolf, its pack's. Every certain fact from the levels above removes candidates. Then
four rules run until nothing changes: a role with one possible holder leaves everyone else; *k*
players who can only hold *k* roles between them take those roles from everyone else; when a watch
saw the visitors to an attacked player and only one of them could have made the attack, it did; and
the game having continued past every check so far constrains who could have been checked. A role
whose holder must have been alive on a night also leaves the bodies that died before it. A
conditional reruns the same propagation
with a claim added as a premise. Propagation can miss a conclusion a full search would find, which
only means the seat is told less; it must never remove a candidate that some legal game still allows.
The exhaustive search exists, but only as the test oracle (§3), never in a game.

Propagation was chosen for its reasons, not its speed: each removal is one named rule resting on
recorded evidence, which is what the line's wording and the turn's log carry, where a search's
answer comes without a step a reader can follow. It is also cheap. Building one seat's candidates
(its constraints, then the solve) took a median 0.45 ms over 3,408 views (p99 1.65 ms), and both
blocks of acceptance case 2's vote turn, every level included, a median 10.5 ms over 30 builds
(`data/solver_census/`, one aarch64 host, for scale only). A model call takes seconds.

**Roles as traits, not names.** The rows ask what a role *is* (night-immune, blockable, whether its
visits show under its own name, whether it reads Suspicious) from one table,
`Agents/schemas/role_traits.py`, rather than naming roles. A new role is declared there, the trait
tests say which rows its traits already cover, and only new behaviour needs a new row.

**Two blocks, by cache placement.** The renderer (`render.py`) is a pure function from items to
text; derivations go to the turn's log, never into the prompt. The public block is built from the
public record alone, so it is identical for every seat and sits in the shared, cached prefix of the
prompt; it changes only at a morning, a reveal or a vote. The seat's own block sits after the cache
boundary, before its carried-forward strategy note. Within a block the order is fixed by seat number,
never by content, because these models favour the first-named seat: an entry put first because it
had the most to say would pull votes toward that player.

What a seat reads, on a real turn. This is AC2, one of four acceptance cases: a known failure from a
served game, frozen at the turn it went wrong and rebuilt from the seat's payload (§3). The seat is
the investigator at a day-3 vote; as played, it voted out the healer who had protected it.

```
- If the current role claims are true, the Serial Killer is player_6 or player_10.
- You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the
  Chanteuse. player_2's report that player_7 came to you that night is true. This does
  not show that player_2 is the Sentinel.
- player_8 can be the Serial Killer only if player_2's watch is false.
```

Over 278 saved Haiku turns (four games, frozen and captured), the seat block is a median of 4 lines
and 742 characters (p90 8 lines, 1,778 characters; the longest 12 lines, 2,920 characters) and the
public block a median of 1 line and 338 characters. Twenty turns got an empty seat block. The
engine adds roughly a paragraph to the prompt.

## 3. How we verify: soundness is tested, coverage is not

The build bar for every row, set by the owner before any row was built, has four parts, and the
tests in `tests/engine/deduction/` are organised around them. Each level has its own file
(`test_own_results.py`, `test_skill_results.py` and `test_morning_results.py` for the seat's own
results; `test_public_events.py`, `test_candidates.py`, `test_joins.py`, `test_conditionals.py`,
`test_comparisons.py`, `test_explanations.py`; `test_evil_seat.py` and `test_covers.py` for the evil
seats), and each file holds that level's examples, counterexamples and exact lines. Three files test
what surrounds the levels: `test_render.py` asserts that the public block is the same for every seat
and sits before the cache boundary, and that `off`, `record` and a human seat get no block;
`test_verified.py` asserts that a role or use limit outside the verified set turns the engine off;
`test_claim_view.py` checks the claims as the engine reads them, from the claim ledger and from
today's speakers' own fields. The tests are largely AI-written and not yet audited.

**An executable example and counterexample on the real engine.** Each row is exercised by a
constructed night resolved through the real night rules: one night where it fires and its
conclusion is true, and one or more where a single condition differs and it must not fire, or must
fire with the weaker wording. The counterexamples cover the interactions the catalogue lists for the
row: borrowed actions through a body, blocked attempts, the living against the reanimated
illusionist's conceal, a fortune teller's self-bet, deaths on the same night.

**A golden of the exact line.** Every row's rendered text is pinned, so a wording change is
deliberate. The four acceptance cases (`test_acceptance.py`) go further: for each known failure the
turn is rebuilt from the frozen payload exactly as the live pipeline builds it, and the whole prompt
must contain every sentence the case lists and nothing on its "must not say" list. For AC1 the
forbidden sentence is "player_7 is the Chanteuse", with or without a premise: a second visitor is
always possible, so it appears only inside the either/or line.

**Two oracles for soundness.** The brute-force oracle (`tests/factories/role_assignments.py`)
enumerates every deal of the cast that agrees with what the view knows, plus the line's premise if it
has one, and asserts that every certain or conditional item holds in all of them. The random-night
oracle (`tests/factories/random_nights.py`) deals a random cast, kills some players on earlier nights
and days, lets every living role make a random legal choice, resolves it with the real engine, and
then checks every fact every surviving seat's lines state against the true roles and the resolved
night. Twenty thousand such nights run in each of `test_own_results.py`, `test_public_events.py`
and `test_candidates.py`. A rule that says more than the game guarantees fails here.

**A leak test.** The metamorphic form of the boundary in §1: several hidden states compatible with
what a seat sees (other seats' roles and results permuted within the legal assignments) must render
identical lines for that seat. It runs per level (for example in `test_own_results.py`,
`test_morning_results.py`, `test_comparisons.py` and `test_covers.py`).

**The role-trait table is derived, not declared.** `test_role_traits.py` resolves real nights with
every role attacked, blocked, watched, followed, checked and sigilled, and fails on any trait the
engine disagrees with. Each of the 168 single-trait flips is caught.

**Completeness of the solver, measured once.** Soundness is tested; whether propagation misses what a
full search finds was measured separately (`evaluation/experiments/deduction_solver_census.py`,
output `data/solver_census/`). On 150 random legal games from the suite's generator (seed
20261018), every view was solved and compared with the brute-force oracle's allowed deals: 3,408
seat views and 525 public views, and in none did the solver keep a role that no allowed deal gives.
The oracle builds its conditions from the same knowledge as the engine, so a fact neither encodes is
invisible to this check: it shows no gap against the oracle, not completeness. One gap is known by
design: a constraint that depends on a choice nobody sees (a self-bet, which body a borrowed action
used) keeps both branches. Conditional runs, with a claim added as a premise, were not measured.

These tests prove that what is built is sound. They do not prove the catalogue is exhaustive; a
deduction a human would make and the engine does not is a gap in coverage, not a false line, and
the acceptance cases are the only test of coverage.

## 4. Evidence: what changed, and what did not

**Verdict.** The engine removes the inferential step it targets: on the R1 turn, every replay now
writes the certain conclusion into its notes. It does not by itself change behaviour where a seat's
own note or a misleading public line pulls the other way. The one whole-game comparison so far is on
the evil side: with new card text and the engine's lines together, the wolves won 3 of 8 paired
games, against none before. It is reported in the [roles report](../roles/report.md); the engine's
share is below. No town-side win-rate claim is made: the engine was assessed on
reasoning, on frozen turns, at small *n*, by design.

### The levers tried before code (why injection)

Four levers were tried against the same failures before the engine was built:

- **A higher thinking budget** (Haiku at `medium` against `low`) is the one that moved votes: 98 of
  160 right against 65 of 160 on sixteen frozen vote cases, better on 12 cases and worse on 1 (sign
  test p = 0.003), at about 2.7× the output tokens. The notes and the discussion turns stayed within
  noise: the votes' notes had a fact error in 46% of samples at medium against 50% at low (11 cases
  better, 5 worse, p = 0.21), and 47 of 115 discussion samples were flawed at medium against 49 at
  low.
- **A stronger summariser** (Sonnet 5.5 for the day summary) was not better: 18 of 30 summaries
  flawed in each arm.
- **A rewritten private-note prompt** was worse on every judged measure (27 fact errors against 15
  in 56 samples per arm) and was not adopted.
- **A majority of three low-effort votes** was right as often as one (39% against 41% of cases).
  The errors repeat across samples, because the model holds the same wrong belief each time it reads
  the same context.

That last result is the case for code. The missing step is deterministic, so it can be written down
once rather than sampled for.

### R1 replayed: the fact is absorbed, the silence is the note's

The healer's three passed turns of day 2 were replayed ten times each, as played and with the
roleblock line injected, at low and medium effort. On the injected turn all ten low-effort notes
record that the Chanteuse visited the healer, where none did as played; the second link, that
player_7 is probably the Chanteuse, appears in 2 of 10 reads against 0 of 10. The seat still spoke in
0 of 10 (1 of 10 at medium). A 2×2 on the turn's inputs found the cause: with its carried-forward
note ("stay quiet") replaced by a neutral one, the seat spoke in 9 of 20 samples against 3 of 20
in this run (p = 0.08), and 3 of 30 pooled with the earlier run (Fisher p = 0.007); removing a
survival sentence from the role card changed nothing (6 of 20 either way). The block, then, must outrank the note, which is why its
placement was screened (next) and why the limits in §5 are about behaviour, not facts.

### Placement and the AC2 vote: before the note, and a third of votes still wrong

The seat block can sit before or after the seat's strategy note. Three screens on the four
acceptance cases (n = 3 and n = 10 per case per arm, judged blind by chat subagents; then a 2×2 on
AC2 alone at n = 25 per arm) found no placement difference that survived the sample size: at n = 10,
AC1 and AC4 favoured `before_note` and AC2 favoured `after_note`; at n = 25 on AC2, player_8 (the
real healer) got 9, 9, 10 and 5 of 25 votes across the four arms, pooled 33 of 100. `before_note`
was ruled the default on 2026-10-18; it is also the cache-friendly order, since the note changes
every turn and the block only at a morning or a vote. The setting has since been removed: the block
always sits before the note (`Agents/prompts/memory/context.py`, the `deduction_seat_before_note`
slot). The two sentences about player_8 that the 2×2
trimmed are kept: they are true and did not move the vote.

What did move AC2 was outside the engine. The moderator's closing line in the frozen game still read
"player_8 has been accused by player_2, player_5 and player_4", although one accuser had withdrawn
and one had only asked a question (R2, fixed in code on 2026-10-16). With today's closing line and
the block, the vote for player_8 fell from 9 to 5 of 25. At this *n* that is suggestive, not
decisive; 5 of 25 is the best current estimate of the remaining AC2 failure with the engine in place.
For scale, before the engine the same seat at low effort voted right in 1 of 10 replays with today's
closing line (a different setup, so not a paired comparison).

### The evil side: facts for a cover

Since a ruling of 2026-10-18, the evil role cards tell an evil seat to claim a role and never deny a
sighting. The advice is the cards'. The engine's part is facts only: which roles the seat could
still claim without a public contradiction, which night stories fit the record, and which of its own
true visits a story would have to explain.

The engine's share was screened on 41 pressured evil turns from earlier games (Haiku 5.5 at low
thinking, two samples per turn), with the new card text in every arm. Without the covers line (the
night stories), the seats claimed a role 36 times and denied 4 times; with the line, after one fix,
44 and 0. Claims that contradicted a sighting another player had reported fell from 4 to 1. The last
version of the line cut the Serial Killer's catchable claims (those a careful town could show false)
from 2 of 15 to 1 of 13, and none of the 42 claims under it contradicted a reported sighting. One
judge labelled each line, and the arms with and without the line were labelled by different judges,
so these are counts from one screen, not a measured effect. What the card text did on its own, and what whole games showed, is in
the [roles report](../roles/report.md) ("The evil contest").

### A dropped line: what each counter-claimant names

Two of the wolves' three wins in the paired games with the new cards were counter-claims the town
decided wrong: a fake claimant's word against a real one's, and the town sided with the fake. In the
clearest case, two players claimed the Investigator and the engine said only that at most one of them
holds it. A follow-up line (catalogue slice 16) spelled out the results each counter-claimant had
named as the role, for example "As the Investigator, player_1 names a check of player_5 on night 1
(Not suspicious), which a reveal of player_5's role would test; player_7 names no check result."

It was screened on the 10 town vote turns of those games where the
line appeared (3 samples per arm, Haiku 5.5 at low thinking, the vote as the measure). Pooled, it
changed nothing: the votes went 12 to the fake claimant and 16 to the real one without the line, and
12 and 17 with it. In the one game it was built for it moved votes the wrong way (7 fake and 4 real
without, 5 and 7 with). One plausible reading: the model follows the seat the line names first and
longest, rather than the argument it makes. The line was dropped on 2026-10-18 and never committed.
It was a true fact, but past the facts the block already had, the vote is the model's call.

## 5. Limits: what the evidence does not say

**No town-side outcome effect is claimed.** The engine was assessed on reasoning: frozen turns, exact
sentences, small *n*. The owner's ruling was that replay measurements do not gate the build, and a
paired whole-game A/B of town with and without the engine has not been run. The one whole-game
comparison is the evil-side one in the [roles report](../roles/report.md), which bundles the card
text with the engine's lines.

**Absorbed is not acted on.** §4 shows a seat writing the injected conclusion into its notes and still
following an earlier "stay quiet". A later screen placed the block before the note; whether the
block outranks a contrary note in general was not measured beyond the four acceptance cases.

**One level has never fired.** The explanation branches for a claim the morning leaves open (row F8,
in `explanations/`) produced no line on any of the 278 census turns. The conditions are real but
rare; the code is tested like every other row and costs nothing when silent.

**Scope is the standard game.** Twelve roles and the standard use limits (two checks, two watches,
two sigils, two conceals, two self-bets). Outside that, every seat gets nothing (§1). The vigilante's
bullet count is deliberately not public, so no line counts bullets.

**Judging was by chat subagents, not an API judge.** The placement and cover screens were labelled
blind by Claude subagents in chat sessions; the thinking-budget and summary screens by Sonnet 5.5 in
a Message Batch. Agreement between judges was not measured, and the cover screen's three steps had
different judges, so its counts are comparable within a step, not across.
