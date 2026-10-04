"""Day-summary agent: the `llm.invoke` (with retry + raw-channel fallback) that condenses one
day's discussion into the plain-text DaySummary block, plus the structured→text serializer it
returns. The graph node (flow.summarize_day_discussion) wraps this call in its DaySummaryCase
eval span.
"""

from __future__ import annotations

from logging import getLogger

from Agents.prompts.prompt_formatters import format_claims_on_record, format_day_channel
from Agents.llm_factory import get_llm_summary
from Agents.prompts import DAY_SUMMARY_PROMPT, GAME_RULES
from Agents.rules.claim_ledger import ClaimedAction, action_text
from Agents.schemas import DaySummary, DaySummaryOutput, DaySummaryOutputV4
from Agents.schemas.game_events import DeathRecord

logger = getLogger(__name__)

# v4: the summariser transcribes the day's accusations and role claims (with claimed night actions in
# fixed words); code keeps the ledger and checks it against the record (Agents/rules/claim_ledger.py).
_SUMMARY_SCHEMA = DaySummaryOutputV4


def summary_context(day_summaries: list[DaySummary], dead_roster: list[DeathRecord] | None = None,
                    cast_role_counts: dict[str, int] | None = None) -> tuple[str, str]:
    """(public_record, claims_on_record) for the summariser: the game master's announcements so far,
    and the claim ledger with its checks, as players see it. Both are public."""
    record = "\n".join(
        f"[Day {s.day}] {s.summary.strip()}" for s in day_summaries if s.source == "game_master"
    ) or "Nothing announced yet."
    claims = format_claims_on_record(day_summaries, dead_roster, cast_role_counts)
    return record, claims or "None yet."


def run_day_summary_agent(
    current_day: int,
    current_day_messages: list,
    max_retries: int = 1,
    day_summaries: list[DaySummary] | None = None,
    dead_roster: list[DeathRecord] | None = None,
    cast_role_counts: dict[str, int] | None = None,
) -> tuple[str, str, dict]:
    """Summarise one day's messages into (summary_text, model_used, structured).

    `structured` is the DaySummaryOutputV4 as a dict (accusations / role_claims). Agents read the
    previous days from it (the claim ledger and the accusations, format_day_summaries); the text is
    what the replay drawer shows, and what agents read for a day stored without it. Retries the
    structured-output call; on repeated failure falls back to the raw formatted channel (model_used "",
    structured {}). `day_summaries` (the game so far), `dead_roster` and `cast_role_counts` give the
    game master's record and the claim ledger the summary is written against.
    """
    public_record, claims_on_record = summary_context(day_summaries or [], dead_roster, cast_role_counts)
    prompt = DAY_SUMMARY_PROMPT.format(
        current_day=current_day,
        day_channel=format_day_channel(current_day_messages),
        game_rules=GAME_RULES,
        public_record=public_record,
        claims_on_record=claims_on_record,
    )
    for attempt in range(max_retries + 1):
        try:
            llm = get_llm_summary()
            result = llm.with_structured_output(_SUMMARY_SCHEMA).invoke(prompt)
            return _serialize_day_summary(result), getattr(llm, "model", "") or "", result.model_dump()
        except Exception as exc:
            logger.warning(f"Day discussion summary failed for day {current_day}: {exc}")
            if attempt < max_retries:
                continue
            logger.error(
                f"Day discussion summary failed all retries for day {current_day}, "
                "using fallback"
            )
            return format_day_channel(current_day_messages), "", {}
    # Loop always returns inside; this satisfies type-checkers for the no-iteration case.
    return format_day_channel(current_day_messages), "", {}


def _serialize_day_summary(result: DaySummaryOutput | DaySummaryOutputV4) -> str:
    """Flatten the structured day summary into the plain-text block stored as the DaySummary: v4
    writes two headings (accusations, role claims); an older schema also writes its alliances and
    village dynamics. The replay drawer splits the text at these headings."""
    parts = []

    if result.accusations:
        acc_parts = []
        for a in result.accusations:
            # The model writes reasoning and defense as full sentences with their own
            # subjects, so the frame names the parties and lets the sentences speak.
            accusers = ", ".join(a.accusers)
            entry = f"{accusers} → {a.target}: {a.reasoning} (evidence type: {a.evidence_type})"
            if a.defense:
                entry += f" Defense: {a.defense}"
            # v3 fields: who disputed it, and where it conflicts with the game master's record.
            if getattr(a, "disputed_by", ""):
                entry += f" Disputed: {a.disputed_by}"
            if getattr(a, "record_check", ""):
                entry += f" Against the record: {a.record_check}"
            acc_parts.append(entry)
        parts.append("Key accusations and defenses: " + " | ".join(acc_parts))
    else:
        parts.append("Key accusations and defenses: None.")

    if result.role_claims:
        claims = []
        for c in result.role_claims:
            if getattr(c, "kind", "") == "retracted":
                claims.append(f"{c.player} retracted {c.claimed_role}")
                continue
            claim = f"{c.player} claimed {c.claimed_role}"
            actions = [
                action_text(ClaimedAction(n.night, n.action, n.target, n.result, 0))
                for n in getattr(c, "night_actions", [])
            ]
            if actions:
                claim += " — " + ", ".join(actions)
            if getattr(c, "evidence", ""):
                claim += f" ({c.evidence})"
            claims.append(claim)
        parts.append("Role claims: " + "; ".join(claims))
    else:
        parts.append("Role claims: None.")

    if not hasattr(result, "village_dynamics"):
        return "\n".join(parts)

    if result.alliances:
        blocs = [
            f"{', '.join(a.players)} aligned based on {a.basis}"
            for a in result.alliances
        ]
        parts.append("Alliances and blocs: " + "; ".join(blocs))
    else:
        parts.append("Alliances and blocs: None.")

    vd = result.village_dynamics
    parts.append(
        f"Village dynamics: {vd.information_landscape} "
        f"{vd.consensus} {vd.drivers}"
    )

    return "\n".join(parts)
