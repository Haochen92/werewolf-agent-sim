"""Compounding loop — (d) the OMNISCIENT per-day DISCUSSION TAGGER.

Discussion has no clean deterministic de-luck proxy (unlike votes/night), so an omniscient end-of-day LLM
(flash-lite) judges each player's day contribution on its MERIT for their faction — INDEPENDENT of whether
the day/game happened to go their way (the de-luck framing; a good move in a lost game is still good). It
also tags framing (the primitive deterministic can't detect) and credibility. Per-day chunked, concurrent.

Output verdict credits the FOLLOWED discussion SPs at that turn — richer than the day-vote-endpoint free
floor (tier 1). Validated INCREMENTALLY (Gate B): does it predict beyond that floor? An LLM "merit vs
outcome" judge is a hypothesis (same caveat as the synthesis de-luck re-judge), so its keep is earned by
that incremental check, not assumed.
"""

from __future__ import annotations

from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import Literal

from pydantic import BaseModel, Field

from Agents.llm_factory import get_llm_pro

logger = getLogger(__name__)


class TurnTag(BaseModel):  # all-required (flash-lite drops optional/nullable)
    player: str = Field(description="The player id this tag is for.")
    verdict: Literal["positive", "neutral", "negative"] = Field(
        description="Did this player's discussion that day ADVANCE their own faction's win condition, "
                    "judged omnisciently and INDEPENDENT of whether the day's vote or the game went "
                    "their way? positive = advanced it, negative = hurt it, neutral = no effect.")
    framing: Literal["none", "legitimate", "manipulative"] = Field(
        description="Did they steer suspicion onto someone? none / legitimate (toward a real threat) / "
                    "manipulative (away from truth or onto an ally's enemy).")
    credibility: Literal["low", "medium", "high"] = Field(
        description="How believable were their claims/reads to the room that day.")
    why: str = Field(description="One line: the faction-merit reason, outcome-independent.")


class DayTags(BaseModel):
    tags: list[TurnTag] = Field(description="One tag per player who contributed meaningfully this day.")


_PROMPT = """You are an omniscient post-game analyst for a social-deduction game (Werewolf-like, 3
factions: villagers / wolves / serial_killer). You see ONE day's full public discussion with TRUE ROLES
revealed, plus how the day's vote and that night resolved.

Judge EACH player who spoke meaningfully on the MERIT of their discussion contribution for THEIR OWN
faction's win condition — judged omnisciently and INDEPENDENT of whether the day's vote or the eventual
game happened to favor them. A good move in a game they later lost is still positive; a move that only
looked good because the dice fell their way is not. Deceivers (wolf/serial_killer) advance by misdirecting
the village and surviving usefully; villagers advance by correctly finding threats and building accurate
consensus.

TRUE ROLES: {roles}
DAY {day} DISCUSSION:
{discussion}
DAY {day} VOTE RESULT: {lynch}
NIGHT {day} DEATHS: {deaths}

For each meaningful contributor output: player, verdict (positive/neutral/negative for their faction),
framing (none/legitimate/manipulative), credibility (low/medium/high), and a one-line outcome-independent
reason."""


def _format_day(msgs: list[dict], roles: dict) -> str:
    lines = []
    for m in msgs:
        if m.get("passed"):
            continue
        tgt = m.get("addressed_targets") or []
        suffix = f"  [addresses: {tgt}]" if tgt else ""
        lines.append(f"{m.get('player')} ({roles.get(m.get('player'), '?')}): {m.get('message', '')}{suffix}")
    return "\n".join(lines) or "(no spoken messages)"


def tag_game(record: dict, model: str | None = None, max_workers: int = 8) -> dict:
    """Tag a finished game's discussion. Returns {(day, player): tag_dict}. flash-lite, per-day concurrent.
    model=None uses get_llm_pro() (env-pinnable to flash-lite via GOOGLE_GENAI_PRO_MODEL)."""
    roles = record.get("roles") or {}
    by_day: dict[int, list] = defaultdict(list)
    for m in record.get("day_channel") or []:
        by_day[m.get("day")].append(m)
    lynch = {dr.get("day"): dr.get("voted_player") for dr in record.get("day_resolutions", [])}
    deaths = {n.get("day"): n.get("deaths") for n in record.get("night_resolutions", [])}
    llm = get_llm_pro().with_structured_output(DayTags)

    def _tag(day: int):
        prompt = _PROMPT.format(roles=roles, day=day, discussion=_format_day(by_day[day], roles),
                                lynch=lynch.get(day), deaths=deaths.get(day))
        try:
            res = llm.invoke(prompt, config={"run_name": f"disc_tag_d{day}"})
            return day, (res if isinstance(res, DayTags) else DayTags.model_validate(res)).tags
        except Exception as e:  # noqa: BLE001
            logger.warning("disc_tag day %s failed: %s", day, e)
            return day, []

    out: dict = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for day, tags in pool.map(_tag, sorted(by_day)):
            for t in tags:
                out[(day, t.player)] = t.model_dump()
    return out
