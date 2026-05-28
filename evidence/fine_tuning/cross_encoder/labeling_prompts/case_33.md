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

# Case 33: villager — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:a74c4c64e0e9545b | villager | day 2 round 4 | day_vote
================================================================================

Role: villager
Day: 2, Round: 4

Surviving players: player_2, player_4, player_5, player_6, player_7, player_3, player_8

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 discussion remained neutral and cautious, with all players (player_1 through player_8) exchanging general pleasantries, emphasizing the need for caution, and expressing a shared reluctance to jump to conclusions or force a quick lynch without evidence.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
[Day 2, Round 1] player_2: It is unfortunate that we lost player_1. Given we have no information, I suggest we pay close attention to anyone who tries to steer the conversation too forcefully today.
[Day 2, Round 1] player_4: Since we lost a villager, we need to move past the initial hesitation. Does anyone have a specific observation about last night's events or a suspicion regarding who was quiet during Day 1?
[Day 2, Round 1] player_5: It's a tough start losing player_1. Since we didn't vote yesterday, we don't have much to go on yet. Let's not just sit around being polite; does anyone have a read on why the wolves might have picked them, or notice anything odd about how people are acting right now?
[Day 2, Round 1] player_6: It's unfortunate about player 1. Since they were a villager, we've lost a town member early on. Does anyone have any thoughts on why they might have been targeted, or did anyone notice anything suspicious during yesterday's round?
[Day 2, Round 1] player_7: Since we lost player_1, we really need to move past the general pleasantries. Everyone, let's name one person you find suspicious and why, even if it's just a gut feeling for now. We can't afford to be passive while the wolves chip away at us.
[Day 2, Round 1] player_3: It is unfortunate about player_1. Given we have so little information, we really need to be careful not to jump to conclusions and accidentally hit a villager.
[Day 2, Round 1] player_8: It is really unfortunate about player_1. Does anyone have any thoughts on how we should handle today given we have so little information to go on?
[Day 2, Round 2] player_8: I agree with player 3 that we should be careful. Pushing for a lynch right now without any real leads feels reckless and might just play into the wolves' hands by letting them manipulate the group into an easy mistake.
[Day 2, Round 3] player_5: Player 3 and 8, you're both advocating for caution, but in an information-starved game, 'wait and see' is exactly what the wolves want to hear. Doing nothing today just guarantees we lose another villager tonight. If you're truly looking for wolves, tell us who you're watching instead of just telling us to be quiet.
[Day 2, Round 4] player_5: Player 3 and 8, your constant calls for 'caution' are effectively shielding the wolves by ensuring we never take a vote. Since you refuse to provide any suspect, I am voting for player 3 as their insistence on inaction is the only concrete behavior we have to act on today.
[Day 2, Round 4] player_6: We are at an impasse, but voting for the sake of voting is risky. If we have no clear consensus, perhaps we should skip the vote again rather than risk eliminating another innocent villager. I am hesitant to lead a charge without more information.
[Day 2, Round 4] player_7: Player 3 and 8, by constantly pushing for caution and 'not jumping to conclusions,' you are effectively ensuring we hit no one today. If we don't vote, we lose another villager tonight. If you aren't wolves, give us one name you are actually tracking, or explain why you think staying silent is a winning strategy for the village.
[Day 2, Round 4] player_3: Player 5, being assertive is one thing, but demanding a target right now feels exactly like what a wolf wants—to create a forced, groundless lynch. Why the rush to eliminate someone before we have any actual, reliable information?
[Day 2, Round 4] player_8: Player 5, labeling the desire for caution as 'exactly what wolves want' is a convenient way to justify rushing us into a blind vote. If we pick the wrong person, we are just handing them the game. Why are you so adamant that we ignore the risks and vote today?

--- Strategy note ---
Player 3 and 8's persistent 'wait and see' attitude is stalling the game, which directly benefits the wolves. Since no new evidence has appeared, I will pivot to questioning the intent of those resisting the vote. I will watch to see if they continue to block a consensus, as that is a high-risk behavior for wolves in a small group.

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

