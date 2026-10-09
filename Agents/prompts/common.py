import json

from pydantic import BaseModel


def build_system_prompt(*sections: str) -> str:
    """Join prompt sections with blank lines after stripping each section."""
    return "\n\n".join(section.strip() for section in sections)


# The line that asks the model for its "reads" (its guess of every other living player's role)
# before it decides. {read_targets} is filled with the living players' names, so the model cannot
# skip one. The wording was tested in a replay and the hallucination bench scores against it, so
# changing it is a prompt epoch.
READS_COMMIT_INSTRUCTION = (
    "\nBefore your decision, record your current read — one entry each for: "
    "{read_targets} (best-guess role, or 'unclear').\n"
)


# How to hold what you know. Read by every turn once the ten-seat prompts are wired (the review of
# 2026-10-09 asked for it): the game needs bluffing, so the rule is not "never invent", it is to keep
# three kinds of statement apart in your own reasoning and record.
REASONING_DISCIPLINE = """
Keep three things apart in your own reasoning: what the Game Master announced or you learned yourself
(fact), what other players said (their claims), and what you infer (your hypotheses). In public you may
say what serves you, including a bluff; a bluff is still a claim, and it never becomes a fact in your
own private notes. Never say the Game Master announced something it did not.
"""


# The "respond with" line of a ten-seat turn, generated from its output schema (Agents/schemas/
# lineup_output.py) so the fields cannot drift. The shared fields show a fixed example; the example
# read names no player and no role, since a named one gets copied.
_CONTRACT_EXAMPLES = {
    "strategy_verdicts": [{"strategy_index": 1, "verdict": "follow", "why": "short reason vs your current board"}],
    "memory_applicability": [{"memory_index": 1, "verdict": "partly_applies", "why": "short reason vs your current board"}],
    "reads": [{"player": "<exact player_id>", "why": "pushed the only counted lynch with no evidence",
               "suspected_role": "<a role from the line-up, or unclear>", "confidence": "low"}],
    "updated_strategy": "your updated private strategy note for future turns",
    "pass_turn": False,
    "message": "your discussion message",
}
"""The example value of each shared field; any other field shows its own description."""


def json_contract(schema: type[BaseModel]) -> str:
    """The "respond with" line: one example value per field, in the schema's order."""
    example = {}
    for name, field in schema.model_fields.items():
        example[name] = _CONTRACT_EXAMPLES.get(name, field.description)
    text = json.dumps(example, ensure_ascii=False)
    return "You must respond with a valid JSON:\n" + text.replace("{", "{{").replace("}", "}}")
