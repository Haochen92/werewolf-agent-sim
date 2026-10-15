# Gate read, sample part 2 (lookups 1001-1024)

## Counts

- Lessons judged: 69 across 24 lookups.
  - fits: 8 (12%)
  - partly: 19 (28%)
  - does_not_fit: 42 (61%)
- Lookups with at least one concrete situation error: 13 of 24 (16 errors in all): 1001, 1002, 1007, 1009, 1010, 1012, 1013, 1014, 1016, 1017, 1018, 1019, 1023.
- Lookups with a leak: 2 of 24 (1010, 1016), both mild: a lesson whose When reads as one past board. No lesson names a player id. No situation states a hidden role as known fact.
- Seat verdicts: yes 15, mixed 7, no 0, n/a 2 (1014 and 1016 recorded no verdicts).
  - Mixed: 1003, 1007, 1008, 1011, 1017, 1020, 1024.

Most of the 42 does_not_fit lessons were dismissed correctly by the seat. The retrieval problem is the mismatch itself: endgame lessons served at 7-9 alive.

- Lookups 1018 and 1022 got four-player and three-player wolf endgame lessons on day 2-3.
- Lookup 1016 got three endgame lessons on night 2.
- Lookup 1005 got three late-stage Speculator lessons at an opening turn.

## Kinds of situation errors

- **Misread rule about what a trace shows (Necromancer, sigil, follow/watch).** 1002: "the one private check ... showing player_7 visited no one ... clears only one candidate". A Necromancer's body attack shows under the body's name, so a null follow clears nobody. Also 1013: the Trailseer calls its own follow "the watched player".
- **No-effect sigil read as exoneration.** 1014: "a sigil with no effect narrows the target to a non-attacker". The rules say no effect looks the same for a non-attacker and for an attacker that night immunity protected, and the Serial Killer is in that game.
- **Body abilities confused.** 1012: "a kill through the dead Vigilante or Investigator body"; an Investigator body only learns a check. Same lookup: the Investigator body "reads Suspicious on attack nights".
- **Phase or vote-count miscounts.** 1018: "two abstain votes"; day 1 has no vote, so there has been one. 1001 has the same loose "two abstain days". 1023: the seat says it is "with the abstaining majority" on day 3, when abstaining is no longer offered after two no-elimination days.
- **Stale or wrong public facts.** 1018: the Fortune Teller "remain[s] unrevealed", but it died night 1 and was revealed. 1019: "player_8's own vote target was a single eliminate vote", contradicting the same text's "against you".
- **Garbled night-action mechanics.** 1010: a block "announced as an ability held back"; blocks are never announced. 1016: "a failed self-bet on a real attack leaves its death unscored"; a self-bet makes the attack fail. 1009: "attacked by both wolves"; only the carrier attacks.
- **Open-versus-fixed carrier.** 1007: "the pack's kill still unassigned"; under seat-order rotation the illusionist carries night 2.
- **Unsupported inference.** 1017: "the Speculator has picked Town publicly, so the wolf-side has no living wolves".

## Three lookups the owner most needs to read

1. **1007 (haiku illusionist, night 2).** The best-scoring lesson in the batch (0.881, "spend a conceal on tonight's victim?") is exactly the seat's question. The seat marked it not_relevant, then called lesson 2 "override" in one round and "follow" in the next two on the same board. It also treats who carries the kill as open when the rotation fixes it. This shows both retrieval working and the seat discarding it. The decisions shown are wolf-chat turns, not the conceal choice.
2. **1017 (haiku necromancer, night 5).** The seat marked lessons 1 and 3 "follow", but they point opposite ways: kill the active information role versus avoid claimed power roles. It shot the claimed Trailseer, which is what lesson 3 says to avoid, and lesson 3's stated reason contradicts itself. Lesson 1's rationale is also mechanically wrong for a Necromancer: a Trailseer following it sees no body-attack. A fresh read is needed on whether the verdicts or the lessons are the problem.
3. **1018 (haiku chanteuse, day 3), with 1022 as its twin.** All three lessons were three-player or partner-dead wolf endgames served at seven alive (1022: eight alive, day 2, four lessons). The situation text has two factual errors (the Fortune Teller "unrevealed", "two abstain votes"). This is the clearest case of retrieval matching the role and the "partner" vocabulary rather than the stage.

Runners-up: 1014 (the no-effect sigil error, with a correct statement of it in the lessons themselves) and 1016 (five lessons, three of them three-player endgames at nine alive).