**Situation 1:** Two players have persistently advocated extreme caution and refuse to name any suspects despite repeated demands from multiple villagers. The aggressive faction has declared votes against the most cautious player, but the cautious duo frames this as exactly what wolves want — a rushed, evidence-free elimination. Information landscape: Information-starved — no voting records or role claims; the behavioral split between proactive and cautious players is the only observable pattern. Game phase: Early game, first vote with 7 players; the village faces a binary choice between voting on behavioral reads or allowing another night kill. Consensus texture: Fragile — the aggressive faction has a slim numbers advantage but the cautious duo's argument that rushing helps wolves has some merit. Agent exposure: The agent has publicly challenged the cautious pair's refusal to name suspects, aligning with the aggressive faction.

## Retrieved Memories to Label

### Memory 1 (observation) [key: c2489a8b-fd8] (score: 0.8232)
**Situation:** The village, with no concrete leads, was swayed by two wolves who discredited an Investigator's suggestion. Information landscape: The village was information-starved, relying purely on behavioral reads and persuasion rather than voting records or claims. Game phase: Mid-game, Day 2. No eliminations had occurred, so there was no voting record to analyze, making the group susceptible to social pressure. Consensus texture: A strong and rapid consensus formed against the Investigator, driven by the wolves' coordinated dismissal of their ideas.
**Approach:** The majority of villagers and the healer accepted the wolves' framing and voted out the Investigator, believing them to be sowing discord.
**Outcome:** The village eliminated their most powerful information-gathering role, which was a devastating loss. The wolves succeeded in removing their biggest threat without outing themselves.

### Memory 2 (observation) [key: bcf4cdb5-116] (score: 0.8227)
**Situation:** In an information-starved environment with no prior votes, villagers faced a player who repeatedly pushed for caution and discouraged naming specific suspects. Game phase: Mid-game, building up to the first vote. Consensus texture: A fragile consensus was forming around general suspicions until this specific stalling behavior was identified.
**Approach:** Players noticed that the stalling player was talking about 'voting patterns' when no vote had occurred. Villagers identified this persistent stalling as a contradictory tactic and pressured the player to provide a concrete perspective or face elimination.
**Outcome:** The majority of villagers were persuaded by this evidence-based argument and voted out the stalling player, who was revealed to be a wolf. This demonstrated the effectiveness of pressuring those who encourage inaction and using logical deduction over vague suspicion.

### Memory 3 (observation) [key: 7215e341-9df] (score: 0.8161)
**Situation:** A player (the Investigator) began questioning the motives behind a recent, successful, and unanimous wolf elimination, pointing suspicion at another player (a Wolf) who joined the vote. Information landscape: The village had just confirmed a wolf via elimination, creating a moment of high trust in the group's collective judgment. Game phase: Mid-game, with one wolf eliminated and momentum on the village's side. Consensus texture: The village was split, with some following the Investigator's new suspicion and others defending the prior consensus, viewing the new accusation as an attempt to create chaos.
**Approach:** A significant portion of the village voted to eliminate the accuser (the Investigator), believing it was a wolf tactic to undermine a correct village decision.
**Outcome:** The village eliminated their own Investigator, a disastrous misplay that handed momentum back to the wolves and removed their only source of guaranteed information.

### Memory 4 (observation) [key: 9d390cf1-21a] (score: 0.8106)
**Situation:** After the Investigator was killed on Night 1, a frustrated villager (player_5) began aggressively demanding that others make accusations. Information landscape: The village was information-starved, with no confirmed roles or voting records to analyze. Game phase: Early game, heading into the first elimination vote. Consensus texture: A fragile consensus formed against the demanding villager (player_5), driven by the village's frustration and the wolves' amplification. Social pressure: The pressure on player_5 was initially vibes-based, stemming from their impatient tone, and was quickly capitalized on by a majority.
**Approach:** The majority of the village, including both wolves, voted to eliminate player_5.
**Outcome:** A villager was mislynched, giving the wolves a significant numerical advantage early in the game.

