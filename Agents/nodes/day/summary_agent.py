"""Day-summary agent: the `llm.invoke` (with retry + raw-channel fallback) that condenses one
day's discussion into the plain-text DaySummary block, plus the structured→text serializer it
returns. The graph node (flow.summarize_day_discussion) wraps this call in its DaySummaryCase
eval span.
"""

from __future__ import annotations

from logging import getLogger

from Agents.prompts.prompt_formatters import format_day_channel
from Agents.llm_factory import get_llm_summary
from Agents.prompts import DAY_SUMMARY_PROMPT, GAME_RULES, SITUATION_STANDARDS
from Agents.schemas import DaySummaryOutput

logger = getLogger(__name__)


def run_day_summary_agent(
    current_day: int,
    current_day_messages: list,
    max_retries: int = 1,
) -> tuple[str, str, dict]:
    """Summarise one day's messages into (summary_text, model_used, structured).

    `structured` is the raw DaySummaryOutput as a dict (role_claims / accusations / alliances /
    village_dynamics) — persisted alongside the prose for the post-game tagger/credit (gameplay-neutral:
    agents see only the prose). Retries the structured-output call; on repeated failure falls back to the
    raw formatted channel (model_used "", structured {}).
    """
    prompt = DAY_SUMMARY_PROMPT.format(
        current_day=current_day,
        day_channel=format_day_channel(current_day_messages),
        situation_standards=SITUATION_STANDARDS,
        game_rules=GAME_RULES,
    )
    for attempt in range(max_retries + 1):
        try:
            llm = get_llm_summary()
            result = llm.with_structured_output(DaySummaryOutput).invoke(prompt)
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


def _serialize_day_summary(result: DaySummaryOutput) -> str:
    """Flatten the structured day-summary output (accusations, role claims, alliances,
    village dynamics) into the plain-text block stored as the DaySummary."""
    parts = []

    if result.accusations:
        acc_parts = []
        for a in result.accusations:
            accusers = ", ".join(a.accusers)
            entry = (
                f"{accusers} accused {a.target} of {a.reasoning} "
                f"(evidence type: {a.evidence_type})"
            )
            if a.defense:
                entry += f"; {a.target} defended by {a.defense}"
            acc_parts.append(entry)
        parts.append("Key accusations and defenses: " + " | ".join(acc_parts))
    else:
        parts.append("Key accusations and defenses: None.")

    if result.role_claims:
        claims = [
            f"{c.player} claimed {c.claimed_role} ({c.evidence})"
            for c in result.role_claims
        ]
        parts.append("Role claims: " + "; ".join(claims))
    else:
        parts.append("Role claims: None.")

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
