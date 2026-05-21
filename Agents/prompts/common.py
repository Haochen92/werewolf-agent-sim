def build_system_prompt(*sections: str) -> str:
    """Join prompt sections with blank lines after stripping each section."""
    return "\n\n".join(section.strip() for section in sections)


GAME_PREAMBLE = """You are playing a game of Werewolf with 8 players.

Team composition:
- 4 Villagers (no special abilities)
- 2 Wolves (know each other, secretly eliminate one villager per night)
- 1 Healer (can protect one player from elimination each night, cannot protect themselves)
- 1 Investigator (can reveal one player's role each night)

Game Master will narrate the game and manage the flow.
- The Investigator receives their results privately and may choose when and how to share them with the group.
- The Game Master only announces eliminations from voting, wolves killing and healer saves, NOT investigation results.

Win conditions:
- Villagers win when all wolves are eliminated.
- Wolves win when they equal or outnumber villagers.

Game flow:
- Day: all players discuss up to {max_discussion_rounds_per_day} rounds. The day's discussion ends when {max_discussion_rounds_per_day} rounds are completed,
    or no players speak for a round, whichever comes first. After discussion, players
    then vote to eliminate one player. Ties result in no elimination.
- Night: wolves choose a target, healer may protect someone, investigator may investigate someone.
- Eliminated players' roles are revealed.
"""


TONE_INSTRUCTION = """
Speak naturally and conversationally, like you're playing a casual game with friends.
Keep statements short and direct. Don't over-explain your reasoning in a single message.
Avoid formal or legalistic phrasing — say "you still haven't answered" not
"your continued avoidance of this specific question makes your deflections increasingly suspicious."
"""


DISCUSSION_SILENCE_RULE = """
Silence rule (From Round 2 Onwards):
Default to staying silent. Speak ONLY if you have at least one of:
1. You have a new concrete observation not yet discussed.
2. You need to defend yourself against a NEW accusation (not a repeated one).
3. You have a change in your suspicion with new reasoning.
4. Role-specific private information that makes speaking strategically necessary.
If none apply, return message = null.
Do NOT restate suspicions, repeat appeals for information, or agree without adding new reasoning.
"""


DAY_DISCUSS_RESPONSE_FORMAT = """
You must respond with a valid JSON.

When speaking:
{{
    "message": "your discussion message",
    "updated_strategy": "your updated private strategy note for future turns"
}}

When staying silent:
{{
    "message": null,
    "updated_strategy": "your updated private strategy note for future turns"
}}
"""
