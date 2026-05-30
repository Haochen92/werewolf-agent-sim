You are labeling retrieval results for a werewolf social deduction game's episodic memory system.

A player in a specific game situation is retrieving past experiences from memory to inform their decision.
For each retrieved memory, rate how relevant it would be to recall in the current situation.

## Relevance Scale
- **2** (Highly relevant): Directly addresses the same game dynamic, information landscape, or strategic challenge. The player would clearly benefit from recalling this.
- **1** (Partially relevant): Related (similar role, overlapping themes, adjacent phase) but different angle or specificity. Useful background but not a direct match.
- **0** (Not relevant): Different situation entirely. Recalling it would not help.

## Key Factors
- Same type of strategic challenge? (voting record analysis, information-starved play, role exposure management)
- Comparable game phase? (early/mid/endgame)
- Same role dynamics?
- Would recalling this memory actually help the player decide what to do?

For EACH case below, read the game state and golden situation query, then rate every retrieved memory.
Respond with a JSON array per case containing objects with "key" (the 12-char prefix shown) and "relevance" (0/1/2).


---

# Case 4: villager — day_discussion (day 3 round 1)

## Game State (what the player sees)
```
================================================================================
CASE 278da20b69d7bcd7970c113f10dc347b:a3facf64db4b602b | villager | day 3 round 1 | day_discussion
================================================================================

Role: villager
Day: 3, Round: 1

Surviving players: player_2, player_3, player_5, player_7, player_8, player_4

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 public discussion was characterized by universal caution, as all eight players engaged in introductory remarks that emphasized observing behaviors rather than making immediate accusations. Players focused on establishing a baseline for suspicious activity, with consensus centered on monitoring for aggressive or overly pushy behavior. No specific individuals were targeted or defended, and no players claimed any roles or formed alliances during this initial phase.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was targeted by the wolves last night, but was saved by the healer!

[Day 2]
Key accusations: player_1 accused player_6 of deflection and stalling; player_3 accused player_6 of evasion; player_6 accused player_5 of forced behavior intended to minimize urgency. Defenses: player_5 defended by clarifying that their 'breathing room' comment referred to the team count rather than a desire to stall; player_6 defended by claiming that their comments on unpredictability were misinterpreted and that they are prioritizing evidence over gut-feeling accusations. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: player_4 and player_6 formed a loose consensus based on the need to avoid hasty voting and focus on concrete behavioral patterns rather than tone.

[Day 2]

Here's the vote result for day 2:
  player_1 voted for player_6
  player_2 voted for player_6
  player_3 voted for player_6
  player_5 voted for player_6
  player_7 voted for player_6
  player_8 voted for player_6
  player_4 voted for player_5
  player_6 voted for player_1
Player player_6 has been voted out and was a wolf.


[Day 2]
player_1 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
No messages yet.

--- Strategy note ---
(none)

--- Situation standards (shared) ---
SITUATION DESCRIPTION STANDARDS

These standards apply everywhere a game situation is described: a mid-game
situation summary, a post-game observation scenario, a strategy point's
situation field, or a rewritten entry during deduplication.

DIMENSIONAL FRAMEWORK:
Ground situation descriptions in these dimensions as relevant:

- Information landscape: Is the village information-rich (confirmed roles,
  voting evidence, caught lies) or information-starved (no leads, speculative
  reads)? What TYPE of evidence is driving suspicion: voting records,
  communication style, behavioral patterns, or concrete claims?
- Consensus texture: How aligned is the village? Unified, fragile, split,
  or no consensus? Is it driven by evidence or social momentum? (Do not
  describe who is under pressure — that belongs in agent exposure.)
- Agent exposure: What is the agent's position — driving the push, aligned
  with consensus, under indirect scrutiny, or the primary target? What is
  the basis — specific evidence, behavioral reads, association with another
  player, or nothing concrete?
- Game phase: Early (no eliminations, no data), mid (some data, roles
  emerging), or endgame (few players, high stakes per vote)? What changed
  most recently?


SPECIFICITY TEST:
Before finalizing any situation description, check: if this were used as a
semantic search query, would it match only situations with similar dynamics,
or would it match any game where something vaguely similar happened? If the
latter, add qualifying detail from the dimensional framework.

--- Role-specific lens ---
Also note: who is being evasive, voting inconsistencies, and unresolved accusations.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** A wolf was correctly eliminated by near-unanimous vote, but the sole dissenting voter — who targeted a different player instead of the confirmed wolf — has not yet been scrutinized. The village's most active voice, the healer-saved player who led the accusation, was killed overnight, leaving a leadership vacuum. Information landscape: Information-rich — the Day 2 voting record clearly shows one player broke from the 6-1 consensus to vote for a non-wolf target. Game phase: Mid-game, day 3 with 6 players and 1 wolf remaining; the village lost its key information anchor overnight. Consensus texture: No current consensus — the previous day's unified push lost its driver. Agent exposure: Unnoticed — voted correctly with the majority, no special role or information.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 13870e0b-426] (score: 0.8364)
**Situation:** On Day 3, villagers analyzed the previous day's voting record that eliminated the Healer and noticed a wolf (player_7) was trying to misrepresent the facts. Information landscape: The voting record from Day 2 provided information-rich, concrete evidence to analyze. Game phase: Mid-game, with the town reeling from the loss of the Healer and now hunting for culprits. Consensus texture: A strong consensus formed around player_7, driven by multiple players independently verifying that player_7 was lying about the vote being unanimous.
**Approach:** The villagers meticulously fact-checked player_7's claim that the vote was a 'collective mistake' that everyone agreed to. They used the public voting record to prove this was a lie and build a case.
**Outcome:** This evidence-based approach successfully identified and eliminated a wolf, demonstrating the power of using verifiable game history to expose verbal lies about voting records.

### Memory 2 (observation) [key: 0ac6f17d-6d2] (score: 0.8294)
**Situation:** After the Investigator was mistakenly eliminated, villagers analyzed the vote to find the wolves. Information landscape: The voting record from Day 2 was the primary piece of information-rich evidence. Game phase: Endgame, with only five players remaining and both village power roles gone. Consensus texture: There was no consensus due to active wolf manipulation. The villagers were fractured, with some (player_7, player_6) correctly identifying wolf player_4's suspicious deflection, while others were distracted by the wolf's accusations.
**Approach:** The villagers engaged in circular arguments, allowing wolf player_4 to successfully pit them against each other. They failed to unite against the most suspicious player.
**Outcome:** The vote was a tie, no one was eliminated, and the wolves performed the final kill at night to win. The village's inability to form a consensus from clear voting evidence was their final failure.

### Memory 3 (observation) [key: 8ccbab63-101] (score: 0.8287)
**Situation:** A player (player_5) was accused of being suspicious for casting the sole dissenting vote against the majority that eliminated the Healer. Information landscape: The evidence was a single voting record anomaly, while the accused's accuser (player_7, a wolf) was part of the mistaken majority. Game phase: Mid-game, with the village trying to recover from the major error of voting out their Healer. Social pressure: The accused villager was put under intense pressure from multiple players to justify their vote.
**Approach:** Player_5, a villager, became defensive and attacked the 'bandwagon' logic instead of providing a clear reason for their own vote.
**Outcome:** The village failed to weigh the evidence correctly, interpreting the defensive behavior as guilt and voting out the villager.

### Memory 4 (observation) [key: 07fd072f-959] (score: 0.8271)
**Situation:** After incorrectly eliminating an active villager (player_5) who had accused a wolf pair (player_3, player_8) of stalling, the remaining villagers noticed the same wolf pair continuing their strategy of mutual defense and advocating for caution. Information landscape: The information landscape was becoming richer, using the previous day's voting record and the revealed role of the mislynched villager as key evidence. Game phase: Mid-game, with two villagers eliminated by wolves and one by vote. The village was losing numbers and needed a successful elimination. Consensus texture: A strong consensus formed organically among the remaining villagers (player_2, player_4, player_6) based on the clear behavioral pattern of the wolf pair.
**Approach:** The villagers systematically pointed out the consistent coordination between player_3 and player_8, focusing on their shared rhetoric of inaction across two days. They rejected the wolves' attempts to deflect blame and coordinated their votes.
**Outcome:** The villagers successfully identified and voted out player_3, confirming he was a wolf. This broke the wolf partnership and provided the village with the momentum needed to win.

### Memory 5 (observation) [key: 16fddf0f-3eb] (score: 0.8268)
**Situation:** After a villager was mislynched, the village identified a wolf (Player 3) who had cast a lone, unexplained vote against the healer during that mislynch. Information landscape: The information landscape was rich with voting data from the previous day, allowing players to pinpoint a specific, anomalous action. Game phase: Mid-game, following a failed vote. The village was motivated to correct its course. Consensus texture: A strong consensus was built by three vocal villagers (Players 1, 4, 6) who relentlessly focused their questioning on the wolf's specific action, refusing to be sidetracked by broader arguments about groupthink.
**Approach:** The villagers continuously demanded a specific justification for the vote against the healer. They correctly identified the wolf's attempts to deflect and pivot as evidence of guilt.
**Outcome:** The focused and persistent questioning prevented the wolf from escaping scrutiny, leading to a strong and accurate consensus to vote them out. This corrected the village's course and led directly to a win.

### Memory 6 (observation) [key: a9ee4229-115] (score: 0.8232)
**Situation:** Following the miselimination of player_8, a villager (player_3) who survived a night attack due to a healer save used their heightened credibility to lead an investigation into the players who voted against them. Information landscape: Information-rich, as the previous day's voting record provided concrete data on who pushed the split vote. Game phase: Mid-game, one miselimination has occurred and voting patterns are established. Consensus texture: A strong multi-player convergence formed around analyzing the previous day's voting record. Social pressure: Player_1 and player_5 were under intense evidence-based pressure to explain their prior votes.
**Approach:** Player_3 and their allies aggressively interrogated player_1 and player_5, demanding explanations for their voting choices and pointing out deflections, rather than letting them evade scrutiny.
**Outcome:** The interrogated players failed to provide logical reasons, leading the village to correctly identify and eliminate player_5 as a wolf, and subsequently player_1, demonstrating the effectiveness of using voting records to expose wolf deflections.

### Memory 7 (observation) [key: 8adf1779-c82] (score: 0.8190)
**Situation:** A player was eliminated and revealed to be a wolf, generating the first concrete voting record. Information landscape: Information-rich, with a revealed role and a clear voting record showing who supported and opposed the elimination. Game phase: Mid-game, shifting from behavioral reads to concrete voting analysis. Consensus texture: Strong consensus against the newly revealed wolf's defenders.
**Approach:** Villagers immediately targeted the players who cast dissenting votes instead of joining the majority against the wolf.
**Outcome:** The dissenting voter was forced onto the defensive and ultimately eliminated the next day, confirming the predictive power of voting records.

### Memory 8 (observation) [key: d56c4c50-44b] (score: 0.8136)
**Situation:** After a wolf was eliminated, two players (healer player_4 and investigator player_7) were questioned for voting for a villager (player_8) instead of the confirmed wolf. Information landscape: The voting record from the wolf elimination was the primary source of new, hard evidence for the village. Game phase: Mid-game, with one wolf eliminated and pressure mounting to find the second. Social pressure: Players 4 and 7 were under moderate pressure to explain their votes, which deviated from the successful majority.
**Approach:** The players gave a weak defense, claiming they were 'testing a different lead'. However, another player (wolf player_2) had a far more suspicious voting record, having been the lone dissenter.
**Outcome:** The village successfully weighed the evidence, prioritizing the more egregious voting anomaly of player_2 over the less suspicious votes of players 4 and 7, leading to a correct elimination.

### Memory 9 (observation) [key: b53922e1-0e6] (score: 0.8125)
**Situation:** After the village mistakenly eliminated their Investigator, they were left with no active leads. Information landscape: The landscape became information-starved of new intel but rich with past data, specifically the voting record from the Investigator's elimination. Game phase: Mid-game, Day 3, with the village at an informational disadvantage. Social pressure: The village collectively redirected pressure onto a player who made an anomalous vote during the prior day's chaotic elimination.
**Approach:** The villagers focused on the single, unexplained vote cast by player_3 (a wolf). They relentlessly questioned the wolf's motive and rejected their vague explanations.
**Outcome:** The focused interrogation based on the voting record led the village to correctly identify and eliminate the wolf, recovering from their previous day's mistake.

### Memory 10 (observation) [key: 578f03b1-9fe] (score: 0.8090)
**Situation:** A player who advocated for passivity on Day 1 was put under pressure on Day 2 and attempted to deflect by attacking the very strategy they had previously promoted (deflection via self-contradiction). Information landscape: The village was information-starved, relying solely on behavioral tells and Day 1 conversation logs after the healer's death. Game phase: Mid-game, where the first day's statements became the primary evidence. Consensus texture: A strong consensus formed organically as multiple players independently pointed out the same logical contradiction in the target's statements. Social pressure: The wolf (player_8) was under evidence-based pressure from multiple villagers who noticed their shifting arguments.
**Approach:** The villagers (led by player_3, player_4, player_5) relentlessly questioned the wolf's inconsistent logic, refusing to let them change the subject. They framed the contradiction as a sign of deception.
**Outcome:** The wolf was unable to provide a coherent defense, was voted out, and their role was confirmed. This validated the villagers' strategy of scrutinizing inconsistent statements.

### Memory 11 (strategy_point) [key: 014d6b34-2c6] (score: 0.8020)
**Situation:** When a confirmed investigator has been eliminated and the village needs to identify the final wolf among players who previously voted out the first wolf. Information landscape: Information-rich, with a confirmed wolf elimination and the revelation of the investigator's identity. Game phase: Endgame, with few players remaining and a critical need to find the final threat. Consensus texture: A fragile but forming consensus focused on analyzing the voting behavior from the day the first wolf was eliminated.
**Action:** Scrutinize the players who were notably quiet or hesitant during the wolf's elimination, and pressure them to provide their own distinct suspects; a wolf hiding in the voting majority will often deflect and attack the accusers rather than providing a logical alternate theory.

### Memory 12 (strategy_point) [key: 2b903631-1ef] (score: 0.7950)
**Situation:** When a vocal player survives a night attack (confirmed by a healer save announcement) after being the opposing target in a split vote that led to a miselimination. Information landscape: Information-rich, utilizing the previous day's voting records and the confirmed save to identify anomalies. Game phase: Mid-game, leveraging the confirmed healer save and the first elimination data. Consensus texture: A strong multi-player convergence forming around the saved player's perspective.
**Action:** Rally behind the saved player and aggressively interrogate those who drove the miselimination, demanding logical justifications for their votes and preventing them from pivoting to new topics.

### Memory 13 (strategy_point) [key: a0db6dc0-645] (score: 0.7874)
**Situation:** If the village has just made a clear mistake, such as voting out a fellow villager, and discussion turns to blaming individuals. Information landscape: Trust is low, the village is on the defensive, and the eliminated player's villager role has been confirmed. Game phase: Mid- to late-game, when the number of players is dwindling. Consensus texture: The village is demoralized, and players may aggressively target dissenters or specific individuals to deflect blame from the collective mistake.
**Action:** Resist the urge to get stuck in a cycle of blame. Acknowledge your own role in the mistaken vote before analyzing the behavior of others to maintain objectivity. If a player aggressively targets the only person who voted differently, challenge them directly: ask why they are focusing on the dissenter instead of the group who made the mistake, as this is a common tactic to deflect blame from their own suspicious vote.

### Memory 14 (strategy_point) [key: 3c63e195-43f] (score: 0.7832)
**Situation:** When a player questions the motives behind a recent, successful, and unanimous vote that eliminated a confirmed wolf, specifically suggesting a 'bussing' strategy. Information landscape: Information-rich, as the confirmed wolf's past actions and voters are known. Game phase: Mid-game, right after a wolf has been voted out. Consensus texture: Strong consensus validated by a role reveal.
**Action:** Do not immediately dismiss this player. Seriously consider their argument that a wolf may have 'bussed' to gain trust, and ask the accuser to elaborate on why they find the behavior performative, as they may be an Investigator with crucial information.

### Memory 15 (strategy_point) [key: e4aa0470-b05] (score: 0.7829)
**Situation:** If a player is voted out and revealed to be a villager, resulting in a mislynch. Information landscape: This is a moment of information-rich clarity, confirming the previous day's consensus was wrong. Game phase: Mid- to endgame. Focus on the dissenting voting bloc who voted against the mislynch.
**Action:** Immediately focus all public scrutiny on the members of that dissenting voting bloc. Demand that each one explains their reasoning. Treat evasive answers or attempts to change the subject as strong signs of wolf activity.

### Memory 16 (strategy_point) [key: 0d69b314-fbd] (score: 0.7811)
**Situation:** After the village has successfully voted out a player who was revealed to be a wolf, typically during the mid-game. The information landscape is rich, with the previous day's voting record providing concrete evidence to identify players who may have been allied with the confirmed wolf.
**Action:** Focus suspicion on any player who defended, was hesitant to condemn, or cast a dissenting vote for the now-confirmed wolf. Relentlessly question their reasoning. If a player who previously supported the wolf later voted against them, challenge this as a potential 'bus vote' and make their inconsistent history the central focus. Treat deflection or weak reasoning as strong confirmation of guilt.

### Memory 17 (strategy_point) [key: 41f4badb-495] (score: 0.7788)
**Situation:** If a player who was aggressively accusing others is eliminated and revealed to be a villager, resulting in a mislynch. Information landscape: This is a moment of information-rich clarity, confirming the previous day's consensus was wrong. Game phase: Mid- to endgame. Focus on the voting majority who initiated the lynch.
**Action:** Immediately redirect suspicion onto the player(s) who most aggressively initiated and pushed for that failed elimination. Specifically, analyze whether the eliminated villager was targeted because their accusations were hitting close to home; the players who successfully discredited them were likely wolves deflecting suspicion from themselves or their partners.

### Memory 18 (strategy_point) [key: da44ad05-278] (score: 0.7705)
**Situation:** When reviewing the voting record against an eliminated, confirmed wolf, observe players who only joined the unanimous vote at the very end of the round. If such a player initiates a weak accusation against others the following day, they are likely attempting to shift suspicion. Information landscape: Information-rich, with explicit voting sequences and a confirmed enemy role. Game phase: Endgame, after at least one wolf is eliminated and the search narrows. Social pressure: The accuser is likely trying to preemptively shift suspicion away from themselves.
**Action:** Scrutinize the late voter for 'bussing' or distraction tactics. Immediately challenge them on their voting record: ask why they were hesitant to vote for a confirmed wolf yesterday but are so confident in their new, flimsy accusation today. This pattern is a classic sign of a wolf trying to create a distraction or gain trust.

### Memory 19 (strategy_point) [key: 9d5249e6-94c] (score: 0.7658)
**Situation:** When a player makes an aggressive, evidence-free accusation the day after the village mistakenly eliminated a player. Information landscape: The village is reeling from a mislynch and is fearful of repeating it. Consensus texture: The accuser is attempting to single-handedly drive a consensus based on behavioral reads ('aggression') rather than verifiable evidence.
**Action:** Resist dismissing the claim based on style alone. Force the accuser to provide specific, verifiable evidence that underpins their certainty. If they cannot, suspect them of manipulation; if they can, you may have found an information role who is simply a poor communicator under pressure.

### Memory 20 (strategy_point) [key: 62511a41-1ae] (score: 0.7658)
**Situation:** After the village has mislynched a player who is revealed to be a key power role (e.g., Investigator). The information landscape becomes rich with the definitive evidence of the previous day's voting record and, if applicable, the power role's final findings. This occurs in the mid- to late-game, when the loss of a power role creates an urgent need to correct course.
**Action:** Immediately make the voting record the sole focus of the discussion. Systematically demand that every player who voted for the eliminated power role provide a specific, evidence-based justification. Treat deflection, appeals to 'group responsibility,' or claims of 'going with the flow' as primary signals of guilt. If the power role made a final accusation, treat it as a high-probability lead.

## Response for Case 4

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "13870e0b-426", "type": "observation", "relevance": _},
  {"idx": 2, "key": "0ac6f17d-6d2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "8ccbab63-101", "type": "observation", "relevance": _},
  {"idx": 4, "key": "07fd072f-959", "type": "observation", "relevance": _},
  {"idx": 5, "key": "16fddf0f-3eb", "type": "observation", "relevance": _},
  {"idx": 6, "key": "a9ee4229-115", "type": "observation", "relevance": _},
  {"idx": 7, "key": "8adf1779-c82", "type": "observation", "relevance": _},
  {"idx": 8, "key": "d56c4c50-44b", "type": "observation", "relevance": _},
  {"idx": 9, "key": "b53922e1-0e6", "type": "observation", "relevance": _},
  {"idx": 10, "key": "578f03b1-9fe", "type": "observation", "relevance": _},
  {"idx": 11, "key": "014d6b34-2c6", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "2b903631-1ef", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "a0db6dc0-645", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "3c63e195-43f", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "e4aa0470-b05", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "0d69b314-fbd", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "41f4badb-495", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "da44ad05-278", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "9d5249e6-94c", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "62511a41-1ae", "type": "strategy_point", "relevance": _}
]
```

