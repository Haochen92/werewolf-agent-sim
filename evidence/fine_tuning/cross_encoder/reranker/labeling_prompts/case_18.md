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

# Case 18: investigator — day_discussion (day 3 round 1)

## Game State (what the player sees)
```
================================================================================
CASE 8e437de2eab2d9d54e45ed4dee61fe54:259d3c37a9f3e166 | investigator | day 3 round 1 | day_discussion
================================================================================

Role: investigator
Day: 3, Round: 1

Surviving players: player_1, player_2, player_3, player_4, player_5, player_7, player_6

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 discussion was characterized by players collectively agreeing to observe behavior and exchange initial thoughts, with no specific accusations, defenses, role claims, or alliances forming.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was targeted by the wolves last night, but was saved by the healer!

[Day 2]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The discussion focused on the significance of the survivor of the previous night's attack, with players 1 through 8 generally agreeing that the group should monitor for suspicious behavior, defensive reactions, or attempts to deflect attention from the failed kill. No specific players were accused, no roles were claimed by individuals, and no voting blocs were formed.

[Day 2]

Here's the vote result for day 2:
  player_1 voted for player_8
  player_2 voted for player_8
  player_3 voted for player_8
  player_4 voted for player_8
  player_5 voted for player_8
  player_7 voted for player_8
  player_6 voted for player_2
  player_8 voted for player_2
Player player_8 has been voted out and was a wolf.


[Day 2]
player_3 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
No messages yet.

--- Your private investigation results ---
Day 1: player_1 was revealed as villager
Day 2: player_2 was revealed as healer

--- Strategy note ---
Since player_1 was targeted by wolves and saved by the healer, they are likely a high-value villager target. I have confirmed player_1 as a villager, so they are a safe ally. I will now investigate player_2 to see if they are a wolf, as they were active early on in the discussion. I need to keep a low profile and avoid revealing my role, focusing on identifying the wolf pack by checking players who seem to be steering the conversation.

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
Lead with how your private findings relate to the public narrative — do they confirm, contradict, or add nothing new? Also note whether your communication style is marking you as a power role.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The investigator has confirmed both the healer-saved player (villager) and a second player (healer) through two nights of investigation. A wolf was eliminated by near-unanimous vote on day 2, and the investigator was targeted by wolves on night 2 but saved by the healer. Information landscape: The investigator possesses rich private knowledge — confirmed identities of two key village roles — while publicly the village has a wolf elimination and voting records to analyze. Game phase: Mid-game, day 3 with 7 players remaining and 1 wolf left; the investigator's survival via healer save suggests the wolves have identified them. Consensus texture: The village was unified on day 2 and should carry momentum. Agent exposure: High-value target — the wolves targeted the investigator specifically, suggesting they know the role; the healer cannot save the same player consecutively.

**Situation 2:** The investigator knows the healer's identity through private investigation and must protect this information while guiding the village toward the remaining wolf. Revealing the healer's identity would expose them to the wolves, but withholding it means the village operates without knowing who is confirmed. Information landscape: The investigator has more confirmed information than any other player but cannot share it without endangering the healer. Game phase: Mid-game with the investigator at risk of being the wolves' primary night target. Consensus texture: Village should be confident after correctly identifying a wolf. Agent exposure: Under lethal threat — wolves have identified the investigator and will likely target them again.

## Retrieved Memories to Label

### Memory 1 (observation) [key: a49feaa8-ca9] (score: 0.8528)
**Situation:** The investigator had privately confirmed two players (a villager and the healer) as innocent. Information landscape: The investigator possessed private, information-rich knowledge about village allies, while the public landscape was still developing. Game phase: Mid-game.
**Approach:** The investigator used their private knowledge to confidently align with the confirmed innocents, forming a trusted bloc. They aggressively led the accusation against a suspect whose public actions (voting for the confirmed healer) contradicted the investigator's private information.
**Outcome:** This trusted coalition led the discussion, dismantled the suspect's defenses, and ensured the village remained united in voting out the wolf, securing the win without the investigator revealing their role.

### Memory 2 (observation) [key: 3625d761-b7d] (score: 0.8479)
**Situation:** The Investigator had confirmed the Healer's identity on Night 1 but needed to survive to gather more information. Information landscape: The Investigator possessed private, confirmed information, but the public landscape was information-starved. Game phase: Mid-game, after the Healer's death was announced.
**Approach:** The Investigator (player_8) chose to remain silent during the Day 2 discussion to avoid drawing attention and being targeted by wolves.
**Outcome:** Their silence was interpreted as suspicious passivity by the information-starved villagers. A consensus formed against them, leading to their elimination before they could share any findings or investigate a wolf.

### Memory 3 (observation) [key: 928fde7b-4c7] (score: 0.8435)
**Situation:** The Investigator identified a wolf on Night 1 and needed to convince the village to eliminate them on Day 2 without revealing their role. Information landscape: The Investigator had private, confirmed information, while the rest of the village was operating on behavioral reads. Game phase: Mid-game, following the first wolf kill which eliminated the Healer.
**Approach:** The Investigator (player_4) aggressively questioned the wolf's arguments for inaction, framing it as a stalling tactic that benefited wolves, galvanizing the village to vote without revealing their role.
**Outcome:** The village successfully eliminated the wolf. However, the Investigator's prominent role in the accusation made them the obvious target for the remaining wolf on the following night.

### Memory 4 (observation) [key: bb9b8a2c-f53] (score: 0.8413)
**Situation:** The Investigator privately identified a wolf and needed to convince the village to eliminate them without revealing their role. Information landscape: The Investigator had private, certain information supported by public, concrete evidence from the voting record. Game phase: Mid-game, after the Healer was eliminated.
**Approach:** The Investigator (player_4) led the discussion by highlighting voting discrepancies to build a logical case against the wolf, avoiding a role reveal.
**Outcome:** The village voted out the wolf, but the Investigator's high-profile leadership made them a target, leading to their death the following night.

### Memory 5 (observation) [key: a5db9f55-0d8] (score: 0.8306)
**Situation:** In the mid-game to endgame, the Investigator possessed private, information-rich knowledge (identifying both innocent players and wolves). The information landscape combined public voting records and behavioral reads with the Investigator's private findings. The village required active, subtle guidance to solidify the case against wolves without the Investigator revealing their role.
**Approach:** The Investigator chose not to reveal their role. Instead, they actively guided the public discussion by reinforcing correct suspicions, amplifying arguments against suspects, and highlighting incriminating public evidence—such as voting records and deflection tactics—to build a natural consensus.
**Outcome:** The Investigator successfully guided the village to eliminate the wolves without becoming a target or revealing their role. This subtle approach preserved their ability to gather information and contribute to discussions safely, leading to a village victory.

### Memory 6 (observation) [key: 6184533a-22e] (score: 0.8281)
**Situation:** Mid-game, the investigator possesses private, confirmed information about innocent allies, but the public discussion is chaotic, speculative, and lacks clear direction. The village is struggling to find consensus and is at risk of mislynching.
**Approach:** Failing to leverage private knowledge to build a trusted bloc or guide the village, instead either remaining passive and voting with a flawed majority (1x) or actively contributing to deadlock by voting based on personal suspicion rather than confirmed information (1x).
**Outcome:** The investigator's failure to effectively use their private information resulted in the village making critical errors (mislynching innocents, vote deadlocks), ultimately allowing the wolves to win the game. The valuable information was wasted.

### Memory 7 (observation) [key: dffa1e08-f2a] (score: 0.8194)
**Situation:** The Investigator (player_1) was saved by the healer and thus publicly confirmed as town-aligned. Information landscape: The Investigator had public trust but their private investigations had only cleared villagers, giving them no wolf leads to share. Game phase: Early game, after the first night's results were announced.
**Approach:** The Investigator used their credibility to lead the discussion, but targeted a proactive villager (player_6) for being 'too eager', framing their energy as suspicious.
**Outcome:** While the Investigator successfully led the vote, their misjudgment resulted in the elimination of a villager. This also confirmed them as the village leader, making them the wolves' priority target for the following night.

### Memory 8 (observation) [key: fd88ea00-70b] (score: 0.8169)
**Situation:** In the final three, the Investigator (Player 7) revealed their role and their finding that Player 3 was the last wolf. Information landscape: The investigator possessed definitive proof, but this information was private and presented to a villager (Player 6) who was skeptical after a recent mislynch. Game phase: Endgame, with the vote of a single villager deciding the game's outcome. Consensus texture: There was no consensus; the villager was a swing vote between two competing claims.
**Approach:** The Investigator stated their finding but struggled to justify why they had withheld this information on the previous day, which had resulted in the mistaken elimination of a villager (Player 8).
**Outcome:** The villager found the timing of the reveal highly suspicious and sided with the wolf's argument that it was a desperate bluff, leading to the Investigator's elimination and a wolf victory.

### Memory 9 (observation) [key: d8ff9b6f-464] (score: 0.8136)
**Situation:** The Investigator (player_7) identified a wolf (player_1) on the first night but had no public evidence to prove it. Information landscape: The investigator possessed information-rich private knowledge, but the public landscape was information-starved with only behavioral reads available. Game phase: Mid-game, following the first night's elimination of the Healer. Social pressure: Pressure built on the wolf after the Investigator highlighted a logical inconsistency from their Day 1 statements.
**Approach:** The Investigator built a consensus against the wolf by subtly guiding the village, publicly questioning the wolf's contradictory advice from Day 1 and framing it as suspicious behavior, rather than revealing their findings or using voting records.
**Outcome:** The wolf reacted defensively, which led other villagers to become suspicious independently. The village voted out the wolf without the Investigator having to reveal their role, preserving their cover for future nights.

### Memory 10 (observation) [key: 1ab6cc11-497] (score: 0.8089)
**Situation:** Having identified the final wolf on Night 3, the Investigator had to decide when and how to reveal this critical information. Information landscape: The investigator possessed perfect, private information in a public landscape that was otherwise based on speculation. Game phase: Endgame, with only four players remaining (Investigator, two Villagers, one Wolf).
**Approach:** The Investigator waited until the Day 4 discussion to make a clear, public claim against the wolf. They presented the information as a definitive fact and resisted getting drawn into a debate about the timing of the reveal.
**Outcome:** The clear, confident claim rallied the remaining villagers, creating an immediate and unbreakable consensus. The wolf was eliminated, and the town won.

### Memory 11 (observation) [key: a9107742-f0f] (score: 0.8000)
**Situation:** After a villager was mislynched on Day 2, an astute player (the Investigator) used the voting record to scrutinize players who had joined the majority vote. Information landscape: The landscape was becoming information-rich, with the Day 2 voting record providing the first concrete data for analysis. Game phase: Mid-game, with two villagers eliminated, increasing the pressure to find a wolf. Social pressure: The Investigator (player_4) placed evidence-based pressure on a wolf (player_6) for dismissing the importance of the prior day's voting history.
**Approach:** The Investigator framed the wolf's attempt to ignore past data as suspicious behavior, arguing it was a tactic to evade accountability for being part of a villager's elimination.
**Outcome:** This line of reasoning successfully swayed the remaining villagers, building a consensus to vote out the wolf (player_6), marking the village's first correct elimination.

### Memory 12 (observation) [key: a6d1e994-772] (score: 0.7994)
**Situation:** The Investigator attempted to guide the village by pointing out general passivity and a lack of factions, without naming specific suspects. Information landscape: The landscape was information-starved, with the only lead being a saved villager from the night before. Game phase: Mid-game, following the first night action which resulted in a save. This was the first real opportunity for analysis. Consensus texture: There was no consensus, and the village was looking for a direction which the Investigator tried to provide in an abstract way. Social pressure: The targeted villager (player_2) put direct pressure on the Investigator to name a suspect, turning the abstract guidance into a point of suspicion.
**Approach:** The Investigator (player_6) used abstract concepts like 'analyzing ambiguity' to prompt discussion, but this was perceived as evasive and unhelpful when pressed for a concrete name.
**Outcome:** A strong consensus formed against the Investigator, with players finding their abstract talk suspicious. They were voted out, costing the village its most powerful information-gathering role early on.

### Memory 13 (strategy_point) [key: a79b348d-e25] (score: 0.8192)
**Situation:** If you have privately identified a wolf and there is strong, corroborating public evidence, but the village has not yet converged on the target or is wary of a mislynch. Information landscape: You possess certain private knowledge, while the public sphere may be driven by speculative reads or verifiable facts. Game phase: Mid-game or Endgame, where you need to actively build consensus to secure an elimination without revealing your role, especially when the village is under high pressure to avoid a final incorrect vote.
**Action:** Lead the discussion confidently, focusing all arguments on the public evidence. Construct a public case using voting records and behaviors to support your private knowledge, framing your certainty as a strong conviction based on shared evidence rather than an unsubstantiated claim. This allows you to leverage your certainty to build momentum and dismantle defenses without having to reveal your Investigator role or appearing as a wolf forcing a bad vote.

### Memory 14 (strategy_point) [key: 61de853f-6e2] (score: 0.8178)
**Situation:** If you have privately confirmed one or more players as villagers, but revealing your role is too risky. Information landscape: You possess private, information-rich knowledge, while the public sphere is information-starved and prone to speculation. Game phase: Mid-game, when the village is desperate for leads and you need to build influence without becoming a target.
**Action:** Determine your approach based on the village's state: if the town is chaotic or prone to bad decisions, avoid suspicious silence. Instead, subtly guide the conversation by asking probing questions or pointing out logical fallacies in accusations against your confirmed villagers, building a silent alliance. If the village is open to direction, actively and publicly align with the confirmed villager to form a trusted voting bloc, giving your joint accusations more weight.

### Memory 15 (strategy_point) [key: d6b71a52-c14] (score: 0.8168)
**Situation:** If your first investigation confirms a power role (e.g., Healer), but that player is killed by wolves overnight before you can reveal your findings. Information landscape: You hold private, valuable information, but the public information landscape is still starved. Game phase: Early to mid-game, after the first night's kill is revealed.
**Action:** You must become more vocal. Subtly guide the conversation by pointing out that the wolves likely targeted the victim because they were a threat. This builds your credibility without forcing you to make a risky early role claim, and it prevents you from being voted out for being too quiet.

### Memory 16 (strategy_point) [key: 5681a68d-971] (score: 0.8111)
**Situation:** If you have privately identified a wolf, and the village is already suspicious of them based on flawed or speculative reasoning. Information landscape: You possess confirmed, private information, while the village's suspicion is based on a misunderstanding. Consensus texture: A fragile or growing consensus against your target already exists.
**Action:** Do not correct the village's flawed reasoning. Instead, publicly agree with their conclusion while providing your own, separate, behavior-based reasons. This allows you to steer the existing momentum to eliminate a known wolf without exposing your valuable information or role.

### Memory 17 (strategy_point) [key: b98bd43c-79a] (score: 0.8027)
**Situation:** If you have been repeatedly targeted by wolves at night but saved by the healer, or if you have identified a wolf and survived an attack, establishing yourself as a high-value target. Information landscape: Public information confirms you were targeted and saved, and your survival provides a signal of your threat to the wolves, even if your role remains unknown. Game phase: Mid-game, when momentum is crucial and you need to build credibility to lead the village.
**Action:** Use the pattern of being targeted as public evidence of your importance, arguing that wolves would only focus on you so relentlessly if you were a high-value role. If you have identified a wolf, immediately lead the accusation, framing your argument around their suspicious behavior and using your survival as implicit proof that you are a threat to the wolves, rather than explicitly claiming your role.

### Memory 18 (strategy_point) [key: 9c21fe39-320] (score: 0.8007)
**Situation:** If you have been saved by the healer, making you a publicly confirmed town-aligned player. Information landscape: Your alignment is confirmed, giving you immense credibility, but you may lack actionable intelligence. Game phase: Early to mid-game, when you have a significant opportunity to shape the village dynamic.
**Action:** Leverage your trusted status to guide the village's logic and focus their attention on evidence-based reasoning. Act as a facilitator to prevent chaotic mislynches, but allow other vocal villagers to lead direct accusations. This prevents you from appearing dictatorial, keeps the consensus feeling organic, and protects you from being targeted as a high-value player.

### Memory 19 (strategy_point) [key: 82a4ac4c-3ac] (score: 0.8003)
**Situation:** When the village is already rapidly converging on the player you know is a wolf due to your private investigation, based on accurate analysis of public data. Information landscape: Information-rich, with the village correctly interpreting voting records and behavior. Game phase: Mid-game or Endgame, with strong consensus building.
**Action:** Keep your contributions focused and avoid overplaying your hand. Do not reveal your role; instead, amplify the existing public evidence to help the village maintain focus and secure the elimination without risking your own exposure.

### Memory 20 (strategy_point) [key: 29866942-0c4] (score: 0.7917)
**Situation:** If you have privately identified a wolf but lack the public evidence or credibility to lead a direct charge, and the village is in the early to mid-game with an information-starved landscape. You prioritize maintaining your cover and avoiding suspicion, so you cannot reveal your role or your private findings.
**Action:** Do not reveal your role or your finding directly. Instead, act as a sharp villager and guide the conversation by pointing out behavioral evidence and logical flaws in the wolf's statements. Build the public case so the village feels they discovered the wolf through their own logic, which protects you from being targeted. If you are met with coordinated dismissal, pivot to pointing out that the coordinated effort to shut down discussion is itself suspicious and indicative of a pack protecting its own.

### Memory 21 (strategy_point) [key: f25fcf4f-641] (score: 0.7797)
**Situation:** If you have identified a wolf on the first night and need to convince the village when there are no other leads, and the village is receptive to your input. Information landscape: You possess a private, information-rich finding, while the public landscape is information-starved. Game phase: Early game (Day 2). Social pressure: You are initiating the pressure, and the village is open to your lead.
**Action:** Do not reveal your role or frame your accusation as a 'hunch.' Instead, state your case with confidence and build a public case based on the wolf's observable behavior—such as stalling, deflecting, or being vaguely agreeable—to substantiate your claim. Presenting a weak, vibes-based accusation makes you look like a disruptive villager and gives the wolf an easy opening to attack your credibility.

### Memory 22 (strategy_point) [key: 3ad8ba65-371] (score: 0.7783)
**Situation:** If you have identified a wolf with your night action, but the village has no other leads. Information landscape: You possess a piece of concrete information (a wolf's identity), while the public landscape is information-starved. Game phase: Early to mid-game, after the first night. Social pressure: You are about to initiate pressure on a target who is not otherwise suspected.
**Action:** Avoid initiating a case with vague, behavioral evidence, as this often backfires. Instead, gently guide the conversation by pointing out suspicious behaviors from your target and asking other villagers for their interpretations, or wait for the wolf to make a tangible mistake. This frames you as a collaborative investigator; however, if you become the target of a vote, be prepared to reveal your role and finding as a last resort to save yourself and pass on the information.

### Memory 23 (strategy_point) [key: c557f813-1d6] (score: 0.7564)
**Situation:** If you have just successfully led the village to vote out a wolf you investigated. Information landscape: Your arguments have been publicly validated by the wolf's role reveal, making you the most credible voice in the game. Game phase: Mid-game, after a successful, high-profile vote that you orchestrated.
**Action:** Immediately reduce your visibility. Your success has painted a large target on your back. Allow other villagers to lead the next round of discussion. You can guide them subtly, but avoid being the sole accuser again, as the remaining wolves will make you their top priority for the next night kill.

### Memory 24 (strategy_point) [key: 9f51af0e-1e5] (score: 0.7544)
**Situation:** If it is early in the game and you have not yet gathered definitive information from your night actions, leaving the village information-starved. Information landscape: There are no concrete leads, and suspicion is based purely on speculative behavioral reads. Game phase: Early game (Day 1), when wolves are looking for high-value targets and you are vulnerable to both day-time elimination and night-time targeting.
**Action:** Adopt a moderate profile to avoid becoming a target for the wolves' first night kill or drawing suspicion for being overly aggressive. Resist the urge to force an elimination based on weak evidence; instead, use the discussion to ask specific, probing questions to individual players to gauge their reactions and generate new information, while keeping your own role claim in reserve.

### Memory 25 (strategy_point) [key: bd79d243-9a6] (score: 0.7488)
**Situation:** When a suspect tries to deflect blame onto a player you have privately confirmed is a key town role, like the Healer. Information landscape: You have an information advantage, combining public evidence with your private investigation results. Game phase: Mid-game or endgame, when your private information becomes critical to prevent a mislynch. Social pressure: A cornered suspect is trying to sow chaos by accusing a powerful town role.
**Action:** Confidently shut down the accusation without revealing your role or your specific findings. Frame the deflection as a 'desperate move' or 'classic wolf tactic.' Your certainty, backed by the existing public evidence against the suspect, will help solidify the town's consensus.

## Response for Case 18

Rate each of the 25 memories above. JSON format:
```json
[
  {"idx": 1, "key": "a49feaa8-ca9", "type": "observation", "relevance": _},
  {"idx": 2, "key": "3625d761-b7d", "type": "observation", "relevance": _},
  {"idx": 3, "key": "928fde7b-4c7", "type": "observation", "relevance": _},
  {"idx": 4, "key": "bb9b8a2c-f53", "type": "observation", "relevance": _},
  {"idx": 5, "key": "a5db9f55-0d8", "type": "observation", "relevance": _},
  {"idx": 6, "key": "6184533a-22e", "type": "observation", "relevance": _},
  {"idx": 7, "key": "dffa1e08-f2a", "type": "observation", "relevance": _},
  {"idx": 8, "key": "fd88ea00-70b", "type": "observation", "relevance": _},
  {"idx": 9, "key": "d8ff9b6f-464", "type": "observation", "relevance": _},
  {"idx": 10, "key": "1ab6cc11-497", "type": "observation", "relevance": _},
  {"idx": 11, "key": "a9107742-f0f", "type": "observation", "relevance": _},
  {"idx": 12, "key": "a6d1e994-772", "type": "observation", "relevance": _},
  {"idx": 13, "key": "a79b348d-e25", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "61de853f-6e2", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "d6b71a52-c14", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "5681a68d-971", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "b98bd43c-79a", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "9c21fe39-320", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "82a4ac4c-3ac", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "29866942-0c4", "type": "strategy_point", "relevance": _},
  {"idx": 21, "key": "f25fcf4f-641", "type": "strategy_point", "relevance": _},
  {"idx": 22, "key": "3ad8ba65-371", "type": "strategy_point", "relevance": _},
  {"idx": 23, "key": "c557f813-1d6", "type": "strategy_point", "relevance": _},
  {"idx": 24, "key": "9f51af0e-1e5", "type": "strategy_point", "relevance": _},
  {"idx": 25, "key": "bd79d243-9a6", "type": "strategy_point", "relevance": _}
]
```