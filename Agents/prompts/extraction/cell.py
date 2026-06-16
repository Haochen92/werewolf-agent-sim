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


# STUB — strategy-points tail, appended AFTER the observation tail for the dual-extraction path.
# Not finalized: the SP fields + output schema land with the strategy-points work; this placeholder
# fixes the shape (prefix + obs tail + sp tail) so the prefix never has to be re-cut later.
CELL_STRATEGY_TAIL = """
---

STRATEGY POINTS — derive for: role = {role}, phase = {phase}.   [STUB — not finalized]

From the {role} observations above, derive prescriptive strategy points for the {phase} phase: reusable
IF-situation -> THEN-action rules, each anchored to the SAME dimensional situation as the observations
so it retrieves the same way. (Strategy-point fields/schema are defined with the strategy-points work;
this tail is a placeholder so the dual-extraction shape is visible.)
"""
