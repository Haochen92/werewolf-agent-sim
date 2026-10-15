# Part 4 read: 24 lookups (3001-3024)

## Counts
- Lessons judged: 68. fits 11, partly 24, does_not_fit 33. Under half the lessons shown were usable (fits + partly = 35 of 68, and only 11 clean fits).
- Lookups with at least one situation error: 11 of 24 (15 errors). 6 are rule or board misstatements (3002, 3006, 3007, 3015, 3018, 3020); 5 are only the arithmetic self-contradiction below (3008, 3009, 3010, 3013, 3024).
- Leaks: 1 (3011, lesson 1: "in one case ended the wolf faction outright, leaving only the lone killer"). No lesson named a player id. Several lessons quote aggregate past outcomes ("Results across the cluster varied...", 3013/3014); not counted as leaks.
- Seat verdicts: yes 18, mixed 6, no 0.

## Kinds of situation error (one example each)
- Hidden or announced facts misread: 3007 necromancer says its reanimated attacks are "concealed" and "publicly ... unknown"; the morning names an attack through a body ("killed by a reanimated wolf"), so the town knows a necromancer struck. 3020 says every body use is a public trace, and that a body block is named; only an attack is announced.
- Private information stated as verified public fact: 3015 "the only verified fact is the night-one block on the lynched healer"; a block is private and the healer's "I was blocked" is a claim.
- Board contradicts the seat's own reveal: 3006 "the remaining wolves and the lone killer are still unidentified among the three survivors" right after the necromancer was voted out and revealed.
- Scoring rule wrong: 3006 "a wrong bet costs a point"; a wrong Fortune Teller bet scores nothing.
- Incoherent vote description: 3002 "one player's vote to eliminate the concealed victim's seat" (a dead player cannot be voted on).
- Template arithmetic: the stakes line gives "six eliminations to parity" and also "the game can end within one more elimination" (3008, 3009, 3010, 3013, 3024). It is machine-generated, but it contradicts itself.
- Seat contradicts itself inside one lookup: 3018 says the pack has chosen a victim and also that the target's role is "not yet known"; the verdict names player_7.

## Patterns
- Retrieval mismatch is the dominant failure. Lessons are late-game or reaction lessons (exposed partner, named by a Sentinel, final three) retrieved for opening or early turns (3003, 3004, 3005, 3014, 3021). 3004 and 3021 get the identical three SK lessons.
- Sentinel lessons for "one watch left" or "Night 1" fetched for a night-2 first watch (3014): all three do_not_fit.
- Seats reject mismatched lessons correctly almost every time. The mixed verdicts are the real misjudgements (below).

## Three lookups the owner most needs to read
1. 3018 (haiku illusionist, conceal decision). The one clean-fit lesson (#3: spend a conceal on a victim whose role and will are still unknown) was overridden on "no watcher remains", which ignores the lesson's point. The victim (player_7, the investigator) then had a will read out that the town used. The situation text also contradicts itself on whether the target is known.
2. 3020 (haiku necromancer, day 4). The seat rejects lesson #1 with "No necromancer is publicly confirmed yet", although its own night-3 attack through the vigilante body was announced as a reanimated kill (3001, same game, shows that record public). The situation says every body use is a public trace and that a block is named, both wrong. This is a rule-misread that changes play.
3. 3007 (luna necromancer, accused of being Suspicious). Strong fits (#2, #3) and a sound defence, but the situation text claims the reanimated attacks are concealed; 3010 (same game, one day earlier) correctly says the necromancer is publicly known to be active. Same-game contradiction on a rule that decides the necromancer's endgame.

## Possible provenance check (not verified)
In game 940365c1 (3003, 3007, 3008, 3010, 3013, 3016) several lessons describe boards close to that game's own later states: 3010 lessons 1-3 (four alive, spent investigator, active trailseer, unclaimed sigilist, fresh vigilante body) and 3003 lessons 1 and 3 (partner exposed by a confirmed vigilante, a blocked tracker claimant). The lookup data carries no lesson source ids, so I could not confirm; if the lesson store was mined from games including the one being played, these are future-information leaks and score 0.893 for 3010 lesson 1 would be inflated.
