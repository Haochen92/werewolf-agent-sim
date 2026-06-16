"""v6 per-cell post-game extraction (current). OFFLINE only (reextract_cells.py) — not wired into
the live graph. Parameterized by role/phase; the bound cell schema decides which fields appear."""


# v6 GENERAL per-cell extraction (step 4 full-DAG roll). Same framing as VILLAGER_DAY_EXTRACTION_PROMPT
# but parameterized by {role}/{phase}; the bound per-cell schema decides WHICH structured fields are
# requested (night cells omit consensus/heat; villager·day omits forward_exposure/public-private), so
# the dimension menu below can describe them all — the model only fills the fields its schema has.
V6_CELL_EXTRACTION_PROMPT = """
You are an expert strategic analyst reviewing this completed Werewolf game. Extract episodic-memory
lessons for the {role} role, for the {phase} phase only. Each observation is a FACT about what
happened, written from a post-game omniscient perspective (you know all roles, private actions, and
outcomes), but it must describe the BOARD STATE as it was readable at the moment the lesson applies,
in the {role}'s own epistemic voice.

GAME RULES:
{game_rules}

{epistemic_status_rule}

NAMING RULE: Never use player IDs (player_1, player_2, etc.) in ANY field — including when the lesson
is about WHICH player you targeted at night. Always refer to players by their role (the wolf, the
investigator, a villager, the healer); when disambiguating multiple players of the same role, use
behavioral descriptors, at the certainty the epistemic rule allows.

Good: "the wolf who led the early accusation", "the quiet villager you investigated", "the surviving wolf"
Bad:  "player_2", "you investigated player_5", "a villager (player_3)"

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

TASK: Extract 6-12 {role} observations from the game's pivotal {phase} moments (a phase with few
decisions may yield fewer; never pad with near-restatements). Cover DISTINCT situations — different
criticality regimes (early/many-alive vs late/near-parity), and different target/consensus/exposure
textures — not minor variations of one moment. Span the days the game ran. Fill EVERY field below.

EXTRACTION GUIDELINES:
- Write every field from the {role}'s own perspective. `approach` = what the {role} DID or FAILED TO
  DO, never what the opposing side did; if the lesson is about something that happened TO the {role},
  reframe it as what the {role} did that led there.
- Look for multi-day patterns — causal chains and strategic sequences, not just single-day events.
- Keep each field concise (1-2 sentences).
- QUALITY BAR: EXCLUDE common-sense fundamentals the base strategy already covers (e.g. "vote with the
  majority", "protect important players", "eliminate suspicious players"); EXCLUDE vague situations
  with no specific game dynamics; INCLUDE pivotal moments and non-obvious mechanisms tied to the
  dimensions (why a move worked or failed given the information/criticality/consensus/exposure).
- For day cells, tag each observation by WHEN the lesson applies: day_discussion (what to say, how to
  argue, reading others, managing suspicion) vs day_vote (vote target, timing, voting to preserve cover).

{driver_horizon}

RULES for the fields (describe board STATE, never prescription):
- Every situation field describes what is TRUE on the board at that moment, in the {role}'s epistemic
  voice — NO should/recommend language; the "how to act" is the agent's job, not part of the situation.
- Criticality: state the exact numbers AND phrase criticality_stakes as their IMPLICATION, derived
  FROM the numbers so the two can never disagree (fold in any conditioner — bullets left / partner
  revealed).
- Direction enums (consensus_direction, divergence_sign): judge ONLY from what is known or expressed
  at THIS moment, NEVER from who later turns out guilty/innocent; if there is no clear consensus, use
  no_clear_direction.

{situation_quality}

Fields to fill (your output schema requests exactly these — descriptions are authoritative):
{dimension_menu}
"""
