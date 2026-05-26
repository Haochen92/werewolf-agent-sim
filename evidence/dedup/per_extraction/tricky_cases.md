# Dedup v2 Golden Labeling — Tricky Cases

Cases where the LLM made the wrong dedup decision, revealing prompt weaknesses.
Use these to refine the dedup prompt after evaluation.

**Prompt that produced these decisions:** [dedup_prompt_baseline.py](dedup_prompt_baseline.py)
(per-extraction prompts: `OBSERVATION_DEDUP_PROMPT` lines 93-162, `STRATEGY_DEDUP_PROMPT` lines 1-90)
**Supporting standards:** [standards_baseline.py](standards_baseline.py)

---

## Case 2 | observation | healer / night_action
- **case_id:** `b1c7c1e4b5fc084c1f18d4dabce1e7f6:be0ccae425b39b21`
- **LLM decision:** D (legacy DISTINCT → keep)
- **Golden label:** M (merge with C2)
- **Tension:** New entry has 3 consecutive saves, C2 has 2 saves, C3 has 2 saves then switched and target died. The strategic lesson ("persist with same target after successful save") is the same between new entry and C2 — the difference is degree (2 vs 3), not kind. But the LLM treated the count difference as novel.
- **Prompt implication:** The dedup prompt may over-weight surface-level outcome differences (count of saves) vs the underlying strategic principle. Could benefit from guidance like "if the actionable takeaway for the agent is the same, merge even if specific numbers differ."
- **New entry:**
  ```json
  {
    "situation": "After the wolves' first night kill, the healer needed to decide who to protect. Information landscape: The landscape was still relatively information-starved, but player 1 had established themself as a vocal leader trying to organize the village. Game phase: Mid-game, after one villager elimination.",
    "approach": "The Healer (player 2) chose to protect player 1. The wolves targeted player 1 that night, and the save was successful.",
    "outcome": "The successful save confirmed player 1 was a high-priority wolf target. The healer continued to protect player 1 on all subsequent nights, successfully saving them three times in a row and keeping a key villager in the game until the final day."
  }
  ```
- **Candidate 2 (sim=0.858, obs_count=1):**
  ```json
  {
    "situation": "The Healer successfully protected a player on Night 1, but then had to decide whether to protect the same person again or rotate protection. Information landscape: The Healer knew their protection on Player 2 was successful, making Player 2 a confirmed wolf target. Game phase: Mid-game, entering Night 3 after one wolf was eliminated.",
    "approach": "The Healer chose to protect the same player (Player 2) again on Night 3. The remaining wolf also chose to target Player 2 that night.",
    "outcome": "The Healer successfully saved the same player twice. This provided irrefutable public evidence in the late game that Player 2 was a villager, which became the cornerstone of the villagers' victory."
  }
  ```

## Case 17 | observation | villager / day_discussion
- **case_id:** `b1ea401bb8e967064bb054784e240e7a:d12b8b203d278bda` (line 17)
- **LLM decision:** B (legacy REPLACE → merge with C2)
- **Golden label:** K (keep as distinct)
- **Tension:** LLM saw both as "endgame villagers rejecting wolf deflection" and wanted to merge. But the new entry has a distinct wolf tactic ("you two are too coordinated" in a 2v1) vs C2's "reject discrediting of dead Investigator." The 2v1 coordination accusation is also strategically weak since voting records confirm only one wolf remains — a different lesson about recognizing desperate/illogical wolf deflection.
- **Prompt implication:** The dedup prompt may over-merge when the *villager response* is similar ("trust evidence, ignore deflection") but the *wolf tactic being countered* is different. Could benefit from guidance: "if the opposing player's strategy is distinct, the observation teaches a different lesson even if the correct response is similar."
- **New entry:**
  ```json
  {
    "situation": "In a 2v1 endgame, the final wolf's only remaining tactic was to accuse the two villagers of being suspiciously coordinated. Information landscape: The information landscape was rich with evidence, including the confirmed wolf status of player_6 and player_5's history of voting with them against villagers. Game phase: Endgame, with only the Investigator, a Villager, and the final Wolf remaining. Social pressure: The wolf (player_5) attempted to create social pressure on the villager (player_4) by suggesting their agreement with the Investigator (player_3) was proof of a conspiracy.",
    "approach": "The Investigator and the Villager ignored the wolf's attempts to sow discord. They remained focused on the clear evidence of the wolf's past voting record and association with their eliminated partner.",
    "outcome": "The villagers held firm, trusted the evidence, and voted out the last wolf to win the game."
  }
  ```
- **Candidate 2 (sim=0.831, obs_count=6):**
  ```json
  {
    "situation": "After the Investigator was eliminated and his accusation against suspects was confirmed credible, the village needed to find the remaining wolves. Information landscape: The landscape became information-rich with a confirmed role and a strong lead. Game phase: Endgame, with the Investigator's posthumous reveal swinging the informational balance. Consensus texture: A strong consensus formed among the villagers, driven by the new evidence and the wolves' voting records.",
    "approach": "Villagers focused on the voting record, identifying that the suspects had cast votes against the confirmed Investigator or to protect each other. They rejected the wolves' attempts to discredit the dead Investigator as misinformation, using the wolves' own aggressive voting record as proof of their guilt.",
    "outcome": "The villagers successfully identified the wolves' narrative as a lie, leading to the confident elimination of the wolves and securing the villager win."
  }
  ```

