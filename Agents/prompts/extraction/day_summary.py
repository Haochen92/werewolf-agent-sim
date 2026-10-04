"""In-game day-summary extraction prompt (run DURING play by summary_agent).

v3 (2026-10-03): the summary is the only account of a past day that agents ever see, so it is
written as attributed claims checked against the game master's record, never as narration. It is
given the record and the claims already on record; it no longer gets the situation-description
standards, which told it never to use player IDs, against its own rule to use them.

v4 (2026-10-04): the summariser only transcribes: the day's accusations, and each role claim with its
claimed night actions in fixed words. Checking claims against the record moved to code
(Agents/rules/claim_ledger.py), and alliances and village dynamics are gone (discussion_evidence.md §6.6).
A plan for a coming night is not a claimed action, and a vague result is not_said (2026-10-04: a
decoy "I'll check player_2 tonight" was logged as a night-2 investigation).
"""


DAY_SUMMARY_PROMPT = """You are a game analyst for a Werewolf game. Record today's public discussion in the structured fields. On later days the players read your record instead of the discussion itself, so it must be exact about who said what.

GAME CONTEXT:
{game_rules}

THE GAME MASTER'S RECORD SO FAR (exact announcements: night outcomes, healer saves, votes, revealed roles):
{public_record}

CLAIMS MADE IN EARLIER DAY DISCUSSIONS (with the game master's checks):
{claims_on_record}

DAY {current_day} PUBLIC DISCUSSION ONLY:
{day_channel}

Rules:
- Attribute everything. Write every statement about the game as something a named player said or argued ("player_8 claimed that player_2 survived an attack"). Never state a player's claim as fact, including the premise an accusation rests on.
- Accusations: every distinct accusation is a separate entry with ALL participating accusers listed. Record the target's defence, and who else argued against it and why.
- The game master's record above is the only source of fact. If an accusation rests on a public event the record contradicts, or one the game master would have announced but did not (a death, a healer save, a vote), say so in record_check and cite the record. Private night results (investigations, protections, a held shot) are never announced, so their absence from the record is not a conflict. An accusation repeated by several players is still a claim.
- Role claims: list every role claim made today, including a player repeating an earlier claim, and mark a withdrawn claim as retracted. Record each night action the player claimed (investigate, protect, shoot, kill) with its night, target and result, using only the allowed result words. Transcribe what they said; do not judge whether it is true.
- A night action is one the player says already happened. A plan for a coming night ("I'll check player_2 tonight") is not a night action: leave it out. If the player gave no result, or only a vague one ("got nothing useful"), the result is not_said.
- Do not include the formal vote tally or night event outcomes (these are recorded separately). However, DO include when players reference past votes or declare current voting intentions during discussion.
- Use player IDs (player_1, player_2, etc.), not role names, since roles are generally unknown during the game.
- A dead player's role, revealed by the game master, is a fact, not a claim: do not list it as a role claim.
- A healer save announced by the game master shows the player was attacked and protected. It does NOT clear them: a wolf can be attacked by the serial killer or the vigilante and saved. Only the attacker type the game master names is fact.
- Be specific about what was said and claimed, not vague summaries.
"""
