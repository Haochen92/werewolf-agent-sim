"""v6 per-cell post-game extraction, in the LIVE prefix/tail shape (mirrors ROLE_EXTRACTION_PREFIX/TAIL).

CELL_EXTRACTION_PREFIX is role/phase-NEUTRAL (framing + rules + epistemic + naming + the general
field-filling rules + quality + GAME DATA), so it is byte-identical across every (role, phase) cell of
a game — the unit cached once per game. The per-cell variation (role, phase, driver/horizon, and the
schema-derived dimension menu) lives in CELL_OBSERVATION_TAIL. CELL_STRATEGY_TAIL is a STUB appended
AFTER the observation tail for the upcoming dual strategy-points extraction.

Built by `Agents.memory.extraction.inputs.build_cell_extraction_prompt` (the live builder convention);
offline only (reextract_cells), not yet wired into the live graph. The old monolithic
V6_CELL_EXTRACTION_PROMPT (pre prefix/tail) is kept in archive.py for reference.
"""


# Role/phase-NEUTRAL — no {role}/{phase}/{dimension_menu}/{driver_horizon} here (those are in the tail),
# so this prefix is byte-identical across cells and caches once per game.
CELL_EXTRACTION_PREFIX = """
You are an expert strategic analyst reviewing this completed Werewolf game. You will extract
episodic-memory lessons for ONE role and ONE phase — named at the very end of these instructions.
Everything below describes HOW to extract; the final section says FOR WHOM. Each observation is a FACT
about what happened, written from a post-game omniscient perspective (you know all roles, private
actions, and outcomes), but it must describe the BOARD STATE as it was readable at the moment the
lesson applies, in the assigned role's own epistemic voice.

GAME RULES:
{game_rules}

{epistemic_status_rule}

NAMING RULE: Never use player IDs (player_1, player_2, etc.) in ANY field — including when the lesson
is about WHICH player was targeted at night. Always refer to players by their role (the wolf, the
investigator, a villager, the healer); when disambiguating multiple players of the same role, use
behavioral descriptors, at the certainty the epistemic rule allows.

Good: "the wolf who led the early accusation", "the quiet villager you investigated", "the surviving wolf"
Bad:  "player_2", "you investigated player_5", "a villager (player_3)"

EXTRACTION GUIDELINES (apply to every observation):
- Look for multi-day patterns — causal chains and strategic sequences, not just single-day events.
- Keep each field concise (1-2 sentences).
- QUALITY BAR: EXCLUDE common-sense fundamentals the base strategy already covers (e.g. "vote with the
  majority", "protect important players", "eliminate suspicious players"); EXCLUDE vague situations
  with no specific game dynamics; INCLUDE pivotal moments and non-obvious mechanisms tied to the
  dimensions (why a move worked or failed given the information/criticality/consensus/exposure).

RULES for the fields (describe board STATE, never prescription):
- Every situation field describes what is TRUE on the board at that moment, in the assigned role's
  epistemic voice — NO should/recommend language; the "how to act" is the agent's job, not part of the
  situation.
- Criticality: state the exact numbers AND phrase criticality_stakes as their IMPLICATION, derived
  FROM the numbers so the two can never disagree (fold in any conditioner — bullets left / partner
  revealed).
- Direction enums (consensus_direction, divergence_sign): judge ONLY from what is known or expressed
  at THIS moment, NEVER from who later turns out guilty/innocent; if there is no clear consensus, use
  no_clear_direction.

{situation_quality}

---

GAME DATA:

PLAYERS AND ROLES:
{formatted_roles}

FULL GAME DISCUSSIONS:
{formatted_discussions}

FINAL STRATEGY NOTES:
{formatted_strategy_notes}

GAME OUTCOME: {game_outcome}
"""


