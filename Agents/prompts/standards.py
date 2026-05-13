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
- Consensus texture: Is there a strong consensus, a fragile one, or none?
  Is the push driven by one vocal player or a genuine multi-player
  convergence? Are people citing specific evidence or echoing each other?
- Social pressure: Who is under pressure and why? Is it evidence-based or
  vibes-based? Are accusations coordinated (possible wolf play) or organic?
- Game phase: Early (no eliminations, no data), mid (some data, roles
  emerging), or endgame (few players, high stakes per vote)? What changed
  most recently?

Not every dimension applies to every situation. Use the ones that make the
situation recognizable and distinguishable.

EPISTEMIC STATUS RULE:
Refer to players by their publicly known role status at the time of the
situation, not by hidden ground truth and not by player IDs:

- System-confirmed role or status: use the public fact directly, e.g.
  "the confirmed wolf," "the eliminated villager," "the healer-saved player."
- Claimed and supported by already-public evidence: describe the claim and
  evidence, e.g. "the player who claimed investigator and correctly identified
  a confirmed wolf."
- Claimed but unvalidated: describe it as a claim, e.g. "a player claiming
  healer."
- Unknown roles: use behavioral descriptors, e.g. "the accuser," "the leading
  voice," "one quiet player," "the target."

SPECIFICITY TEST:
Before finalizing any situation description, check: if this were used as a
semantic search query, would it match only situations with similar dynamics,
or would it match any game where something vaguely similar happened? If the
latter, add qualifying detail from the dimensional framework.

GOOD: "The village is in the early game with no eliminations and no concrete
evidence. One player is pushing an accusation based entirely on another
player's phrasing and tone, and two others are echoing the suspicion without
adding independent reasoning."

GOOD: "The village is in the midgame after a confirmed wolf was eliminated,
and current suspicion is driven by voting records. One player is under pressure
for having voted with the confirmed wolf against the eliminated villager, while
others are treating that vote alignment as stronger evidence than tone reads."

GOOD: "A player has claimed investigator and correctly identified a confirmed
wolf, creating a strong but still socially contested information source. The
remaining discussion centers on whether to trust the claim's public track
record or treat the timing of the reveal as suspicious."

BAD: "After a mislynch, the village needed to identify the wolves."
"""
