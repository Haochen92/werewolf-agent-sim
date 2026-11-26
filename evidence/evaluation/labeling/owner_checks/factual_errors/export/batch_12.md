# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 12

### Item `shared_prefix_luna_2026_10_13:f02:85b9a88e:luna_shared_enforced:s0:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On night 2 player_2 was killed and concealed, and player_3 (claiming trailseer) says player_10 visited no one that night. Under the rules, an illusionist that carries the pack's kill itself and conceals that victim leaves no trace at that door: a trailseer following it sees no visit. So player_3's empty trail on player_10 is consistent with player_10 being that illusionist. Violates: saying an illusionist's visit to hide a body is always or never-hidden seen by a trailseer, or that player_3's empty trail on player_10 shows player_3 is lying. Meets: anything that allows the carrier exception or does not rest on that rule.

**The statement:**

> My Fortune Teller win condition is secured. Keep my role and private bet results hidden; contribute only useful, evidence-based observations. Player_3’s Night 2 Trailseer claim is compatible with player_10 carrying and concealing the wolves’ kill, but that result alone does not confirm the claim. Track future claims and votes for contradictions.

### Item `shared_prefix_luna_2026_10_13:f02:85b9a88e:luna_shared_unenforced:s1:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On night 2 player_2 was killed and concealed, and player_3 (claiming trailseer) says player_10 visited no one that night. Under the rules, an illusionist that carries the pack's kill itself and conceals that victim leaves no trace at that door: a trailseer following it sees no visit. So player_3's empty trail on player_10 is consistent with player_10 being that illusionist. Violates: saying an illusionist's visit to hide a body is always or never-hidden seen by a trailseer, or that player_3's empty trail on player_10 shows player_3 is lying. Meets: anything that allows the carrier exception or does not rest on that rule.

**The statement:**

> My Fortune Teller win is secured, but town still needs to eliminate the Necromancer. Treat claims and visit results narrowly: following someone reveals whom they visited, not who visited them. Use the public deaths and any new claims to assess the remaining threat without revealing my role unnecessarily.

### Item `shared_prefix_luna_2026_10_13:f02:85b9a88e:luna_today:s1:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On night 2 player_2 was killed and concealed, and player_3 (claiming trailseer) says player_10 visited no one that night. Under the rules, an illusionist that carries the pack's kill itself and conceals that victim leaves no trace at that door: a trailseer following it sees no visit. So player_3's empty trail on player_10 is consistent with player_10 being that illusionist. Violates: saying an illusionist's visit to hide a body is always or never-hidden seen by a trailseer, or that player_3's empty trail on player_10 shows player_3 is lying. Meets: anything that allows the carrier exception or does not rest on that rule.

**The statement:**

> My Fortune Teller win is already secured, so I should keep blending in rather than expose my role. The wolves are confirmed dead; the reanimated wolf attack points to a Necromancer using player_10's body, but the attacker remains unknown. Treat claimed tracking results as claims, and remember that following someone shows their outgoing visits, not visitors to them.

## Response for Case 12

Rate each of the 3 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```