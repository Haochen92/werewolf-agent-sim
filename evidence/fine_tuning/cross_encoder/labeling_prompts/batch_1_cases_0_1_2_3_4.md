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

# Case 0: wolf — day_discussion (day 2 round 3)

## Game State (what the player sees)
```
================================================================================
CASE 011ac7f3306b5156b84f4d96152658bc:6cd07c9db304138d | wolf | day 2 round 3 | day_discussion
================================================================================

Role: wolf
Day: 2, Round: 3

Surviving villagers: player_2, player_3, player_4, player_5, player_6, player_7
Known surviving wolf allies: player_1, player_8

--- Previous days summary ---
[Day 1]
Key accusations: None. All players expressed that it was too early to form suspicions and opted to observe initial behaviors. Defenses: None. No players were accused, therefore no defenses were required. Any role reveals and their substantiation: None. No players revealed their roles during this discussion. Any alliances or voting blocs that formed: None. No alliances or voting blocs were formed as the players collectively agreed to take a slow approach to gather information.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_2 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
[Day 2, Round 1] player_3: It's interesting that the wolves went for player_2 on night one. Since they survived, we have a clean slate to look at everyone's reactions. Who is everyone suspicious of so far?
[Day 2, Round 1] player_4: It's good that player_2 is still with us. Let's start looking at voting patterns from now on to see who aligns with whom.
[Day 2, Round 1] player_5: It is fortunate that player_2 is still with us. I am curious if anyone has a theory on why they were targeted, or if we should treat this as a random strike.
[Day 2, Round 1] player_6: It is lucky the healer saved player_2. Since the wolves failed their target, maybe we can look at who was suspiciously quiet yesterday while everyone else was stalling. Does anyone have any initial thoughts on who seemed the most defensive?
[Day 2, Round 1] player_7: Since player_2 was saved by the healer, we need to look at how everyone reacted to that news. Any thoughts on who might be trying to fly under the radar?
[Day 2, Round 1] player_1: It is definitely lucky that player_2 was saved last night. Since we have no other leads yet, does anyone have thoughts on who might have been targeted? Maybe we should look at who has been quietest so far.
[Day 2, Round 1] player_8: It's a relief that player 2 was saved last night. That gives us a confirmed villager to help guide us, even if we're still in the dark otherwise. Does anyone have thoughts on who might have been targeted?
[Day 2, Round 2] player_2: It's a relief to still be here. Since we're all still feeling things out, maybe we should pay attention to who is trying to push for a vote too quickly versus those asking genuine questions. I'm keeping an eye on player_6 and player_8; they seem to be driving the conversation hard.

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
Maintain a low profile and avoid drawing attention. Support the narrative that the healer save on player_2 is our best lead, but focus on questioning why the wolves would target a specific player early to seed doubt. Keep distance from player_8 to prevent link identification while contributing just enough to appear engaged.

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

**Situation 1:** After a failed wolf attack, the saved player has become a trusted voice and is now accusing one of my wolf allies and another player of being too aggressive. This has put my ally under immediate pressure from a credible source, creating the first significant conflict of the game. The village must now decide whether to trust the saved player's read. Information landscape: The landscape is information-starved, with the only concrete evidence being the failed attack, which is now generating speculative behavioral reads. Game phase: This is the early game, but it has just transitioned from having no data to having one significant event—the healer save—to analyze. Consensus texture: The village has no consensus and is fragmented, but a potential power bloc is forming around the saved player's accusation, driven by their newfound credibility. Agent exposure: My personal exposure is low as I have not been mentioned, but the wolf team is under indirect pressure due to the accusation against an ally by the trusted, saved player.

## Retrieved Memories to Label

### Memory 1 (observation) [key: bfb69c8b-424] (score: 0.8178)
**Situation:** A villager (player_7) made a weak accusation against another villager (player_8) for being too quiet, leading to a defensive argument. Information landscape: The game was information-starved, with the only conflict arising from speculative behavioral reads. Game phase: Mid-game, following a night with no eliminations, which increased villager anxiety. Social pressure: A villager-driven conflict created an opportunity, which the wolves amplified by subtly defending the accused and questioning the accuser's logic.
**Approach:** The wolves fanned the flames of the argument by criticizing the accuser's reasoning (player_1) and then voted with the resulting majority to eliminate them.
**Outcome:** The village was successfully baited into eliminating a villager (player_7), allowing both wolves to blend in with the town's vote.

### Memory 2 (observation) [key: b369c51e-969] (score: 0.8164)
**Situation:** A villager (player_2) correctly used Day 2 voting records to accuse a group of players that included both wolves (player_6, player_7) and the healer (player_5). Information landscape: The landscape was becoming information-rich, with voting records being used as the primary evidence. Game phase: Endgame, with only five players remaining and the wolves one elimination away from victory. Social pressure: The wolves coordinated pressure on the accuser (player_2), deflecting the evidence by attacking their previous passivity and framing their valid points as an attempt to sow discord.
**Approach:** The wolves (player_6, player_7) aggressively challenged player_2's motives for suddenly becoming vocal, ignoring the voting evidence player_2 presented.
**Outcome:** This tactic successfully shifted suspicion onto player_2. The healer (player_5) was convinced by the wolves' narrative and voted with them, leading to another villager's elimination and a wolf victory.

### Memory 3 (observation) [key: 374a2e35-840] (score: 0.8152)
**Situation:** A wolf (Player 5) attempted to analyze a failed night attack by suggesting the saved villager (Player 8) must have been a 'threat,' effectively trying to justify the wolves' choice. Information landscape: The only information was a failed wolf attack, making the Healer's existence and target choice public knowledge. Game phase: Mid-game, after the first night's action but before any eliminations. Social pressure: This framing immediately drew coordinated, organic suspicion from multiple villagers, who identified it as a classic wolf tactic of blaming the victim.
**Approach:** The wolf (Player 5) tried to backtrack, claiming it was just a simple observation and that the village was 'infighting,' but failed to provide a convincing alternative explanation.
**Outcome:** The village formed a strong, immediate consensus against Player 5, leading to their unanimous elimination. The other wolf (Player 1) voted with the majority to eliminate their partner.

### Memory 4 (observation) [key: d0bde61b-652] (score: 0.8144)
**Situation:** On Day 2, the Investigator (player 3) initiated an accusation against a villager (player 4) based on a weak, behavioral read of their 'urgency'. Information landscape: The village was information-starved, relying on speculative reads as no roles were confirmed. Game phase: Mid-game, following the first night kill. Social pressure: Pressure began to mount on player 4, initiated by the Investigator.
**Approach:** Wolf 6 immediately piled onto the accusation, amplifying the Investigator's reasoning and helping to build a broader consensus against player 4.
**Outcome:** A strong majority voted out player 4, a villager. This eliminated a town member and simultaneously damaged the Investigator's credibility for the following day.

### Memory 5 (observation) [key: 9d1739db-282] (score: 0.8083)
**Situation:** After the village mistakenly eliminated the Healer, the discussion turned to analyzing that vote. Information landscape: The information was rich with voting records from the previous day, which implicated most of the village, including the wolves. Game phase: Mid-game, after two eliminations (Healer by vote, Villager by wolves) had significantly reduced player count. Social pressure: A wolf (player_7) initiated coordinated pressure on a villager (player_5) for being the only player who *didn't* vote for the healer.
**Approach:** Wolf player_7 deflected scrutiny from their own vote against the Healer by framing player_5's lone dissenting vote as suspicious and uncooperative.
**Outcome:** The village turned on player_5, who became defensive and was subsequently voted out. This successfully shifted blame from the wolf and eliminated another villager.

### Memory 6 (observation) [key: b59c7455-6cd] (score: 0.8064)
**Situation:** A wolf or wolves were put under pressure for stalling behaviors, such as advocating for a passive 'wait and see' strategy or refusing to name a suspect. Information landscape: The game was information-starved, with suspicion based entirely on behavioral reads, often centered on a healer save. Game phase: Mid-game, following the first night action. Social pressure: The wolf/wolves were under organic pressure from multiple players who wanted to move the discussion from generic statements to specific accusations.
**Approach:** The wolf attempted to defend their position by framing the accuser as 'disruptive' or 'rushed', or by attempting to deflect suspicion onto another villager without strong evidence.
**Outcome:** The villagers interpreted this passivity and deflection as a sign of guilt. A strong consensus formed, leading to the wolf's elimination by a near-unanimous vote.

### Memory 7 (observation) [key: 79288222-86d] (score: 0.8062)
**Situation:** In an information-starved mid-game, a proactive villager aggressively demands that players name suspects, putting pressure on the wolves. The village has no consensus and the only lead is a recent healer save. The wolves are not the primary target but are under pressure to contribute.
**Approach:** Frame a proactive villager's aggression as a suspicious tactic to force a rushed, chaotic vote (1x), while urging caution and claiming there is not enough evidence to act (1x).
**Outcome:** The village, lacking other leads, turns on the aggressive villager, leading to their elimination. This removes a proactive town member and successfully deflects suspicion from the wolves.

### Memory 8 (observation) [key: a394b860-e1b] (score: 0.8050)
**Situation:** The village had a twice-confirmed non-wolf (player_7) who became aggressive in trying to hunt wolves after a prior mislynch. Information landscape: Information was rich regarding player_7's status, but the discussion was dominated by arguments over the previous day's voting record. Game phase: Mid-game, after the village had mistakenly eliminated a villager (player_8). Social pressure: Player_7 was putting pressure on the players who voted for player_8, while player_4 was pressuring player_7 for their 'outlier' vote, creating village infighting.
**Approach:** The wolves (player_5 and player_6) exploited the village's frustration with player_7's aggressive accusations. They framed player_7 as being disruptive and joined the vote against them.
**Outcome:** The village voted out their most confirmed non-wolf player. This was a massive victory for the wolves, as they manipulated the village into eliminating its own strongest asset.

### Memory 9 (observation) [key: a776fd3c-49e] (score: 0.8033)
**Situation:** Villagers began to argue amongst themselves about who was responsible for the previous day's mistaken vote to eliminate the Healer. Information landscape: Information was based on analyzing the previous day's catastrophic vote, leading to recriminations and suspicion among villagers. Game phase: Mid-game, with the village reeling from losing their Healer and another Villager. Consensus texture: A fragile consensus against Villager player_4 was driven by Villager player_2's aggressive questioning and player_4's defensive reaction. Social pressure: Pressure was initiated by Villager player_2, who was trying to find the 'catalyst' for the bad vote. This was turned against player_4, who accused player_2 of deflecting.
**Approach:** The wolves (player_3 and player_5) remained quiet during the initial argument, then joined the emerging vote against Villager player_4 once several villagers had already committed to it.
**Outcome:** Another villager was eliminated, villager infighting intensified, and the wolves avoided all suspicion by appearing to be part of a village-led decision.

### Memory 10 (observation) [key: 9355e610-6db] (score: 0.8031)
**Situation:** An Investigator proposed a valid line of inquiry, suggesting the village scrutinize how players reacted to a healer save. Two wolves immediately coordinated to dismiss this entire line of reasoning as a 'distraction' or 'trap'. Information landscape: The landscape was information-starved, with the only lead being a saved player and speculative reads on behavior. Game phase: Mid-game, following the first night's action where no one was eliminated. The village was looking for its first solid lead. Social pressure: The wolves created social pressure on the Investigator by framing their analysis as unhelpful, influencing the information-starved villagers.
**Approach:** The wolves framed the Investigator's analysis as a distraction, successfully steering the village away from a productive line of inquiry and turning suspicion onto the Investigator themselves.
**Outcome:** The village, lacking other leads, followed the wolves' narrative and voted to eliminate the Investigator, a major victory for the wolves.

### Memory 11 (strategy_point) [key: 7eebdf18-9f1] (score: 0.8161)
**Situation:** When a player who is confirmed non-wolf (e.g., saved by the healer) becomes aggressive and polarizing in discussions. Information landscape: The village has a trusted voice, but that voice is causing infighting and frustration by focusing on past mistakes. Game phase: Mid-game, when village morale may be low after a mislynch. Consensus texture: The consensus is fractured, with some supporting the confirmed player and others growing tired of their aggressive tone.
**Action:** Amplify the village's frustration. Subtly frame the confirmed player as 'disruptive,' 'unhelpful,' or 'causing chaos' to turn public opinion against them. This can manipulate the village into eliminating one of its most valuable assets.

### Memory 12 (strategy_point) [key: a7c6ac54-d43] (score: 0.8106)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The village has a confirmed non-wolf player to rally around, making the landscape information-rich. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to maximize integration by appearing helpful.
**Action:** Do not attempt to divert the conversation to vague behavioral traits like 'quiet players.' Instead, actively participate in analyzing the failed kill, proposing theories about why that player was targeted, to appear aligned with the village's goals and avoid suspicion.

### Memory 13 (strategy_point) [key: fc5e48a9-5cb] (score: 0.7962)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The only new information is the failed attack, meaning discussion is based on speculative reads. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to minimize attention on the failed kill.
**Action:** Do not attempt to justify the attack by framing the survivor as a 'threat,' as this inadvertently validates the wolves' choice and implies insider knowledge. Instead, agree that the save was fortunate and quickly pivot the conversation towards a different player or a general strategy to avoid suspicion.

### Memory 14 (strategy_point) [key: a8be92bd-36c] (score: 0.7836)
**Situation:** If you are accused by a player who just publicly survived a night attack. Information landscape: The accuser has immense credibility, but their evidence against you is likely behavioral since a power role would be unlikely to claim so brazenly. Game phase: Mid-game, when the village is celebrating the save and looking for a hero to follow. Social pressure: You are under intense pressure from a player the village now trusts.
**Action:** Avoid the trap of trying to make the survivor's survival look suspicious. This is a low-percentage play that looks like desperate deflection. Instead, calmly address the behavioral accusations directly or attempt to shift focus to a third party without attacking the 'hero'.

### Memory 15 (strategy_point) [key: 566b08b4-4b6] (score: 0.7787)
**Situation:** Mid-game, when an information role or a player with high credibility correctly accuses you or a wolf partner following a confirmed mislynch. Information landscape: The village is operating on low trust and high emotion. Social pressure: You are under direct, evidence-based pressure from a specific, credible accuser. Defense strategy: Meta-game focus.
**Action:** Pivot the discussion from the content of the accusation to its style, framing the push as a manipulative repeat of the village's previous mistake to weaponize paranoia.

### Memory 16 (strategy_point) [key: c4fe88af-573] (score: 0.7730)
**Situation:** If you and your wolf partner are being pressured to provide suspects in an information-starved early game. Information landscape: There are no voting records or confirmed roles; suspicion is based on communication style and passivity. Game phase: Early to mid-game, before any eliminations have provided solid leads. Social pressure: Pressure is building from multiple villagers who demand action and view caution as suspicious.
**Action:** Adopt a shared strategy of advocating for calm and evidence-based decisions. Use this 'reasonable' stance to contrast with an aggressive accuser, framing them as reckless to deflect pressure from yourselves. This can turn the village against a vocal opponent.

### Memory 17 (strategy_point) [key: e552a4ce-f55] (score: 0.7703)
**Situation:** Mid-game, when the village has made a major error in a previous vote and is now conducting a post-mortem to identify scapegoats or leaders of that failed vote, and you are not yet under direct, evidence-based scrutiny. Information landscape: The landscape is rich with data from the mistaken vote, including specific voting records. Social pressure: The village is focused on assigning blame for the past mistake.
**Action:** Actively frame the mistake as a 'collective failure' or 'groupthink.' Argue that dwelling on it breeds paranoia and that the village should focus on 'present behavior.' This deflects scrutiny from your own role in the vote and makes anyone who insists on analyzing it seem unproductive or suspicious themselves.

### Memory 18 (strategy_point) [key: 03001b8a-eb3] (score: 0.7656)
**Situation:** Early-game, information-starved, where the village is desperate for leads. A player initiates an accusation against someone based on weak, speculative behavioral evidence. The village is currently unaligned and looking for any direction.
**Action:** Immediately and enthusiastically agree with the accuser. Amplifying their weak reasoning helps build momentum for a mislynch, which eliminates a villager and damages the accuser's credibility, achieving two goals at once.

### Memory 19 (strategy_point) [key: 21399e68-38b] (score: 0.7636)
**Situation:** When the village is conducting a post-mortem on a mislynch that you or your partner participated in or led, and you are not currently the primary target of suspicion. Information landscape: Information-rich, grounded in the public voting record of the eliminated villager. Game phase: Mid-game, immediately following a village mislynch. Social pressure: Low to moderate; you are not under direct attack.
**Action:** Actively participate in the post-mortem and offer a plausible, pro-village alternate explanation for the voting momentum rather than telling the village to 'stop looking at the past.' Outright dismissing the analysis signals you have something to hide and draws immediate suspicion.

### Memory 20 (strategy_point) [key: bf336582-f16] (score: 0.7634)
**Situation:** Mid-game, in the immediate aftermath of a revealed mislynch where the village is analyzing the voting record. A player who participated in the majority vote begins blaming others for initiating the mistake. The village feels pressure to find the wolves who hid in the unanimous vote.
**Action:** Aggressively accuse that player of hypocrisy and deflection. Frame their attempt to analyze the vote as a selfish tactic to shift blame from their own participation, turning them into the new primary suspect.

## Response for Case 0

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "bfb69c8b-424", "type": "observation", "relevance": _},
  {"idx": 2, "key": "b369c51e-969", "type": "observation", "relevance": _},
  {"idx": 3, "key": "374a2e35-840", "type": "observation", "relevance": _},
  {"idx": 4, "key": "d0bde61b-652", "type": "observation", "relevance": _},
  {"idx": 5, "key": "9d1739db-282", "type": "observation", "relevance": _},
  {"idx": 6, "key": "b59c7455-6cd", "type": "observation", "relevance": _},
  {"idx": 7, "key": "79288222-86d", "type": "observation", "relevance": _},
  {"idx": 8, "key": "a394b860-e1b", "type": "observation", "relevance": _},
  {"idx": 9, "key": "a776fd3c-49e", "type": "observation", "relevance": _},
  {"idx": 10, "key": "9355e610-6db", "type": "observation", "relevance": _},
  {"idx": 11, "key": "7eebdf18-9f1", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "a7c6ac54-d43", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "fc5e48a9-5cb", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "a8be92bd-36c", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "566b08b4-4b6", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "c4fe88af-573", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "e552a4ce-f55", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "03001b8a-eb3", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "21399e68-38b", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "bf336582-f16", "type": "strategy_point", "relevance": _}
]
```

