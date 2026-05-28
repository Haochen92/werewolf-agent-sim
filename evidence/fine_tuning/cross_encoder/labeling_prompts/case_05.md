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