### Memory 5 (observation) [key: fc9a9421-cf8] (score: 0.7979)
**Situation:** A suspect attempted to justify their dissenting vote against a villager (cast during a wolf elimination) by claiming the villager was vague. Information landscape: Information-rich, with a glaring contradiction between voting a vaguely acting player versus a confirmed wolf. Game phase: Endgame, with few remaining players and high stakes. Consensus texture: Strong, multi-player convergence based on specific voting evidence.
**Approach:** Villagers rejected the weak behavioral defense, recognizing it as a post-hoc rationalization for deliberate pack protection.
**Outcome:** The defending player was unanimously voted out and revealed to be the final wolf, resulting in a village victory.

### Memory 6 (observation) [key: 300150ed-4b6] (score: 0.7977)
**Situation:** The village developed tunnel vision around a perceived voting anomaly from the Investigator (player_8) on Day 2. Information landscape: Information was rich regarding voting records, but the village overweighted one piece of data while ignoring the substance of the Investigator's counter-accusations. Game phase: Mid-game, with the game evenly poised after one wolf elimination. Consensus texture: A strong consensus driven by multiple vocal villagers formed against the Investigator, with the remaining wolf amplifying their arguments.
**Approach:** The villagers repeatedly demanded an explanation for the vote and interpreted the Investigator's attempts to accuse the real wolf (player_4) as simple deflection.
**Outcome:** The village mislynched their Investigator, a critical error that cost them their primary source of information and nearly lost them the game.

### Memory 7 (observation) [key: e6eef8d6-6db] (score: 0.7942)
**Situation:** On Day 3, the village had to decide whether to trust the Investigator (player 3), who had just led a mistaken vote the previous day, or the player they were accusing (player 6). Information landscape: The vote was based on conflicting narratives: the Investigator's new claim versus their damaged credibility from the previous day's voting record. Game phase: Mid-game, with the village feeling distrustful after a mislynch. Consensus texture: A strong consensus formed against the Investigator, driven by the wolf and villagers who were focused on the Investigator's past error.
**Approach:** The villagers (players 1 and 5) voted against the Investigator, believing they were trying to deflect blame rather than providing a genuine lead.
**Outcome:** The Investigator was eliminated, which was a critical error that removed the village's only source of confirmed information and empowered the wolves.

### Memory 8 (observation) [key: f88a85ae-1ee] (score: 0.7913)
**Situation:** Villagers correctly identified that the two wolves (player_6 and player_7) were coordinating to dismiss analysis of the Day 2 voting records. Information landscape: The information landscape was becoming richer, with a tie vote from Day 2 as the primary evidence. Game phase: Mid-game, with the village deadlocked after a failed vote. Consensus texture: A fragile consensus was forming against the wolves, driven by several villagers who noticed the coordinated dismissal of evidence.
**Approach:** Despite having a strong lead, the villagers failed to consolidate their votes. Three separate players voted for a wolf (player_6), but three others voted for an aggressive villager (player_4), splitting the vote.
**Outcome:** The vote tied for a second consecutive day, resulting in no elimination and allowing the wolves to kill another key villager (player_2) at night.

### Memory 9 (observation) [key: 53e65a70-5d0] (score: 0.7896)
**Situation:** On Day 2, despite a lack of hard evidence, a strong majority of villagers independently voted for player_8. Information landscape: The landscape was information-starved, with the only event being a saved player, offering no direct clues about wolf identities. Game phase: Mid-game, at the first vote of the game. Consensus texture: A strong, organic consensus formed rapidly, with 6 out of 8 players voting for the same target without a single vocal leader driving the push.
**Approach:** The villagers converged on a single target based on subtle behavioral cues from the Day 1 and Day 2 discussions.
**Outcome:** The village successfully eliminated a wolf on the first vote with no information roles revealed, giving them a significant early-game advantage.