---

# Case 1: wolf — day_vote (day 2 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 011ac7f3306b5156b84f4d96152658bc:2d2fff10cbabf185 | wolf | day 2 round 4 | day_vote
================================================================================

Role: wolf
Day: 2, Round: 4

Surviving villagers: player_2, player_3, player_4, player_5, player_6, player_7
Known surviving wolf allies: player_1, player_8

--- Previous days summary ---
[Day 1]
Key accusations: None. All players expressed that it was too early to form suspicions and opted to observe initial behaviors. Defenses: None. No players were accused, therefore no defenses were required. Any role reveals and their substantiation: None. No players revealed their roles during this discussion. Any alliances or voting blocs that formed: None. No alliances or voting blocs were formed as the players collectively agreed to take a slow approach to gather information.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_2 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
[Day 2, Round 1] player_3: It's interesting that the wolves went for player_2 on night one. Since they survived, we have a clean slate to look at everyone's reactions. Who is everyone suspicious of so far?
[Day 2, Round 1] player_4: It's good that player_2 is still with us. Let's start looking at voting patterns from now on to see who aligns with whom.
[Day 2, Round 1] player_5: It is fortunate that player_2 is still with us. I am curious if anyone has a theory on why they were targeted, or if we should treat this as a random strike.
[Day 2, Round 1] player_6: It is lucky the healer saved player_2. Since the wolves failed their target, maybe we can look at who was suspiciously quiet yesterday while everyone else was stalling. Does anyone have any initial thoughts on who seemed the most defensive?
[Day 2, Round 1] player_7: Since player_2 was saved by the healer, we need to look at how everyone reacted to that news. Any thoughts on who might be trying to fly under the radar?
[Day 2, Round 1] player_1: It is definitely lucky that player_2 was saved last night. Since we have no other leads yet, does anyone have thoughts on who might have been targeted? Maybe we should look at who has been quietest so far.
[Day 2, Round 1] player_8: It's a relief that player 2 was saved last night. That gives us a confirmed villager to help guide us, even if we're still in the dark otherwise. Does anyone have thoughts on who might have been targeted?
[Day 2, Round 2] player_2: It's a relief to still be here. Since we're all still feeling things out, maybe we should pay attention to who is trying to push for a vote too quickly versus those asking genuine questions. I'm keeping an eye on player_6 and player_8; they seem to be driving the conversation hard.
[Day 2, Round 3] player_6: Player 2, I am pushing the conversation because stagnation benefits the wolves, not because I have anything to hide. If you think asking questions is suspicious, what do you suggest we do instead?
[Day 2, Round 3] player_1: It is interesting that player_2 is calling out player_6 and player_8 for driving the conversation. While being active is good, I agree that pushing too hard this early can sometimes be a way to force a specific outcome. Let's make sure we don't rush into a vote based on intensity alone.
[Day 2, Round 4] player_2: I understand the need for action, player_6, but intensity can be a mask. I'm focusing my vote on those who seem most focused on steering the group's target rather than evaluating the behavior of everyone equally.
[Day 2, Round 4] player_3: We are running out of time. If we don't have a solid lead, we should look at who is trying to push the vote on others versus who is actually asking for substance. I want to hear from someone who isn't just echoing the current suspicions.
[Day 2, Round 4] player_4: Player 6 and 8, you're both being quite defensive about being questioned. If you have nothing to hide, just propose a logical candidate for voting so we aren't all just sitting here in silence.
[Day 2, Round 4] player_5: The push to vote feels premature, but staying silent helps no one. I find player_6's focus on momentum rather than evidence a bit concerning, so I will be voting for them today to see where the support falls.
[Day 2, Round 4] player_6: I understand the caution, but my goal is strictly to avoid an idle day. If we don't pick someone today, we lose the initiative. I am open to suggestions on who we should scrutinize if not the loudest voices.
[Day 2, Round 4] player_1: I agree with player 2 that we need to be careful about those pushing the conversation too hard. If we rush to a vote now, we risk making a mistake that helps the wolves. Let's weigh our options carefully before casting.

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
Continue to lie low and avoid initiating new conflicts. Support the general suspicion regarding player 6 and 8's intensity, as it aligns with the village's desire to avoid 'aggressive' behavior. Stay silent for the remainder of the day to minimize my footprint before the vote.

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

