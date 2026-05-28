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

# Case 36: wolf — day_discussion (day 2 round 3)

## Game State (what the player sees)
```
================================================================================
CASE cdcd2c6e46f59a85cad3d634c3595a67:2f16c4ee84af2c74 | wolf | day 2 round 3 | day_discussion
================================================================================

Role: wolf
Day: 2, Round: 3

Surviving villagers: player_2, player_4, player_5, player_6, player_7
Known surviving wolf allies: player_3, player_8

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

--- Wolf night chat ---
No messages yet.

--- Strategy note ---
Maintain a low profile and act as a voice of reason. Since player_7 is being assertive, I will observe if the village views them as reckless. I will continue to advocate for caution to avoid appearing too eager or aggressive.

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

**Situation 1:** The wolf pair killed a villager on night 1 and must now navigate an information-starved day 2 where vocal players are demanding suspects. The wolf's partner is also advocating caution, creating a visible alignment between the two wolves on the 'wait and see' side of the discussion. Information landscape: Information-starved — no healer save, no voting records; the only behavioral signal is the emerging split between proactive and cautious players. Game phase: Early game, day 2 with 7 players; the wolves need to avoid creating a traceable voting pattern. Consensus texture: Polarizing — the village is splitting between action and caution factions, and both wolves are currently on the caution side. Agent exposure: Moderate risk — the wolf's caution rhetoric matches their partner's, which could look like coordination if the village notices the pattern.

## Retrieved Memories to Label

### Memory 1 (observation) [key: b59c7455-6cd] (score: 0.8044)
**Situation:** A wolf or wolves were put under pressure for stalling behaviors, such as advocating for a passive 'wait and see' strategy or refusing to name a suspect. Information landscape: The game was information-starved, with suspicion based entirely on behavioral reads, often centered on a healer save. Game phase: Mid-game, following the first night action. Social pressure: The wolf/wolves were under organic pressure from multiple players who wanted to move the discussion from generic statements to specific accusations.
**Approach:** The wolf attempted to defend their position by framing the accuser as 'disruptive' or 'rushed', or by attempting to deflect suspicion onto another villager without strong evidence.
**Outcome:** The villagers interpreted this passivity and deflection as a sign of guilt. A strong consensus formed, leading to the wolf's elimination by a near-unanimous vote.

### Memory 2 (observation) [key: cc10c6bf-be8] (score: 0.8005)
**Situation:** During Day 2 discussions, Wolf Player 5 attempted to sound like a helpful villager by suggesting the group analyze voting patterns. Information landscape: The game was information-starved, as no vote had occurred on Day 1, meaning there were no voting patterns to analyze. Game phase: Mid-game, following the first night's elimination of the Healer. Social pressure: Multiple villagers (Player 4, Player 7) immediately identified the logical flaw in Player 5's argument, putting them under evidence-based pressure.
**Approach:** Player 5 continued to pivot to generalities like 'silence' instead of addressing the specific criticism, which only increased suspicion.
**Outcome:** A consensus formed against Player 5, leading to their elimination and confirmation as a wolf. This mistake cost the wolf team a member early on.

### Memory 3 (observation) [key: 55ad1ead-bb0] (score: 0.7891)
**Situation:** An assertive villager (player_7) aggressively pushed for a vote on Day 2 to break the village's inaction. Information landscape: The game was information-starved, with no voting records or confirmed roles, making any accusation purely speculative. Game phase: Early-game, following the first night kill, so villagers were anxious but had no concrete leads. Social pressure: Pressure was successfully applied to the assertive villager (player_7) by framing their urgency as reckless and a wolf-like tactic to force a mislynch.
**Approach:** A wolf (player_3) and the Investigator (player_5) both publicly argued that pushing for a vote without evidence was dangerous, creating a powerful coalition against the assertive villager.
**Outcome:** A strong consensus formed against the assertive villager, leading to their elimination. This successfully removed an active villager and taught the village to fear taking decisive action.

### Memory 4 (observation) [key: 92046e6d-6ce] (score: 0.7854)
**Situation:** A wolf was put under scrutiny for a specific piece of strategic advice they gave on Day 1, which backfired after the night's events. Information landscape: The village had no hard evidence, so Day 1 statements were the only available data for analysis. Game phase: Mid-game, after the first kill. Social pressure: The wolf (player_8) who suggested 'monitoring quiet players' on Day 1 came under immediate suspicion after the quiet healer was killed.
**Approach:** The wolf attempted to deflect by pivoting their strategy, attacking vocal players, and then framing the villagers' scrutiny as 'infighting'.
**Outcome:** The deflection failed because the initial statement was too specific and the pivot was too obvious. The wolf was eliminated by a near-unanimous vote, revealing them and confirming the villagers' suspicions.

### Memory 5 (observation) [key: 79288222-86d] (score: 0.7839)
**Situation:** In an information-starved mid-game, a proactive villager aggressively demands that players name suspects, putting pressure on the wolves. The village has no consensus and the only lead is a recent healer save. The wolves are not the primary target but are under pressure to contribute.
**Approach:** Frame a proactive villager's aggression as a suspicious tactic to force a rushed, chaotic vote (1x), while urging caution and claiming there is not enough evidence to act (1x).
**Outcome:** The village, lacking other leads, turns on the aggressive villager, leading to their elimination. This removes a proactive town member and successfully deflects suspicion from the wolves.

### Memory 6 (observation) [key: b369c51e-969] (score: 0.7837)
**Situation:** A villager (player_2) correctly used Day 2 voting records to accuse a group of players that included both wolves (player_6, player_7) and the healer (player_5). Information landscape: The landscape was becoming information-rich, with voting records being used as the primary evidence. Game phase: Endgame, with only five players remaining and the wolves one elimination away from victory. Social pressure: The wolves coordinated pressure on the accuser (player_2), deflecting the evidence by attacking their previous passivity and framing their valid points as an attempt to sow discord.
**Approach:** The wolves (player_6, player_7) aggressively challenged player_2's motives for suddenly becoming vocal, ignoring the voting evidence player_2 presented.
**Outcome:** This tactic successfully shifted suspicion onto player_2. The healer (player_5) was convinced by the wolves' narrative and voted with them, leading to another villager's elimination and a wolf victory.

### Memory 7 (observation) [key: 83487df0-7a8] (score: 0.7834)
**Situation:** After the village mistakenly eliminated the Investigator, the discussion fractured over whether to analyze that disastrous vote. Information landscape: The information landscape was information-rich regarding the Day 2 vote (a confirmed mislynch of a power role), but poor otherwise. Game phase: Mid-game, with both the Investigator and Healer eliminated, leaving the village with no special roles. Social pressure: A villager (player_4) came under pressure for arguing that analyzing the past vote was a waste of time, a position that objectively benefited the wolves.
**Approach:** One wolf (player_5) publicly agreed with the villager's flawed logic to amplify the conflict, while both wolves voted for a different target (player_1) to ensure a villager was eliminated regardless of the outcome of the main dispute.
**Outcome:** The villagers focused their votes on the contrarian villager (player_4) and eliminated them, while the wolves' split vote eliminated a village leader and sowed more confusion.

### Memory 8 (observation) [key: bfb69c8b-424] (score: 0.7822)
**Situation:** A villager (player_7) made a weak accusation against another villager (player_8) for being too quiet, leading to a defensive argument. Information landscape: The game was information-starved, with the only conflict arising from speculative behavioral reads. Game phase: Mid-game, following a night with no eliminations, which increased villager anxiety. Social pressure: A villager-driven conflict created an opportunity, which the wolves amplified by subtly defending the accused and questioning the accuser's logic.
**Approach:** The wolves fanned the flames of the argument by criticizing the accuser's reasoning (player_1) and then voted with the resulting majority to eliminate them.
**Outcome:** The village was successfully baited into eliminating a villager (player_7), allowing both wolves to blend in with the town's vote.

### Memory 9 (observation) [key: 9355e610-6db] (score: 0.7773)
**Situation:** An Investigator proposed a valid line of inquiry, suggesting the village scrutinize how players reacted to a healer save. Two wolves immediately coordinated to dismiss this entire line of reasoning as a 'distraction' or 'trap'. Information landscape: The landscape was information-starved, with the only lead being a saved player and speculative reads on behavior. Game phase: Mid-game, following the first night's action where no one was eliminated. The village was looking for its first solid lead. Social pressure: The wolves created social pressure on the Investigator by framing their analysis as unhelpful, influencing the information-starved villagers.
**Approach:** The wolves framed the Investigator's analysis as a distraction, successfully steering the village away from a productive line of inquiry and turning suspicion onto the Investigator themselves.
**Outcome:** The village, lacking other leads, followed the wolves' narrative and voted to eliminate the Investigator, a major victory for the wolves.

### Memory 10 (observation) [key: d0bde61b-652] (score: 0.7741)
**Situation:** On Day 2, the Investigator (player 3) initiated an accusation against a villager (player 4) based on a weak, behavioral read of their 'urgency'. Information landscape: The village was information-starved, relying on speculative reads as no roles were confirmed. Game phase: Mid-game, following the first night kill. Social pressure: Pressure began to mount on player 4, initiated by the Investigator.
**Approach:** Wolf 6 immediately piled onto the accusation, amplifying the Investigator's reasoning and helping to build a broader consensus against player 4.
**Outcome:** A strong majority voted out player 4, a villager. This eliminated a town member and simultaneously damaged the Investigator's credibility for the following day.

### Memory 11 (strategy_point) [key: c4fe88af-573] (score: 0.8135)
**Situation:** If you and your wolf partner are being pressured to provide suspects in an information-starved early game. Information landscape: There are no voting records or confirmed roles; suspicion is based on communication style and passivity. Game phase: Early to mid-game, before any eliminations have provided solid leads. Social pressure: Pressure is building from multiple villagers who demand action and view caution as suspicious.
**Action:** Adopt a shared strategy of advocating for calm and evidence-based decisions. Use this 'reasonable' stance to contrast with an aggressive accuser, framing them as reckless to deflect pressure from yourselves. This can turn the village against a vocal opponent.

### Memory 12 (strategy_point) [key: 17add23c-00b] (score: 0.7874)
**Situation:** Mid-game, after a villager has been incorrectly eliminated. Information landscape: The voting record from the mislynch is the primary evidence being discussed. Social pressure: You and your partner are both under pressure as key participants in the failed vote, creating a risk of coordinated suspicion.
**Action:** Avoid using the exact same deflection tactic as your partner. If you both argue to 'move on from the past,' it creates a strong rhetorical link that exposes you both. Instead, one of you should shift blame to a specific villager who also voted that way, while the other focuses on a different line of reasoning to create distance.

### Memory 13 (strategy_point) [key: 21399e68-38b] (score: 0.7824)
**Situation:** When the village is conducting a post-mortem on a mislynch that you or your partner participated in or led, and you are not currently the primary target of suspicion. Information landscape: Information-rich, grounded in the public voting record of the eliminated villager. Game phase: Mid-game, immediately following a village mislynch. Social pressure: Low to moderate; you are not under direct attack.
**Action:** Actively participate in the post-mortem and offer a plausible, pro-village alternate explanation for the voting momentum rather than telling the village to 'stop looking at the past.' Outright dismissing the analysis signals you have something to hide and draws immediate suspicion.

### Memory 14 (strategy_point) [key: 7eebdf18-9f1] (score: 0.7805)
**Situation:** When a player who is confirmed non-wolf (e.g., saved by the healer) becomes aggressive and polarizing in discussions. Information landscape: The village has a trusted voice, but that voice is causing infighting and frustration by focusing on past mistakes. Game phase: Mid-game, when village morale may be low after a mislynch. Consensus texture: The consensus is fractured, with some supporting the confirmed player and others growing tired of their aggressive tone.
**Action:** Amplify the village's frustration. Subtly frame the confirmed player as 'disruptive,' 'unhelpful,' or 'causing chaos' to turn public opinion against them. This can manipulate the village into eliminating one of its most valuable assets.

### Memory 15 (strategy_point) [key: 5cf87925-551] (score: 0.7802)
**Situation:** If you are trying to appear helpful and contribute to the discussion during the early game. Information landscape: The game is information-starved with no votes or confirmed roles. Game phase: Early-game, when establishing a believable villager persona is key.
**Action:** Avoid referencing specific types of evidence that do not yet exist, such as 'voting patterns' before any votes have been cast. Sticking to generic observations about who is quiet or asking open-ended questions is safer. Making a factual error gives savvy villagers concrete proof to use against you.

### Memory 16 (strategy_point) [key: a7c6ac54-d43] (score: 0.7717)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The village has a confirmed non-wolf player to rally around, making the landscape information-rich. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to maximize integration by appearing helpful.
**Action:** Do not attempt to divert the conversation to vague behavioral traits like 'quiet players.' Instead, actively participate in analyzing the failed kill, proposing theories about why that player was targeted, to appear aligned with the village's goals and avoid suspicion.

### Memory 17 (strategy_point) [key: e552a4ce-f55] (score: 0.7675)
**Situation:** Mid-game, when the village has made a major error in a previous vote and is now conducting a post-mortem to identify scapegoats or leaders of that failed vote, and you are not yet under direct, evidence-based scrutiny. Information landscape: The landscape is rich with data from the mistaken vote, including specific voting records. Social pressure: The village is focused on assigning blame for the past mistake.
**Action:** Actively frame the mistake as a 'collective failure' or 'groupthink.' Argue that dwelling on it breeds paranoia and that the village should focus on 'present behavior.' This deflects scrutiny from your own role in the vote and makes anyone who insists on analyzing it seem unproductive or suspicious themselves.

### Memory 18 (strategy_point) [key: fc5e48a9-5cb] (score: 0.7663)
**Situation:** When a wolf target is saved by the healer and the village begins discussing the motive behind the attack. Information landscape: The only new information is the failed attack, meaning discussion is based on speculative reads. Game phase: Mid-game, when the first night attack is revealed. Strategic context: You prefer to minimize attention on the failed kill.
**Action:** Do not attempt to justify the attack by framing the survivor as a 'threat,' as this inadvertently validates the wolves' choice and implies insider knowledge. Instead, agree that the save was fortunate and quickly pivot the conversation towards a different player or a general strategy to avoid suspicion.

### Memory 19 (strategy_point) [key: 09f24ec7-55c] (score: 0.7653)
**Situation:** If your wolf partner is exposed by compelling evidence and their elimination is imminent or has just occurred. Information landscape: The information landscape is rich against your partner, based on confirmed roles or damning voting records. Game phase: Endgame, when your connection to your partner is under scrutiny and a strong consensus has formed.
**Action:** Vote with the majority to eliminate your partner to establish credibility. After the elimination, do not attack those who voted for your partner, as this appears defensive. Instead, praise the village for the successful elimination to build trust, then subtly pivot to a new target by re-interpreting old evidence.

### Memory 20 (strategy_point) [key: 3b06f99a-28d] (score: 0.7642)
**Situation:** If you are under pressure for being too quiet or passive. Information landscape: The village is in an information-starved state and is relying on behavioral reads to find leads. Game phase: Mid-game, during the first or second day's discussion. Social pressure: Multiple players are pressing you for your thoughts and treating your silence as suspicious.
**Action:** Avoid meta-game defenses like 'a wolf wouldn't act this way.' Instead, offer a concrete but non-committal contribution, such as, 'I've been watching Player X, their tone seems off, but I need more evidence.' This pivots the focus, makes you seem thoughtful rather than evasive, and buys you time.

## Response for Case 36

Rate each of the 20 memories above. JSON format:
```json
[
  {"idx": 1, "key": "b59c7455-6cd", "type": "observation", "relevance": _},
  {"idx": 2, "key": "cc10c6bf-be8", "type": "observation", "relevance": _},
  {"idx": 3, "key": "55ad1ead-bb0", "type": "observation", "relevance": _},
  {"idx": 4, "key": "92046e6d-6ce", "type": "observation", "relevance": _},
  {"idx": 5, "key": "79288222-86d", "type": "observation", "relevance": _},
  {"idx": 6, "key": "b369c51e-969", "type": "observation", "relevance": _},
  {"idx": 7, "key": "83487df0-7a8", "type": "observation", "relevance": _},
  {"idx": 8, "key": "bfb69c8b-424", "type": "observation", "relevance": _},
  {"idx": 9, "key": "9355e610-6db", "type": "observation", "relevance": _},
  {"idx": 10, "key": "d0bde61b-652", "type": "observation", "relevance": _},
  {"idx": 11, "key": "c4fe88af-573", "type": "strategy_point", "relevance": _},
  {"idx": 12, "key": "17add23c-00b", "type": "strategy_point", "relevance": _},
  {"idx": 13, "key": "21399e68-38b", "type": "strategy_point", "relevance": _},
  {"idx": 14, "key": "7eebdf18-9f1", "type": "strategy_point", "relevance": _},
  {"idx": 15, "key": "5cf87925-551", "type": "strategy_point", "relevance": _},
  {"idx": 16, "key": "a7c6ac54-d43", "type": "strategy_point", "relevance": _},
  {"idx": 17, "key": "e552a4ce-f55", "type": "strategy_point", "relevance": _},
  {"idx": 18, "key": "fc5e48a9-5cb", "type": "strategy_point", "relevance": _},
  {"idx": 19, "key": "09f24ec7-55c", "type": "strategy_point", "relevance": _},
  {"idx": 20, "key": "3b06f99a-28d", "type": "strategy_point", "relevance": _}
]
```