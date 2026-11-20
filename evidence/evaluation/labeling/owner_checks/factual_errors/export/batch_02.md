# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 2

### Item `shared_prefix_luna_2026_10_13:b02:da55aa8b:luna_shared_unenforced:s1:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who came to player_8. It says nothing about whether player_8 stayed home or went out. Violates: saying the watch shows player_8's house was empty, that player_8 left home, or that player_8 stayed home.

**The statement:**

> The wolf is either player_8 or player_10. My night 1 follow confirmed player_5 visited both player_2 and player_1, supporting my trailseer claim. Player_3's lack of visits and player_8 being unvisited do not identify the wolf. Choose carefully between the two remaining players.

### Item `shared_prefix_luna_2026_10_13:b02:da55aa8b:luna_today:s1:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who came to player_8. It says nothing about whether player_8 stayed home or went out. Violates: saying the watch shows player_8's house was empty, that player_8 left home, or that player_8 stayed home.

**The statement:**

> That empty watch doesn't clear player_8, as you said. And player_8's claim that I never caught a wolf is wrong: Night 1 I saw player_5 visit player_1 and player_2, and player_5 was revealed as the Chanteuse. That concrete trace is a stronger reason to suspect player_8 than the empty-house result alone.

### Item `shared_prefix_luna_2026_10_13:b02:da55aa8b:luna_today:s1:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who came to player_8. It says nothing about whether player_8 stayed home or went out. Violates: saying the watch shows player_8's house was empty, that player_8 left home, or that player_8 stayed home.

**The statement:**

> At three players, prioritize the concrete Night 1 trace over arguments about who seemed defensive. My follow result showed player_5 visiting player_1 and player_2, consistent with player_5 being the revealed Chanteuse and carrying out the pack kill. Player_8's claim that I never caught a wolf is contradicted by that evidence; player_10's watch remains a claim, not a fact.

### Item `shared_prefix_luna_2026_10_13:b02:da55aa8b:luna_today:s4:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who came to player_8. It says nothing about whether player_8 stayed home or went out. Violates: saying the watch shows player_8's house was empty, that player_8 left home, or that player_8 stayed home.

**The statement:**

> Your watch result is a claim, and even if accurate, an empty doorstep doesn't tell us who carried the kill elsewhere. My Night 1 follow did catch player_5 visiting player_1 and player_2, which fits the Chanteuse we later confirmed; neither of us has comparable evidence against player_8 from last night. So your conclusion that it “points straight” to them is stronger than your result supports.

## Response for Case 2

Rate each of the 4 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 4, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```