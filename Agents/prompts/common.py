def build_system_prompt(*sections: str) -> str:
    """Join prompt sections with blank lines after stripping each section."""
    return "\n\n".join(section.strip() for section in sections)


# Human-turn instruction that pairs with the schema `reads` field (Agents.schemas.output.PlayerRead)
# and the {read_targets} key filled by build_agent_prompt_input: it names the exact living players
# the agent must commit a read for BEFORE its decision. Deliberately terse — the schema field
# description and the JSON example carry the fuller spec; the load-bearing part is the {read_targets}
# enumeration (the T4 completeness mechanism the decision.py tripwire scores against). Exact tested
# text (T1c replay) — do not reword.
READS_COMMIT_INSTRUCTION = (
    "\nBefore your decision, record your current read — one entry each for: "
    "{read_targets} (best-guess role, or 'unclear').\n"
)


# Canonical game rules — the single source of truth for the role line-up, abilities,
# win conditions, and flow. Composed into GAME_PREAMBLE (play prompt) AND the
# extraction-family prompts (postgame / per-role / day-summary) so the rules can never
# drift between copies. Person-neutral facts; keep it free of `{}` (it is passed as a
# .format() value). When the game design changes, edit HERE only.
GAME_RULES = """Team composition (three sides):
- 3 Villagers (no special abilities)
- 2 Wolves (know each other, secretly kill one player each night) — they win as a team
- 1 Healer (each night may protect one player from being killed; cannot protect themselves) — village side
- 1 Investigator (each night may learn one player's true role) — village side
- 1 Vigilante (village side; each night may shoot one player, but has only a few bullets for the whole game)
- 1 Serial Killer (works ALONE against everyone; kills one player each night, cannot be killed at night,
    and wins by outlasting everyone else)

Game Master will narrate the game and manage the flow.
- The Investigator receives their results privately and may choose when and how to share them with the group.
- The Game Master announces who died each night and by which kind of attacker (wolves, the serial killer,
    or the vigilante) and any healer saves, but NOT investigation results and NOT who acted.

Win conditions:
- The village side (villagers, healer, investigator, vigilante) wins when BOTH the wolves and the serial killer are gone.
- The wolves win when the serial killer is gone and they equal or outnumber the remaining village side.
- The serial killer wins by outlasting the others — being the last player (or one of the last) standing.

Game flow:
- Day: players discuss one at a time. You speak when you have something to add or are directly
    addressed, and may pass when you don't. The discussion winds down once players stop having new
    things to say, and then everyone votes. You may vote to eliminate a player, or abstain; if no
    single player gets the most votes (a tie, or an abstain majority), no one is eliminated.
- Night: the wolves choose a victim, the healer may protect someone, the investigator may investigate
    someone, the serial killer chooses a victim, and the vigilante may take a shot.
- Eliminated players' roles are revealed. The serial killer can only be removed by a daytime vote
    (it cannot be killed at night).

What is public vs. hidden:
- Votes are public and permanent — who voted for whom each day stays on the record.
- Night actions (who killed, healed, investigated, or shot whom) are hidden; only the outcomes are announced.
- A player can claim any role, but the game cannot verify a role claim — only an elimination reveals a role."""


# Play-side preamble = a second-person intro + the canonical rules. Reconstructed to be
# byte-identical to the prior literal (verified by sha256) — the rules text did not change.
GAME_PREAMBLE = (
    "You are playing a game of Werewolf with 9 players. The role line-up below is\n"
    "public knowledge — everyone knows these roles are in the game, but not who holds them.\n\n"
    + GAME_RULES
    + "\n"
)
