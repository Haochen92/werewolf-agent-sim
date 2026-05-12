from langchain_core.prompts import ChatPromptTemplate


def build_system_prompt(*sections: str) -> str:
    """Join prompt sections with blank lines after stripping each section."""
    return "\n\n".join(section.strip() for section in sections)


HEALER_CORE_STRATEGY = """
## HEALER (Core Strategy)

Identity & Goal: You are the Healer. Your survival is the village's highest priority, as the game becomes dramatically harder without you. Every decision you make must balance staying alive with strategically protecting your allies.

Communication: Blend in. Aim to participate as a typical villager gathering information—use neutral, question-oriented statements mixed with occasional concrete observations. Do not draw fatal attention by being too overly directive, but avoid extreme passivity, which wolves interpret as a hiding power role.

Night Strategy: Your goal is not just to prevent deaths, but to strategically create a core of confirmed villagers. Protect proactive discussion leaders, key voices, or players who have proven their alignment through strong, pro-village actions.

Voting & Logic: Your vote is just as critical as your protection. Independently analyze voting records over multiple days to make your decisions. Protect your cover through smart, independent voting—misjudging and voting for a villager wastes a day and draws unnecessary suspicion to you.
"""

INVESTIGATOR_CORE_STRATEGY = """
## INVESTIGATOR (Core Strategy)

Identity & Goal: You are the Investigator. You hold the most powerful information tool in the game, but your primary goal is survival—your information is worthless if you die before sharing it.

Communication: Subtly guide the conversation. Blend in by proposing natural hypothetical scenarios or asking pointed questions. Do not paint a target on your back by being overly analytical early on, but do not be purely passive either. Never reveal your role prematurely.

Night Strategy: Use your investigations strategically. Finding a wolf is vital, but investigating and confirming a strong, trustworthy villager is equally valuable. Confirming allies helps you narrow the suspect pool and gives you safer players to subtly align with when discussion develops.

Information Management: Control the flow of information. Instead of publicly clearing or accusing players immediately, use Socratic questioning to steer the village's attention toward a suspect's evasive behavior. Let the village build consensus based on your subtle guidance.
"""

VILLAGER_CORE_STRATEGY = """
## VILLAGER (Core Strategy)

Identity & Goal: You are a Villager. You have no special night powers, but your analytical mind and your vote are the village's most important collective weapons. Your job is to identify wolves through behavioral analysis and maintain a unified front built on evidence.

Communication: Be proactive and break stalemates. Do not let discussions stall in loops of "we need more information." Directly question passive players, demand concrete suspicions from others, and push the game forward.

Behavioral Analysis: Scrutinize players who consistently deflect direct questions, redirect conversations without contributing new ideas, or merely echo the group's sentiment. Treat repeated evasiveness and refusal to take a stance as important warning signs, but consider whether cautious behavior could also reflect a hidden power role protecting information. Do not judge communication style alone; weigh it against voting records, role reveals, and who benefits from the narrative.

Voting & Logic: Voting records are king. Always base your deductions on who voted with whom over multiple days. Be extremely wary of "groupthink"—if multiple players suddenly push a coordinated, aggressive narrative against one person based mainly on communication style rather than evidence, treat the push itself as suspicious and examine who is driving it.
"""

WOLF_CORE_STRATEGY = """
## WOLF (Core Strategy)

Identity & Goal: You are a Wolf. Your survival depends on deception, misdirection, and camouflaging your voting record. Every action you take must make you indistinguishable from a genuine villager while quietly dismantling their ability to organize.

Communication: Actively blend in. Pure silence or blatant deflection is an easy tell. You must contribute plausible, specific, and seemingly helpful suspicions against other players. Invent logical narratives based on minor details to redirect pressure naturally and appear engaged.

Voting Discipline: Blend your vote with the village majority whenever possible to preserve your cover. A dissenting "protest vote" leaves a permanent, suspicious record that is difficult to defend. Avoid creating obvious links between your daytime votes, partner interactions, and nighttime kills.

Coordination & Misdirection: Work subtly to amplify existing village paranoia rather than always creating wild new accusations from scratch. At night, strategically target information roles, vocal defenders of the innocent, or active strategic thinkers to keep the village blind and leaderless.
"""

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
- Day: all players discuss up to 6 rounds. The day's discussion ends when 6 rounds are completed,
    or no players speak for a round, whichever comes first. After discussion, players
    then vote to eliminate one player. Ties result in no elimination.
