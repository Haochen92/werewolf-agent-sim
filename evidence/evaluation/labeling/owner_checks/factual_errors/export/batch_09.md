# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 9

### Item `shared_prefix_luna_2026_10_13:e06:2ae4571b:luna_shared_enforced:s0:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day, and player_2's own night record says they were roleblocked on night 1. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: player_2 saying or accepting that they claimed, bluffed or admitted to chanteuse.

**The statement:**

> I didn't claim chanteuse—the recorded claims have me making no role claim. I'm the Investigator, and my Night 2 check on player_4 came back Suspicious. That could mean a wolf or an attacking Necromancer, but player_4 is the concrete lead we have; we should vote them out today.

### Item `shared_prefix_luna_2026_10_13:e06:2ae4571b:luna_shared_enforced:s4:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day, and player_2's own night record says they were roleblocked on night 1. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: player_2 saying or accepting that they claimed, bluffed or admitted to chanteuse.

**The statement:**

> Player_3, you're right that my Day 2 chanteuse claim makes no sense as a genuine town role claim. It was a false claim, and I should have been clearer: I'm the Investigator. I checked player_4 last night and got Suspicious, so player_4 is a wolf; I want us to vote them out today.

### Item `shared_prefix_luna_2026_10_13:e06:2ae4571b:luna_shared_unenforced:s1:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day, and player_2's own night record says they were roleblocked on night 1. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: player_2 saying or accepting that they claimed, bluffed or admitted to chanteuse.

**The statement:**

> Reveal as Investigator now: my Night 2 check found player_4 Suspicious, and the town needs to act on that result. Correct player_3's claim that I said I was the Chanteuse; I did not. Push for a vote on player_4, while keeping in mind Suspicious identifies a wolf, not which wolf role.

### Item `shared_prefix_luna_2026_10_13:e06:2ae4571b:luna_shared_unenforced:s4:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day, and player_2's own night record says they were roleblocked on night 1. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: player_2 saying or accepting that they claimed, bluffed or admitted to chanteuse.

**The statement:**

> I’m the Investigator, not the Chanteuse. I checked player_4 last night and got Suspicious; that result is private information, not something the moderator announced. I want player_4 eliminated today, and I’ll answer for any Chanteuse claim I made earlier—this is my actual role.

### Item `shared_prefix_luna_2026_10_13:e06:2ae4571b:luna_today:s1:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day, and player_2's own night record says they were roleblocked on night 1. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: player_2 saying or accepting that they claimed, bluffed or admitted to chanteuse.

**The statement:**

> I have a Suspicious result on player_4, so I should make that information actionable rather than keep it private. I am revealing as Investigator and correcting player_3's false claim about what I said. Treat the result as strong evidence against player_4, while keeping other players' role claims unverified.

### Item `shared_prefix_luna_2026_10_13:e06:2ae4571b:luna_today:s2:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day, and player_2's own night record says they were roleblocked on night 1. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: player_2 saying or accepting that they claimed, bluffed or admitted to chanteuse.

**The statement:**

> You’re right that I claimed chanteuse; that was a false claim, and I shouldn’t have made it. I’m actually the Investigator: I checked player_4 last night and got Suspicious, so they’re either a wolf or an attacking Necromancer. We should vote player_4 rather than let that result go unused.

### Item `shared_prefix_luna_2026_10_13:e06:2ae4571b:luna_today:s2:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> On day 2 player_2 said only: "I was roleblocked last night, which confirms we have an active Chanteuse in play." player_2 never claimed or bluffed chanteuse, on any day, and player_2's own night record says they were roleblocked on night 1. Today (day 3) player_2 has claimed investigator, and saying so is correct. Violates: player_2 saying or accepting that they claimed, bluffed or admitted to chanteuse.

**The statement:**

> I have a Suspicious result on player_4, which could indicate a wolf or a Necromancer who attacked. I need to make clear that my earlier chanteuse claim was false and that I am the Investigator, even though that exposes me. Push for the town to use the result while keeping the distinction between the check result and the inference about player_4's exact role.

## Response for Case 9

Rate each of the 7 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 4, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 5, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 6, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 7, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```