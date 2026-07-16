"""Tell mining + detection — the LLM half of the tell pipeline, GRADUATED 2026-07-13 from the probes
in evidence/extraction/tell_extraction/scripts/ (tell_mining_probe.py, detector_probe.py — those stay frozen
records of the probe runs; this module is the maintained code). Prompts are the frozen artifacts the
goldens certified, copied verbatim into tell_prompts/ (mining v4 channel-split; detector det_v1
full-view + det_v2 split-view = the k=2 union, golden-parity verified CACHED at thinking=low,
2026-07-13).

Design constraints (read/tactic design record §3):
- The MINER is omniscient (true-roles header) and salience-biased — discovery only; it emits exhibitor
  player_ids, never roles or valence; lift arithmetic decides what a behavior indicates, later.
- The DETECTOR is role-blind (the leak-guard: a role-aware detector rubber-stamps "the wolf did
  wolf-things" and the hit-rate is circular) and exhaustive: one call per (game, player, channel, view);
  every scanned cell is a denominator entry by construction.
- Deterministic post-screens are STRUCTURAL only (role words, player ids, quote-not-in-record) — the
  semantic-eval-≠-string-parse rule; flagged rows never feed lift (tell_credit drops them).
"""

from __future__ import annotations

import glob
import json
import re
from collections import defaultdict
from pathlib import Path

from pydantic import BaseModel, Field

PROMPTS_DIR = Path(__file__).resolve().parent / "tell_prompts"
DETECTOR_MODEL = "gemini-3.1-flash-lite"
CACHE_MIN_TOKENS = 4096  # Vertex-enforced minimum (evidence/caching probe)

ROLE_WORDS = re.compile(
    r"\b(wolf|wolves|werewolf|villager|healer|investigator|vigilante|serial[ _-]?killer|town|evil)\b",
    re.IGNORECASE,
)
CERTAINTY_MARKERS = re.compile(r"\b(reveal|revealed|claiming|claimed|claims|claim)\b", re.IGNORECASE)
HIDDEN_RELATION = re.compile(
    r"\b(ally|allies|packmate|pack mate|teammate|team mate|their partner|fellow threat|valuable player)\b",
    re.IGNORECASE,
)
PLAYER_IDS = re.compile(r"\bplayer[_ ]?\d+\b", re.IGNORECASE)


# ── game record → public text (shared renderers) ──────────────────────────────────────────────


def _day_messages(rec: dict, day: int) -> list[dict]:
    return [m for m in rec["day_channel"] if m["day"] == day and not m.get("passed")]


def _render_votes(rec: dict, day: int) -> str:
    res = next((r for r in rec["day_resolutions"] if r.get("day") == day), None)
    if not res:
        return "No vote recorded."
    votes = ", ".join(f"{v['voter']} -> {v['votee']}" for v in res.get("votes", [])) or "none"
    lynched = res.get("voted_player") or "no one (no lynch)"
    return f"Votes: {votes}. Lynched: {lynched}."


def _render_day(rec: dict, day: int, include_votes: bool = True) -> str:
    lines = [f"{m['player']}: {m['message']}" for m in _day_messages(rec, day)]
    body = f"--- DAY {day} ---\n" + "\n".join(lines)
    return body + f"\n{_render_votes(rec, day)}" if include_votes else body


def _game_days(rec: dict) -> list[int]:
    return sorted({m["day"] for m in rec["day_channel"]
                   if not m.get("passed") and m["player"] != "game_master"})


def load_games(dumps_glob: str, n: int | None = None, skip: int = 0) -> list[dict]:
    games: list[dict] = []
    for path in sorted(glob.glob(dumps_glob)):
        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("status") == "success":
                    rec["_source"] = Path(path).name
                    games.append(rec)
    return games[skip:skip + n] if n is not None else games[skip:]


def _norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-").replace("…", "...")
    return re.sub(r"\s+", " ", s).strip().lower()