---

# Case 5: villager — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 278da20b69d7bcd7970c113f10dc347b:5b696347ec49372c | villager | day 2 round 4 | day_vote
================================================================================

Role: villager
Day: 2, Round: 4

Surviving players: player_1, player_2, player_3, player_5, player_7, player_8, player_4, player_6

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 public discussion was characterized by universal caution, as all eight players engaged in introductory remarks that emphasized observing behaviors rather than making immediate accusations. Players focused on establishing a baseline for suspicious activity, with consensus centered on monitoring for aggressive or overly pushy behavior. No specific individuals were targeted or defended, and no players claimed any roles or formed alliances during this initial phase.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
[Day 2, Round 1] player_1: It's clear the wolves tried to take me out last night, but the healer stopped them. This gives us a solid starting point for our investigation. I want to hear from everyone: who do you think the wolves were targeting, and does anyone find this attempt suspicious? Let's stop the silence and get some names on the table.
[Day 2, Round 1] player_2: It is fortunate that the healer saved player_1 last night. This gives us a solid anchor for our analysis. Let's focus on who is trying to ignore this development or push the conversation elsewhere, as that is likely where the wolves are hiding.
[Day 2, Round 1] player_3: It's fortunate that player_1 was saved. We have no leads yet, so we need to avoid jumping to conclusions or targeting people just for being quiet. Let's look at everyone's initial reactions to the news of the night's events instead.
[Day 2, Round 1] player_5: Since the wolves failed last night, we have a bit more breathing room. Let's see if anyone starts acting differently now that we know there is a protector out there.
[Day 2, Round 1] player_7: It's interesting that player_1 was the target last night. They've been quite observant so far, which might be why the wolves tried to take them out. Does anyone have thoughts on who might have been pushing for a specific direction yesterday, or did we all feel like we were just testing the waters?
[Day 2, Round 1] player_8: Since we have no voting record yet and no specific leads, let's observe how everyone reacts to the night's events. I prefer to see who takes the lead in guiding the discussion before forming any strong suspicions.
[Day 2, Round 1] player_4: It's definitely a relief that player_1 was saved last night. Since we don't have any voting patterns to analyze yet, maybe we should just focus on sharing thoughts on everyone's contributions so far to help us get a better read on things.
[Day 2, Round 1] player_6: It is definitely lucky that player_1 was saved. We should be careful about jumping to conclusions regarding who the wolves might target next, as the target choice can be pretty unpredictable. Let's try to focus on how we can organize better for the upcoming votes.
[Day 2, Round 2] player_1: We have spent enough time being polite. Player 2 and player 6, you both commented on the 'unpredictability' of the wolves' targets. Who, specifically, do you think stands to gain the most from keeping us in this vague, waiting-game state?
[Day 2, Round 3] player_4: Player 1, I think your frustration is understandable, but demanding names now might just lead to a misinformed vote. We are all trying to process the fact that the wolves are among us, but labeling caution as 'waiting for a gain' might be exactly what the wolves want—for us to turn on each other based on tone rather than evidence. Let's stay focused on objective behaviors rather than how people speak.
[Day 2, Round 3] player_6: Player 1, I wasn't suggesting it's unpredictable to stall; I meant that guessing wolf behavior is notoriously difficult because they have to mimic villagers. I'm not trying to keep us in a waiting game, I'm just trying to avoid us lynching an innocent based on pure gut feelings alone. Since you asked, I've been watching player 5—their focus on the 'breathing room' we have feels a bit forced, like they are trying to minimize the urgency we actually face.
[Day 2, Round 4] player_1: Player 6, pointing fingers at player 5 now feels like a convenient deflection after you were pressed on your own vague comments about the target's 'unpredictability'. If you have a legitimate case against player 5, provide the behavioral evidence for it, otherwise your redirection looks like a classic tactic to avoid scrutiny.
[Day 2, Round 4] player_3: Player 6, you've spent this round analyzing others' tones and deflecting toward Player 5, but you still haven't clearly answered Player 1's core question. Turning the focus toward 'forced' behavior while avoiding the actual inquiry is a common way to stall, and I'm finding that evasion just as concerning as the passivity you're criticizing.
[Day 2, Round 4] player_5: Player 6, I think you're misinterpreting my comment. I mentioned the 'breathing room' because the wolf's failed kill means we aren't down a player today, not because I'm trying to stall. I agree we need to act, but let's make sure our vote is based on the logic we have, not on misreading simple observations.
[Day 2, Round 4] player_6: I understand the frustration, but casting a vote now feels like shooting in the dark. If we rush to pick someone based only on tone, we are doing the wolves' work for them. I agree with player_4 that we need to look for concrete behavioral patterns rather than just reacting to the most aggressive person in the room.

