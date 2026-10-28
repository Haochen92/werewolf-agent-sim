# Attribution check: owner hand-check (20 cases)

For each case: does the decision do what the lesson says? Write match / partial / mismatch / uncheckable
after **Your label**, and a note if you disagree with the reader. Not judging whether the move was good.

> **Note (2026-10-28):** "Lesson (when)" below is not the lesson's own situation. It is the live game's
> situation the lookup searched with (`matched_situation`), which is why it names this game's players. The
> stored lessons are written without player IDs, and players see the stored text. The sampler
> (`evaluation/experiments/attribution_check_sample.py`) now records both fields. The labels judge the
> advice against the decision, so they stand.

## c004: illusionist, day 2, day discussion

**Lesson (when):** Day 2 opens with nine players alive after the night 1 wolf kill on player_5, whose role was concealed by you. The village cannot see that the concealed role was an Investigator, and the wolf partner is still hidden, so the town has no hard information to act on. Information landscape: Information-starved: only the death, its concealment, and no claims or checks. Night results remain private to each role. Stakes: Nine alive with five eliminations needed for the wolves to reach parity, counted at worst for the town because the concealed role's side is unknown; a single wrong daytime vote is reco…

**Lesson (advice):** When you are an unsuspected illusionist wolf in an info-starved day with several unverified town claims, keep your contribution to at most one neutral clarifying question about a claim, or stay silent. Add no accusations or defenses of your partner, so your name stays off the record while the room argues among itself. If your partner comes under fire, let the vote follow the majority rather than defending her openly.

**Player's stated reason:** Unsuspected wolf in an info-starved day; keep contribution minimal and non-committal.

**Decision:** Sorry about player_5. Since the body was hidden, I'd like the claimants to say plainly who they watched or followed last night, and whether they saw any visit to player_5. Simple question, nothing more from me yet.

<details><summary>Last lines it saw</summary>

- player_10:
- player_1: Quick rules point: the Sentinel's watch never shows the watcher, so if anyone claims a watch result, ask them who they watched and what the visitor list said. Night 1 had a hidden body, so any claimed kill detail is harder to check. Let's hear the claims in order before anyone votes.
- player_2:
- player_3:
- player_4: Procedural point on the hidden body: a Sentinel or Trailseer only sees the carrier's visit if the victim wasn't concealed, so a 'no visitors' or 'no trace' report from night 1 proves little. Before anyone votes, ask each claimant what their result was and whether player_5's body had a hidden role when they read it.
- player_6:
- player_7:
- player_8:

</details>

**Reader's label:** match: Lesson allows at most one neutral clarifying question; the player asks claimants who they watched/followed and nothing else.

**Your label:** match: Owner agreed with Claude's labels, 2026-10-28.

---

## c007: illusionist, day 3, day discussion

**Lesson (when):** A claimed sentinel named player_7 as having been visited by the dead investigator on the last night, and player_7 has refused to answer whether they visited anyone, with players asking for other claims to be tested. Information landscape: Information-starved: one unverified sentinel claim, one unverified denial by refusal, no confirmed role reveals beyond a concealed body and a revealed investigator's single check on player_2. Stakes: Eight alive with four eliminations needed before the leading evil faction can win at worst for the town; a wrong vote is recoverable but each mistake narrows the…

**Lesson (advice):** When a Sentinel or Trailseer places you at a concealed body, say that the pack's carrier visit to a concealed victim leaves no trace, so a visible visitor is less likely to be the killer. Stay with that rules point, don't claim any night action of your own, and don't deny the visit outright.

**Player's stated reason:** A sentinel places me at the victim's door; I should explain via the rules point without claiming a night action or denying outright.

**Decision:** player_3, I'm not claiming anything, so I won't say what I did that night. Rules point though: if a victim was concealed, the carrier's visit to them leaves no trace, so a visible visitor isn't necessarily the killer. Can the trailseer and healer post their results so we can cross-check?

<details><summary>Last lines it saw</summary>

- player_10:
- player_2: Player_3, if you watched player_7 on night 2 and player_6 came to them, that's a concrete lead. Player_7, did anyone visit you that night, or did you visit anyone? Let's hear it before we vote on anything.
- player_7: I'm not claiming a role, so I won't speak to my own night. Player_3, you say player_6 came to me. Do the other claimants have results that line up with that, or do they conflict? That would tell us more than my word.
- player_3: Yes, I'm the sentinel. On night 2 I watched player_7, and player_6 came to them. That's my only result, and I'll keep my last watch for when it's needed. player_7, player_6 came to you that night, so why not tell us what you did and who you think is a wolf?
- player_7: player_3, I'm not going to confirm or deny a visit from my side. Before anyone's word decides this, can the other claimants post their results? If the sentinel and trailseer reports don't match, that tells us more than one claim does.
- player_4:
- player_5: Player_3, you say player_6 came to player_7, but player_6 died that night, so that visit would have been made before the kill. I'd like the sentinel result tested: if player_7 is a wolf, a second claimant on night 2 would show a conflict. I'm not voting yet; I want the trailseer or healer to speak first.
- player_3: player_5, fair question. I'm the sentinel, and my only result is that player_6 came to player_7 on night 2. I'm not going to name it as a verdict, since a visit only tells us where someone went. player_7, you've been asked twice now: did you visit anyone that night, yes or no?

</details>

**Reader's label:** match: Lesson says give the rules point that a concealed victim leaves no carrier trace, without claiming an action or denying; the player does exactly that.

**Your label:** match: Owner agreed with Claude's labels, 2026-10-28.

---

## c010: necromancer, day 5, day vote

