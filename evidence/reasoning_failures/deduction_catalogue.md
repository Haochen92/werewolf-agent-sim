# Deduction catalogue: what is certain, for whom, and when

*Second version, 2026-10-16. Renamed from `deduction_catalogue_draft.md`. Built from the working tree
on `feature-frontend-v1`, including the owner's uncommitted rule changes of 2026-10-16. No model was
called. Rows marked "verified by run" were checked by calling `resolve_night`, `night_action_records`
and `night_resolution` on constructed nights (`poetry run python`, scratch scripts, not committed).
This version also takes in the corrections from `deduction_catalogue_review.md` that I re-checked
against the code; each one is marked "(review §k)" or "(review Mk)". Third pass, same day: the
corrections from `deduction_catalogue_review_v2.md` that held against the code (its probes are in
`data/catalogue_review_v2/probes.py`), marked "(review v2 §k)", and the owner's note that wills make
private results public (L11). Table E is a specification only: the owner has not yet approved
building it. Fourth pass, same day: the corrections from `deduction_catalogue_review_v3.md` that held
against the code (probes in `data/catalogue_review_v3/probes.py`), marked "(review v3 §k)", and the
owner's bar for building any row ("Build verification", below). Fifth pass, same day: the owner's
coverage ruling (R9) and the fourth review. The standard in §0 now grades every line (certain,
follows if named claims are true, possible explanations) instead of admitting only certain ones.
New: Table F (joins and conditionals), the rule for how the engine derives them, E17 (direction of a
visit), and "Acceptance cases": four turns from the Haiku games, each with the exact sentences the
seat should have received.*

## Rulings (owner, 2026-10-16)

| Ruling | What it settles | Code now | Rows changed |
|---|---|---|---|
| R1 (was OQ1) | Only a **kill** through a body (the illusionist's, or a shot through the vigilante's) makes the necromancer read Suspicious. A sigil, block, protection, check, watch or follow through a body does not. The card was corrected. | `night.py:239-246`; `prompts/roles/necromancer.py` RULES | L7, L10, A22, B9, B12, C3, Table D |
| R2 (was OQ2) | A save through the dead healer's body is announced as "saved by **a reanimated healer**". The records say "a reanimated healer saved them" / "a reanimated healer's protection". The ledger flags a claimant who claims to be the living healer for such a save (review v3, small corrections). So "saved by the healer" now means the living healer protected that night. | `night.py:276-277` (`protected_through_body`); `nodes/night/resolution.py:150-151`; `night_record.py:64-67`, `:70-83`, `:165-170`; `schemas/night.py` `NightReport.reanimated_saves`; `claim_ledger.py` `_REANIMATED_SAVE` | A11, A12, A29, A37, B11, B12, C9, C16, Table D, E5 |
| R3 (was OQ3) | A blocked blocker cannot happen in a legal game. The owner will make blockers unblockable in future. No code change. | `night.py:135-153` unchanged | L3 |
| R4 (was OQ4) | The roleblock record will be rewritten in build step 1; the "you learned nothing tonight" clause goes. | `night_record.py:239` unchanged for now | A6, A7, A8 (wording marked as the step-1 target) |
| R5 (was OQ5) | Only the **living** illusionist's conceal hides the pack carrier's visit. A clean through the illusionist's body no longer hides it. | `night.py:221-237` (`concealed_by_illusionist`) | L4, A28, A31, B2, B7, C6 |
| R6 (was OQ7, OQ8, OQ12) | Cards fixed. Chanteuse: "Her block works on Town players (she cannot block her own pack)". Necromancer: "such a block works on wolves too", and no vigilante "penalty". Trailseer: "'Visited no one' means only that no visit was made in their name that night, not that they did nothing." | `prompts/roles/chanteuse.py`, `necromancer.py`, `trailseer.py` | A35 (wording now matches the card) |
| R7 (was OQ17) | The vigilante's bullet count stays out of the public rules: it is a balance setting. No public row counts bullets. | `prompts/roles/vigilante.py:6`, `:70` unchanged | C5, C20 |
| R8 (owner note) | **Wills make private information public.** When a revealed town player's record is read out, its earlier private results become public facts from that moment on. | `night_record.py:296-312`; `resolution.py:168-170`; `orchestrator.py:213-215` | L11, B32, C20, C21, Table E |
| R9 (owner, coverage) | **Coverage first; the only bar is never stating as absolute what is not.** Inject as much as possible of what a careful human would deduce by joining the public record, the seat's own results and other players' claims, including conditional conclusions, claim sets against the census, and which roles each player could still be. "Holds in every legal game" is the bar for stating a line as certain, not for including it. Every other line names its premises on the same line. Lines are direct and concrete. Replay measurements do not gate the build. | none (specification) | §0, Table E status, Table F, Acceptance cases |

## Build verification (owner, 2026-10-16)

Injected text is taken up almost every time (§4 of `experiment_log.md`: 10 of 10 notes). So a wrong
row is not an occasional error: it is a **deterministic falsehood in every game** where its
conditions hold. No row is built until it meets all three of these:

1. **Executable example and counterexample on the real engine.** For each cast the row names (and
   each night condition, e.g. night 1 against later nights), a constructed night run through
   `resolve_night`, `night_action_records` and `night_resolution`:
   - one night where the row fires and its conclusion is true;
   - one or more nights where its conditions differ in a single respect and it must not fire, or
     must fire with the weaker wording.
   The counterexamples cover the interactions this catalogue lists for the row: borrowed actions,
   blocked attempts, live against body conceals, the fortune teller's self-bets, and deaths on the
   same night.
2. **A golden test of the exact rendered line** on a constructed night, so any change to the
   wording is deliberate.
3. **A leak test.** The receiver's rendered deductions must not change when facts hidden from it
   change. This is a metamorphic test: build several hidden states compatible with what the
   receiver sees (other seats' roles and private results permuted within the legal assignments)
   and assert identical output. Separately, check that the function's inputs are only the
   receiver's legitimate payload (the public record, its own records and, for a wolf, its pack's),
   never `roles`, the night's choices or other seats' records.
4. **The acceptance cases pass** (section "Acceptance cases", review v4). Given the frozen state of
   each case's turn, and only the receiver's payload, the engine renders every sentence the case
   lists, exactly, and nothing that the case's "must not say" list forbids. A row that no case
   exercises still needs 1–3.

