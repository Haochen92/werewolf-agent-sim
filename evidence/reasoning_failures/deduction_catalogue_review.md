# Deduction catalogue review — 2026-10-16

Reviewed `deduction_catalogue_draft.md` (310 lines), the file present for the requested
`deduction_catalogue.md`. Baseline: working tree on top of `df62a3a2`, including existing uncommitted
rule changes. The catalogue and production code were not changed by this review.

**Verdict: broad coverage of individual night results, but not exhaustive or ready to serve as a
specification for certain deductions.** There are incorrect statements, stale descriptions of code,
and missing constraint families. In particular, the claim-corroboration assistance motivating this
work does not yet have an explicit catalogue of its own.

## Corrections needed

### 1. A32/B19: an empty watch excludes the watcher, not all actions

Catalogue line 148 says “No one acted on X last night.” The sentinel itself watched X; a necromancer
using the sentinel's body likewise performed a watch. Its own visit is deliberately omitted from
the result (`Agents/rules/night_record.py:137`). The listed exclusion of checks, blocks, protection,
etc. can be useful, but the blanket wording is false.

Use: **“No other visitor was seen at X. Because X survived, no carrier visit was concealed there;
apart from your watch, no visiting action reached X.”** Keep the separate warning that this says
nothing about X's outgoing actions. For a disclosed will, name the watcher instead of “your”.
Verified with a night where the only visitor to X is the sentinel and its `seen` list is empty.

### 2. A31/OQ5 and L4: reanimated conceal no longer hides the carrier

Catalogue lines 147 and 271–275 describe behaviour that has already changed. Current
`Agents/rules/night.py:223` captures `concealed_by_illusionist` before applying a reanimated clean,
and only that first set suppresses carrier visits. When a wolf and the necromancer kill the same
target and the illusionist's body cleans it, both visiting names remain visible.

Update A31 and L4, and mark OQ5 resolved. The blanket “victim ended up concealed” condition is too
broad. Extend A28/C6 to distinguish a live conceal from a reanimated clean instead of excluding
every concealed victim. Verified by direct resolution and the existing regression test.

### 3. B2 and B7 inherit statements that their own conditions reverse

- B2 (line 177) says “As B1”, which imports “The carrier's visit to X was visible.” That is false
  for the live conceal B2 describes. Reproduced directly.
- B7 (line 182) says “As B6”, which imports “The illusionist's body had no conceals left.” B7
  requires a remaining conceal and spends one. Say explicitly which parts of B6 carry over.

These are not harmless shorthand in a specification intended to generate certain conclusions.

### 4. A12/B12/OQ2: reanimated protection is now explicitly announced

Catalogue lines 128, 187 and 255–259 describe the old wording. The current morning announcement,
attack record and sigil record name **“a reanimated healer”**; the structured night report also has
`reanimated_saves`. See `Agents/nodes/night/resolution.py:150` and
`Agents/rules/night_record.py:64`. Update the rows and mark OQ2 resolved.

This also supplies positive evidence: the necromancer used the healer body that night, so it did
not simultaneously use another body to kill, block, investigate, watch, follow or place a sigil.

### 5. C15 contradicts B24: not every revealed town death has a will

C15 (line 227) says every revealed town death after night 1 publishes a record. B24 correctly
allows a player who declined all optional actions to have none. An investigator can decline all
checks, die later, and have no record to disclose. `disclosure(..., [])` returns `None`.

Use “Every revealed town death publishes any previously received records.” No record is not proof
of a non-town role or a fraudulent claim. Also preserve the distinction between a night death,
whose fatal night supplies no record, and a daytime execution after a completed night.

### 6. Table D's SK row repeats the incoming/outgoing visit error

Line 241 treats a watcher at the SK's victim as contradicting both “I visited no one” and
“No one visited me.” It only contradicts the first. The SK can visit its victim while nobody visits
the SK. Direct resolution confirms those facts coexist.

Checks must use ordered `(visitor, destination, night)` facts, never an undirected visit relationship.

### 7. Table D sometimes assumes the hidden role it is supposed to investigate

The FT row (line 244) lists “I was roleblocked” as publicly contradicted. That is an impossible
experience for an actual FT, but a hidden FT pretending to be a town role can claim it without an
immediate public contradiction. “I am the FT and I was blocked” is an inconsistent pair of claims;
“I was blocked” alone is not publicly disproved just because the engine knows the speaker is FT.

Separate three categories: impossible for the true role; incompatible with a claimed role; and
contradicted by receiver-visible facts. Apply the same distinction to the SK and speculator rows.
The necromancer's true borrowed sentinel result also never has a period before the sentinel reveal:
the body must already be revealed before it can be borrowed.

