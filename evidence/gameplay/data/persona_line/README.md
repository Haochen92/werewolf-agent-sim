# Persona line screen (2026-10-18)

**Question:** does one persona line in the seat's own discussion prompt make the messages read more
like people, without moving what the seat says? This follows the voice rewrite screen
(`../voice_rewrite/`): a second rewrite call read better but changed something a listener could act
on in 19 of 90 rewrites.

**Method.** Runner: `evaluation/experiments/persona_line_screen.py`.
- **Turns:** 15 day-discussion turns of the frozen Haiku turn bench
  (`evidence/gameplay/deduction/data/haiku_effort_replay/turn_cases.jsonl`, seeded draw), rebuilt
  by the replay bench in "full" deduction mode.
- **Arms:** sampled on Haiku 5.5 (thinking low) with no persona (twice) and with each of three voices
  (blunt, warm, dry; once each). The voices are the rewrite screen's.
- **The persona paragraph** follows the tone block, in the seat's part of the prompt: "Your voice at
  the table: {voice} This is how you sound, not what you think: it never changes your facts, your
  claims, how sure you are or what you ask for."
- **Judging:** four blind Sonnet chat subagents.
  - Naturalness: each voiced message against the turn's first plain one, X/Y in a seeded order.
  - Stance: the same pairs plus plain against plain (the sampling-noise baseline), A/B. The judges
    asked whether a listener would take the same position and request from both.

**Cost:** 75 calls, $0.09; one invalid sample. Pass rate: plain 9 of 30, voiced 11 of 44.
Median length: 50–59 words in every arm.

## Results

| | blunt | warm | dry | all |
|---|---|---|---|---|
| Voiced judged more natural | 7 | 9 | 9 | **25 / 30** |
| Plain judged more natural | 3 | 1 | 1 | 5 |

| | Voiced | Plain |
|---|---|---|
| Flagged robotic | 5 | 20 |
| Flagged as having a recognisable voice | 13 | 1 |

| Stance | same | minor | different |
|---|---|---|---|
| Voiced vs plain (30 pairs) | 1 | 20 | 9 (30%) |
| Plain vs plain, baseline (10 pairs) | 0 | 7 | 3 (30%) |

The "different" pairs read as ordinary sampling choices: which player to press, whether to claim,
whether to propose a vote. They lean no way by voice, and a blunt seat is not more aggressive.

## Reading

- **Naturalness:** the persona line wins as clearly as the rewrite did (25 of 30 against 74 of 90),
  without a second call.
- **Stance:** the voiced replies differ from a plain one exactly as often as two plain replies
  differ from each other. On this sample, the voice moves how a seat sounds, not what it argues.
- **Limits:**
  - The baseline is 10 pairs, so a modest content effect could hide in the noise.
  - The turns are from one bench and one model.
  - The voices are subtle: the judges heard a recognisable voice in 13 of 30 voiced replies.
  - A real game would show whether a seat keeps its voice across a day, and whether three or more
    voiced seats sound like a cast or like one tic each.