## Case 22 | observation | villager / day_discussion
- **case_id:** (line 22)
- **LLM decision:** B (legacy REPLACE → merge with C2)
- **Golden label:** K (keep as distinct)
- **Tension:** LLM saw both as "endgame, use voting record to press wolf → village wins" and wanted to merge. But the voting anomaly being detected is fundamentally different: new entry detects *late bussing* (wolf joined correct vote but suspiciously late), C2 detects *partner protection* (wolf voted against eliminating partner). These are two distinct wolf-hunting heuristics.
- **Prompt implication:** Same pattern as Case 17 — LLM focuses on the *village response structure* (press with evidence → wolf folds) rather than the *signal being detected*. The prompt should emphasize: "if the observations teach different detection heuristics, they are distinct even if the village's follow-up action is similar."
- **New entry:**
  ```json
  {
    "situation": "After a wolf was eliminated, the village analyzed the voting record and noticed that the remaining wolf had joined the vote against their partner very late in the process. Information landscape: The landscape was information-rich, with the confirmed roles of an Investigator and a wolf providing a baseline for analyzing voting patterns. Game phase: Endgame, with 5 players remaining. The focus shifted from behavioral reads to scrutinizing past voting records. Social pressure: The villagers systematically questioned the remaining wolf about their delayed vote, refusing to accept deflections.",
    "approach": "The villagers collectively focused on the single piece of hard evidence—the voting record—and pressed the suspect until their evasive answers confirmed their guilt.",
    "outcome": "The coordinated pressure based on a specific voting anomaly successfully exposed the final wolf, leading to a village victory."
  }
  ```
- **Candidate 2 (sim=0.836, obs_count=2):**
  ```json
  {
    "situation": "After a wolf was eliminated, suspicion immediately fell upon the player who had voted to protect them. Information landscape: The information landscape became extremely rich. The voting record from the previous day provided clear, undeniable evidence of a potential alliance. Game phase: Endgame, with only one wolf remaining. The previous day's elimination provided the final clue needed. Consensus texture: An immediate and powerful consensus formed against the remaining wolf suspect (player_4), driven by multiple villagers citing the same voting evidence.",
    "approach": "Multiple villagers (player_1, player_2, player_6) used the Day 3 voting record to pressure the remaining wolf suspect (player_4), demanding an explanation for why they voted against eliminating a now-confirmed wolf.",
    "outcome": "The suspect's defense was weak and easily dismantled, leading to a unanimous vote for their elimination and a win for the villagers."
  }
  ```

## Case 23 | observation | healer / night_action
- **case_id:** (line 23)
- **LLM decision:** B (legacy REPLACE → merge with C2)
- **Golden label:** D (also acceptable: M)
- **Tension:** New entry is a specific instance of C2's already well-generalized pattern ("protect the most effective villager in mid/endgame → successful save → village wins"). C2 has obs_count=3 and already covers this. The new entry adds specific game-state detail (post-elimination Night 3, "revenge" targeting) but no meaningfully different strategic lesson. Could be Discard (C2 covers it) or Merge (slightly enriches C2), but definitely not Keep.
- **Prompt implication:** LLM defaults to Merge when a new entry adds any specificity, even if the existing entry already generalizes the pattern well enough. Could benefit from guidance: "if the existing entry already captures the general principle and has high observation count, Discard unless the new entry adds a genuinely different tactical dimension."
- **New entry:**
  ```json
  {
    "situation": "On Night 3, after a wolf (player_1) was eliminated, the Healer had to decide who to protect. Information landscape: The information landscape was rich with voting data from the recent elimination, showing player_4 was the most instrumental villager in outing the wolf. Game phase: Mid-game, transitioning to endgame with 5 players remaining.",
    "approach": "The Healer (player_3) correctly predicted that the remaining wolf (player_8) would target the most effective villager (player_4) for revenge and protected them.",
    "outcome": "The Healer successfully saved player_4, who then went on to lead the discussion that eliminated the final wolf on Day 4, securing the win for the villagers."
  }
  ```
- **Candidate 2 (sim=0.804, obs_count=3):**
  ```json
  {
    "situation": "The wolves repeatedly targeted a vocal, influential villager (often the Investigator) who was successfully identifying them. The Healer observed that this player was an active and logical participant, making them a persistent threat to the wolves. This occurred across the mid-game and endgame phases, where the Healer's protection became a deciding factor.",
    "approach": "The Healer chose to protect the vocal and logical player on multiple nights (e.g., Night 1 and Night 3), correctly anticipating that the wolves would continue to target this high-value asset.",
    "outcome": "The Healer's consistent protection kept a key villager (often an investigator) in the game, allowing them to survive, identify the wolves, and lead the village to victory. This also created a public pattern of saves that helped validate the Investigator's role claim, demonstrating the high value of protecting the player driving correct eliminations."
  }
  ```

