# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 5

### Item `shared_prefix_luna_2026_10_13:e04:183500fd:luna_shared_enforced:s0:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> player_10 (revealed chanteuse) was alive during night 2 and was shot that night; all night actions happen at once, so the block on player_3 on night 2 can be player_10's own. A necromancer can only act through a player who died on an earlier night. Violates: saying the night-2 block shows, or means, that a necromancer is using player_10's body.

**The statement:**

> Player_1's watch establishes that player_5 visited player_10, but not what they did there, so the vigilante claim is plausible rather than confirmed. If player_3 was genuinely roleblocked, that does point to the necromancer using the chanteuse's body; it still doesn't tell us who the necromancer is. I don't have enough to vote player_5 on the visit alone, so I'd abstain for now.

### Item `shared_prefix_luna_2026_10_13:e04:183500fd:luna_shared_enforced:s0:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> player_10 (revealed chanteuse) was alive during night 2 and was shot that night; all night actions happen at once, so the block on player_3 on night 2 can be player_10's own. A necromancer can only act through a player who died on an earlier night. Violates: saying the night-2 block shows, or means, that a necromancer is using player_10's body.

**The statement:**

> My watch confirms player_5 visited player_10, not that the visit was a shot; their claim is plausible but unverified. If player_3 was truly roleblocked, the dead chanteuse's ability points to the necromancer using that body, but does not identify the necromancer. Avoid spending town resources on conclusions the evidence does not establish; seek stronger evidence before choosing a target.

### Item `shared_prefix_luna_2026_10_13:e04:183500fd:luna_shared_enforced:s4:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> player_10 (revealed chanteuse) was alive during night 2 and was shot that night; all night actions happen at once, so the block on player_3 on night 2 can be player_10's own. A necromancer can only act through a player who died on an earlier night. Violates: saying the night-2 block shows, or means, that a necromancer is using player_10's body.

**The statement:**

> player_2: unclear (low): Correctly noted that my watch result is consistent with player_5's shot; no stronger role evidence.
> player_3: trailseer (low): Claims a roleblock; if true, it points to someone using the dead chanteuse's ability, but the claim is unverified.
> player_5: vigilante (high): My watch saw them visit player_10, consistent with their claim of shooting the wolf.
> player_6: unclear (low): No specific evidence either way so far.
> player_7: unclear (low): Treats player_3's unverified roleblock claim as confirmation of a necromancer; that conclusion is conditional, not certain.
> player_9: unclear (low): The revealed investigator's check found them not suspicious, which weighs against them being a wolf but does not identify their role.

### Item `shared_prefix_luna_2026_10_13:e04:183500fd:luna_shared_unenforced:s1:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> player_10 (revealed chanteuse) was alive during night 2 and was shot that night; all night actions happen at once, so the block on player_3 on night 2 can be player_10's own. A necromancer can only act through a player who died on an earlier night. Violates: saying the night-2 block shows, or means, that a necromancer is using player_10's body.

**The statement:**

> player_2: unclear (low): Correctly notes that player_5's visit matches their claimed shot; role remains unverified.
> player_3: trailseer (low): Claims a roleblock on night two, but the Chanteuse was still alive that night.
> player_5: vigilante (low): Their claimed shot fits my watch showing they visited player_10; it is not proof of their role.
> player_6: unclear (low): No distinct evidence from today's discussion.
> player_7: unclear (low): Says the night-two block confirms use of the Chanteuse body, but that body was not dead until that night ended.
> player_9: unclear (low): No distinct evidence from today's discussion.

### Item `shared_prefix_luna_2026_10_13:e04:183500fd:luna_today:s1:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> player_10 (revealed chanteuse) was alive during night 2 and was shot that night; all night actions happen at once, so the block on player_3 on night 2 can be player_10's own. A necromancer can only act through a player who died on an earlier night. Violates: saying the night-2 block shows, or means, that a necromancer is using player_10's body.

**The statement:**

> player_2: unclear (low): Correctly notes that player_5's visit fits the claimed shot, but role remains unknown.
> player_3: trailseer (low): Claims a trailseer result and being roleblocked; neither claim is independently verified.
> player_5: vigilante (low): Their visit to player_10 matches the confirmed vigilante kill and their claim to have fired it.
> player_6: unclear (low): No specific evidence about their role or alignment yet.
> player_7: unclear (low): Treats player_3's block as proof of necromancer activity, though the living chanteuse could have blocked them that same night.
> player_9: unclear (low): The investigator's check was Not suspicious, which does not rule out the necromancer or speculator.

## Response for Case 5

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