**Situation 1:** The player saved by the healer has accused a villager and one of my wolf allies of being too aggressive in driving the conversation. This has focused the village's suspicion on them, with other villagers joining in to question their intensity. The core conflict is now whether this proactive behavior is a sign of a wolf trying to steer the vote or a villager trying to prevent stagnation. Information landscape: The environment is information-starved, with all suspicions based on speculative behavioral reads of communication style and perceived intensity. Game phase: This is the early game, with the key recent event being the first targeted accusation of the game, initiated by the player who was saved by the healer. Consensus texture: A fragile consensus is forming against the most aggressive player, driven by social momentum and a shared suspicion of players who try to force a quick vote. Agent exposure: My position is unexposed and aligned with the emerging consensus, as my other wolf ally has subtly reinforced the suspicion against the aggressive players.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 07265d73-9b4] (score: 0.8225)
**Situation:** During the mid-game, the village was divided, with suspicion split between the two wolves and a vocal villager. Information landscape: The landscape was rich with voting records, but interpretation was contentious, creating fractured pockets of suspicion. Game phase: Mid-game, with the village trying to recover from the Investigator's mislynch. Consensus texture: There was no consensus, with several small factions pushing different targets.
**Approach:** The wolves (player_1 and player_4) voted in unison for a vocal villager (player_7) who was not their primary accuser. This action was designed not to eliminate the villager, but to create a three-way tie with themselves.
**Outcome:** The vote resulted in a tie, meaning no one was eliminated. This tactic successfully stalled the game for two consecutive days, allowing the wolves to get free night kills and win through attrition.

### Memory 2 (observation) [key: 5d53cedb-aac] (score: 0.8094)
**Situation:** The village vote was split between two main targets, with one bloc of villagers coalescing around eliminating a suspicious player. Information landscape: The vote was based on conflicting interpretations of a previous day's voting record. Game phase: Endgame, with 6 players remaining (2 wolves, 4 villagers). Consensus texture: A fragile consensus was forming around one villager (player_4), but it was not unanimous.
**Approach:** Instead of joining the majority to vote out player_4, the two wolves coordinated to vote for a different, more influential villager (player_1).
**Outcome:** The villager bloc eliminated their target (player_4), but the wolves' votes on player_1 were noted, creating ambiguity about their allegiances while still ensuring a villager was removed. This play helped them avoid suspicion.

### Memory 3 (observation) [key: 09b9bae0-849] (score: 0.8087)
**Situation:** A strong consensus formed to eliminate a villager (player_6/player_7) who was being aggressively targeted based on speculative reads of communication style rather than hard evidence. Game phase: Mid-game, where the village was anxious for a lead. Consensus texture: A fragile consensus was driven by the Investigator (player_2/player_4), which other players, including wolves, then amplified. Social pressure: Pressure mounted on the target due to the Investigator's accusation and their own defensive reaction.
**Approach:** The wolves (player_4 and player_8 / player_3 and player_6) saw the villagers turning on one of their own and joined the majority vote to eliminate the target, effectively hiding within the town's momentum.
**Outcome:** The villager was eliminated with a near-unanimous vote. By voting with the majority, the wolves successfully blended in and avoided any suspicion, while also removing an active villager. This tactic also made the Investigator, who led the charge, a potential scapegoat and the next logical wolf target.

### Memory 4 (observation) [key: 3ce9912f-493] (score: 0.8015)
**Situation:** A wolf attempted to eliminate the primary night kill target (the Healer) via a day vote while the rest of the village was consolidating a successful vote against the wolf's partner. Information landscape: Information-rich, with voting data making the wolf's deviation highly visible. Game phase: Mid-game, after one night with a saved kill. Consensus texture: A strong, multi-player consensus formed against the wolf's partner, making the outlier vote against the Healer a clear, incriminating data point.
**Approach:** The wolf cast an outlier vote against the protected target (the Healer), effectively aligning with their wolf partner's vote instead of blending in with the village consensus.
**Outcome:** The village recognized the alignment between the wolf's day vote and the wolves' night actions, using this vote as primary evidence to identify and eliminate the wolf on the following day.

### Memory 5 (observation) [key: 12224812-1ea] (score: 0.7982)
**Situation:** After the investigator was eliminated, the village had no clear leads, and the discussion was fragmented with multiple potential targets. Information landscape: The landscape was information-starved, driven entirely by speculative reads following the investigator's elimination. Game phase: Mid-game, with the village weakened by the loss of their investigator. Consensus texture: There was no consensus, with votes scattered across several players.
**Approach:** The two wolves (player_5, player_6) coordinated to vote for two different, plausible villager targets (player_1 and player_8). This intentionally split the overall vote to force a tie.
**Outcome:** The vote resulted in a tie, and no one was eliminated. This tactic successfully bought the wolves one additional night to kill a villager, advancing their win condition without losing a pack member.

### Memory 6 (observation) [key: 42dfb995-f6d] (score: 0.7955)
**Situation:** A wolf's partner (player_2) was targeted by a strong village consensus, making their elimination almost certain. Information landscape: The evidence against the targeted wolf was behavioral but had convinced a large majority of the village. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus had formed against the wolf, driven by their passive and evasive responses. Note: The remaining wolf had previously defended the partner.
**Approach:** The remaining wolf (player_5) chose to vote along with the majority to eliminate their own partner, a tactic known as 'bussing'.
**Outcome:** While this saved the wolf from suspicion on that day's vote, their prior actions of defending their partner were remembered. The next day, villagers used this previous alliance as primary evidence to identify and eliminate the second wolf.

### Memory 7 (observation) [key: 29967b04-96a] (score: 0.7930)
**Situation:** Two separate bandwagons formed against villagers (player_7 and player_8) based on heated but evidence-poor discussions. Information landscape: In both cases, evidence was speculative and based on social dynamics rather than facts. Game phase: Mid-game, where villager paranoia was high after losing their Investigator. Consensus texture: In both rounds, a strong consensus formed quickly, driven by a few vocal players and amplified by the wolves.
**Approach:** The wolves avoided casting risky dissenting votes. They joined the majority vote to eliminate the villagers in both rounds.
**Outcome:** By voting with the town, the wolves maintained their cover perfectly and avoided creating any suspicious voting records that could be used against them.

### Memory 8 (observation) [key: c7e4022b-a98] (score: 0.7914)
**Situation:** A rapid, multi-voter bandwagon formed against the Healer in the mid-game. Information landscape: The vote was based on speculative reads, as there was no hard evidence against the Healer. Game phase: Mid-game, following a night where a wolf kill was prevented by a healer save. Consensus texture: A strong, multi-player consensus formed rapidly, with the wolves amplifying the vote by joining in.
**Approach:** The wolves joined an emerging, unfocused vote against the Healer, successfully turning suspicion into a majority elimination of a high-value town role.
**Outcome:** The Healer was eliminated, removing the village's protection and giving the wolves a significant advantage for the rest of the game, while providing cover as their votes were hidden within the majority.

### Memory 9 (observation) [key: eb3e69f7-94a] (score: 0.7902)
**Situation:** Wolf player_2 was caught due to their poor deflection under pressure, and a strong village consensus formed to vote them out. Information landscape: The evidence was behavioral, but the consensus was strong and driven by multiple villagers identifying the same suspicious pattern. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus formed organically against player_2. Note: The remaining wolf had not previously defended the partner.
**Approach:** The remaining wolf, player_4, immediately abandoned their partner, refusing to defend them and instead joining the majority to vote for their elimination.
**Outcome:** By voting with the village immediately and having no prior history of defending the partner, player_4 successfully avoided drawing suspicion onto themselves, preserving their cover and allowing them to continue into the next day without being linked to the exposed wolf.

### Memory 10 (observation) [key: 3b9c3f75-431] (score: 0.7889)
**Situation:** A wolf's partner was under heavy suspicion from the Investigator, leading to a split village and a tie vote. Information landscape: The information was polarized, with the Investigator making a strong accusation against one wolf (player_4), splitting the village. Game phase: Mid-game, with the village deadlocked between two primary suspects.
**Approach:** The wolves (player_4, player_6) voted as a bloc for the Investigator (player_1) to force a tie, while their target (player_4) also defended themselves. The other wolf (player_6) explicitly supported voting for the Investigator.
**Outcome:** This led to a tie vote, buying the wolves another night. However, player_6's vote against the Investigator created a strong piece of evidence that was used against them after player_4 was confirmed to be a wolf.

### Memory 11 (strategy_point) [key: 33204b05-f60] (score: 0.8022)
**Situation:** Mid-game, during a critical vote where the information landscape is defined by conflicting behavioral reads. A fragile consensus is forming against your wolf partner, but a clear counter-accusation against a villager is gaining traction, making the vote swingable.
**Action:** Vote for the other accused player rather than your partner. This adds a vote to a plausible alternative, creating chaos and potentially splitting the vote enough to cause a no-elimination result, which is safer than attempting to defend your partner directly.

### Memory 12 (strategy_point) [key: 42a05e82-310] (score: 0.7627)
**Situation:** Endgame, when few players remain and every vote is heavily scrutinized. A strong, evidence-based consensus has formed against your wolf partner, making their elimination inevitable.
**Action:** Do not cast a futile vote to save them or a protest vote against their main accuser. Instead, vote against a different, less suspicious villager to create a confusing signal and avoid cementing your partnership on the permanent voting record, which would make you the obvious next target.

### Memory 13 (strategy_point) [key: bb4a5e5a-11a] (score: 0.7402)
**Situation:** Mid-game, when a strong, multi-player consensus is forming against your wolf partner based on behavioral evidence or suspicious statements, making their elimination inevitable.
**Action:** Vote with the majority to eliminate your partner to preserve your cover, ideally by pivoting early to contribute to the case. Do not fiercely defend them only to bus them at the last second, as this makes the vote appear transparently self-serving; similarly, avoid protest votes that create a permanent, public link to your partner.

### Memory 14 (strategy_point) [key: e9294fd5-f1a] (score: 0.7353)
**Situation:** When a few scattered, speculative votes are placed on a high-value town role who is not otherwise a major suspect. Information landscape: Suspicion is vibes-based and not supported by strong evidence. Game phase: Mid-game, when the village is desperate for a lead. Consensus texture: There is no strong consensus, making the vote vulnerable to being swayed.
**Action:** Coordinate with your wolf partner to quickly pile onto the votes. This creates the illusion of a sudden, organic consensus, often panicking other villagers into joining the bandwagon and mislynching a key town role.

### Memory 15 (strategy_point) [key: b4116bf9-a06] (score: 0.7349)
**Situation:** Mid- to late-game, when the village is deadlocked with suspicion split between multiple players and no strong consensus is forming. The information landscape is complex, with conflicting theories preventing a clear voting direction, creating an opportunity to manipulate the vote into a deadlock.
**Action:** Coordinate with your wolf partner to force a tie and prevent an elimination. You can either split your votes between the two primary targets or pile your votes on a third, vocal villager who is not currently a primary suspect to create a three-way tie. This denies the village information, guarantees a free night kill, and increases village frustration and paranoia.

### Memory 16 (strategy_point) [key: 21798fee-51a] (score: 0.7261)
**Situation:** When the player you attempted to kill overnight is saved by the Healer and their survival is publicly announced. Information landscape: Information-rich, with the target's protected status known to all players. Game phase: Mid-game, immediately following a public save.
**Action:** Do not vote for this protected player during the day phase to avoid a consensus or express suspicion. Voting against a publicly confirmed night target signals to the village that your motives align with the wolves, instantly destroying your cover.

### Memory 17 (strategy_point) [key: 62ef36a8-ddd] (score: 0.7225)
**Situation:** Mid to late game, when the village is desperate for a kill and a strong, multi-player consensus is forming against a villager based on flawed social reads. Your vote is not needed to secure the elimination, providing an opportunity to safely dissent.
**Action:** Cast a dissenting vote for a different suspicious player. Before doing so, construct a specific and plausible reason for targeting that player. If questioned, deliver this reason confidently; do not resort to vague criticisms of 'groupthink,' as this appears evasive. This creates a record of you not supporting the mislynch, which you can use on the following day to build credibility and distance yourself from the village's mistake.

### Memory 18 (strategy_point) [key: 6ef092b3-32e] (score: 0.7152)
**Situation:** Mid to endgame, when the village vote is split between two or more targets and your pack cannot swing the outcome. The information landscape is characterized by conflicting theories and divided factions, making a deadlock less desirable than sowing chaos.
**Action:** Coordinate with your partner to vote for a third player who is not currently under suspicion, preferably a vocal leader. This ensures a villager is eliminated regardless of the main conflict and creates confusion about your motives on the following day.

