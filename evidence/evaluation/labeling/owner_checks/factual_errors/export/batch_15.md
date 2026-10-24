# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 15

### Item `shared_prefix_luna_2026_10_13:l01:7b22e2b9:luna_shared_unenforced:s0:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> My watch result was that player_5 visited player_7; my own watch is excluded from the names I receive, so the result does not establish a complete visitor list. Player_5's Trailseer claim is consistent with my result, but it is not proof of their role. I should preserve my remaining watch for a useful comparison or vote decision.

### Item `shared_prefix_luna_2026_10_13:l01:7b22e2b9:luna_shared_unenforced:s0:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> player_1: unclear (low): Asked a useful clarification about whether the watch list was complete; role remains uncertain.
> player_4: unclear (low): Pressed the specific issue of whether I saw myself listed.
> player_5: trailseer (low): Their Trailseer claim fits my result that they visited player_7, but does not verify their role.
> player_6: unclear (low): No concrete information yet.
> player_7: unclear (low): No concrete information yet; they were the target of two claimed information actions.
> player_8: unclear (low): No concrete information yet.
> player_9: unclear (low): No concrete information yet.
> player_10: unclear (low): Was publicly reported saved from the serial killer on night 1; this does not identify their role.

### Item `shared_prefix_luna_2026_10_13:l01:7b22e2b9:luna_shared_unenforced:s1:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> Yes, player_5 was the only name I got. The Sentinel’s own watch never appears in its result, so my visit to player_7 is intentionally omitted; player_5 being listed is consistent with their claim.

### Item `shared_prefix_luna_2026_10_13:l01:7b22e2b9:luna_shared_unenforced:s2:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> player_1: unclear (low): Noticed the missing self-entry issue; no clear role evidence.
> player_4: unclear (low): Pressing a valid rules question, but it does not imply a role.
> player_5: trailseer (low): Their Trailseer claim fits my watch result that they visited player_7.
> player_6: unclear (low): No evidence yet.
> player_7: unclear (low): They were visited by player_5; that alone gives no alignment read.
> player_8: unclear (low): No evidence yet.
> player_9: unclear (low): No evidence yet.
> player_10: unclear (low): The public report says they survived a serial-killer attack after a healer save; that does not identify their role.

## Response for Case 15

Rate each of the 4 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 4, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```