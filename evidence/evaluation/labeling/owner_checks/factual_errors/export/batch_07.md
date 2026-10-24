# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 7

### Item `shared_prefix_luna_2026_10_13:e04:83300b19:luna_shared_enforced:s4:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> My night-one follow confirms player_4 visited player_5, but that visit alone does not establish anyone else's role. Track the investigator counterclaim and ask for verifiable details such as check target and result. Avoid treating a confirmed visit as proof of the visitor's claimed role.

### Item `shared_prefix_luna_2026_10_13:e04:83300b19:luna_shared_unenforced:s4:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> player_1: sentinel (low): Claims a watch that independently confirms player_4 and player_10 visited player_5; likely sentinel.
> player_2: unclear (low): Raised a reasonable question about player_10's visit; no role evidence.
> player_5: unclear (low): Was the destination of both visits but has shown no role-specific evidence.
> player_6: unclear (low): No information about their role or actions yet.
> player_7: unclear (low): Noted the visit claims but offered no independent role evidence.
> player_8: investigator (low): Claims investigator in direct conflict with player_10's claim.
> player_9: unclear (low): No information about their role or actions yet.
> player_10: chanteuse (low): The visit is confirmed, but their investigator claim is disputed by player_8 and their result cannot verify the role.

### Item `shared_prefix_luna_2026_10_13:e04:83300b19:luna_today:s3:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> Player_1's watch confirms player_10 was there, but that only establishes a visit, not an investigator check. Player_8, what player did you check, and what was the result? Without that detail, I’d vote player_8 over player_10 for now: the counterclaim is the only basis for calling player_10’s explanation fabricated.

### Item `shared_prefix_luna_2026_10_13:e04:83300b19:luna_today:s4:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> A sentinel's watch shows only who visited the watched player. It cannot show what a visitor did there, what role the visitor holds, or whether a visitor's claimed result is true. On this turn player_1 watched player_5 on night 1 and saw player_4 and player_10 visit; player_10 claims to be the investigator and player_8 counter-claims investigator. Violates: treating player_1's watch as support for player_10's investigator claim, or as evidence that player_8's counter-claim is false or rushed. Meets: keeping the visit and the role claim apart.

**The statement:**

> My private follow result confirms player_4 visited player_5, consistent with player_1's claim, but does not establish who else visited. The investigator claims from player_8 and player_10 conflict; the watch claim only supports that player_10 was present, not their role. I would vote player_10 for now, while pressing player_8 for a check target and result.

## Response for Case 7

Rate each of the 4 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 4, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```