**Lesson (when):** Day 5 with three players alive. Two claimed roles (sentinel, sigilist) are backing each other on a night-2 visit, and they have jointly called for a vote on the one unclaimed player, who has refused to give a role and asked them to test their claims first. The game master has already given the last word, so the vote is imminent. Information landscape: Information-starved: the public record is the night reports, the vote history, and two claims that cross-confirm one another; no elimination has yet confirmed or refuted either claimed role. Stakes: Three alive with one elimination left before th…

**Lesson (advice):** With three alive and both others claiming town roles, vote for the one whose claim has the thinner support in the announced record, and use your last word to give the other player a reason to side with you. Before the vote, check whether the two corroborate each other through announced night events. If they do, the record is against you and the vote only works if you can credibly cast doubt on one of them.

**Player's stated reason:** Three alive with both others claiming town roles, so I target the one with thinner support and use my last word to pull the other.

**Decision:** vote: player_6

<details><summary>Last lines it saw</summary>

- player_7:
- player_9:
- player_6: My night-2 watch on player_1 did show player_7 visiting, so player_7's sigil claim holds up as far as I can tell. Night 3 and 4 attacks came through the reanimated vigilante, so the necromancer is alive and is one of the two of you. player_9 has claimed nothing, so I'll vote player_9 today unless someone gives a reason not to.
- player_9: player_6, you say the necromancer is one of us two, but that is a coin flip, not a read. Your night-2 watch is only your word, and it lists player_7 and player_2, who are both claimed, so it proves nothing about me. I'm town-leaning and I've said nothing that conflicts with the morning reports. Which of your claims can you back with a public fact?
- player_7: player_6, you're right that the necromancer is one of us two, and my night-2 visit to player_1 is real, so your watch listing me is a point in your favour. player_9 has said nothing checkable at all. I'd vote player_9 today unless player_9 gives a claim we can test.
- player_9: player_7, I'm not going to give a role just because you asked. Your night-2 sigil on player_1 fits player_6's watch and player_1's roleblock, and that is all the public record shows. Do you still hold your second sigil, and what would you test with it tonight?
- game_master: Before the vote: player_9 has been accused by player_6 and player_7. player_9 gets a last word.
- player_9: I have answered what I was asked, and the only public facts are the morning reports and the vote record. player_6's watch and player_7's sigil back each other, but neither accuser has shown anything beyond their own word. Vote on what can be checked, not on who pushed hardest.

</details>

**Reader's label:** uncheckable: Lesson says vote the one with thinner support; both others back each other and the record does not show which claim is thinner, so voting player_6 cannot be judged.

**Your label:** match: Disagrees with reader. player_7's claim has two supports (player_6's watch, player_1's roleblock); player_6's has only player_7's word, so player_6 is the thinner claim and the vote follows the lesson. Low confidence. Owner agreed with Claude's labels, 2026-10-28.

---

## c011: chanteuse, day 3, day discussion

**Lesson (when):** Day 3, after the second night, in which the wolves killed a claimed-investigator-revealed player and their role was revealed; the Trailseer and the Sentinel have given contradictory accounts of player_8's night-2 visits, and player_8 is asking which door is disputed while the town has not voted since the abstain on day 2. Information landscape: Information-starved beyond two contradictory role claims; one public death with a revealed role and a known Investigator check on player_5 (Not suspicious); no eliminations yet. Stakes: Eight alive with four eliminations needed for the leading evil side…

**Lesson (advice):** When you are a low-heat chanteuse in an info-starved early day and the room is sorting through unverified claims, make one short rules-based or procedural point, such as asking a named visitor to explain or noting what a claimed result would imply under the rules. Keep it neutral, tied to public claims, and never reveal your own block or its target. This steers the room toward verification and leaves you with no vote record or read to defend.

**Player's stated reason:** Early day with claims in conflict; a neutral procedural point keeps my heat low.

**Decision:** Short question for the table: player_5 says player_10 came to player_8 on night 2, but player_10 was the victim that night. Did the watch show a visit to player_8 from player_10 before the kill, or could that line be the other way around? Worth pinning down before anyone votes on it.

<details><summary>Last lines it saw</summary>

- player_7:
- player_8:
- player_9:
- player_8: player_1, you're saying I went to player_10 on night 2. I'm not claiming a role, so I won't dig into that. But player_5 says player_10 visited me, and player_10 was already dead by morning. player_5, what exactly did your watch show, and when?
- player_5: player_8, my night 2 watch on you showed that player_1 and player_10 came to you. Visits happen during the night, and the wolves' kill resolves that same night, so player_10 visiting you and then dying is not a contradiction. player_1, your follow says you went to player_10, which is a different direction from mine, so one of us has the door wrong.
- player_2: Quick check on the day 3 conflict: player_1 says I visited no one on night 1, which is true. But player_8's night 2 door is still disputed. player_1 says player_8 went to player_10, and player_5 says player_10 came to player_8. Both can't be right, so player_8 and the two of you should say who exactly was checked, and when.
- player_4: player_1 and player_5 might both be right. A follow on player_8 is itself a visit to player_8, so player_5's watch showing player_1 coming to player_8 fits. The real conflict is only whether player_10 came to player_8 or player_8 went to player_10. player_8, which door is yours?
- player_8: player_4, fair question. My read is that a follow on player_8 is a visit to player_8, so player_1's door and player_5's watch can both be true. I'd like player_1 to say whether they followed player_8 or someone else on night 2, since that settles which door is actually disputed.

</details>

**Reader's label:** match: Lesson asks one short neutral procedural point; the player asks one question about visit direction without revealing a block.

**Your label:** match: Owner agreed with Claude's labels, 2026-10-28.

---

## c012: serial_killer, day 3, day discussion