def _strip_vote_blocks(day_text: str) -> str:
    """The split-view transcript (det_v2 / mining v4's channel split): drop the per-voter tally lines
    and the "Votes:" summary so the compact structured block can't anchor a cheap model's attention;
    OUTCOMES stay (lynch results / GM announcements are public context discussion tells reference)."""
    return "\n".join(
        line for line in day_text.splitlines()
        if not (line.startswith("Votes: ") or "vote result for day" in line
                or (line.startswith("  ") and " voted for " in line))
    )


# ── mining (omniscient, discovery-only) ────────────────────────────────────────────────────────


class TellCandidate(BaseModel):
    exhibitor: str = Field(description="The player_id of the player who exhibited the behavior.")
    behavior: str = Field(
        description="One sentence, present tense, describing the behavior as a general pattern "
        "that could recur in another game. No player IDs, no role names, observable-only."
    )
    evidence_quote: str = Field(
        description="A short verbatim snippet (<=25 words) from this day's record showing the "
        "behavior — copied exactly, message text or vote line."
    )


class DayTells(BaseModel):
    tells: list[TellCandidate] = Field(
        description="Every distinct candidate tell exhibited this day; empty list if none."
    )


def screen_tell(tell: dict, day_text: str) -> list[str]:
    flags = []
    if ROLE_WORDS.search(tell["behavior"]) and not CERTAINTY_MARKERS.search(tell["behavior"]):
        flags.append("bare_role_word_in_behavior")
    if HIDDEN_RELATION.search(tell["behavior"]):
        flags.append("hidden_relation_in_behavior")
    if PLAYER_IDS.search(tell["behavior"]):
        flags.append("player_id_in_behavior")
    quote = _norm(tell["evidence_quote"]).strip(". ")
    if quote[:160] not in _norm(day_text):
        flags.append("quote_not_in_record")
    return flags


def _mine_day(llm, prompt_template: str, rec: dict, day: int, days: list[int], version: str,
              channel: str) -> list[dict]:
    from Agents.prompts.common import GAME_RULES

    roles_line = ", ".join(f"{p} = {r}" for p, r in sorted(rec["roles"].items()))
    prior = "\n\n".join(_render_day(rec, d) for d in days if d < day) or "(game start)"
    # discussion-layer call excludes the focus day's vote block: temporally the vote hasn't happened
    day_text = _render_day(rec, day, include_votes=(channel != "discussion"))
    prompt = prompt_template.format(
        game_rules=GAME_RULES, roles_line=roles_line,
        prior_days=prior, focus_day=day, day_record=day_text,
    )
    result = llm.invoke(prompt)
    rows = []
    for t in result.tells:
        row = {
            "game_id": rec["game_id"], "source": rec.get("_source", ""), "day": day,
            "exhibitor": t.exhibitor, "behavior": t.behavior,
            "evidence_quote": t.evidence_quote,
            "exhibitor_role": rec["roles"].get(t.exhibitor),  # deterministic join
            "winner": rec.get("winner"), "prompt_version": version,
            "channel": channel,
        }
        row["screen_flags"] = screen_tell(row, _render_day(rec, day))
        rows.append(row)
    return rows


