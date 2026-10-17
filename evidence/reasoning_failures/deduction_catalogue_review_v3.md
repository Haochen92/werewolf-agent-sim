# Third catalogue review — 2026-10-16

Reviewed the 458-line `deduction_catalogue.md`, including the third-pass additions, against the
current working tree (HEAD observed as `b8f0b426` at validation). This review leaves the catalogue
and production code unchanged. Reproductions are in `data/catalogue_review_v3/probes.py`.

**Verdict:** the previous major corrections are incorporated, and the catalogue is substantially
closer to an implementable specification. It is not yet exhaustive or entirely consistent. The
remaining findings below distinguish false implications, lost deductions, and implementation
requirements. Passing the existing tests does not establish correctness of the proposed solver.

## 1. E8a still needs the borrowed-shot distinction

Catalogue line 377: no announced **vigilante** attack after a claimed shot is said to require
roleblock or immunity. That is false for a necromancer shooting through the vigilante's body.
The target can die, with a **reanimated vigilante** attack announced, while neither alternative
holds. E8b includes the distinction, but E8a does not.

The probe kills p1 through the dead vigilante p4: the attack type is `reanimated_vigilante`, the
verdict is `killed`, and nobody is blocked. This is a truthful borrowed-shot claim.

**Correction:** select the expected attack type from the claimed actor/action mechanism in both
rows. No matching attack after a living vigilante's attempted shot permits block or immunity;
after a valid borrowed shot it permits immunity only, since the necromancer cannot be blocked.
With the mechanism unstated, retain the possible branches rather than treating absence of an
ordinary vigilante line as absence of the claimed attack.

Code: `Agents/rules/night.py:113-119`; `Agents/nodes/night/resolution.py:30-38`, `:138-153`.

## 2. C20 contradicts its own shared-conceal rule

Catalogue line 315 says that a reanimated sigil **and any other borrowed action** spend nothing
from the dead role's budget. The latter phrase needs the illusionist exception already present
in C5 and the role overview.

A successful kill through the illusionist's body spends one of that role's remaining conceals.
The probe starts at 2, hides one death, and ends at 1.

**Correction:** “Borrowed actions do not spend the dead role's original budget, except that a
successful conceal through the illusionist's body spends one conceal from the shared pool.”
The exact public conceal formula elsewhere in C20 is correct.

Code: `Agents/nodes/night/resolution.py:55-60`.

## 3. E16 discards valid comparisons involving partial information

Catalogue lines 352-353 and 386 prohibit comparisons whenever the result is unknown or partial.
This conflicts with E1 and loses precisely the useful corroboration the feature is intended to
provide. “I saw p7 at p5 on night 2” can establish a claimed positive visit without claiming an
exhaustive visitor list. It can agree with p7's visit claim, or conflict with p7's explicit denial.
Neither comparison needs the other visitors.

There is also a schema distinction: a positive sighting can have `result="not_said"` and a
nonempty `seen` list. The now-correct OQ16 tests use exactly that representation. An unknown
generic result field does not make the sighting unknown.

**Correction:** each comparison declares the fields it needs. Unknown night prevents a
night-specific join; partial sightings permit positive comparisons but do not support exclusion
from omission. Return “insufficient information” only for the particular comparison that lacks
its required premises. Roleblock versus a claimed unblockable role, for example, does not need
a night number at all.

## 4. OQ16 has a further information-loss path when an undated claim is dated

The previously reported named-to-named and empty-to-named corrections are fixed. A separate
path in `Agents/rules/claim_ledger.py:237-241` still drops a sighting:

1. Day 2: “I watched p5 and saw p7”, with night unspecified (`night=0`).
2. Day 3: the same watch is dated to night 1, without repeating the visitors.
3. The ledger removes the undated entry and renders only “Night 1: watched p5”. Both the p7
   sighting and its history are absent.

The probe uses validated `ClaimedNightAction` inputs. The dated-entry merge carries over an
unstated `result`, but not an unstated `seen` list. This undermines Table E's input completeness.

**Correction:** preserve previously stated fields when the new entry supplies only missing
metadata, including the sighting and relevant provenance/history. An explicitly new sighting
must still be treated according to correction semantics. Add a regression for undated-to-dated
enrichment, separate from the fixed same-night corrections. Keep the existing OQ16 fixes marked
resolved, but record this additional case rather than claiming all sighting retention is settled.

## 5. A35 and Table D still say “blocked” where “attempted to block” is needed