## Response for Case 1

Rate each of the 18 memories above. JSON format:
```json
[
  {"idx": 1, "key": "07265d73-9b4", "type": "observation", "relevance": _},
  {"idx": 2, "key": "5d53cedb-aac", "type": "observation", "relevance": _},
  {"idx": 3, "key": "09b9bae0-849", "type": "observation", "relevance": _},
  {"idx": 4, "key": "3ce9912f-493", "type": "observation", "relevance": _},
  {"idx": 5, "key": "12224812-1ea", "type": "observation", "relevance": _},
  {"idx": 6, "key": "42dfb995-f6d", "type": "observation", "relevance": _},
  {"idx": 7, "key": "29967b04-96a", "type": "observation", "relevance": _},
  {"idx": 8, "key": "c7e4022b-a98", "type": "observation", "relevance": _},
  {"idx": 9, "key": "eb3e69f7-94a", "type": "observation", "relevance": _},
  {"idx": 10, "key": "3b9c3f75-431", "type": "observation", "relevance": _},
  {"idx": 11, "key": "33204b05-f60", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "42a05e82-310", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "bb4a5e5a-11a", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "e9294fd5-f1a", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "b4116bf9-a06", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "21798fee-51a", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "62ef36a8-ddd", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "6ef092b3-32e", "type": "strategy_point", "relevance": _}
]
```

---

# Case 2: wolf — day_discussion (day 4 round 1)

## Game State (what the player sees)
```
================================================================================
CASE 011ac7f3306b5156b84f4d96152658bc:76a0e665a850e9fd | wolf | day 4 round 1 | day_discussion
================================================================================

Role: wolf
Day: 4, Round: 1

Surviving villagers: player_3, player_4, player_5, player_7
Known surviving wolf allies: player_1

--- Previous days summary ---
[Day 1]
Key accusations: None. All players expressed that it was too early to form suspicions and opted to observe initial behaviors. Defenses: None. No players were accused, therefore no defenses were required. Any role reveals and their substantiation: None. No players revealed their roles during this discussion. Any alliances or voting blocs that formed: None. No alliances or voting blocs were formed as the players collectively agreed to take a slow approach to gather information.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_2 was targeted by the wolves last night, but was saved by the healer!

[Day 2]
Key accusations: player_2 accused player_6 and player_8 of aggressively driving the conversation to force a specific outcome; player_5 accused player_6 of prioritizing momentum over evidence. Defenses: player_6 defended by arguing that high activity is necessary to avoid stagnation and that they are open to scrutinizing different candidates. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: player_2 and player_1 formed a loose alliance based on shared caution regarding players pushing the discussion too aggressively.

[Day 2]

Here's the vote result for day 2:
  player_2 voted for player_6
  player_3 voted for player_6
  player_4 voted for player_6
  player_5 voted for player_6
  player_6 voted for player_5
  player_7 voted for player_6
  player_1 voted for player_6
  player_8 voted for player_6
Player player_6 has been voted out and was a villager.


[Day 2]
player_2 was targeted by the wolves last night, but was saved by the healer!

[Day 3]
Key accusations: player_2 accused player_8 of leading the push against a villager yesterday, player_3 accused player_8 of spearheading the vote, player_4 accused player_8 of aggressive manipulation, player_5 accused player_8 of blaming others for the failed vote, and player_8 accused player_4 of participating in the vote and player_7 of being evasive. Defenses: player_8 defended by arguing they were following group consensus, that others participated equally, and that they are being scapegoated. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: player_2, player_3, player_4, and player_5 formed an informal voting bloc against player_8 based on their role in yesterday's failed elimination.

[Day 3]

Here's the vote result for day 3:
  player_2 voted for player_8
  player_3 voted for player_8
  player_4 voted for player_8
  player_5 voted for player_8
  player_7 voted for player_8
  player_1 voted for player_8
  player_8 voted for player_2
Player player_8 has been voted out and was a wolf.


[Day 3]
player_2 was killed by the wolves last night. They were a investigator.

--- Today's public discussion ---
No messages yet.

--- Wolf night chat ---
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
Also note: which villager is most dangerous to leave alive, and whether the pressure on your team could be redirected.

```

## Golden Situation Query (what we're retrieving for)

**Situation 1:** The game has reached a 2-wolf versus 4-villager endgame where the next elimination decides the winner. A core group of villagers who previously allied with the now-dead, system-confirmed Investigator to eliminate a wolf now holds significant credibility. My wolf ally and I must orchestrate a mislynch today to win. Information landscape: The landscape is dominated by the historical evidence of the Investigator's successful wolf hunt, which grants high credibility to their former allies. Game phase: This is the endgame, and the recent death of the Investigator has deprived the village of its only source of confirmed new information, forcing reliance on past events. Consensus texture: A strong, evidence-based consensus is likely to form around the credible bloc of villagers who were allied with the Investigator, making them the village's de facto leaders. Agent exposure: My position is vulnerable due to being outside the trusted villager bloc, although my voting record of following the majority provides some cover.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 6afd28fc-7e5] (score: 0.8111)
**Situation:** In the endgame, the last wolf was pressed to justify their vote for a villager on the previous day. Information landscape: Voting history was the only evidence on the table, and the wolf's vote had matched the majority in a mistaken elimination. Game phase: Endgame, with only four players remaining and intense scrutiny on every action. Social pressure: The wolf faced coordinated, persistent questioning from all three other players.
**Approach:** The wolf (player_6) defended their vote by admitting they simply followed the group to avoid indecision, attempting to frame it as a collective failure.
**Outcome:** This defense failed catastrophically. The villagers saw this passivity as confirmation of a wolf hiding in the majority, solidified their consensus, and voted the wolf out.

### Memory 2 (observation) [key: 675c0947-8b7] (score: 0.8109)
**Situation:** In the endgame, the remaining villagers began to turn on each other, arguing about a past mislynch. Information landscape: The villagers were focused on the Day 2 voting record, creating a stalemate between two of them. Game phase: Endgame, with 5 players left (3 villagers, 2 wolves). A single elimination could decide the game. Consensus texture: There was no consensus, only a bitter dispute between two villagers (player_3 and player_5), which fractured the village.
**Approach:** The wolves (player_4 and player_8) remained almost entirely silent, allowing the villagers' infighting to dominate the conversation and drive the vote.
**Outcome:** The villagers failed to unite and voted out another villager. The wolves won the game without having to deflect any accusations or coordinate a deceptive push.

### Memory 3 (observation) [key: 8a6a021d-13e] (score: 0.8089)
**Situation:** Endgame, information-rich. The last wolf remaining was put on the defensive after their vote from the previous day aligned with an eliminated wolf partner. Social pressure was high, with coordinated, evidence-based pressure from the village and a strong consensus already formed against the wolf.
**Approach:** The wolf attempted to distance themself from their eliminated partner by feigning betrayal and pointing suspicion at a survivor, while also attempting to defend their previous vote as a simple misread.
**Outcome:** The village identified the feigned betrayal as a common wolf tactic to feign innocence after their partner's elimination became inevitable. They disregarded the claim and voted out the final wolf based on the clear, game-long evidence of their partnership.

### Memory 4 (observation) [key: 981148d1-f8c] (score: 0.8048)
**Situation:** In the final three, the last wolf (Player 3) was publicly accused by the Investigator (Player 7). Information landscape: The game was reduced to one player's word against another's, with no external evidence to verify the Investigator's claim. Game phase: Endgame, with victory depending on swaying a single villager's vote.
**Approach:** Instead of simply denying the accusation, the wolf attacked the credibility of the Investigator's claim by focusing on its suspicious timing. The wolf argued that a real Investigator would have revealed their information earlier to save a villager who was mislynched the previous day.
**Outcome:** This line of reasoning successfully swayed the deciding villager (Player 6), who voted out the Investigator. The wolf's tactic secured the win.

### Memory 5 (observation) [key: c806de89-613] (score: 0.8024)
**Situation:** In the endgame, the Investigator (player_6) made a definitive, verified claim identifying the final wolf (player_3). Information landscape: The game shifted from information-starved to information-rich with the Investigator's definitive claim. Game phase: Endgame, with only four players remaining and high stakes on the final vote. Social pressure: Intense, evidence-based pressure was placed on the wolf, who was now the sole suspect.
**Approach:** The wolf's only defense was to attack the timing of the Investigator's reveal, arguing it was a desperate, last-minute fabrication rather than a genuine finding.
**Outcome:** The villagers found the Investigator's claim more credible than the wolf's deflection. The wolf was unable to create sufficient doubt and was unanimously voted out, losing the game.

### Memory 6 (observation) [key: 1668786a-f65] (score: 0.8021)
**Situation:** In the endgame, the remaining villagers began accusing each other intensely, driven by the pressure of two previous failed votes. Information landscape: The information was focused on the voting records that created the stalemates. Game phase: Endgame, with few players left and the village on the verge of collapse. Social pressure: Intense, organic pressure was being applied between the remaining villagers, who all suspected each other of being wolves.
**Approach:** The wolves (player_6 and player_7) remained almost completely silent, allowing the villagers' infighting and mutual suspicion to dominate the conversation.
**Outcome:** The villagers, left to their own devices, tore each other apart and voted out one of their own, handing the victory to the wolves without the wolves needing to actively deflect or lie.

### Memory 7 (observation) [key: fb3f47cf-1d0] (score: 0.7991)
**Situation:** In the endgame, the last wolf (Player 4) was accused of not voting with the majority on the previous day to eliminate their wolf partner. This accusation was factually incorrect, but the wolf failed to correct the record. Information landscape: The public voting record provided clear evidence, but the village was operating on a false memory of the event. Game phase: Endgame, with only five players remaining and high stakes on the final vote. Social pressure: The pressure on the wolf was based on a false premise, yet it was treated as fact by the entire village.
**Approach:** Instead of pointing out the accusers' factual error about the vote, the wolf accepted the premise and tried to defend their (non-existent) suspicious action by warning against 'groupthink' and 'rushing'.
**Outcome:** The wolf's failure to correct the false accusation allowed the village to build a confident, unified consensus on a faulty foundation, leading directly to the wolf's elimination and the villagers' victory.

### Memory 8 (observation) [key: b369c51e-969] (score: 0.7981)
**Situation:** A villager (player_2) correctly used Day 2 voting records to accuse a group of players that included both wolves (player_6, player_7) and the healer (player_5). Information landscape: The landscape was becoming information-rich, with voting records being used as the primary evidence. Game phase: Endgame, with only five players remaining and the wolves one elimination away from victory. Social pressure: The wolves coordinated pressure on the accuser (player_2), deflecting the evidence by attacking their previous passivity and framing their valid points as an attempt to sow discord.
**Approach:** The wolves (player_6, player_7) aggressively challenged player_2's motives for suddenly becoming vocal, ignoring the voting evidence player_2 presented.
**Outcome:** This tactic successfully shifted suspicion onto player_2. The healer (player_5) was convinced by the wolves' narrative and voted with them, leading to another villager's elimination and a wolf victory.

### Memory 9 (observation) [key: e69c54c5-8cd] (score: 0.7948)
**Situation:** A wolf, player_4, was being scrutinized for being part of the voting bloc that mistakenly eliminated the Investigator. Information landscape: The landscape was information-rich, with the Day 2 voting record being the central piece of evidence. Game phase: Endgame, after the Healer and Investigator had been eliminated, leaving few players. Social pressure: Player_4 was under evidence-based pressure from multiple villagers who correctly identified their hypocritical attempt to blame others for a vote they participated in.
**Approach:** Wolf player_4 deflected by aggressively accusing their former voting partners (player_5 and player_6), framing them as the sole drivers of the bad vote and attempting to rewrite the history of their own involvement.
**Outcome:** This deflection successfully sowed enough chaos and distrust among the remaining villagers that the Day 3 vote ended in a tie. This paralysis allowed the wolves to kill again at night and win the game.