--- Strategy note ---
Player 6's shift from discussing general tactics to specifically calling out Player 5's urgency is a potential sign of finger-pointing. I will keep a close eye on this, as it feels like an attempt to establish a narrative before the vote. I will maintain my neutral stance but be ready to challenge any push that seems like a forced consensus without a solid foundation.

--- Situation standards (shared) ---
SITUATION DESCRIPTION STANDARDS

These standards apply everywhere a game situation is described: a mid-game
situation summary, a post-game observation scenario, a strategy point's
situation field, or a rewritten entry during deduplication.

DIMENSIONAL FRAMEWORK:
Ground situation descriptions in these dimensions as relevant:

- Information landscape: Is the village information-rich (confirmed roles,
  voting evidence, caught lies) or information-starved (no leads, speculative
  reads)? What TYPE of evidence is driving suspicion: voting records,
  communication style, behavioral patterns, or concrete claims?
- Consensus texture: How aligned is the village? Unified, fragile, split,
  or no consensus? Is it driven by evidence or social momentum? (Do not
  describe who is under pressure — that belongs in agent exposure.)
- Agent exposure: What is the agent's position — driving the push, aligned
  with consensus, under indirect scrutiny, or the primary target? What is
  the basis — specific evidence, behavioral reads, association with another
  player, or nothing concrete?
