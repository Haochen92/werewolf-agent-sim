"""Tell-detector offline probe — PROBE SCAFFOLDING (see experiment_log.md §5).

The other half of the two-count design (design record §3): the miner is omniscient and
salience-biased (discovery only); the DETECTOR is role-blind and exhaustive, and its counts
are the ONLY lift source. One flash-lite call per (game, player, channel): the model sees the
full PUBLIC record (no true-roles header — role-blind by construction) plus the frozen
checklist for that channel, and reports every (tell, day) instance the focus player exhibited.
Non-detections need no rows: every scanned cell is a denominator entry by construction.

Checklist v0 is seeded from the §3.9 consolidated canon (top-K per channel by mined support —
a stand-in ordering until detected counts exist; dumped to outputs/checklist_v0.json for
provenance). Prompt layout is prefix-cache-friendly: rules + transcript + checklist first,
the per-player focus block last.

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/detector_probe.py \
      --games 5 --version det_v1
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from pydantic import BaseModel, Field

from Agents.llm_factory.backends import _use_vertex, create_chat_model
from Agents.prompts.common import GAME_RULES
from tell_mining_probe import DEFAULT_DUMPS, _game_days, _norm, _render_day, load_games

PROBE_DIR = Path(__file__).resolve().parent.parent
CHECKLIST_PER_CHANNEL = 48  # ledger spec cap: 25 incumbent + 15 probation + 8 rotation
DETECTOR_MODEL = "gemini-3.1-flash-lite"
CACHE_MIN_TOKENS = 4096  # Vertex-enforced minimum (evidence/caching probe, verbatim)


def _make_llm(cached_content: str | None = None, thinking: str = "low"):
    """The detector's model policy (temp 0), optionally cache-bound.

    `thinking` defaults to the calibrated "low"; "minimal" is the cost/determinism probe
    (caching log §⑤: reasoning saturates the low budget at 1,051 tok/call)."""
    kwargs = {"cached_content": cached_content} if cached_content else {}
    return create_chat_model(DETECTOR_MODEL, temperature=0.0,
                             thinking_level=thinking, **kwargs).with_structured_output(PlayerDetections)


def _create_prefix_cache(prefix: str) -> str | None:
    """Best-effort Vertex context cache for one (game, channel, view) prefix —
    the extraction-v5 mechanism (Agents/memory/extraction/prefix_cache.py) applied
    to the detector: the 9 per-player calls share a byte-identical
    rules+transcript+checklist prefix; the per-player tail rides on top. Any
    failure returns None and the caller falls back to the full uncached prompt."""
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


def build_checklist() -> dict[str, list[dict]]:
    """Top-K per channel by consolidated mined support (checklist v0; support is a stand-in
    ranking until detected counts exist). Deterministic: support desc, tid asc."""
    cons = json.load(open(PROBE_DIR / "outputs" / "consolidated_store.json"))
    out = {}
    for ch in ("vote", "discussion"):
        pool = sorted((e for e in cons if e["channel"] == ch),
                      key=lambda e: (-e["support"], e["tid"]))
        out[ch] = [{"tell_id": e["tid"], "text": e["canonical"]}
                   for e in pool[:CHECKLIST_PER_CHANNEL]]
    (PROBE_DIR / "outputs" / "checklist_v0.json").write_text(json.dumps(out, indent=1))
    return out


def _render_checklist(items: list[dict]) -> str:
    return "\n".join(f"[{t['tell_id']}] {t['text']}" for t in items)


def _players(rec: dict) -> list[str]:
    return sorted(rec["roles"])  # roster only — roles are NOT shown to the detector


def _strip_vote_blocks(day_text: str) -> str:
    """Discussion-channel view (mirrors mining v4's channel split): drop the per-voter tally
    lines and the "Votes:" summary so the compact structured block can't anchor a cheap
    model's attention. OUTCOMES stay — lynch results/role reveals and GM night announcements
    are public context that discussion tells reference."""
    return "\n".join(
        line for line in day_text.splitlines()
        if not (line.startswith("Votes: ") or "vote result for day" in line
                or (line.startswith("  ") and " voted for " in line))
    )


def _build_prompt_parts(template: str, rec: dict, channel: str, checklist: dict,
                        split_view: bool) -> tuple[str, str]:
    """Split one (game, channel, view) prompt into (shared prefix, per-player tail template).

    The prefix — everything through the checklist — is byte-identical across the 9
    per-player calls (and across prompt versions, whose text differs only in the task
    tail), so it is the explicit-cache unit. The tail template still needs
    {focus_player} formatted in.
    """
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
            "game_id": rec["game_id"], "source": rec["_source"], "channel": channel,
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


def run(dumps_glob: str, n_games: int, version: str, out_path: Path,
        workers: int = 8, skip: int = 0, split_view: bool = False,
        cache: bool = False, thinking: str = "low") -> None:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    template = (PROBE_DIR / "prompt_versions" / f"{version}.txt").read_text()
    checklist = build_checklist()
    valid_ids = {ch: {t["tell_id"] for t in checklist[ch]} for ch in checklist}
    plain_llm = _make_llm(thinking=thinking)
    games = load_games(dumps_glob, n_games, skip=skip)
    print(f"detector {version}: {len(games)} games / {len(games) * 18} calls"
          f"{' (cached prefixes)' if cache else ''} -> {out_path}", flush=True)

    # (game, channel) groups: each shares one byte-identical prefix = one cache unit.
    groups = []
    cache_names: list[str] = []
    n_cached_groups = 0
    for rec in games:
        for ch in ("vote", "discussion"):
            prefix, tail_tpl = _build_prompt_parts(template, rec, ch, checklist, split_view)
            name = _create_prefix_cache(prefix) if cache else None
            if name:
                cache_names.append(name)
                n_cached_groups += 1
            groups.append((rec, ch, prefix, tail_tpl, _make_llm(name, thinking) if name else plain_llm,
                           name is not None))
    if cache:
        print(f"  prefix caches created: {n_cached_groups}/{len(groups)} groups", flush=True)

    tasks = [(rec, p, ch, tail_tpl.format(focus_player=p, channel=ch.upper()) if cached
              else prefix + tail_tpl.format(focus_player=p, channel=ch.upper()), llm)
             for rec, ch, prefix, tail_tpl, llm, cached in groups for p in _players(rec)]

    n_done = n_rows = 0
    flag_counts: dict[str, int] = {}
    scanned = []
    with open(out_path, "w") as out, ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_detect, llm, prompt, rec, p, ch, version,
                               valid_ids[ch]): (rec, p, ch)
                   for rec, p, ch, prompt, llm in tasks}
        for fut in as_completed(futures):
            rec, p, ch = futures[fut]
            try:
                rows = fut.result()
            except Exception as e:  # noqa: BLE001 — a probe: log and continue
                print(f"  FAIL {rec['game_id'][:8]} {p} {ch}: {e}", flush=True)
                continue
            scanned.append({"game_id": rec["game_id"], "player": p, "channel": ch})
            for row in rows:
                for fl in row["screen_flags"]:
                    flag_counts[fl] = flag_counts.get(fl, 0) + 1
                out.write(json.dumps(row) + "\n")
                n_rows += 1
            out.flush()
            n_done += 1
            if n_done % 10 == 0:
                print(f"  {n_done}/{len(tasks)} scans done, {n_rows} detections", flush=True)

    # the denominator record: every completed scan cell (needed for rates; design record §3)
    denom_path = out_path.with_name(out_path.stem + "_scanned.json")
    denom_path.write_text(json.dumps(scanned, indent=1))
    print(f"\n{n_done}/{len(tasks)} scans ok, {n_rows} detections "
          f"({n_rows / max(n_done, 1):.1f}/scan)", flush=True)
    print(f"screen flags: {flag_counts or 'none'}", flush=True)

    # best-effort cache cleanup; the 900s TTL is the backstop
    if cache_names:
        client_model = create_chat_model(DETECTOR_MODEL, temperature=0.0)
        deleted = 0
        for name in cache_names:
            try:
                client_model.client.caches.delete(name=name)
                deleted += 1
            except Exception:  # noqa: BLE001
                pass
        print(f"caches deleted: {deleted}/{len(cache_names)} (rest TTL-expire)", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", default=DEFAULT_DUMPS)
    ap.add_argument("--games", type=int, default=5)
    ap.add_argument("--version", default="det_v1")
    ap.add_argument("--out", default=None)
    ap.add_argument("--skip", type=int, default=0)
    ap.add_argument("--split-view", action="store_true",
                    help="discussion calls read a vote-tally-stripped transcript (mining-v4 analog)")
    ap.add_argument("--no-cache", action="store_true",
                    help="disable the explicit per-(game, channel) prefix cache (the standing "
                         "config since 2026-07-13 is CACHED — golden-parity verified; "
                         "caching log §⑤a)")
    ap.add_argument("--thinking", default="low", choices=["minimal", "low", "medium"],
                    help="detector thinking level (default: the calibrated low)")
    args = ap.parse_args()
    out = Path(args.out) if args.out else PROBE_DIR / "outputs" / f"detector_{args.version}.jsonl"
    run(args.dumps, args.games, args.version, out, skip=args.skip, split_view=args.split_view,
        cache=not args.no_cache, thinking=args.thinking)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
