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

# Case 28: investigator — day_discussion (day 2 round 1)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:0594bfab4ecdc541 | investigator | day 2 round 1 | day_discussion
================================================================================

Role: investigator
Day: 2, Round: 1

Surviving players: player_2, player_4, player_5, player_6, player_7, player_3, player_8

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 discussion remained neutral and cautious, with all players (player_1 through player_8) exchanging general pleasantries, emphasizing the need for caution, and expressing a shared reluctance to jump to conclusions or force a quick lynch without evidence.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a villager.

--- Today's public discussion ---
No messages yet.

--- Your private investigation results ---
Day 1: player_1 was revealed as villager

--- Strategy note ---
Since the game is in the very early stages and no one has stood out yet, I will begin by investigating player_1. Player_1 initiated the conversation and took a leadership role early on, which is either a sign of a helpful villager or a wolf trying to direct the narrative. Establishing a read on the first speaker will give me a baseline to compare others against in later rounds.

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

**Situation 1:** A villager was killed on the first night, and the investigator had investigated that same player — confirming them as a villager but losing the information to the wolf kill. The day 2 discussion has not yet begun in earnest. Information landscape: The investigator holds private confirmation that the killed player was indeed a villager (no information gain), while publicly the village has zero leads. Game phase: Early game, day 2 with 7 players; the investigator's first investigation was wasted on a player who is already dead. Consensus texture: No consensus has formed yet. Agent exposure: Low profile — the investigator has not drawn attention and needs to decide how to use a wasted investigation night without revealing their role.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 928fde7b-4c7] (score: 0.8311)
**Situation:** The Investigator identified a wolf on Night 1 and needed to convince the village to eliminate them on Day 2 without revealing their role. Information landscape: The Investigator had private, confirmed information, while the rest of the village was operating on behavioral reads. Game phase: Mid-game, following the first wolf kill which eliminated the Healer.
**Approach:** The Investigator (player_4) aggressively questioned the wolf's arguments for inaction, framing it as a stalling tactic that benefited wolves, galvanizing the village to vote without revealing their role.
**Outcome:** The village successfully eliminated the wolf. However, the Investigator's prominent role in the accusation made them the obvious target for the remaining wolf on the following night.

### Memory 2 (observation) [key: d87c1479-d9d] (score: 0.8115)
**Situation:** The Investigator (player_1) took an active role in leading the Day 1 discussion, attempting to organize the village. Information landscape: The landscape was information-starved as it was the first day. Game phase: Early game, before any night actions had occurred.
**Approach:** The Investigator tried to steer the conversation, which made them stand out as a proactive player. That night, they successfully identified player_8 as a wolf.
**Outcome:** The Investigator's high visibility made them the wolves' Night 1 target. They were eliminated before they could share their findings, and the crucial information was lost.

### Memory 3 (observation) [key: d8ff9b6f-464] (score: 0.8042)
**Situation:** The Investigator (player_7) identified a wolf (player_1) on the first night but had no public evidence to prove it. Information landscape: The investigator possessed information-rich private knowledge, but the public landscape was information-starved with only behavioral reads available. Game phase: Mid-game, following the first night's elimination of the Healer. Social pressure: Pressure built on the wolf after the Investigator highlighted a logical inconsistency from their Day 1 statements.
**Approach:** The Investigator built a consensus against the wolf by subtly guiding the village, publicly questioning the wolf's contradictory advice from Day 1 and framing it as suspicious behavior, rather than revealing their findings or using voting records.
**Outcome:** The wolf reacted defensively, which led other villagers to become suspicious independently. The village voted out the wolf without the Investigator having to reveal their role, preserving their cover for future nights.

### Memory 4 (observation) [key: a6d1e994-772] (score: 0.8029)
**Situation:** The Investigator attempted to guide the village by pointing out general passivity and a lack of factions, without naming specific suspects. Information landscape: The landscape was information-starved, with the only lead being a saved villager from the night before. Game phase: Mid-game, following the first night action which resulted in a save. This was the first real opportunity for analysis. Consensus texture: There was no consensus, and the village was looking for a direction which the Investigator tried to provide in an abstract way. Social pressure: The targeted villager (player_2) put direct pressure on the Investigator to name a suspect, turning the abstract guidance into a point of suspicion.
**Approach:** The Investigator (player_6) used abstract concepts like 'analyzing ambiguity' to prompt discussion, but this was perceived as evasive and unhelpful when pressed for a concrete name.
**Outcome:** A strong consensus formed against the Investigator, with players finding their abstract talk suspicious. They were voted out, costing the village its most powerful information-gathering role early on.

