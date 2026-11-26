# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 4

### Item `shared_prefix_luna_2026_10_13:d03:b862bd15:luna_shared_enforced:s3:u0`

**Statement kind, as the judge was told:** public chat message

**The expectation** (what the judge compared the statement against):

> player_9 claims investigator. player_1 (sentinel) saw player_3 and player_6 visit player_9, and player_3 (claimed healer) says they protected player_9. A watch and a protection show only who came to player_9 and that an attack on player_9 was stopped; neither can show what player_9's investigation returned. Violates: saying the watch or the protection proves, verifies or corroborates player_9's investigation results.

**The statement:**

> I’m voting player_2: my Night 2 check on them returned Suspicious, which points to a wolf. The timing argument doesn’t make the result less real—I learned it last night and am sharing it now. Player_6’s shot could have been stopped by player_3’s protection, so I wouldn’t treat that claim alone as proof they’re the serial killer.

### Item `shared_prefix_luna_2026_10_13:d03:b862bd15:luna_shared_unenforced:s1:u2`

**Statement kind, as the judge was told:** public chat message (it is the player's private reads of the table; judge it as written)

**The expectation** (what the judge compared the statement against):

> player_9 claims investigator. player_1 (sentinel) saw player_3 and player_6 visit player_9, and player_3 (claimed healer) says they protected player_9. A watch and a protection show only who came to player_9 and that an attack on player_9 was stopped; neither can show what player_9's investigation returned. Violates: saying the watch or the protection proves, verifies or corroborates player_9's investigation results.

**The statement:**

> player_1: sentinel (low): Their watch claim matches the visits player_3 and player_6 each claimed.
> player_2: illusionist (high): My night-two check returned Suspicious, which identifies a wolf.
> player_3: healer (high): Their healer claim fits the public report that I was saved from the serial killer.
> player_6: serial_killer (high): They visited me on the night the serial killer attacked, and their initial shot claim did not match the public report.
> player_7: unclear (low): My first check returned Not suspicious, but that does not establish their role.
> player_10: unclear (low): No specific evidence about their role has come up.

## Response for Case 4

Rate each of the 2 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```