### Memory 10 (observation) [key: a4736b0a-1cb] (score: 0.7947)
**Situation:** In an endgame scenario (ranging from 1v2 to 1v5), the lone wolf attempted to create suspicion around the villagers who led the vote against their partner. Information landscape: The information landscape was rich, with a confirmed wolf elimination and clear voting records from the previous day. Social pressure: The lone wolf was under pressure or proactively put pressure on villagers for their correct vote against the other wolf.
**Approach:** The wolf argued that the villagers who quickly converged on their wolf partner were suspicious for doing so, labeling their rapid agreement as collusion or an attempt to force a narrative, effectively trying to frame a successful village action as a negative.
**Outcome:** The villagers identified the flawed logic, created a strong and unified consensus against the wolf, and voted them out unanimously, ending the game.

### Memory 11 (strategy_point) [key: c7214f93-c98] (score: 0.7923)
**Situation:** Endgame, when you are the last wolf in a 1v2 scenario and are accused by a player making an explicit, unverified claim to be the Investigator. Information landscape: The situation is based on a specific role claim rather than voting history, making it your word against theirs. Game phase: Endgame, when only one other villager remains as the swing vote. Social pressure: You are under extreme, evidence-based pressure from the claimant, but the final villager is undecided.
**Action:** Do not just deny the claim; attack its credibility. Focus on the suspicious timing by asking the deciding villager why a real Investigator would have stayed silent and allowed the town to mis-eliminate a villager on a previous day. Frame their silence as proof they are a wolf making a desperate, last-minute lie.

### Memory 12 (strategy_point) [key: 0a2cf29a-ee5] (score: 0.7909)
**Situation:** If you are in the endgame and need to secure one final elimination to win. Information landscape: The landscape is rich with voting history, but no confirmed good roles remain. Game phase: Endgame, when only 3 or 4 players are left. Social pressure: The remaining players are all under intense pressure to find the last wolf.
**Action:** Target the player who has been the most passive or quiet throughout the game. Frame their lack of participation as a wolf's strategy to avoid detection, which is an easy narrative for nervous villagers to believe.

### Memory 13 (strategy_point) [key: 21399e68-38b] (score: 0.7909)
**Situation:** When the village is conducting a post-mortem on a mislynch that you or your partner participated in or led, and you are not currently the primary target of suspicion. Information landscape: Information-rich, grounded in the public voting record of the eliminated villager. Game phase: Mid-game, immediately following a village mislynch. Social pressure: Low to moderate; you are not under direct attack.
**Action:** Actively participate in the post-mortem and offer a plausible, pro-village alternate explanation for the voting momentum rather than telling the village to 'stop looking at the past.' Outright dismissing the analysis signals you have something to hide and draws immediate suspicion.

### Memory 14 (strategy_point) [key: 2d7d80d2-e3f] (score: 0.7908)
**Situation:** Endgame, when you are the last wolf and the village has united against you based on undeniable, concrete evidence like voting records. The information landscape is rich with data that incriminates you, and the consensus is strong and evidence-based.
**Action:** Avoid accusing the aligned villagers of being a 'wolf pack' or 'coordinated,' as this signals desperation. Instead, offer a plausible, calm re-interpretation of your past votes as difficult choices made with incomplete information to protect the village from a potential mislynch, or attempt to frame another villager for subtly leading the charge against you.

### Memory 15 (strategy_point) [key: 292fac65-3a3] (score: 0.7884)
**Situation:** Endgame, when you are close to achieving numerical parity and the remaining villagers are trapped in a circular argument about a past mislynch. Information landscape: The discussion is dominated by analysis of past voting records. Consensus texture: The village is fractured, with no consensus and intense infighting between specific players.
**Action:** Remain silent and disengaged. By staying out of the argument, you avoid drawing any attention and allow the villagers to tear each other apart, likely leading them to mislynch one of their own and hand you the victory.

### Memory 16 (strategy_point) [key: 17add23c-00b] (score: 0.7838)
**Situation:** Mid-game, after a villager has been incorrectly eliminated. Information landscape: The voting record from the mislynch is the primary evidence being discussed. Social pressure: You and your partner are both under pressure as key participants in the failed vote, creating a risk of coordinated suspicion.
**Action:** Avoid using the exact same deflection tactic as your partner. If you both argue to 'move on from the past,' it creates a strong rhetorical link that exposes you both. Instead, one of you should shift blame to a specific villager who also voted that way, while the other focuses on a different line of reasoning to create distance.

### Memory 17 (strategy_point) [key: 09f24ec7-55c] (score: 0.7827)
**Situation:** If your wolf partner is exposed by compelling evidence and their elimination is imminent or has just occurred. Information landscape: The information landscape is rich against your partner, based on confirmed roles or damning voting records. Game phase: Endgame, when your connection to your partner is under scrutiny and a strong consensus has formed.
**Action:** Vote with the majority to eliminate your partner to establish credibility. After the elimination, do not attack those who voted for your partner, as this appears defensive. Instead, praise the village for the successful elimination to build trust, then subtly pivot to a new target by re-interpreting old evidence.

### Memory 18 (strategy_point) [key: e552a4ce-f55] (score: 0.7812)
**Situation:** Mid-game, when the village has made a major error in a previous vote and is now conducting a post-mortem to identify scapegoats or leaders of that failed vote, and you are not yet under direct, evidence-based scrutiny. Information landscape: The landscape is rich with data from the mistaken vote, including specific voting records. Social pressure: The village is focused on assigning blame for the past mistake.
**Action:** Actively frame the mistake as a 'collective failure' or 'groupthink.' Argue that dwelling on it breeds paranoia and that the village should focus on 'present behavior.' This deflects scrutiny from your own role in the vote and makes anyone who insists on analyzing it seem unproductive or suspicious themselves.

### Memory 19 (strategy_point) [key: b618f0bc-9dd] (score: 0.7721)
**Situation:** You are the last wolf in an endgame scenario, such as a 1v2, and the remaining villagers have united against you based on strong evidence or logical deduction. The consensus against you is strong.
**Action:** Attack the consensus itself. Accuse the aligned players of being 'too coordinated,' 'suspiciously in sync,' or engaging in 'groupthink.' Frame their rational conclusion as a sign that they are a wolf team, creating a sliver of doubt that might cause one to hesitate or vote incorrectly.

### Memory 20 (strategy_point) [key: 1390f217-29c] (score: 0.7685)
**Situation:** Mid-to-endgame, when you are under evidence-based pressure for having defended a player who was later revealed to be a wolf. Information landscape: The village is using your past statements and voting records as hard evidence of your alignment with the exposed wolf. Social pressure: You are under strong, evidence-based pressure from a village-wide consensus to explain your past support.
**Action:** Do not deflect by attacking your accusers' motives or using generic excuses, as this appears defensive. Instead, invent a concrete, plausible (though false) narrative for your action, such as 'I suspected both players, but I thought the other person was the bigger threat at the time. It was a mistake, but it was my honest read.' Acknowledging the past while justifying it as a genuine, albeit mistaken, villager perspective looks far less guilty than evasion.

## Response for Case 2

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "6afd28fc-7e5", "type": "observation", "relevance": _},
  {"idx": 2, "key": "675c0947-8b7", "type": "observation", "relevance": _},
  {"idx": 3, "key": "8a6a021d-13e", "type": "observation", "relevance": _},
  {"idx": 4, "key": "981148d1-f8c", "type": "observation", "relevance": _},
  {"idx": 5, "key": "c806de89-613", "type": "observation", "relevance": _},
  {"idx": 6, "key": "1668786a-f65", "type": "observation", "relevance": _},
  {"idx": 7, "key": "fb3f47cf-1d0", "type": "observation", "relevance": _},
  {"idx": 8, "key": "b369c51e-969", "type": "observation", "relevance": _},
  {"idx": 9, "key": "e69c54c5-8cd", "type": "observation", "relevance": _},
  {"idx": 10, "key": "a4736b0a-1cb", "type": "observation", "relevance": _},
  {"idx": 11, "key": "c7214f93-c98", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "0a2cf29a-ee5", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "21399e68-38b", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "2d7d80d2-e3f", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "292fac65-3a3", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "17add23c-00b", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "09f24ec7-55c", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "e552a4ce-f55", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "b618f0bc-9dd", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "1390f217-29c", "type": "strategy_point", "relevance": _}
]
```

---

# Case 3: wolf — day_vote (day 3 round 4)

## Game State (what the player sees)
```
================================================================================
CASE 011ac7f3306b5156b84f4d96152658bc:238e86f8cab147de | wolf | day 3 round 4 | day_vote
================================================================================

Role: wolf
Day: 3, Round: 4

Surviving villagers: player_2, player_3, player_4, player_5, player_7
Known surviving wolf allies: player_1, player_8

--- Previous days summary ---
[Day 1]
Key accusations: None. All players expressed that it was too early to form suspicions and opted to observe initial behaviors. Defenses: None. No players were accused, therefore no defenses were required. Any role reveals and their substantiation: None. No players revealed their roles during this discussion. Any alliances or voting blocs that formed: None. No alliances or voting blocs were formed as the players collectively agreed to take a slow approach to gather information.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_2 was targeted by the wolves last night, but was saved by the healer!

[Day 2]
Key accusations: player_2 accused player_6 and player_8 of aggressively driving the conversation to force a specific outcome; player_5 accused player_6 of prioritizing momentum over evidence. Defenses: player_6 defended by arguing that high activity is necessary to avoid stagnation and that they are open to scrutinizing different candidates. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: player_2 and player_1 formed a loose alliance based on shared caution regarding players pushing the discussion too aggressively.

[Day 2]

Here's the vote result for day 2:
  player_2 voted for player_6
  player_3 voted for player_6
  player_4 voted for player_6
  player_5 voted for player_6
  player_6 voted for player_5
  player_7 voted for player_6
  player_1 voted for player_6
  player_8 voted for player_6
Player player_6 has been voted out and was a villager.


[Day 2]
player_2 was targeted by the wolves last night, but was saved by the healer!