### Memory 5 (observation) [key: aaa08a1d-619] (score: 0.8023)
**Situation:** Early or mid-game, an Investigator who has correctly identified a wolf on Night 1 attempts to lead the village against them. The public information landscape is starved, with no concrete evidence available, making the village reliant on behavioral reads and social dynamics. The Investigator's push is perceived as overly aggressive and unsubstantiated, allowing the wolf (or wolves) to successfully frame the Investigator as a disruptor and create a counter-consensus.
**Approach:** Making aggressive, public accusations based on behavioral reads (e.g., 'shift in behavior', 'being too quiet') without revealing the Investigator role (11x); failing to counter a coordinated dismissal of reasoning (2x); and relying on subjective 'vibe checks' that were easily dismissed (1x).
**Outcome:** The village, finding the Investigator's unsubstantiated aggression more suspicious than the wolf's defense, votes out the Investigator. This catastrophic error removes the only player with concrete information from the game, giving the wolves a major advantage.

### Memory 6 (observation) [key: 3625d761-b7d] (score: 0.8023)
**Situation:** The Investigator had confirmed the Healer's identity on Night 1 but needed to survive to gather more information. Information landscape: The Investigator possessed private, confirmed information, but the public landscape was information-starved. Game phase: Mid-game, after the Healer's death was announced.
**Approach:** The Investigator (player_8) chose to remain silent during the Day 2 discussion to avoid drawing attention and being targeted by wolves.
**Outcome:** Their silence was interpreted as suspicious passivity by the information-starved villagers. A consensus formed against them, leading to their elimination before they could share any findings or investigate a wolf.

### Memory 7 (observation) [key: dffa1e08-f2a] (score: 0.8000)
**Situation:** The Investigator (player_1) was saved by the healer and thus publicly confirmed as town-aligned. Information landscape: The Investigator had public trust but their private investigations had only cleared villagers, giving them no wolf leads to share. Game phase: Early game, after the first night's results were announced.
**Approach:** The Investigator used their credibility to lead the discussion, but targeted a proactive villager (player_6) for being 'too eager', framing their energy as suspicious.
**Outcome:** While the Investigator successfully led the vote, their misjudgment resulted in the elimination of a villager. This also confirmed them as the village leader, making them the wolves' priority target for the following night.

### Memory 8 (observation) [key: a49feaa8-ca9] (score: 0.7978)
**Situation:** The investigator had privately confirmed two players (a villager and the healer) as innocent. Information landscape: The investigator possessed private, information-rich knowledge about village allies, while the public landscape was still developing. Game phase: Mid-game.
**Approach:** The investigator used their private knowledge to confidently align with the confirmed innocents, forming a trusted bloc. They aggressively led the accusation against a suspect whose public actions (voting for the confirmed healer) contradicted the investigator's private information.
**Outcome:** This trusted coalition led the discussion, dismantled the suspect's defenses, and ensured the village remained united in voting out the wolf, securing the win without the investigator revealing their role.

### Memory 9 (observation) [key: d20aabe2-748] (score: 0.7945)
**Situation:** An Investigator found a wolf on the first night and needed to convince the village to eliminate them. Information landscape: The Investigator had a confirmed wolf identity, but the rest of the village was information-starved with no public leads. Game phase: Mid-game, after one night action but before any eliminations, so stakes were high for the first vote. Consensus texture: A fragile consensus was built from scratch by the Investigator's claim, turning into a strong one. Social pressure: The Investigator placed heavy, evidence-based pressure on the wolf (player_2), who was initially under suspicion for being quiet.
**Approach:** The Investigator (player_3) first accused the wolf (player_2) based on behavior (being too quiet), and when challenged, revealed their role and their finding to force the village's hand.
**Outcome:** The village overwhelmingly voted out the wolf. However, this act of revealing their role made the Investigator the clear target for the remaining wolf on the following night.

