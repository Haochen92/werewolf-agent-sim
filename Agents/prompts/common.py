def build_system_prompt(*sections: str) -> str:
    """Join prompt sections with blank lines after stripping each section."""
    return "\n\n".join(section.strip() for section in sections)


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


TONE_INSTRUCTION = """
Speak naturally and conversationally, like you're playing a casual game with friends.
Keep statements short and direct. Don't over-explain your reasoning in a single message.
Avoid formal or legalistic phrasing — say "you still haven't answered" not
"your continued avoidance of this specific question makes your deflections increasingly suspicious."
Avoid canned openers and filler — don't start with "I agree with X that...", "fair point",
"good point", "classic wolf move", and don't mirror the structure of the message before yours.
A short reaction is fine; not every turn needs a full paragraph. If you agree with someone, add
a new reason or a new piece of information rather than just seconding what they said.
"""


DISCUSSION_SILENCE_RULE = """
Silence rule:
If you were directly addressed (asked a question or accused), you MUST respond this turn:
set pass_turn=false and answer or defend.
Otherwise, speak only if you have at least one of:
1. A new concrete observation not yet discussed.
2. A change in your suspicion with new reasoning.
3. Role-specific private information that makes speaking strategically necessary.
If none of those apply, set pass_turn=true to decline this turn.
Do NOT restate suspicions, repeat appeals for information, or agree without adding new reasoning.
When there is no concrete information yet, don't manufacture suspicion out of how talkative, quiet,
aggressive, or cautious someone is — it's acceptable to say there's little to go on. If you want to
move things forward, prefer information-generating moves: propose a concrete test, point to a
specific contradiction, or track the voting record once there is one.
"""


DAY_DISCUSS_RESPONSE_FORMAT = """
You must respond with a valid JSON.

When speaking:
{{
    "adopted_strategy_keys": [1, 3],
    "memory_applicability": [{{"memory_index": 1, "verdict": "partly_applies", "why": "short reason vs your current board"}}],
    "pass_turn": false,
    "message": "your discussion message",
    "updated_strategy": "your updated private strategy note for future turns",
    "addressed_targets": [{{"target": "player_2", "addressed_form": "response", "stance": "defense"}}]
}}

When declining to speak (only if you were NOT directly addressed):
{{
    "adopted_strategy_keys": [],
    "memory_applicability": [{{"memory_index": 1, "verdict": "does_not_apply", "why": "short reason vs your current board"}}],
    "pass_turn": true,
    "message": "",
    "updated_strategy": "your updated private strategy note for future turns",
    "addressed_targets": []
}}
"""