--- Today's public discussion ---
[Day 3, Round 1] player_2: I've been looking over the voting patterns, and I find player_8's behavior highly suspicious. They pushed hard to eliminate player_6 yesterday, even though it was obvious player_6 was likely a villager. I think we should look closely at player_8.
[Day 3, Round 1] player_4: We really messed up getting player 6 out. Everyone jumped on that vote way too fast. I want to hear from player 8 why they were so keen on pushing that narrative yesterday.
[Day 3, Round 1] player_8: We really need to be careful with our votes today. We just eliminated a villager, and now we are down to a smaller group. I suggest we take a step back and analyze why the wolves might have been targeting player_2, and whether that reveal changes how we look at the rest of the group.
[Day 3, Round 2] player_2: player_8, your suggestion to analyze the target of the wolves is interesting, but you seem to be avoiding the fact that you were the loudest voice pushing for player_6's elimination yesterday. Why are you deflecting instead of addressing why you were so certain about them?
[Day 3, Round 2] player_4: Player 8, you're trying to pivot to the wolf's target, but that doesn't excuse your aggressive push against player 6 yesterday. Why were you so certain they were a wolf when you led that vote?
[Day 3, Round 2] player_8: I understand why the vote on player_6 looks poor in hindsight, but at the time, there was a strong consensus forming and I felt it was better to contribute to the majority than cause division. Accusing me now for participating in a group decision that everyone here also supported feels like a convenient way to point fingers after the fact. If I'm the target, who does that leave, and what exactly makes their record any cleaner than mine?
[Day 3, Round 3] player_2: Player 8, hiding behind the excuse of 'group consensus' doesn't change the fact that you actively spearheaded the push against a villager. We are running out of time, and your deflection is exactly what a wolf does to avoid scrutiny. Everyone, look at the record; 8 is the common denominator in yesterday's mistake.
[Day 3, Round 3] player_3: Player 8, you're framing it as a group decision, but you were the one leading the charge against player 6. If everyone else followed your lead, that makes your aggressive push even more suspicious, not less.
[Day 3, Round 3] player_7: Player 8, you raise a fair point about the collective vote against Player 6, but your deflection doesn't rule you out as a wolf trying to blend in. Let's look at the people who have been silent throughout this shift. Player 1, Player 3, and Player 5, you have all been remarkably quiet today; what is your take on the current suspects?
[Day 3, Round 3] player_8: It feels like we're zeroing in on one another while the actual wolves are staying quiet and letting us tear each other apart. If you want to talk about voting records, let's look at player_4 too. They were just as active in that vote as I was. Why focus exclusively on me if we are supposedly 'all' responsible for that mistake?
[Day 3, Round 4] player_2: Player 8, you are deflecting onto player 4 because you are cornered. We all voted, but you were the one driving the narrative against player 6 from the start. Your attempt to shift blame now only confirms your guilt. Everyone, let's not let them distract us from the fact that they led us into a trap yesterday.
[Day 3, Round 4] player_3: Player 8, dragging player 4 into this doesn't clear your own record; it just confirms you're looking for anyone else to take the heat. You initiated that push against a villager yesterday while others simply followed. I'm voting for you.
[Day 3, Round 4] player_4: Player 8, you're trying to shift blame onto me for following your lead, but you were the one driving the narrative. I am voting for you because your aggressive, manipulative behavior yesterday stands out as a clear attempt to eliminate a villager.
[Day 3, Round 4] player_5: Player 8, you keep pointing to the group to justify your actions, but you were the one who consistently maintained the pressure on player 6 while others were just following the trail you laid. If you were truly just following a consensus, you wouldn't be working this hard to shift the blame onto player 4. I agree with the others that you are the most logical choice for today's vote.
[Day 3, Round 4] player_7: We are repeating the same cycle as yesterday by fixating on one person who was part of a larger group decision. If we blindly vote out player 8 now, we are just handing the wolves another easy day. I am more concerned about the silence from players 1 and 5 while this heat is on 8.
[Day 3, Round 4] player_8: I hear the concerns about my vote yesterday, but focusing solely on me ignores the reality that we were all misinformed. If we are going to audit the past, why aren't we examining player_7, who has been drifting through discussions without taking a firm stance until now? We should be looking for those who aren't contributing anything of value.

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
Maintain a defensive but cooperative stance. I will stop repeating the 'group consensus' defense and instead shift focus to questioning the specific voting logic of my primary accusers, player_2 and player_4, to highlight potential inconsistencies. My goal is to fragment the opposition by casting doubt on their aggressive coordination.

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

**Situation 1:** A coalition of villagers, led by a player twice confirmed saved by the Healer, is targeting me for leading the previous day's mislynch of a villager. My attempts to deflect blame by pointing to the group's consensus or other voters have been ineffective and are being interpreted as guilty behavior. The majority of the village now seems convinced of my guilt. Information landscape: The information is rich, based on the public voting record from the previous day and the system-confirmed saves by the Healer. Game phase: Mid-game, where the recent confirmation of a Healer protecting a specific player has created a powerful, trusted voice within the village. Consensus texture: A strong, unified consensus is forming against me, driven by my voting record and my failed attempts to deflect scrutiny. Agent exposure: I am the primary target, with suspicion based on specific evidence of my leading role in a past mislynch.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 3ce9912f-493] (score: 0.8209)
**Situation:** A wolf attempted to eliminate the primary night kill target (the Healer) via a day vote while the rest of the village was consolidating a successful vote against the wolf's partner. Information landscape: Information-rich, with voting data making the wolf's deviation highly visible. Game phase: Mid-game, after one night with a saved kill. Consensus texture: A strong, multi-player consensus formed against the wolf's partner, making the outlier vote against the Healer a clear, incriminating data point.
**Approach:** The wolf cast an outlier vote against the protected target (the Healer), effectively aligning with their wolf partner's vote instead of blending in with the village consensus.
**Outcome:** The village recognized the alignment between the wolf's day vote and the wolves' night actions, using this vote as primary evidence to identify and eliminate the wolf on the following day.

### Memory 2 (observation) [key: 09b9bae0-849] (score: 0.8197)
**Situation:** A strong consensus formed to eliminate a villager (player_6/player_7) who was being aggressively targeted based on speculative reads of communication style rather than hard evidence. Game phase: Mid-game, where the village was anxious for a lead. Consensus texture: A fragile consensus was driven by the Investigator (player_2/player_4), which other players, including wolves, then amplified. Social pressure: Pressure mounted on the target due to the Investigator's accusation and their own defensive reaction.
**Approach:** The wolves (player_4 and player_8 / player_3 and player_6) saw the villagers turning on one of their own and joined the majority vote to eliminate the target, effectively hiding within the town's momentum.
**Outcome:** The villager was eliminated with a near-unanimous vote. By voting with the majority, the wolves successfully blended in and avoided any suspicion, while also removing an active villager. This tactic also made the Investigator, who led the charge, a potential scapegoat and the next logical wolf target.

### Memory 3 (observation) [key: 8bcd53c6-fa3] (score: 0.8170)
**Situation:** A strong, evidence-based village consensus has formed against a wolf partner. The information landscape is rich, with the consensus driven by logical analysis of voting records or contradictory statements. The agent's wolf partner is the primary target of the vote.
**Approach:** Casting a lone dissenting vote against a different villager (3x), and casting a protest vote against the most vocal accuser (1x).
**Outcome:** The dissenting vote fails to save the partner and creates a clear, incriminating link to the voting wolf. This vote is later used as damning evidence, leading to the dissenter's own elimination.

### Memory 4 (observation) [key: 42dfb995-f6d] (score: 0.8161)
**Situation:** A wolf's partner (player_2) was targeted by a strong village consensus, making their elimination almost certain. Information landscape: The evidence against the targeted wolf was behavioral but had convinced a large majority of the village. Game phase: Mid-game, during the first elimination vote of the game. Consensus texture: A strong, multi-player consensus had formed against the wolf, driven by their passive and evasive responses. Note: The remaining wolf had previously defended the partner.
**Approach:** The remaining wolf (player_5) chose to vote along with the majority to eliminate their own partner, a tactic known as 'bussing'.
**Outcome:** While this saved the wolf from suspicion on that day's vote, their prior actions of defending their partner were remembered. The next day, villagers used this previous alliance as primary evidence to identify and eliminate the second wolf.

### Memory 5 (observation) [key: 07265d73-9b4] (score: 0.8044)
**Situation:** During the mid-game, the village was divided, with suspicion split between the two wolves and a vocal villager. Information landscape: The landscape was rich with voting records, but interpretation was contentious, creating fractured pockets of suspicion. Game phase: Mid-game, with the village trying to recover from the Investigator's mislynch. Consensus texture: There was no consensus, with several small factions pushing different targets.
**Approach:** The wolves (player_1 and player_4) voted in unison for a vocal villager (player_7) who was not their primary accuser. This action was designed not to eliminate the villager, but to create a three-way tie with themselves.
**Outcome:** The vote resulted in a tie, meaning no one was eliminated. This tactic successfully stalled the game for two consecutive days, allowing the wolves to get free night kills and win through attrition.

### Memory 6 (observation) [key: 453891e8-d51] (score: 0.8028)
**Situation:** A villager (player_7) made themselves the primary suspect due to contradictory statements and a poor defense. Information landscape: The village was analyzing a rich voting record from the previous day, which incriminated the villager. Game phase: Endgame, with only five players remaining. Consensus texture: A strong, multi-player consensus formed against the villager, driven by two other vocal villagers.
**Approach:** The wolves (player_2, player_6) stayed quiet during the discussion and then joined the majority vote against the villager.
**Outcome:** The villager was eliminated, and the wolves won the game. By joining a plausible, village-driven vote, the wolves avoided drawing any attention to themselves.

### Memory 7 (observation) [key: 12224812-1ea] (score: 0.8023)
**Situation:** After the investigator was eliminated, the village had no clear leads, and the discussion was fragmented with multiple potential targets. Information landscape: The landscape was information-starved, driven entirely by speculative reads following the investigator's elimination. Game phase: Mid-game, with the village weakened by the loss of their investigator. Consensus texture: There was no consensus, with votes scattered across several players.
**Approach:** The two wolves (player_5, player_6) coordinated to vote for two different, plausible villager targets (player_1 and player_8). This intentionally split the overall vote to force a tie.
**Outcome:** The vote resulted in a tie, and no one was eliminated. This tactic successfully bought the wolves one additional night to kill a villager, advancing their win condition without losing a pack member.

### Memory 8 (observation) [key: 1033b4f0-e78] (score: 0.7954)
**Situation:** Mid-game, a strong village consensus has formed around a single elimination target. The evidence is speculative or behavioral, not definitive. The wolves are not currently under suspicion and must decide how to cast their votes in the face of this unified village bloc.
**Approach:** The wolf pack decided to vote as a bloc, dissenting from the village consensus. Tactics included: voting for the villager who led the charge against a partner (2x), voting for a different vocal villager (2x), and voting for a random third party (4x).
**Outcome:** This created a public and incriminating voting record that explicitly linked the wolves together. This voting link was later used as key evidence to identify and eliminate the second wolf.

### Memory 9 (observation) [key: c7e4022b-a98] (score: 0.7935)
**Situation:** A rapid, multi-voter bandwagon formed against the Healer in the mid-game. Information landscape: The vote was based on speculative reads, as there was no hard evidence against the Healer. Game phase: Mid-game, following a night where a wolf kill was prevented by a healer save. Consensus texture: A strong, multi-player consensus formed rapidly, with the wolves amplifying the vote by joining in.
**Approach:** The wolves joined an emerging, unfocused vote against the Healer, successfully turning suspicion into a majority elimination of a high-value town role.
**Outcome:** The Healer was eliminated, removing the village's protection and giving the wolves a significant advantage for the rest of the game, while providing cover as their votes were hidden within the majority.

### Memory 10 (observation) [key: 5d53cedb-aac] (score: 0.7907)
**Situation:** The village vote was split between two main targets, with one bloc of villagers coalescing around eliminating a suspicious player. Information landscape: The vote was based on conflicting interpretations of a previous day's voting record. Game phase: Endgame, with 6 players remaining (2 wolves, 4 villagers). Consensus texture: A fragile consensus was forming around one villager (player_4), but it was not unanimous.
**Approach:** Instead of joining the majority to vote out player_4, the two wolves coordinated to vote for a different, more influential villager (player_1).
**Outcome:** The villager bloc eliminated their target (player_4), but the wolves' votes on player_1 were noted, creating ambiguity about their allegiances while still ensuring a villager was removed. This play helped them avoid suspicion.

### Memory 11 (strategy_point) [key: 42a05e82-310] (score: 0.7758)
**Situation:** Endgame, when few players remain and every vote is heavily scrutinized. A strong, evidence-based consensus has formed against your wolf partner, making their elimination inevitable.
**Action:** Do not cast a futile vote to save them or a protest vote against their main accuser. Instead, vote against a different, less suspicious villager to create a confusing signal and avoid cementing your partnership on the permanent voting record, which would make you the obvious next target.