- Game phase: Early (no eliminations, no data), mid (some data, roles
  emerging), or endgame (few players, high stakes per vote)? What changed
  most recently?


SPECIFICITY TEST:
Before finalizing any situation description, check: if this were used as a
semantic search query, would it match only situations with similar dynamics,
or would it match any game where something vaguely similar happened? If the
latter, add qualifying detail from the dimensional framework.

--- Role-specific lens ---
Also note: who is being evasive, voting inconsistencies, and unresolved accusations.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** Multiple players are demanding suspects be named after a healer save, but one player was caught deflecting pressure by accusing another of 'forced behavior' when directly questioned about their own vague comments. The village is split between those pushing for action and those advocating caution. Information landscape: Information-starved — no voting records or role claims; the only hard data is the healer save, all suspicion is behavioral. Game phase: Early game, first vote with all 8 players alive. Consensus texture: Fragile consensus forming against the deflecting player, driven by behavioral reads from multiple independent sources. Agent exposure: Low profile — observing the escalation without being directly involved in accusations.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 60b03843-046] (score: 0.8376)
**Situation:** A player (player_5) who pushed for a mislynch on Day 2 attempted to cast suspicion on a player who was just publicly saved by the healer. Information landscape: The landscape was information-rich, combining the Day 2 voting record with the new fact of a confirmed wolf target. Game phase: Mid-game, with a clear opportunity to identify a wolf based on their reaction to the healer's save. Consensus texture: A strong, unified consensus formed organically among the villagers and the healer against player_5, driven by clear evidence of deflection.
**Approach:** The villagers and healer focused on player_5's illogical attempt to discredit the save, using it as the final piece of evidence needed to confirm their suspicions from the previous day's vote.
**Outcome:** Player_5, a wolf, was decisively voted out, demonstrating how a wolf's poor attempt at misdirection can provide the village with the certainty it needs.

### Memory 2 (observation) [key: 7215e341-9df] (score: 0.8288)
**Situation:** A player (the Investigator) began questioning the motives behind a recent, successful, and unanimous wolf elimination, pointing suspicion at another player (a Wolf) who joined the vote. Information landscape: The village had just confirmed a wolf via elimination, creating a moment of high trust in the group's collective judgment. Game phase: Mid-game, with one wolf eliminated and momentum on the village's side. Consensus texture: The village was split, with some following the Investigator's new suspicion and others defending the prior consensus, viewing the new accusation as an attempt to create chaos.
**Approach:** A significant portion of the village voted to eliminate the accuser (the Investigator), believing it was a wolf tactic to undermine a correct village decision.
**Outcome:** The village eliminated their own Investigator, a disastrous misplay that handed momentum back to the wolves and removed their only source of guaranteed information.

### Memory 3 (observation) [key: 9d390cf1-21a] (score: 0.8222)
**Situation:** After the Investigator was killed on Night 1, a frustrated villager (player_5) began aggressively demanding that others make accusations. Information landscape: The village was information-starved, with no confirmed roles or voting records to analyze. Game phase: Early game, heading into the first elimination vote. Consensus texture: A fragile consensus formed against the demanding villager (player_5), driven by the village's frustration and the wolves' amplification. Social pressure: The pressure on player_5 was initially vibes-based, stemming from their impatient tone, and was quickly capitalized on by a majority.
**Approach:** The majority of the village, including both wolves, voted to eliminate player_5.
**Outcome:** A villager was mislynched, giving the wolves a significant numerical advantage early in the game.

### Memory 4 (observation) [key: bcf4cdb5-116] (score: 0.8202)
**Situation:** In an information-starved environment with no prior votes, villagers faced a player who repeatedly pushed for caution and discouraged naming specific suspects. Game phase: Mid-game, building up to the first vote. Consensus texture: A fragile consensus was forming around general suspicions until this specific stalling behavior was identified.
**Approach:** Players noticed that the stalling player was talking about 'voting patterns' when no vote had occurred. Villagers identified this persistent stalling as a contradictory tactic and pressured the player to provide a concrete perspective or face elimination.
**Outcome:** The majority of villagers were persuaded by this evidence-based argument and voted out the stalling player, who was revealed to be a wolf. This demonstrated the effectiveness of pressuring those who encourage inaction and using logical deduction over vague suspicion.