Grades 2 and 3 of §0 (conditional lines and branch lists) also need a **brute-force check** in tests:
on each constructed night, enumerate every role assignment that agrees with the receiver's knowledge
(plus the line's premise) and assert the line holds in all of them. This is the oracle for Table F's
propagation engine; it runs only in tests, never in a game.

These tests verify the built rows; they do not prove that the catalogue is exhaustive.

## Build status

Code: the package `Agents/deduction/` (entry points in its `__init__.py`; types in
`Agents/schemas/deduction.py`). Tests: `tests/engine/deduction/`, with the random legal nights and
the fact checker in `tests/factories/random_nights.py`. Nothing committed yet.

| # | Slice | Rows | Where | Status |
|---|---|---|---|---|
| 1 | Level 1: roleblocks, immunity, saves | A1 (with B11's attack types), A2–A5, A6–A8, A11–A19, A48 | `own_results/roleblock.py`, `own_results/attacks.py`; shared: `seat_view.py` (the leak boundary), `night_state.py`, `wording.py`. Shown beside each record by `format_night_actions`. | Built 2026-10-16. Tests: exact lines per row and cast; the leak boundary; 20,000 random legal nights, every stated fact checked against the true roles (three deliberately broken rules each caught). The roleblock record no longer says "and you learned nothing tonight" (R4). |
| 2 | The per-game switch | — | `RunConfig.deduction_mode`: off / record / full, default full; carried into each AI turn's payload (`turn/pipeline.py` `_with_deduction_mode`); `scripts/run_batch.py --deductions`. A human seat gets nothing whatever the mode (`seat_view.deduction_mode_for`). The replay bench sets `deduction_mode` on the payload. | Built 2026-10-16. Not yet on the server's game row or the replay record (served games run "full"). |
| 3 | Level 1: rows that need only the record and the roster | A21, A22 (condition a, and both wolves revealed), A23–A27, A32–A35, A37–A43, A49, A50 | `own_results/checks.py`, `sightings.py`, `sigils.py`, `blocks.py`, `bets.py` | Next, after the owner's code review |
| 4 | The morning announcement as structured data in the payload | — | | |
| 5 | Level 1: rows that need the announcement | A22 (conditions b, c), A28–A31, A36 (concealed case), A45 | | |
| 6–12 | Levels 5, 3 (the core and the block), 2, 4, 6, 7; the acceptance cases end to end | Tables B–F | `public_events.py`, `candidates.py`, `render.py`, `joins.py`, `conditionals.py`, `claims.py`, `explanations.py` | |

## 0. Purpose and the rule

The AI seats (Claude Haiku) miss simple deductions (case R1, `experiment_log.md` §4). The plan is to
inject, by code, what a careful human would deduce from (a) the public record, (b) the receiving seat's
own private knowledge and (c) other players' claims, each line graded by how far it holds (R9). This
catalogue lists those conclusions before any of them is built.

**What the seat knows.** The public record (announcements, dead roster, votes, the dealt cast), its
own role, its own night records, and, for a wolf, who its allies are and the pack's kill record. A line
never relies on hidden state.

**The standard: three grades (R9).** The grade shows in the wording of the line itself, never in a
header the model may skip.

1. **Certain.** Holds in *every* legal game that agrees with what the seat knows at that turn. Stated
   plainly: "player_7 cannot be the Serial Killer." Tables A to D are this grade.
2. **Follows if named claims are true.** Holds in every legal game that agrees with what the seat
   knows *and* in which the named claims are true. The premise opens the line: "If player_2's watch is
   true, player_8 is the Healer." A premise is one or two named claims, or "the current role claims"
   as a single premise (the latest role claim of each player, withdrawn ones excluded). "If player_8 is not the Healer" is a valid premise; "if player_8 is lying" is
   not, because it does not say which part is false. The contrapositive form is also allowed: "For
   player_8 not to be the Healer, player_2's watch must be false."
3. **Possible explanations.** A certain disjunction: "Either A, or B." The list must be complete,
   since a missing branch is a false certainty. Branch lists are generated from the rows and checked
   by the brute-force oracle (Build verification), never written by hand. A list that explains a
   claim includes the branch that the claim is false, unless the line is already conditional on it.
   Example: "player_10 says it shot player_5, and player_5 is alive: either player_10 was roleblocked,
   or player_5 could not be killed that night, or player_10's claim is false." (The shooter's own
   record is a separate, certain line: the engine tells the shooter which of these happened.)

A conclusion that holds only on some branches of its premises is not stated at all. **The one
prohibition: never state as absolute what is not.**

**Form.** Every line names players and nights, uses plain verbs, and ends at its conclusion. No lemma
or row references, no "see L4", no two-way links. The test for a proposed wording: a reader with no
rules knowledge takes it the right way on first reading. A reason may follow the conclusion when it is
short and made of facts the seat can check ("…, because no one had died before that night").

**Where knowledge comes from (review M7).** The engine-certified sources are the announcements, the
dead roster, the read-out wills (from their reveal on, L11), the seat's own records and, for wolves,
the identities of the pack and the pack's kill record. These are *not* certified facts: the pack chat, any player's claims, and the seat's own notes
or earlier statements. They can be assumptions in a conditional line ("if player_2's claim is true,
then …") but never premises of a certain one. Each derived item, when built, should carry: receiver,
source events, the night of the event, when it was learned, the rule version, assumptions, and
certainty category. A frozen replay must not use facts revealed after its decision turn, and old
games must be read under the rules of their own epoch (R5 changed what an old watch shows).

**Configuration scope (review §10).** This catalogue is for the standard `GameConfig`: 2 checks,
2 watches, 2 bullets, 2 sigils, 2 conceals, 2 self-bets, day 1 with no vote (`config/game.py:27-43`).
Count-based rows use only the limits the rules text tells the players. The cards state 2 checks,
2 watches, 2 sigils, "twice" for conceals and self-bets. The vigilante's card says only "a few
bullets" (`prompts/roles/vigilante.py:6`), so **its bullet count is not public** and no public row
uses it (OQ17).

**Conventions every row uses.**

- **Night n** is the night after day n; the code numbers it `current_day` (`nodes/night/resolution.py:86`, `:91`).
- **Use the state of night n, not the current state.** All night actions are simultaneous, so a player
  who dies on night n still acts on night n. "Alive at the start of night n" is the condition for
  acting. "Revealed dead before night n" is the condition for a body being usable on night n
  (`night.py:53-64`). That means a night death on night ≤ n−1, or a lynch on day ≤ n: a day-n lynch
  supplies a body for night n, a night-n death does not (review M5). A role revealed dead *this
  morning* may have acted last night.
- **The cast is public.** The rules block lists the dealt lineup, including which lone killer and which
  neutral were drawn (`prompts/compose.py:59-70`, `:104`; `schemas/roles.py:98-104`). There are four
  casts. Rows that depend on the cast name them:
  **SK+SP** (serial killer, speculator), **SK+FT** (serial killer, fortune teller), **NE+SP**
  (necromancer, speculator), **NE+FT** (necromancer, fortune teller).
- **The wording must never introduce a falsehood.** Each proposed line hedges where it stands: if a
  line compares a claim with the record, the hedge goes on that same line ("player_2 claims to have
  seen player_7 visit player_5. This is consistent with …; it does not establish which action
  player_7 performed."), never in a header the model may skip. A role is named for a living player
  without a premise only when it is certain. Visits are always stated with a direction ("player_7 went to player_5"),
  never as a two-way link (review §6).

### 0.1 The twelve roles

| Role | Side | Night action (`NightKind`) | Visit? | Night-immune | Blockable | Uses | Special interactions | Code |
|---|---|---|---|---|---|---|---|---|
| Investigator | town | investigate one living player (not self), or `no_check` | yes | no | yes | 2 checks | Suspicious = wolves, plus the necromancer on a night it made a kill through a body (R1) | `roles.py:60`; `night.py:239-246` |
| Sentinel | town | watch one living player (not self), or `no_watch` | yes | no | yes | 2 watches | told every visitor but itself; sees the body's name for the necromancer; does not see the pack carrier's visit to a victim the *living* illusionist concealed (R5) | `roles.py:61`; `night_record.py:137-144`; `night.py:232-237` |
| Trailseer | town | follow one living player (not self), every night, must act | yes | no | yes | unlimited | told whom the target visited; following the necromancer always shows "no one" (its visits are under the body's name) | `roles.py:62`; `night.py:290-297`, `:169` |
| Vigilante | town | shoot one living player (not self), or `hold_fire` (recorded) | yes | no | yes | 2 bullets (not public, OQ17), spent on the attempt, not if blocked | told `immune` when the target cannot be killed | `roles.py:63`; `night_record.py:70-83`; `resolution.py:49-73` |
| Sigilist | town | sigil one living player (not self), or `keep_sigil` | yes | no | yes | 2 sigils, spent when placed, not if blocked | if the target attacked *in its own name* that night, a `sigilist` attack on it; told hit / saved / miss (miss also covers an immune attacker) | `roles.py:64`; `night.py:182-187`; `night_record.py:154-173` |
| Healer | town | protect one other living player, every night, must act | yes | no | yes | unlimited | protection beats death, loses to immunity; cannot protect itself | `roles.py:65`; `night.py:189-205`; `action_space.py:53` |
| Chanteuse | wolves | block one living **non-wolf** (not self), every night, must act; may also carry the pack kill | yes | no | only by the necromancer through her body, so never while she is alive | unlimited | her block takes on town only (R6); not on the lone killer or neutral (`no_effect`) | `roles.py:67`; `night.py:21-24`, `:135-153`; `action_space.py:46-48` |
| Illusionist | wolves | conceal the pack's victim, or `no_conceal`; may also carry the pack kill | yes (to the pack's victim) | no | as above | 2 conceals, spent only when a body is concealed | hides the victim's role and the carrier's visit to it; unspent conceals pass to its body for the necromancer, but a body clean hides no visit (R5) | `roles.py:68`; `night.py:164-165`, `:213-237`; `resolution.py:57-60` |
| (Pack kill) | wolves | the carrier, rotating through living wolves in seat order, kills one living non-wolf every night, must act | yes (carrier only) | n/a | carrier yes | unlimited | the only wolf visit for the kill; record shared by every wolf under actor `wolves` | `night.py:37-44`, `:67-70`; `night_record.py:48`, `:86-87`; `pack.py:181-202` |
| Serial killer | lone_killer | kill one living player (not self), every night, must act | yes | **always** | **never** | unlimited | reads Not suspicious; can only die by lynch | `roles.py:70`; `night.py:21-34` |
| Necromancer | lone_killer | from night 2, with a usable body: one action per night through one body (`via`), or `stay_put` | yes, **shown under the body's name** | **night 1 only** | **never** | unlimited (only a clean through the illusionist's body spends the illusionist's conceals) | bodies are revealed, unconcealed, with a role in `BORROWED_ABILITY`; attacks announced `reanimated_*`, saves "a reanimated healer" (R2); never punished by a sigil; Suspicious only on a night it made a kill through a body (R1) | `roles.py:71`, `:109-118`; `night.py:27-34`, `:47-64`, `:113-119`, `:169`, `:180`, `:244-246`, `:276-277`; `orchestrator.py:457-458`; `resolve.py:242-255` |
| Speculator | neutral | pick a side once (town / wolves / lone_killer / self), or `not_yet` | **no** | no | **never** | 1 pick | the side (not the seat) is announced next morning | `roles.py:73`; `night.py:167`, `:252-253`; `resolution.py:177-180` |
| Fortune teller | neutral | bet on one other living player (optionally naming a role) every night, or bet on itself | **no** | **on a self-bet night** | **never** | 2 self-bets; ordinary bets unlimited | a self-bet makes it immune that night; points are private until the game ends | `roles.py:74`, `:95`; `night.py:194-201`, `:254-260`; `action_space.py:56-57` |

### 0.2 Lemmas the rows use

- **L1. Immunity has three sources** (`night.py:27-34`, `:194-201`): the serial killer every night; the
  necromancer on night 1 only; the fortune teller on a night it self-bets. Per cast, the possible
  immune targets on night n are:
  SK+SP: the SK. SK+FT: the SK or the FT. NE+SP: the necromancer if n = 1, otherwise nobody.
  NE+FT: the necromancer or the FT if n = 1, otherwise the FT.
  - These are the base possibilities; every row refines them with all evidence the receiver can see
    (review v2 §3). A self-bet is never announced, but it can be ruled out by: public facts (no FT in
    the cast, the FT revealed dead before night n); the FT's **budget of two** (a player known to the
    seat to have been immune on three distinct nights is not the FT, and several attacks on one
    night use one self-bet: C17); a will (L11); or the seat's own knowledge. The FT itself knows
    whether it self-bet.
- **L2. Blockers.** The chanteuse blocks, or the necromancer through her **revealed** body
  (`roles.py:109-118`; `night.py:53-64`). Never both on one night: one needs her alive at the start of
  night n, the other needs her revealed dead before night n. If she died concealed (possible only
  through a reanimated illusionist's clean, NE casts), her body is unusable and no block can happen
  at all. The living chanteuse targets only living non-wolves (`action_space.py:46-48`). The
  necromancer through her body targets anyone but itself, wolves included. A block takes on town and
  wolves only (`night.py:21-24`). There is at most one block per night.
- **L3. A blocker is never blocked in any legal game** (ruled R3). The living chanteuse cannot block
  herself and is never blocked by the necromancer, which needs her dead. The necromancer cannot be
  blocked. So the code's "a blocked blocker still blocks, but makes no visit" (`night.py:135-153`)
  never comes up, and **every block is a visit**, except the one hidden visit in L4.
- **L4. What a watch or follow sees** (`night.py:155-169`, `:221-237`; `night_record.py:137-152`).
  - A visit is every action that went ahead (not blocked) and has a player target. Picks, bets and
    hold_fire are not visits.
  - The necromancer's visit shows the **body's** name.
  - The illusionist's conceal is a visit to the pack's victim whenever the pack's kill went ahead,
    whether or not the victim died.
  - **Hidden (R5): only when the living illusionist concealed the pack's victim**, every visit by the
    pack's carrier to that victim. That covers the kill visit, and also the chanteuse-carrier's block
    or the illusionist-carrier's conceal on the same victim (verified by run). A clean through the
    illusionist's body hides no visit: the carrier, if the pack attacked the same victim, and the
    body's name both stay visible (verified by run).
  - The sentinel never sees its own visit. A carrier can visit two different players (kill plus a
    block on someone else); no other seat ever visits two.
- **L5. Must-act seats.** The pack (every night a wolf is alive), the serial killer, the healer, the
  trailseer, the chanteuse and the fortune teller have no decline word (`roles.py:60-74`;
  `pack.py:146-157`). A failed model turn falls back to a random legal target, not to inaction
  (`agent_player.py:181-196`). A human must name a legal target (`human_turn.py:129-136`) or delegate
  to the agent (`human_turn.py:110-113`).
- **L6. Attacking in one's own name** (the sigil's trigger, `night.py:171-187`): the pack's carrier, the
  serial killer and the vigilante. Not the necromancer (it attacks through a body), and not the
  sigil's own retaliation. A blocked attacker did not attack.
- **L7. Suspicious** (`night.py:239-246`; ruled R1): every wolf, plus the necromancer on a night it made
  a `kill` through the illusionist's or the vigilante's body, whatever came of the kill (killed,
  saved, or immune).
- **L8. Conceal accounting.** The living illusionist and its body draw on one pool of two
  (`resolution.py:57-60`, `:68-72`; `night.py:224-231`). At most one body is concealed per night,
  since the live conceal and the body clean need the illusionist alive and dead respectively. So
  concealed deaths in a game ≤ 2, and after two no role is ever hidden again. The morning tells them
  apart: "hidden by an illusionist" (live) or "hidden by a reanimated illusionist" (body;
  `resolution.py:158`).
  - A live conceal hides only the pack's victim: never a wolf, never the SK (who cannot die at
    night), never the necromancer on night 1.
  - A body clean can hide anyone but the necromancer and the illusionist, **including the chanteuse**.
- **L9. Pack targets and wolf skills** are living non-wolves only (`action_space.py:46-48`). No one else
  targets itself, except the fortune teller's self-bet (`action_space.py:53-57`).
- **L10. One necromancer action per night** (review M2). The necromancer's turn yields one choice with one
  body (`nodes/night/solo.py:59-81`; `resolve.py:242-255`). Any one announced reanimated event on
  night n is therefore its whole night: an attack, a "reanimated sigil", or a "reanimated healer"
  save. It rules out every other reanimated action that night. A reanimated sigil or reanimated save
  also means the necromancer read **Not suspicious** that night (R1).
- **L11. Wills make private results public** (owner note R8). The moment a revealed town player's
  record is read out, every clause in it becomes a public fact for every seat. A record is read
  out at a night death (with the morning report) or a lynch (with the vote result). It covers the
  nights before the death: a night death leaves out its own night
  (`resolution.py:131-133`, `:168-170`; `orchestrator.py:213-215`). Seats reasoning at a turn
  *before* the reveal must not use it (time-indexing). What a clause establishes:
  - A **completed use**: a check, watch, sigil (including "it had no effect"), shot (including at an
    immune target) or protection on that night. These count for C20 even though they were silent
    when made.
  - A **verified sighting**: a watch's or follow's list, with the completeness of L12. Table E may
    compare claims with it as with the seat's own result.
  - A **roleblock** on that night (B22), a **hold_fire** (B23), and every result word, with the
    conclusions of the matching Table A row now public (B15–B23).
  - **Missing nights in a complete will** (review v3 §6). The record is complete: records accumulate
    (`state/orchestrator.py:70-73`, an `add` reducer), and a blocked action still leaves a
    "was roleblocked" clause (`night_record.py:235-241`, `:261-262`). So if the holder survived night
    n (n before its death night) and the will has no clause for night n, the holder **made no choice**
    that night: no completed use and no attempt (it declined; OQ14). That excludes, for night n,
    any completed check, watch or sigil by it, and any visit it made. It also fixes its use count
    exactly for the nights the will covers (C20). Two things it does **not** support: inferring a block (a block leaves its own
    clause), and conclusions for its fatal night, which is never in the will. A missing night for a
    must-act role (healer, trailseer) is an input-integrity error to report, not a deduction.
- **L12. When a sighting list is complete** (review v2 §2). An engine record (the seat's own watch or
  follow, or a will), read through the L14 adapter, lists *every* visit that went ahead. There are two exceptions: a watch never
  lists the watcher itself, and a carrier's visit to a victim the living illusionist concealed is
  hidden from **both** the watch and the follow (`night.py:232-237`, verified by the v2 probe). A
  player's claimed list ("I saw B") is a partial report. It is exhaustive only when the claim says
  so ("only B", "no one else", "no one").
- **L13. Attempted and completed actions** (review v2 §1). A blocked action was chosen but not carried
  out: no visit, no effect, no use spent (`night.py:150-153`; `resolution.py:66-67`). So two
  predicates are kept apart: "selected / tried to act on X" and "the action went ahead on X". A
  claim's wording decides which it asserts. When unclear, read it as the weaker "tried".
- **L14. Normalize records before reading sightings** (review v3 §7). `NightActionRecord.seen` is not
  always a list of observed names. For a necromancer's record, `night_record.py:218-220` puts the
  borrowed **body's** name first (`seen = [via, *seen]`). The investigate and clean records also put
  the target or the learned role in `seen` (`night_record.py:122-135`, `:183-189`). Before any row
  uses a record, an adapter must split each record the receiver holds into separate fields:
  actor, body (if any), target, observed visitors or destinations, and result. For a watch, the
  observed list already omits the watcher (and the body, through a body). Example: an empty watch
  through the sentinel's body has raw `seen = [the body]` and the text "No one visited p1". Read
  raw, it would invent a visitor (verified in code; the v3 probe builds it). The adapter uses only
  the receiver's own records, never the night's hidden choices.

---

## Table A: private results

"Receiver" is who gets the record. A necromancer acting through a body gets the same result word as
the body's role (prefixed "Through Y's body:") and appears in this table under that role, with its
differences noted. Every row assumes the receiver survived the night: a seat that died that night gets
no record of it (`resolution.py:121`). **Self-knowledge is target-aware (review §8):** when the target
is another player, subtract the receiver's own role (and, for a wolf, its allies' roles) using the role
counts. When the target is the receiver itself, use its actual role and actions. Rows that read a
watch or follow list (A26–A35, and every "necro via" variant) read the **normalized** observed list
(L14), never raw `seen`. A "Changed" note
marks rows revised in this version.