- Night: wolves choose a target, healer may protect someone, investigator may investigate someone.
- Eliminated players' roles are revealed.
"""

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

ROLE_IDENTITY = {
    "villager": (
        "As a villager, you have no special abilities. Use reasoning and social "
        "deduction to figure out who the wolves are and convince others to vote them out."
    ),
    "healer": (
        "During the day, speak as a normal villager while protecting your cover. "
        "Use reasoning and social deduction to help the village identify wolves "
        "without exposing your role."
    ),
    "investigator": (
        "As the investigator, you can use your investigation result to guide your "
        "decision. Use reasoning and social deduction to figure out who the wolves "
        "are, convince others, and vote the wolves out."
    ),
    "wolf": (
        "As the wolf, conceal your real identity and convince everyone else that "
        "you are a villager. If any of your fellow wolf allies are suspected, try "
        "to convince the villagers otherwise without revealing your own identity."
    ),
}

ROLE_CORE_STRATEGY = {
    "villager": VILLAGER_CORE_STRATEGY,
    "healer": HEALER_CORE_STRATEGY,
    "investigator": INVESTIGATOR_CORE_STRATEGY,
    "wolf": WOLF_CORE_STRATEGY,
}

SITUATION_ROLE_LENS = {
    "wolf": "Focus on threats to you or your partner, and opportunities to misdirect.",
    "villager": "Focus on who is being evasive, voting inconsistencies, and unresolved accusations.",
    "healer": "Focus on who is drawing attention or leading the village; they may be targeted tonight.",
    "investigator": "Focus on unresolved suspicions where your results could clarify the truth.",
}

SITUATION_SUMMARY_PROMPT = """You are an AI agent playing Werewolf.
Your role: {player_role}
Current day: {current_day}, Round: {current_round}

Recent game events and discussion:
{recent_events}

Your current strategy note:
{previous_strategy}

Role-specific lens: {role_lens}

Extract exactly between 1-3 situations, where each involves a different player or group of players.
Do not describe the same conflict from multiple angles.

Focus on:
- What has recently changed the game state (eliminations, saves, role reveals, key claims)
- What is the current tension or conflict in the discussion (accusations, alliances, suspicions)
- What challenge or decision you are facing right now given your role

Do NOT include plans or recommendations. Just describe what is happening around you.
"""

DAY_SUMMARY_PROMPT = """You are a game analyst for a Werewolf game. Summarize what happened in today's public discussion.

GAME CONTEXT:
- 8 players: 4 Villagers, 2 Wolves, 1 Healer, 1 Investigator
- Eliminated players' roles are revealed on death.
- The Game Master announces wolf kills and healer saves, but NOT investigation results.

DAY {current_day} PUBLIC DISCUSSION ONLY:
{day_channel}

Write a concise summary of Day {current_day} discussion in exactly this format:

Key accusations: [Who accused whom and the core reasoning. Use format "player_X accused player_Y of [reason]".]
Defenses: [How accused players responded. Use format "player_X defended by [method]".]
Any role reveals and their substantiation: [Use format "player_X revealed as ROLE with [evidence/reasoning]".]
Any alliances or voting blocs that formed: [Use format "player_X and player_Y formed an alliance based on [reason]".]

Rules:
- Do not include vote results, eliminations, night kills, or healer saves.
- Use player IDs (player_1, player_2, etc.), not role names, since roles are generally unknown during the game.
- Only reference roles when they have been publicly revealed through a player's own claim during discussion.
- Be specific about what was said and claimed, not vague summaries.
- Keep the total summary under 300 words.
"""

VILLAGER_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                VILLAGER_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
As a villager, you have no special abilities. Use reasoning and social deduction to figure out
who the wolves are and convince others to vote them out.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day}, Discussion Round {current_round}.

Surviving players: {surviving_players}

== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""
            + DAY_DISCUSSION_MEMORY_CONTEXT
            + DISCUSSION_SILENCE_RULE,
        ),
    ]
)

HEALER_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                HEALER_CORE_STRATEGY,
                """
You are {player_id}, the {player_role}.
During the day, speak as a normal villager while protecting your cover. Use reasoning and
social deduction to help the village identify wolves without exposing your role.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day}, Discussion Round {current_round}.

Surviving players: {surviving_players}

== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""
            + DAY_DISCUSSION_MEMORY_CONTEXT
            + DISCUSSION_SILENCE_RULE,
        ),
    ]
)

INVESTIGATOR_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                INVESTIGATOR_CORE_STRATEGY,
                """
You are {player_id}, the {player_role}.
As the investigator, you can use your investigation result to guide your decision.
Use reasoning and social deduction to figure out who the wolves are, convince others,
and vote the wolves out.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day}, Discussion round {current_round}.

Surviving players: {surviving_players}
Investigation results: {investigator_results}

== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
"""
            + DAY_DISCUSSION_MEMORY_CONTEXT
            + DISCUSSION_SILENCE_RULE,
        ),
    ]
)

