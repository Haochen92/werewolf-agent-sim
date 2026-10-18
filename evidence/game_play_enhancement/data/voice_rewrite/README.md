# Voice rewrite screen (2026-10-18)

**Question (owner):** would a second, short model call that rewrites a seat's spoken line in a
persona's voice, keeping the argument, read better, and how often would it change the facts?

**Method.** Runner: `evaluation/experiments/voice_rewrite_screen.py` (prompt and gate in the file).
- Lines: 30 real AI lines. Twenty were drawn at random from the two captured Haiku games (645228e7,
  88aee4e4; the human seat's lines left out). Ten came from the deduction placement screen
  (`evidence/reasoning_failures/data/deduction_placement_n10/`, the new prompts).
- Rewrites: Haiku 5.5 (thinking low) rewrote each line once in each of three voices (blunt, warm,
  dry), seeing only the line and the voice, never the game.
- Fact gate (deterministic): the rewrite must name the same players, the same nights and the same
  role words as the original.
- Judging: four blind Sonnet chat subagents. Two judged naturalness on X/Y pairs in a seeded order
  (key in `blind_key.json`); two judged argument fidelity, original against rewrite, as
  same / minor / changed.

Files:
- `lines.jsonl`, `rewrites.jsonl`
- `naturalness_packet_*.md`, `fidelity_packet_*.md`
- `verdicts_*.jsonl`

## Results

| | blunt | warm | dry | all |
|---|---|---|---|---|
| Rewrite judged more natural | 22 | 23 | 29 | **74 / 90** |
| Original judged more natural | 2 | 7 | 1 | 10 |
| Same | 6 | 0 | 0 | 6 |
| Fidelity: same / minor / changed | 10 / 14 / 6 | 11 / 12 / 7 | 16 / 8 / 6 | **37 / 34 / 19** |
| Fact gate failed | 1 | 2 | 2 | 5 |

- **Robotic flags:** originals 20 times, rewrites 2 times.
- **Latency:** median 1.2 s per rewrite, p90 2.6 s, max 4.9 s.
- **Cost:** under $0.01 for all 90.
- **Openers:** the warm voice opened 11 of 30 lines with "Okay".

**What changed in the 19 "changed" rewrites** (read and confirmed against the originals):
- **Wrong party, 3:** all three voices on one line. "your watch showing me at their door" became
  "your watch has you at their door". This is a new false statement with the same names, so the
  gate passed it.
- **Commitment raised, 7:** "I'd vote you" became "I'm voting you" (5); "I'd rather not lynch"
  became "I'm not lynching"; "not voting anyone today yet" became "No vote today".
- **Addressee of a question moved, 3:** "ask player_1 which night…" (to player_8) became
  "player_1, which night…".
- **Meaning shifted, 6:**
  - "acted on player_10 and nothing more" became "that's all I'm sharing" (now implies withholding);
  - a fact became a conditional;
  - an added hedge;
  - "gets accused" became "accuses";
  - a dropped "clean result" judgment;
  - "I'm the trailseer" dropped. This last one is the only change the gate caught.

The gate caught 1 of the 19.

## Reading

The rewrite reads clearly better: 74 of 90 preferred, and almost none read robotic. But about one
rewrite in five changes something a listener could act on. The deterministic gate sees names and
nights, not who did what or how firmly, so it misses nearly all of them. That is far above the
measured message hallucination rate (about 3%, `project-hallucination-screen-v2`), so a rewrite pass
as built would add more false statements than it removes robotic ones. Not adopted as built.

Options weighed:
1. Put the voice in the main call (one persona line per seat), where the model that reasons also
   speaks, so there is no second text to drift. Cheapest and safest; to be measured the same way on
   a replay.
2. A stricter rewriter (keep "I'd" vs "I'm", keep who did what to whom, keep each question's
   addressee), plus an equivalence check by a second call. That doubles the added latency, and the
   checker would itself err.
