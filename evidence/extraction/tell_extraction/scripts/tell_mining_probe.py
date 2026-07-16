"""Tell-mining offline probe — PROBE SCAFFOLDING, not pipeline code (graduates JIT if the
read/tactic v1 adopts it; see evidence/extraction/tell_extraction/experiment_log.md).

Mines candidate TELLS (recurring, publicly-observable behavior patterns that might correlate
with hidden role) from finished v6ab games, one omniscient LLM call per game-day. Design
constraints from evidence/credit/read_tactic_credit_redesign.md §3:

- The miner sees the PUBLIC record only (day transcripts, votes, GM announcements) plus the
  true-roles header. Detectability-by-construction: behaviors invisible at the table (night
  actions, private reasoning) cannot be mined because the miner never sees them.
- The model emits exhibitor player_id, never a role — the behavior→role join is a
  deterministic lookup on the game record afterward.
- The model assigns NO valence/direction ("suggests wolf" is banned); lift arithmetic decides
  what a behavior indicates, later, out-of-sample.

Deterministic post-screens (structural only, per the semantic-eval≠string-parse rule): role
words in a behavior description, player IDs in a description, evidence quote not found in the
day's record. Semantic quality is judged by reading the samples, never by these screens.

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/tell_mining_probe.py \
      --games 5 --version v1
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from pydantic import BaseModel, Field

from Agents.llm_factory import get_llm_pro
from Agents.prompts.common import GAME_RULES

PROBE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DUMPS = "batch_results/v6ab_*.jsonl"

ROLE_WORDS = re.compile(
    r"\b(wolf|wolves|werewolf|villager|healer|investigator|vigilante|serial[ _-]?killer|town|evil)\b",
    re.IGNORECASE,
)
# v3 epistemic rule: a role word is legitimate when the sentence marks public certainty
# (a death reveal or a claim). Structural triage only — the read is the real judge.
CERTAINTY_MARKERS = re.compile(r"\b(reveal|revealed|claiming|claimed|claims|claim)\b", re.IGNORECASE)
HIDDEN_RELATION = re.compile(
    r"\b(ally|allies|packmate|pack mate|teammate|team mate|their partner|fellow threat|valuable player)\b",
    re.IGNORECASE,
)
PLAYER_IDS = re.compile(r"\bplayer[_ ]?\d+\b", re.IGNORECASE)


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


# ── game record → public text ─────────────────────────────────────────────────────────────────

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
    return sorted({m["day"] for m in rec["day_channel"] if not m.get("passed") and m["player"] != "game_master"})


def load_games(dumps_glob: str, n: int, skip: int = 0) -> list[dict]:
    games: list[dict] = []
    for path in sorted(glob.glob(dumps_glob)):
        with open(path) as f:
            for line in f:
                rec = json.loads(line)
                if rec.get("status") == "success":
                    rec["_source"] = Path(path).name
                    games.append(rec)
    return games[skip:skip + n]


# ── deterministic post-screens (structural only) ──────────────────────────────────────────────

def _norm(s: str) -> str:
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("—", "-").replace("–", "-").replace("…", "...")
    return re.sub(r"\s+", " ", s).strip().lower()


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


# ── the probe ─────────────────────────────────────────────────────────────────────────────────

def _mine_day(llm, prompt_template: str, rec: dict, day: int, days: list[int], version: str,
              channel: str | None = None) -> list[dict]:
    roles_line = ", ".join(f"{p} = {r}" for p, r in sorted(rec["roles"].items()))
    prior = "\n\n".join(_render_day(rec, d) for d in days if d < day) or "(game start)"
    # The discussion-layer call excludes the focus day's vote block: temporally, the vote has
    # not happened yet — and it removes the compact structured block cheap models anchor on.
    day_text = _render_day(rec, day, include_votes=(channel != "discussion"))
    prompt = prompt_template.format(
        game_rules=GAME_RULES, roles_line=roles_line,
        prior_days=prior, focus_day=day, day_record=day_text,
    )
    result = llm.invoke(prompt)
    rows = []
    for t in result.tells:
        row = {
            "game_id": rec["game_id"], "source": rec["_source"], "day": day,
            "exhibitor": t.exhibitor, "behavior": t.behavior,
            "evidence_quote": t.evidence_quote,
            "exhibitor_role": rec["roles"].get(t.exhibitor),  # deterministic join
            "winner": rec["winner"], "prompt_version": version,
            "channel": channel or "combined",
        }
        # Vote-channel quotes may cite the vote block, which the discussion render lacks.
        row["screen_flags"] = screen_tell(row, _render_day(rec, day))
        rows.append(row)
    return rows


def run(dumps_glob: str, n_games: int, version: str, out_path: Path, workers: int = 8,
        split: bool = False, skip: int = 0) -> None:
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if split:
        templates = {ch: (PROBE_DIR / "prompt_versions" / f"{version}_{ch}.txt").read_text()
                     for ch in ("discussion", "vote")}
    else:
        templates = {None: (PROBE_DIR / "prompt_versions" / f"{version}.txt").read_text()}
    llm = get_llm_pro().with_structured_output(DayTells)
    games = load_games(dumps_glob, n_games, skip=skip)
    tasks = [(rec, day, _game_days(rec), ch)
             for rec in games for day in _game_days(rec) for ch in templates]
    print(f"mining {len(games)} games / {len(tasks)} calls with prompt {version}"
          f"{' (split)' if split else ''} -> {out_path}", flush=True)

    n_done = n_tells = 0
    flag_counts: dict[str, int] = {}
    with open(out_path, "w") as out, ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_mine_day, llm, templates[ch], rec, day, days, version, ch): (rec, day)
                   for rec, day, days, ch in tasks}
        for fut in as_completed(futures):
            rec, day = futures[fut]
            try:
                rows = fut.result()
            except Exception as e:  # noqa: BLE001 — a probe: log and continue, never crash the sweep
                print(f"  FAIL {rec['game_id'][:8]} day {day}: {e}", flush=True)
                continue
            for row in rows:
                for fl in row["screen_flags"]:
                    flag_counts[fl] = flag_counts.get(fl, 0) + 1
                out.write(json.dumps(row) + "\n")
                n_tells += 1
            out.flush()
            n_done += 1
            if n_done % 10 == 0:
                print(f"  {n_done}/{len(tasks)} day-calls done, {n_tells} tells", flush=True)

    print(f"\n{n_done}/{len(tasks)} calls ok, {n_tells} tells ({n_tells / max(n_done, 1):.1f}/day-call)", flush=True)
    print(f"screen flags: {flag_counts or 'none'}", flush=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dumps", default=DEFAULT_DUMPS)
    ap.add_argument("--games", type=int, default=5)
    ap.add_argument("--version", default="v1")
    ap.add_argument("--out", default=None)
    ap.add_argument("--split", action="store_true",
                    help="two calls per day (discussion / vote layers) via <version>_<channel>.txt")
    ap.add_argument("--skip", type=int, default=0, help="skip the first N loaded games")
    args = ap.parse_args()
    out = Path(args.out) if args.out else PROBE_DIR / "outputs" / f"mining_{args.version}.jsonl"
    run(args.dumps, args.games, args.version, out, split=args.split, skip=args.skip)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
