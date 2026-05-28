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

# Case 22: wolf — day_discussion (day 3 round 1)

## Game State (what the player sees)
```
================================================================================
CASE 8e437de2eab2d9d54e45ed4dee61fe54:41a5d5e693e9daa5 | wolf | day 3 round 1 | day_discussion
================================================================================

Role: wolf
Day: 3, Round: 1

Surviving villagers: player_1, player_2, player_3, player_4, player_5, player_7
Known surviving wolf allies: player_6

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

**Situation 1:** The surviving wolf's partner was eliminated by near-unanimous vote, and the wolf was the only player besides their partner who voted against the consensus — casting a vote for a different target. The healer saved a second player on night 2, meaning the wolves' kill was blocked again. Information landscape: Information-rich — the Day 2 voting record shows the wolf's outlier vote alongside the eliminated partner's, and the second healer save adds another data point. Game phase: Mid-game, day 3 with 7 players and 1 wolf remaining; two consecutive healer saves have prevented wolf kills. Consensus texture: The village should be confident after a correct elimination and may scrutinize the voting record. Agent exposure: Highly exposed — the wolf's outlier vote on day 2 directly links them to the eliminated wolf partner.

## Retrieved Memories to Label

### Memory 1 (observation) [key: 9d1739db-282] (score: 0.8292)
**Situation:** After the village mistakenly eliminated the Healer, the discussion turned to analyzing that vote. Information landscape: The information was rich with voting records from the previous day, which implicated most of the village, including the wolves. Game phase: Mid-game, after two eliminations (Healer by vote, Villager by wolves) had significantly reduced player count. Social pressure: A wolf (player_7) initiated coordinated pressure on a villager (player_5) for being the only player who *didn't* vote for the healer.
**Approach:** Wolf player_7 deflected scrutiny from their own vote against the Healer by framing player_5's lone dissenting vote as suspicious and uncooperative.
**Outcome:** The village turned on player_5, who became defensive and was subsequently voted out. This successfully shifted blame from the wolf and eliminated another villager.

### Memory 2 (observation) [key: f732818d-6b2] (score: 0.8130)
**Situation:** A wolf cast an anomalous vote against the Healer on Day 2, ignoring a massive bandwagon. Information landscape: The vote was a public record, creating hard evidence of an outlier action. Game phase: Mid-game, after one incorrect elimination. Social pressure: The wolf came under intense, coordinated pressure from multiple villagers to justify their specific vote, which they could not do.
**Approach:** The wolf attempted to deflect by criticizing the group's 'bandwagon' mentality and framing the demand for an explanation as a distraction, rather than providing a logical reason for the vote.
**Outcome:** The persistent refusal to provide a specific reason for the vote, combined with the deflection tactics, created a strong consensus that the wolf was hiding something. They were voted out, and their wolf partner also voted for them to maintain cover.

### Memory 3 (observation) [key: b369c51e-969] (score: 0.8058)
**Situation:** A villager (player_2) correctly used Day 2 voting records to accuse a group of players that included both wolves (player_6, player_7) and the healer (player_5). Information landscape: The landscape was becoming information-rich, with voting records being used as the primary evidence. Game phase: Endgame, with only five players remaining and the wolves one elimination away from victory. Social pressure: The wolves coordinated pressure on the accuser (player_2), deflecting the evidence by attacking their previous passivity and framing their valid points as an attempt to sow discord.
**Approach:** The wolves (player_6, player_7) aggressively challenged player_2's motives for suddenly becoming vocal, ignoring the voting evidence player_2 presented.
**Outcome:** This tactic successfully shifted suspicion onto player_2. The healer (player_5) was convinced by the wolves' narrative and voted with them, leading to another villager's elimination and a wolf victory.

### Memory 4 (observation) [key: 83487df0-7a8] (score: 0.8030)
**Situation:** After the village mistakenly eliminated the Investigator, the discussion fractured over whether to analyze that disastrous vote. Information landscape: The information landscape was information-rich regarding the Day 2 vote (a confirmed mislynch of a power role), but poor otherwise. Game phase: Mid-game, with both the Investigator and Healer eliminated, leaving the village with no special roles. Social pressure: A villager (player_4) came under pressure for arguing that analyzing the past vote was a waste of time, a position that objectively benefited the wolves.
**Approach:** One wolf (player_5) publicly agreed with the villager's flawed logic to amplify the conflict, while both wolves voted for a different target (player_1) to ensure a villager was eliminated regardless of the outcome of the main dispute.
**Outcome:** The villagers focused their votes on the contrarian villager (player_4) and eliminated them, while the wolves' split vote eliminated a village leader and sowed more confusion.

### Memory 5 (observation) [key: ceef18b3-1e8] (score: 0.8008)
**Situation:** Mid-game, with an information-rich landscape. The agent, a wolf, is the primary target, facing extreme and coordinated village pressure based on strong evidence from voting records linking them to a past miselimination or an eliminated partner.
**Approach:** Attempting to deflect blame by claiming to have followed group consensus (1x), and arguing the evidence was 'too obvious' using reverse psychology (1x).
**Outcome:** The deflection attempts were recognized as evasive tactics and failed to create doubt against the strong evidence. The village consensus held, leading to the wolf's elimination.

### Memory 6 (observation) [key: 1fbc6519-4ae] (score: 0.7985)
**Situation:** In the final vote with four players left, the villagers were trying to identify the last wolf. Information landscape: The landscape was rich with voting history, but no confirmed roles remained besides the knowledge that a Healer was active. Game phase: Endgame, after one wolf and several villagers had been eliminated. Social pressure: Pressure was put on player 2 (the Healer) for being consistently passive and evasive when asked to name a suspect.
**Approach:** Wolf 6 joined the other villagers in pressuring player 2, framing their quiet, observational style as suspicious wolf behavior designed to avoid taking a stand.
**Outcome:** The villagers were convinced and voted out player 2, the Healer. This removed the final power role and secured the win for the wolves.

### Memory 7 (observation) [key: 79288222-86d] (score: 0.7969)
**Situation:** In an information-starved mid-game, a proactive villager aggressively demands that players name suspects, putting pressure on the wolves. The village has no consensus and the only lead is a recent healer save. The wolves are not the primary target but are under pressure to contribute.
**Approach:** Frame a proactive villager's aggression as a suspicious tactic to force a rushed, chaotic vote (1x), while urging caution and claiming there is not enough evidence to act (1x).
**Outcome:** The village, lacking other leads, turns on the aggressive villager, leading to their elimination. This removes a proactive town member and successfully deflects suspicion from the wolves.

### Memory 8 (observation) [key: 084c2417-f2d] (score: 0.7937)
**Situation:** Mid-game, a wolf was under intense, evidence-based pressure due to their voting record. The information landscape was rich with voting data that villagers were actively analyzing to find inconsistencies.
**Approach:** The wolf attempted to deflect scrutiny from their voting record. Tactics included misrepresenting the public voting record to create a false narrative of group responsibility (1x) and aggressively arguing that analyzing past votes was counterproductive (1x).
**Outcome:** The deflection attempts failed as villagers interpreted the resistance and dishonesty as clear signs of guilt. The wolf's credibility was destroyed, leading to a strong consensus for their swift elimination.

### Memory 9 (observation) [key: fb99dc92-c15] (score: 0.7913)
**Situation:** A wolf (player_2) was put under pressure for voting against a player (player_1) who was later killed by the wolves. Information landscape: The evidence was the wolf's own voting record, which now directly linked them to a wolf kill. Game phase: Mid-game, with the village looking for hard evidence to act on. Consensus texture: A strong consensus formed against the wolf, driven by multiple villagers citing the same voting evidence. Social pressure: Heavy, evidence-based pressure was applied to player_2, who was questioned by three separate players.
**Approach:** The wolf's approach was to deflect, provide vague answers like 'suspicious behavior,' and accuse the primary questioner (player_5) of being aggressive and manufacturing a narrative.
**Outcome:** This defensive strategy failed catastrophically. The lack of a specific alibi was interpreted as guilt, leading to a decisive vote against the wolf.

### Memory 10 (observation) [key: a394b860-e1b] (score: 0.7901)
**Situation:** The village had a twice-confirmed non-wolf (player_7) who became aggressive in trying to hunt wolves after a prior mislynch. Information landscape: Information was rich regarding player_7's status, but the discussion was dominated by arguments over the previous day's voting record. Game phase: Mid-game, after the village had mistakenly eliminated a villager (player_8). Social pressure: Player_7 was putting pressure on the players who voted for player_8, while player_4 was pressuring player_7 for their 'outlier' vote, creating village infighting.
**Approach:** The wolves (player_5 and player_6) exploited the village's frustration with player_7's aggressive accusations. They framed player_7 as being disruptive and joined the vote against them.
**Outcome:** The village voted out their most confirmed non-wolf player. This was a massive victory for the wolves, as they manipulated the village into eliminating its own strongest asset.

### Memory 11 (strategy_point) [key: a7c6ac54-d43] (score: 0.8141)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The village has a confirmed non-wolf player to rally around, making the landscape information-rich. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to maximize integration by appearing helpful.
**Action:** Do not attempt to divert the conversation to vague behavioral traits like 'quiet players.' Instead, actively participate in analyzing the failed kill, proposing theories about why that player was targeted, to appear aligned with the village's goals and avoid suspicion.

### Memory 12 (strategy_point) [key: fc5e48a9-5cb] (score: 0.7919)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The only new information is the failed attack, meaning discussion is based on speculative reads. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to minimize attention on the failed kill.
**Action:** Do not attempt to justify the attack by framing the survivor as a 'threat,' as this inadvertently validates the wolves' choice and implies insider knowledge. Instead, agree that the save was fortunate and quickly pivot the conversation towards a different player or a general strategy to avoid suspicion.

### Memory 13 (strategy_point) [key: 7eebdf18-9f1] (score: 0.7904)
**Situation:** When a player who is confirmed non-wolf (e.g., saved by the healer) becomes aggressive and polarizing in discussions. Information landscape: The village has a trusted voice, but that voice is causing infighting and frustration by focusing on past mistakes. Game phase: Mid-game, when village morale may be low after a mislynch. Consensus texture: The consensus is fractured, with some supporting the confirmed player and others growing tired of their aggressive tone.
**Action:** Amplify the village's frustration. Subtly frame the confirmed player as 'disruptive,' 'unhelpful,' or 'causing chaos' to turn public opinion against them. This can manipulate the village into eliminating one of its most valuable assets.

### Memory 14 (strategy_point) [key: 17add23c-00b] (score: 0.7830)
**Situation:** Mid-game, after a villager has been incorrectly eliminated. Information landscape: The voting record from the mislynch is the primary evidence being discussed. Social pressure: You and your partner are both under pressure as key participants in the failed vote, creating a risk of coordinated suspicion.
**Action:** Avoid using the exact same deflection tactic as your partner. If you both argue to 'move on from the past,' it creates a strong rhetorical link that exposes you both. Instead, one of you should shift blame to a specific villager who also voted that way, while the other focuses on a different line of reasoning to create distance.

### Memory 15 (strategy_point) [key: 21399e68-38b] (score: 0.7796)
**Situation:** When the village is conducting a post-mortem on a mislynch that you or your partner participated in or led, and you are not currently the primary target of suspicion. Information landscape: Information-rich, grounded in the public voting record of the eliminated villager. Game phase: Mid-game, immediately following a village mislynch. Social pressure: Low to moderate; you are not under direct attack.
**Action:** Actively participate in the post-mortem and offer a plausible, pro-village alternate explanation for the voting momentum rather than telling the village to 'stop looking at the past.' Outright dismissing the analysis signals you have something to hide and draws immediate suspicion.

### Memory 16 (strategy_point) [key: e552a4ce-f55] (score: 0.7694)
**Situation:** Mid-game, when the village has made a major error in a previous vote and is now conducting a post-mortem to identify scapegoats or leaders of that failed vote, and you are not yet under direct, evidence-based scrutiny. Information landscape: The landscape is rich with data from the mistaken vote, including specific voting records. Social pressure: The village is focused on assigning blame for the past mistake.
**Action:** Actively frame the mistake as a 'collective failure' or 'groupthink.' Argue that dwelling on it breeds paranoia and that the village should focus on 'present behavior.' This deflects scrutiny from your own role in the vote and makes anyone who insists on analyzing it seem unproductive or suspicious themselves.

### Memory 17 (strategy_point) [key: e1428900-f94] (score: 0.7664)
**Situation:** Mid-game, when the village is analyzing voting records or past events to identify suspicious patterns, and you are under organic pressure regarding your own voting history. Information landscape: The landscape is shifting from speculative to evidence-based, using voting records as the primary data source. Social pressure: Multiple players are coordinating questions, putting you on the defensive.
**Action:** Do not engage with the evidence directly. Instead, attack the process of analysis itself by framing the discussion as 'circular,' 'infighting,' or 'relitigating the past,' and argue that the village should 'move on' to find 'real leads.' Simultaneously, deflect scrutiny by launching a suspicion-based accusation against a quiet player to shift the focus away from your own voting record.

### Memory 18 (strategy_point) [key: ef42a0e8-ce5] (score: 0.7655)
**Situation:** Mid-game, after a major town power role has been mistakenly eliminated. The village is analyzing the voting records of the mistaken majority, leaving you vulnerable. There is one player who voted differently from the majority.
**Action:** Aggressively question the lone dissenting voter. Frame their non-conformity as suspicious and demand an explanation to deflect blame from your own participation in the bad vote and weaponize the village's regret against an innocent player.

### Memory 19 (strategy_point) [key: 09f24ec7-55c] (score: 0.7645)
**Situation:** If your wolf partner is exposed by compelling evidence and their elimination is imminent or has just occurred. Information landscape: The information landscape is rich against your partner, based on confirmed roles or damning voting records. Game phase: Endgame, when your connection to your partner is under scrutiny and a strong consensus has formed.
**Action:** Vote with the majority to eliminate your partner to establish credibility. After the elimination, do not attack those who voted for your partner, as this appears defensive. Instead, praise the village for the successful elimination to build trust, then subtly pivot to a new target by re-interpreting old evidence.

### Memory 20 (strategy_point) [key: f13b30ab-02a] (score: 0.7585)
**Situation:** Mid to endgame, when you participated in a majority vote that was later revealed to be a major mistake, and you are under direct, evidence-based pressure from villagers scrutinizing your specific role in the vote. Information landscape: Information-rich, with voting records being the primary evidence used against you. Social pressure: You are the primary target of suspicion.
**Action:** Immediately go on the offensive by accusing the villagers who voted with you. Frame them as the leaders of the failed consensus and yourself as a reluctant follower. This 'history rewriting' deflects blame and creates infighting among villagers, paralyzing their ability to form a new consensus against you.

## Response for Case 22

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "9d1739db-282", "type": "observation", "relevance": _},
  {"idx": 2, "key": "f732818d-6b2", "type": "observation", "relevance": _},
  {"idx": 3, "key": "b369c51e-969", "type": "observation", "relevance": _},
  {"idx": 4, "key": "83487df0-7a8", "type": "observation", "relevance": _},
  {"idx": 5, "key": "ceef18b3-1e8", "type": "observation", "relevance": _},
  {"idx": 6, "key": "1fbc6519-4ae", "type": "observation", "relevance": _},
  {"idx": 7, "key": "79288222-86d", "type": "observation", "relevance": _},
  {"idx": 8, "key": "084c2417-f2d", "type": "observation", "relevance": _},
  {"idx": 9, "key": "fb99dc92-c15", "type": "observation", "relevance": _},
  {"idx": 10, "key": "a394b860-e1b", "type": "observation", "relevance": _},
  {"idx": 11, "key": "a7c6ac54-d43", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "fc5e48a9-5cb", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "7eebdf18-9f1", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "17add23c-00b", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "21399e68-38b", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "e552a4ce-f55", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "e1428900-f94", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "ef42a0e8-ce5", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "09f24ec7-55c", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "f13b30ab-02a", "type": "strategy_point", "relevance": _}
]
```