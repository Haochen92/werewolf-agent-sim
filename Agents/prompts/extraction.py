DAY_SUMMARY_PROMPT = """You are a game analyst for a Werewolf game. Extract a structured summary of today's public discussion.

GAME CONTEXT:
- 8 players: 4 Villagers, 2 Wolves, 1 Healer, 1 Investigator
- Eliminated players' roles are revealed on death.
- The Game Master announces wolf kills and healer saves, but NOT investigation results.

{situation_standards}

DAY {current_day} PUBLIC DISCUSSION ONLY:
{day_channel}

Extract all strategically important information from the discussion into the structured fields. Be exhaustive — every distinct accusation should be a separate entry with ALL participating accusers listed.

Rules:
- Do not include the formal vote tally or night event outcomes (these are recorded separately). However, DO include when players reference past votes or declare current voting intentions during discussion — both voting history and vote declarations are strategically critical.
- Use player IDs (player_1, player_2, etc.), not role names, since roles are generally unknown during the game.
- When a player claims a role, distinguish the certainty level in the evidence field:
  - Confirmed by death reveal: eliminated players' roles are publicly revealed — reference to a dead player's known role is a confirmed fact, NOT a claim. Do not list confirmed-dead roles as role_claims.
  - Claimed with public corroboration (e.g., "accusation confirmed by subsequent elimination")
  - Claimed without evidence (write "unverified")
  - A healer save announced by the Game Master confirms the player is not a wolf, but does NOT confirm their specific role.
  - Do not treat unverified claims as fact.
- Be specific about what was said and claimed, not vague summaries.
"""