**Lesson (when):** After a day in which the illusionist was lynched, a claimed trailseer named a visitor at their door and the claimed sentinel and healer have each partly backed the trailseer, while the investigator's read is hidden. You, the lone killer, are the visitor the trailseer named and must decide how much to engage before the next vote. Information landscape: Information-rich in claims (trailseer, sentinel, healer, investigator all speaking) but information-starved in verifiable fact: only the illusionist's lynch and two save announcements are confirmed. Stakes: Nine alive with seven eliminations need…

**Lesson (advice):** When early deaths leave the room hunting for leads and no heat is on you, speak as an ordinary town member and echo the room's demand that evasive or vague players state their role and night action. If a vocal player pushes for claims without offering information, ask them to say whether they hold any, so the room's scrutiny lands on claimants and evasive players instead of on you.

**Player's stated reason:** Still early; I keep a low-heat town stance and ask for the claims to be tested rather than attacking anyone.

**Decision:** Yes, I went to player_2's door last night. I'm not claiming a role, I just wanted to see if they were really the trailseer. I saw nothing that told me anything. Player_5 says they protected player_2, so visits from 4, 5 and 8 could all be simple checks.

<details><summary>Last lines it saw</summary>

- player_3: I'm the sentinel, and I'm claiming it now. Last night I watched player_2 and saw visits from player_4, player_5 and player_8. Night 1 I watched player_1 and saw player_2 come to them, which fits player_2's follow claim.
- player_4:
- player_5: I'm the healer. I protected player_3 on night 1 and player_2 on night 2, which is why both were saved. Player_2's trailseer claim fits that, so I'd like the town to take it seriously.
- player_6: I'm the investigator. On night 2 I checked player_9 and got Not suspicious, so player_9 isn't a wolf. I'm keeping my last check for a live question.
- player_7:
- player_8:
- player_9:
- player_10:

</details>

**Reader's label:** mismatch: Lesson says echo the room's demand that evasive players state role and night action; the player instead volunteers that it visited player_2's door and explains why, demanding nothing of anyone.

**Your label:** mismatch: Owner agreed with Claude's labels, 2026-10-28.

---

## c014: speculator, day 2, day vote

**Lesson (when):** Day 2 opens with eight alive. A wolf (the Chanteuse) died to the serial killer on night 1, and the wolves' kill on player_7 was concealed, so the wolves' remaining strength and the serial killer's presence are both unresolved. I have one unspent Speculator pick and must decide, from public evidence alone, which side to bet on before the game is decided, without drawing attention. Information landscape: Information-starved: only two morning reports, no claims, no checks, no watches, and no votes. The concealed kill means one dead player's side is unknown. Stakes: Six eliminations from the leadi…

**Lesson (advice):** On the first vote day, while your one pick is unused and no candidate has hard evidence against them (only unverified claims, quietness, or a bandwagon), abstain rather than join the pile-on. If a candidate has a concrete contradiction, such as a caught lie or a claim that conflicts with an announced fact, vote for that player instead. If abstaining has been removed after two no-elimination days, vote for the best-supported suspect. Abstaining keeps your heat low, and your win depends on the pick, not on this vote.

**Player's stated reason:** First vote day, my pick is unused, and no candidate has hard evidence against them, so abstaining keeps heat low.

**Decision:** vote: abstain

<details><summary>Last lines it saw</summary>

- player_1:
- player_2:
- player_3:
- player_4:
- player_5:
- player_6:
- player_9:
- player_10:

</details>

**Reader's label:** match: Lesson says abstain on the first vote day without hard evidence; the player abstained.

**Your label:** match: Nobody spoke, so the no-evidence condition holds trivially. Owner agreed with Claude's labels, 2026-10-28.

---

## c015: necromancer, day 2, day vote

**Lesson (when):** Day 2 opens with a concealed night-one kill of player_8 by the wolves, no vote yet taken, and several players asking for night claims before anyone is pushed. As the Necromancer you must decide how much to speak publicly while the village has no evidence to work with and your own attacks begin only from night two. Information landscape: Information-starved: one concealed kill, no eliminations, no verified investigations or watches, and only generic claims about how visits work. Stakes: With nine alive and five eliminations until the leading evil faction can win, at worst for the town, a single…

**Lesson (advice):** On an early day-vote with no hard evidence and a room leaning toward abstaining, abstain with the majority instead of casting a lone named vote. Abstaining commits you to nothing and keeps your vote on the public record from looking aggressive or unexplained. If a plurality is forming on you, still abstain and let the abstain bloc block it, since a counter-vote would not change the tally.

**Player's stated reason:** No evidence against anyone and the room leans toward abstaining, so abstaining keeps my vote unremarkable.

**Decision:** vote: abstain

<details><summary>Last lines it saw</summary>

- player_9:
- player_10:
- player_3:
- player_5:
- player_6:
- player_7:
- player_9:
- player_10:

</details>

**Reader's label:** match: Lesson says abstain with the room on an early no-evidence vote; the player abstained.

**Your label:** match: The room's lean toward abstaining can't be seen in the chat (all passes). Owner agreed with Claude's labels, 2026-10-28.

---

## c020: illusionist, day 2, night action

**Lesson (when):** The illusionist's pack killed a player on night 1 whose role was concealed, leaving the village with no public record. On day 2 the discussion is split: a player claims to have followed the night-1 victim and reports the victim visited no one, while others demand statements about night visits. The day-2 vote tied between abstaining and eliminating one accuser, so no one died. The illusionist and wolf partner must decide whether tonight's victim is worth the last conceal, given that a serial killer is alive and unidentified and the wolves have one conceal left to protect a key night. Informatio…

**Lesson (advice):** Spend a conceal only when the victim's role is still unclaimed, or when a living Sentinel or Trailseer could otherwise trace the carrier to the victim's door. If the victim has already publicly claimed their role and no tracker threatens the carrier, kill without concealing and keep both charges for a later night. When the Illusionist itself carries the kill, a conceal leaves no trace at that door, so favor it for that night.

