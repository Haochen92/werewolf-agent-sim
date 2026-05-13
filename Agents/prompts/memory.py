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

Your role-specific lens:
{role_lens}

Describe 1-3 distinct situations you are currently facing. Each situation will
be used as a semantic search query to retrieve relevant strategy advice, so
describe the GAME DYNAMICS, not just who said what.

Do not describe the same conflict from multiple angles.

For each situation, capture whichever of these dimensions are relevant:

INFORMATION LANDSCAPE
- Is the village information-rich (confirmed roles, voting evidence, caught
  lies) or information-starved (no leads, grasping at vibes)?
- What type of evidence is driving current suspicions: voting records,
  communication style, behavioral reads, or concrete claims?

CONSENSUS TEXTURE
- Is there a strong consensus forming, a fragile one, or no consensus at all?
- Is the push driven by one vocal player or a genuine multi-player convergence?
- Are people citing specific evidence or just echoing each other?

SOCIAL PRESSURE
- Who is under pressure and why? Is it evidence-based or vibes-based?
- Is anyone deflecting, over-defending, or conspicuously silent?
- Are accusations coordinated (possible wolf play) or organic?

GAME PHASE DYNAMICS
- What phase is the game in: early (no eliminations, no data), mid (some
  data, roles emerging), or endgame (few players, high stakes per vote)?
- What changed most recently: an elimination, a failed heal, a role reveal,
  a surprising vote?

FORMAT: Write each situation as a 2-3 sentence description of a game dynamic
you are facing. Do NOT name specific players; describe their behavior and
role in the dynamic (e.g., "one player is leading an accusation based on
communication style" not "Player 3 accused Player 5").

Do NOT include plans, recommendations, or what you should do. Only describe
what is happening.
"""
