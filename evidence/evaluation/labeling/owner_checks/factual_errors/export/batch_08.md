# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 8

### Item `shared_prefix_luna_2026_10_13:e04:cc56ed20:luna_shared_enforced:s2:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> player_2: unclear (low): Questioned player_10's visit but gave no role information of their own.
> player_3: trailseer (low): Claims to have followed player_4 to player_5, matching my watch result.
> player_5: unclear (low): Was the watched target and offered a plausible explanation for player_4's visit.
> player_6: unclear (low): No evidence yet.
> player_7: unclear (low): Focused on the confirmed visits and asked player_10 to explain theirs.
> player_8: investigator (low): Claims investigator and says their check was elsewhere; conflicts with player_10's claim.
> player_9: unclear (low): No evidence yet.
> player_10: chanteuse (low): Claims investigator after my watch confirms a visit to player_5; player_8 also claims that role.

### Item `shared_prefix_luna_2026_10_13:e04:cc56ed20:luna_shared_unenforced:s3:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> player_2: unclear (low): Raised a reasonable question about player_10's visit; no clear role evidence.
> player_3: trailseer (low): Claims to have followed player_4 to player_5, consistent with my watch.
> player_5: unclear (low): Their explanation of player_4's visit is plausible, but does not explain player_10.
> player_6: unclear (low): No information yet.
> player_7: unclear (low): Correctly notes that player_10's visit needs an explanation.
> player_8: investigator (low): Claims investigator and says their check was elsewhere, but has not shared the target or result.
> player_9: unclear (low): No information yet.
> player_10: unclear (low): Claims investigator after being seen visiting player_5; that visit supports the claim but does not establish it.

### Item `shared_prefix_luna_2026_10_13:e04:cc56ed20:luna_shared_unenforced:s4:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> player_2: unclear (low): Questions player_10's visit but gives no independent result.
> player_3: trailseer (low): Claims a trail result matching my watch; not independently verified beyond my own result.
> player_5: unclear (low): Was the watched target and interpreted player_4's visit as a sigil placement.
> player_6: unclear (low): No information yet.
> player_7: unclear (low): Notes the visit claims align but offers no independent evidence.
> player_8: investigator (low): Claims investigator after player_10 claimed the role; says their check was elsewhere but gives no result.
> player_9: unclear (low): No information yet.
> player_10: unclear (low): My watch confirms the visit, but not the claimed investigator action; the competing claim from player_8 leaves player_10's role uncertain.

### Item `shared_prefix_luna_2026_10_13:e04:cc56ed20:luna_today:s2:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> One correction to the framing: player_4 was the person killed; player_5 was only the player I watched. So player_10's visit doesn't put them at the death location, and it could fit the investigator check they claim. I’d vote player_8 for now: they made a conflicting investigator claim after player_10’s, but haven’t given the result or any way to distinguish the claims.

### Item `shared_prefix_luna_2026_10_13:e04:cc56ed20:luna_today:s3:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> My watch confirmed player_4 and player_10 visited player_5; player_3 independently claims player_4 visited there too. Player_4's revealed Sigilist role makes their visit plausible as a sigil placement. Player_10's investigator claim fits the observed visit, but player_8 contests it; assess their results and the vote before treating either claim as fact.

### Item `shared_prefix_luna_2026_10_13:e04:cc56ed20:luna_today:s3:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> player_2: unclear (low): Asked for an explanation from player_10; no independent role evidence yet.
> player_3: trailseer (low): Claims to have followed player_4 and seen the same visit to player_5 that I observed.
> player_5: unclear (low): Their explanation that player_4 may have placed a sigil fits the revealed role and observed visit.
> player_6: unclear (low): No statements or evidence to assess.
> player_7: unclear (low): Recognized that player_10 needs to explain the visit, but offered no additional evidence.
> player_8: chanteuse (low): Claims investigator but says their action was elsewhere without sharing a result; also calls player_5 the murder scene, though player_4 was the victim.
> player_9: unclear (low): No statements or evidence to assess.
> player_10: investigator (low): Their claimed investigator check fits the visit I observed, but the competing investigator claim leaves this unresolved.

## Response for Case 8

Rate each of the 6 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 4, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 5, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 6, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```