| ID | Receiver | Result as told today | Conditions | Certain conclusion | Proposed wording | Interactions / caveats | Code |
|---|---|---|---|---|---|---|---|
| A1 | Healer | `saved`: "Y was attacked by {types}, and your protection saved them." | — | Y was attacked by each listed type that night and was not immune: not the SK; not the necromancer if night 1; not a fortune teller who self-bet that night. Y is not the healer. | "Y was attacked last night and your protection saved them, so Y cannot be the serial killer [SK casts] / the necromancer [NE casts, night 1]." | Add the type-specific rows from B11. | `night_record.py:101-107`; `night.py:200-205` |
| A2 | Healer | `no_attack`: "No attack on Y was announced." | SK+SP | Either no one attacked Y, or Y is the serial killer (an attack on it is silent). | "No attack on Y was announced. Either no one attacked Y, or Y could not be killed at night; in this game only the serial killer cannot." | Never word as "no one attacked Y". | `night_record.py:108-112`; L1 |
| A3 | Healer | `no_attack` | SK+FT | No one attacked Y, or Y is the SK, or Y is the FT and self-bet. | as A2, "…only the serial killer, or the fortune teller on a night it bets on itself, cannot." | | same |
| A4 | Healer | `no_attack` | NE+SP | Night 1: no one attacked Y, or Y is the necromancer. Night ≥ 2: no one attacked Y. | Night ≥ 2: "No one attacked Y last night." Night 1: as A2, naming the necromancer. | | same |
| A5 | Healer | `no_attack` | NE+FT | Night 1: none, or Y is the necromancer or a self-betting FT. Night ≥ 2: none, or Y is a self-betting FT. | as A3, with the cast's roles | | same |
| A6 | Any town seat that chose an action (incl. hold_fire) | `roleblocked` | Chanteuse **not** revealed dead before night n | The chanteuse was alive at the start of night n, visited you and blocked you. She is not among any bodies concealed before night n (if she were, no block could happen). Her visit to you was visible to a watcher at your door. | **Step-1 target (R4):** "You were roleblocked: your action was not carried out. Only the Chanteuse can block in this game, and blocking is a visit, so the Chanteuse, a wolf, visited you that night." | Says nothing about who she is. A body concealed *after* night n could still be her. If she was revealed dead the morning after night n, she still acted that night: same conclusion. **Changed:** wording marked as the step-1 target. | `night_record.py:228-242`; L2, L3 |
| A7 | Any town seat | `roleblocked` | Chanteuse revealed dead before night n (NE casts only) | The necromancer was alive at the start of night n and blocked you through the chanteuse's body. A watcher at your door would have seen the chanteuse's (dead) name. That was its whole night (L10): it made no kill, so it read Not suspicious that night. | **Step-1 target (R4):** "You were roleblocked by the Necromancer acting through the Chanteuse's body (the Chanteuse herself is dead). Its visit shows the Chanteuse's name, not its own." | In SK casts this branch cannot occur. **Changed:** step-1 target; L10 added. | `night.py:53-64`, `:169`; `roles.py:115` |
| A8 | Illusionist (the pack's last wolf) | `roleblocked` on its conceal and on the pack record | Possible only when the chanteuse is revealed dead before night n (NE casts) | The necromancer blocked you through the chanteuse's body. If you were the carrier, the pack's kill did not happen. | **Step-1 target (R4):** "You were roleblocked by the Necromancer through the Chanteuse's body; the pack's kill and your conceal did not happen." | The pack record is filed under `wolves`; only the illusionist can be alive here (review: confirmed no other path). **Changed:** step-1 target. | `night_record.py:235-241`; `night.py:135-153`; verified by run |
| A9 | Vigilante (also necromancer via the vigilante's body) | `killed`, role revealed | — | Public already. | (no injection beyond the record) | | `night_record.py:73-76` |
| A10 | Vigilante / necromancer via a killing body | `killed`, "Their role was concealed." | — | Y was also killed by the wolves with a live conceal (then Y is not a wolf), or by a reanimated wolf with the body's conceal left (NE casts). The morning line says which (B2/B7). | (none needed) | | `night_record.py:74-75`; `night.py:213-231` |
| A11 | Vigilante / necro via a killing body / SK / pack | `saved`: "Y survived: **the healer** saved them." | — | The living healer was alive at the start of night n, unblocked, and protected Y. Y was not immune. | "Y was protected last night by the Healer, who was alive and unblocked that night; Y cannot be the serial killer [SK casts]." | **Changed (R2):** now certain from the wording alone; no census condition needed. | `night_record.py:64-67`, `:77-78` |
| A12 | same | `saved`: "Y survived: **a reanimated healer** saved them." | NE casts only | The necromancer protected Y through the dead healer's body; it was alive at the start of night n and is not Y. That was its whole night (L10), so it made no kill and read Not suspicious that night. | "Y was protected last night by the Necromancer acting through the Healer's body (the Healer is dead)." | **Changed (R2):** the wording now carries this; formerly misleading. | `night.py:276-277`; `night_record.py:64-67`; verified by run |
| A13 | Vigilante, pack | `immune` | SK+SP | Y is the serial killer. | "Y cannot be killed at night. In this game only the serial killer cannot, so Y is the serial killer." | | `night_record.py:79-83`; L1 |
| A14 | Vigilante, pack | `immune` | SK+FT | Y is the SK, or Y is the FT and self-bet that night. Being a wolf adds nothing here; other evidence the seat holds can settle it (the FT budget, C17; a will, L11; the chanteuse's `no_effect`, A41). **Changed (review v2 §3).** | "Y cannot be killed at night: Y is the serial killer, or the fortune teller on a night it bet on itself." | | same |
| A15 | Vigilante, pack | `immune` | NE+SP | Night 1: Y is the necromancer. Night ≥ 2: cannot happen. | "Y was immune on night 1, when only the necromancer is: Y is the necromancer." | | same |
| A16 | Vigilante, pack | `immune` | NE+FT | Night 1: the necromancer or a self-betting FT. Night ≥ 2: Y is the FT, and it has used a self-bet. | as A14, with the cast | | same |
| A17 | SK | `immune` | SK+SP | Cannot happen. | — | | L1 |
| A18 | SK | `immune` | SK+FT | Y is the fortune teller; it self-bet that night. | "Y survived your attack because Y is the fortune teller and bet on itself." | | L1 |
| A19 | Necromancer via a killing body | `immune` | NE+FT (night ≥ 2) | Y is the fortune teller. | as A18 | NE+SP: cannot happen. | L1 |
| A20 | Vigilante | `held` | — | Nothing. | — | | `night_record.py:114-116` |
| A21 | Investigator | `suspicious` | SK casts, any night; NE casts, night 1 | Y is a wolf. | "Y reads Suspicious: Y is a wolf." | | `night.py:239-246`; L7 |
| A22 | Investigator | `suspicious` | NE casts, night ≥ 2 | Y is a wolf, or Y is the necromancer and made a kill through the illusionist's or the vigilante's body that night. **Certainly a wolf** if any one holds: (a) neither of those bodies was revealed dead before night n; (b) that night's announced reanimated event was a **reanimated sigil** or a **reanimated healer** save, or a seat knows of a reanimated block, check, watch or follow (L10); (c) no "reanimated wolf" or "reanimated vigilante" attack was announced that night **and** no silent immune target was possible (NE+SP; or the FT revealed dead before night n). **Certainly the necromancer** if both wolves are revealed dead. | General: "Y reads Suspicious: Y is a wolf, or the Necromancer on a night it killed through a body." Narrowed only when a condition holds. | A reanimated kill on a self-betting FT is silent but still makes the necromancer Suspicious. A concealed body (NE casts) may be a wolf, so "both wolves dead" needs both **revealed**. **Changed (R1, L10):** condition (b) added. | `night.py:244-246`; L1, L8, L10 |
| A23 | Investigator | `not_suspicious` | SK casts | Y is not a wolf. | "Y reads Not suspicious: Y is not a wolf. This does not clear Y of being the serial killer or the [neutral]." | Never "Y is town". | `night.py:239-243` |
| A24 | Investigator | `not_suspicious` | NE casts | Y is not a wolf; and if Y is the necromancer, it made no kill through a body that night. | as A23, "…the necromancer or the [neutral]" | | same |
| A25 | Necromancer via the investigator's body | `suspicious` / `not_suspicious` | NE | Suspicious: Y is a wolf (the only other Suspicious seat is the necromancer itself, which made no kill that night, L10). Not suspicious: Y is not a wolf. | "Y is a wolf." / "Y is not a wolf." | | same |
| A26 | Sentinel (also necro via the sentinel's body) | `seen`, names V | general | Each name in V went to X that night with an action that was carried out (not blocked). A **living** name in V is not the necromancer, not the speculator, not the fortune teller (and not the watcher). | "player_7 went to X last night. A visit shows only that player_7 acted on X, not which action." | The watcher never sees its own visit; through a body, the body's name is also left out of the observed list. Raw `seen` for a borrowed watch starts with the body's name: normalize first (L14; review v3 §7). | `night_record.py:137-144`; L4 |
| A27 | Sentinel / necro | a name D in V of a player **revealed dead before night n** | — | The necromancer acted on X through D's body with D's ability (a dead healer's name = protected X; a dead investigator's = checked X), and was alive at the start of night n. | "Player D was already dead: the Necromancer used D's body to visit X with the [D's role]'s ability." | A name in V of a player who died *on* night n is that player's own visit, made before it died. V is the normalized list (L14): for a necromancer's own borrowed watch, the body it used is never in V. **Changed (review M5):** "dead" means dead before night n. | `night.py:169`; `roles.py:109-118` |
| A28 | Sentinel / necro | V, and the morning says X was attacked by type T (killed or saved), and X was **not** "hidden by an illusionist" (a live conceal) | T = wolves / serial killer / vigilante / reanimated_* | The attacker of each type is in V: the carrier (a wolf) for "the wolves"; the SK; the vigilante; a dead body's name for a reanimated attack. Attackers of different types are different players. If exactly one name in V can be that attacker, that name holds the role. | "The [type] attacked X last night and you saw everyone else who visited X, so the attacker is one of: V. [If one:] player_7 attacked X: player_7 is [a wolf / the serial killer / the vigilante]." | A sigil's retaliation (the sigilist, or a dead sigilist's name) is also a visitor, to the attacker. **Changed (R5):** a victim "hidden by a reanimated illusionist" now qualifies: every attacker's visit is visible. | `night.py:155-187`, `:232-237`; verified by run |
| A29 | Sentinel / necro | V, X was saved | — | The protector is also in V: a living name if the morning said "the healer"; the healer's dead name if it said "a reanimated healer". | "player_3 [or: the Healer's body] protected X." only when the protector is the one name left; otherwise "Someone in V protected X: [the living Healer / the Necromancer through the Healer's body]." | With A28: two living names, one attack by "the wolves", one save by "the healer" → one is a wolf and the other the healer; the line must not say which. **Changed (R2):** the protector's kind now comes from the wording. | same |
| A30 | Sentinel / necro | X killed by the wolves, "hidden by an illusionist" (live) | — | The carrier's visit is hidden. The illusionist (alive at the start of the night) is in V unless it was the carrier. If V has no living name, the illusionist carried the kill. | "The carrier's visit to a concealed victim is hidden. [If no living name:] So the Illusionist carried the kill itself." | Never "no wolf visited X". | `night.py:232-237`; verified by run |
| A31 | Sentinel / necro | X "hidden by a reanimated illusionist" | NE | The illusionist's dead name is in V (the necromancer's clean). If the morning also lists "the wolves", the carrier (a living wolf) is in V too; A28 applies. | "The Illusionist's body went to X: the Necromancer acted through it. [If 'the wolves' too:] The carrier's visit is not hidden by a body's clean, so one of the living names you saw is a wolf." | **Changed (R5):** the carrier is no longer hidden. | `night.py:221-237`; verified by run |
| A32 | Sentinel / necro | "No one visited X", X alive | — | No other visitor was seen at X. Because X survived, no carrier visit was hidden there. Apart from this watch, no visiting action reached X: no attack, protection, check, block, sigil or follow went ahead on X. | "No other visitor was seen at X. Because X survived, no visit there was hidden; apart from your own watch, no one acted on X. This says nothing about where X went or whether X acted." (For a will, name the watcher instead of "your".) | **Changed (review §1):** the old line "No one acted on X" was false; the watcher itself did. | L4; `game_rules.py:66-70` |
| A33 | Trailseer (also necro via the trailseer's body) | `seen`, one name: "Tonight X visited Y." | — | X went to Y with an action that was carried out. X is not the necromancer and not the neutral. | "player_X went to Y. A visit does not show which action." | Through a body, raw `seen` is `[body, destinations…]`: count destinations only after normalizing (L14; review v3 §7). | `night_record.py:146-152`; `night.py:290-297` |
| A34 | Trailseer / necro | two distinct names | — | X is the chanteuse and carried the pack's kill that night. One of the two was the pack's kill target, the other the target of her **block attempt**. The block may have had no effect: on the lone killer or the neutral it does nothing but still visits. | "X visited two players last night. Only a wolf carrying the kill while using its skill visits two, and the Illusionist's conceal goes to the same victim, so X is the Chanteuse; one of the two was the pack's target and the other the target of her block." | If a separate result shows which one was actually blocked (a roleblocked record or will), the other was the pack's kill (C4). **Changed (review v2 §3):** "the other was blocked" overstated; verified by the v2 probe (the block on the speculator: `blocked` empty, two destinations). | L4; `night.py:135-153` |
| A35 | Trailseer / necro | "X visited no one tonight." | — | X is not the serial killer: it must attack, cannot be blocked, and its visit is never hidden. It does **not** mean X did not act: the necromancer always shows "no one"; neutrals never visit; a declined, blocked or hidden-carrier action leaves no trace. X is not the healer unless the healer was blocked. X is not the chanteuse unless she carried the kill, aimed her block attempt at the same victim (it need not take: a neutral victim gives `no_effect`), and the living illusionist concealed that victim. | "X visited no one last night: no visit was made in X's name. In this game that rules out the serial killer; it does not show that X stayed home or did nothing." | **Changed (R5, R6):** the chanteuse exception needs a *live* conceal; wording matches the trailseer card. **Changed (review v3 §5):** a block *attempt* on the victim is enough (verified by the v3 probe: the speculator as victim, `no_effect`, the follow shows no one). | `night.py:155-169`, `:232-237`; L5 |
| A36 | Sigilist (also necro via the sigilist's body) | `hit` | — | Y attacked in its own name that night and died (role public). If Y's role is concealed: live conceal → Y is the vigilante; body clean → Y is the carrier wolf or the vigilante. | "Your sigil struck Y: Y attacked someone last night." (+ the concealed case) | | `night_record.py:155-159`; L6 |
| A37 | Sigilist / necro | `saved`, "…but the healer's / a reanimated healer's protection saved them" | — | Y attacked someone in its own name that night and was protected: Y was the pack's carrier (a wolf) or the vigilante who shot. Y is not the SK. If the vigilante was revealed dead before night n, Y is a wolf. The protector is the living healer or the necromancer, per the wording. | "Y attacked someone last night, so Y is a wolf (that night's carrier) or the vigilante." | No "shot by the vigilante" line does not rule the vigilante out (the shot may have hit an immune target). **Changed (R2):** the saver is named. | `night_record.py:165-170`; L6 |
| A38 | Sigilist | `miss` | SK casts | Y did not attack in its own name that night, **or** Y is the serial killer (an immune attacker reads the same). | "Your sigil had no effect: either Y did not attack last night, or Y is the serial killer." | Never "Y did not attack". | `night_record.py:160-164`, `:171-173` |
| A39 | Sigilist / necro via the sigilist's body | `miss` | NE casts | Y did not attack in its own name: Y was not the pack's carrier (or the carrier was blocked) and did not shoot as the vigilante. Y may be the necromancer. | "Your sigil had no effect: Y did not attack in its own name last night (the Necromancer's attacks through bodies do not count)." | | same |
| A40 | Chanteuse | `blocked`: "Y was roleblocked tonight." | — | Y is on the town side. | "Y is on the Town side." | Y may not have acted (blocked is reported whether or not Y acted). | `night_record.py:175-178`; L2, L9 |
| A41 | Chanteuse | `no_effect` | — | Y is the lone killer or the neutral. If the pack has an `immune` result on a player known to be the SK (A13), and Y is not that player, Y is the neutral. | "Y is the [lone killer] or the [neutral]." | | `night_record.py:179-181`; `night.py:21-24` |
| A42 | Necromancer via the chanteuse's body | `blocked` | NE | Y is town or a wolf. | "Y is town or a wolf." | | same |
| A43 | Necromancer via the chanteuse's body | `no_effect` | NE | Y is the neutral (it cannot target itself; there is no SK in the cast). | "Y is the [speculator / fortune teller]." | | same |
| A44 | Illusionist | `concealed`, role R | — | The concealed body was R. The other wolves read only "Their role was concealed". | "The body you concealed was the R." | Private to the illusionist. | `night_record.py:183-189` |
| A45 | Illusionist | `no_body` | — | The pack's target did not die. If a save on it was announced, it was protected; if nothing was announced, it was immune (L1, per cast). The conceal was not spent. | "The pack's target survived. [No save announced:] It was immune: [cast list]." | | `night_record.py:190-192` |
| A46 | Every living wolf (pack record) | killed / saved / immune | — | As A9–A16 for the pack's target. | as those rows | | `night_record.py:118-121` |
| A47 | Necromancer via the illusionist's body | clean: "Y died, and you hid their role: they were R." | — | Y was R. | (already explicit) | | `night_record.py:122-126` |
| A48 | Necromancer via the healer's body | `saved` / `no_attack` | NE | Saved: as A1. No attack: no one attacked Y, or Y is a self-betting FT (NE+FT). NE+SP: no one attacked Y. | as A4 / A5 | | `night_record.py:101-112` |
| A49 | Fortune teller | `scored_2` on a concealed victim | — | The concealed body was the named role. | "The concealed body was the R." | | `night_record.py:206-208`; `night.py:254-260` |
| A50 | Fortune teller | `scored_1` with a role named, victim concealed | — | The concealed body was not the named role. | "The concealed body was not the R." | | `night_record.py:209-213` |
| A51 | Fortune teller | `missed` / `self_bet` | — | Missed: public. Self-bet: nothing about whether it was attacked. | — | Never infer an attack or its absence **from the self-bet record alone**. The attacker does know (A14, A16, A18, A19). **Changed (review §9).** | `night_record.py:199-216` |
| A52 | Speculator | `picked` | — | Nothing beyond the pick. | — | | `night_record.py:194-197` |

---

## Table B: public events (certain for every seat)

| ID | Announcement (as worded) | Conditions | Certain for every seat | Code |
|---|---|---|---|---|
| B1 | "X was killed by the wolves last night. They were a R." | — | X was not a wolf and not immune that night. A wolf was alive at the start of night n and was not blocked. The carrier's visit to X was visible. No protection reached X. | `resolution.py:162-167`; `action_space.py:46-48` |
| B2 | "X was killed by the wolves last night. Their role is hidden by an illusionist." | — | X was not a wolf, not the SK, not immune that night; on night 1 not the necromancer. A wolf was alive and unblocked. No protection reached X. The illusionist was alive at the start of night n and spent a conceal (L8). **The carrier's visit to X is hidden** (L4). X has no will. | `resolution.py:155-161`; `night.py:213-220`, `:232-237`. **Changed (review §3):** no longer "as B1", which imported a visible carrier visit. |
| B3 | "X was stabbed by the serial killer…" | SK casts | X is not the SK. The SK acted (it is alive until lynched). The SK's visit to X was visible. | `resolution.py:32` |
| B4 | "X was shot by the vigilante…" | — | The vigilante was alive at the start of night n and unblocked. X is not the vigilante. | `resolution.py:33` |
| B5 | "X was struck down by a sigil… They were a R." | — | X attacked in its own name that night, so R is the chanteuse, the illusionist or the vigilante. The sigilist was alive at the start of night n and unblocked. If R is a wolf, X was that night's carrier, so the pack attacked someone; if no wolf attack was announced, the pack's target was immune (L1). If R is the vigilante, it shot someone; if no vigilante attack was announced, the target was immune. | `night.py:182-187`; L6 |
| B6 | "X was killed by a reanimated wolf… They were a R." | NE casts, night ≥ 2 | The illusionist was revealed dead before night n. The necromancer was alive at the start of night n, is not X, and read Suspicious that night (L7). That was its whole night (L10). The illusionist's body had **no conceals left**, otherwise X would be hidden. | `night.py:113-119`, `:224-231`; `resolution.py:57-60` |
| B7 | "…killed by a reanimated wolf… Their role is hidden by a reanimated illusionist." | NE | The illusionist was revealed dead before night n. The necromancer was alive at the start of night n, is not X, read Suspicious that night, and that was its whole night. **The body had a conceal left and has now spent one** (L8). X is not the necromancer and not the illusionist; X **may be a wolf**. No visit to X was hidden (R5). | `resolution.py:158`; verified by run. **Changed (review §3, R5):** no longer "as B6", which imported "no conceals left"; visits now visible. |
| B8 | "X was shot by a reanimated vigilante…" | NE | The vigilante was revealed dead before night n. The necromancer was alive, is not X, read Suspicious that night, and that was its whole night. | `night.py:244-246` |
| B9 | "X was struck down by a reanimated sigil…" | NE | The sigilist was revealed dead before night n. X attacked in its own name: the carrier (a wolf) or the vigilante. The necromancer acted, read **Not suspicious** that night (R1), and made no other action (L10). | `night.py:186`; verified by run. **Changed (R1):** certain now. |
| B10 | "X was attacked by A, B [and C] last night…" (several types) | — | Each type is a different attacker. **the wolves + a sigil** → X is the vigilante, even when concealed (X is not a wolf, attacked in its own name, not the SK). **the vigilante + a sigil** → X is a wolf (that night's carrier). **a reanimated vigilante + a sigil** → X is a wolf. **the serial killer + a sigil** → X is a wolf or the vigilante. **a reanimated wolf + a sigil** → X is a wolf or the vigilante. | `resolution.py:145-157`; verified by run |
| B11 | "X was attacked by {types} but was saved by **the healer**!" | — | The **living** healer was alive at the start of night n, unblocked, and protected X. X is not the healer and was not immune that night (not the SK; not the necromancer on night 1; not a self-betting FT). By type: "the wolves" → X not a wolf; "a sigil" → X attacked in its own name (carrier wolf or vigilante); "the wolves and a sigil" → X is the vigilante. | `resolution.py:147-151`. **Changed (R2):** certain from the wording, any cast. |
| B12 | "X was attacked by {types} but was saved by **a reanimated healer**!" | NE | The healer was revealed dead before night n. The necromancer was alive at the start of night n, protected X through the healer's body, and is not X. That was its whole night (L10): it made no reanimated attack, sigil, block, check, watch or follow, and read **Not suspicious** that night. The type rows of B11 apply. | `night.py:276-277`; `resolution.py:150`; verified by run. **Changed (R2):** new wording. |
| B13 | (nothing about an attack on an immune player) | — | Absence lines, each needing the actor alive at the start of night n and a complete morning report (review M5). **SK+SP, SK alive:** every night has an SK attack line. **SK+FT, SK alive:** a night with no SK line means the SK's target was the FT on a self-bet. **Pack, a wolf alive** (not always public in NE casts, L8): a night with no wolves line means the target was immune (L1), or the carrier was blocked (NE only, chanteuse revealed dead before night n). In SK+SP, no wolves line means the pack attacked the SK. | L1, L5; `resolution.py:139-142`. **Changed (review M5):** the SK-alive condition is explicit. |
| B14 | "No one died last night." | — | No attack that night killed or was saved. Every attack (if any) was on an immune target, or the pack's carrier was blocked. In SK+SP this cannot happen while the SK lives. | `resolution.py:174-175` |
| B15 | Will clause "protected Y; no attack on them was announced" | — | As A2–A5, for that night. | `night_record.py:263-266` |
| B16 | Will "shot Y, who was unharmed" | — | Y was immune that night: SK+SP → Y is the SK. NE+SP → night 1 → the necromancer. SK+FT / NE+FT: as A14 / A16. | `night_record.py:269-274`; verified by run |
| B17 | Will "shot Y, who was saved" / "who died" | — | Saved: as B11/B12, whichever that night's line said. Died: public. | same |
| B18 | Will "checked Y: Suspicious / Not suspicious" | — | As A21–A24, now public. | `night_record.py:275-278` |
| B19 | Will "watched Y; saw A and B visit them" / "saw no one" | — | As A26–A32, now public, worded with the dead watcher's name. A living named visitor is not the necromancer and not the neutral. The list is complete except for the watcher itself and a hidden carrier visit (L12), so Table E may treat it as exhaustive. | `night_record.py:279-282`. **Changed (L11, L12).** |
| B20 | Will "followed Y; they visited Z" / "visited no one" | — | As A33–A35. The list of Y's visits is complete except for a hidden carrier visit (L12). | `night_record.py:283-286`. **Changed (L12).** |
| B21 | Will "set a sigil on Y, who attacked and was saved" / "it had no effect" | — | As A37 / A38–A39. | `night_record.py:287-292` |
| B22 | Will "night n, was roleblocked" | — | As A6/A7: on night n the chanteuse (or, if she was revealed dead before night n, the necromancer through her body) went to this player. The player had chosen an action, possibly hold_fire. | `night_record.py:261-262` |
| B23 | Will "held fire" | — | The vigilante did not shoot that night. | `night_record.py:267-268` |
| B24 | A revealed town role with no will | — | It had no record on any earlier night: it died on night 1, or it declined every action it was offered (only roles with a decline word; the vigilante's hold_fire is recorded). Healer and trailseer have wills if they lived through a night. **No will is not evidence of a non-town role or of a false claim.** | `night_record.py:296-312`; L5 |
| B25 | "Player X has been voted out and was a R." (+ will if town) | — | R is X's role (a lynch is never concealed). A town will contains the records X received on completed nights; declined checks, watches and sigils leave no entry (B24). If R is in `BORROWED_ABILITY` (a town role, the illusionist or the chanteuse), X's body is usable by the necromancer from night n (the day-n lynch precedes it; the necromancer acts from night 2). A lone killer's or a neutral's body gives nothing. | `orchestrator.py:205-215`; `roles.py:109-118`; `night.py:53-64`. **Changed (review v2 §3).** |
| B26 | "The Speculator has picked {side}." | SP casts | The speculator was alive at the start of that night (it may have died that night). The pick is final; there will be no other pick announcement. | `resolution.py:177-180`; `orchestrator.py:446-456` |
| B27 | Speculator revealed dead, no pick ever announced (including the morning after a night death) | SP | It never picked and has lost. | `orchestrator.py:356-359` |
| B28 | Fortune teller: no per-night announcement | FT | Nothing (bets and points are private until game end). | `resolution.py:124-129` |
| B29 | The alive-roles census line | — | Cast minus revealed dead. "(one of these is dead: a body whose role is hidden)" also applies, and L8 narrows which roles a hidden body can be. | `prompt_formatters.py:46-75` |
| B30 | Vote records / no-lynch lines | — | Who voted for whom. No role conclusion. | `orchestrator.py:198-257` |
| B31 | Game over lines: winner, and the neutral's result | — | Two endings, kept apart. **An ordinary end:** the winner's condition held at that check (C18), or "No side is left standing" (a draw). **The day limit** (`max_days`, 12 by default, not in any prompt): the largest surviving side wins (a tie is a draw, worded "The day limit was reached"), **whether or not its ordinary condition holds**. A day-limit winner is worded exactly like an ordinary win, so a winner line alone does not prove the ordinary condition. "The [neutral] won/lost (N points)" gives the fortune teller's final score. | `orchestrator.py:330-340`, `:376-416`. **Changed (review v2 §3):** a day-limit winner need not meet its ordinary condition (verified by the v2 probe). |
| B32 | A town will read out (any clause) | From the moment of the reveal only | Every clause becomes public (L11). Completed uses enter C20's public count. Sightings become verified evidence for Table E. Each clause's Table A conclusions become public conclusions (B15–B23). A missing night the holder survived means it made no choice that night (L11): no completed use, no visit. It never means it was blocked, and the fatal night is never in the will. **Changed (review v3 §6):** formerly "a missing night is not evidence", too broad. | `night_record.py:296-312`; L11. **New (R8).** |

---

## Table C: what a solver would derive (constraints, not instances)

| ID | Constraint | Derives | Code / basis |
|---|---|---|---|
| C1 | **Census with hidden bodies.** Cast minus revealed dead, with each hidden body restricted by L8. A body hidden "by an illusionist" is a non-wolf, non-SK (and not the necromancer on night 1). A body hidden "by a reanimated illusionist" is anything but the necromancer and the illusionist. | When every non-revealed copy of a role is accounted for, its count is exact. | `board_clocks.py:95-111`; L8 |
| C2 | **Immune set, narrowed, target-aware** (review §8). L1, minus roles revealed dead *before night n*. For a target other than the receiver, also minus the receiver's own role and its known allies. For the receiver itself, its actual role decides. | When one candidate is left, an `immune` result (A13–A19) or a will's "unharmed" (B16) names that role. A will's immune target may be the receiving FT itself: then it learns no new role identity, though it may learn, from the vigilante's will, that it was attacked on a self-bet night (its own record never said so; OQ10; review v3, small corrections). | L1. **Changed (review §8).** |
| C3 | **Suspicious set, narrowed.** SK casts: Suspicious = wolf. NE casts: as A22, with L10. | Both wolves revealed dead → a Suspicious read is the necromancer. No killing body usable → Suspicious = wolf. A reanimated sigil, save or (known) block / check / watch / follow that night → Suspicious = wolf. | L7, L10. **Changed (R1).** |
| C4 | **Blocker identity.** Fixed by whether the chanteuse was revealed dead before night n (A6/A7). One block per night. | A block also proves she was not a hidden body from before night n. A known block target plus a two-door chanteuse follow (A34) shows which door was the kill (review M2). | L2 |
| C5 | **Use counts, standard configuration only** (review §10). Public limits (from the cards): checks ≤ 2, watches ≤ 2, sigils ≤ 2, conceals ≤ 2, self-bets ≤ 2, picks ≤ 1. Count only *completed* uses by the living role: a blocked attempt spends nothing; one night reported twice is one use; uses through a body do not spend the dead role's budget (except the illusionist's conceals). Concealed deaths ≤ 2 in all. The vigilante's bullet count is **not public** (OQ17). | A claim to have made three distinct completed checks, watches or sigils **as the living investigator, sentinel or sigilist** is false. A necromancer can truthfully report more through a body (review v2 §1). After two concealed deaths, no role is hidden again. Remaining counts: C20. | `config/game.py:30-43`; `resolution.py:49-73`. **Changed (review §10, review v2 §1).** |
| C6 | **Attacker at the door.** A watch or will listing the visitors to X, plus a morning attack of type T on X (not "hidden by an illusionist"), means the T-attacker is among the visitors (A28). Different types are different players. A save adds the protector, of the kind the wording names (A29). | With one unaccounted name, an identity. Example: SK+SP, "X was stabbed by the serial killer", the watch saw only player_7 → player_7 is the SK. | L4. **Changed (R5):** a reanimated clean no longer exempts. |
| C7 | **Two visits = Chanteuse carrier** (A34). | Identifies the chanteuse and that night's carrier. | L4 |
| C8 | **Carrier rotation.** The carrier on night n is the living wolves in seat order, index (n−1) mod count. | If a known wolf was that night's carrier (B5, A34, A37) and two wolves were alive, the other wolf's seat is above it (n odd) or below it (n even). | `night.py:37-44` |
| C9 | **Eliminations from attacks and saves.** A player announced as attacked is not the SK, and not the necromancer if it was night 1. Saved means not the healer. Attacked by the wolves means not a wolf. Attacked by a sigil means a wolf or the vigilante. | Accumulates per living player across nights. | B11, B12 |
| C10 | **Visitors are never the necromancer or a neutral.** This applies to any living name seen going somewhere (in a will, or the seat's own watch or follow). | Narrows who the lone killer and the neutral can be. | L4 |
| C11 | **Absence lines** (B13, B14), with the actor alive at the start of night n. | SK+SP: no wolves line with wolves alive → the pack hit the SK. NE+SP, night ≥ 2, no wolves line, a wolf alive → the carrier was blocked by the necromancer through the chanteuse's body (needs her revealed dead), else impossible. | L1, L5 |
| C12 | **Must-act roles and visits.** The SK always visits; the healer, trailseer and chanteuse visit unless blocked or hidden (A35). | A follow showing "no one" excludes the SK. | L5 |
| C13 | **Speculator lifecycle.** A pick means it was alive that night. Dead with no pick means it lost. A claimed pick must match the announced side and night. | Claim checks (Table E). | B26–B27 |
| C14 | **The chanteuse's split** (wolves only). `no_effect` targets are the lone killer or the neutral (A41). The pack's `immune` target in SK+SP is the SK. | Combined, the wolves can name both the SK and the neutral. | A41, A13 |
| C15 | **Town wills.** Every revealed town death publishes whatever records it had received (B24). A living claimant's account can be checked against every will that saw them. | Contradictions only, worded per line (Table E). | `night_record.py:296-312`. **Changed (review §5):** no longer claims every death has a will. |
| C16 | **One necromancer action per night** (L10). | A reanimated save, sigil or attack on night n excludes every other reanimated action that night. It also excludes any claim that the necromancer did something else that night. A reanimated save or sigil makes that night's Suspicious reads wolves. | `solo.py:59-81`. **New (R1, R2, review M2).** |
| C17 | **The fortune teller's self-bet budget** (review M3). Two self-bets in the standard configuration; several attacks on one night use one. | SK+FT: a player known (to the receiving seat) to have been immune on three distinct nights is the SK. NE+FT: an immune result after night 1 names the FT and uses one of its self-bets; after two such nights, it has none left, so a further immune result after night 1 is impossible. | `config/game.py:41-42`; L1. **New.** |
| C18 | **Joint assignment and game continuation** (review M4, M6). (Continuation is safe to use: the day limit only ends a game, it never continues one. A game's *end* proves the ordinary condition only when it was not the day limit, B31.) One copy of each dealt role over living players and hidden bodies, across all nights. If two players can only be the healer or the trailseer, no one else is either. The game ends when `determine_winner` holds at the checks after the day and after the night. While it continues, the role assignments that would have ended it are ruled out, but only after that phase's check, not mid-phase. A seat's private knowledge of hidden roles (illusionist, necromancer, FT) goes into its own assignments, never the public's. | A result is certain only when every consistent assignment agrees. Zero consistent assignments means an input or rule error, to be reported, not a basis for a "certain" line. | `orchestrator.py:310-327`, `:419-430`, `:505-516`. **New.** |
| C19 | **Neutral objectives** (review M6). The FT's win is secured once it holds 2 points (private; kept after death). The speculator's objective is fixed at its picked side, alive or dead. | Private lines for those seats only. | `orchestrator.py:350-373`. **New.** |
| C20 | **Public use accounting** (owner, 2026-10-16; refined by review v2 §2 and R8). The public starting limits (standard configuration, from the cards) are: sigils 2, conceals 2 (one pool for the illusionist and its body), self-bets 2, checks 2, watches 2, one pick. Bullets are not public (R7). **Exact counts** after a complete morning report: conceals left = 2 − the distinct deaths announced as hidden (by an illusionist or a reanimated illusionist). Every spent conceal hides exactly one death, and a conceal that hid nothing spends nothing (`resolution.py:57-60`, `:68-69`). The speculator has its pick until one is announced, then none. **Bounds for the rest:** left ∈ [S − U_max, S − U_min]. U_min is the uses of the *original living role* that are publicly established, distinct and completed. U_max is the most it could have made (one per night it was alive and could act, at most S). The count is exact only when they meet. A use is publicly established by: a death or save by "a sigil" (one sigil); a will's clause (L11: a check, a watch, a sigil including "it had no effect", a self-bet only by deduction); or a sound deduction (C17: immune nights after night 1 in NE+FT establish self-bets). One actor, resource and night counts once even when a death line and a later will both show it. Borrowed actions do not spend the dead role's own budget (a "reanimated sigil" spends no sigil), **except** that a clean through the illusionist's body spends one conceal from the shared pool (`resolution.py:55-60`; review v3 §2). A complete will with no clause for a night the holder survived fixes that night's use at zero (L11), so the bounds can close. **Who is told the exact count:** the holder (`uses_remaining`, a seat event), and the necromancer, whose payload and prompt carry `body_conceals` (the illusionist's conceals left; `solo.py:51`, `prompts/roles/necromancer.py:89`), which equals the public exact count above. | Public: the exact conceal and pick counts; the bounds for the rest. A claim of more uses than S − U_min left is false. A claim of a further completed use by the original role beyond its limit is false. A vigilante shot shows that a bullet was used, never how many remain. | `resolution.py:49-73`; `server/schemas/events.py:528`, `:647`; `night.py:182-187`, `:213-231`. **Changed (review v2 §2, R7, R8):** formerly 'only an announced use lowers the public count' and 'only the holder is told'; both too strong. |
| C21 | **Wills as evidence, from the reveal on** (R8, L11). Each clause of a read-out town record is a public, engine-certified fact about its night. | Silent uses become public (C20). Sightings become verified, complete lists (L12) that claims can be checked against (Table E). An earlier "unharmed" shot or Suspicious check gets the cast-resolved conclusions of B16 / B18. A roleblock clause places the chanteuse or her body at that door (B22). Seats reasoning before the reveal, and frozen replays of turns before it, must not use any of this. | `night_record.py:296-312`; `resolution.py:131-133`. **New (R8).** |

---

## Table D: what the public can know about evil and neutral seats

Three different kinds of contradiction are kept apart (review §7):
- **Impossible for the true role.** Only the seat itself knows; never a public statement.
- **Incompatible with a role the player claimed.** E.g. "I am the FT" + "I was roleblocked".
- **Contradicted by public facts.** An announcement, the dead roster, a will, or the census.

Counter-claims and missing counter-claims are neither.

| Seat | What the public can deduce about it | Claims incompatible with a role it claims | Claims contradicted by public facts |
|---|---|---|---|
| Chanteuse | She goes somewhere every night (L5), unless she carried the kill and aimed her block attempt at the same victim, which the living illusionist then concealed (review v3 §5: the block need not take). She is Suspicious. She is never killed by the wolves and never announced as saved from the wolves. A will showing a block on night n means she (or her body) went to that player. Two visits on one night identify her (A34). | Claiming the healer while saying she was "attacked by the wolves and saved". Claiming the SK, necromancer or a neutral while saying she was roleblocked. | A role revealed dead with no hidden bodies; being a named visitor in a will while claiming a neutral (C10); "I went nowhere on night n" when a will saw her go somewhere. |
| Illusionist | Suspicious. Never a pack victim. Goes to the pack's victim whenever it conceals, unless it carried and concealed (then it is invisible there). | As the chanteuse. | As the chanteuse. |
| Serial killer | Never dies at night, never saved, never announced as attacked (C9). Goes somewhere every night (A35). Reads Not suspicious. A vigilante's will saying "unharmed" names it in SK+SP (B16). | Claiming any town role and saying it was roleblocked is fine for a town claim; "I am the SK and was roleblocked" is incompatible. | "I was saved" on a night it says it was attacked (an SK save is never announced; any announced save names someone else). "I went nowhere on night n" when a will saw it go to its victim. A claim that someone came to it is **not** contradicted by its victim's watcher (review §6). |
| Necromancer | Immune on night 1: no night-1 death or save is it. From night 2, the reanimated lines show that it acted, through which body, and that it did nothing else that night (L10), not who it is. It never appears under its own name, and a follow on it always shows "no one". It reads Suspicious only on a night it killed through a body (R1). | "I am the healer and I saved X" on a night X was "saved by a reanimated healer": a living healer did not make that save. A claim "I protected X through the healer's body" (a necromancer claim) stays compatible (review v2 §1; the ledger now agrees, OQ18 resolved). | A claimed role whose holder is revealed (census). A claimed outgoing visit that a will contradicts. It can report a true borrowed result (e.g. a watch) only after the body's role was revealed, so the census already shows that role dead (review §7). |
| Speculator | Alive on the night of its pick. Never goes anywhere (C10). Cannot be blocked. | "I am the speculator and was roleblocked"; a speculator claim with a pick that differs from the announcement. | A pick claim that differs from the announced side or night; claiming the speculator while named as a visitor in a will. |
| Fortune teller | Possibly immune on any night it had self-bets. Public facts, C17, a will (L11) or a seat's own evidence can rule that out (review v2 §3). Never goes anywhere. Cannot be blocked. | "I am the FT and was roleblocked." | Claiming the FT while named as a visitor in a will. |

---

## Table E: comparing claims (specification; review M1, revised by review v2 §1)

**Status:** a specification, in scope under R9 (comparisons of claims with each other and with the
record are part of the coverage the owner ruled in). Built as level 6 of the build order (Rendering).

**How comparisons work.** Comparisons are typed: they run over source-qualified facts and claims, never
over text matching. Every fact carries its source (announcement, own record, will, dead roster) and
its night. Every claim carries its claimant, night, action, target, result and sighting, plus three
flags:
- whether it asserts an attempt or a completed action (L13);
- whether a sighting list is exhaustive (L12);
- whether it is the claimant's latest version.

A withdrawal changes the claim's current status but stays in the public history. **Each comparison
declares the fields it needs** (review v3 §3). It returns "insufficient information" only when *those*
fields are missing:
- An unknown night blocks only comparisons that join on a night. "Roleblocked" against an
  unblockable claimed role (E6) needs no night.
- A partial sighting ("I saw p7 at p5", `result = not_said` with a non-empty `seen`) still supports
  positive corroboration (E1, E13) and contradiction with an explicit denial (E2b, E2c).
- Only a deduction from an **omitted** name needs an exhaustive list (E3a, E6b; L12).

**What a comparison can say.**
- Every line is hedged where it stands.
- Two incompatible claims mean they cannot both be true, **not** which claimant is false.
- A false claim does not prove an evil role: any player may bluff.
- A missing counter-claim reserves no role, and neither does a withdrawn one.
- Comparisons use the latest version of each claim (the ledger keeps corrections with their history
  since the OQ16 fixes).

| ID | Comparison | Certain reading | Proposed wording | Basis |
|---|---|---|---|---|
| E1 | A sighting "A came to X on night n" (claimed, or verified) + A's claim "I went to X on night n" | Consistent. Says nothing about A's action or role. | By source. Claim: "player_2 claims to have seen player_7 come to player_5; player_7 says they went to player_5. These agree; neither shows which action player_7 performed." Will or own record: "[player_2's will / your watch] shows player_7 came to player_5, as player_7 says; it does not show which action." | L4. **Changed (review v3, small corrections):** the source is kept in the wording. |
| E2a | "A came to X on night n" + A's claim "I went to Y (≠ X)" that night, **not** stated as exclusive | Both can be true only if A visited two players that night, which only the Chanteuse carrying the kill does. | "These can both be true only if player_7 visited two players that night, which only the Chanteuse does when she carries the pack's kill." | A34. **Changed (review v2 §1).** |
| E2b | "A came to X on night n" + A's claim "I went only to Y" or "I did not go to X" | Incompatible: they cannot both be true. | "player_2's sighting of player_7 at player_5 and player_7's statement that they did not go to player_5 cannot both be true." | L4. **New (review v2 §1).** |
| E2c | "A came to X on night n" (A a living name) + A's claim "I went nowhere" that night | Incompatible: two visits cannot explain it. | "player_2's sighting of player_7 at player_5 and player_7's statement that they went nowhere that night cannot both be true." | L4. **New (review v2 §1):** formerly merged with E2a, which wrongly offered the Chanteuse as an explanation. |
| E3a | A follow "A went to X" + a watch at X whose list leaves A out | If the watch list is exhaustive (an engine record, a will, or a claim saying "only" / "no one else"): both can be true only if **A is the watcher** (a watch omits the watcher's own visit). A live conceal cannot explain it: it hides the carrier's visit from both the watch and the follow. If the watch list is a partial claim ("I saw B"): no contradiction. | Exhaustive, A ≠ watcher: "These two reports cannot both be true." A = watcher: "These agree: a watch never lists the watcher's own visit." Partial: no line, or "player_2 did not say they saw everyone." | L12; `night_record.py:137-144`; `night.py:232-237`; v2 probe. **Changed (review v2 §1):** the conceal exception was wrong. |
| E3b | A follow of A (exhaustive) "A visited only Y" or "no one" + a sighting of A at X ≠ Y | Incompatible: a follow lists every visit A made that went ahead, and a hidden carrier visit is hidden from both. | "These two reports cannot both be true." | L12. **New.** |
| E4a | A claim "I tried to protect X on night n" + X died that night | Consistent only if the protection was blocked. | "If player_3 chose to protect X that night, X could have died only if player_3 was roleblocked." | L13; `night.py:189-205` |
| E4b | A claim that the protection *went ahead* on X + X died that night | Incompatible. | "A protection that went ahead on X would have stopped every attack that night; X died, so these cannot both be true." | L13. **Changed (review v2 §1):** attempt and completion split. |
| E5 | A claimed protection of X on night n + the save line | "saved by the healer": consistent with a living-healer claim. "saved by a reanimated healer": the save was made by the necromancer through the dead healer's body. A claim to be the living healer who saved X is incompatible. A claim to have protected X through the healer's body stays compatible. | "X was saved that night by the Necromancer acting through the dead Healer's body; it was not saved by a living Healer." | R2. **Changed (review v2 §1):** "a living player did not make that save" was false (the necromancer is living). Ledger: OQ18. |
| E6 | "I was roleblocked" + a claimed role of SK, necromancer, speculator or FT | Incompatible pair: those roles cannot be blocked. | "The [role] cannot be roleblocked, so these two claims of player_X's cannot both be true." | `night.py:21-24` |
| E6b | "I was roleblocked on night n" + a verified, complete watch on the claimant that night (L12) | The blocker's visit cannot be hidden on a living claimant. If the watch shows no living name and no dead chanteuse's name: incompatible. If exactly one name could be the blocker: if the claim is true, that player is the chanteuse (or, if her body is the name, the necromancer acted). | "If player_3 was roleblocked that night, the Chanteuse came to them, and the only visitor seen was player_7." (never "player_7 is the Chanteuse" as a certainty) | L2, L4. **New (review v2 §1).** |
| E7 | A claimed check result + Y's revealed role | "Suspicious" + Y revealed town, neutral or SK: incompatible. "Not suspicious" + Y revealed a wolf: incompatible. "Suspicious" + Y revealed the necromancer: consistent only if it killed through a body that night (B6, B8; A22). "Not suspicious" + necromancer: consistent unless it killed through a body that night. | "player_4 says Y read Suspicious; Y was revealed as a [role], who reads Not suspicious." | L7. **Changed (review v2 §1):** SK and wolf cases added. |
| E8a | A claim "I tried to shoot Y on night n" + no **matching** attack on Y announced | The matching line depends on the mechanism the claim states. **As the living vigilante** ("the vigilante"): no such line means the shot was blocked or Y was immune (L1, per cast). **Through the vigilante's body** ("a reanimated vigilante"): no such line means Y was immune; the necromancer cannot be blocked. **Mechanism unstated:** keep both branches. A "reanimated vigilante" line on Y means a borrowed shot went ahead, so the absence of an ordinary vigilante line proves nothing about it. | Living vigilante: "If player_7 shot at Y as the Vigilante that night, either player_7 was roleblocked or Y could not be killed ([cast list])." | L1, L13; `night.py:113-119`; `resolution.py:29-37`. **Changed (review v3 §1):** verified by the v3 probe (p1 killed through the vigilante's body, `reanimated_vigilante`, nobody blocked). |
| E8b | A claim that the shot *went ahead* + no attack on Y announced | Consistent only if Y was immune. Attack type depends on the claimed actor: a living vigilante's shot reads "the vigilante"; a shot through the vigilante's body reads "a reanimated vigilante". | "If player_7's shot went ahead, Y could not be killed at night ([cast list])." | L1, L13; `night.py:113-119`. **Changed (review v2 §1).** |
| E9 | A claimed sigil "hit" or "saved" on Y + the announcements | A living sigilist's hit or save needs a "sigil" attack on Y that night; one through the body needs a "reanimated sigil". Without the matching line: incompatible. | "No [reanimated] sigil attack on Y was announced that night." | B5, B9, B11 |
| E10 | A claimed speculator pick + the announcements | Must match the side and the night. | "The Speculator's pick was announced as [side] on the morning after night n." | B26 |
| E11 | A claim of a third completed check, watch or sigil **as the living role** | False under the standard configuration. A necromancer's borrowed uses are not limited. | "The [role] has 2 [checks] for the whole game." | C5. **Changed (review v2 §1):** applies only to the original living role. |
| E12 | A claimed sighting or result + a will from the same night | The will is engine fact with complete lists (L12); compare as in E1–E3, E7. | as E1–E3, citing the will | L11, C21 |
| E13 | **The seat's own verified result corroborates part of a claim.** E.g. the sentinel saw player_8 come to player_2; player_8 claims healer and says it protected player_2. | Only the visit is confirmed: player_8 went to player_2 with an action that went ahead. Neither the role nor which action is confirmed. | "Your watch confirms that player_8 went to player_2 that night. It does not confirm that player_8 is the Healer or that the visit was a protection." | L4, A26. **New (review v2 §1; the healer/sentinel case).** |
| E14 | A claimed action that could not legally happen | Incompatible with the claimed role if: the necromancer acting on night 1; the actor dead before night n; the target dead before night n; a body not usable (not yet dead, hidden, or no ability); the original role out of publicly established uses (C20); a self-target other than the FT's self-bet; the healer protecting itself; the living chanteuse blocking a known wolf (wolves only). | "The [role] cannot [act] [reason]; this claim cannot be true as stated." | L2, L9, C20; `orchestrator.py:446-459`. **New (review v2 §1).** |
| E15 | Counter-claims, withdrawals, no claim | Status only: "player_3 and player_8 both claim the healer; at most one holds it" (only when the role count is 1). A withdrawal: "player_8 claimed healer on day 2 and withdrew it on day 3." No claim: nothing follows. | as stated | C18. **New (review v2 §1).** |
| E16 | A comparison whose required field is missing (night, target, result or an exhaustive list, per the preamble) | That comparison only returns "insufficient information"; other comparisons on the same claim still run. | "player_X did not say which night, so this cannot be checked against that night's record." | **New (review v2 §1). Changed (review v3 §3):** formerly barred every comparison with partial information. |
| E17 | **Direction of a visit.** A's statement about where A went ("I visited no one", "I went to Y") + a sighting of who came **to** A (a watch on A, claimed or verified) | Never in conflict: one is about A's outgoing visit, the other about visits to A. Likewise a follow of A (where A went) never conflicts with a claim about who came to A. | "player_6 says it visited no one on night 2. That is about where player_6 went. player_9's watch is about who came to player_6. The two do not conflict." | L4. **New (acceptance case AC3):** 403f4dbc's investigator read the watch as contradicting player_6. |

---

## Table F: joins and conditionals (specification; R9, review v4)

**Status:** a specification under R9. Built as levels 2–4 and 7 of the build order (Rendering).

Tables A to E produce single facts and pairwise comparisons. This table joins them into what a careful
human keeps in their head: the seat's own results set against claims, claim sets against the census,
and what each living player could still be. The four acceptance cases below show why it is needed:
in each, the sentence that would have changed the turn is a join, not a single row.

**How the engine derives them (step 2).**
- **Candidate roles per player.** Each living player and hidden body starts with the census (C1):
  the dealt roles not yet revealed, minus the receiver's own role and, for a wolf, its pack's roles.
  Every certain row of Tables A to D removes candidates (C9, C10, C17, C20, L8, …).
- **Count propagation** (C18). One copy of each role. When a role has one possible holder, it is
  removed from everyone else. When k players can only hold k roles between them, no one else holds
  those roles. When a role's holder must be alive (it acted on a night after every hidden death),
  the hidden bodies lose it.
- **Conditionals** rerun the same propagation with the premise added. A claim as premise adds the
  claimant's role and treats the claimed facts as verified for that run only. "If X is not the
  [role]" removes that candidate. A premise that leaves some player with no candidate produces **no
  conditional line**; a contradiction is shown only by a Table E row that names it.
- **Hidden night choices are not enumerated.** Each night record already becomes a role constraint
  through Tables A and B. Where a constraint depends on a choice nobody sees (a self-bet, which body
  a borrowed action used), the row keeps both branches as candidates.
- **Sound, not complete.** Propagation can miss a conclusion that a full search would find; that only
  means the seat is told less. It must never emit a line that some consistent assignment breaks. The
  brute-force oracle (Build verification) is the test for that, on constructed nights, in tests only.

**Placement and order** (cache layout, `Agents/prompts/layout.py`).
- Lines that are the same for every seat (public certain lines, public conditionals on claims) go in
  the cached public record. They change only at the morning, at a reveal, or when a claim changes, as the claim ledger
  there already does.
- Lines for one seat (its own joins, conditionals that use its private results or its own role) go
  after the cache boundary, together with today's claim comparisons (build step 4).
- A standing fact repeated across days is folded into one line, not restated each morning.
- The order of the per-seat lines (own joins first or last) is a cheap screen, not a ruling: the
  list-order memory says models favour what comes first.
- The block must not lose to the seat's own carried-forward note (§5 of `experiment_log.md`: the
  healer took in the injected fact 10 of 10 times and still followed its note's "stay quiet"). OQ21.

| ID | Family | Grade | Fires when | Proposed wording (example) | Basis |
|---|---|---|---|---|---|
| F1 | **Own result confirms part of a claim** | Certain, about that part only | The seat's own record (or its own action) shows a fact that a claim also states | "player_9 says you came to player_6 on night 2. You did: you checked player_6 that night. This confirms that part of player_9's report, not that player_9 is the Sentinel." | E13 extended to the seat's own actions and own received results |
| F2 | **Own result + claim → conclusion** | Follows if the claim is true, or possible explanations | The seat's own result and one claim about the same night and player join into a role conclusion | "player_3 says player_7 came to you on night 1, and player_7 agrees. If that is true, either player_7 is the Chanteuse, or player_7 and the Chanteuse both came to you." | A6, L4; AC1 |
| F3 | **Claim status and census** | Certain | Every turn from the first claim on | "Claims so far: player_2 the Sentinel, player_4 the Sigilist, player_8 the Healer. No role is claimed twice. player_6 and player_10 have made no role claim. The Serial Killer is alive and is one of player_2, player_4, player_6, player_8 and player_10." | E15, C1, C18 |
| F4 | **The current role claims true** | Follows if the current role claims are true | The latest, not withdrawn, role claim of each player can all be true together (propagation with all of them assumed leaves every player a candidate, and no Table E row finds them incompatible), and the premise narrows a role. Claimed actions and results are not part of this premise; a line that needs them names them (F5). | "If the current role claims are true, the Serial Killer is player_6 or player_10." | C18; AC2. **Changed (review v4):** was "every claim made so far", which left open whether actions and withdrawn claims counted. |
| F5 | **One claim true** | Follows if the claim is true | Assuming one claim (or two named claims) fixes a role or narrows it below the census | "If player_2's watch is true, player_8 is the Healer: no other role still in play could have come to you on night 2." | C18; AC2 |
| F6 | **What it takes for a claim to be false** | Contrapositive of F5 | F5 fires with a role conclusion | "For player_8 not to be the Healer, player_2's watch must be false." | as F5 |
| F7 | **What each player could still be** | Certain | A living player's candidates are fewer than the census leaves everyone (some role is excluded for that player in particular) | "player_6 can only be the Vigilante, the Serial Killer or the Speculator." The full list, never a part of it. For an evil seat, the same lines tell it which roles it can still claim without a public contradiction (ruling, 2026-10-16). | C9, C10, C18 |
| F8 | **Possible explanations of a claim** | Possible explanations | A claim is consistent with the record only on some branches | "player_10 says it shot player_5, and player_5 is alive: either player_10 was roleblocked, or player_5 could not be killed that night, or player_10's claim is false." | E4a, E8a, §0 grade 3 |
| F9 | **Across nights** | Certain, or follows if a claim is true | Exclusions and budgets that build up over several nights (C9, C17, C20) | Per cast, for a seat that knows of the immune results (the attacker, or a will): NE+FT, "player_5 could not be killed on nights 2 and 3, so player_5 is the Fortune Teller and has no self-bets left." SK+FT: "If player_5 is the Fortune Teller, both its self-bets are spent" (two immune nights also fit the Serial Killer). | C17, C20; review v4 |

---

## Rendering: what the seat reads (review v4)

**Tables are the engine's rules; the block is what the seat reads.** Most rows of Tables A to D are
working steps that feed Table F and are never shown on their own. The build order follows what the
seat reads, by level, most useful lines for the fewest added lines first:

| Order | Level | Rows | Lines a turn, typical (busy day) |
|---|---|---|---|
| 1 | The seat's own night result and what it implies | Table A | +0: rewrites the record line the seat already gets |
| 2 | Its own result joined with claims | F1, F2 | 0–2 (3) |
| 3 | Census and what each player could still be | F3, F7, Table C | 1–3 (6) |
| 4 | Conditionals | F4–F6 | 0–2 (4) |
| 5 | Public events and what they imply | Table B, wills | 1–3 (5), cached |
| 6 | Today's claims against the record | Table E | 2–5 (8) |
| 7 | Possible explanations | F8 | 0–1 (3) |

The line counts are estimates from the acceptance cases. Before Table F is built, the renderer runs
on every turn of the saved Haiku games (no model call) to measure the real spread.

**Items, then text.** The engine produces structured items: subject player, conclusion, grade,
premises, sources (the seat's record, a will, a morning announcement, player_X's claim) and the full
derivation with its source events. The renderer is a pure function from items to text. The
derivation is logged with every injected block but never shown, so a live line can be traced to why
it was produced; the tests verify it.

**Fold rules** (review v4, amended by review v5).
1. **Conclusion first within an entry,** with at most one short reason made of facts the seat can
   check, so it can defend the conclusion aloud. A reason the conclusion depends on is never dropped.
2. **Never fold away a premise, a source or a hedge.** A conclusion that rests on a claim stays
   conditional ("If player_3's check is true, player_6 is a wolf"); a source stays named. When a line
   confirms a claim's *content*, the clause saying what it does not confirm stays on the same line
   ("That does not show that player_2 is the Sentinel"). That clause is the one exception to the
   clause limit in rule 4: without it a seat reads "the report is true" as "the reporter is
   verified" (E13).
3. **Remove a line only when another shown line states the same proposition under the same
   premises.** F5 and F6 are the same fact read in opposite directions (if A then B; so if not B,
   then not A). Which one is shown depends on the turn: on a vote turn, the form whose condition is
   about the vote's possible target ("player_8 can be the Serial Killer only if player_2's watch is
   false"), since a weak model does not reverse a conditional; on other turns, F5. Never worded as
   advice ("to vote player_8 you must believe …"). Statements that sound alike but differ
   ("if player_8 is not the Healer, player_8 is …" restricts player_8's alternatives; "if player_2's
   watch is true, player_8 is the Healer" ties player_8 to player_2's testimony) both stay.
4. **One entry per living player, in seat order,** after the shared lines (the census, the
   role-claims conditional) at the top. Seat order is fixed, not by content: these models favour the
   first-named seat (memory: list order and example bias), so an entry put first because it has the
   most to say would pull votes toward that player. A conclusion stands out by its wording, not its
   position. The entries follow the same order as the seat's `reads` list. Each entry has one primary
   sentence and at most two supporting clauses (plus the hedge of rule 2). A player with nothing to
   report gets a short entry ("player_6 has made no role claim"). This is how the block is
   organised, not a length limit; constraints across players go on the shared lines, not into each
   entry. **Check:** once built, rotate the seat order on the frozen vote cases (small n) and confirm
   the votes do not follow the first entry.
5. **A working step is shown on its own only when** it is the seat's own private result (only it can
   cite it), or an event raised in today's discussion. "Raised" is mechanical: (a) a message today
   carries a structured claim (the speaker-filled `claim` field the ledger reads) on that night and
   player, or (b) a message today names both that player and that night ("player_7", "night 1").
   The day summariser's accusation entries are **not** a source: they kept withdrawn accusations
   (R5), and the summary runs only after the discussion, before the vote (`graphs/day.py:74`), so
   discussion turns would never have it.

Folding changes the layout, not the propositions: the folded block must carry every proposition its
acceptance case lists, with the same premise and source. Tests check the items (propositions) and,
separately, golden the rendered text.

**AC2 folded (the investigator's day-3 vote).** Six sentences become one shared line and five
entries, in seat order:
- "The Serial Killer is the only evil player left, and it is one of player_2, player_4, player_6,
  player_8 and player_10. If the current role claims are true, it is player_6 or player_10."
- "player_2 claims the Sentinel. Its report that player_7 came to you on night 2 is true: you were
  roleblocked that night, and player_7 was the Chanteuse. That does not show that player_2 is the
  Sentinel."
- "player_4 claims the Sigilist."
- "player_6 has made no role claim."
- "player_8 claims the Healer; no one else does. player_8 can be the Serial Killer only if player_2's
  watch is false. player_3's will shows player_7, the Chanteuse, went to player_8 on night 1; the
  pack's kill that night was on player_1, so she went there to block player_8, which agrees with
  player_8's claim to have been roleblocked."
- "player_10 has made no role claim."

The night-1 line keeps its reason (the kill went to player_1). Without it the line would overstate:
a Chanteuse's visit is a block or the pack's kill, and only the kill's announced target settles which.
"Agrees with" rather than "as player_8 said": a block on the Serial Killer has no effect, so the visit
fits player_8's claim without proving it.

---

## Acceptance cases (review v4)

For each known failure: what the seat knew, the deduction a careful human makes, and the exact
sentences the seat should have received, each with its grade. Build verification item 4 makes these
golden tests: the engine, given only the receiver's payload at that turn, must render these sentences
and nothing on the "must not say" list. Each case was checked against its game's frozen state
(`data/haiku_effort_replay/`, `data/deduction_injection/`); the reasoning for "holds in every
consistent assignment" is written out so the oracle can confirm it when built.

### AC1. R1: 2f19d908, day 2, the healer (player_8), the turn after player_7's admission

**Knew.** Own record: night 1, tried to protect player_5, roleblocked. Public: night 1, player_1 was
attacked by the wolves and the serial killer, role hidden by an illusionist; no one dead before
night 1. Claims: player_3 (trailseer) followed player_7 on night 1 and saw it go to player_8;
player_7 admitted going to player_8 and claimed no role.

**Should receive.**
1. Certain (A6, the step-1 wording): "You were roleblocked on night 1: your protection of player_5
   did not happen. Only the Chanteuse can roleblock, so the Chanteuse came to you that night."
2. Possible explanations under a premise (F2): "player_3 says player_7 came to you on night 1, and
   player_7 agrees. If that is true, either player_7 is the Chanteuse, or player_7 and the Chanteuse
   both came to you."

**Must not say.** "player_7 is the Chanteuse", with or without the premise. A second visitor is
possible: any visiting role could also have come to player_8. (An earlier chat example, "if
player_3's follow is true, player_7 is the Chanteuse", was wrong for this reason.)

**What the seat did.** Wrote every premise in its notes, drew no conclusion, passed all three turns.

### AC2. R3: 2f19d908, day 3 vote, the investigator (player_5)

**Knew.** Public: player_9 voted out on day 2, the illusionist. Night 2: player_3 attacked by the
wolves and the serial killer, a trailseer; its will: "night 1, followed player_7; they visited
player_8". player_7 struck down by a sigil, a chanteuse. Cast SK+SP. Own records: night 1 checked
player_9, Suspicious; night 2 roleblocked. Claims: player_2 the Sentinel (night 2 watch on player_5
saw player_7 and player_8); player_4 the Sigilist (its sigil struck player_7); player_8 the Healer
(protected player_5 on night 2; roleblocked on night 1). player_6 and player_10 no claim.

**Should receive.**
1. Certain (F3): "Both wolves are dead: player_9 and player_7. The Serial Killer is alive and is one
   of player_2, player_4, player_6, player_8 and player_10." *Why it holds:* the serial killer cannot
   die at night, no one revealed was it, and player_1's body was hidden by an illusionist, which
   never hides the serial killer (L8).
2. Certain (F1): "You were roleblocked on night 2, so the Chanteuse came to you, and player_7 was the
   Chanteuse. player_2's report that player_7 came to you that night is true. This does not show that
   player_2 is the Sentinel."
3. Certain (B20, R3's misread): "player_3's will shows player_7, the Chanteuse, went to player_8 on
   night 1. The pack's kill that night was on player_1, so that visit was her block on player_8. It
   agrees with player_8's claim that it was roleblocked on night 1."
4. Follows if a claim is true (F5): "If player_2's watch is true, player_8 is the Healer: no other
   role still in play could have come to you on night 2." *Why it holds:* under the premise
   player_8 visited player_5 on night 2 and player_2 is the Sentinel. The serial killer attacked
   player_3 that night; the sigil struck player_7; a vigilante's shot on player_5 would have been
   announced; the speculator never visits; player_5 is the investigator; the trailseer, the
   chanteuse and the illusionist are revealed. Only the healer is left.
5. Contrapositive (F6): "For player_8 not to be the Healer, player_2's watch must be false."
6. Follows if the current role claims are true (F4): "If the current role claims are true, the Serial Killer is
   player_6 or player_10."

**Must not say.** That player_8 is the Healer without the premise. That player_7's night-1 visit
counts against player_8.

**What the seat did.** Voted player_8, citing player_7's night-1 visit to player_8 and "accused by
three players" (R2).

### AC3. 403f4dbc, day 3, the investigator (player_4), the visit-direction turn

**Knew.** Public: no deaths on night 1, no vote on day 1, the town abstained on day 2; night 2,
player_8 killed by the wolves, role hidden by an illusionist. Cast NE+SP. Own record: night 2 checked
player_6, Suspicious. Claims: player_9 the Sentinel, night 2 watch on player_6 saw player_4 and
player_8; player_6 said it visited no one on night 2.

**Should receive.**
1. Certain (A22, condition (a)): "Your check read player_6 Suspicious on night 2. No one had died
   before that night, so the Necromancer had no body to kill through and could not read Suspicious:
   player_6 is a wolf."
2. Certain (F1): "player_9 says you came to player_6 on night 2. You did: you checked player_6 that
   night. This confirms that part of player_9's report, not that player_9 is the Sentinel."
3. Certain (E17): "player_6 says it visited no one on night 2. That is about where player_6 went.
   player_9's watch is about who came to player_6. The two do not conflict."

**Must not say.** That player_6's statement and the watch conflict.

**What the seat did.** Told player_6 that "the watch shows two visitors, so one of those answers is
false", and never stated that its own check proved player_6 a wolf.

### AC4. 403f4dbc, day 5 vote, the vigilante (player_2)

**Knew.** Public: player_6 voted out on day 3, the illusionist; player_1 voted out on day 4, the
chanteuse. Night 2: player_8 hidden by an illusionist. Night 3: player_4 killed by the wolves, the
investigator, will "night 2, checked player_6: Suspicious"; player_5 killed by a reanimated wolf,
hidden by a reanimated illusionist; the speculator picked Town. Night 4: player_7 killed by a
reanimated wolf, the healer, will (protected player_9 on nights 1 and 3, player_4 on night 2). Living:
player_2, player_3, player_9, player_10. Claims: player_9 the Sentinel (night 2 watch on player_6 saw
player_4 and player_8; night 4 watch on player_3 saw no one). player_3 and player_10 no claim.

**Should receive.**
1. Certain (F3): "Both wolves are dead: player_6 and player_1. The Necromancer is alive: it killed
   through a body on night 4. It is player_3, player_9 or player_10." *Why it holds:* it acted on
   night 4, only player_7 has died since, and the hidden bodies died on nights 2 and 3.
2. Certain (F1 through a will, E12): "player_4's will shows player_4 checked player_6 on night 2, so
   player_4 went to player_6 that night, as player_9's watch reported. This confirms that part of the
   report, not that player_9 is the Sentinel."
3. Certain (F3, E15): "No one else claims the Sentinel. player_3 and player_10 have made no role
   claim."
4. Follows if a claim is true (F5): "If player_9's claim is true, the Necromancer is player_3 or
   player_10."
5. Certain (E17): "player_9 says no one came to player_3 on night 4. That is about who came to
   player_3, not about whether player_3 acted."

**Must not say.** Anything that singles out one of player_3, player_9 and player_10: nothing certain
separates them. Which one to vote stays the model's judgment.

**What the seat did.** Voted player_9 as "unverified", though part of player_9's report was the only
claim a will had confirmed.

## Open questions

1. **OQ1 Resolved (R1, 2026-10-16).** *Was:* the necromancer's card said "On a night it attacks, it
   reads Suspicious" while the code made only a `kill` through a body Suspicious. The engine rule
   stands and the card now says so.
2. **OQ2 Resolved (R2, 2026-10-16).** *Was:* "saved by the healer" was printed for a save through the
   dead healer's body. Now "saved by a reanimated healer", in the morning line, the records and the
   ledger.
3. **OQ3 Ruled (R3, 2026-10-16).** *Was:* a blocked blocker blocks but makes no visit
   (`night.py:135-153`). No legal game reaches it (L3; the review confirms). The owner will make
   blockers unblockable in future; no code change now.
4. **OQ4 Resolved (R4, built 2026-10-16).** The record now ends at "your action was not carried out";
   the A6–A8 lines say who blocked. *Was:* every living wolf reads the pack's "You were
   roleblocked", and "you learned nothing tonight" is false. Today only the lone illusionist can be
   the blocked carrier.
5. **OQ5 Resolved (R5, 2026-10-16).** *Was:* a reanimated clean also hid the pack carrier's visit. Now
   only the living illusionist's conceal hides it (`night.py:221-237`).
6. **OQ6 (open)** The census and clocks treat a hidden body as any side (`board_clocks.py:98-111`;
   `prompt_formatters.py:64-74`). L8 says a body hidden "by an illusionist" is never a wolf. Not
   false, but a solver should use L8 (C1).
7. **OQ7 Resolved (R6).** *Was:* the chanteuse card said her block "works on Town players and on
   wolves". Now: "Her block works on Town players (she cannot block her own pack)".
8. **OQ8 Resolved (R6).** *Was:* a trailseer's "visited no one" on the necromancer could be read as "did
   not act". The card now says "visited no one" means only that no visit was made in their name.
9. **OQ9 (closed by the review, re-checked).** *Was:* whether a human SK can submit no target. The human
   validator rejects a pass and any target outside the legal list, which has no decline word for the
   SK (`human_turn.py:129-136`). The SK always acts.
10. **OQ10 (narrowed, review §9).** The FT is not told whether it was attacked on a self-bet night
    (`night_record.py:200-202`). No line may infer an attack or its absence *from the self-bet record
    alone*. The attacker does know its target was immune (A14, A16, A18, A19).
11. **OQ11 (note)** A vigilante shot on a self-betting FT is spent and silent. B5 / B13 keep the hedge
    that the absence of a vigilante line does not rule out a shot (`resolution.py:61-72`).
12. **OQ12 Resolved (R6).** *Was:* the necromancer card mentioned a vigilante "penalty for a miss" that
    does not exist in code. Removed.
13. **OQ13 (note)** The cleaner phrase is "a reanimated illusionist" exactly when a `reanimated_wolves`
    attack is on the victim (`resolution.py:158`). No contradiction found. B6 / B7 depend on it.
14. **OQ14 (note)** Declines (no_check, no_watch, keep_sigil) leave no record and so no will line
    (`night_record.py:33-46`). The public cannot tell "declined" from "had no uses left". A will's
    missing night must not be read as "was blocked" (a block leaves its own clause). It does mean that
    no choice was made that night (L11; review v3 §6).
15. **OQ15 (note)** A failed FT turn may fall back to a random self-bet while one is left
    (`agent_player.py:194`; `action_space.py:56-57`). No row changes, but a self-bet can happen
    without the model choosing it.
16. **OQ16 (resolved 2026-10-16, in two fixes; review §11, review v2 §4)** The claim ledger kept a
    superseded sighting. When a claim kept its target and result, `_add_action` kept the old `seen`
    list, and the roleless branch dropped `seen` altogether.
    - *First fix:* the roleless branch keeps `seen`, and a different sighting is a change.
    - *Second fix* (after review v2 found two residual failures with schema-valid inputs: "saw p7" →
      "saw p8", both `not_said`, lost the history; "saw no one" (`no_visitors`) → "saw p8" kept
      `no_visitors` and hid p8): a **stated sighting** is `[]` for `no_visitors`, the names when
      named, and `None` when unstated. A sighting stated both times and different is a change, kept
      with its history (`claim_ledger.py` `_sighting`, `_sighting_changed`).
    - Tests in `tests/engine/test_claim_ledger.py` now use the schema-valid results `not_said` /
      `no_visitors`.
    - Re-checked here: named→named shows p8 with "says p7 visited them" as history; empty→named
      shows p8 with "says no one visited them" as history; named→unstated keeps p7.
    - The reviewer's probe (`data/catalogue_review_v2/probes.py`, line 104) now fails its assertion
      because the bug it reproduced is fixed.
    - *Third fix* (review v3 §4): dating an undated watch claim erased its named visitor. Day 2: "I
      watched p5 and saw p7" (no night); day 3: the same watch dated to night 1, visitors not
      repeated. The ledger kept only "Night 1: watched p5". Now `_add_action` carries the earlier
      `seen` over when the dated claim states no sighting; a dated claim with a different sighting
      is still a correction with history. Test: `test_dating_an_undated_watch_keeps_its_sighting`
      (`tests/engine/test_claim_ledger.py`). The v3 probe (`data/catalogue_review_v3/probes.py`,
      line 82) now fails its assertion because this bug is fixed.
17. **OQ17 (ruled 2026-10-16: card stays)** The vigilante's bullet count (2) is in the config but not in
    the rules text, which says "a few bullets" (`prompts/roles/vigilante.py:6`, `:70`). Owner: the count
    is a balancing setting, not a fixed rule, so it stays out of the public rules. Counting bullets is
    therefore not public, and C5 leaves it out.
18. **OQ18 (resolved 2026-10-16; review v2 §1)** The ledger flagged every claimed protection of a player
    "saved by a reanimated healer" as contradicted, whatever role the claimant claimed. Fixed in
    `claim_ledger.py` (`action_checks` now takes the claimant's current role): a healer claim gets
    "…not a living healer." (fits = False), a necromancer claim "…as a necromancer's protection would
    be." (fits = True), any other or no role the fact alone (fits = None). Tests in
    `tests/engine/test_claim_ledger.py`.
19. **OQ19 (resolved by R9, 2026-10-16)** *Was:* Table E awaited the owner's yes. The coverage ruling
    puts claim comparisons in scope; Table E is built in step 4.
20. **OQ20 (open, a screen)** The order of the per-seat lines after the cache boundary: the seat's own
    joins first, or nearest the question. Settle by a small replay screen when step 3 is built.
21. **OQ21 (open)** How the deduction block outranks the seat's carried-forward note. In R1 the note's
    "stay quiet" beat an injected fact the seat had absorbed (`experiment_log.md` §5). Options: place the
    block after the note, or have the note prompt say that the computed lines replace earlier
    conclusions where they conflict. A prompt change, so it waits for the block to exist.
