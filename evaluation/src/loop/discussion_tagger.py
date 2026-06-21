"""Compounding loop — (d) the OMNISCIENT per-day TAGGER (discussion + night).

One omniscient end-of-day flash-lite pass over the full day+night judges, per player:
  DISCUSSION — framing / credibility / role_reveal tags → ONE holistic de-luck verdict that WEIGHS them
               (tag-fine, credit-coarse: tags are the detection lens; the SP still gets one coarse value).
  NIGHT      — read-quality of that player's night target given the day's discussion: a SKILLED read vs a
               LUCKY hit. De-lucks `_night_credit`, which is outcome-only (hit_power/threat = partly luck).

Discussion has no deterministic de-luck proxy (the irreducible LLM job); night HAS one (`_night_credit`)
but it's outcome-luck — the tagger adds the read-quality the proxy can't see. Role-reveal is ANCHORED on
the persisted day-summary `role_claims` (the reliable in-game extraction; falls back to the raw messages
for pre-A4 records that lack it). Returns ({(day,player): disc_tag}, {(day,player):
night_tag}). Validated by the de-luck tests (does discussion beat the day-floor redundancy; does night
beat `_night_credit`'s halo).

A4 (2026-06-20): the agent's OWN reasoning (`updated_strategy`, already on the EvalCase — gameplay-neutral)
is fed in for ATTRIBUTION ONLY — de-confound night targets (discussion-driven read vs known-power-role
removal), surface the hidden read (formed but not voiced), trace influence. VALENCE stays on observable
behavior + true roles; the agent's account never drives merit (LLMs confabulate). structure-not-valence.
"""

from __future__ import annotations

import json
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger
from typing import Literal

from pydantic import BaseModel, Field

from Agents.llm_factory import get_llm_pro

logger = getLogger(__name__)


class TurnTag(BaseModel):  # all-required (flash-lite drops optional/nullable)
    player: str = Field(description="The player id this discussion tag is for.")
    verdict: Literal["positive", "neutral", "negative"] = Field(
        description="HOLISTIC: weighing framing, credibility and any role-reveal below, did this player's "
                    "discussion ADVANCE their own faction's win condition — judged omnisciently and "
                    "INDEPENDENT of whether the day's vote or the game went their way?")
    framing: Literal["none", "legitimate", "manipulative"] = Field(
        description="Steering suspicion: none / legitimate (toward a real threat) / manipulative.")
    credibility: Literal["low", "medium", "high"] = Field(
        description="How believable their claims/reads were to the room.")
    role_reveal: Literal["none", "own_role_claim", "challenge_claim"] = Field(
        description="Did they claim their own role, challenge someone's claim, or neither this day?")
    why: str = Field(description="One line: the faction-merit reason, outcome-independent.")


class NightTag(BaseModel):
    player: str = Field(description="The player id who took this night action.")
    verdict: Literal["positive", "neutral", "negative"] = Field(
        description="READ QUALITY of their night target given the day's discussion + true roles, judged "
                    "INDEPENDENT of whether the target happened to be valuable. positive = a SKILLED read "
                    "(the discussion justified targeting them); neutral = a blind/lucky pick with no basis; "
                    "negative = a misread that ignored available reads. Credit the READ, not a lucky hit.")
    read_quality: Literal["skilled", "reasonable", "blind_or_lucky", "misread"] = Field(
        description="The read behind the target choice.")
    why: str = Field(description="One line, outcome-independent.")


class DayTags(BaseModel):
    discussion: list[TurnTag] = Field(description="One tag per player who contributed to discussion.")
    night: list[NightTag] = Field(description="One tag per player who took a night action this day.")