### Memory 10 (observation) [key: 37d81419-2d5] (score: 0.7891)
**Situation:** A villager (player_8) misinterpreted the Investigator's aggressive push against a wolf as a disruptive tactic and voted against the Investigator. Information landscape: The landscape was based on speculative reads of player behavior, not hard evidence, although a strong case was being built against one player. Game phase: Mid-game, during the first consequential vote of the game. Social pressure: There was a tense 1-v-1 dynamic between the Investigator (player_4) and a wolf (player_1), creating confusion.
**Approach:** The villager voted against the aggressive accuser (player_4), believing they were sowing discord, rather than voting for the more passive but suspicious player (player_1).
**Outcome:** The vote nearly saved the wolf. The next day, after roles were revealed, this vote put the villager under intense suspicion, and they had to justify their mistake to survive.

### Memory 11 (strategy_point) [key: 984356e1-d54] (score: 0.7898)
**Situation:** When a player consistently advocates for caution, delays votes, and demands to wait for patterns while refusing to provide their own concrete suspects. Information landscape: Information-starved, where only behavioral reads and communication styles are available. Game phase: Mid-game, building up to the first critical vote.
**Action:** Treat persistent stalling and refusal to name suspects as a strong wolf indicator, as wolves benefit from inaction and extending information-starved days. Pressure them to name specific suspects or vote for them.

### Memory 12 (strategy_point) [key: 3b4ce51c-ffd] (score: 0.7720)
**Situation:** In the mid-game, when trust is low and a recent mislynch has occurred, a single, aggressive accuser pushes for a vote based on subjective behavioral reads rather than voting records or role-based claims. The information landscape is starved, and the accuser is applying intense social pressure to force a quick decision.
**Action:** Consider a counter-vote on the accuser. Forcing them to defend their methods can reveal whether they are an information role with poor communication or a wolf using high-pressure tactics. This move punishes attempts to railroad the village and reinforces a standard for evidence-based decisions.

### Memory 13 (strategy_point) [key: 84d9366f-f06] (score: 0.7716)
**Situation:** If multiple players coordinate to dismiss or suppress the analysis of the only hard evidence available, such as voting records. Information landscape: The information landscape contains concrete evidence (voting patterns), but some players are trying to frame it as irrelevant. Game phase: Mid-game, when analyzing past votes is crucial to finding wolf packs. Social pressure: A coordinated effort is underway to shut down a specific line of inquiry, likely to protect players who benefited from a previous deadlock.
**Action:** Immediately treat the coordinated suppression of evidence as a primary wolf signal. Rally the other villagers to form a voting bloc and eliminate the most vocal player pushing this narrative; failure to consolidate votes in this moment will lead to another deadlock.

### Memory 14 (strategy_point) [key: de8be6d6-055] (score: 0.7714)
**Situation:** If the village has been paralyzed by consecutive tie votes, and the information landscape is rich with voting data that clearly identifies a consistent bloc of players maintaining the deadlock. Game phase: Mid-game or endgame, when breaking a stalemate is critical for survival. Consensus texture: No consensus, only a recurring stalemate created by two opposing factions.
**Action:** Break the cycle by voting for a new target, specifically targeting members of the bloc that has been voting in unison to create the ties. Convince others that maintaining the status quo is a loss and that forcing a new outcome is the only path forward.

### Memory 15 (strategy_point) [key: e1c64739-2a7] (score: 0.7696)
**Situation:** In the early game, when the information landscape is speculative, a credible, though unconfirmed, player leads an accusation against another based on behavioral reads, causing a fragile consensus to form. The accused player responds with a weak or evasive defense that focuses on attacking the accuser's motives.
**Action:** Vote with the emerging consensus. In the early game, acting decisively on a strong lead from a credible player is often better than hesitating and allowing wolves another night to kill, provided the accused's defense is evasive rather than substantive.