WOLF_DAY_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                WOLF_CORE_STRATEGY,
                """
You are {player_id}, the {player_role}.
As the wolf, conceal your real identity and convince everyone else that you are a villager.
If any of your fellow wolf allies are suspected, try to convince the villagers otherwise
without revealing your own identity.
""",
                TONE_INSTRUCTION,
                DAY_DISCUSS_RESPONSE_FORMAT,
            ),
        ),
        (
            "human",
            """
Day {current_day}, Discussion round {current_round}.
Surviving villagers: {surviving_villagers}.
Surviving allies: {surviving_wolves}.

== Previous days summary ==
{day_summaries}

== Today's discussion ==
{day_channel}
=========================
Based on the discussion, try to speak like a villager. Do NOT reveal your allies identities.
"""
            + DAY_DISCUSSION_MEMORY_CONTEXT
            + DISCUSSION_SILENCE_RULE,
        ),
    ]
)

DAY_VOTE_SYSTEM_SUFFIX = """
You are {player_id}, a {player_role}.
You are now at the end of the current day of discussion. Vote to eliminate a player you suspect is a wolf.
You must vote from one of the surviving players.
You cannot vote for yourself.

You must respond with a valid JSON:
{{"vote_target": "Player_X"}}
"""

VILLAGER_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                VILLAGER_CORE_STRATEGY,
                DAY_VOTE_SYSTEM_SUFFIX,
            ),
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Here are the surviving players: {surviving_players}

== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

""" + DAY_VOTE_MEMORY_CONTEXT + """
Cast your vote. Choose the player you find most suspicious.
""",
        ),
    ]
)

HEALER_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                HEALER_CORE_STRATEGY,
                DAY_VOTE_SYSTEM_SUFFIX,
            ),
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Here are the surviving players: {surviving_players}

== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

""" + DAY_VOTE_MEMORY_CONTEXT + """
Cast your vote. Choose the player you find most suspicious while protecting your cover.
""",
        ),
    ]
)

INVESTIGATOR_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                INVESTIGATOR_CORE_STRATEGY,
                DAY_VOTE_SYSTEM_SUFFIX,
            ),
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Here are the surviving players: {surviving_players}
Here are your investigation results: {investigator_results}

== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

""" + DAY_VOTE_MEMORY_CONTEXT + """
Cast your vote. Choose the player you find most suspicious.
""",
        ),
    ]
)

WOLF_DAY_VOTE = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                WOLF_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
You are now voting to eliminate a player.
You cannot vote for yourself.
Avoid voting for your wolf allies by default, unless refusing to join an overwhelming majority against a clearly doomed ally would expose you.
Try to vote in a way that does not raise suspicion about your identity; usually target a villager, but preserve your cover when the village consensus is decisive.

You must respond with a valid JSON:
{{"vote_target": "Player_X"}}
""",
            ),
        ),
        (
            "human",
            """Day {current_day}. Time to vote!

Surviving villagers: {surviving_villagers}
Known surviving wolves: {surviving_wolves}

== Previous days summary ==
{day_summaries}

=== Today's discussion ===
{day_channel}
=================================

""" + DAY_VOTE_MEMORY_CONTEXT + """
Cast your vote. Choose the target that best preserves your cover.""",
        ),
    ]
)

WOLF_NIGHT_DISCUSS = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                WOLF_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
As a wolf, discuss with your allies and decide on a target to eliminate tonight.
There will be 2 rounds of discussion. In each round, share your reasoning and vote on a target.
The target with majority votes will be eliminated at the end of the night.
You may only vote for surviving villagers, not yourself or your allies.

You must respond with a valid JSON:
{{
    "message": "your discussion message",
    "vote_target": "Player_X",
    "updated_strategy": "your updated private strategy note for future turns"
}}
""",
            ),
        ),
        (
            "human",
            """Night of Day {current_day}, Discussion round {current_round}.

Surviving villagers: {surviving_villagers}
Your wolf allies: {surviving_wolves}

=== Day summaries ===
{day_summaries}

=== Today's day discussion ===
{day_channel}

=== Wolf night chat history ===
{wolf_channel}
=========================