### 8. C2 needs a target-aware self-knowledge rule

“Minus self” (line 214) cannot be applied indiscriminately to role candidates, particularly when
using public wills. A will's immune target can be the receiving FT itself. Removing its own role
would wrongly leave SK in an SK+FT game.

For a different player, subtract the receiver's known role subject to the public role count. For
the receiver itself, constrain to its actual role and known actions. Known allies need the same
target-aware handling. Time-index all revealed-death exclusions to the night being analysed.

### 9. OQ10 overstates who cannot know a self-betting FT was attacked

Lines 290–292 correctly say the FT receives no attack notification, but incorrectly extend that to
“nobody else” and “any line implying the FT was attacked ... is unknowable.” The attacker knows its
own target and immune result. In SK+FT, the SK can identify the FT and know it attacked it (A18).
A watch may provide another route once combined with other evidence.

Restrict the prohibition to drawing an attack/no-attack conclusion **from the self-bet result alone**.
Reproduced the attacker's `immune` record.

### 10. C5 needs successful-use accounting and a declared configuration scope

“A third check, watch, shot or sigil is false” (line 217) needs qualifications: three distinct
completed uses by the original living role, under the standard two-use configuration. Blocked
attempts do not spend uses; repeated reports of one night are not extra uses; borrowed abilities
do not consume the dead town role's remaining budget. Conceals spend only on a concealed death.

`GameConfig` exposes configurable checks, watches, bullets, sigils, conceals and self-bets
(`Agents/config/game.py:30`). Either explicitly restrict this catalogue to the standard configuration,
or make limits parameters supplied through the public rules. Do not silently read hidden runtime
budgets or assume every supported configuration uses two.

### 11. Current ledger loses corrections to sightings

This is an implementation dependency the catalogue should record before cross-claim checks are
built. `_same_claim` compares target/result but not `seen`; `_add_action` retains a nonempty old
`seen` list (`Agents/rules/claim_ledger.py:205`, `:229`). A day-2 claim “night 1, watched X, saw A”,
corrected on day 3 to “saw B”, remains A with no correction history. Reproduced using two
`DaySummary` inputs.

The `claimed_role == "none"` branch also constructs an action without copying `seen` (line 172).
Decide which roleless action reports are supported and preserve the relevant fields. A comparison
engine must not certify consistency using a dropped or superseded sighting.

## Coverage missing or insufficiently specified

### M1. The claim-corroboration catalogue itself

Table D is mainly a per-role list of possible bluffs, not the proposed ledger extension. Add rows for:

- claimed watch versus claimed visit, and claimed follow versus claimed destination;
- verified private/public sighting versus claimed action: which component is confirmed and which is not;
- claimed block versus visitors, while preserving that a visitor could have performed another action;
- claimed protection versus death/save, and immunity masking protection;
- a claimed complete visitor list that omits a known visitor, with watcher and conceal exceptions;
- agreement, incompatibility, partial information, unknown night and unknown result;
- current counterclaim/no-counterclaim and no-role-claim status, including withdrawals;
- revised claims and conditional “if these named claims are true, then ...” arguments.

Two incompatible claims imply that they cannot both be true, not which claimant is lying. A false
claim does not prove an evil role: the public rules allow any player to bluff. A missing counterclaim
does not reserve a role slot. Require provenance and explicit assumptions on every comparison.

### M2. One action/body/target constraints across observations on the same night

The necromancer can use only one body that night. An established reanimated save rules out its
having made a body kill, even if the FT could have hidden a kill. A Suspicious result that night
therefore identifies a wolf under the current implementation. A known reanimated action also limits
other claims of reanimated actions that same night.

There is only one legal blocker per night and one block target. A verified block plus a two-door
Chanteuse follow identifies which door was blocked and which was the pack kill. These constraints
should explicitly combine records; listing each record independently leaves useful deductions out.

### M3. Cross-night resource constraints, especially FT immunity

In the standard SK+FT cast, an individual confirmed immune on three distinct nights cannot be the
FT (two self-bets), so it is the SK. Multiple attacks on one night consume only one self-bet.
In NE+FT, a confirmed immune result after night 1 identifies the FT and establishes a self-bet use;
two distinct such nights establish exhaustion. Earlier inferred uses constrain later possibilities.

Generalise this to announced and privately known uses. Conceal and vigilante counts are partly in
C5, but the strongest cumulative FT deductions are absent, and L1/D currently suggest too broad an
inability to rule self-bets out.