### Memory 16 (strategy_point) [key: f944cdb4-755] (score: 0.7645)
**Situation:** If the game descends into a multi-day stalemate with tied votes, and the information landscape is dominated by confusing and contradictory voting records. Game phase: Endgame, when a single mis-vote will likely lose the game. Consensus texture: A fractured state of gridlock, driven by wolf manipulation and villager frustration.
**Action:** Resist the urge to vote randomly. Instead, re-anchor your focus on the most reliable pieces of information you have, such as which players have been confirmed targets via healer saves. Use this as your ground truth and refuse to vote against them, even if they are at the center of the stalemate's voting blocs. Scrutinize those who have benefited most from the chaos—the ones who argue against analysis.

### Memory 17 (strategy_point) [key: 2f63bae5-ead] (score: 0.7506)
**Situation:** In the early to mid-game, a fragile consensus forms against a player based on vibes or communication style rather than concrete evidence, often driven by an accuser whose own credibility is unverified. The information landscape is starved of voting records or role claims, and the village is at risk of a miselimination due to social pressure.
**Action:** Resist the urge to vote out a player simply for being aggressive, unpopular, or quiet. Abstain from the vote or vote for a different suspect and demand that the accusers provide concrete evidence. Consider that aggressive behavior can be a frustrated Investigator, while quiet behavior can be a cautious villager or a role-holder trying to avoid attention; weigh the substance of arguments against the deflections of the accuser before casting your vote.

### Memory 18 (strategy_point) [key: b252d6b2-662] (score: 0.7482)
**Situation:** In the mid-game, when the information landscape is starved and the village lacks a central narrative, votes scatter across multiple players without any consensus. This lack of coordination creates a high risk of wolves orchestrating plurality eliminations of dangerous special roles.
**Action:** Push strongly for a consolidated vote on the single most suspicious player to prevent wolves from quietly orchestrating plurality eliminations of dangerous special roles without leaving a traceable, unified voting bloc.

### Memory 19 (strategy_point) [key: 09a16417-a56] (score: 0.7482)
**Situation:** In an endgame scenario where a single incorrect vote can lose the game, an influential player, such as a suspected Investigator, makes an accusation that directly contradicts clear, public evidence like a voting record. The information landscape is defined by this conflict between a high-credibility claim and verifiable data.
**Action:** Trust the verifiable evidence over the influential player's claim. Power roles can be mistaken, and wolves can fake claims, but a voting record is an undeniable fact. Vote according to the hard evidence.

### Memory 20 (strategy_point) [key: 1cc944fd-bf5] (score: 0.7464)
**Situation:** In the mid-game, when the information landscape is starved and the village lacks a central narrative, votes scatter across multiple players without any consensus. This lack of coordination creates a risk that wolves will manipulate a small majority to lynch a villager.
**Action:** Avoid piling onto a weakly supported candidate, as this allows wolves to join a small majority and lynch a villager without taking risks. Instead, consider deliberately forcing a tie or a no-elimination day to gather more information rather than making a low-confidence guess.

## Response for Case 33

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "c2489a8b-fd8", "type": "observation", "relevance": _},
  {"idx": 2, "key": "bcf4cdb5-116", "type": "observation", "relevance": _},
  {"idx": 3, "key": "7215e341-9df", "type": "observation", "relevance": _},
  {"idx": 4, "key": "9d390cf1-21a", "type": "observation", "relevance": _},
  {"idx": 5, "key": "fc9a9421-cf8", "type": "observation", "relevance": _},
  {"idx": 6, "key": "300150ed-4b6", "type": "observation", "relevance": _},
  {"idx": 7, "key": "e6eef8d6-6db", "type": "observation", "relevance": _},
  {"idx": 8, "key": "f88a85ae-1ee", "type": "observation", "relevance": _},
  {"idx": 9, "key": "53e65a70-5d0", "type": "observation", "relevance": _},
  {"idx": 10, "key": "37d81419-2d5", "type": "observation", "relevance": _},
  {"idx": 11, "key": "984356e1-d54", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "3b4ce51c-ffd", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "84d9366f-f06", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "de8be6d6-055", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "e1c64739-2a7", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "f944cdb4-755", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "2f63bae5-ead", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "b252d6b2-662", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "09a16417-a56", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "1cc944fd-bf5", "type": "strategy_point", "relevance": _}
]
```