DAY_DISCUSSION_MEMORY_CONTEXT = """
Relevant observations: (These are specific, detailed observations from past games that are relevant to the current situation):
{retrieved_observations}

Dynamic strategy points (strategies from past games relevant to your current situation):
{strategy_points}

Adaptive Strategic thinking:
    You have a private strategy note from your previous turns:
    {previous_strategy}

    Update your strategy notes based on new information, relevant observations. If your current approach
    resembles a pattern that led to a bad outcome, adjust.
    You can reference dynamic strategy points to refine your approach, but do not apply rigidly.
    Keep your strategy notes concise (3-5 sentences).
    This is private and will not be shared with other players.
"""


DAY_VOTE_MEMORY_CONTEXT = """
Relevant observations: (These are specific, detailed observations from past games that are relevant to the current situation):
{retrieved_observations}

Dynamic strategy points (strategies from past games relevant to your current situation):
{strategy_points}
"""


SITUATION_ROLE_LENS = {
    "wolf": "Also note: which villager is most dangerous to leave alive, and whether the pressure on your team could be redirected.",
    "villager": "Also note: who is being evasive, voting inconsistencies, and unresolved accusations.",
    "healer": "Also note: who most needs protection, whether your activity level risks exposing you, and whether it's time to claim.",
    "investigator": "Also note: whether your private findings align with or contradict the public consensus, and whether your communication style is marking you as a power role.",
}


SITUATION_SUMMARY_PROMPT = """You are an AI agent playing Werewolf.
Your role: {player_role}
Current day: {current_day}, Round: {current_round}

Recent game events and discussion:
{recent_events}

Your current strategy note:
{previous_strategy}

{situation_standards}

Your role-specific lens:
{role_lens}

Describe 1-3 distinct situations you are currently facing. Each situation will
be used as a semantic search query to retrieve relevant strategy advice, so
describe the GAME DYNAMICS, not just who said what.

Do not describe the same conflict from multiple angles.

FORMAT: Write each situation as a 2-3 sentence description of a game dynamic
you are facing.

Do NOT include plans, recommendations, or what you should do. Only describe
what is happening.
"""