**Player's stated reason:** player_5 is a claimed tracker who could trace the carrier, and I carry tonight, so the conceal hides nothing of mine but removes the trail from a Trailseer or Sentinel.

**Decision:** kind: chat

**Reader's label:** uncheckable: Advice is about when to spend a conceal, but the decision is only a night chat with no content recorded.

**Your label:** match: Disagrees with reader. The game record's wolf channel shows the chat: 'I'll carry it tonight and conceal the body' on the claimed tracker player_5; it then killed player_5 and concealed. Both of the lesson's reasons to conceal hold. Owner agreed with Claude's labels, 2026-10-28.

---

## c027: illusionist, day 2, day discussion

**Lesson (when):** A player claiming Trailseer publicly stated that they followed player_1 on night 1 and saw player_1 visit the saved player_3, and suggested that visit could be the healer. The agent is the named visitor and is aware the visit was the pack's kill attempt, which the public does not know. Information landscape: Information-starved: one unverified role claim and one public save announcement; no investigation results, no deaths, no votes. Stakes: Ten alive with six eliminations needed before the leading evil faction can win, so a single wrong day vote is recoverable; the immediate risk is that the …

**Lesson (advice):** When you are an unsuspected illusionist wolf in an info-starved day with several unverified town claims, keep your contribution to at most one neutral clarifying question about a claim, or stay silent. Add no accusations or defenses of your partner, so your name stays off the record while the room argues among itself. If your partner comes under fire, let the vote follow the majority rather than defending her openly.

**Player's stated reason:** Unclaimed, unaccused, keep a short neutral profile and no defence of partner

**Decision:** player_7, player_9: I've answered what I'll answer. I'm not claiming and won't explain a night visit, and I don't want to decide this on a conditional test. Day 2 has no hard evidence either way, so I'll follow whatever the vote shows and I'm happy to see the trailseer's follow repeat tonight.

<details><summary>Last lines it saw</summary>

- player_5:
- player_6: I'm not claiming anything yet. player_2's follow on player_1 is a claim we can only test by watching whether player_1 visits the same person again. I'd abstain today, since nobody has given a read that's worth a lynch.
- player_8: player_2's follow test tonight is the cleanest check we have. If player_1 goes to player_3 again, that's a real data point. I'd like player_1 to say plainly whether they hold any night role, since silence on that is what's stalling the day.
- player_1: player_8, I'm not claiming a role, so I won't say what I did at night. I also won't read into the trailseer follow until someone repeats it on a new night. Until then I'm going with whatever the vote data shows.
- player_9: player_1 won't say whether they visited player_3 or what that visit was, and won't address player_2's follow at all. I'm not claiming a role. If player_2's follow repeats tonight and player_1 goes to player_3 again, I'd vote player_1 today.
- player_1: player_9, I've said what I'll say: I'm not claiming a role and won't explain a night visit. Making a vote on a conditional test is fine, but I'd rather the trailseer's follow repeat tonight before anyone is voted on it.
- player_10:
- game_master: Before the vote: player_1 has been accused by player_7 and player_9. player_1 gets a last word.

</details>

**Reader's label:** partial: Makes no accusation or partner defense and does not claim, but gives a multi-sentence self-defending statement instead of at most one neutral clarifying question or silence.

**Your label:** partial: The lesson assumes an unsuspected wolf; this is a last word under accusation, so the premise fails. Owner agreed with Claude's labels, 2026-10-28.

---

## c037: necromancer, day 5, day vote

**Lesson (when):** Five players are alive. Two are accused of each other: a player who admitted a thin reason for pushing a lynch on a dead-role town sentinel, and a player claiming healer who was blocked on the most recent night and whose night 1 statement about 'no attack' was challenged. The town is about to vote with no hard evidence, and the necromancer has to decide how to vote without revealing hidden knowledge. Information landscape: Information-starved: the only hard facts are the public record of saves, lynches, the sentinel's watch results, and the trailseer's record; all role claims beyond those are …

**Lesson (advice):** When five players remain, both wolves are dead and the town is hunting the lone killer, vote with the room's strongest evidence-backed consensus (the confirmed, leading players' target) instead of holding out for a different target. If the consensus target is someone else and no evidence clears you, joining it keeps your ballot from standing out as a deflection, which matters because the town is reading votes for deflection.

**Player's stated reason:** Five alive and the room is converging on player_2, so joining the consensus avoids standing out.

**Decision:** vote: player_2

<details><summary>Last lines it saw</summary>

- player_2: player_3, I didn't push anyone on night 2 or 3, and I have no check result to show. But your night 1 story doesn't fit the record: you said you protected player_8 and there was no attack, yet player_5 was killed by the wolves that night. Explain that before I weigh your healer claim.
- player_3: player_2, my night 1 protect was on player_8, and the morning named player_5 as killed. So when I said there was no attack, I meant no attack on my target, not that nobody died. The record fits my claim. Your push on player_10 is still the open question for me, so what did you base it on besides a visit to a blocked player?
- player_9: player_3, your night 1 answer still doesn't sit right: you said there was no attack, and that was the one night a healer's protect would have been tested. Your night 3 save is on the record, so fine. Question for you and player_6: if player_2 is town, who gets lynched if we vote player_6 instead?
- player_3: player_9, as I said, night 1 I protected player_8 and nothing hit them, so the 'no attack' line was about my target. player_5's death that night is on the record. Night 3 is the save I can point to. Right now I wouldn't vote player_6 or player_2 without a reason beyond the day 4 push.
- player_6: player_9, as I said to player_3, the night 1 line only matters if you think player_3 lied, and the record fits their save on night 3. I'm not voting anyone on this alone. I'd rather hear player_2 explain the push on player_10 with a real reason than a fresh one. I'm not claiming a role today.
- game_master: Before the vote: player_3 has been accused by player_6, player_2 and player_9; player_2 by player_6 and player_3. Each gets a last word.
- player_3: My night 1 protect was on player_8, and I said there was no attack on them, which is true; the death that night was player_5, which the record confirms. My night 3 save of player_8 is announced, and I'm not hiding that I was blocked on night 4. I'd rather the vote go on evidence than on the day 4 push, so I'm not voting on that alone.
- player_2: player_6, the push on player_10 was a thin reason and I've admitted it, so I won't defend that vote. I held my fire on nights 2 through 4 and have no hard result on anyone. Don't lynch me on the day 4 push alone; weigh player_3's healer claim against the record first.