def mine_games(games: list[dict], out_path: Path, version: str = "v4",
               workers: int = 8, llm=None) -> int:
    """Mine candidate tells from finished games — 2 channel-split calls per game-day (the v4 design).
    Appends nothing: writes `out_path` fresh; the fold owns accumulation. Returns rows written."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from Agents.llm_factory import get_llm_pro

    templates = {ch: (PROMPTS_DIR / f"{version}_{ch}.txt").read_text()
                 for ch in ("discussion", "vote")}
    llm = llm or (get_llm_pro().with_structured_output(DayTells)
                  .with_retry(stop_after_attempt=8, wait_exponential_jitter=True))  # tick path: no retry above (see tell_fold judge)
    tasks = [(rec, day, _game_days(rec), ch)
             for rec in games for day in _game_days(rec) for ch in templates]
    n_rows = 0
    with open(out_path, "w") as out, ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_mine_day, llm, templates[ch], rec, day, days, version, ch): (rec, day)
                   for rec, day, days, ch in tasks}
        for fut in as_completed(futures):
            rec, day = futures[fut]
            try:
                rows = fut.result()
            except Exception as e:  # noqa: BLE001 — one failed day-call must not kill the fold
                print(f"  MINE FAIL {rec['game_id'][:8]} day {day}: {e}", flush=True)
                continue
            for row in rows:
                out.write(json.dumps(row) + "\n")
                n_rows += 1
            out.flush()
    return n_rows


# ── detection (role-blind, exhaustive, k=2 union) ──────────────────────────────────────────────


class Detection(BaseModel):
    tell_id: str = Field(description="The id of the checklist tell that was exhibited.")
    day: int = Field(description="The day on which the focus player exhibited it.")
    evidence_quote: str = Field(
        description="A short verbatim snippet (<=25 words) from that day's record showing the "
        "behavior — copied exactly, message text or vote line."
    )


class PlayerDetections(BaseModel):
    detections: list[Detection] = Field(
        description="Every (tell, day) instance the FOCUS PLAYER exhibited; empty list if none."
    )


def _make_llm(cached_content: str | None = None, thinking: str = "low"):
    from Agents.llm_factory.backends import create_chat_model

    kwargs = {"cached_content": cached_content} if cached_content else {}
    return (create_chat_model(DETECTOR_MODEL, temperature=0.0,
                              thinking_level=thinking, **kwargs).with_structured_output(PlayerDetections)
            .with_retry(stop_after_attempt=8, wait_exponential_jitter=True))  # tick path: no retry above (see tell_fold judge)


def _create_prefix_cache(prefix: str) -> str | None:
    """Best-effort Vertex context cache for one (game, channel, view) prefix — the 9 per-player calls
    share a byte-identical rules+transcript+checklist prefix (the standing CACHED config, golden-parity
    verified 2026-07-13). Any failure returns None and the call falls back to uncached."""
    from Agents.llm_factory.backends import _use_vertex, create_chat_model

    if not _use_vertex() or len(prefix) / 4 < CACHE_MIN_TOKENS * 1.1:
        return None
    try:
        from langchain_core.messages import HumanMessage
        from langchain_google_genai import create_context_cache

        base = create_chat_model(DETECTOR_MODEL, temperature=0.0)
        return create_context_cache(base, messages=[HumanMessage(content=prefix)], ttl="900s")
    except Exception as e:  # noqa: BLE001 — caching must never break detection
        print(f"  cache creation failed ({e}); falling back to uncached", flush=True)
        return None


def _render_checklist(items: list[dict]) -> str:
    return "\n".join(f"[{t['tell_id']}] {t['text']}" for t in items)


def _build_prompt_parts(template: str, rec: dict, channel: str, checklist: dict,
                        split_view: bool) -> tuple[str, str]:
    from Agents.prompts.common import GAME_RULES

    days = _game_days(rec)
    if split_view and channel == "discussion":
        transcript = "\n\n".join(_strip_vote_blocks(_render_day(rec, d)) for d in days)
    else:
        transcript = "\n\n".join(_render_day(rec, d) for d in days)
    prefix_tpl, tail_tpl = template.split("FOCUS PLAYER:", 1)
    prefix = prefix_tpl.format(game_rules=GAME_RULES, transcript=transcript,
                               channel=channel.upper(),
                               checklist=_render_checklist(checklist[channel]))
    return prefix, "FOCUS PLAYER:" + tail_tpl


def _detect(llm, prompt: str, rec: dict, player: str, channel: str,
            version: str, valid_ids: set) -> list[dict]:
    days = _game_days(rec)
    result = llm.invoke(prompt)
    rows = []
    for d in result.detections:
        row = {
            "game_id": rec["game_id"], "source": rec.get("_source", ""), "channel": channel,
            "player": player, "tell_id": d.tell_id, "day": d.day,
            "evidence_quote": d.evidence_quote, "prompt_version": version,
        }
        flags = []
        if d.tell_id not in valid_ids:
            flags.append("unknown_tell_id")
        if d.day not in days:
            flags.append("day_out_of_range")
        elif _norm(d.evidence_quote).strip(". ")[:160] not in _norm(_render_day(rec, d.day)):
            flags.append("quote_not_in_record")
        row["screen_flags"] = flags
        rows.append(row)
    return rows


def _detect_pass(games: list[dict], checklist: dict, version: str, split_view: bool,
                 cache: bool, thinking: str, workers: int) -> tuple[list[dict], list[dict]]:
    """One detector pass over (game × player × channel). Returns (rows, scanned denominators)."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    from Agents.llm_factory.backends import create_chat_model

    template = (PROMPTS_DIR / f"{version}.txt").read_text()
    valid_ids = {ch: {t["tell_id"] for t in checklist[ch]} for ch in checklist}
    plain_llm = _make_llm(thinking=thinking)

    groups, cache_names = [], []
    for rec in games:
        for ch in ("vote", "discussion"):
            prefix, tail_tpl = _build_prompt_parts(template, rec, ch, checklist, split_view)
            name = _create_prefix_cache(prefix) if cache else None
            if name:
                cache_names.append(name)
            groups.append((rec, ch, prefix, tail_tpl,
                           _make_llm(name, thinking) if name else plain_llm, name is not None))

    tasks = [(rec, p, ch, tail_tpl.format(focus_player=p, channel=ch.upper()) if cached
              else prefix + tail_tpl.format(focus_player=p, channel=ch.upper()), llm)
             for rec, ch, prefix, tail_tpl, llm, cached in groups for p in sorted(rec["roles"])]

    rows, scanned = [], []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_detect, llm, prompt, rec, p, ch, version,
                               valid_ids[ch]): (rec, p, ch)
                   for rec, p, ch, prompt, llm in tasks}
        for fut in as_completed(futures):
            rec, p, ch = futures[fut]
            try:
                rows.extend(fut.result())
            except Exception as e:  # noqa: BLE001 — one failed scan drops one denominator cell, logged
                print(f"  DETECT FAIL {rec['game_id'][:8]} {p} {ch}: {e}", flush=True)
                continue
            scanned.append({"game_id": rec["game_id"], "player": p, "channel": ch,
                            "prompt_version": version})

    if cache_names:  # best-effort cleanup; the 900s TTL is the backstop
        client_model = create_chat_model(DETECTOR_MODEL, temperature=0.0)
        for name in cache_names:
            try:
                client_model.client.caches.delete(name=name)
            except Exception:  # noqa: BLE001
                pass
    return rows, scanned


