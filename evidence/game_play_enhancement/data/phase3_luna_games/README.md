# Phase 3: four games on GPT-6 Luna (2026-10-10)

GPT-6 Luna (`openai/gpt-6-luna`, medium reasoning, JSON-schema output; admitted to the model catalog on
2026-10-04) in every seat and as the summariser, memory off, two games at a time, on the working tree of
2026-10-10 (fb193104 plus that day's uncommitted prompt changes: the illusionist sentence, the cover-note
rewrite, claim retention, the rules-are-exact line; the illusionist card's one-sentence rewording came
after these games). Six were started; the owner stopped the last two (`logs/stopped/`). One difference
from a served game: the capture falls back to a flash-lite rescue model on a failed turn, where a served
Luna game has no rescue; no turn failed. Cost from the run's usage meter at Luna's listed $0.10 in,
$0.01 cached, $0.50 out per million tokens.

| Game | Drawn seats | Winner | Neutral | Days | Calls | Cost | Time |
|---|---|---|---|---|---|---|---|
| l01 | serial killer, speculator | wolves | lost | 4 | 142 | $0.12 | 17 min |
| l02 | necromancer, fortune teller | town | won (4 points) | 7 | 192 | $0.19 | 24 min |
| l03 | serial killer, fortune teller | town | won (2 points) | 4 | 149 | $0.13 | 18 min |
| l04 | necromancer, speculator | town | won | 6 | 214 | $0.22 | 29 min |

| Per game, mean | Luna, 4 games | flash, 6 | flash-lite batch 4, 6 |
|---|---|---|---|
| Winners | town 3, wolves 1 | town 5, necromancer 1 | town 5, necromancer 1 |
| Cost | $0.17 | $2.72 | $0.72 |
| Time | 22 min | 12 min | 8 min |
| Days | 5.2 | 4.5 | 4.0 |
| Lines heard | 42 | 40 | 29 |
| Words per line | 41 | 52 | 32 |

## The turn replay

The fourteen frozen turns on the current prompts (`../phase3_turn_replay/`, `bench_summary_luna.json`): bad
spoken messages among 55 positive samples, flash-lite 17, Luna 7 (gemini-3.5-flash 6, on slightly earlier
prompts), and among 15 controls 4, 3 and 0. Luna takes no sighting as proof and almost never reads an
empty watch as an empty house. Its errors sat in the four f02 rule turns, where it read the illusionist's
card literally ("the concealment hides the carrier's trace, not the Illusionist's own visit"; the real
trailseer doubted its own true result); after the card stated the carrier exception in one sentence its
errors there went from 8 of 20 to 0 of 20 (`bench_summary_f02_wording.json`), while flash-lite's cascade
turns stayed at 10 of 10.

## The audit

Two Opus readers, the rubric of `../phase3_reads/README.md` with its review corrections (downstream use
observed, not counterfactual outcomes; defeasible reads kept apart; deductions on corrupted context
marked). Per game: l01 A0 B4 C4 D-self 2 E0 (~28 lines); l02 A1 (a private note) B9 C3 D-self 1 E0 (~56);
l03 A2 B2 C3 D-self 0 E0 (~28); l04 A0 B4 C4 D-self 1 E0 (~54). About 166 heard lines: A 3, B 19, C 14,
D-self 4, E 0.

**One unstated rule decided four games' worth of reasoning.** The engine leaves a sentinel out of its own
visitor list, and the sheet says so; the sentinel's card says only "Watching is a visit". In all four games
a player argued that a watch is a visit, so the sentinel should appear in its own list; the real sentinel
conceded ("since watching is a visit, I should have appeared too", l01; "by the rules I should have appeared
in the visitor list", l04), evil seats amplified it believing it, and the true sentinel was voted out in
l01 (8–1), l02 (4–2) and l04 (unanimous among the others). Eleven of the fourteen invalid deductions belong
to this one chain. Neither flash-lite nor flash fell into it in the games read: a model that reads rules
literally exposes the gaps a looser reader glossed over.

**The summary.** Of the 19 summary errors, about half are results the claim record cannot hold: a watch
that saw no one, a sigil with no effect. And one is a regression from the claim-retention change of the
same day: the summariser filed "I was roleblocked" as a denial ("says they did not act", l03 day 2, l04
day 3), and in both games a later player called the real trailseer's claim inconsistent because of it.

**Discussion.** Real claim contests (an investigator counter-claim resolved by a visit test both claimants
committed to, l02; a fortune teller contest won by the player with a complete, checkable bet history, l02;
two fake covers broken by the real holders within a day, l03). Luna hedges heavily ("not proof", "doesn't
verify"), which reads repetitive and presses few cases (l04), and some days are thin (l01). Votes on
undiscussed players still occur on scattered days (l01 day 3, l04 days 3 to 5).