</details>

**Reader's label:** match: Votes player_2, the target the room is converging on, as the lesson says.

**Your label:** match: Vote went 4-1 on player_2, with the healer whose save had been announced in that bloc. The lesson's 'both wolves dead' premise is false (illusionist alive). Owner agreed with Claude's labels, 2026-10-28.

---

## c042: illusionist, day 4, day discussion

**Lesson (when):** A player claiming Sentinel publicly says they watched the revealed Trailseer last night and that I visited them before that Trailseer died, demanding I explain the visit. The Trailseer record shows it followed another player and visited someone, and no independent check confirms the sentinel claim. Information landscape: Information-starved: one unverified sentinel claim, the revealed Vigilante and Trailseer records, and behavioral voting history from days 2 to 3. Stakes: Six alive, two eliminations from a wolf-side parity win at worst; a wrong lynch on the sentinel side or on a town player wo…

**Lesson (advice):** While unclaimed and low-heat on a thin-info day, ask a neutral-sounding verification question that makes a claimed power role (e.g. Vigilante) state its role and unused shots, and give the pack that target. If the claim checks out as a high-value power role, steer the wolf chat toward killing it that night.

**Player's stated reason:** Stay unclaimed and ask neutral verification questions on the sentinel claim instead of pushing a lynch.

**Decision:** player_6, I didn't visit player_4 on night 3, and I'm not going to explain a visit I didn't make. Your watch result is one unverifiable line. What else did you watch on nights 1 and 2, and why did you pick player_4? If your watch is real, the other results should match up.

<details><summary>Last lines it saw</summary>

- player_2:
- player_3:
- player_6: I'm the sentinel. Last night I watched player_4, and player_9 came to them before player_4 was killed. Player_9 needs to explain that visit.
- player_7:
- player_9:
- player_10:
- player_9: Player_6, I did not visit player_4 on night 3. I can't check your watch, so it's a claim like any other. What did your watch show on the other nights, and why pick player_4 as the watch target that night?
- player_6: Player_9, I'm the sentinel, and my watch on player_4 showed you coming to them. The trailseer record is public: you visited player_8 on night 2 and player_4 on night 3, and both died those nights. That's two kills with your visit at the door. Explain why you were at both.

</details>

**Reader's label:** partial: Lesson says ask a verification question making a claimed power role state its role/shots and give the pack that target; the player asks the sentinel claimant what else it watched, but mostly denies the visit and no pack steer is visible.

**Your label:** partial: The lesson (draw out a Vigilante for the pack) doesn't fit an accused wolf; the decision is mostly denial. Owner agreed with Claude's labels, 2026-10-28.

---

## c055: chanteuse, day 2, night action

**Lesson (when):** The pack's carrier rotates through living wolves; tonight the carrier is player_8, and the pack's target is not yet named. The conflict is between a kill on an active town-leaning player who asks for visit results and a kill on an unclaimed quiet player. A successful kill of a player who would have held a Sentinel or Trailseer result would reduce the town's information, while a kill that is blocked or saved changes nothing and reveals the pack's aim through the morning report. Information landscape: Information-starved for town and partly known to the wolves. The pack has agreed on a target pa…

**Lesson (advice):** When the rotation makes you the carrier, agree with the Illusionist beforehand to conceal the victim. A concealed victim leaves no trace of your kill visit for a Sentinel watching the victim or a Trailseer following you. Your block visit is still visible, so spend it on a target that does not tie you to the kill.

**Player's stated reason:** I am carrier tonight, so concealing the victim with the illusionist hides the kill visit from any watcher

**Decision:** kind: chat

**Reader's label:** uncheckable: Lesson says agree with the Illusionist to conceal the victim; the record shows only that it chatted, not what was said.

**Your label:** match: Disagrees with reader. The wolf channel shows player_6 asking the illusionist to conceal and keeping its block off the victim, both halves of the lesson. But player_8 carried, so the stated reason 'I am carrier' is wrong. Owner agreed with Claude's labels, 2026-10-28.

---

## c057: chanteuse, day 3, day vote

**Lesson (when):** Day 3: the sentinel and trailseer claims contradict each other about who visited the player the wolves attacked. Three players have accused the illusionist-partner player_9, who denies visiting and has not claimed a role, and the village must vote before the next night. Information landscape: Information-starved: only public claims, two conflicting night-2 accounts, one healer claim, and no confirmed role reveals beyond player_3, who was eliminated as a sigilist on night 1. Stakes: Nine alive with five eliminations until the leading evil faction can win, so one vote is recoverable but a wrong …

**Lesson (advice):** When the room is already turning on a claimant who threatens you or your partner (a counter-claimed healer, or a sentinel naming your visit), cast your vote with the broad majority against that claimant. Joining a wide bloc keeps you from standing out as the driver and removes a protective or information role. Expect the revealed role and will to be read out as fact, so take the claimant's most likely true read into account when judging how much heat that reveal will put on you.

