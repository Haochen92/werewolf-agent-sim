SITUATION_STANDARDS = """
SITUATION DESCRIPTION STANDARDS

These standards apply everywhere a game situation is described: a mid-game
situation summary, a post-game observation scenario, a strategy point's
situation field, or a rewritten entry during deduplication.

DIMENSIONAL FRAMEWORK:
Ground situation descriptions in these dimensions as relevant:

- Information landscape: Is the village information-rich (confirmed roles,
  voting evidence, caught lies) or information-starved (no leads, speculative
  reads)? What TYPE of evidence is driving suspicion: voting records,
  communication style, behavioral patterns, or concrete claims?
- Consensus texture: How aligned is the village? Unified, fragile, split,
  or no consensus? Is it driven by evidence or social momentum? (Do not
  describe who is under pressure — that belongs in agent exposure.)
- Agent exposure: What is the agent's position — driving the push, aligned
  with consensus, under indirect scrutiny, or the primary target? What is
  the basis — specific evidence, behavioral reads, association with another
  player, or nothing concrete?
- Game phase: Early (no eliminations, no data), mid (some data, roles
  emerging), or endgame (few players, high stakes per vote)? What changed
  most recently?
- Core dilemma: In one sentence, what is the specific strategic tension or
  tradeoff the agent faces right now? This is the decision point, not the
  game state — e.g., "must contribute to discussion without revealing
  analytical depth that marks them as a power role" or "private info
  contradicts the emerging consensus."


SPECIFICITY TEST:
Before finalizing any situation description, check: if this were used as a
semantic search query, would it match only situations with similar dynamics,
or would it match any game where something vaguely similar happened? If the
latter, add qualifying detail from the dimensional framework.
"""


EPISTEMIC_STATUS_RULE = """
EPISTEMIC STATUS RULE:
Describe players' roles at the degree of certainty that matches what is
known from the assigned role's perspective. This is a spectrum, not binary:

1. Your own role and private findings — you know these directly.
   e.g. "you have identified a wolf through your investigation."
2. System-confirmed — role revealed by game mechanics (elimination, healer
   save announcement).
   e.g. "the eliminated player was revealed as the Investigator,"
   "the healer-saved player."
3. Claimed with strong evidence — a player claimed a role and public events
   support it (e.g., their finding was later confirmed by an elimination).
   e.g. "a player claiming Investigator whose guilty finding was confirmed
   when the accused was eliminated and revealed as a wolf."
4. Claimed with no evidence — a player made a role claim but nothing public
   validates it.
   e.g. "a player claiming Healer," "an unverified Investigator claim."
5. Unknown — no claim, no confirmation. Use behavioral descriptors only.
   e.g. "the aggressive accuser," "one quiet player," "the leading voice."

Never use player IDs (player_1, player_2). Use role-based or behavioral
descriptors instead.

GOOD: "You have identified a wolf through investigation and need to convince
the village without revealing your role." — the investigator's own private
knowledge is valid from their perspective.

GOOD: "A player claiming Investigator whose previous finding was confirmed
by elimination is now pushing a second accusation." — claimed role with
strong public evidence, described at the right certainty level.

GOOD: "After a player was eliminated and revealed as the Investigator, the
village realized they had lost their information source." — system-confirmed
role, post-elimination.

GOOD: "One player is relentlessly accusing another with no concrete evidence,
creating a deadlock." — unknown roles, behavioral descriptors only.

BAD: "A wolf was being targeted by the Investigator." — uses hidden ground
truth for both players. From a villager's perspective, this is just two
players in conflict.

BAD: "The wolves are trying to eliminate the Healer." — omniscient narrator
perspective. From the healer's perspective: "You suspect you may be targeted
based on your activity level."

BAD: "After the village mislynched the Investigator." — uses the hidden role
as if known at vote time. If revealed post-elimination: "After a player was
eliminated and revealed to be the Investigator."
"""
