# Rule errors in the seeded strategy points (2026-10-11)

A read of all 150 points (`strategy_points.json`, action and situation text) against the agents'
rules text (`rules_block` for two lineups that together cover the 12 roles), `role_sheet.md` and the
engine. Done by an Opus subagent; Claude checked the carrier, Illusionist and Sigilist rules against
the rules text and `Agents/rules/night.py`. Only claims about what the game does, announces or lets
a role know are flagged, not strategy. One read, not a measurement.

**14 of 150 flagged: 8 high confidence, 6 medium.** Keys are the first 8 characters.

| Key | Cell | Claim | The rule |
|---|---|---|---|
| 77bf9429 | necromancer/night_action | an Illusionist body gives concealment that hides the Necromancer from death reports | a body attack is announced as reanimated; an Illusionist body gives an attack (`BORROWED_ABILITY`) |
| 3da5f01a | necromancer/night_action | a borrowed block triggers a "system-announced reanimated ability signature" | only attacks are announced; a block is told to the blocked player alone |
| 7e0540c4 | serial_killer/night_action | a saved player's protection is "essentially permanent" | the Healer protects one player per night |
| 70cfc8b0 | illusionist/night_action | sigils protect victims; a reanimated entity can take the pack's kill; the kill can stall; a save reveals the attacker | the sigil goes on the attacker; the Necromancer is not in the pack; the pack kills every night; a save names only "the wolves" |
| 7d457aad | illusionist/night_action | on a save, no evidence of the Illusionist's visit is shown | if the victim survived, nothing is hidden and every visit is seen |
| 7fe3513f | sigilist/day_vote | a failed sigil indicates night immunity | "no effect" looks the same for a non-attacker and an immune attacker |
| 83cb62bb | sigilist/day_discussion | an all-clear for players who were not struck | the Sigilist learns nothing about players it did not sigil |
| 3240103b | sigilist/night_action | a sigil can stop a kill or punish a lone killer | the attack resolves either way; the Serial Killer is immune; body attacks are never punished |
| f1207ff1 | sigilist/night_action | "no effect" is evidence of immunity; a sigil can shut down the lone killer (medium) | as above |
| 163395b5 | illusionist/night_action | a failed kill privately identifies the lone killer (medium) | a Fortune Teller's self-bet also fails an attack; the Necromancer is immune on night 1 only |
| 4e5de30e | vigilante/day_vote | unspent bullets arm the Necromancer (medium) | a Vigilante body gives a shot with no use limit, whatever was left |
| 41e70866 | trailseer/night_action | following a victim shows who visited them (medium) | a Trailseer learns whom its target visited; seeing visitors is the Sentinel's |
| 83a1b961 | investigator/night_action | night-1 checks on "aggressive voting patterns" (medium) | day 1 has no vote |
| 543a3d6c | illusionist/day_discussion | the Serial Killer as a neutral role (medium) | the lone killer is its own side |

**Not counted: the rules text and the engine disagree.** Two points (961e6670 Chanteuse night,
46b9d27e Illusionist night) assume the pack chooses its carrier. The agents' rules text allows it
("the carrier rotates unless the pack agrees otherwise"), but `pack_carrier` in
`Agents/rules/night.py` only rotates by seat order, and the role sheet says the chat override was
never built. The rules text is wrong, not the points.

**Borderline, not flagged:** a block "to ensure the elimination" (f63ac2f4); "Tracker", an old role
name (de763f2c) and casual "tracker" for the Trailseer in several points.