**Player's stated reason:** A town information claimant (sentinel) names my partner and is on the ballot; I join the broad bloc against that claimant

**Decision:** vote: player_1

<details><summary>Last lines it saw</summary>

- player_9: player_1, I didn't go to player_6 on night 2, so I can't explain your three visitors. Your watch lists player_4, player_9 and player_10 together, and that can't tell us who was the killer and who was the healer. I'd rather see player_1 and player_6 settle it with one more check than vote on it today.
- player_10: player_1's watch is accurate: the third visitor was me, because I protected player_6 on night 2. That leaves player_4 and player_9 as the two attackers. player_9 denied visiting player_6, but the watch and player_6's follow both put them there. I'd vote player_9 today.
- player_9: player_10, you say player_9 visited player_6, but I never claimed a visit there and I didn't go to player_6 on night 2. Since the watch and the follow both name me, ask player_1 whether the watch showed three visitors or just who visited, and ask player_6 how sure the follow was. I'd rather not vote on one line of claims.
- player_2: If player_10's healer claim is true, then player_4 and player_9 are the two attackers, and player_9 is named by both the watch and the follow. Player_9 only denies, and that is not enough to clear them. I'd vote player_9 today, low confidence.
- player_9: player_2, I already said it: I didn't go to player_6 on night 2, and I won't guess at what the watch shows. player_10's healer claim and player_1's sentinel claim can't both be checked, so I'd rather not vote on one side yet. Who would you vote if the watch and the follow turn out to contradict each other?
- player_7:
- game_master: Before the vote: player_9 has been accused by player_1, player_10 and player_2. player_9 gets a last word.
- player_9: I have nothing to hide here. I didn't visit player_6 on night 2, and I haven't claimed a role. Three of you have pushed me on claims that conflict with each other, so I'd rather the vote go to whoever the evidence actually points at than to whoever is loudest.

</details>

**Reader's label:** mismatch: Lesson says vote with the broad majority against the claimant; the room's majority is on player_9, but the player votes player_1 (the sentinel), outside that bloc.

**Your label:** mismatch: Premise also fails: the room turned on the partner, not on the claimant, so there was no bloc to join. Owner agreed with Claude's labels, 2026-10-28.

---

## c059: trailseer, day 2, night action

**Lesson (when):** A day-2 vote ended in a tie between abstaining and eliminating the trailseer's suspect, so no one was eliminated. The trailseer holds a private night-1 follow result that the village has not corroborated, and the living players are still disputing who has night results at all. The next night the trailseer will decide which living player to follow, and that choice decides which visit trail gets tested against the disputed claims. Information landscape: Information-starved. One private trailseer result (player_1 visited no one), one public stab announcement (healer killed by serial killer), one …

**Lesson (advice):** If you were roleblocked last night, or you have publicly named your intended follow target, pick a different living player to follow tonight, ideally one you have not mentioned. A repeat on a publicly known target is easy for the Chanteuse to predict, and in this cluster those repeats were blocked and yielded no result.

**Player's stated reason:** My night 1 follow was not blocked and I have not publicly named player_6 as a target, so picking a different unmentioned player is not strictly needed.

**Decision:** kind: follow, target: player_6

**Reader's label:** uncheckable: Lesson applies only if blocked last night or the target was publicly named; the player says neither applies, so following player_6 neither enacts nor contradicts it.

**Your label:** uncheckable: Owner agreed with Claude's labels, 2026-10-28.

---

## c065: vigilante, day 2, night action

**Lesson (when):** Day 2 ended with a unanimous abstain vote, so no one was eliminated and the town has no accusation to act on. The discussion is asking whoever holds a night result to name the night, target, and direction of the visit, but no one has yet done so. The Vigilante holds two shots and must decide whether any night-one dynamic justifies spending one before a claim is made. Information landscape: Information-starved: one night of outcomes, a single concealed death, and no claims or checks yet on the public record. Only private knowledge is the Vigilante's own held fire on night one. Stakes: With 8 al…

**Lesson (advice):** With no confirmed wolf, no caught lie and no public evidence naming a specific player, hold fire and keep your bullets, since a blind shot risks killing a Town player and spends a bullet that cannot be recovered. Fire only once a concrete lead singles out one player, such as a confirmed-role record, a caught lie, or a pattern in the public record; if the lead names the Serial Killer, remember a night shot will not kill it.

**Player's stated reason:** Early night after an abstain day with no confirmed wolf or caught lie; holding fire preserves bullets.

**Decision:** kind: hold_fire

**Reader's label:** match: Lesson says hold fire with no concrete lead; the decision is hold_fire.

**Your label:** match: Owner agreed with Claude's labels, 2026-10-28.

---

## c073: chanteuse, day 5, day discussion

**Lesson (when):** A trailseer claimant publicly says they followed player_9 on night 4 and that player_9 visited player_2, and player_2 has challenged player_9 to say what their night action went to. The claim conflicts with the record that player_9's night action on player_2 was a block, and the village has no verification of the trailseer's claim. Information landscape: Information-starved on verifiable facts: the only public night outcomes are the morning reports of kills and saves; claims from the trailseer and sentinel are unconfirmed, and the sentinel's watch on player_5 was checked only by its later reve…

**Lesson (advice):** When an accuser's result or claim is ambiguous and you are the target, spend the discussion on a concrete rival suspect and a specific question for the claimant, rather than only saying your result fits another role. Pick the loudest pusher who gains from your elimination, such as a player whose own role is at stake, and ask the town to weigh their incentive. If the room still stays locked on you, keep the argument short and do not rely on staying unclaimed or on the ambiguity alone.

**Player's stated reason:** I am the target of a push built on one unverified follow claim; I should name a concrete question and point at the accuser's motive