### Memory 10 (observation) [key: 6184533a-22e] (score: 0.7884)
**Situation:** Mid-game, the investigator possesses private, confirmed information about innocent allies, but the public discussion is chaotic, speculative, and lacks clear direction. The village is struggling to find consensus and is at risk of mislynching.
**Approach:** Failing to leverage private knowledge to build a trusted bloc or guide the village, instead either remaining passive and voting with a flawed majority (1x) or actively contributing to deadlock by voting based on personal suspicion rather than confirmed information (1x).
**Outcome:** The investigator's failure to effectively use their private information resulted in the village making critical errors (mislynching innocents, vote deadlocks), ultimately allowing the wolves to win the game. The valuable information was wasted.

### Memory 11 (strategy_point) [key: d6b71a52-c14] (score: 0.8310)
**Situation:** If your first investigation confirms a power role (e.g., Healer), but that player is killed by wolves overnight before you can reveal your findings. Information landscape: You hold private, valuable information, but the public information landscape is still starved. Game phase: Early to mid-game, after the first night's kill is revealed.
**Action:** You must become more vocal. Subtly guide the conversation by pointing out that the wolves likely targeted the victim because they were a threat. This builds your credibility without forcing you to make a risky early role claim, and it prevents you from being voted out for being too quiet.

### Memory 12 (strategy_point) [key: 9f51af0e-1e5] (score: 0.8041)
**Situation:** If it is early in the game and you have not yet gathered definitive information from your night actions, leaving the village information-starved. Information landscape: There are no concrete leads, and suspicion is based purely on speculative behavioral reads. Game phase: Early game (Day 1), when wolves are looking for high-value targets and you are vulnerable to both day-time elimination and night-time targeting.
**Action:** Adopt a moderate profile to avoid becoming a target for the wolves' first night kill or drawing suspicion for being overly aggressive. Resist the urge to force an elimination based on weak evidence; instead, use the discussion to ask specific, probing questions to individual players to gauge their reactions and generate new information, while keeping your own role claim in reserve.

### Memory 13 (strategy_point) [key: 5681a68d-971] (score: 0.7865)
**Situation:** If you have privately identified a wolf, and the village is already suspicious of them based on flawed or speculative reasoning. Information landscape: You possess confirmed, private information, while the village's suspicion is based on a misunderstanding. Consensus texture: A fragile or growing consensus against your target already exists.
**Action:** Do not correct the village's flawed reasoning. Instead, publicly agree with their conclusion while providing your own, separate, behavior-based reasons. This allows you to steer the existing momentum to eliminate a known wolf without exposing your valuable information or role.

### Memory 14 (strategy_point) [key: 61de853f-6e2] (score: 0.7778)
**Situation:** If you have privately confirmed one or more players as villagers, but revealing your role is too risky. Information landscape: You possess private, information-rich knowledge, while the public sphere is information-starved and prone to speculation. Game phase: Mid-game, when the village is desperate for leads and you need to build influence without becoming a target.
**Action:** Determine your approach based on the village's state: if the town is chaotic or prone to bad decisions, avoid suspicious silence. Instead, subtly guide the conversation by asking probing questions or pointing out logical fallacies in accusations against your confirmed villagers, building a silent alliance. If the village is open to direction, actively and publicly align with the confirmed villager to form a trusted voting bloc, giving your joint accusations more weight.

### Memory 15 (strategy_point) [key: 29866942-0c4] (score: 0.7777)
**Situation:** If you have privately identified a wolf but lack the public evidence or credibility to lead a direct charge, and the village is in the early to mid-game with an information-starved landscape. You prioritize maintaining your cover and avoiding suspicion, so you cannot reveal your role or your private findings.
**Action:** Do not reveal your role or your finding directly. Instead, act as a sharp villager and guide the conversation by pointing out behavioral evidence and logical flaws in the wolf's statements. Build the public case so the village feels they discovered the wolf through their own logic, which protects you from being targeted. If you are met with coordinated dismissal, pivot to pointing out that the coordinated effort to shut down discussion is itself suspicious and indicative of a pack protecting its own.

### Memory 16 (strategy_point) [key: f25fcf4f-641] (score: 0.7741)
**Situation:** If you have identified a wolf on the first night and need to convince the village when there are no other leads, and the village is receptive to your input. Information landscape: You possess a private, information-rich finding, while the public landscape is information-starved. Game phase: Early game (Day 2). Social pressure: You are initiating the pressure, and the village is open to your lead.
**Action:** Do not reveal your role or frame your accusation as a 'hunch.' Instead, state your case with confidence and build a public case based on the wolf's observable behavior—such as stalling, deflecting, or being vaguely agreeable—to substantiate your claim. Presenting a weak, vibes-based accusation makes you look like a disruptive villager and gives the wolf an easy opening to attack your credibility.

