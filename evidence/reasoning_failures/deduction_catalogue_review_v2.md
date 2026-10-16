# Second catalogue review — 2026-10-16

Reviewed `deduction_catalogue.md`, second version, 379 lines, including C20 and Table E, against the
working tree on `df62a3a2`. This is a review, not a change to the catalogue or production rules.
Reproducible probes are in `data/catalogue_review_v2/probes.py`.

**Verdict:** many first-review corrections are now incorporated. The current text still contains
false implications, especially in Table E. Keep Table E as part of the design, but correct its logic
and specify the information each claim represents before implementing it. C20 is useful as a
conservative bound, but its restrictions on what others can know are too strong.

## 1. Table E: remaining incorrect or underspecified deductions

### E2: split a different destination from a denial of all visits

Line 315 groups “I went to Y, not X”/“I went to Y” with “I went nowhere”. They are not the same.

- “A came to X” and “I went nowhere” cannot both be true. Two visits cannot reconcile them.
- “A came to X” and “I also went to Y” can both be true only for the Chanteuse carrying the kill,
  for distinct X/Y under the current cast.
- “I went only to Y” or “I did not visit X” is incompatible with the claimed visit to X.

Preserve whether a statement is exclusive. Do not turn an outright contradiction into a certain
Chanteuse identification.

### E3: the proposed conceal exception is wrong, and watcher self-exclusion is missing

Line 316 says a follower can see A go to X while a watcher at X omits A because conceal hid A.
The engine hides that carrier-to-victim edge from **both** watchers and followers. Conceal cannot
reconcile those two claimed observations (`Agents/rules/night.py:232–237`).

A valid exception is that **A is the watcher itself**: a trailseer follows the sentinel to X;
the sentinel's watch excludes its own visit. Both truthful reports coexist without any conceal.
The probe reproduces both this case and the conceal suppression affecting both observers.

Also distinguish a complete list from a partial report. “I saw B” does not assert “I saw only B”.
An omitted name is a contradiction only when the claim explicitly supplies an exhaustive list or
denies that visitor. A private engine result or published will can supply an exhaustive list;
an ordinary extracted list is not automatically exhaustive.

### E5: a living necromancer really can make a reanimated save

Line 318 says “a living player did not make that save.” False: the living necromancer did, through
the healer's body. Its truthful “I protected X through the healer's body” must remain compatible.

Use: **“The save was performed by the Necromancer through the dead Healer's body. It was not
performed by a living Healer.”** An explicitly claimed living-Healer role is contradicted; a
generic protection claim is not. The current ledger also flags a `protect` action against a
reanimated save without checking the claimant's role (`claim_ledger.py:368–374`), so this is an
implementation issue as well as a wording issue. Verified that the living necromancer receives
its own successful protection record.

### E4/E8: separate selected targets from completed actions

Lines 317 and 321 use “protected”/“shot” and then allow roleblock as an explanation. A blocked
attempt did not complete. Specify separate predicates:

- “I selected/tried to protect X”: compatible with X dying if the protection was blocked.
- “My protection successfully went ahead on X”: incompatible with X dying that night.
- “I selected/tried to shoot X”: no announced attack can be explained by block or immunity.
- “My shot went ahead”: no announced attack requires immunity, not a block.

Interpret natural language conservatively when completion is unclear. Also condition the attack
type on the claimed actor: a necromancer's shot produces a reanimated-vigilante line, not a normal
vigilante line. E9 has the analogous distinction for a sigil and a reanimated sigil.

### E11: require the original living role

Line 324 declares a third check/watch/sigil false without the C5 restriction. A necromancer can
truthfully report three borrowed checks, watches or sigils. Apply the two-use limit to the original
role's own completed uses, not to everyone who performed that action kind.

### Coverage Table E still lacks

- The central private-result case: **your own verified sighting** confirms the visit component of
  someone else's claim, while leaving their role and action unconfirmed. E1 is claim-to-claim;
  E12 covers wills, but neither explicitly covers this central receiver-specific case.
- Claimed roleblock versus a verified watch, and the conditional identity of its blocker.
- No current counterclaim, withdrawn counterclaims, and no-role-claim status, without reserving
  roles as truth. A withdrawal affects current status but remains part of the public history.
- Claimed Not suspicious against a revealed wolf; claimed Suspicious against a revealed SK.
  E7 handles only some of the investigator's contradiction cases.
- Inference when an actor could not legally have acted: not yet active, dead before that night,
  target dead before that night, unusable body, exhausted uses, illegal self-target.
- Unknown night, partial/unknown result, and an explicit “insufficient information” outcome.

These should be typed comparisons over source-qualified facts and claims, not text matching.

## 2. C20: retain the bound, correct the knowledge claims

### Conceals and picks can be counted exactly

With the standard public limit, after a complete report:

**conceals remaining = 2 − distinct deaths publicly marked concealed.**

Every spent conceal produces such a death, and unsuccessful conceal attempts spend nothing. The
living illusionist and its body share this pool. It is exact even when one use remains; it is not
merely an upper bound that becomes exact at zero. The speculator's one pick is similarly exact once
that night's report is complete. The probes verify successful/unsuccessful conceal spending.

### Silent at the time does not mean forever private

Line 281 says silent uses lower only the holder's own count. Counterexamples:

- A later town will publishes an earlier check, watch, or sigil that had no effect. Those are now
  publicly established completed uses. A no-effect sigil disclosure is reproduced by the probe.