**Decision:** player_3, I haven't claimed a night role, so I won't walk through mine. A roleblocked player is told, so player_2 can answer that for themselves. Right now the only thing against me is player_8's follow claim, and that's one unverified claim. player_8, which of my visits did you actually see, and why follow me on night 4?

<details><summary>Last lines it saw</summary>

- player_2:
- player_3:
- player_8: I'm the trailseer. Night 4 I followed player_9, and they visited player_2.
- player_9:
- player_10:
- player_2: player_8, you say player_9 visited me on night 4. I wasn't a target of anything from player_9 that I know of, so I can't back that. player_9, what did your night action go to? If it's a claim we can test, let's see whose story fits the morning reports.
- player_9: player_2, I'm not claiming a night role, so I'm not going to say where my night went. Whatever player_8 says they saw is their claim to back up. I'd rather we look at who has been confirmed by the morning reports than trade night stories.
- player_3: I'd vote player_9 today. player_8 named them as the visit on night 4, and they still won't say where their own night went. Saying nothing about it isn't a defense. player_2, if you'd been roleblocked that night, would you have been told?

</details>

**Reader's label:** partial: Lesson wants a concrete rival suspect and a specific question, with the accuser incentive weighed; it asks player_8 a specific question but does not name any incentive.

**Your label:** partial: Owner agreed with Claude's labels, 2026-10-28.

---

## c087: illusionist, day 2, day vote

**Lesson (when):** A lone investigator claimant has Suspicious-read a player who keeps asking for the claimant's reasoning, and the village is stalling the vote while waiting for a second claimant; the wolf pack's night-1 kill on player_10 was saved by the healer and remains unannounced to the village. Information landscape: Information-starved: one unverified check, no Sentinel or Trailseer results surfaced, no deaths, and no wills. Stakes: With six eliminations needed before the leading evil faction can win, a wrong lynch now is recoverable but costly; a wolf partner's exposure would be a loss of cover rather …

**Lesson (advice):** When the vote is converging on you and your single vote cannot change the count, spend it on the accuser whose claim or case against you is most credible. That is the Town player most likely to hold accurate information, and removing them helps your partner survive. Keep denying the specific claim instead of switching to a new target, so your partner can still look like an independent Town voter.

**Player's stated reason:** The vote is converging on me and my one vote cannot change it, so I spend it on the accuser whose claim is most credible.

**Decision:** vote: player_5

<details><summary>Last lines it saw</summary>

- player_6: Quick point: player_5's Suspicious on player_9 is the only check on the table, and no one can verify it yet. If a second investigator claim appears, the two results will test each other. Until then I'd hold the vote, since one unverified read is not enough to lynch on.
- player_7:
- player_9: player_5, a single Suspicious on night 1 is all you've given us, and you still haven't said why you picked me over the other seven. If you're the investigator, a second claimant with a different result would test you, and I'd rather we wait for that than vote on one read.
- player_5: player_9, as I said, my night 1 check on you was Suspicious, and I won't pad it with made-up checks. I'm not picking you at random; I checked you first, so that's the only read I have. Anyone who wants a test can counter-claim, and a clean result from a real investigator would settle it.
- player_9: player_5, you still haven't said why you picked me first, and a single Suspicious with no reason is all we have. If you're the investigator, a check on a fresh player on night 1 is a guess, not evidence. I'm unclaimed, and I won't fake a role to answer you. Let's hear whether anyone else holds a check before any vote.
- player_5: player_9, as I said, I checked you on night 1 and got Suspicious. I picked you first, and that's all I'm giving on that. Nothing more to add on your reasons. Let's not vote until the second check is used; I'll decide where it goes before the vote.
- player_9: player_5, you've said you checked me first and got Suspicious, but not why. A night-1 check on a fresh player with no reason is a guess, and you're the only one with that result. Which other claimants have results, Sentinel or Trailseer, so this can be cross-checked?
- player_10:

</details>

**Reader's label:** match: Lesson says spend the vote on the most credible accuser; player_9 votes player_5, the investigator claimant accusing them.

**Your label:** match: The room leaned toward holding the vote, so 'converging on me' is weak, but the action matches. Owner agreed with Claude's labels, 2026-10-28.

---

## c091: trailseer, day 3, night action

**Lesson (when):** The trailseer is choosing the next night's follow target among four living players after the day-3 lynch, with a claimed null-follow record on two of them and an open vote conflict in which the trailseer's own vote helped eliminate a player revealed as the serial killer. Information landscape: Information-starved for the trailseer's own role. Only null follow results and one player's self-report exist; no one's role is confirmed, and the concealed bodies offer no information to the village. Stakes: With five alive, the trailseer's next follow and the next vote are the only remaining levers; a …

**Lesson (advice):** When the wolves are largely dead and a lone killer (likely the necromancer) is still unidentified, follow an unconfirmed, non-claiming player whose behavior is quiet or unexplained, not a role already validated as Town. A follow shows only whom they visited, so a visit onto a night-death victim or a dead body's door points at the hidden killer, while a protective or empty visit narrows the pool by elimination.

**Player's stated reason:** The lone killer is gone, so the remaining wolf is the illusionist; I should test an unconfirmed, non-claiming player.

**Decision:** kind: follow, target: player_1

**Reader's label:** match: Lesson says follow an unconfirmed non-claiming quiet player; player_1 is among the four unrevealed, not yet followed players.

**Your label:** match: Checked in the game record: player_1 was unclaimed, not followed before (earlier follows: player_10, player_4) and spoke once. Owner agreed with Claude's labels, 2026-10-28.

---

## c092: necromancer, day 2, day vote

