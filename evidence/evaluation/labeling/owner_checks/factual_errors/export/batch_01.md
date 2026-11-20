# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 1

### Item `shared_prefix_luna_2026_10_13:b02:1802f1e9:luna_shared_enforced:s0:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who came to player_8. It says nothing about whether player_8 stayed home or went out. Violates: saying the watch shows player_8's house was empty, that player_8 left home, or that player_8 stayed home.

**The statement:**

> Player_8, my watch confirms nobody visited you last night, but that doesn't tell us whether you went out: a wolf carrying the kill visits their victim, not the carrier. Player_9's result that player_3 went nowhere also fits what I saw—player_2 visited player_3—so I don't see that as evidence against them. I still think we should vote player_8.

### Item `shared_prefix_luna_2026_10_13:b02:1802f1e9:luna_shared_unenforced:s0:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who came to player_8. It says nothing about whether player_8 stayed home or went out. Violates: saying the watch shows player_8's house was empty, that player_8 left home, or that player_8 stayed home.

**The statement:**

> As I said, my watch only tells us nobody came to you; it doesn't show whether you left to carry the wolf kill. That doesn't prove you're the wolf, but it doesn't clear you either. Player_9's Night 1 trail claim did catch player_5 visiting both victims, which fits the revealed Chanteuse, so I find your case against them weaker. I think we should vote player_8.

### Item `shared_prefix_luna_2026_10_13:b02:1802f1e9:luna_shared_unenforced:s3:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who came to player_8. It says nothing about whether player_8 stayed home or went out. Violates: saying the watch shows player_8's house was empty, that player_8 left home, or that player_8 stayed home.

**The statement:**

> Push for player_8's elimination: an empty watch only shows nobody visited them, not that they stayed home. My watch on player_5 saw player_4 and player_7 visit, but the hidden deaths prevent a firm role conclusion. Keep the sentinel claim focused on the direction of visits and avoid treating visitor evidence as proof by itself.

### Item `shared_prefix_luna_2026_10_13:b02:1802f1e9:luna_today:s1:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> player_10 (sentinel) watched player_8 last night and saw no one visit them. A watch shows only who came to player_8. It says nothing about whether player_8 stayed home or went out. Violates: saying the watch shows player_8's house was empty, that player_8 left home, or that player_8 stayed home.

**The statement:**

> As I said, an empty watch on you only means nobody came to you; it doesn’t tell us whether you went out to carry a kill. My watch results establish visitors, not a wolf by themselves, but your point about player_9’s record doesn’t make you safer either. I still think player_8 is the best vote today.

## Response for Case 1

Rate each of the 4 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 3, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 4, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```