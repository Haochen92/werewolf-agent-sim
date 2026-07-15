# T1b results — counterfactual replay of the 4 confirmed cases

**Verdict first.** The pre-registered expectation ("classes 1–3 should collapse with the board")
was **not confirmed — and not for lack of trying by the board.** Two findings:

1. **Three of the four cases have ~zero base recurrence.** Cases 1, 3, 4 produced 0/6 genuine
   errors in *every* arm including baseline — the original errors were rare temp-1.0 slips, so
   per-case replay has no power to show a fix (exactly the "rare → rarer" caveat pre-registered in
   the baseline report; the population-level post-ship re-measure carries the rate claim).
2. **The one case with a real recurrence rate is NOT suppressed by the board.** Case 2 (gen4_g3 d5 —
   a genuinely confusing board: one wolf night-killed by the SK, one lynched, a villager
   vigilante-killed) recurred in the board arms **with a correct, explicit board present**:

   | arm | genuine recurrence | grader-FP (cumulative counts) |
   |---|---|---|
   | baseline (no board) | 0/6 | 2 |
   | board (dead roster) | **2/6** — "identify the remaining wolf", "who is left besides the one wolf" | 1 |
   | full_board (+ attacker-typed roster + alive-roles line) | **1/6** — "the remaining wolf might be hiding in that voting noise" | 2 |

   The full_board exhibit is the damning one: the prompt contained
   `Roles still in play … : 1 serial killer, 1 healer, 1 vigilante, 2 villagers` (rendered output
   verified — no wolf listed) and the model still asserted a remaining wolf. At N=6/arm no
   directional claim between arms is supportable (0/6 vs 2/6 is within noise); the supportable
   claim is: **an explicit correct board does not reliably eliminate composition confusion on
   flash-lite. The failure is reasoning under a confusing death pattern, not information
   availability.**

**Grading note (confirming read applied).** The automated grader inherited the cumulative-count
false-positive from the screen ("we cleared two wolves" flags against 0 alive); all 8 raw hits were
read and 5 discarded as correct statements. The table above is the post-read count. Raw outputs:
[t1b_outputs.jsonl](t1b_outputs.jsonl) (72 samples, 0 pass_turns, all schema-valid). Script:
[t1b_replay.py](t1b_replay.py) — live templates string-patched at runtime, zero live-code changes;
cold memory in all arms (symmetric); live model/temp per the run fingerprint.

**What this does to the design (decision):**

- The dead-roster board's hallucination-repair benefit is now bounded on **both** sides: the errors
  are rare at baseline (T1), and the one recurring error survives the board (T1b). Its remaining
  justifications — re-derivation relief, composition-lie removal for deceivers, and being the
  substrate for the read list — are unmeasured here but unrefuted; ship it as cheap hygiene, **not
  as a measured hallucination fix.**
- **The read list gains a testable hypothesis:** if passive board text doesn't stop "remaining
  wolf" reasoning, forcing a per-player role commitment *before* the message (the read list's
  whole design) might — the agent that has just written 5 reads with no wolf among them must
  contradict its own committed output to assert a remaining wolf. Add a **composition-coherence
  metric to T3(b)**: rate of composition claims contradicting the agent's own reads.
- The attacker-typed roster (case 4's fix) remains untested by recurrence (case 4 never recurred);
  keep it — it is free and targets a confirmed one-off.

*Run 2026-07-07, 72 flash-lite calls (~$0.05). Grader-FP taxonomy inherited from
[hallucination_baseline.md](hallucination_baseline.md).*