- In NE+FT, a vigilante's published will containing immune shots on two distinct nights after
  night 1 identifies the FT and establishes that it used both self-bets. No self-bet was directly
  announced. This is already implied by C17, so C20 currently conflicts with C17.
- A verified visit combined with an independently established role can establish a use even
  before the actor dies, subject to that role's action and visibility rules.

“Announced direct uses” is a safe conservative lower bound on spending; it is not the full set of
publicly knowable uses. Use **publicly established distinct completed uses**, including sound
deductions, or explicitly label an announcement-only implementation as intentionally incomplete.

Count one underlying use once even if a death/save and a later will both describe it. Deduplicate
by actor/resource/night and preserve the shared conceal pool. Reanimated sigils spend none of the
original sigilist's budget, as C20 already correctly says.

### Useful bounds can have both a lower and an upper endpoint

For public starting limit S and feasible use counts `U_min .. U_max`:

```text
remaining is between S - U_max and S - U_min
```

For example, after only one night, the original sigilist can have spent at most one sigil and has
at least one left, even if no sigil attack was announced. A guaranteed blocked night spends none.
Conceals collapse to a single exact count because every expenditure is observable.

Keep the owner's bullet ruling: do not use the private starting number for a public remaining-
bullet bound. Public shot evidence can establish past shots without establishing the initial total.

### “Only the holder is told” has a specific exception

The `uses_remaining` event is seat-private, but it is not the only delivery path. The necromancer's
payload explicitly receives `body_conceals` (`Agents/nodes/night/solo.py:49–51`), and its night prompt
prints it (`Agents/prompts/roles/necromancer.py:89`). This count is also publicly derivable by the
conceal rule above. State the per-recipient information accurately rather than inferring secrecy
from one event type.

## 3. Remaining errors elsewhere

### A34: the second door was targeted by a block, not necessarily roleblocked

Line 198 correctly identifies the Chanteuse from two distinct destinations, but says the other
destination “was blocked.” The block may fail on a neutral or lone killer. Reproduced a Chanteuse
carrying the kill while blocking the speculator: the trailseer sees two destinations, but
`outcome.blocked` is empty and the block result is `no_effect`.

Use “one was the pack's kill target and the other was the target of her block attempt.” The
stronger C4 inference still works when a separate result establishes which target was actually blocked.

### B25: not every revealed body is usable

Line 248 says the executed player's body is usable that night. A revealed neutral or lone-killer
body gives no ability. Qualify with membership in `BORROWED_ABILITY`, plus the necromancer's active
night restriction. Also replace “a town will covers every night X lived through” with “contains
received records from completed nights”: declined checks/watches/sigils leave no entry.

### B31: a winner announcement does not always prove the ordinary win condition

Line 254 says the winner's condition held. At the day limit, `end_game` can instead use
`_max_days_winner`, choosing the largest surviving faction while normal victory conditions are
still false (`Agents/nodes/orchestrator.py:330`, `:395–400`). The probe constructs such a board.
Keep the termination reason separate. C18's normal continuation constraints remain valid only
after the relevant normal victory check.

### Some “only” statements still overstate the list of possible exclusions

L1 (95–98) and the FT row in D say self-bets can be ruled out only through the listed public/budget
conditions. The FT itself knows whether it self-bet; other legitimate private evidence can exclude
FT as a target's role. A14's “a wolf can rule out nothing more” should mean wolf identity alone,
not all of the wolf's other information. Phrase these as base possibilities refined by all
receiver-visible evidence, not exhaustive lists of what could ever be known.

## 4. OQ16 is only partially fixed

The new tests in `tests/engine/test_claim_ledger.py:408` use `result="seen"`. This token is not in
`CLAIMED_RESULT_ENUM` and cannot be emitted as a valid `ClaimedNightAction`; real positive sightings
use a `seen` list with an allowed result such as `not_said`.

Using schema-validated inputs, the probes reproduce two residual failures:

1. “Saw p7” → “saw p8”, both `not_said`: the latest sighting changes, but the earlier sighting is
   not retained as history, contrary to OQ16. The history guard treats the old `not_said` as no
   substantive result even though its `seen` list was substantive.
2. “Saw nobody” (`no_visitors`) → “saw p8” (`not_said`, `seen=[p8]`): the ledger retains
   `result=no_visitors`, adds `seen=[p8]`, and renders “says no one visited them”, suppressing p8.

This directly undermines Table E's guarantee that comparisons use the latest claim. Test with
schema-valid result values and distinguish unknown sightings from explicitly empty sightings.

## 5. Validation and next step

Run the preserved probes from repository root:

```sh
PYTHONPATH=. poetry run python evidence/reasoning_failures/data/catalogue_review_v2/probes.py
```

They check current engine behaviour without model calls, including the empty-to-positive ledger
correction and rejection of the test-only `seen` token. They isolate interactions rather than
claiming exhaustive game-history enumeration.

The existing focused regression suites also passed:

```text
poetry run pytest -q tests/engine/test_ten_seat_game.py \
  tests/engine/test_night_whiff_disclosure.py tests/engine/test_claim_ledger.py
74 passed in 5.71s
```

Passing these suites does not validate the proposed prose deductions or the uncovered correction
cases above. Earlier fixes to reanimated conceal, saver wording and named-to-named sightings are
present; the new findings concern their remaining boundaries and the added catalogue rows.

Fix the certain false implications first: E2, E3, E5, A34 and OQ16. Then make C20 distinguish
exact counts from conservative bounds, and establish claim semantics for the rest of E. These
are substantive correctness issues; a model screen should follow, not substitute for, those fixes.