### Memory 17 (strategy_point) [key: 3ad8ba65-371] (score: 0.7740)
**Situation:** If you have identified a wolf with your night action, but the village has no other leads. Information landscape: You possess a piece of concrete information (a wolf's identity), while the public landscape is information-starved. Game phase: Early to mid-game, after the first night. Social pressure: You are about to initiate pressure on a target who is not otherwise suspected.
**Action:** Avoid initiating a case with vague, behavioral evidence, as this often backfires. Instead, gently guide the conversation by pointing out suspicious behaviors from your target and asking other villagers for their interpretations, or wait for the wolf to make a tangible mistake. This frames you as a collaborative investigator; however, if you become the target of a vote, be prepared to reveal your role and finding as a last resort to save yourself and pass on the information.

### Memory 18 (strategy_point) [key: a79b348d-e25] (score: 0.7731)
**Situation:** If you have privately identified a wolf and there is strong, corroborating public evidence, but the village has not yet converged on the target or is wary of a mislynch. Information landscape: You possess certain private knowledge, while the public sphere may be driven by speculative reads or verifiable facts. Game phase: Mid-game or Endgame, where you need to actively build consensus to secure an elimination without revealing your role, especially when the village is under high pressure to avoid a final incorrect vote.
**Action:** Lead the discussion confidently, focusing all arguments on the public evidence. Construct a public case using voting records and behaviors to support your private knowledge, framing your certainty as a strong conviction based on shared evidence rather than an unsubstantiated claim. This allows you to leverage your certainty to build momentum and dismantle defenses without having to reveal your Investigator role or appearing as a wolf forcing a bad vote.

### Memory 19 (strategy_point) [key: 306a4905-b9d] (score: 0.7630)
**Situation:** If you are being targeted by a growing consensus based on vibes or your silence in an information-starved early game. Information landscape: The village is information-starved and acting on speculation, with no concrete leads. Game phase: Early game, when your role is most critical and most vulnerable. Social pressure: A bandwagon is forming against you, and staying silent is being interpreted as guilt.
**Action:** Claim your Investigator role immediately and share your findings. Being eliminated by the village is the worst-case scenario as it removes your powers permanently. Claiming your role forces the wolves to kill you at night, giving the healer a chance to save you and buying the village at least one more day of your insights.

### Memory 20 (strategy_point) [key: f294f167-8d7] (score: 0.7588)
**Situation:** If your nightly investigation yielded no useful information (e.g., you identified a villager) and a strong consensus is already forming against a suspect based on solid public evidence.
**Action:** Do not intervene by making a new accusation based on a weak behavioral read. Contradicting a strong, evidence-based consensus to push a speculative theory can derail the village and make you appear suspicious. It is better to support the logical conclusion and save your influence for when you have concrete information.

## Response for Case 28

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "928fde7b-4c7", "type": "observation", "relevance": _},
  {"idx": 2, "key": "d87c1479-d9d", "type": "observation", "relevance": _},
  {"idx": 3, "key": "d8ff9b6f-464", "type": "observation", "relevance": _},
  {"idx": 4, "key": "a6d1e994-772", "type": "observation", "relevance": _},
  {"idx": 5, "key": "aaa08a1d-619", "type": "observation", "relevance": _},
  {"idx": 6, "key": "3625d761-b7d", "type": "observation", "relevance": _},
  {"idx": 7, "key": "dffa1e08-f2a", "type": "observation", "relevance": _},
  {"idx": 8, "key": "a49feaa8-ca9", "type": "observation", "relevance": _},
  {"idx": 9, "key": "d20aabe2-748", "type": "observation", "relevance": _},
  {"idx": 10, "key": "6184533a-22e", "type": "observation", "relevance": _},
  {"idx": 11, "key": "d6b71a52-c14", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "9f51af0e-1e5", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "5681a68d-971", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "61de853f-6e2", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "29866942-0c4", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "f25fcf4f-641", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "3ad8ba65-371", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "a79b348d-e25", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "306a4905-b9d", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "f294f167-8d7", "type": "strategy_point", "relevance": _}
]
```