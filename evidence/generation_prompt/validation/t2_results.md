# T2 + T3 results — regression replay, reads soundness, ordering A/B

60 frozen decisions (40 day-vote / 20 night, all with original retrieved memories from the eval-case
sidecars), replayed under 4 arms, 200 calls, 100% schema-valid. Raw rows:
[t2_outputs.jsonl](t2_outputs.jsonl); script: [regression_replay.py](regression_replay.py).

## T2 — non-regression: PASS, no tripwire fired

| arm | valid | verdict coverage (mem / sp) | sp verdicts (fol / n-rel / ovr) | out tokens |
|---|---|---|---|---|
| old (no board) | 60/60 | 1.00 / 0.98 | .51 / .43 / .06 | 375 |
| board | 60/60 | 1.00 / 0.99 | .51 / .44 / .05 | 384 |
| reads_first | 40/40 | 1.00 / 1.00 | .49 / .34 / **.17** | 599 |
| reads_after | 40/40 | 0.97 / 1.02 | .54 / .40 / .06 | 637 |

- **The attention-dilution fear did not materialize**: verdict coverage holds at ~1.0 even with 8
  forced reads + whys in the schema; zero parse failures anywhere.
- **The board is token-free** (375→384); **the reads cost +60% output tokens** (~+220/call) — the
  predicted dominant cost, now measured.
- **Flip metrics are noise-dominated and reported as such**: action-flip vs the original recorded
  action is ~0.5 *in the unchanged old arm too* (temp-1.0 resampling + reconstruction variance), and
  verdict agreement with originals is ~0.55 in every arm. Lesson recorded: the next replay design
  should include **same-arm resample pairs** to calibrate the flip noise floor before reading
  between-arm flips (old-vs-board 12/40 differ — uninterpretable without that floor).

## T3(a) — reads instrument: viable, with one enforcement gap

Across 410 reads in the two reads arms: **wolf-pack golden probe 9/9** (wolves privately read their
packmates as wolves — the field is filled honestly from private knowledge); **not degenerate**
(unclear 57%, low-confidence dominant — healthy skepticism, with 43% committed guesses);
committed-guess role accuracy 0.47–0.60 (vs ~0.17 blind random; faction accuracy 0.63–0.73 is *not*
clearly above the always-town baseline — the proper Brier-vs-cast-prior scoring stays with the live
T3). **Completeness is the gap: 0.84–0.85**, not 1.0 — but the mechanism is NOT the predicted
list-truncation (the length hypothesis was checked and falsified): the longest lists are covered
*best* (8 living others → 3% missed, day-1 boards) and mid-game boards are worst (3–7 others →
17–25% missed); skipped players overwhelmingly spoke that day (69/74); no dead players were ever
included, no duplicates, and misses are position-uniform. The signature is **selective omission
under generation effort** — mid-game reads require differentiated content per player, and
flash-lite economizes by dropping players outside its active reasoning threads (the same laziness
signature as the cold "unchanged" filler). **Decision: T4's completeness check must be a hard
validator — a parse-time retry naming the omitted player ids (the alive set is deterministic) —
not a monitor.** Build spec addendum (user, 2026-07-07): the instruction line itself enumerates the
expected targets via a **dynamic placeholder** — a derived `read_targets` key (surviving minus
self) filled in `build_agent_prompt_input`, "one entry each for: {read_targets}" — never
hard-coded ids; the validator's retry message reuses the same derived list. Zero self-reads
(instruction followed).

**Enumeration probe (same 40 decisions, `reads_enum` arm, 2026-07-07):** the dynamic-enumeration
instruction lifts completeness **0.85 → 0.93** (29/40 perfect; mid-game misses halved to 8–10%,
day-1 boards perfect) — but not to 1.0: effort-driven omission survives an explicit id list.
"Unchanged"-filler rate unchanged by enumeration (89/226) — a separate failure owned by the
feedback wiring. Rows: [t2_enum_outputs.jsonl](t2_enum_outputs.jsonl).

**Completeness policy — REVISED (user call, 2026-07-07), superseding the hard-validator decision
above.** An importance check settled it: agents essentially never act on an unread player (0/40
enum, 1/80 original arms voted for a player missing from their reads), and misses skew *away* from
threats (evil roles ~12% of misses vs ~37% of cast — the skipped players are the ones there's
nothing to say about). So a content-level completeness retry is not worth its cost (~27% of
mid-game decisions re-generated to recover ~7% of near-empty entries). **Final policy:**
(a) dynamic enumeration ships (the measured miss-halver); (b) missing reads are **imputed at
analysis time** as `unclear/low` (cast-prior for Brier scoring); (c) completeness is a **monitored
metric** with a tripwire (revisit if a future model/prompt change drops it below ~0.85);
(d) **no content retry** — the standard transport/parse retry layer (429s, schema-invalid) that
already wraps live LLM calls is unaffected and stays.

## T3 ordering A/B — a genuine split, not a winner

- **reads_first** (verdicts → reads → strategy → vote): **triples the SP override rate**
  (0.17 vs ~0.06 in all other arms) — committing evidence first makes the agent actually check
  strategy points against its own reads, exactly the synergy-instruction behavior the memory system
  wants. But its reads are lazier: 40% "unchanged" whys **on a cold first elicitation where
  "unchanged" is meaningless** (filler artifact), fewer distinct whys (109/204), lower guess
  accuracy (0.47).
- **reads_after** (verdicts → strategy → reads → vote): better reads — 17% "unchanged", 152/206
  distinct whys, 0.60 accuracy — but standard override rate (0.06).

**Decision: ship reads_first as the default** (the override effect is the one that feeds credit
quality, and the "unchanged" laziness should shrink once fed-back prior reads exist and the sentinel
becomes meaningful) — but the call is explicitly provisional: **re-run this A/B in the live smoke
with feedback wired**, where the cold-start artifact disappears and the composition-coherence metric
(added post-T1b) can arbitrate. If reads_first's read quality stays degraded live, flip the order.

*Run 2026-07-07, 200 flash-lite calls (~$0.15). Caveats: replay is turn-cold on read feedback
(pre-registered); abstain allowed in all replays (a few originals may have been forced days);
knowledge masking approximated (wolf packmates only — investigator-checked masking deferred to the
live scoring).*