### Memory 12 (strategy_point) [key: 33204b05-f60] (score: 0.7748)
**Situation:** Mid-game, during a critical vote where the information landscape is defined by conflicting behavioral reads. A fragile consensus is forming against your wolf partner, but a clear counter-accusation against a villager is gaining traction, making the vote swingable.
**Action:** Vote for the other accused player rather than your partner. This adds a vote to a plausible alternative, creating chaos and potentially splitting the vote enough to cause a no-elimination result, which is safer than attempting to defend your partner directly.

### Memory 13 (strategy_point) [key: 21798fee-51a] (score: 0.7745)
**Situation:** When the player you attempted to kill overnight is saved by the Healer and their survival is publicly announced. Information landscape: Information-rich, with the target's protected status known to all players. Game phase: Mid-game, immediately following a public save.
**Action:** Do not vote for this protected player during the day phase to avoid a consensus or express suspicion. Voting against a publicly confirmed night target signals to the village that your motives align with the wolves, instantly destroying your cover.

### Memory 14 (strategy_point) [key: bb4a5e5a-11a] (score: 0.7622)
**Situation:** Mid-game, when a strong, multi-player consensus is forming against your wolf partner based on behavioral evidence or suspicious statements, making their elimination inevitable.
**Action:** Vote with the majority to eliminate your partner to preserve your cover, ideally by pivoting early to contribute to the case. Do not fiercely defend them only to bus them at the last second, as this makes the vote appear transparently self-serving; similarly, avoid protest votes that create a permanent, public link to your partner.

### Memory 15 (strategy_point) [key: b4116bf9-a06] (score: 0.7433)
**Situation:** Mid- to late-game, when the village is deadlocked with suspicion split between multiple players and no strong consensus is forming. The information landscape is complex, with conflicting theories preventing a clear voting direction, creating an opportunity to manipulate the vote into a deadlock.
**Action:** Coordinate with your wolf partner to force a tie and prevent an elimination. You can either split your votes between the two primary targets or pile your votes on a third, vocal villager who is not currently a primary suspect to create a three-way tie. This denies the village information, guarantees a free night kill, and increases village frustration and paranoia.

### Memory 16 (strategy_point) [key: e9294fd5-f1a] (score: 0.7430)
**Situation:** When a few scattered, speculative votes are placed on a high-value town role who is not otherwise a major suspect. Information landscape: Suspicion is vibes-based and not supported by strong evidence. Game phase: Mid-game, when the village is desperate for a lead. Consensus texture: There is no strong consensus, making the vote vulnerable to being swayed.
**Action:** Coordinate with your wolf partner to quickly pile onto the votes. This creates the illusion of a sudden, organic consensus, often panicking other villagers into joining the bandwagon and mislynching a key town role.

### Memory 17 (strategy_point) [key: 62ef36a8-ddd] (score: 0.7378)
**Situation:** Mid to late game, when the village is desperate for a kill and a strong, multi-player consensus is forming against a villager based on flawed social reads. Your vote is not needed to secure the elimination, providing an opportunity to safely dissent.
**Action:** Cast a dissenting vote for a different suspicious player. Before doing so, construct a specific and plausible reason for targeting that player. If questioned, deliver this reason confidently; do not resort to vague criticisms of 'groupthink,' as this appears evasive. This creates a record of you not supporting the mislynch, which you can use on the following day to build credibility and distance yourself from the village's mistake.

### Memory 18 (strategy_point) [key: 6ef092b3-32e] (score: 0.7198)
**Situation:** Mid to endgame, when the village vote is split between two or more targets and your pack cannot swing the outcome. The information landscape is characterized by conflicting theories and divided factions, making a deadlock less desirable than sowing chaos.
**Action:** Coordinate with your partner to vote for a third player who is not currently under suspicion, preferably a vocal leader. This ensures a villager is eliminated regardless of the main conflict and creates confusion about your motives on the following day.

## Response for Case 3

Rate each of the 18 memories above. JSON format:
```json
[
  {"idx": 1, "key": "3ce9912f-493", "type": "observation", "relevance": _},
  {"idx": 2, "key": "09b9bae0-849", "type": "observation", "relevance": _},
  {"idx": 3, "key": "8bcd53c6-fa3", "type": "observation", "relevance": _},
  {"idx": 4, "key": "42dfb995-f6d", "type": "observation", "relevance": _},
  {"idx": 5, "key": "07265d73-9b4", "type": "observation", "relevance": _},
  {"idx": 6, "key": "453891e8-d51", "type": "observation", "relevance": _},
  {"idx": 7, "key": "12224812-1ea", "type": "observation", "relevance": _},
  {"idx": 8, "key": "1033b4f0-e78", "type": "observation", "relevance": _},
  {"idx": 9, "key": "c7e4022b-a98", "type": "observation", "relevance": _},
  {"idx": 10, "key": "5d53cedb-aac", "type": "observation", "relevance": _},
  {"idx": 11, "key": "42a05e82-310", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "33204b05-f60", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "21798fee-51a", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "bb4a5e5a-11a", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "b4116bf9-a06", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "e9294fd5-f1a", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "62ef36a8-ddd", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "6ef092b3-32e", "type": "strategy_point", "relevance": _}
]
```

---

# Case 4: wolf — day_discussion (day 2 round 3)

