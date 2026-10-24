# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 16

### Item `shared_prefix_luna_2026_10_13:l01:dff43694:luna_shared_enforced:s0:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> Player_3's watch and player_5's follow account fit together: player_5 says they went to player_7, and player_3 says player_7 went nowhere. That supports both claims, though it doesn't prove either. I don't have enough to name a vote target yet, so I'd abstain rather than vote against someone on this alone.

### Item `shared_prefix_luna_2026_10_13:l01:dff43694:luna_shared_enforced:s4:u1`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> player_3: sentinel (low): Claims a watch result; player_5's visit is consistent with it, but neither claim is verified.
> player_4: unclear (low): No evidence yet.
> player_5: trailseer (low): Claims a follow result that is consistent with player_3's watch claim.
> player_6: unclear (low): No evidence yet.
> player_7: unclear (low): No evidence yet.
> player_8: unclear (low): No evidence yet.
> player_9: unclear (low): No evidence yet.
> player_10: unclear (low): Was publicly reported saved from a serial killer attack; that does not identify their role.

### Item `shared_prefix_luna_2026_10_13:l01:dff43694:luna_shared_unenforced:s2:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> player_3: sentinel (low): Claims a watch showing player_5 visited player_7; unverified, but it does not conflict with player_5's claim.
> player_4: unclear (low): No information yet to distinguish their role or alignment.
> player_5: trailseer (low): Claims to have followed player_7; their result that player_7 visited no one is compatible with player_3's claim.
> player_6: unclear (low): No information yet to distinguish their role or alignment.
> player_7: unclear (low): The two claims about them can both be true; no read from that alone.
> player_8: unclear (low): No information yet to distinguish their role or alignment.
> player_9: unclear (low): No information yet to distinguish their role or alignment.
> player_10: unclear (low): Was publicly reported saved from the serial killer on night one; this does not establish their role.

## Response for Case 16

Rate each of the 3 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```