def detect_games(games: list[dict], checklist: dict, *, cache: bool = True,
                 thinking: str = "low", workers: int = 8) -> tuple[list[dict], list[dict]]:
    """The standing k=2 detection: det_v1 full-view UNION det_v2 split-view (the measurement config —
    cached, thinking=low, golden-parity verified 2026-07-13; k=2→k=1 is an open cost decision). Returns
    (union rows deduped on (game, player, channel, tell, day), scanned denominator cells)."""
    rows1, scanned1 = _detect_pass(games, checklist, "det_v1", False, cache, thinking, workers)
    rows2, scanned2 = _detect_pass(games, checklist, "det_v2", True, cache, thinking, workers)
    union, seen = [], set()
    for r in rows1 + rows2:
        key = (r["game_id"], r["player"], r["channel"], r["tell_id"], r["day"])
        if key not in seen:
            seen.add(key)
            union.append(r)
    return union, scanned1 + scanned2


def scanned_games_by_tell(checklist: dict, scanned: list[dict]) -> dict[str, int]:
    """How many distinct games each checklist tell was scanned in (both views count once) — the
    probation clock's input: a tell's K-games window counts SCANNED games, because scanning is what
    produces its evidence."""
    games_per_channel: dict[str, set] = defaultdict(set)
    for s in scanned:
        games_per_channel[s["channel"]].add(s["game_id"])
    return {t["tell_id"]: len(games_per_channel[ch])
            for ch, tells in checklist.items() for t in tells}
