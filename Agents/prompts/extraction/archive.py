"""Archived extraction prompts — superseded, kept for reference, NOT for new work.
VILLAGER_DAY_EXTRACTION_PROMPT = the v6 cheap-first slice (superseded by V6_CELL_EXTRACTION_PROMPT);
ARCHIVED_POSTGAME_EXTRACTION_PROMPT = the old v5 whole-game prompt (zero live usage)."""


# v6 dimension schema — villager·day cell (cheap-first re-extraction). Self-contained: it describes
# the NEW dimensional framework (criticality numbers + stakes-as-implication, consensus split, heat,
# target landscape) and does NOT reuse SITUATION_STANDARDS (which describes the old game_phase/
# consensus_texture/agent_exposure dimensions). The per-field micro-guidance lives in the
# VillagerDayObservation Field(description=) — this prompt frames the task + the criticality rule +
# the descriptive-only (state, not prescription) discipline. Used only by the re-extraction runner
# (evaluation/src/experiments/reextract_villager_day.py); the live extraction prompts are untouched.
VILLAGER_DAY_EXTRACTION_PROMPT = """
You are an expert strategic analyst reviewing this completed Werewolf game. Extract
episodic-memory lessons for the VILLAGER role, for the DAY phases only (day_discussion and
day_vote). Each observation is a FACT about what happened, written from a post-game omniscient
perspective — you know all roles, all private actions, and all outcomes — but it must describe the
BOARD STATE as it was readable at the moment the lesson applies, in the villager's epistemic voice.

GAME RULES:
{game_rules}

{epistemic_status_rule}

NAMING RULE: Never use player IDs (player_1, player_2, ...). Refer to players by role (the wolf, the
investigator, a villager, the healer) or by behavioral descriptors when disambiguating.

---

GAME DATA:

PLAYERS AND ROLES:
{formatted_roles}

FULL GAME DISCUSSIONS:
{formatted_discussions}

FINAL STRATEGY NOTES:
{formatted_strategy_notes}

GAME OUTCOME: {game_outcome}

---

TASK: Extract 6-12 villager day-phase observations from the game's pivotal day moments (discussion
and vote). Cover DISTINCT day situations — different criticality regimes (early with many alive vs
late near a game-ending parity), consensus textures, and target landscapes — not minor variations of
one moment. Span the days the game ran, not just one. Fill EVERY field.

SITUATION DIMENSIONS describe the board STATE only (what is TRUE on the board), with NO
should/recommend language — the "how to act" is the agent's job, never part of the situation:

- situation: the core dynamic — the concrete event or conflict and who is involved.
- information_landscape: what evidence exists and its type (information-rich vs information-starved).
- players_alive / distance_to_parity / is_swing: the EXACT criticality numbers at this moment — how
  many are alive; how many more eliminations until the leading evil faction reaches a game-ending
  parity; whether one result here flips which faction is winning. State the true numbers from the board.
- criticality_stakes: phrase the IMPLICATION of those numbers as board reality (e.g. "seven alive, a
  mislynch is still recoverable" or "one elimination from a wolf win, every vote decisive"), NOT a
  bare label like "endgame". Derive it FROM the numbers above so the two can never disagree.
- consensus_text / my_position / consensus_direction: how aligned the village is and on what basis;
  where the villager stands relative to that consensus; and whether the consensus aligns with,
  opposes, or is unrelated to the villager's own read of who the threats are.
- heat_now: how much suspicion rests on the villager right now, and on what basis.
- target_landscape: the candidate set this decision chooses among — who remains in contention, their
  public role status, and whether the case against each rests on evidence or on behavior.

OUTCOME (judged from the END of the game):
- approach: what the villager DID or failed to do in that situation.
- impact_on_final_game_outcome: the NET effect on the villager win condition. A move that helped in
  the moment but contributed to a later loss is a NET NEGATIVE — say so and name the causal chain. If
  genuinely untraceable, write 'unclear' and why.
- immediate_response: how others responded in the moment, before the longer-term consequence.
- net_verdict: one word — positive, negative, mixed, or unclear.
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
