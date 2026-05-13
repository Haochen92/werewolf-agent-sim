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

---

SHARED QUALITY STANDARDS

These standards apply to ALL outputs below — observations and strategy points alike.

DESCRIBING SITUATIONS — THE DIMENSIONAL FRAMEWORK:
When describing a game situation (whether as an observation scenario or a strategy
point situation), ground it in these dimensions as relevant:

- Information landscape: Is the village information-rich (confirmed roles, voting
  evidence, caught lies) or information-starved (no leads, speculative reads)?
  What TYPE of evidence is driving suspicion — voting records, communication style,
  behavioral patterns, or concrete claims?
- Consensus texture: Is there a strong consensus, a fragile one, or none? Is the
  push driven by one vocal player or a genuine multi-player convergence? Are people
  citing specific evidence or echoing each other?
- Social pressure: Who is under pressure and why? Is it evidence-based or
  vibes-based? Are accusations coordinated (possible wolf play) or organic?
- Game phase: Early (no eliminations, no data), mid (some data, roles emerging),
  or endgame (few players, high stakes per vote)? What changed most recently —
  an elimination, a failed heal, a role reveal, a surprising vote?

Not every dimension applies to every situation. Use the ones that make the
situation recognizable and distinguishable.

FIELD-SPECIFIC PERSPECTIVE RULE:
- Situation fields (both in observations and strategy points): describe each
  player according to their publicly known role status at that moment:
  - System-confirmed roles (post-elimination reveals, announced saves): use the
    role directly, e.g. "the confirmed wolf," "the eliminated villager."
  - Claimed roles with strong evidence: describe the claim and evidence, e.g.
    "a player who claimed investigator and correctly identified a confirmed wolf."
  - Unverified claims: describe them as claims, e.g. "a player claiming healer."
  - Unknown roles: use behavioral descriptors, e.g. "the accuser," "the target,"
    "one quiet player."
  This is what the in-game agent could see and describe. Do not use player IDs
  or hidden role knowledge.
- Approach and outcome fields (in observations only): use actual roles freely —
  "the wolf voted with the majority," "the target was actually the healer."
  This is the factual record for learning, not the search surface.
- Action fields (in strategy points): use the role the point is assigned to
  since the agent reading it knows their own role.

SPECIFICITY TEST:
Before finalizing any situation description, check: if this were used as a
search query, would it match ONLY games with similar dynamics, or would it
match any game where something vaguely similar happened? If the latter, add
qualifying detail from the dimensional framework above.

GOOD example:
  Situation: "The village is in the early game with no eliminations yet and no
  concrete evidence. One player is pushing an accusation based entirely on
  another player's phrasing and tone, and two others are echoing the suspicion
  without adding independent reasoning."
  Why good: specifies game phase (early, no data), evidence type (phrasing-based),
  consensus texture (one driver + echoes, no independent reasoning).

BAD example:
  Situation: "After a mislynch, the village needed to identify the wolves."
  Why bad: matches every post-mislynch state in every game. No distinguishing
  dynamics.

DO NOT USE PLAYER IDS:
Never use player IDs. For situation/search-surface text, use only role status
that was publicly knowable at the time. For factual observation approach/outcome
text and strategy actions, use actual roles where the field-specific rule allows it.

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
observations are FACTS about what happened. They serve as episodic memory
retrieved via semantic search in future games.

Format each observation as a single paragraph with three parts:
- Scenario: The game situation as it appeared at the time (using the dimensional
  framework and perspective rule above).
- Approach: What the agent(s) did in that situation.
- Outcome: What resulted — how others responded and the downstream consequences.
  You may reveal actual roles here since this is the factual record.

Guidelines:
- 2-4 sentences per observation.
- Assign each observation a perspective — the role that would find it most useful.
  The same event can produce separate observations for different roles if the
  lesson differs.
- Look for multi-day patterns — causal chains and strategic sequences, not just
  single-day events.
- Extract 8-15 observations that cover the game's key dynamics.

---

TASK 2: STRATEGY POINT EXTRACTION

Derive tactical hypotheses from the observations you extracted in Task 1. Each
strategy point is a PROPOSED principle — it may or may not hold in future games.
Your job is to distill the observation into a reusable hypothesis that preserves
the situational specificity.

For each principle:

**situation**: A "When..." or "If..." clause describing the game dynamic this
principle applies to. Use the same dimensional framework as your observations
so that the situation description aligns with how agents will describe their
own game state during play. This field is what semantic search matches against.

**action**: The concrete recommended action, including WHY it works in this
specific context. The action should capture a learned nuance, not restate
common-sense fundamentals.

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
  given specific information availability, consensus texture, or social dynamics.
- INCLUDE principles that refine previous strategies with new nuance.

Example principles:
- wolf situation: "When your wolf partner is under heavy suspicion and a
  multi-player voting consensus is forming against them with concrete evidence,
  leaving no realistic way to save them."
  wolf action: "Vote with the majority to eliminate your partner rather than
  casting a dissenting vote — a lone protest vote creates a permanent record
  that links you to the eliminated wolf when roles are revealed."

- villager situation: "When multiple players suddenly coordinate an aggressive
  accusation against one player based on communication style rather than voting
  evidence, and the target has no prior suspicious voting record."
  villager action: "Treat the coordinated push itself as a potential wolf
  signal — wolves amplify existing village paranoia rather than creating new
  accusations, so scrutinize the accusers' voting records across previous days."

Extract 4-8 principles per role. Focus on:
- What the winning side did right that should be repeated
- What the losing side did wrong that should be avoided
- Novel situations that produced a clear lesson
"""


ARCHIVED_POSTGAME_EXTRACTION_PROMPT = """
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
