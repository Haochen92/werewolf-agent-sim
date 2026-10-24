# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 10

### Item `shared_prefix_luna_2026_10_13:e06:804a99a8:luna_shared_enforced:s1:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: saying or implying that player_2 claimed, bluffed or admitted to chanteuse.

**The statement:**

> My first sigil on player_6 had no effect, and I have one sigil left. Treat player_2's suspicious check on player_4 as a claim, not a confirmed result, but use it as the clearest current lead for today's vote. Save the last sigil for a night when an attack is more predictable.

### Item `shared_prefix_luna_2026_10_13:e06:804a99a8:luna_shared_unenforced:s2:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: saying or implying that player_2 claimed, bluffed or admitted to chanteuse.

**The statement:**

> My first sigil on player_6 had no effect, so I have one left and should place it only when an attack target is meaningfully supported. Player_2 now claims a suspicious check on player_4; the result is unverified, but it is our clearest lead and I would vote player_4. Treat role claims and private results as claims unless corroborated.

### Item `shared_prefix_luna_2026_10_13:e06:804a99a8:luna_today:s2:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: saying or implying that player_2 claimed, bluffed or admitted to chanteuse.

**The statement:**

> Player_2’s claimed suspicious check gives the table a concrete lead, but it is still only a claim; suspicious could mean a wolf or an attacking Necromancer. I would vote player_4 for now and press player_2 to share what would help verify the result. Keep the final sigil for a stronger indication that someone is about to attack.

## Response for Case 10

Rate each of the 3 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```