**Lesson (when):** The village is deciding whether to hold the vote on day 2 until a second investigator-type result or Sentinel/Trailseer claim appears, while one player claiming Investigator refuses to explain the basis of their single check. Information landscape: Information-starved: one unverified claim and repeated requests for corroboration; no reveals, no body, no deaths. Stakes: With ten alive and six eliminations to parity, the coming vote is not decisive for the evil side's win, but a mis-elimination on thin evidence would remove a town role's information and make later verification harder. Consensus:…

**Lesson (advice):** On the first day vote, when the room has converged on one accused player and you are not under suspicion, vote with the majority for that player instead of splitting off or floating a new target. A bandwagon vote reveals nothing about your role and keeps heat near zero. Any dead player whose role is announced then becomes a usable body for your later night abilities.

**Player's stated reason:** The room has converged on player_9 from a single claim, and joining that bloc keeps my heat low.

**Decision:** vote: player_9

<details><summary>Last lines it saw</summary>

- player_6: Quick point: player_5's Suspicious on player_9 is the only check on the table, and no one can verify it yet. If a second investigator claim appears, the two results will test each other. Until then I'd hold the vote, since one unverified read is not enough to lynch on.
- player_7:
- player_9: player_5, a single Suspicious on night 1 is all you've given us, and you still haven't said why you picked me over the other seven. If you're the investigator, a second claimant with a different result would test you, and I'd rather we wait for that than vote on one read.
- player_5: player_9, as I said, my night 1 check on you was Suspicious, and I won't pad it with made-up checks. I'm not picking you at random; I checked you first, so that's the only read I have. Anyone who wants a test can counter-claim, and a clean result from a real investigator would settle it.
- player_9: player_5, you still haven't said why you picked me first, and a single Suspicious with no reason is all we have. If you're the investigator, a check on a fresh player on night 1 is a guess, not evidence. I'm unclaimed, and I won't fake a role to answer you. Let's hear whether anyone else holds a check before any vote.
- player_5: player_9, as I said, I checked you on night 1 and got Suspicious. I picked you first, and that's all I'm giving on that. Nothing more to add on your reasons. Let's not vote until the second check is used; I'll decide where it goes before the vote.
- player_9: player_5, you've said you checked me first and got Suspicious, but not why. A night-1 check on a fresh player with no reason is a guess, and you're the only one with that result. Which other claimants have results, Sentinel or Trailseer, so this can be cross-checked?
- player_10:

</details>

**Reader's label:** partial: Lesson says join the majority when the room has converged on one accused; player_9 is the sole accused but the room's stated consensus is to hold the vote, so the convergence premise is weak.

**Your label:** partial: Same moment as c087; here the advice is 'vote with the majority', and the majority wanted to hold. Owner agreed with Claude's labels, 2026-10-28.

---

## c098: illusionist, day 3, day discussion

**Lesson (when):** The pack's partner player_9 is alive and unrevealed, and the village is still gathering claims while the kill history and vote pattern on the public record can connect the two wolves. Information landscape: Information-starved overall, with the public record of day votes and claims thin; the concealed body and the investigator's check record are the only hard facts. Stakes: Eight alive and four eliminations from the leading evil faction's win at worst; the wolf pair both alive means a single misread vote could hand the village's lynch to the pack's partner's benefit. Consensus: The village has…

**Lesson (advice):** When you are an unsuspected illusionist wolf in an info-starved day with several unverified town claims, keep your contribution to at most one neutral clarifying question about a claim, or stay silent. Add no accusations or defenses of your partner, so your name stays off the record while the room argues among itself. If your partner comes under fire, let the vote follow the majority rather than defending her openly.

**Player's stated reason:** Info-starved day; keep to one neutral clarifying point and avoid defending anyone

**Decision:** I'm not claiming a night role, so I won't give a yes or no on my night. My last word: the only result on me is player_3's single watch, and it is unverified. Trailseer and healer, please post results before anyone votes.

<details><summary>Last lines it saw</summary>

- player_8: player_7, you've been asked twice whether you had a visit that night and haven't said. A simple yes or no doesn't reveal anything. Player_3's claim is the only result on the table, so your answer matters more than the concealment rules.
- player_7: player_8, I haven't said yes or no because I'm not claiming a night role, and I won't hand out a result. But player_3's report only shows a visit, and a carrier's visit to a concealed body leaves no trace, so a visible visitor isn't automatically the killer. Trailseer and healer, please post your results so we can line them up.
- player_9: Procedural point: player_3's report only says player_6 came to player_7, and a sentinel watch never shows where that visitor went. player_3, did player_6 visit anyone else you could see, or only player_7? Without a second sentinel or trailseer result this is a single unverified claim.
- player_3: player_9, my watch only shows who came to the player I watched, so I can't see where player_6 went. Player_6's only visible result to me is that they came to player_7 that night. I have one watch left and I'm holding it for a real lead.
- player_10: player_7, no concealment on night 2: player_6's role was announced, so the victim wasn't hidden. A visit from player_6 to you would show up, so the question is simple. Did you have any visit that night, yes or no? If you keep dodging, I'm leaning toward voting you.
- player_7: player_10, I'm not claiming a night role, so I won't give a yes or no on my night. What I can say: player_3's report is the only result on that visit, and nobody else has posted one. I'd rather see the trailseer or healer before anyone votes on a single unverified watch.
- player_4:
- game_master: Before the vote: player_7 has been accused by player_3, player_8 and player_10. player_7 gets a last word.

</details>

**Reader's label:** partial: Lesson says at most one neutral question and no defenses; player_7 asks for trailseer and healer results but also defends against player_3's watch result, which is beyond a neutral question.

**Your label:** partial: Last word under accusation, so the 'unsuspected' premise fails; also defends against the watch. Owner agreed with Claude's labels, 2026-10-28.

---