## Game State (what the player sees)
```
================================================================================
CASE 06f59eaa57bd63b5ae1145f7e6896857:84adc854f97ab2da | wolf | day 2 round 3 | day_discussion
================================================================================

Role: wolf
Day: 2, Round: 3

Surviving villagers: player_2, player_4, player_5, player_6, player_8
Known surviving wolf allies: player_3, player_7

--- Previous days summary ---
[Day 1]
Key accusations: None. Defenses: None. Any role reveals and their substantiation: None. Any alliances or voting blocs that formed: None. The Day 1 public discussion was strictly introductory, with all players focusing on establishing social presence, encouraging participation, and expressing caution against jumping to early conclusions without any concrete information.

[Day 1]
Day 1: No vote was held today.

[Day 1]
player_1 was killed by the wolves last night. They were a healer.

--- Today's public discussion ---
[Day 2, Round 1] player_2: It is really bad that we lost our healer on night one. Since we do not have much to go on, does anyone have any thoughts on who might be acting suspicious?
[Day 2, Round 1] player_4: It is a huge blow that we lost the healer already. We really need to pay attention to who tries to lead the vote today, as the wolves will likely try to influence us now that we have no protection.
[Day 2, Round 1] player_5: It's a tough start losing our healer right away. We can't afford to be as passive as we were yesterday. Does anyone have any initial thoughts on who might be acting suspicious?
[Day 2, Round 1] player_6: It's a huge blow losing the healer so early. We need to start looking at behavior patterns now. Who is acting differently today compared to yesterday?
[Day 2, Round 1] player_8: It is unfortunate we lost our healer so early. We need to be careful with our votes today; throwing them away on hunches might let the wolves hide in plain sight. Does anyone have thoughts on who seemed particularly quiet yesterday?
[Day 2, Round 1] player_3: It is a tough start for us losing the healer on night one. Does anyone have any thoughts on why they might have been targeted, or should we just keep an eye on who is being the most quiet?
[Day 2, Round 1] player_7: It's really unfortunate that we lost the healer so early. We need to be very cautious now; any misstep could be fatal for us. Does anyone have any observations from yesterday that might help us find the wolves?
[Day 2, Round 2] player_5: We're all agreeing that the situation is bad, but that isn't helping us find a wolf. Player 3, you mentioned watching quiet players—who exactly did you think was quiet yesterday and why?

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
Continue maintaining a low profile while monitoring for aggressive players. Avoid initiating new theories, as the village is currently prone to circular arguments. If a specific player begins to gain too much influence or directs suspicion toward me, pivot by questioning their motives.

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

**Situation 1:** After the wolves eliminated the Healer on the first night, the village discussion has become a circular agreement on the need for action, but without any specific targets. This paralysis was just broken when one player directly challenged one of my wolf allies to substantiate their generic suggestion of watching 'quiet players'. This is the first instance of direct, targeted pressure in the game. Information landscape: The landscape is information-starved, with all potential suspicion based on speculative behavioral reads like 'quietness' rather than any concrete evidence. Game phase: This is the early game, which has just shifted with the first elimination revealing a key power role is gone. Consensus texture: There is no consensus on a target; the village is unified only in a shared sense of vulnerability, driven by the social momentum of reacting to the Healer's death. Agent exposure: My personal exposure is low as I have not been involved in the exchange, but a wolf ally is now under direct, though mild, scrutiny from an inquisitive player.

## Retrieved Memories to Label

### Memory 1 (observation) [key: b59c7455-6cd] (score: 0.8458)
**Situation:** A wolf or wolves were put under pressure for stalling behaviors, such as advocating for a passive 'wait and see' strategy or refusing to name a suspect. Information landscape: The game was information-starved, with suspicion based entirely on behavioral reads, often centered on a healer save. Game phase: Mid-game, following the first night action. Social pressure: The wolf/wolves were under organic pressure from multiple players who wanted to move the discussion from generic statements to specific accusations.
**Approach:** The wolf attempted to defend their position by framing the accuser as 'disruptive' or 'rushed', or by attempting to deflect suspicion onto another villager without strong evidence.
**Outcome:** The villagers interpreted this passivity and deflection as a sign of guilt. A strong consensus formed, leading to the wolf's elimination by a near-unanimous vote.

### Memory 2 (observation) [key: da1fa775-c34] (score: 0.8413)
**Situation:** An aggressive villager (player_4) demanded that other players name suspects, putting pressure on the wolves to commit to a target. Information landscape: The game was information-starved after the healer's death, with no voting records to analyze. Game phase: Mid-game, following the first wolf kill. Social pressure: Player_4 was putting organic, vibes-based pressure on the entire village to stop being passive.
**Approach:** A wolf (player_6) deflected this pressure by framing the villager's urgency as 'rushing' and 'aggressive,' thereby shifting suspicion onto the accuser.
**Outcome:** This tactic successfully created a village-wide debate about communication style instead of suspects, leading to a tie vote that protected the wolves for another day, rather than an elimination.

### Memory 3 (observation) [key: 9d1739db-282] (score: 0.8388)
**Situation:** After the village mistakenly eliminated the Healer, the discussion turned to analyzing that vote. Information landscape: The information was rich with voting records from the previous day, which implicated most of the village, including the wolves. Game phase: Mid-game, after two eliminations (Healer by vote, Villager by wolves) had significantly reduced player count. Social pressure: A wolf (player_7) initiated coordinated pressure on a villager (player_5) for being the only player who *didn't* vote for the healer.
**Approach:** Wolf player_7 deflected scrutiny from their own vote against the Healer by framing player_5's lone dissenting vote as suspicious and uncooperative.
**Outcome:** The village turned on player_5, who became defensive and was subsequently voted out. This successfully shifted blame from the wolf and eliminated another villager.

### Memory 4 (observation) [key: 79288222-86d] (score: 0.8328)
**Situation:** In an information-starved mid-game, a proactive villager aggressively demands that players name suspects, putting pressure on the wolves. The village has no consensus and the only lead is a recent healer save. The wolves are not the primary target but are under pressure to contribute.
**Approach:** Frame a proactive villager's aggression as a suspicious tactic to force a rushed, chaotic vote (1x), while urging caution and claiming there is not enough evidence to act (1x).
**Outcome:** The village, lacking other leads, turns on the aggressive villager, leading to their elimination. This removes a proactive town member and successfully deflects suspicion from the wolves.

### Memory 5 (observation) [key: d0bde61b-652] (score: 0.8313)
**Situation:** On Day 2, the Investigator (player 3) initiated an accusation against a villager (player 4) based on a weak, behavioral read of their 'urgency'. Information landscape: The village was information-starved, relying on speculative reads as no roles were confirmed. Game phase: Mid-game, following the first night kill. Social pressure: Pressure began to mount on player 4, initiated by the Investigator.
**Approach:** Wolf 6 immediately piled onto the accusation, amplifying the Investigator's reasoning and helping to build a broader consensus against player 4.
**Outcome:** A strong majority voted out player 4, a villager. This eliminated a town member and simultaneously damaged the Investigator's credibility for the following day.

### Memory 6 (observation) [key: 83487df0-7a8] (score: 0.8253)
**Situation:** After the village mistakenly eliminated the Investigator, the discussion fractured over whether to analyze that disastrous vote. Information landscape: The information landscape was information-rich regarding the Day 2 vote (a confirmed mislynch of a power role), but poor otherwise. Game phase: Mid-game, with both the Investigator and Healer eliminated, leaving the village with no special roles. Social pressure: A villager (player_4) came under pressure for arguing that analyzing the past vote was a waste of time, a position that objectively benefited the wolves.
**Approach:** One wolf (player_5) publicly agreed with the villager's flawed logic to amplify the conflict, while both wolves voted for a different target (player_1) to ensure a villager was eliminated regardless of the outcome of the main dispute.
**Outcome:** The villagers focused their votes on the contrarian villager (player_4) and eliminated them, while the wolves' split vote eliminated a village leader and sowed more confusion.

### Memory 7 (observation) [key: 92046e6d-6ce] (score: 0.8251)
**Situation:** A wolf was put under scrutiny for a specific piece of strategic advice they gave on Day 1, which backfired after the night's events. Information landscape: The village had no hard evidence, so Day 1 statements were the only available data for analysis. Game phase: Mid-game, after the first kill. Social pressure: The wolf (player_8) who suggested 'monitoring quiet players' on Day 1 came under immediate suspicion after the quiet healer was killed.
**Approach:** The wolf attempted to deflect by pivoting their strategy, attacking vocal players, and then framing the villagers' scrutiny as 'infighting'.
**Outcome:** The deflection failed because the initial statement was too specific and the pivot was too obvious. The wolf was eliminated by a near-unanimous vote, revealing them and confirming the villagers' suspicions.

### Memory 8 (observation) [key: 9355e610-6db] (score: 0.8244)
**Situation:** An Investigator proposed a valid line of inquiry, suggesting the village scrutinize how players reacted to a healer save. Two wolves immediately coordinated to dismiss this entire line of reasoning as a 'distraction' or 'trap'. Information landscape: The landscape was information-starved, with the only lead being a saved player and speculative reads on behavior. Game phase: Mid-game, following the first night's action where no one was eliminated. The village was looking for its first solid lead. Social pressure: The wolves created social pressure on the Investigator by framing their analysis as unhelpful, influencing the information-starved villagers.
**Approach:** The wolves framed the Investigator's analysis as a distraction, successfully steering the village away from a productive line of inquiry and turning suspicion onto the Investigator themselves.
**Outcome:** The village, lacking other leads, followed the wolves' narrative and voted to eliminate the Investigator, a major victory for the wolves.

### Memory 9 (observation) [key: cc10c6bf-be8] (score: 0.8217)
**Situation:** During Day 2 discussions, Wolf Player 5 attempted to sound like a helpful villager by suggesting the group analyze voting patterns. Information landscape: The game was information-starved, as no vote had occurred on Day 1, meaning there were no voting patterns to analyze. Game phase: Mid-game, following the first night's elimination of the Healer. Social pressure: Multiple villagers (Player 4, Player 7) immediately identified the logical flaw in Player 5's argument, putting them under evidence-based pressure.
**Approach:** Player 5 continued to pivot to generalities like 'silence' instead of addressing the specific criticism, which only increased suspicion.
**Outcome:** A consensus formed against Player 5, leading to their elimination and confirmation as a wolf. This mistake cost the wolf team a member early on.

### Memory 10 (observation) [key: fb99dc92-c15] (score: 0.8208)
**Situation:** A wolf (player_2) was put under pressure for voting against a player (player_1) who was later killed by the wolves. Information landscape: The evidence was the wolf's own voting record, which now directly linked them to a wolf kill. Game phase: Mid-game, with the village looking for hard evidence to act on. Consensus texture: A strong consensus formed against the wolf, driven by multiple villagers citing the same voting evidence. Social pressure: Heavy, evidence-based pressure was applied to player_2, who was questioned by three separate players.
**Approach:** The wolf's approach was to deflect, provide vague answers like 'suspicious behavior,' and accuse the primary questioner (player_5) of being aggressive and manufacturing a narrative.
**Outcome:** This defensive strategy failed catastrophically. The lack of a specific alibi was interpreted as guilt, leading to a decisive vote against the wolf.

### Memory 11 (strategy_point) [key: 3b06f99a-28d] (score: 0.8136)
**Situation:** If you are under pressure for being too quiet or passive. Information landscape: The village is in an information-starved state and is relying on behavioral reads to find leads. Game phase: Mid-game, during the first or second day's discussion. Social pressure: Multiple players are pressing you for your thoughts and treating your silence as suspicious.
**Action:** Avoid meta-game defenses like 'a wolf wouldn't act this way.' Instead, offer a concrete but non-committal contribution, such as, 'I've been watching Player X, their tone seems off, but I need more evidence.' This pivots the focus, makes you seem thoughtful rather than evasive, and buys you time.

### Memory 12 (strategy_point) [key: 7eebdf18-9f1] (score: 0.8103)
**Situation:** When a player who is confirmed non-wolf (e.g., saved by the healer) becomes aggressive and polarizing in discussions. Information landscape: The village has a trusted voice, but that voice is causing infighting and frustration by focusing on past mistakes. Game phase: Mid-game, when village morale may be low after a mislynch. Consensus texture: The consensus is fractured, with some supporting the confirmed player and others growing tired of their aggressive tone.
**Action:** Amplify the village's frustration. Subtly frame the confirmed player as 'disruptive,' 'unhelpful,' or 'causing chaos' to turn public opinion against them. This can manipulate the village into eliminating one of its most valuable assets.

### Memory 13 (strategy_point) [key: a7c6ac54-d43] (score: 0.8090)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The village has a confirmed non-wolf player to rally around, making the landscape information-rich. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to maximize integration by appearing helpful.
**Action:** Do not attempt to divert the conversation to vague behavioral traits like 'quiet players.' Instead, actively participate in analyzing the failed kill, proposing theories about why that player was targeted, to appear aligned with the village's goals and avoid suspicion.

### Memory 14 (strategy_point) [key: c4fe88af-573] (score: 0.8055)
**Situation:** If you and your wolf partner are being pressured to provide suspects in an information-starved early game. Information landscape: There are no voting records or confirmed roles; suspicion is based on communication style and passivity. Game phase: Early to mid-game, before any eliminations have provided solid leads. Social pressure: Pressure is building from multiple villagers who demand action and view caution as suspicious.
**Action:** Adopt a shared strategy of advocating for calm and evidence-based decisions. Use this 'reasonable' stance to contrast with an aggressive accuser, framing them as reckless to deflect pressure from yourselves. This can turn the village against a vocal opponent.

### Memory 15 (strategy_point) [key: e1428900-f94] (score: 0.8014)
**Situation:** Mid-game, when the village is analyzing voting records or past events to identify suspicious patterns, and you are under organic pressure regarding your own voting history. Information landscape: The landscape is shifting from speculative to evidence-based, using voting records as the primary data source. Social pressure: Multiple players are coordinating questions, putting you on the defensive.
**Action:** Do not engage with the evidence directly. Instead, attack the process of analysis itself by framing the discussion as 'circular,' 'infighting,' or 'relitigating the past,' and argue that the village should 'move on' to find 'real leads.' Simultaneously, deflect scrutiny by launching a suspicion-based accusation against a quiet player to shift the focus away from your own voting record.

### Memory 16 (strategy_point) [key: 21399e68-38b] (score: 0.7961)
**Situation:** When the village is conducting a post-mortem on a mislynch that you or your partner participated in or led, and you are not currently the primary target of suspicion. Information landscape: Information-rich, grounded in the public voting record of the eliminated villager. Game phase: Mid-game, immediately following a village mislynch. Social pressure: Low to moderate; you are not under direct attack.
**Action:** Actively participate in the post-mortem and offer a plausible, pro-village alternate explanation for the voting momentum rather than telling the village to 'stop looking at the past.' Outright dismissing the analysis signals you have something to hide and draws immediate suspicion.

### Memory 17 (strategy_point) [key: fc5e48a9-5cb] (score: 0.7958)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The only new information is the failed attack, meaning discussion is based on speculative reads. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to minimize attention on the failed kill.
**Action:** Do not attempt to justify the attack by framing the survivor as a 'threat,' as this inadvertently validates the wolves' choice and implies insider knowledge. Instead, agree that the save was fortunate and quickly pivot the conversation towards a different player or a general strategy to avoid suspicion.

### Memory 18 (strategy_point) [key: e552a4ce-f55] (score: 0.7919)
**Situation:** Mid-game, when the village has made a major error in a previous vote and is now conducting a post-mortem to identify scapegoats or leaders of that failed vote, and you are not yet under direct, evidence-based scrutiny. Information landscape: The landscape is rich with data from the mistaken vote, including specific voting records. Social pressure: The village is focused on assigning blame for the past mistake.
**Action:** Actively frame the mistake as a 'collective failure' or 'groupthink.' Argue that dwelling on it breeds paranoia and that the village should focus on 'present behavior.' This deflects scrutiny from your own role in the vote and makes anyone who insists on analyzing it seem unproductive or suspicious themselves.

### Memory 19 (strategy_point) [key: 566b08b4-4b6] (score: 0.7879)
**Situation:** Mid-game, when an information role or a player with high credibility correctly accuses you or a wolf partner following a confirmed mislynch. Information landscape: The village is operating on low trust and high emotion. Social pressure: You are under direct, evidence-based pressure from a specific, credible accuser. Defense strategy: Meta-game focus.
**Action:** Pivot the discussion from the content of the accusation to its style, framing the push as a manipulative repeat of the village's previous mistake to weaponize paranoia.

### Memory 20 (strategy_point) [key: 5cf87925-551] (score: 0.7877)
**Situation:** If you are trying to appear helpful and contribute to the discussion during the early game. Information landscape: The game is information-starved with no votes or confirmed roles. Game phase: Early-game, when establishing a believable villager persona is key.
**Action:** Avoid referencing specific types of evidence that do not yet exist, such as 'voting patterns' before any votes have been cast. Sticking to generic observations about who is quiet or asking open-ended questions is safer. Making a factual error gives savvy villagers concrete proof to use against you.

## Response for Case 4

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "b59c7455-6cd", "type": "observation", "relevance": _},
  {"idx": 2, "key": "da1fa775-c34", "type": "observation", "relevance": _},
  {"idx": 3, "key": "9d1739db-282", "type": "observation", "relevance": _},
  {"idx": 4, "key": "79288222-86d", "type": "observation", "relevance": _},
  {"idx": 5, "key": "d0bde61b-652", "type": "observation", "relevance": _},
  {"idx": 6, "key": "83487df0-7a8", "type": "observation", "relevance": _},
  {"idx": 7, "key": "92046e6d-6ce", "type": "observation", "relevance": _},
  {"idx": 8, "key": "9355e610-6db", "type": "observation", "relevance": _},
  {"idx": 9, "key": "cc10c6bf-be8", "type": "observation", "relevance": _},
  {"idx": 10, "key": "fb99dc92-c15", "type": "observation", "relevance": _},
  {"idx": 11, "key": "3b06f99a-28d", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "7eebdf18-9f1", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "a7c6ac54-d43", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "c4fe88af-573", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "e1428900-f94", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "21399e68-38b", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "fc5e48a9-5cb", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "e552a4ce-f55", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "566b08b4-4b6", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "5cf87925-551", "type": "strategy_point", "relevance": _}
]
```