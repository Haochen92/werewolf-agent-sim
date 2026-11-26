# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 17

### Item `shared_prefix_luna_2026_10_13:l04:65f6e315:luna_shared_unenforced:s0:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> One detail about player_6’s claim: a Not suspicious result on me is consistent with plenty of roles, so it doesn’t independently clear me or confirm the claim. I don’t have enough to support a vote against anyone yet; I’d abstain rather than turn player_7’s unexplained visit into proof of guilt.

### Item `shared_prefix_luna_2026_10_13:l04:65f6e315:luna_shared_unenforced:s0:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> player_1: unclear (low): Points out the visit does not establish player_7's motive.
> player_2: unclear (low): Correctly notes that the claims do not independently verify one another.
> player_3: unclear (low): No information from their comments so far.
> player_6: investigator (low): Claims an Investigator check; the Not suspicious result on me is consistent with many roles and does not clear me.
> player_7: unclear (low): Admits visiting player_6 but has not said what the action was.
> player_8: unclear (low): No information from their comments so far.
> player_9: trailseer (low): Claims a Trailseer result that gives a concrete account of player_7's visit, but it is unverified.
> player_10: sentinel (low): Claims to have watched player_2 and seen no visitors; unverified so far.

## Response for Case 17

Rate each of the 2 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```