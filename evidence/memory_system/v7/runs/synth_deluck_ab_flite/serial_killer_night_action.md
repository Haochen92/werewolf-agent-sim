# Synthesis A/B — serial_killer/night_action

**Pure-prune survivor (arm S, highest realized lift +0.26):**
> If a player claims an information-gathering role (like Investigator) and is publicly accusing you, you must target them for elimination that night. Accept the future suspicion as the cost of surviving the immediate threat of being voted out.

## Realized track record fed to the credit arm

```
- realized lift +0.26 (followed 8x): If a player claims an information-gathering role (like Investigator) and is publicly accusing you, you must target them for elimination that night. Accept the future suspicion as the cost of surviving the immediate threat of being voted out.
- realized lift +0.26 (followed 14x): Once an information-gathering role like the Investigator is confirmed by the village, make them your priority target every single night. Even if they are being protected by a Healer, your consistent attacks force the Healer to use their save, creating a predictable pattern and opening the possibility that another faction will remove the Healer for you.
- realized lift +0.10 (followed 48x): In the mid-game, if the wolf faction is strong or nearing parity, prioritize killing a wolf over a villager. Analyze voting records and discussion to identify the most influential wolf and eliminate them to cripple the competing evil faction and seize control of the game's pace.
- realized lift +0.08 (followed 36x): During the wolf-hunting phase of the game, let the village and its power roles (Investigator, Vigilante) focus on the wolves. Use your night kills on ambiguous, quiet villager targets to avoid interfering. This allows the village to weaken the wolf faction for you, while your kills accelerate the countdown to parity without drawing the Investigator's attention.
- realized lift +0.04 (followed 19x): When the village and wolves are deadlocked over an accusation, kill a neutral, quiet villager. This keeps the primary conflict raging for another day, allows the other factions to weaken each other, and keeps investigative focus away from you while you still make progress towards your win condition.
- realized lift -0.03 (followed 22x): After the village successfully eliminates a wolf and you voted with them, use the resulting goodwill to kill one of the villagers who was most instrumental in that successful hunt. This weakens the town's strongest players while you are least likely to be suspected.
- realized lift -0.04 (followed 6x): After a successful lynch of a wolf, immediately target the most prominent player who was opposing that wolf during the day's debate. This removes a proven active player and capitalizes on the chaos of the previous day.
- realized lift -0.05 (followed 8x): In a 1 vs. N endgame (e.g., 1v2 or 1v3), use your night kill to eliminate the most strategically adept remaining player. Analyze their past arguments and voting record to identify the biggest threat to your cover and remove them.
- realized lift -0.06 (followed 12x): If you make a conspicuous or unusual vote during the day (e.g., a lone vote, breaking from a majority), do not kill that same player at night. This creates an easily traceable link between your public and secret actions. Target a different player to maintain plausible deniability and frame your day-vote as a genuine misread, not a prelude to a kill.
- realized lift -0.08 (followed 17x): In the early game before roles are known, avoid killing a vocal village organizer if you have publicly disagreed with them. Instead, target players who are quietly influential or seem like potential power roles but have not been in direct conflict with your public persona. This severs village leadership without painting a target on your back.
- realized lift -0.11 (followed 14x): If you are a primary suspect in a tie-vote with another player, resist the obvious move of trying to kill them at night. This is a common play that a Healer is likely to anticipate and counter. Instead, target a player from the voting bloc that supports your rival to weaken their coalition and introduce new chaos.
- realized lift -0.12 (followed 12x): In a three-player endgame against a wolf and a villager, always target the wolf. The wolf is your only remaining competitor for the win. Eliminating them guarantees your victory, as you will either be the sole survivor or face a lone villager you can kill the next night.
```

## Cluster 1 (10 obs)

**H — halo-synthesis:**
- (offensive/honest) On Night 1, target the most aggressive or loud vocal participant in the day's discussion to maximize the chance of hitting a high-value role (Wolf or Healer) while minimizing the risk of redundant target convergence with the wolves.
- (offensive/honest) Prioritize targets who appear less central to the village narrative if you want to avoid 'hero' status or healer protection, or target identified agitators to proactively remove wolves and speed up the game.

**D — credit-aware synthesis:**
- (offensive/deceptive) Prioritize identifying and targeting any confirmed information-gathering roles like the Investigator, even if protected by a healer; consistent pressure forces protective resources to exhaust or creates openings for other factions to eliminate the healer.
- (positional/deceptive) In the early game with minimal information, avoid targeting the most vocal strategists or individuals you have personally sparred with; instead, select quiet but influential players who lack direct conflict with your public persona to thin the village without leaving a trail of personal animosity.
- (offensive/honest) In the final three-player endgame, always eliminate the remaining wolf regardless of prior alliances or behavioral patterns, as they are your only path to a solo win.

## Cluster 2 (5 obs)

**H — halo-synthesis:**
- (positional/deceptive) Prioritize killing quiet, low-profile players to reduce village numbers while avoiding the spotlight of public rivalries; only target known threats or vocal rivals if there is verifiable confirmation that protective roles (like the Healer) are eliminated from the game.

**D — credit-aware synthesis:**
- (offensive/honest) Prioritize the immediate elimination of any player confirmed by the village to hold an information-gathering role (e.g., Investigator). If they are suspected of protection, maintain a consistent attack on them every night; this forces the Healer to commit to them, creating a predictable pattern that limits the Healer's utility elsewhere.
- (offensive/deceptive) In mid-game scenarios where wolf activity is detected via voting records, focus night kills on the most influential identified wolf. If the game is in an ambiguous state with no clear wolf leader, target quiet, neutral villagers to avoid attracting the investigative focus of the village's power roles.
- (positional/deceptive) If caught in a tie-vote or public conflict, actively avoid targeting your direct rival for a night kill. Instead, identify and eliminate a member of that rival's voting coalition to destabilize their support structure and introduce chaotic doubt into the room.

## Cluster 3 (4 obs)

**H — halo-synthesis:**
- (offensive/honest) Target the 'middle-of-the-pack' players who are neither the most vocal leaders nor completely inactive, avoiding the players who attract the village's attention or the wolf faction's kill path during the first night.

**D — credit-aware synthesis:**
- (offensive/deceptive) Prioritize the confirmed power role (e.g., Investigator) as your nightly target. If you know a Healer is protecting them, keep attacking to force the Healer's hand or draw out a rival faction's counter-move against the healer.
- (positional/deceptive) In the early game, target quiet, ambiguous villagers rather than vocal organizers or players you have publicly debated. By avoiding prominent figures, you keep the focus on village-versus-wolf dynamics and prevent being linked to high-profile deaths.
- (offensive/honest) When the wolf faction is strong and nearing game-winning parity, ignore villagers and focus your night kills exclusively on identifying and removing the wolves. Use voting records from the day phase to confirm the wolves' influence before committing the kill.