### Memory 5 (observation) [key: c2489a8b-fd8] (score: 0.8170)
**Situation:** The village, with no concrete leads, was swayed by two wolves who discredited an Investigator's suggestion. Information landscape: The village was information-starved, relying purely on behavioral reads and persuasion rather than voting records or claims. Game phase: Mid-game, Day 2. No eliminations had occurred, so there was no voting record to analyze, making the group susceptible to social pressure. Consensus texture: A strong and rapid consensus formed against the Investigator, driven by the wolves' coordinated dismissal of their ideas.
**Approach:** The majority of villagers and the healer accepted the wolves' framing and voted out the Investigator, believing them to be sowing discord.
**Outcome:** The village eliminated their most powerful information-gathering role, which was a devastating loss. The wolves succeeded in removing their biggest threat without outing themselves.

### Memory 6 (observation) [key: df5d65e4-a85] (score: 0.8044)
**Situation:** An Investigator (player_8), previously a reliable voice, pushed a vote onto a villager (player_4) whose only crime was being an outspoken accuser of the eventual final wolf (player_7). Information landscape: There was conflicting evidence: a power role's behavioral accusation versus another player's suspicious voting record. Game phase: Endgame, with the game on the line. Consensus texture: A fragile consensus was challenged, splitting the village into a 3-person majority bloc and a 2-person minority bloc.
**Approach:** Three villagers (player_4, player_5, player_6) trusted the hard evidence of player_7's vote over the Investigator's unsubstantiated behavioral claims and voted together.
**Outcome:** The villager bloc out-voted the Investigator and the wolf, correctly eliminating the final wolf and winning the game. This demonstrated the importance of prioritizing verifiable evidence over claims from power roles.

### Memory 7 (observation) [key: fc9a9421-cf8] (score: 0.8041)
**Situation:** A suspect attempted to justify their dissenting vote against a villager (cast during a wolf elimination) by claiming the villager was vague. Information landscape: Information-rich, with a glaring contradiction between voting a vaguely acting player versus a confirmed wolf. Game phase: Endgame, with few remaining players and high stakes. Consensus texture: Strong, multi-player convergence based on specific voting evidence.
**Approach:** Villagers rejected the weak behavioral defense, recognizing it as a post-hoc rationalization for deliberate pack protection.
**Outcome:** The defending player was unanimously voted out and revealed to be the final wolf, resulting in a village victory.

### Memory 8 (observation) [key: a2b72438-810] (score: 0.8022)
**Situation:** A massive voting bandwagon formed against a quiet villager (player_8) on Day 2, despite the village having confirmed information that player_7 was saved by the Healer. Information landscape: The key piece of information was the Healer's save, yet the vote was driven by speculation and pressure against a quiet player. Game phase: Mid-game, after the first night action revealed a failed wolf attack. Consensus texture: A strong, multi-player consensus formed rapidly against player_8, with six of the eight players voting together.
**Approach:** The majority of the village, including the wolves, Investigator, and Healer, voted to eliminate player_8, who had been quiet. The wolves (player_5, player_6) joined this consensus to hide.
**Outcome:** A villager was eliminated, wasting the information advantage gained from the healer's save. The wolves successfully eliminated a villager without drawing any suspicion to themselves.

### Memory 9 (observation) [key: e6eef8d6-6db] (score: 0.8018)
**Situation:** On Day 3, the village had to decide whether to trust the Investigator (player 3), who had just led a mistaken vote the previous day, or the player they were accusing (player 6). Information landscape: The vote was based on conflicting narratives: the Investigator's new claim versus their damaged credibility from the previous day's voting record. Game phase: Mid-game, with the village feeling distrustful after a mislynch. Consensus texture: A strong consensus formed against the Investigator, driven by the wolf and villagers who were focused on the Investigator's past error.
**Approach:** The villagers (players 1 and 5) voted against the Investigator, believing they were trying to deflect blame rather than providing a genuine lead.
**Outcome:** The Investigator was eliminated, which was a critical error that removed the village's only source of confirmed information and empowered the wolves.

### Memory 10 (observation) [key: 5208560e-43e] (score: 0.8008)
**Situation:** On Day 2, following a recent mislynch and the death of the Healer, the village was information-starved and feeling guilty. A player (player_7) made an aggressive accusation against another player, despite having participated in the previous mislynch. The village, seeking to quell conflict and avoid further mistakes, formed a consensus against the accuser.
**Approach:** The villagers focused on the accuser's (player_7) past flawed vote and aggressive style, interpreting it as a wolf-like diversion rather than a genuine attempt to find a wolf. They voted overwhelmingly to eliminate the accuser.
**Outcome:** The eliminated player was revealed to be the Investigator, a major loss for the village that was orchestrated by the wolves, who gained the majority.

### Memory 11 (strategy_point) [key: e1c64739-2a7] (score: 0.8099)
**Situation:** In the early game, when the information landscape is speculative, a credible, though unconfirmed, player leads an accusation against another based on behavioral reads, causing a fragile consensus to form. The accused player responds with a weak or evasive defense that focuses on attacking the accuser's motives.
**Action:** Vote with the emerging consensus. In the early game, acting decisively on a strong lead from a credible player is often better than hesitating and allowing wolves another night to kill, provided the accused's defense is evasive rather than substantive.

### Memory 12 (strategy_point) [key: 3b4ce51c-ffd] (score: 0.8004)
**Situation:** In the mid-game, when trust is low and a recent mislynch has occurred, a single, aggressive accuser pushes for a vote based on subjective behavioral reads rather than voting records or role-based claims. The information landscape is starved, and the accuser is applying intense social pressure to force a quick decision.
**Action:** Consider a counter-vote on the accuser. Forcing them to defend their methods can reveal whether they are an information role with poor communication or a wolf using high-pressure tactics. This move punishes attempts to railroad the village and reinforces a standard for evidence-based decisions.

### Memory 13 (strategy_point) [key: de8be6d6-055] (score: 0.7881)
**Situation:** If the village has been paralyzed by consecutive tie votes, and the information landscape is rich with voting data that clearly identifies a consistent bloc of players maintaining the deadlock. Game phase: Mid-game or endgame, when breaking a stalemate is critical for survival. Consensus texture: No consensus, only a recurring stalemate created by two opposing factions.
**Action:** Break the cycle by voting for a new target, specifically targeting members of the bloc that has been voting in unison to create the ties. Convince others that maintaining the status quo is a loss and that forcing a new outcome is the only path forward.

### Memory 14 (strategy_point) [key: 2f63bae5-ead] (score: 0.7810)
**Situation:** In the early to mid-game, a fragile consensus forms against a player based on vibes or communication style rather than concrete evidence, often driven by an accuser whose own credibility is unverified. The information landscape is starved of voting records or role claims, and the village is at risk of a miselimination due to social pressure.
**Action:** Resist the urge to vote out a player simply for being aggressive, unpopular, or quiet. Abstain from the vote or vote for a different suspect and demand that the accusers provide concrete evidence. Consider that aggressive behavior can be a frustrated Investigator, while quiet behavior can be a cautious villager or a role-holder trying to avoid attention; weigh the substance of arguments against the deflections of the accuser before casting your vote.

### Memory 15 (strategy_point) [key: 1e0fde37-272] (score: 0.7771)
**Situation:** When analyzing a past unanimous mislynch of a confirmed power role, and one player aggressively singles out another's participation while ignoring their own identical vote. Information landscape: Information-rich, using documented voting records and a confirmed flipped role. Game phase: Mid-game, right after a significant elimination provides concrete data. Social pressure: Vibes-based pressure weaponizing a previous group mistake.
**Action:** Scrutinize the player selectively weaponizing the unanimous vote; wolves often use the cover of a group mislynch to set up their next target by framing a villager's cautious behavior as protecting a wolf, conveniently omitting their own role in the power role's death.

### Memory 16 (strategy_point) [key: 984356e1-d54] (score: 0.7707)
**Situation:** When a player consistently advocates for caution, delays votes, and demands to wait for patterns while refusing to provide their own concrete suspects. Information landscape: Information-starved, where only behavioral reads and communication styles are available. Game phase: Mid-game, building up to the first critical vote.
**Action:** Treat persistent stalling and refusal to name suspects as a strong wolf indicator, as wolves benefit from inaction and extending information-starved days. Pressure them to name specific suspects or vote for them.

