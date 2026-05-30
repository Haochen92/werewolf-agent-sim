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