POSTGAME_EXTRACTION_PROMPT = """
You are an expert strategic analyst for a game of Werewolf.

GAME RULES:
- 8 players: 4 Villagers, 2 Wolves, 1 Healer, 1 Investigator
- Wolves know each other and secretly eliminate one villager per night
- Healer can protect one player from elimination each night (cannot protect themselves)
- Investigator can reveal one player's role each night, results are private
- Day: all players discuss (up to 4 rounds), then vote to eliminate one player. Ties result in no elimination.
- Night: wolves choose a target, healer may protect someone, investigator may investigate someone.
- Villagers win when all wolves are eliminated. Wolves win when they equal or outnumber villagers.
- Eliminated players' roles are revealed.
- The Game Master only announces eliminations from voting, wolf kills, and healer saves — NOT investigation results.

{situation_standards}

ACTION PHASES:
Each observation and strategy point must be tagged with the game phase it
applies to:
- day_discussion: Lessons about what to say, how to argue, when to stay
  silent, how to read others, and how to manage suspicion during public
  discussion rounds.
- day_vote: Lessons about vote target selection, vote timing, voting to
  preserve cover, and reading voting patterns.
- night_action: Lessons about night target selection — who wolves should
  kill, who the healer should protect, who the investigator should
  investigate. Villagers have no night action — do not assign night_action
  to the villager perspective.

Tag based on WHEN THE LESSON APPLIES, not when the event occurred. A night
kill that teaches wolves whom to target is night_action. A night kill that
teaches villagers how to read the kill pattern the next morning is
day_discussion.

---

GAME DATA:

PLAYERS AND ROLES:
{formatted_roles}

FULL GAME DISCUSSIONS:
{formatted_discussions}

FINAL STRATEGY NOTES:
{formatted_strategy_notes}

PREVIOUS ROLE STRATEGIES:
{formatted_previous_strategies}

GAME OUTCOME: {game_outcome}

---

TASK 1: OBSERVATION EXTRACTION

Analyze the full game and extract key observations — patterns, mistakes, and
pivotal moments that would help agents play better in future games. These
observations are FACTS about what happened, written from a post-game
omniscient perspective. You know all roles, all private actions, and all
outcomes. They serve as episodic memory retrieved via semantic search in
future games.

NAMING RULE: Never use player IDs (player_1, player_2, etc.). Always refer to
players by their role (the wolf, the investigator, a villager, the healer).
When disambiguating multiple players of the same role, use behavioral
descriptors.

Good: "the wolf who led the early accusation", "the quiet villager",
      "the surviving wolf", "the eliminated villager"
Bad:  "player_2", "player_5 and player_8", "a villager (player_3)"

Each observation has structured fields:

- situation: The core game dynamic — what triggered the situation. Do not
  embed dimensional context here; use the dedicated dimensional fields below.
  1-2 sentences.
- information_landscape (required): What evidence exists and what type —
  information-rich (confirmed roles, voting records, caught lies) or
  information-starved (no leads, speculative reads). 1 sentence.
- game_phase (required): Early (no eliminations), mid (some data, roles
  emerging), or endgame (few players, high stakes). Note what changed most
  recently. 1 sentence.
- consensus_texture (optional): Village alignment — unified, fragile, split,
  or none. Driven by evidence or social momentum. Do not describe who is
  under pressure here. Only include if relevant to the situation.
- agent_exposure (optional): The agent's position — driving the push, aligned
  with consensus, under indirect scrutiny, or primary target. What is the
  basis. Only include if relevant to the situation.
- approach: What the agent(s) did in that situation. 1-2 sentences.
- outcome: What resulted — how others responded and the downstream
  consequences. 1-2 sentences.

PERSPECTIVE RULE:
Each observation is assigned to a specific role. ALL THREE narrative fields
(situation, approach, outcome) must be written from that role's perspective:
- situation: What that role is facing or must respond to.
- approach: What that role DID or FAILED TO DO — not what the opposing
  side did. If the key lesson is about something that happened TO the
  role (e.g., the Investigator was targeted), reframe the approach as
  what the role did that led to that outcome (e.g., "The Investigator
  had been highly visible after orchestrating the previous day's vote,
  making them a predictable target").
- outcome: The consequences from that role's perspective.

If you find the approach describing the opposing side's actions ("The
wolves identified..." in an Investigator observation), you have the
wrong perspective. Either reframe to the assigned role's actions, or
reassign the observation to the role whose actions you are actually
describing.

Guidelines:
- Each field should be 1-2 sentences. Keep the total observation concise.
- Assign each observation a perspective — the role whose actions or
  decisions are the subject of the observation. If the same event teaches
  different lessons to different roles, extract separate observations for
  each, with each one's approach describing that role's own actions.
- Assign each observation an action_phase — the phase where this lesson
  would be applied.
- Look for multi-day patterns — causal chains and strategic sequences, not
  just single-day events.
- For each role, extract 4-8 observations that cover the game's key dynamics
  across the relevant action phases.

---

TASK 2: STRATEGY POINT EXTRACTION

Derive tactical hypotheses from the observations you extracted in Task 1. Each
strategy point is a PROPOSED principle — it may or may not hold in future games.
Your job is to distill the observation into a reusable hypothesis that preserves
the situational specificity.

For each principle:

{epistemic_status_rule}

**situation**: A "When..." or "If..." clause describing the core game dynamic
this principle applies to. Do not embed dimensional context here; use the
dedicated dimensional fields below. Do not include recommended actions,
conditional strategy, or advice — those belong in the action field.
Strategy points are retrieved during gameplay — the situation must be
recognizable from the assigned role's perspective when other players' true
roles are unknown. Strictly follow the epistemic status rule above.

**information_landscape** (required): What evidence exists and what type —
information-rich (confirmed roles, voting records, caught lies) or
information-starved (no leads, speculative reads). 1 sentence.

**game_phase** (required): Early (no eliminations), mid (some data, roles
emerging), or endgame (few players, high stakes). Note what changed most
recently. 1 sentence.

**consensus_texture** (optional): Village alignment — unified, fragile, split,
or none. Driven by evidence or social momentum. Do not describe who is under
pressure here. Only include if relevant to the situation.

**agent_exposure** (optional): The agent's position — driving the push,
aligned with consensus, under indirect scrutiny, or primary target. What is
the basis. Only include if relevant to the situation.

**action**: The concrete recommended action, including WHY it works in this
specific context. The action should capture a learned nuance, not restate
common-sense fundamentals. This field may refer to the assigned role, since
the agent reading it knows their own role. Include conditional branches here
if the situation implies different responses for different findings.

**action_phase**: The game phase where this principle would be applied.

Assign each principle to the role that should use it.

DERIVATION RULE: Each strategy point should trace to one or more of your Task 1
observations. If you find yourself writing a strategy point that doesn't connect
to an observation, either you missed an observation in Task 1 or the point is
too generic.

QUALITY BAR — what to include vs. exclude:
- EXCLUDE common-sense fundamentals the base strategy already covers (e.g.,
  "eliminate active players," "protect important players," "vote with the
  majority"). Only extract principles that add learned nuance beyond obvious play.
- EXCLUDE vague situations without specific game dynamics.
- EXCLUDE actions without reasoning for why they work in that context.
- INCLUDE principles that capture non-obvious mechanisms — why a tactic works
  given specific information availability, consensus texture, or agent exposure.
- INCLUDE principles that refine previous strategies with new nuance.

Example principles:
- wolf, day_vote:
  situation: "When your wolf partner is under heavy suspicion and a multi-player
  voting consensus is forming against them, leaving no realistic way to save them."
  information_landscape: "Concrete evidence (voting records or caught lies)
  supports the case against your partner."
  game_phase: "Mid-game, at least one elimination has occurred."
  consensus_texture: "Strong multi-player convergence driven by specific evidence."
  agent_exposure: "The agent's wolf partner is the primary target; the agent is not yet under scrutiny."
  action: "Vote with the majority to eliminate your partner rather than casting
  a dissenting vote — a lone protest vote creates a permanent record that links
  you to the eliminated wolf when roles are revealed."

- villager, day_discussion:
  situation: "When multiple players suddenly coordinate an aggressive accusation
  against one player based on communication style rather than voting evidence,
  and the target has no prior suspicious voting record."
  information_landscape: "Suspicion is driven by tone and phrasing reads, not
  voting records or concrete claims."
  game_phase: "Early to mid-game, before strong evidence has emerged."
  agent_exposure: "The agent is not the target but is observing coordinated
  pressure against another player, possibly wolf-driven amplification."
  action: "Treat the coordinated push itself as a potential wolf signal — wolves
  amplify existing village paranoia rather than creating new accusations, so
  scrutinize the accusers' voting records across previous days."

Extract 4-8 principles per role. Focus on:
- What the winning side did right that should be repeated
- What the losing side did wrong that should be avoided
- Novel situations that produced a clear lesson
"""


