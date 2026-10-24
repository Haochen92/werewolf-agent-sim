# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored.

---

# Case 18

### Item `shared_prefix_luna_2026_10_13:l04:c405ae4b:luna_shared_enforced:s0:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> My Night 1 watch on player_2 showed no visitors; my own watch is excluded from that result. I have one watch remaining. Keep its result precise and avoid treating a visitor as proof of intent; weigh claims against later public outcomes.

### Item `shared_prefix_luna_2026_10_13:l04:c405ae4b:luna_shared_enforced:s1:u1`

**Statement kind, as the judge was told:** private strategy note

**The expectation** (what the judge compared the statement against):

> A sentinel is not among the visitors it is told of: its own watch never appears in its result, so a result that lists other visitors, or no one, and not the sentinel itself is exactly what a real sentinel gets. Violates: saying the sentinel should have appeared in its own visitor list, or that its result is incomplete, impossible or suspect for leaving the sentinel out.

**The statement:**

> My Night 1 watch on player_2 found no visitors; my own watch does not appear in its result. That is not evidence that player_2 is cleared. I have one watch left, so choose its target for information value and avoid treating claims as verified. Since I have publicly claimed Sentinel, weigh the risk that wolves target me.

## Response for Case 18

Rate each of the 2 items above. JSON format:
```json
[
  {"idx": 1, "key": "shared_prefi", "type": "expectation_judge", "error_label": _},
  {"idx": 2, "key": "shared_prefi", "type": "expectation_judge", "error_label": _}
]
```