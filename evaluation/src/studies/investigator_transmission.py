"""Investigator-transmission metric — does the confirmed-wolf read reach the village?

Diagnoses the bottleneck flagged in the v6 A/B reads: the investigator gets the single most
valuable fact in the game (a confirmed wolf) and the town loses anyway because the read never
enters the public channel. This measures, per game, whether a wolf-read was *transmitted* — and
lets a flat town-memory result be read as either "no effect" or "bottleneck-capped".

Per game (from the batch JSONL record — no Langfuse, no eval_cases needed):
  has_wolf_read  : investigator obtained >=1 result with role_revealed == "wolf"
  claimed        : investigator publicly ASSERTED that wolf (names it AND a claim term —
                   wolf/confirmed/investigated/scanned) in a non-passed day message, day >= learn
  vague_mention  : named the wolf but with NO claim term (the "keep an eye on player_6" failure mode)
  voted          : investigator voted for that wolf, day >= learn
  transmitted    : claimed OR voted  (the confirmed read actually entered the public arena —
                   a bare name-drop does NOT count; that was the first-cut bug this metric fixes)
  removed        : that wolf was lynched (voted_player) on day >= learn  (the read propagated + acted on)

CAUTION on interpretation (see the A/B-design note): `transmitted` is POST-TREATMENT — investigator
memory could itself change it. So the headline stays the unconditional ITT win-rate; the
transmitted/win cross-tab below is DESCRIPTIVE (collider risk), and the per-arm transmission RATE is
the mediator to check first (does memory move transmission at all?).

Usage:
  poetry run python -m evaluation.src.studies.investigator_transmission batch_results/v6ab_*.jsonl
"""

from __future__ import annotations

import glob
import sys
from pathlib import Path

from evaluation.src.data.sources.batch_records import read_records_file


def _mention_forms(player_id: str) -> list[str]:
    """The ways a model refers to a player in prose: 'player_4', 'player 4', 'player4'."""
    n = player_id.split("_")[-1]
    return [player_id.lower(), f"player {n}", f"player{n}"]


# INVESTIGATION-specific terms (deliberately NOT generic "wolf" — that fires on speculation like
# "player_6 might be a wolf"). A message that names the wolf AND asserts an investigation result is a
# real transmission of the confirmed read; a name without one is a vague mention. NOTE: this is a
# rough heuristic — it UNDER-counts assertions phrased without these words ("player_6 is definitely a
# wolf, trust me"), just as generic "wolf" OVER-counts. The two bracket the truth; a clean measure
# needs an LLM judge over the investigator's post-read messages (run that post-batch). `removed` (the
# wolf actually lynched after the read) is the one unambiguous, judge-free signal.
_CLAIM_TERMS = ("investigat", "confirmed", "scan", "checked", "my result", "my read", "i learned")


def analyze_game(rec: dict) -> dict:
    roles = rec.get("roles") or {}
    investigator = next((p for p, ro in roles.items() if ro == "investigator"), None)
    wolf_reads = [
        (r["day"], r["player_investigated"])
        for r in (rec.get("investigator_results") or [])
        if r.get("role_revealed") == "wolf"
    ]
    out = {
        "has_wolf_read": bool(wolf_reads),
        "claimed": False,
        "vague_mention": False,
        "voted": False,
        "removed": False,
        "transmitted": False,
        "town_win": rec.get("winner") == "villagers",
    }
    if not wolf_reads or investigator is None:
        return out

    day_channel = rec.get("day_channel") or []
    resolutions = rec.get("day_resolutions") or []
    for learn_day, wolf in wolf_reads:
        forms = _mention_forms(wolf)
        for m in day_channel:
            if m.get("player") != investigator or m.get("passed") or (m.get("day") or 0) < learn_day:
                continue
            msg = (m.get("message") or "").lower()
            if any(f in msg for f in forms):
                if any(t in msg for t in _CLAIM_TERMS):
                    out["claimed"] = True
                else:
                    out["vague_mention"] = True
        for d in resolutions:
            if (d.get("day") or 0) < learn_day:
                continue
            for v in d.get("votes") or []:
                if v.get("voter") == investigator and v.get("votee") == wolf:
                    out["voted"] = True
            if d.get("voted_player") == wolf:
                out["removed"] = True
    # Strict: transmission = the investigator ASSERTED the confirmed read. Voting for the wolf is
    # tracked separately (weaker — a public vote signals suspicion but doesn't convey "I confirmed it").
    out["transmitted"] = out["claimed"]
    return out


def _rate(num: int, den: int) -> str:
    return f"{num}/{den} ({100*num/den:.0f}%)" if den else f"{num}/0 (—)"


def analyze_arm(path: Path) -> dict:
    games = [analyze_game(rec) for rec in read_records_file(path, require_success=False)]
    wr = [g for g in games if g["has_wolf_read"]]
    trans = [g for g in wr if g["transmitted"]]
    return {
        "arm": path.stem,
        "n": len(games),
        "town_win_rate": (sum(g["town_win"] for g in games), len(games)),
        "wolf_read": (len(wr), len(games)),
        "transmitted": (len(trans), len(wr)),
        "voted": (sum(g["voted"] for g in wr), len(wr)),
        "vague_only": (sum(g["vague_mention"] and not g["claimed"] for g in wr), len(wr)),
        "removed": (sum(g["removed"] for g in wr), len(wr)),
        # DESCRIPTIVE cross-tab (collider-risk; not the causal estimate):
        "win_if_transmitted": (sum(g["town_win"] for g in trans), len(trans)),
        "win_if_not_transmitted": (
            sum(g["town_win"] for g in wr if not g["transmitted"]),
            len([g for g in wr if not g["transmitted"]]),
        ),
    }


def main(argv: list[str]) -> int:
    patterns = argv or ["batch_results/v6ab_*.jsonl"]
    paths = sorted({Path(p) for pat in patterns for p in glob.glob(pat)})
    if not paths:
        print("no matching batch JSONL files", file=sys.stderr)
        return 1
    print("transmit = investigator ASSERTED the confirmed read (strict); voted/vague/removed are separate signals")
    print(f"{'arm':24} {'n':>3} {'town_win':>10} {'wolf_read':>10} {'transmit|wr':>12} {'voted|wr':>10} {'vague|wr':>10} {'removed|wr':>11}")
    for path in paths:
        a = analyze_arm(path)
        print(
            f"{a['arm']:24} {a['n']:>3} {_rate(*a['town_win_rate']):>10} "
            f"{_rate(*a['wolf_read']):>10} {_rate(*a['transmitted']):>12} "
            f"{_rate(*a['voted']):>10} {_rate(*a['vague_only']):>10} {_rate(*a['removed']):>11}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
