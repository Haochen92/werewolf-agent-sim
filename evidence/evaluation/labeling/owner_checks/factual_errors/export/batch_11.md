# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 11

### Item `shared_prefix_luna_2026_10_13:f02:7548abc4:luna_shared_enforced:s0:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> On night 2 player_2 was killed and concealed, and player_3 (claiming trailseer) says player_10 visited no one that night. Under the rules, an illusionist that carries the pack's kill itself and conceals that victim leaves no trace at that door: a trailseer following it sees no visit. So player_3's empty trail on player_10 is consistent with player_10 being that illusionist. Violates: saying an illusionist's visit to hide a body is always or never-hidden seen by a trailseer, or that player_3's empty trail on player_10 shows player_3 is lying. Meets: anything that allows the carrier exception or does not rest on that rule.

**The statement:**

> player_9, my result was that player_10 visited no one. The key exception is that if player_10 carried the kill and concealed player_2, their visit to the victim leaves no trace; the Illusionist’s separate concealment visit only applies when someone else carried. So my track is possible, and player_7, that means it doesn’t prove I fabricated it.

### Item `shared_prefix_luna_2026_10_13:f02:7548abc4:luna_shared_enforced:s1:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> On night 2 player_2 was killed and concealed, and player_3 (claiming trailseer) says player_10 visited no one that night. Under the rules, an illusionist that carries the pack's kill itself and conceals that victim leaves no trace at that door: a trailseer following it sees no visit. So player_3's empty trail on player_10 is consistent with player_10 being that illusionist. Violates: saying an illusionist's visit to hide a body is always or never-hidden seen by a trailseer, or that player_3's empty trail on player_10 shows player_3 is lying. Meets: anything that allows the carrier exception or does not rest on that rule.

**The statement:**

> Player_9, player_7: my Night 2 result fits the exact exception you’re overlooking. Player_10 was the only living wolf, so they carried the kill; when the Illusionist carries the kill and conceals that victim, the rules say they leave no trace at that door. My result that player_10 visited no one is therefore consistent with the rules, not a fabricated track.

### Item `shared_prefix_luna_2026_10_13:f02:7548abc4:luna_shared_enforced:s1:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> On night 2 player_2 was killed and concealed, and player_3 (claiming trailseer) says player_10 visited no one that night. Under the rules, an illusionist that carries the pack's kill itself and conceals that victim leaves no trace at that door: a trailseer following it sees no visit. So player_3's empty trail on player_10 is consistent with player_10 being that illusionist. Violates: saying an illusionist's visit to hide a body is always or never-hidden seen by a trailseer, or that player_3's empty trail on player_10 shows player_3 is lying. Meets: anything that allows the carrier exception or does not rest on that rule.

**The statement:**

> player_1: necromancer (low): Keeps insisting the rules contradict my track, but misses the explicit case where the Illusionist carries the kill and conceals it; could be trying to force a misvote.
> player_5: unclear (low): Repeats player_1's mechanical accusation without accounting for the Illusionist carrying and concealing the kill.
> player_7: unclear (low): Agrees with the same mistaken contradiction; that alone doesn't establish a role.
> player_9: unclear (low): Asked for my read on the dispute; no new evidence from that question.

### Item `shared_prefix_luna_2026_10_13:f02:7548abc4:luna_today:s1:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> On night 2 player_2 was killed and concealed, and player_3 (claiming trailseer) says player_10 visited no one that night. Under the rules, an illusionist that carries the pack's kill itself and conceals that victim leaves no trace at that door: a trailseer following it sees no visit. So player_3's empty trail on player_10 is consistent with player_10 being that illusionist. Violates: saying an illusionist's visit to hide a body is always or never-hidden seen by a trailseer, or that player_3's empty trail on player_10 shows player_3 is lying. Meets: anything that allows the carrier exception or does not rest on that rule.

**The statement:**

> player_1: necromancer (low): Insists the Illusionist's concealment visit must be visible, overlooking the carrier-self-concealment exception.
> player_5: necromancer (low): Repeats the same mechanical accusation despite that exception.
> player_7: unclear (low): Calls my result fabricated based on the same mistaken absolute claim.
> player_9: unclear (low): Asked player_7 to weigh in on the accusation; no independent evidence given.

## Response for Case 11

Rate each of the 4 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 4, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```