### M4. Joint role assignment, not just independent candidate lists

Enforce one copy per dealt role over living players and concealed bodies, integrating all nights.
If two players can only be healer/trailseer, those two roles are unavailable to everyone else even
before either individual is identified. Carry private knowledge of concealed roles from the
illusionist, necromancer and FT into that receiver's assignments. Do not make that knowledge public.

Claims remain optional assumptions, not hard role assignments. A result is certain only when all
consistent assignments agree. Zero consistent assignments is an input/rule contradiction to report,
not a basis for arbitrary “certain” conclusions.

### M5. Negative evidence with the full historical preconditions

Make absence deductions explicit about a complete morning report and an actor alive at that
night's start. In particular, B13's SK+FT “no SK line” implication needs the SK-alive condition too.
A dead SK produces no attack without any FT self-bet.

Use the phase of a death, not just its day number: a day-n execution supplies a body for night n;
a night-n death does not. In A27, “dead name” means dead before that night, not merely dead when an
old watch result is read. Later legitimate knowledge can refine an old result, but a frozen replay
cannot use facts revealed after its decision turn.

### M6. Endgame, voting and neutral objectives

If the stated scope really is all mechanics, add exact terminal conditions, neutral counts in
wolf parity, the lone killer's last-two condition, ties/abstentions, and the no-lynch restriction.
At a phase after the game has checked for victory, the fact that play continues rules out role
assignments that would already have ended the game. Do not apply that during an unresolved phase.

Add the FT's private “win secured” deduction at the score threshold (it remains won after death),
and the speculator's fixed picked-side objective even after death. Treat configurable day-limit
rules as usable only when they are publicly available; do not introduce hidden configuration into
the player's knowledge.

### M7. Knowledge provenance and historical rule versions

The opening standard lists pack chat among private knowledge. Chat is evidence of what an ally
said, not an engine-certified action or result; neither a plan nor a bluff becomes a fact. The
same distinction applies to the receiver's own remembered claims and notes.

Each derived item should record receiver, source event(s), event night, time learned, rule version,
assumptions and certainty category. This review found same-day rule changes already making rows
stale. Old frozen outcomes must not silently be interpreted with incompatible new conceal rules.

## Questions resolved or still open

- **L3/OQ3:** the draft's reachability argument is correct for the current four fixed casts and legal
  targets. A living Chanteuse cannot coexist with use of her own corpse, cannot target herself or
  another wolf, and the necromancer cannot be blocked. The blocked-blocker engine branch is not a
  present legal counterexample. Keep the invariant checked; this does not need a new rules decision.
- **OQ4:** for the same reason, the only legally blockable pack carrier is the lone illusionist after
  the Chanteuse's revealed death. The apparent plural-pack issue is a future-extension concern.
- **OQ9:** the human validator rejects a missing target, `no_action`, and a pass for an SK night
  turn; a legal target is accepted. The listed uncertainty is resolved.
- **OQ1:** remains real: the necromancer card's “night it attacks” is broader than the implementation's
  `kind == "kill"`. A triggered borrowed sigil is currently Not suspicious. Resolve this before
  treating the wording and code as interchangeable rules.
- **OQ2/OQ5:** already resolved in code, but stale in this draft, as above.

## Validation and the limit of this review

Read all four tables and their lemmas against the twelve-role registry, action legality, night
resolution, result/disclosure formatting, resource spending, human validation, claim folding and
endgame rules. Ran targeted probes for empty watches, live conceal, reanimated conceal, no-will
declines, FT attack knowledge, human SK validation, changed claimed sightings, and visit direction.
These probes exercised local code without model calls; some isolate the relevant actions rather
than replaying an entire game history.

Existing checks:

```text
poetry run pytest -q tests/engine/test_ten_seat_game.py \
  tests/engine/test_night_whiff_disclosure.py tests/engine/test_claim_ledger.py
71 passed in 7.03s
```

Those tests passing does not validate the catalogue: no deduction implementation exists yet, and
the tests do not assert these prose conclusions. The draft's uncommitted scratch checks are likewise
not a reproducible coverage argument.

Before implementation, map each catalogue row to executable examples and counterexamples. Cover
each cast; living/dead/concealed bodies at the relevant night; blocked/declined/exhausted actions;
all outcome types; own-name versus corpse-name visits; and combinations across nights. For each
generated conclusion, require soundness against compatible legal assignments. Separately verify
that changing hidden facts invisible to the receiver cannot change its deductions. This establishes
a defensible completeness boundary for a supported rule set, rather than claiming every possible
multi-step deduction has been enumerated in prose.
