# Persona voices: before/after games (2026-10-18)

**Question (owner):** with every AI seat speaking in its puppet's voice (`RunConfig.persona_voices`,
`Agents/prompts/voices.py`), do the AI seats still read each other and reason as well?

**Method.**
- Runner: `evaluation/experiments/persona_voice_games.py`; scorer: `persona_voice_games_score.py`
  (output `scores.json`).
- Games: 8 pairs of AI-only games, Haiku 5.5 at thinking low, memory off, deductions "full". Voices
  off in one arm and on in the other. A pair shares its game id, the deal's seed, so both arms deal
  the same roles and seats; after the first differing line the games diverge.
- Reads: scored as the read ledger does. A committed read is checked against the true role, Brier at
  the confidence's coarse probability, "unclear" counted apart; a pack seat's read on its packmate
  is masked.
- Cost: $2.48 for all 16 games ($0.08–0.26 a game).

## Results

| | Voices off | Voices on |
|---|---|---|
| Spoken lines (8 games) | 206 | 246 |
| Median words per line | 53 | 53.5 |
| Committed reads | 1,105 | 973 |
| Reads left "unclear" | 86.8% | 87.3% |
| Committed reads: role correct | 87.5% | 95.5% |
| Committed reads: side correct | 88.1% | 95.7% |
| Brier (lower is better) | 0.155 | 0.129 |
| Town votes on a non-town player / on town / abstain | 50 / 41 / 37 | 49 / 28 / 35 |
| Town wins | 4 of 8 | 7 of 8 |

- **Brier by pair:** voices on was better in 7 of 8 pairs (voices-06 the exception); a two-sided
  sign test gives p ≈ 0.07.
- **Town votes:** of the non-abstaining town votes, 64% went to a non-town player with voices on,
  55% with them off.
- **Voices** (on arm):
  - Median words by voice run from 47 (Kitsune) to 61.5 (Owl), on 5–29 lines each; no voice runs long.
  - The Badger opened most of its lines with "Right then", the phrase its voice quoted. The quote is
    removed.
  - The Whale used a sea phrase once in 11 lines ("Captain's log, day 3.").
  - One Cyclops line ("it feels so sincere to me") let the sentimental voice colour a judgment.
- **Leak check:** 5 games (both arms) failed. Every flag was a sentence the receiving seat also has
  in its own record: two killers on one victim share "player_5 survived: the healer saved them.",
  and two roleblocked seats share the generic roleblock line. In the Necromancer's case, its record
  "Through player_9's body: player_8 was roleblocked tonight." contains the dead Chanteuse's
  sentence. No real leak. The check now ignores words that are in a record the seat may see
  (`tests/leak_test.py` `check_night_record_isolation`), and all 16 games pass it; the manifests keep
  the original result.
- **Silence:** the games are quiet. voices-01's off arm spoke no line in four days, and about 87% of
  reads stay "unclear" in both arms. A replay showed the deduction blocks are not the cause: seats
  passed 15 of 15 times with them and 15 of 16 without. The opening silence rule and the role cards'
  caution are, as in the pre-engine live game 645228e7.

## Reading

There is no sign that voices hurt the AI readers, and every measure leans toward voices on. The
leaning is not established:
- 8 pairs only.
- The arms diverge after the deal.
- The voiced arm talked about 19% more, which by itself gives the readers more to read.
- Wins at n = 8 are noise.

What this licenses: the voices are safe to ship behind the toggle, and the AIs take in voiced text at
least as well as plain. Not checked here: the hallucination census on the voiced lines.
