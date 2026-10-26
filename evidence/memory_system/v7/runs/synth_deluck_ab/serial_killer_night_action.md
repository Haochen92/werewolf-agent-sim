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
- (offensive/deceptive) On Night 1, target the most aggressive or accusatory player from Day 1. This player is often a wolf attempting to sow discord. Killing a wolf removes a rival evil, accelerates your solo win condition, and can mislead the village into thinking a pro-town killing role is active.
- (positional/deceptive) On Night 1, avoid targeting the most obvious town leader or proactive strategist. Wolves will likely target them too, risking a saved double-hit that confirms a town power role. Instead, kill a quiet, random, or less conspicuous player to ensure an elimination, thin the herd, and avoid creating a confirmed town hero.

**D — credit-aware synthesis:**
- (offensive/deceptive) On Night 1, avoid targeting the most vocal and prominent village organizer. This player is a common target for wolves, and attacking them risks a redundant kill or a healer-save that inadvertently confirms them as a town hero. Instead, target a quieter, less-central player to guarantee a unique elimination and sow chaos without creating a credible leader for the village.
- (offensive/deceptive) On Night 1, distinguish between 'vocal organizers' and 'aggressive accusers'. Instead of targeting the player trying to build village consensus, prioritize killing a player who initiated a conflict or pushed aggressively for a lynch with little evidence. This behavior is a stronger early indicator of a wolf, and killing them removes a rival evil, accelerates your win condition, and may frame the kill as a pro-town action.

## Cluster 2 (5 obs)

**H — halo-synthesis:**
- (defensive/deceptive) When you are a primary suspect locked in a public rivalry, resist the urge to kill your rival. This move is predictable and likely to be blocked by a protective role, which would clear your rival and confirm your guilt. Instead, attack a quiet, less-involved player to create confusion and deflect suspicion. However, if a protective role is confirmed to be out of the game, your rival becomes a viable, high-value target.

**D — credit-aware synthesis:**
- (offensive/deceptive) When locked in a public rivalry or tie-vote, do not target your rival directly; this is a predictable move likely to be saved by a Healer. Instead, target a player from the voting bloc that supported your rival to weaken their coalition, create confusion, and avoid confirming your rival as 'town-aligned' via a public save.
- (positional/deceptive) After voting with a clear bloc (especially one containing wolves) against a player, do not kill that same player at night. This creates a highly suspicious and traceable link. Instead, target a quiet, neutral villager to allow suspicion to remain focused on the day's conflict while you advance your win condition without connecting your public and private actions.
- (defensive/deceptive) If an information-gathering role (e.g., Investigator) publicly accuses you, you must target them for elimination that night, even if a Healer might protect them. This is a necessary defensive kill to survive the next day's vote. The risk of a failed, saved kill is less than the certainty of being lynched on their testimony.

## Cluster 3 (4 obs)

**H — halo-synthesis:**
- (offensive/deceptive) On Night 1, avoid targeting the most vocal, active, or strategically influential player. Instead, kill a quiet, low-profile player. This minimizes the risk of your kill overlapping with the wolves' kill and prevents the accidental creation of a 'confirmed-good' town hero if a Healer save occurs.

**D — credit-aware synthesis:**
- (defensive/deceptive) On Night 1, do not target the most vocal or strategically active player, especially if you have publicly disagreed with them. This 'obvious' target is also obvious to the wolves, risking a kill overlap that gets saved by a Healer and inadvertently 'confirms' the target's importance to the town. Instead, target a quiet, non-controversial player to reduce numbers while minimizing the risk of a failed kill and avoiding drawing attention.
- (offensive/deceptive) Adapt your kill priority to the immediate board state. 1. DEFENSIVE: If an information-gathering role is actively and publicly accusing you, you must kill them to survive the next vote. 2. STRATEGIC: If a village power role is confirmed but you are not their target, focus your kills on them to cripple the town's information flow. 3. COMPETITIVE: If the wolf faction is strong or nearing parity, shift focus to killing a key wolf. 4. DEFAULT: Otherwise, kill quiet, low-information villagers to lower the player count without drawing attention.