_PROMPT = """You are an omniscient post-game analyst for a social-deduction game (3 factions: villagers /
wolves / serial_killer). You see ONE day's full PUBLIC discussion with TRUE ROLES revealed, the day's
vote, that night's actions, and that night's deaths.

Judge each player on the MERIT for THEIR OWN faction's win condition — omnisciently and INDEPENDENT of
whether the day's vote / the game happened to favor them (a good move in a lost game is still positive; a
lucky move is not). Deceivers advance by misdirection + useful survival; villagers by correctly finding
threats + accurate consensus.

DISCUSSION: weigh framing (steering suspicion), credibility, and any role-reveal into ONE holistic verdict.
role_reveal must reflect the DECLARED ROLE CLAIMS listed below (the reliable in-game extraction). Cross each
claim against TRUE ROLES: a claim whose role != the player's actual role is a FALSE claim = a strong
deception tell (manipulative framing / the room mis-trusting it should read as low credibility).
NIGHT: for each night action, judge the READ behind the target given the day's discussion — a SKILLED read
(discussion justified it) earns credit; a blind/lucky pick that merely happened to hit does NOT.

ATTRIBUTION INPUTS (A4) — the PRIVATE READS and the night-target rationales below are each player's OWN
account, captured before they acted; LLMs CONFABULATE, so use them ONLY to ATTRIBUTE, never for merit:
(i) tell whether a night target was a discussion-driven read vs. an obvious known-power-role removal;
(ii) surface a read a player FORMED BUT NEVER VOICED (a deception tell the public chat misses);
(iii) trace influence ("Y convinced me"). Take VALENCE only from observable behavior + true roles — never
from a player's own account of itself.

TRUE ROLES: {roles}
DAY {day} DISCUSSION:
{discussion}
DAY {day} DECLARED ROLE CLAIMS (in-game summary; cross vs TRUE ROLES — a claim != true role is a deception tell):
{role_claims}
DAY {day} PRIVATE READS (each agent's own account — ATTRIBUTION ONLY, not merit):
{private_reads}
DAY {day} VOTE RESULT: {lynch}
NIGHT {day} ACTIONS (target [why] = the actor's own rationale, ATTRIBUTION ONLY):
{night_actions}
NIGHT {day} DEATHS: {deaths}

Output: discussion tags (per meaningful contributor) + night tags (per night actor), each
outcome-independent."""


def _format_day(msgs: list[dict], roles: dict) -> str:
    lines = []
    for m in msgs:
        if m.get("passed"):
            continue
        tgt = m.get("addressed_targets") or []
        suffix = f"  [addresses: {tgt}]" if tgt else ""
        lines.append(f"{m.get('player')} ({roles.get(m.get('player'), '?')}): {m.get('message', '')}{suffix}")
    return "\n".join(lines) or "(no spoken messages)"


def _night_actions_by_day(record: dict) -> dict[int, list]:
    """[(player, role, target)] per day, from the game's night-action eval cases."""
    out: dict[int, list] = defaultdict(list)
    path = record.get("eval_cases_path")
    if not path or not os.path.exists(path):
        return out
    for cl in open(path):
        if not cl.strip():
            continue
        ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
        na = ec.get("agent_night_action")
        if ec.get("action_phase") == "night_action" and na and na.get("target"):
            out[ec.get("day")].append((ec.get("player_id"), na.get("role"), na.get("target")))
    return out


def _reasoning_by_day(record: dict) -> tuple[dict, dict]:
    """(A4) The agent's OWN reasoning (`updated_strategy`) per (day, player), split night vs discussion.
    Fed to the tagger for ATTRIBUTION ONLY (who/why), never valence: it de-confounds a night target (a
    discussion-driven read vs a known-power-role removal) and surfaces the HIDDEN READ (a read formed but
    not voiced — the deception tell the public chat misses). Carrier is the already-captured EvalCase
    field, so this is gameplay-NEUTRAL (no new generation). Returns (night_reason, disc_reason), each
    {(day, player): reasoning}; for multi-turn discussion the last turn's read wins (their settled read)."""
    night_reason: dict = {}
    disc_reason: dict = {}
    path = record.get("eval_cases_path")
    if not path or not os.path.exists(path):
        return night_reason, disc_reason
    for cl in open(path):
        if not cl.strip():
            continue
        ec = (json.loads(cl).get("output") or {}).get("eval_case") or {}
        why = (ec.get("updated_strategy") or "").strip()
        if not why:
            continue
        key = (ec.get("day"), ec.get("player_id"))
        phase = ec.get("action_phase")
        if phase == "night_action":
            night_reason[key] = why
        elif phase == "day_discussion":
            disc_reason[key] = why
    return night_reason, disc_reason


