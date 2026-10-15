# Gate read, sample part 3 (lookups 2001-2024)

Per-lookup judgments: `part_3.jsonl` (same folder).

## Counts

- Lessons judged: 63 across 24 lookups. **fits 12 / partly 17 / does_not_fit 34.** Only about a fifth of fetched lessons are usable as written; over half do not fit the decision.
- Lookups whose situation text has a concrete error: **9 of 24** (2001, 2008, 2009, 2012, 2013, 2014, 2016, 2017, 2024), 11 errors in all.
- Leaks: **0 lessons name a player id.** 5 lookups (2007, 2009, 2017, 2018, 2020) have lessons that quote aggregate past-game outcomes ("in this cluster", "in one case ended the wolf faction outright", "Past observations show the Town pick won when ..."). No situation states something the seat cannot know.
- Seat verdicts: **yes 15, mixed 8, no 0**, 1 not gradable (2005 recorded none).

## Kinds of situation error (one example each)

- **"Game can end within one more elimination" is wrong.** A stakes line says it at seven or five alive with a wolf and a serial killer both alive (2014, 2016, 2017). Example, 2017: "the board can end within one more elimination at worst for the town" with seven alive. It looks like a stock phrase that the engine's own count contradicts ("five eliminations from parity" in the same sentence).
- **Self-reference or miscount of the board.** 2008: "player_6 and player_9 are both pressing me" (the seat is player_6). 2024: "the one wolf-side player among these five" (two wolves are alive, one is the seat's partner). 2013: the night-2 save is given to the claimed Sentinel and again to a separate candidate.
- **Public/private mixed up.** 2012: "my only public exposure is the night bets" (a Fortune Teller's bets are private). 2009: "Publicly firing a shot would reveal the vigilante role" (the report names the kind of attacker, not who fired).
- **Loose or wrong rules wording.** 2001: "no will was read out for a wolf victim-equivalent" (the victim was a revealed Town trailseer, so a record is read). 2016: the dead Trailseer's Day 2 vote and a live "player who favored eliminating the agent" are treated as the same person.
- Not counted as errors but worth knowing: parity counts that ignore the lone killer or necromancer still alive (the wolves cannot win while it lives) appear in 2001, 2003, 2012.

## Retrieval pattern

Wolf-under-fire lessons ("partner exposed", "tracker outed my visit", "tracking report plus a dead partner") are fetched for wolves who are NOT under fire: lessons 1-2 of 2022 and 2024 are identical and miss both times; 2001 and 2010 get the same two exposure lessons. Early-stage lessons (night 1, day 2) are fetched at night 2-4 and are usually dismissed correctly. The best matches (2008, 2013, 2014, 2015, 2018, 2020, 2023) come from role plus a specific trigger (a named kind of report, a last conceal, a saved leader).

## Seat verdict problems (the 8 mixed)

- Fitting lesson dismissed on a wrong or contradicted premise: 2001 (lesson 1: "the claimed trailseer is dead", but its Do covers "other claimant"), 2010 (lesson 3, "no broad consensus to abstain", against its own "broadly cautious" situation), 2013 ("my last conceal is not available" when it conceals in the next decision), 2009 (dismissed as not information-starved while its own text says "Information-starved").
- Miscount in a verdict: 2017 ("only six alive", seven were). Stage misread: 2012 ("Still early" on day 4 at five alive). 2004 and 2007: conclusion right, reasoning thin or garbled.
- Dismissing non-fitting lessons as not_relevant is almost always right (the 15 yes).

## The three the owner most needs to read

1. **2013 (luna, illusionist, night 4).** The best retrieval in the sample: lessons 1 and 2 are exact fits (lone illusionist, last conceal). The seat followed lesson 2 and then dismissed lesson 1 with a false premise about its own resource, contradicting its own next decision. It shows the verdict layer can discard the right lesson, and the situation text also holds an internal contradiction about the night-2 save.
2. **2010 (luna, chanteuse, day 2 vote).** A fitting lesson (do not force a lone elimination vote on an unpressured player in an info-poor day) was rejected on a premise the seat's own situation text contradicts, and the seat cast exactly that vote on player_4. It also shows the pair of exposure lessons that miss here and in 2001.
3. **2024 (haiku, illusionist, day 3 discussion; read with 2022).** Three wolf-under-fire lessons, none fitting, fetched across four decisions; two are the very same lessons that missed in 2022. It also carries the "one wolf-side player among these five" miscount. Together they show the retrieval misfire and the stock stakes-line errors that the situation writer produces.

Runner-up: 2017 (an irreversible Speculator pick with a seven-alive miscount, a false "game can end" line, and an override of the lesson's hold condition).