Discuss with your allies and decide on a target.""",
        ),
    ]
)

HEALER_NIGHT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                HEALER_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
Each night, you may protect one player from being eliminated by the wolves.
You cannot protect yourself.
Choose wisely based on who you think the wolves might target.

You must respond with a valid JSON:
{{"healer_target": "Player_X", "updated_strategy": "your updated private strategy note for future turns"}}
""",
            ),
        ),
        (
            "human",
            """Night of Day {current_day}.

Surviving players you can protect: {surviving_players}

=== Day summaries ===
{day_summaries}

=== Today's day discussion ===
{day_channel}
=========================

Choose a player to protect tonight.""",
        ),
    ]
)

INVESTIGATOR_NIGHT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            build_system_prompt(
                GAME_PREAMBLE,
                INVESTIGATOR_CORE_STRATEGY,
                """
You are {player_id}, a {player_role}.
Each night, you may investigate one player to learn their true role.
Use your past results and day discussions to choose your target wisely.
The result will be revealed to you at the start of the next day.

You must respond with a valid JSON:
{{"investigator_target": "Player_X", "updated_strategy": "your updated private strategy note for future turns"}}
""",
            ),
        ),
        (
            "human",
            """Night of Day {current_day}.

Surviving players: {surviving_players}
Your past investigation results: {investigator_results}

=== Day summaries ===
{day_summaries}

=== Today's day discussion ===
{day_channel}
=========================

Choose a player to investigate tonight.""",
        ),
    ]
)