## Case 25 | observation | wolf / day_discussion
- **case_id:** (line 25)
- **LLM decision:** B (legacy REPLACE → merge with C5)
- **Golden label:** D (discard)
- **Tension:** New entry and C5 describe the exact same wolf tactic ("groupthink"/"coordinated attack" accusation in endgame), same situation (lone wolf, information-rich, strong consensus), and same outcome (fails, wolf eliminated). LLM chose Merge because new entry has "more specific details regarding the game state (4 players left)." But the added specificity doesn't change the lesson at all — this is a straightforward Discard with count bump.
- **Prompt implication:** LLM has a bias toward Merge over Discard when any surface-level detail differs, even when the strategic lesson is identical. The prompt should clarify: "Merge is for when the new entry adds a meaningfully different tactical dimension to the existing entry's text. If it's just a different instance of the same lesson, Discard and bump the count."

## Case 41 | observation | wolf / day_discussion
- **case_id:** (line 41)
- **LLM decision:** C (legacy DIFFERENTIATE → keep)
- **Golden label:** D (discard, duplicate of C4)
- **Tension:** LLM differentiated because the "too obvious" defense occurs in different game phases (endgame vs mid-game). But the tactic, the defense, and the outcome are identical — the phase difference doesn't change the lesson ("meta-gaming 'too obvious' defense fails against strong evidence"). C1 also covers the same endgame last-wolf scenario with a similar deflection tactic. The LLM chose the opposite of the correct decision.
- **Prompt implication:** LLM over-differentiates based on game phase alone, even when the tactic, defense mechanism, and outcome are identical. The prompt should emphasize: "a different game phase does not make an observation distinct if the strategic lesson and the tactic are the same."
- **New entry:**
  ```json
  {
    "situation": "Wolf player_5 was confronted with their suspicious Day 2 vote and attempted to defend it by arguing it was too 'obvious' a move for a real wolf. Information landscape: The information was rich and focused entirely on player_5's voting record. Game phase: Endgame, with player_5 as the last wolf facing a unified village. Consensus texture: A very strong consensus had formed against player_5, driven by multiple players citing the same evidence. Social pressure: Player_5 was under extreme, evidence-based pressure from the entire remaining village.",
    "approach": "Player_5 used meta-gaming arguments ('would a wolf do something so obvious?') and attempted to deflect suspicion onto the most vocal accusers without providing counter-evidence.",
    "outcome": "This defense was completely ineffective. The villagers identified it as a classic deflection tactic and it only strengthened their resolve, leading to player_5's unanimous elimination."
  }
  ```
- **Candidate 4 (sim=0.834, obs_count=1):**
  ```json
  {
    "situation": "A wolf was confronted with irrefutable evidence from a past voting record that linked them to suspicious activity. Information landscape: The information landscape was rich with damning evidence in the form of voting records. Game phase: Mid-game, after their wolf partner had just been eliminated based on the same evidence. Social pressure: The lone wolf was under extreme, coordinated pressure from the entire village, who saw them as the obvious final threat.",
    "approach": "The wolf (player_6) attempted to argue that the evidence was 'too obvious' and that voting with their partner would have been a foolish move for a real wolf. This defense tried to use reverse psychology to create doubt.",
    "outcome": "The villagers immediately identified this as a classic deflection tactic. The argument failed to create any doubt and the wolf was unanimously voted out, losing the game."
  }
  ```
- **New entry:**
  ```json
  {
    "situation": "In the endgame, the last wolf (player_1) was cornered, with the remaining villagers pointing to their consistent alliance with the previously exposed wolf (player_5). Information landscape: The landscape was information-rich, dominated by the voting history that clearly linked player_1 and player_5. Game phase: Endgame, with only four players left and the villagers needing one more vote to win. Consensus texture: A rock-solid consensus existed among the three remaining villagers, all citing the same evidence.",
    "approach": "The lone wolf attempted to deflect by arguing that the villagers' perfect alignment was itself suspicious, framing it as 'groupthink' and a potential blind spot.",
    "outcome": "The villagers were not swayed, recognizing this as a last-ditch deflection. They held firm, trusted the voting record, and eliminated the final wolf to win the game."
  }
  ```
- **Candidate 5 (sim=0.844, obs_count=1):**
  ```json
  {
    "situation": "Endgame, information-rich. The last wolf remaining was put on the defensive after their vote from the previous day aligned with an eliminated wolf partner. Social pressure was high, with coordinated, evidence-based pressure from the village and a strong consensus already formed against the wolf.",
    "approach": "The wolf attempted to deflect by accusing the remaining villagers of a 'coordinated attack' and 'groupthink', framing the evidence-based consensus as a conspiracy.",
    "outcome": "The deflection tactic failed because the evidence from the voting record was too strong. The villagers saw through the attempt to sow discord and eliminated the final wolf."
  }
  ```
