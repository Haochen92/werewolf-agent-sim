# Gate read, sample part 1 (24 lookups, 68 lessons)

Per-lookup judgments: `part_1.jsonl` (same folder).

## Counts

- Lessons: fits 8, partly 19, does_not_fit 41 (of 68). Only 12% fit.
- Lookups with at least one fitting lesson: 8 of 24 (1, 3, 9, 11, 14, 17, 18, 24).
- Lookups where every lesson does_not_fit: 4, 13, 19, 22.
- Lookups with situation-text errors: 4 of 24 (5 errors): lookups 1, 10 (two), 16, 24.
- Leaks: no lesson names a player id or a game id. 9 lookups carry game-specific detail in lesson text (2, 4, 8, 9, 11, 13, 19, 20, 23), mostly mild; one is the lesson-writer's own meta text ("The prescription is to join the majority instead") inside the When of all three lessons in lookup 8. No situation states a concealed role as known fact.
- Seat verdicts: sound 17, mixed 4 (1, 9, 20, 24), no verdicts recorded 3 (5, 16, 18).

## What went wrong, by kind

1. Stage mismatch is the dominant failure (most of the 41). Retrieval matches the role and the "feel" (e.g. "chanteuse + wolf partner") but not the board: lessons for a dead partner, four alive, a final day, a revealed wolf or night 1 are served to day-2 or nine-alive seats. Lookups 4, 13, 19 and 22 are clean sweeps. Example: lookup 4, a day-2 chanteuse with her partner alive, got three lessons that all need the partner dead or three players left.
2. Speculator lessons assume a picked Town (lookups 3, 6, 21, 22). Lookup 22 and 6 are unpicked seats served "you have picked Town" lessons.
3. Healer lessons assume a lone killer (lookups 12, 14, 18). Lookup 14's top lesson (0.887) was the worst fit; its 0.829 lesson (protected claimant was attacked and saved, protect again) was the best.
4. Highest scores do not track fit. Lookup 1's one fitting lesson was the top score but the seat dismissed it.

## Kinds of situation-text errors

- Misstated rule: lookup 1, "I am not visible to anyone's night checks" (a Necromancer reads Suspicious on a night it attacks).
- Count contradicting what the seat knows: lookup 10, "the wolves (two living, unidentified)" while the same text says the Illusionist is dead; the Town count is also off by one.
- Claim about hidden information stated as fact: lookup 16, "the only unspent information tool among the living" (the Sentinel is not announced dead, so it cannot be said).
- Mischaracterised rule: lookup 24, "a forced abstain" on day 2 (abstaining is only removed after two no-elimination days).
- Garbled harness phrases (not counted as errors): "at worst for the town, because the concealed body's side is unknown" (several lookups), "(the swing flag is set)" (18), "wolf-channel-independent" (9).

## Three lookups the owner most needs to read

1. **Lookup 1** (haiku necromancer, day vote). The one lesson that exactly matches the live dispute (a claimed watcher's report against an accused player) was dismissed as "no one has claimed a trailseer or investigator result", although its When says "tracker or watcher". It also contains a rules error about Investigator checks. Shows a verdict failure on the best-case retrieval, and the seat voted a true Sentinel.
2. **Lookup 20** (luna illusionist, conceal decision). The lesson was followed with reasoning that runs against the seat's own situation text: it says the claimed Sentinel is unverified and the will would expose information, yet concluded "the role is already public so concealing adds little". A confident follow that rests on a bad analogy; this is where a lesson most plausibly changed play for the worse.
3. **Lookup 14** (luna healer, night 3) together with 12 and 18. The same three healer lessons are served to three different boards. In 14 the top-scored (0.887) lesson was the worst fit and the third (0.829) was the best, so score order inverts fit. It is the cleanest case that rerank score is not a fit signal, and it is the one where following a lesson was right (protect the saved Sentinel again).