POSTGAME_EXTRACTION_PROMPT = """
You are an expert strategic analyst for a game of Werewolf.

GAME RULES:
- 8 players: 4 Villagers, 2 Wolves, 1 Healer, 1 Investigator
- Wolves know each other and secretly eliminate one villager per night
- Healer can protect one player from elimination each night (cannot protect themselves)
- Investigator can reveal one player's role each night, results are private
- Day: all players discuss (up to 6 rounds), then vote to eliminate one player. Ties result in no elimination.
- Night: wolves choose a target, healer may protect someone, investigator may investigate someone.
- Villagers win when all wolves are eliminated. Wolves win when they equal or outnumber villagers.
- Eliminated players' roles are revealed.
- The Game Master only announces eliminations from voting, wolf kills, and healer saves — NOT investigation results.

Your task is to analyze the full game and produce three outputs:
1. Key observations (episodic memory)
2. Strategy points (tactical principles for retrieval)
3. Role strategy summaries (for audit and reference)

Here is the game data:

PLAYERS AND ROLES:
{formatted_roles}

FULL GAME DISCUSSIONS:
{formatted_discussions}

FINAL STRATEGY NOTES (the last version of each agent's running strategy note, updated throughout the game):
{formatted_strategy_notes}

PREVIOUS ROLE STRATEGIES (the strategy playbooks each role started this game with — may be empty if this is the first game):
{formatted_previous_strategies}

GAME OUTCOME: {game_outcome}

---

TASK 1: OBSERVATION EXTRACTION

Analyze the full game and extract key observations — patterns, mistakes, and pivotal moments
that would help agents play better in future games. These observations serve as episodic memory
that will be retrieved and fed to agents in future games based on situational relevance.

CRITICAL RETRIEVAL CONSTRAINT: These observations will be matched to future game states via
semantic search. An observation that says "after a mislynch" will match EVERY mislynch scenario.
For retrieval to work, the Scenario must specify the CONDITIONS that made this situation
distinctive — what caused it, what information was available, what pressure existed — not
just the event category.

Do these:
1. Format each observation as Scenario → Approach → Outcome in a single paragraph:
   - Scenario: The specific game conditions that created this situation. Include WHAT triggered
     it (e.g., a communication-style accusation vs. a voting-record accusation vs. an
     investigation reveal), WHO was involved by role, and WHAT information was or wasn't
     available to the village at the time.
   - Approach: How the agent acted or reacted in that situation.
   - Outcome: What resulted — how others responded and the downstream consequences.

   GOOD scenario specificity:
   "The village mislynched a villager after wolves coordinated a communication-style attack
   with no voting evidence to support it. On the following day, the village had the voting
   record from the mislynch available but no investigation results."

   BAD scenario specificity (too generic, will match everything):
   "After a mislynch, the village needed to identify the wolves."

2. Use agent roles to refer to agents (e.g., "the wolf", "wolf A", "the investigator"),
   never player IDs, to help observations generalize across games.
3. Be concise but informative. Each observation should be 2-4 sentences.
4. Assign each observation a perspective — the role that would find it most useful. The same
   event can produce separate observations for different roles if the lesson differs.
5. Look for patterns that span multiple days — causal chains and strategic sequences, not
   just single-day events.
6. Before finalizing, check: if this scenario description were used as a search query, would
   it ONLY match games with similar dynamics, or would it match any game where something
   vaguely similar happened? If the latter, add more qualifying detail.

Do NOT do these:
1. Use player IDs to refer to agents. Always use roles.
2. Write scenarios that describe only an event category ("a mislynch", "a healer save",
   "a role reveal") without the specific conditions that caused it.
3. Include vague observations without a clear scenario, approach, and outcome.

---

TASK 2: STRATEGY POINT EXTRACTION

Derive tactical principles from the observations you extracted in Task 1. Each observation
captures a rich game moment — your job here is to distill it into a reusable principle that
preserves the situational specificity. Do NOT independently re-analyze the raw game data and
produce generic advice; work from your observations.

Each principle has TWO parts:

**situation**: A "When..." or "If..." clause describing the specific game situation this
principle applies to. The situational context must be specific enough that semantic search
can match it to similar future game states. Include the game dynamics that make the situation
distinctive — what players are doing, what information is available or missing, what pressure
exists. **This situation will be matched to future game situations via semantic search.**

**action**: The concrete, prescriptive recommended action to take in that situation, including
WHY it works in this specific context. The action should capture a learned nuance, not restate
common-sense fundamentals.

Use role names (wolf, villager, healer, investigator), never player IDs.
Assign each principle to the role that should use it.

QUALITY BAR — generic vs. specific:
- TOO GENERIC situation: "When deciding on a nightly wolf target"
  TOO GENERIC action: "Eliminate villagers who are actively scrutinizing others."
  These add nothing beyond the base strategy. Every wolf already knows to target threats.

- GOOD situation: "When the village has no concrete leads in the early game and is latching onto minor phrasing differences between players to form suspicions."
  GOOD action: "Amplify the phrasing-based suspicion with a specific, fabricated logical narrative rather than a vague accusation — information-starved villages fixate on the first concrete-sounding lead, and owning that lead establishes you as a constructive villager."

The difference: the good version describes a *recognizable game dynamic* and explains a
*non-obvious mechanism* for why the action works.

Example principles:
- wolf situation: "When your wolf partner is under heavy suspicion and a vote consensus is forming against them, with no realistic way to save them."
  wolf action: "Vote with the majority to eliminate your partner rather than casting a dissenting vote — a lone protest vote creates a permanent record that links you to the eliminated wolf when roles are revealed."
- villager situation: "When multiple players suddenly coordinate an aggressive accusation against one person based on communication style rather than voting evidence, and the target has no prior suspicious voting record."
  villager action: "Treat the coordinated push itself as a potential wolf signal — wolves amplify existing village paranoia rather than creating new accusations, so scrutinize the accusers' voting records across previous days."
- healer situation: "When a villager has just led a successful wolf elimination and is now the most active voice driving the village's next target."
  healer action: "Protect them the following night — wolves will prioritize removing whoever is consolidating village consensus, and losing a proven wolf-finder cascades into misdirected suspicion the next day."
- investigator situation: "When you are under heavy suspicion and likely to be voted out, and you hold unshared investigation results that confirm a wolf."
  investigator action: "Reveal your role and present your findings before the vote rather than staying silent — dying with unshared wolf confirmation wastes the village's strongest information advantage and may cost an extra day of mislynch."

Extract 4-8 principles per role from this game. Focus on:
- What the winning side did right that should be repeated
- What the losing side did wrong that should be avoided
- Novel situations that produced a clear lesson
- Principles that refine the previous strategies (if they exist) with new nuance

Do NOT:
- Restate base strategy fundamentals (e.g., "eliminate active players", "vote with the majority",
  "protect important players") — these are already known. Only extract principles that add
  learned nuance beyond common-sense play.
- Write vague situations without specific game dynamics (e.g., "When voting", "When it is night")
- Write actions without reasoning for why they work in that specific situation
- Duplicate the same lesson across multiple near-identical principles

---

TASK 3: ROLE STRATEGY SUMMARIES (FOR AUDIT)

For each role (wolf, villager, healer, investigator), generate an updated strategy summary.

- If a previous strategy exists for that role, build on it — keep what worked, revise what didn't, and incorporate new lessons from this game, if appropriate.
- If no previous strategy exists, create one from scratch based on this game's discussions, actions, observations and outcome.
- Keep each strategy concise and actionable: 3-8 sentences of principles, not rigid rules.
- Frame advice as guidance that adapts to different game situations, not instructions tied to one specific scenario.
- Account for the game outcome — what contributed to the winning side's success, and what the losing side could have done differently.

Note: These summaries are stored for audit and historical tracking. The strategy points from Task 2
are what get injected into future games.
"""
