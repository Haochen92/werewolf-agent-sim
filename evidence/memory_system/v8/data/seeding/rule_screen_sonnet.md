# Rule errors in the Sonnet 5.5 strategy points (2026-10-12)

The same screen as `rule_screen.md`, on the 164 points of the Sonnet 5.5 re-synthesis
(`strategy_points_sonnet.json`, store `memory_stores/v8_seed_synth_sonnet`). Opus subagent; Claude
checked the bullet, Necromancer-immunity, sigil-result and will rules against the rules text and
role sheet. One read, not a measurement.

**32 of 164 flagged (20%): 15 high confidence, 17 medium**, against 14 of 150 (9%) for flash-lite.

| Recurring error | Points |
|---|---|
| The pack chooses its carrier (it rotates by seat order) | 5 |
| A sigil's "no effect" misread (a Healer save has its own result; immunity and body attacks also read "no effect") | 5 |
| The Necromancer immune every night (night 1 only) | 2 |
| Results reaching a player who died or was blocked that night | 2 |
| Which watch or follow shows whom | 3 |
| Others: a blocked shot "wastes the bullet" (it keeps it); written wills (the GM reads the record); day 1 after a night visit; a neutral that kills; a miss names the shooter | 15 |

The carrier rows: synthesis ran after the rules text was fixed (`af67dae3`), so these come from the
observations, which describe games played under the old text.

**Style.** Points average about 2,100 characters (actions 645) against about 1,050 (230). They are
more specific and branching, and get several fine rules right (rotation in seat order, a carrying
Illusionist's conceal leaving no trace, "no effect" clearing no one); stating more mechanics, they
state more wrong ones.

Full table: the subagent's report, kept in the session transcript; the flagged keys are listed here
for the review.

High: ef5b0e2d 8244f01c 4493257d 0452048c d524aaa6 e7558082 9ad7fc37 6ea700e0 1e94cb38 452a8d57
8fc4a70f f13dfd95 b0b3ab88 f7fe4afd 2e1adddf. Medium: c63b9b6e fc8fad06 58c65bde a656856a e263322c
7b24d264 0dea4221 6fef08c2 4acca434 7039f93d 300fce68 3c20150c 70349868 968cfc71 3de31d9a 2ee88b3a
875154ee.