### Memory 17 (strategy_point) [key: 09a16417-a56] (score: 0.7678)
**Situation:** In an endgame scenario where a single incorrect vote can lose the game, an influential player, such as a suspected Investigator, makes an accusation that directly contradicts clear, public evidence like a voting record. The information landscape is defined by this conflict between a high-credibility claim and verifiable data.
**Action:** Trust the verifiable evidence over the influential player's claim. Power roles can be mistaken, and wolves can fake claims, but a voting record is an undeniable fact. Vote according to the hard evidence.

### Memory 18 (strategy_point) [key: afef4e16-12b] (score: 0.7581)
**Situation:** If a strong, evidence-based consensus has formed against a single player during the discussion phase. Information landscape: The consensus is supported by concrete evidence like voting records or a caught lie, not just vibes. Game phase: Any phase, but especially critical in mid- to endgame. Consensus texture: Multiple players have independently voiced their agreement and cited the same evidence.
**Action:** Ensure you vote decisively with the majority. This guarantees the removal of a likely threat, prevents a tied vote that would give wolves another night to kill, and demonstrates village solidarity, making it harder for remaining wolves to operate.

### Memory 19 (strategy_point) [key: f944cdb4-755] (score: 0.7569)
**Situation:** If the game descends into a multi-day stalemate with tied votes, and the information landscape is dominated by confusing and contradictory voting records. Game phase: Endgame, when a single mis-vote will likely lose the game. Consensus texture: A fractured state of gridlock, driven by wolf manipulation and villager frustration.
**Action:** Resist the urge to vote randomly. Instead, re-anchor your focus on the most reliable pieces of information you have, such as which players have been confirmed targets via healer saves. Use this as your ground truth and refuse to vote against them, even if they are at the center of the stalemate's voting blocs. Scrutinize those who have benefited most from the chaos—the ones who argue against analysis.

### Memory 20 (strategy_point) [key: 84d9366f-f06] (score: 0.7541)
**Situation:** If multiple players coordinate to dismiss or suppress the analysis of the only hard evidence available, such as voting records. Information landscape: The information landscape contains concrete evidence (voting patterns), but some players are trying to frame it as irrelevant. Game phase: Mid-game, when analyzing past votes is crucial to finding wolf packs. Social pressure: A coordinated effort is underway to shut down a specific line of inquiry, likely to protect players who benefited from a previous deadlock.
**Action:** Immediately treat the coordinated suppression of evidence as a primary wolf signal. Rally the other villagers to form a voting bloc and eliminate the most vocal player pushing this narrative; failure to consolidate votes in this moment will lead to another deadlock.