ROLE_EXTRACTION_PROMPT = """
You are a {role} analyst reviewing this completed Werewolf game. Your goal is
to extract lessons specifically for the {role} agent — what worked, what failed,
and what the {role} should do differently in future games.

GAME RULES:
- 8 players: 4 Villagers, 2 Wolves, 1 Healer, 1 Investigator
- Wolves know each other and secretly eliminate one villager per night
- Healer can protect one player from elimination each night (cannot protect themselves)
- Investigator can reveal one player's role each night, results are private
- Day: all players discuss (up to 4 rounds), then vote to eliminate one player. Ties result in no elimination.
- Night: wolves choose a target, healer may protect someone, investigator may investigate someone.
- Villagers win when all wolves are eliminated. Wolves win when they equal or outnumber villagers.
- Eliminated players' roles are revealed.
- The Game Master only announces eliminations from voting, wolf kills, and healer saves — NOT investigation results.

{{situation_standards}}

ACTION PHASES:
Each observation and strategy point must be tagged with the game phase it
applies to:
- day_discussion: Lessons about what to say, how to argue, when to stay
  silent, how to read others, and how to manage suspicion during public
  discussion rounds.
- day_vote: Lessons about vote target selection, vote timing, voting to
  preserve cover, and reading voting patterns.
- night_action: Lessons about night target selection — who wolves should
  kill, who the healer should protect, who the investigator should
  investigate. Villagers have no night action — do not assign night_action
  to the villager perspective.

Tag based on WHEN THE LESSON APPLIES, not when the event occurred. A night
kill that teaches wolves whom to target is night_action. A night kill that
teaches villagers how to read the kill pattern the next morning is
day_discussion.

---

GAME DATA:

PLAYERS AND ROLES:
{{formatted_roles}}

FULL GAME DISCUSSIONS:
{{formatted_discussions}}

FINAL STRATEGY NOTES:
{{formatted_strategy_notes}}

PREVIOUS ROLE STRATEGIES:
{{formatted_previous_strategies}}

GAME OUTCOME: {{game_outcome}}

---

TASK 1: OBSERVATION EXTRACTION

Analyze the full game from the {role}'s perspective and extract key
observations — patterns, mistakes, and pivotal moments that would help the
{role} agent play better in future games. These observations are FACTS about
what happened, written from a post-game omniscient perspective. You know all
roles, all private actions, and all outcomes. They serve as episodic memory
retrieved via semantic search in future games.

NAMING RULE: Never use player IDs (player_1, player_2, etc.). Always refer to
players by their role (the wolf, the investigator, a villager, the healer).
When disambiguating multiple players of the same role, use behavioral
descriptors.

Good: "the wolf who led the early accusation", "the quiet villager",
      "the surviving wolf", "the eliminated villager"
Bad:  "player_2", "player_5 and player_8", "a villager (player_3)"

Each observation has structured fields:

- situation: The core game dynamic — what triggered the situation. Do not
  embed dimensional context here; use the dedicated dimensional fields below.
  1-2 sentences.
- information_landscape (required): What evidence exists and what type —
  information-rich (confirmed roles, voting records, caught lies) or
  information-starved (no leads, speculative reads). 1 sentence.
- game_phase (required): Early (no eliminations), mid (some data, roles
  emerging), or endgame (few players, high stakes). Note what changed most
  recently. 1 sentence.
- consensus_texture (optional): Village alignment — unified, fragile, split,
  or none. Driven by evidence or social momentum. Do not describe who is
  under pressure here. Only include if relevant to the situation.
- agent_exposure (optional): The agent's position — driving the push, aligned
  with consensus, under indirect scrutiny, or primary target. What is the
  basis. Only include if relevant to the situation.
- approach: What the {role} did in that situation. 1-2 sentences.
- outcome: What resulted — how others responded and the downstream
  consequences. 1-2 sentences.

Guidelines:
- Every observation must use perspective="{role}". All narrative fields
  (situation, approach, outcome) must be written from the {role}'s perspective.
- approach must describe what the {role} DID or FAILED TO DO — not what the
  opposing side did. If the key lesson is about something that happened TO the
  {role}, reframe as what the {role} did that led to that outcome.
- Each field should be 1-2 sentences. Keep the total observation concise.
- Assign each observation an action_phase — the phase where this lesson
  would be applied.
- Look for multi-day patterns — causal chains and strategic sequences, not
  just single-day events.
- Extract 4-8 observations that cover the game's key dynamics for the {role}
  across the relevant action phases.

---

TASK 2: STRATEGY POINT EXTRACTION

Derive tactical hypotheses from the observations you extracted in Task 1. Each
strategy point is a PROPOSED principle — it may or may not hold in future games.
Your job is to distill the observation into a reusable hypothesis that preserves
the situational specificity.

For each principle:

{{epistemic_status_rule}}

**situation**: A "When..." or "If..." clause describing the core game dynamic
this principle applies to. Do not embed dimensional context here; use the
dedicated dimensional fields below. Do not include recommended actions,
conditional strategy, or advice — those belong in the action field.
Strategy points are retrieved during gameplay — the situation must be
recognizable from the {role}'s perspective when other players' true
roles are unknown. Strictly follow the epistemic status rule above.

**information_landscape** (required): What evidence exists and what type —
information-rich (confirmed roles, voting records, caught lies) or
information-starved (no leads, speculative reads). 1 sentence.

**game_phase** (required): Early (no eliminations), mid (some data, roles
emerging), or endgame (few players, high stakes). Note what changed most
recently. 1 sentence.

**consensus_texture** (optional): Village alignment — unified, fragile, split,
or none. Driven by evidence or social momentum. Do not describe who is under
pressure here. Only include if relevant to the situation.

**agent_exposure** (optional): The agent's position — driving the push,
aligned with consensus, under indirect scrutiny, or primary target. What is
the basis. Only include if relevant to the situation.

**action**: The concrete recommended action, including WHY it works in this
specific context. The action should capture a learned nuance, not restate
common-sense fundamentals. This field may refer to the {role}, since
the agent reading it knows their own role. Include conditional branches here
if the situation implies different responses for different findings.

**action_phase**: The game phase where this principle would be applied.

Every principle must use perspective="{role}".

DERIVATION RULE: Each strategy point should trace to one or more of your Task 1
observations. If you find yourself writing a strategy point that doesn't connect
to an observation, either you missed an observation in Task 1 or the point is
too generic.

QUALITY BAR — what to include vs. exclude:
- EXCLUDE common-sense fundamentals the base strategy already covers (e.g.,
  "eliminate active players," "protect important players," "vote with the
  majority"). Only extract principles that add learned nuance beyond obvious play.
- EXCLUDE vague situations without specific game dynamics.
- EXCLUDE actions without reasoning for why they work in that context.
- INCLUDE principles that capture non-obvious mechanisms — why a tactic works
  given specific information availability, consensus texture, or agent exposure.
- INCLUDE principles that refine previous strategies with new nuance.

Extract 4-8 principles for the {role}. Focus on:
- What the {role} did right that should be repeated
- What the {role} did wrong that should be avoided
- Novel situations that produced a clear lesson for the {role}
"""


# Archived version

ARCHIVED_POSTGAME_EXTRACTION_PROMPT = """
You are an expert strategic analyst for a game of Werewolf.

GAME RULES:
- 8 players: 4 Villagers, 2 Wolves, 1 Healer, 1 Investigator
- Wolves know each other and secretly eliminate one villager per night
- Healer can protect one player from elimination each night (cannot protect themselves)
- Investigator can reveal one player's role each night, results are private
- Day: all players discuss (up to 4 rounds), then vote to eliminate one player. Ties result in no elimination.
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
