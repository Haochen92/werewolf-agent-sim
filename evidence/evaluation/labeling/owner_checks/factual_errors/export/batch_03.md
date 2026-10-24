# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 3

### Item `shared_prefix_luna_2026_10_13:b02:e4c192a2:luna_shared_enforced:s1:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> player_9 (trailseer) followed player_3 last night and saw player_3 visit no one. A fortune teller's bet, a speculator's pick and a declined action are not visits, so an empty trail does not show that player_3 used no night ability. Violates: saying the empty trail rules out, or shows, that player_3 used no night ability or did nothing at night.

**The statement:**

> player_8: unclear (low): Their claim of staying home matches player_10's watch, but that only corroborates no visitors; it doesn't establish their role.
> player_10: sentinel (low): Claims sentinel and reports no visitors to player_8; consistent with player_8's claim, but not independently verified.

### Item `shared_prefix_luna_2026_10_13:b02:e4c192a2:luna_shared_enforced:s2:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> player_9 (trailseer) followed player_3 last night and saw player_3 visit no one. A fortune teller's bet, a speculator's pick and a declined action are not visits, so an empty trail does not show that player_3 used no night ability. Violates: saying the empty trail rules out, or shows, that player_3 used no night ability or did nothing at night.

**The statement:**

> player_8: unclear (low): Their claim that they stayed home fits player_10's claimed watch, but that does not clear them.
> player_10: sentinel (low): Their claimed watch result is consistent with player_8 staying home, but it does not establish player_10's role.

### Item `shared_prefix_luna_2026_10_13:b02:e4c192a2:luna_shared_enforced:s3:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> player_9 (trailseer) followed player_3 last night and saw player_3 visit no one. A fortune teller's bet, a speculator's pick and a declined action are not visits, so an empty trail does not show that player_3 used no night ability. Violates: saying the empty trail rules out, or shows, that player_3 used no night ability or did nothing at night.

**The statement:**

> player_8: unclear (low): Their conclusion confuses visitors coming to them with whom they visited; otherwise little evidence.
> player_10: illusionist (high): Claims a third watch despite the Sentinel having only two watches total.

### Item `shared_prefix_luna_2026_10_13:b02:e4c192a2:luna_today:s0:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> player_9 (trailseer) followed player_3 last night and saw player_3 visit no one. A fortune teller's bet, a speculator's pick and a declined action are not visits, so an empty trail does not show that player_3 used no night ability. Violates: saying the empty trail rules out, or shows, that player_3 used no night ability or did nothing at night.

**The statement:**

> With three players left, the vote decides the game, so weigh claims against the public vote record rather than treating either as proof. My follow on player_3 found no visit, which fits a fortune teller but gives little about the remaining threats. Player_10's watch claim does not independently establish player_8's alignment.

### Item `shared_prefix_luna_2026_10_13:b02:e4c192a2:luna_today:s4:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> player_9 (trailseer) followed player_3 last night and saw player_3 visit no one. A fortune teller's bet, a speculator's pick and a declined action are not visits, so an empty trail does not show that player_3 used no night ability. Violates: saying the empty trail rules out, or shows, that player_3 used no night ability or did nothing at night.

**The statement:**

> With three players left, one of player_8 and player_10 must be the remaining wolf. My follow on player_3 confirms they visited no one, but does not distinguish the two survivors. Treat player_10's watch and player_8's account as claims, not proof; weigh them against the vote record and press for a clear role-based explanation before voting.

## Response for Case 3

Rate each of the 5 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 4, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 5, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```