Catalogue lines 232 and 331 allow an invisible Chanteuse only when she carried the kill,
**blocked** the same victim, and the living illusionist concealed it. A successful block is not
required. She can target the speculator with both actions: the block returns `no_effect`, the
kill succeeds, and conceal hides both visits to that door. A follow reports “visited no one”.

The probe reproduces this on night 1. A34 already makes the attempt/completion distinction
correctly; apply the same wording here.

**Correction:** “carried the kill, targeted the same victim with her block attempt, and that
victim was concealed by the living illusionist.” Otherwise an implementation could wrongly
exclude the Chanteuse when the concealed victim was a neutral.

Code: `Agents/rules/night.py:135-169`, `:232-237`.

## 6. Complete wills support useful negative deductions too

L11 and B32 (lines 171-172 and 288) overcorrect with “a missing night proves nothing” / “is not
evidence”. The narrower OQ14 statement, “missing does not mean roleblocked”, is correct.

Given a complete engine disclosure and a night the town holder survived, a completed check,
watch or sigil would have produced a retained record, even when a sigil had no effect. Its
absence therefore rules out that completed use on that night. It can constrain use accounting
and contradict a purported sighting of that optional actor making its role's visit that night.

Example: a sigilist survives nights 1 and 2, then is revealed on day 3. Its complete record
contains only a quiet night-2 sigil. It spent exactly one original sigil across those nights,
not an unknown one or two. The probe verifies that a quiet completed sigil is recorded and
disclosed; records are accumulated with `add`, not replaced each night.

**Correction:** distinguish absence from a complete certified record from absence in a partial
summary or claim. Exclude the fatal night, nights before the game, and incomplete historical
data. Missing records for mandatory actions should trigger an input-integrity check, not a
fabricated deduction. Preserve the prohibition on inferring a block from a missing clause.

Code: `Agents/state/orchestrator.py:70-73`; `Agents/rules/night_record.py:154-173`, `:296-312`;
`Agents/nodes/night/resolution.py:117-133`; `Agents/nodes/orchestrator.py:211-215`.

## 7. Specify normalization of private borrowed sightings before using L12/Table E

This is an implementation requirement the catalogue does not yet state, rather than a false
game rule. `NightActionRecord.seen` is not uniformly a list of observed visitors/destinations.
For the necromancer, `night_record.py:218-220` prepends the borrowed body's name as metadata.

The probe constructs an empty watch through the sentinel's body. The text correctly says
“No one visited p1”, but raw `seen` is `[p2]`, the sentinel's body. Treating raw `seen` as L12's
complete sighting would invent a visitor. A borrowed follow similarly prepends a body to its
destination list.

**Addition:** normalize each receiver-visible record by action and mechanism into distinct
actor, body, target, observed visitors/destinations, and result fields before applying any
deduction. The adapter must preserve the watcher's self-exclusion. Use the recipient's own
available records, never global hidden choices to fill missing information.

## Small wording/status corrections

- R2 still says the ledger flags a “living claimant”; make this “a claimant claiming the living
  healer”. A living necromancer's protection can be valid.
- Table D's necromancer row says “the ledger currently flags it, OQ18”, but OQ18 and the code now
  record that bug as fixed. Remove the stale parenthetical.
- C2's receiving fortune teller “learns nothing new” should be “learns no new role identity”.
  A vigilante's will can newly tell it that it was attacked on its self-bet night; its own
  self-bet record did not reveal that (OQ10).
- E1's wording should preserve whether its source is a claim or a verified result/will. The
  current generic template always says “claims”, although the row allows either source.

## Validation and remaining scope

The existing focused suite passes: **79 tests** in `test_ten_seat_game.py`,
`test_night_whiff_disclosure.py`, and `test_claim_ledger.py`.

The new deterministic probes pass:

```bash
PYTHONPATH=. poetry run python evidence/reasoning_failures/data/catalogue_review_v3/probes.py
```

They demonstrate current behavior; the dating probe intentionally asserts the observed bug and
will need updating after a fix. The prior v2 probe still intentionally fails at its now-fixed
OQ16 assertion, as the catalogue already notes.

The catalogue now covers the major mechanics across all four casts. This review is not a proof
of exhaustive combinations. Before emitting solver-certified conclusions, validate each rule
against feasible histories with source/time boundaries, including borrowed actions, blocked
attempts, partial claims, hidden visits, and uses established by later disclosures. Keep Table E
as a specification until the separately recorded owner decision to build it.