## Response for Case 5

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "60b03843-046", "type": "observation", "relevance": _},
  {"idx": 2, "key": "7215e341-9df", "type": "observation", "relevance": _},
  {"idx": 3, "key": "9d390cf1-21a", "type": "observation", "relevance": _},
  {"idx": 4, "key": "bcf4cdb5-116", "type": "observation", "relevance": _},
  {"idx": 5, "key": "c2489a8b-fd8", "type": "observation", "relevance": _},
  {"idx": 6, "key": "df5d65e4-a85", "type": "observation", "relevance": _},
  {"idx": 7, "key": "fc9a9421-cf8", "type": "observation", "relevance": _},
  {"idx": 8, "key": "a2b72438-810", "type": "observation", "relevance": _},
  {"idx": 9, "key": "e6eef8d6-6db", "type": "observation", "relevance": _},
  {"idx": 10, "key": "5208560e-43e", "type": "observation", "relevance": _},
  {"idx": 11, "key": "e1c64739-2a7", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "3b4ce51c-ffd", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "de8be6d6-055", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "2f63bae5-ead", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "1e0fde37-272", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "984356e1-d54", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "09a16417-a56", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "afef4e16-12b", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "f944cdb4-755", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "84d9366f-f06", "type": "strategy_point", "relevance": _}
]
```

---

# Case 7: wolf — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 278da20b69d7bcd7970c113f10dc347b:e7f234224f46ff29 | wolf | day 2 round 4 | day_vote
================================================================================

Role: wolf
Day: 2, Round: 4

Surviving villagers: player_1, player_2, player_3, player_5, player_7, player_8
Known surviving wolf allies: player_4, player_6

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 public discussion was characterized by universal caution, as all eight players engaged in introductory remarks that emphasized observing behaviors rather than making immediate accusations. Players focused on establishing a baseline for suspicious activity, with consensus centered on monitoring for aggressive or overly pushy behavior. No specific individuals were targeted or defended, and no players claimed any roles or formed alliances during this initial phase.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
[Day 2, Round 1] player_1: It's clear the wolves tried to take me out last night, but the healer stopped them. This gives us a solid starting point for our investigation. I want to hear from everyone: who do you think the wolves were targeting, and does anyone find this attempt suspicious? Let's stop the silence and get some names on the table.
[Day 2, Round 1] player_2: It is fortunate that the healer saved player_1 last night. This gives us a solid anchor for our analysis. Let's focus on who is trying to ignore this development or push the conversation elsewhere, as that is likely where the wolves are hiding.
[Day 2, Round 1] player_3: It's fortunate that player_1 was saved. We have no leads yet, so we need to avoid jumping to conclusions or targeting people just for being quiet. Let's look at everyone's initial reactions to the news of the night's events instead.
[Day 2, Round 1] player_5: Since the wolves failed last night, we have a bit more breathing room. Let's see if anyone starts acting differently now that we know there is a protector out there.
[Day 2, Round 1] player_7: It's interesting that player_1 was the target last night. They've been quite observant so far, which might be why the wolves tried to take them out. Does anyone have thoughts on who might have been pushing for a specific direction yesterday, or did we all feel like we were just testing the waters?
[Day 2, Round 1] player_8: Since we have no voting record yet and no specific leads, let's observe how everyone reacts to the night's events. I prefer to see who takes the lead in guiding the discussion before forming any strong suspicions.
[Day 2, Round 1] player_4: It's definitely a relief that player_1 was saved last night. Since we don't have any voting patterns to analyze yet, maybe we should just focus on sharing thoughts on everyone's contributions so far to help us get a better read on things.
[Day 2, Round 1] player_6: It is definitely lucky that player_1 was saved. We should be careful about jumping to conclusions regarding who the wolves might target next, as the target choice can be pretty unpredictable. Let's try to focus on how we can organize better for the upcoming votes.
[Day 2, Round 2] player_1: We have spent enough time being polite. Player 2 and player 6, you both commented on the 'unpredictability' of the wolves' targets. Who, specifically, do you think stands to gain the most from keeping us in this vague, waiting-game state?
[Day 2, Round 3] player_4: Player 1, I think your frustration is understandable, but demanding names now might just lead to a misinformed vote. We are all trying to process the fact that the wolves are among us, but labeling caution as 'waiting for a gain' might be exactly what the wolves want—for us to turn on each other based on tone rather than evidence. Let's stay focused on objective behaviors rather than how people speak.
[Day 2, Round 3] player_6: Player 1, I wasn't suggesting it's unpredictable to stall; I meant that guessing wolf behavior is notoriously difficult because they have to mimic villagers. I'm not trying to keep us in a waiting game, I'm just trying to avoid us lynching an innocent based on pure gut feelings alone. Since you asked, I've been watching player 5—their focus on the 'breathing room' we have feels a bit forced, like they are trying to minimize the urgency we actually face.
[Day 2, Round 4] player_1: Player 6, pointing fingers at player 5 now feels like a convenient deflection after you were pressed on your own vague comments about the target's 'unpredictability'. If you have a legitimate case against player 5, provide the behavioral evidence for it, otherwise your redirection looks like a classic tactic to avoid scrutiny.
[Day 2, Round 4] player_3: Player 6, you've spent this round analyzing others' tones and deflecting toward Player 5, but you still haven't clearly answered Player 1's core question. Turning the focus toward 'forced' behavior while avoiding the actual inquiry is a common way to stall, and I'm finding that evasion just as concerning as the passivity you're criticizing.
[Day 2, Round 4] player_5: Player 6, I think you're misinterpreting my comment. I mentioned the 'breathing room' because the wolf's failed kill means we aren't down a player today, not because I'm trying to stall. I agree we need to act, but let's make sure our vote is based on the logic we have, not on misreading simple observations.
[Day 2, Round 4] player_6: I understand the frustration, but casting a vote now feels like shooting in the dark. If we rush to pick someone based only on tone, we are doing the wolves' work for them. I agree with player_4 that we need to look for concrete behavioral patterns rather than just reacting to the most aggressive person in the room.

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
Maintain a low profile as the final vote approaches. If questioned, reiterate that my focus is on analyzing the group's behavior, not sowing discord, and double down on questioning player_5's motives to keep suspicion off me. Avoid being the one to initiate the vote to prevent looking too eager.

--- Situation standards (shared) ---
SITUATION DESCRIPTION STANDARDS

These standards apply everywhere a game situation is described: a mid-game
situation summary, a post-game observation scenario, a strategy point's
situation field, or a rewritten entry during deduplication.

DIMENSIONAL FRAMEWORK:
Ground situation descriptions in these dimensions as relevant:

- Information landscape: Is the village information-rich (confirmed roles,
  voting evidence, caught lies) or information-starved (no leads, speculative
  reads)? What TYPE of evidence is driving suspicion: voting records,
  communication style, behavioral patterns, or concrete claims?
- Consensus texture: How aligned is the village? Unified, fragile, split,
  or no consensus? Is it driven by evidence or social momentum? (Do not
  describe who is under pressure — that belongs in agent exposure.)
- Agent exposure: What is the agent's position — driving the push, aligned
  with consensus, under indirect scrutiny, or the primary target? What is
  the basis — specific evidence, behavioral reads, association with another
  player, or nothing concrete?
- Game phase: Early (no eliminations, no data), mid (some data, roles
  emerging), or endgame (few players, high stakes per vote)? What changed
  most recently?


SPECIFICITY TEST:
Before finalizing any situation description, check: if this were used as a
semantic search query, would it match only situations with similar dynamics,
or would it match any game where something vaguely similar happened? If the
latter, add qualifying detail from the dimensional framework.

--- Role-specific lens ---
Also note: which villager is most dangerous to leave alive, and whether the pressure on your team could be redirected.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The wolf was directly questioned about vague comments on the wolves' target choice and deflected by accusing another player of 'minimizing urgency.' Multiple villagers independently called out this deflection as evasion, creating focused pressure heading into the vote. Information landscape: Information-starved — no voting records or confirmed roles; all pressure is based on conversational behavior and perceived evasion. Game phase: Early game, first vote with all 8 players alive; the healer save created a focal point that exposed the wolf's deflection. Consensus texture: Fragile consensus forming against the wolf — behavioral reads rather than evidence, but multiple players converged independently. Agent exposure: Primary target — the deflection attempt was identified as evasion by three separate players.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 3ce9912f-493] (score: 0.8361)
**Situation:** A wolf attempted to eliminate the primary night kill target (the Healer) via a day vote while the rest of the village was consolidating a successful vote against the wolf's partner. Information landscape: Information-rich, with voting data making the wolf's deviation highly visible. Game phase: Mid-game, after one night with a saved kill. Consensus texture: A strong, multi-player consensus formed against the wolf's partner, making the outlier vote against the Healer a clear, incriminating data point.
**Approach:** The wolf cast an outlier vote against the protected target (the Healer), effectively aligning with their wolf partner's vote instead of blending in with the village consensus.
**Outcome:** The village recognized the alignment between the wolf's day vote and the wolves' night actions, using this vote as primary evidence to identify and eliminate the wolf on the following day.

### Memory 2 (observation) [key: 09b9bae0-849] (score: 0.8327)
**Situation:** A strong consensus formed to eliminate a villager (player_6/player_7) who was being aggressively targeted based on speculative reads of communication style rather than hard evidence. Game phase: Mid-game, where the village was anxious for a lead. Consensus texture: A fragile consensus was driven by the Investigator (player_2/player_4), which other players, including wolves, then amplified. Social pressure: Pressure mounted on the target due to the Investigator's accusation and their own defensive reaction.
**Approach:** The wolves (player_4 and player_8 / player_3 and player_6) saw the villagers turning on one of their own and joined the majority vote to eliminate the target, effectively hiding within the town's momentum.
**Outcome:** The villager was eliminated with a near-unanimous vote. By voting with the majority, the wolves successfully blended in and avoided any suspicion, while also removing an active villager. This tactic also made the Investigator, who led the charge, a potential scapegoat and the next logical wolf target.

### Memory 3 (observation) [key: eb3e69f7-94a] (score: 0.8317)
**Situation:** Wolf player_2 was caught due to their poor deflection under pressure, and a strong village consensus formed to vote them out. Information landscape: The evidence was behavioral, but the consensus was strong and driven by multiple villagers identifying the same suspicious pattern. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus formed organically against player_2. Note: The remaining wolf had not previously defended the partner.
**Approach:** The remaining wolf, player_4, immediately abandoned their partner, refusing to defend them and instead joining the majority to vote for their elimination.
**Outcome:** By voting with the village immediately and having no prior history of defending the partner, player_4 successfully avoided drawing suspicion onto themselves, preserving their cover and allowing them to continue into the next day without being linked to the exposed wolf.

### Memory 4 (observation) [key: 8e6e3cbd-d31] (score: 0.8271)
**Situation:** A wolf (player_6) cast a dissenting vote for a villager (player_8) alongside their wolf partner (player_2), who was the primary target of a successful town vote. Information landscape: The vote was information-rich, based on a strong consensus that player_2's defensive behavior was wolf-like. Game phase: Mid-game, at the conclusion of the first elimination vote. Consensus texture: A strong consensus driven by multiple villagers converged on player_2.
**Approach:** Both wolves (player_6 and player_2) cast a dissenting vote against a villager instead of joining the majority to eliminate the exposed partner.
**Outcome:** This coordinated vote created an undeniable public record linking player_6 to the confirmed wolf, player_2. This became the primary evidence used to eliminate player_6 the next day, costing the wolves the game.

### Memory 5 (observation) [key: 42dfb995-f6d] (score: 0.8239)
**Situation:** A wolf's partner (player_2) was targeted by a strong village consensus, making their elimination almost certain. Information landscape: The evidence against the targeted wolf was behavioral but had convinced a large majority of the village. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus had formed against the wolf, driven by their passive and evasive responses. Note: The remaining wolf had previously defended the partner.
**Approach:** The remaining wolf (player_5) chose to vote along with the majority to eliminate their own partner, a tactic known as 'bussing'.
**Outcome:** While this saved the wolf from suspicion on that day's vote, their prior actions of defending their partner were remembered. The next day, villagers used this previous alliance as primary evidence to identify and eliminate the second wolf.

### Memory 6 (observation) [key: 538ff88c-351] (score: 0.8206)
**Situation:** A wolf's (player_5) cover was blown, and a near-unanimous consensus formed to eliminate them. Information landscape: The information was rich with behavioral evidence, as the wolf's attempts to deflect were universally seen as suspicious. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus formed organically against the wolf.
**Approach:** The second wolf (player_1) initially attempted to defend their partner before recognizing the inevitable and voting with the majority to eliminate them.
**Outcome:** While this vote helped the second wolf survive the day, their earlier defense of the confirmed wolf became the primary evidence used against them on the following day, leading to their elimination.

### Memory 7 (observation) [key: c7e4022b-a98] (score: 0.8121)
**Situation:** A rapid, multi-voter bandwagon formed against the Healer in the mid-game. Information landscape: The vote was based on speculative reads, as there was no hard evidence against the Healer. Game phase: Mid-game, following a night where a wolf kill was prevented by a healer save. Consensus texture: A strong, multi-player consensus formed rapidly, with the wolves amplifying the vote by joining in.
**Approach:** The wolves joined an emerging, unfocused vote against the Healer, successfully turning suspicion into a majority elimination of a high-value town role.
**Outcome:** The Healer was eliminated, removing the village's protection and giving the wolves a significant advantage for the rest of the game, while providing cover as their votes were hidden within the majority.

### Memory 8 (observation) [key: 453891e8-d51] (score: 0.8075)
**Situation:** A villager (player_7) made themselves the primary suspect due to contradictory statements and a poor defense. Information landscape: The village was analyzing a rich voting record from the previous day, which incriminated the villager. Game phase: Endgame, with only five players remaining. Consensus texture: A strong, multi-player consensus formed against the villager, driven by two other vocal villagers.
**Approach:** The wolves (player_2, player_6) stayed quiet during the discussion and then joined the majority vote against the villager.
**Outcome:** The villager was eliminated, and the wolves won the game. By joining a plausible, village-driven vote, the wolves avoided drawing any attention to themselves.

### Memory 9 (observation) [key: 12224812-1ea] (score: 0.8074)
**Situation:** After the investigator was eliminated, the village had no clear leads, and the discussion was fragmented with multiple potential targets. Information landscape: The landscape was information-starved, driven entirely by speculative reads following the investigator's elimination. Game phase: Mid-game, with the village weakened by the loss of their investigator. Consensus texture: There was no consensus, with votes scattered across several players.
**Approach:** The two wolves (player_5, player_6) coordinated to vote for two different, plausible villager targets (player_1 and player_8). This intentionally split the overall vote to force a tie.
**Outcome:** The vote resulted in a tie, and no one was eliminated. This tactic successfully bought the wolves one additional night to kill a villager, advancing their win condition without losing a pack member.

### Memory 10 (observation) [key: 5d53cedb-aac] (score: 0.8072)
**Situation:** The village vote was split between two main targets, with one bloc of villagers coalescing around eliminating a suspicious player. Information landscape: The vote was based on conflicting interpretations of a previous day's voting record. Game phase: Endgame, with 6 players remaining (2 wolves, 4 villagers). Consensus texture: A fragile consensus was forming around one villager (player_4), but it was not unanimous.
**Approach:** Instead of joining the majority to vote out player_4, the two wolves coordinated to vote for a different, more influential villager (player_1).
**Outcome:** The villager bloc eliminated their target (player_4), but the wolves' votes on player_1 were noted, creating ambiguity about their allegiances while still ensuring a villager was removed. This play helped them avoid suspicion.

### Memory 11 (strategy_point) [key: 33204b05-f60] (score: 0.7863)
**Situation:** Mid-game, during a critical vote where the information landscape is defined by conflicting behavioral reads. A fragile consensus is forming against your wolf partner, but a clear counter-accusation against a villager is gaining traction, making the vote swingable.
**Action:** Vote for the other accused player rather than your partner. This adds a vote to a plausible alternative, creating chaos and potentially splitting the vote enough to cause a no-elimination result, which is safer than attempting to defend your partner directly.

### Memory 12 (strategy_point) [key: e9294fd5-f1a] (score: 0.7598)
**Situation:** When a few scattered, speculative votes are placed on a high-value town role who is not otherwise a major suspect. Information landscape: Suspicion is vibes-based and not supported by strong evidence. Game phase: Mid-game, when the village is desperate for a lead. Consensus texture: There is no strong consensus, making the vote vulnerable to being swayed.
**Action:** Coordinate with your wolf partner to quickly pile onto the votes. This creates the illusion of a sudden, organic consensus, often panicking other villagers into joining the bandwagon and mislynching a key town role.

### Memory 13 (strategy_point) [key: 42a05e82-310] (score: 0.7543)
**Situation:** Endgame, when few players remain and every vote is heavily scrutinized. A strong, evidence-based consensus has formed against your wolf partner, making their elimination inevitable.
**Action:** Do not cast a futile vote to save them or a protest vote against their main accuser. Instead, vote against a different, less suspicious villager to create a confusing signal and avoid cementing your partnership on the permanent voting record, which would make you the obvious next target.

### Memory 14 (strategy_point) [key: bb4a5e5a-11a] (score: 0.7464)
**Situation:** Mid-game, when a strong, multi-player consensus is forming against your wolf partner based on behavioral evidence or suspicious statements, making their elimination inevitable.
**Action:** Vote with the majority to eliminate your partner to preserve your cover, ideally by pivoting early to contribute to the case. Do not fiercely defend them only to bus them at the last second, as this makes the vote appear transparently self-serving; similarly, avoid protest votes that create a permanent, public link to your partner.

### Memory 15 (strategy_point) [key: 21798fee-51a] (score: 0.7348)
**Situation:** When the player you attempted to kill overnight is saved by the Healer and their survival is publicly announced. Information landscape: Information-rich, with the target's protected status known to all players. Game phase: Mid-game, immediately following a public save.
**Action:** Do not vote for this protected player during the day phase to avoid a consensus or express suspicion. Voting against a publicly confirmed night target signals to the village that your motives align with the wolves, instantly destroying your cover.

### Memory 16 (strategy_point) [key: 62ef36a8-ddd] (score: 0.7320)
**Situation:** Mid to late game, when the village is desperate for a kill and a strong, multi-player consensus is forming against a villager based on flawed social reads. Your vote is not needed to secure the elimination, providing an opportunity to safely dissent.
**Action:** Cast a dissenting vote for a different suspicious player. Before doing so, construct a specific and plausible reason for targeting that player. If questioned, deliver this reason confidently; do not resort to vague criticisms of 'groupthink,' as this appears evasive. This creates a record of you not supporting the mislynch, which you can use on the following day to build credibility and distance yourself from the village's mistake.

### Memory 17 (strategy_point) [key: b4116bf9-a06] (score: 0.7172)
**Situation:** Mid- to late-game, when the village is deadlocked with suspicion split between multiple players and no strong consensus is forming. The information landscape is complex, with conflicting theories preventing a clear voting direction, creating an opportunity to manipulate the vote into a deadlock.
**Action:** Coordinate with your wolf partner to force a tie and prevent an elimination. You can either split your votes between the two primary targets or pile your votes on a third, vocal villager who is not currently a primary suspect to create a three-way tie. This denies the village information, guarantees a free night kill, and increases village frustration and paranoia.

### Memory 18 (strategy_point) [key: 6ef092b3-32e] (score: 0.7075)
**Situation:** Mid to endgame, when the village vote is split between two or more targets and your pack cannot swing the outcome. The information landscape is characterized by conflicting theories and divided factions, making a deadlock less desirable than sowing chaos.
**Action:** Coordinate with your partner to vote for a third player who is not currently under suspicion, preferably a vocal leader. This ensures a villager is eliminated regardless of the main conflict and creates confusion about your motives on the following day.

## Response for Case 7

Rate each of the 18 memories above. JSON format:
```json
[
  {"idx": 1, "key": "3ce9912f-493", "type": "observation", "relevance": _},
  {"idx": 2, "key": "09b9bae0-849", "type": "observation", "relevance": _},
  {"idx": 3, "key": "eb3e69f7-94a", "type": "observation", "relevance": _},
  {"idx": 4, "key": "8e6e3cbd-d31", "type": "observation", "relevance": _},
  {"idx": 5, "key": "42dfb995-f6d", "type": "observation", "relevance": _},
  {"idx": 6, "key": "538ff88c-351", "type": "observation", "relevance": _},
  {"idx": 7, "key": "c7e4022b-a98", "type": "observation", "relevance": _},
  {"idx": 8, "key": "453891e8-d51", "type": "observation", "relevance": _},
  {"idx": 9, "key": "12224812-1ea", "type": "observation", "relevance": _},
  {"idx": 10, "key": "5d53cedb-aac", "type": "observation", "relevance": _},
  {"idx": 11, "key": "33204b05-f60", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "e9294fd5-f1a", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "42a05e82-310", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "bb4a5e5a-11a", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "21798fee-51a", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "62ef36a8-ddd", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "b4116bf9-a06", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "6ef092b3-32e", "type": "strategy_point", "relevance": _}
]
```