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
    "reads": [{"player": "<exact player_id>", "why": "pushed the only counted lynch with no evidence",
               "suspected_role": "<a role from the line-up, or unclear>", "confidence": "low"}],
    "updated_strategy": "your updated private strategy note for future turns",
    "pass_turn": False,
    "message": "your discussion message",
}
"""The example value of each shared field; any other field shows its own description."""


# The verdict fields' examples ride the {memory_verdict_example} variable instead: a turn shown no
# lessons sees no "strategy_index": 1 to copy, and its schema has no verdict field (owner, 2026-10-14;
# turn/action_space.output_schema_for_memory_shown).
VERDICT_EXAMPLES = {
    "strategy_verdicts": [{"strategy_index": 1, "verdict": "follow", "why": "short reason vs your current board"}],
    "memory_applicability": [{"memory_index": 1, "verdict": "partly_applies", "why": "short reason vs your current board"}],
}
VERDICT_EXAMPLES_PASS = {
    "strategy_verdicts": [{"strategy_index": 1, "verdict": "not_relevant", "why": "short reason vs your current board"}],
    "memory_applicability": [{"memory_index": 1, "verdict": "does_not_apply", "why": "short reason vs your current board"}],
}
MEMORY_VERDICT_SLOT = "{memory_verdict_example}"


def memory_verdict_example(fields: list[str], examples: dict = VERDICT_EXAMPLES, indent: str = "") -> str:
    """The verdict fields' example for the memory this turn was shown ("" when none), each as
    ``"name": value,`` on one line after ``indent`` (a one-line contract: no indent)."""
    sep = "\n" if indent else " "
    return "".join(f"{indent}{json.dumps(f)}: {json.dumps(examples[f], ensure_ascii=False)},{sep}" for f in fields)


def json_contract(schema: type[BaseModel]) -> str:
    """The "respond with" line: one example value per field, in the schema's order, the verdict
    fields as the {memory_verdict_example} slot."""
    parts, slot = [], ""
    for name, field in schema.model_fields.items():
        if name in VERDICT_EXAMPLES:
            slot = MEMORY_VERDICT_SLOT  # placed once, before the next field
            continue
        item = json.dumps({name: _CONTRACT_EXAMPLES.get(name, field.description)}, ensure_ascii=False)[1:-1]
        parts.append(slot + item.replace("{", "{{").replace("}", "}}"))
        slot = ""
    return "You must respond with a valid JSON:\n{{" + ", ".join(parts) + "}}"