# Per-cell observation lock: role + phase + driver/horizon + the schema-derived dimension menu.
CELL_OBSERVATION_TAIL = """
---

ASSIGNED CELL — extract observations for: role = {role}, phase = {phase}.

Apply everything above EXCLUSIVELY to the {role} for the {phase} phase. Write every field from the
{role}'s own perspective: approach = what the {role} DID or FAILED TO DO, never what the opposing side
did; if the lesson is about something that happened TO the {role}, reframe it as what the {role} did
that led there. For day cells, tag each observation by WHEN the lesson applies: day_discussion (what to
say, how to argue, reading others, managing suspicion) vs day_vote (vote target, timing, voting to
preserve cover).

{driver_horizon}

TASK: Extract 6-12 {role} observations from the game's pivotal {phase} moments (a phase with few
decisions may yield fewer; never pad with near-restatements). Cover DISTINCT situations — different
criticality regimes (early/many-alive vs late/near-parity), and different target/consensus/exposure
textures — not minor variations of one moment. Span the days the game ran. Fill EVERY field below.

Fields to fill (your output schema requests exactly these — descriptions are authoritative):
{dimension_menu}
"""


# Strategy-points tail — appended AFTER the observation tail for the dual obs+sp extraction path.
# An SP is a recurring tactical RULE distilled from the observations above: same situation dims (the
# rule's IF), a single prescriptive `action` (the THEN), and two coarse classes of that action
# (direction/honesty) that keep rival moves distinct. {strategy_menu} = the prescriptive fields only
# (the situation dims are reused identically from the observation tail above).
CELL_STRATEGY_TAIL = """
---

STRATEGY POINTS — derive for: role = {role}, phase = {phase}.

From the {role} observations above, derive 3-8 reusable PRESCRIPTIVE strategy points for the {phase}
phase — generalized IF-situation -> THEN-action rules. The right grain is a RECURRING TACTICAL PATTERN:
- NOT a single-game retelling (that is an observation),
- NOT an overall game/day stance (that is base strategy the agent already has).

Each strategy point reuses the SAME situation dimensions as the observations above — fill them
IDENTICALLY in kind, so the rule retrieves alongside the observations it generalizes — PLUS these
prescriptive fields:
{strategy_menu}

RULES:
- A strategy point is ALWAYS a positive prescription (something to DO). If the only lesson is "X
  backfires", that is a negative observation — keep it OUT of the strategy points.
- Cover DISTINCT moves: points that differ in direction (offensive/defensive/positional) or honesty
  (honest/deceptive) are different rules, not variations of one. Do not pad with near-restatements.
- Ground each rule in what actually recurred across the {role} observations, not generic advice.
"""


# Cluster-synthesis prompt (the cluster_synth sp_source). Given ONE cluster of same-situation-regime
# observations (MIXED outcomes — the gate_key partition drops net_verdict on purpose), synthesize the
# generalized rule(s) the cluster teaches. Standalone (the cluster IS the input — no game transcript).
# The outcome SPREAD across the cluster is the weighting: a move that succeeded across many instances is
# a strong rule; one mostly contradicted becomes the corrective. {dimension_menu} is the FULL SP cell
# menu (situation dims + direction/honesty/action) — synthesis builds a fresh generalized situation.
CELL_SP_SYNTHESIS_PROMPT = """
You are distilling reusable strategy from a completed-game memory store for a Werewolf agent.

Below is a CLUSTER of observations that all share the same situation regime for role = {role},
phase = {phase}. They are post-game facts (omniscient) with varied outcomes — some moves helped, some
hurt. Your job: synthesize the GENERALIZED prescriptive rule(s) this cluster teaches.

OBSERVATIONS IN THIS CLUSTER:
{observations}

TASK: Emit 1-3 strategy points — generalized IF-situation -> THEN-action rules a {role} could apply
when this regime recurs.
- Use the outcome SPREAD as weighting: a move that succeeded across many observations is a strong rule;
  if the cluster mostly shows a move BACKFIRING, the rule is the corrective/opposite (still a positive
  "do"), not a restatement of the failure.
- A strategy point is ALWAYS a positive prescription (something to DO). Never emit "don't do X".
- Emit MORE than one only when the cluster genuinely teaches distinct moves (differing in direction or
  honesty); a tight single-lesson cluster yields exactly one. Do not pad.
- Fill the situation dimensions as a GENERALIZED situation representative of the whole cluster (not a
  copy of one observation), so the rule retrieves for the regime.

Fields to fill (descriptions authoritative):
{dimension_menu}
"""