def _role_claims_by_day(record: dict) -> dict[int, list]:
    """{day: [(player, claimed_role)]} from the in-game day-summary's STRUCTURED role_claims (persisted on
    DaySummary.structured). The reliable in-game extraction of who claimed what — fed to the tagger so
    role_reveal/credibility are ANCHORED on it (a claim whose role != the true role is a deception tell),
    rather than re-judged from raw chat (which under-detects). Empty for pre-A4 records with no structured
    field -> the tagger falls back to judging role_reveal from the messages alone."""
    out: dict[int, list] = defaultdict(list)
    for s in record.get("day_summaries", []) or []:
        for rc in (s.get("structured") or {}).get("role_claims", []) or []:
            p, cr = rc.get("player"), rc.get("claimed_role")
            if p and cr:
                out[s.get("day")].append((p, cr))
    return out


def tag_game(record: dict, max_workers: int = 8) -> tuple[dict, dict]:
    """Omniscient per-day tags. Returns ({(day,player): disc_tag}, {(day,player): night_tag}).
    flash-lite via get_llm_pro() (env-pin GOOGLE_GENAI_PRO_MODEL)."""
    roles = record.get("roles") or {}
    by_day: dict[int, list] = defaultdict(list)
    for m in record.get("day_channel") or []:
        by_day[m.get("day")].append(m)
    lynch = {dr.get("day"): dr.get("voted_player") for dr in record.get("day_resolutions", [])}
    deaths = {n.get("day"): n.get("deaths") for n in record.get("night_resolutions", [])}
    night_acts = _night_actions_by_day(record)
    night_reason, disc_reason = _reasoning_by_day(record)  # A4: attribution-only carrier
    role_claims = _role_claims_by_day(record)              # anchors role_reveal on the in-game extraction
    llm = get_llm_pro().with_structured_output(DayTags)

    def _tag(day: int):
        na = night_acts.get(day, [])
        na_str = "; ".join(
            f"{p}({r}) -> {t}" + (f"  [why: {night_reason[(day, p)][:240]}]" if (day, p) in night_reason else "")
            for p, r, t in na) or "(none)"
        pr_str = "\n".join(
            f"{p} ({roles.get(p, '?')}): {disc_reason[(day, p)][:240]}"
            for p in sorted({pp for (dd, pp) in disc_reason if dd == day})) or "(none captured)"
        rc_str = "; ".join(f"{p} claimed {cr}" for p, cr in role_claims.get(day, [])) or "(none)"
        prompt = _PROMPT.format(roles=roles, day=day, discussion=_format_day(by_day[day], roles),
                                role_claims=rc_str, private_reads=pr_str, lynch=lynch.get(day),
                                night_actions=na_str, deaths=deaths.get(day))
        try:
            res = llm.invoke(prompt, config={"run_name": f"tag_d{day}"})
            return day, (res if isinstance(res, DayTags) else DayTags.model_validate(res))
        except Exception as e:  # noqa: BLE001
            logger.warning("tag day %s failed: %s", day, e)
            return day, DayTags(discussion=[], night=[])

    disc: dict = {}
    night: dict = {}
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        for day, dt in pool.map(_tag, sorted(by_day)):
            for t in dt.discussion:
                disc[(day, t.player)] = t.model_dump()
            for t in dt.night:
                night[(day, t.player)] = t.model_dump()
    return disc, night


def tag_game_cached(record: dict, tags_dir: str | None, version: str = "v1",
                    max_workers: int = 8) -> tuple[dict, dict]:
    """PERSIST tags per game_id so the rolling-window credit recompute doesn't re-tag finished games.
    A played game's tags are immutable, so re-running `tag_game` over the window each generation is pure
    waste. Keyed by (game_id, version) — bump `version` when the tagger prompt changes so stale tags
    invalidate (same idea as the SHA-keyed embedding cache). tags_dir=None or no game_id => tag fresh."""
    gid = record.get("game_id")
    if not tags_dir or not gid:
        return tag_game(record, max_workers=max_workers)
    path = os.path.join(tags_dir, f"{gid}.{version}.json")
    if os.path.exists(path):
        data = json.load(open(path))
        unpack = lambda d: {(int(k.split("|", 1)[0]), k.split("|", 1)[1]): v for k, v in d.items()}
        return unpack(data["disc"]), unpack(data["night"])
    disc, night = tag_game(record, max_workers=max_workers)
    os.makedirs(tags_dir, exist_ok=True)
    pack = lambda m: {f"{d}|{p}": v for (d, p), v in m.items()}
    with open(path, "w") as f:
        json.dump({"disc": pack(disc), "night": pack(night)}, f)
    return disc, night
