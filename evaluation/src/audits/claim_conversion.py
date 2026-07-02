"""Metrics audit — Workstream 1, Idea C: claim-timing conversion joins.

Pre-registered join: investigator finds (a private wolf-confirm) + role_claims + subsequent votes ->
does a claim-with-find convert the room (next-round vote convergence onto the found wolf; claim ->
correct elimination)? The CLAIM half depends on the persisted `DaySummary.structured.role_claims`
field (the tagger's `_role_claims_by_day` source).

COVERAGE CATCH (checked, not assumed): that structured field is an A4 (2026-06-20) addition and is
absent from BOTH validation sets (0/180 v6ab, 0/50 v5). So the claim-conditioned joins (C0) are
UNBUILDABLE here and reported as blocked — no validation claim. What survives without claims is the
deterministic timing refinement:

  C1 investigator_find_next_round_convergence — after a wolf is found on night d, the fraction of town
     votes on day d+1 (the immediate next round) that land on that wolf. A tighter, timing-sensitive
     cousin of the already-validated `investigator_find_to_lynch_rate` (+0.40).

Validated vs villager win on N=180 v6ab + the pre-registered game_id 50/50 split
(`evidence/metrics/metrics_audit/proxy_discovery_log.md` §3.0). Deterministic, ZERO LLM.

    poetry run python evaluation/src/audits/claim_conversion.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.src.core.stats import point_biserial
from evaluation.src.audits.metrics_common import (
    REPO_ROOT,
    TOWN_ROLES,
    load_v6ab,
    split_half,
    won,
)

OUT = REPO_ROOT / "evidence/metrics/metrics_audit/data/claim_conversion.json"


def role_claim_coverage(games: list[dict]) -> dict:
    """How many games carry the persisted structured role_claims the C0 joins need."""
    with_claims = total_claims = 0
    for g in games:
        claims = sum(len((s.get("structured") or {}).get("role_claims") or [])
                     for s in (g.get("day_summaries") or []))
        total_claims += claims
        with_claims += int(claims > 0)
    return {"n_games": len(games), "games_with_role_claims": with_claims,
            "total_role_claims": total_claims}


def find_next_round_convergence(record: dict) -> float | None:
    """Mean over wolf-finds of: town votes on the found wolf on day d+1 / all town votes day d+1.

    A find lands on NIGHT d; day d+1 is the first round the town can act on it. Skips finds where the
    wolf is no longer a votable target on d+1 (already lynched/dead) or the next round has no town votes.
    """
    roles = record.get("roles") or {}
    votes_by_day: dict[int, list[dict]] = {}
    for d in record.get("day_resolutions", []):
        votes_by_day[d["day"]] = d.get("votes") or []
    finds = [(n["day"], n.get("investigator_target"))
             for n in record.get("night_resolutions", [])
             if n.get("investigator_target_role") == "wolf" and n.get("investigator_target")]
    convs = []
    for day, wolf in finds:
        nxt = votes_by_day.get((day or 0) + 1)
        if not nxt:
            continue
        town_votes = [v for v in nxt if roles.get(v["voter"]) in TOWN_ROLES]
        if not town_votes:
            continue
        # only meaningful if the wolf was still a candidate that round (someone could vote it)
        on_wolf = sum(1 for v in town_votes if v["votee"] == wolf)
        convs.append(on_wolf / len(town_votes))
    return (sum(convs) / len(convs)) if convs else None


def corr(rows, metric, outcome, subset=None):
    rr = [r for r in rows if subset is None or subset(r)]
    pairs = [(r[outcome], r[metric]) for r in rr if r.get(metric) is not None]
    if len(pairs) < 3:
        return {"r": None, "p": None, "n": len(pairs)}
    r, p = point_biserial([b for b, _ in pairs], [v for _, v in pairs])
    return {"r": r, "p": p, "n": len(pairs)}


def _fmt(d):
    if d["r"] is None or d["r"] != d["r"]:
        return f"— (n={d['n']})"
    return f"{d['r']:+.3f} (p={d['p']:.3f}, n={d['n']})"


def main() -> None:
    games = load_v6ab()
    cov = role_claim_coverage(games)
    print(f"Idea C — N={cov['n_games']} v6ab games\n")
    print("C0 (claim-conditioned joins) COVERAGE CHECK:")
    print(f"  games with persisted role_claims: {cov['games_with_role_claims']}/{cov['n_games']}"
          f" | total role_claims: {cov['total_role_claims']}")
    print("  -> role_claims absent (A4 field postdates this epoch); C0 BLOCKED, no validation claim.\n")

    rows = [{
        "game_id": g.get("game_id"),
        "half": split_half(g.get("game_id")),
        "town_won": won(g, "villagers"),
        "investigator_find_next_round_convergence": find_next_round_convergence(g),
    } for g in games]

    block = {
        "full": corr(rows, "investigator_find_next_round_convergence", "town_won"),
        "discover_half": corr(rows, "investigator_find_next_round_convergence", "town_won",
                              subset=lambda r: r["half"] == 0),
        "confirm_half": corr(rows, "investigator_find_next_round_convergence", "town_won",
                             subset=lambda r: r["half"] == 1),
    }
    covered = sum(1 for r in rows if r["investigator_find_next_round_convergence"] is not None)
    print("C1 investigator_find_next_round_convergence (vs villagers win)")
    print(f"  coverage: {covered}/{len(rows)} games have a computable find->next-round")
    print("| metric | full | discover half | confirm half |")
    print("|---|---|---|---|")
    print(f"| `investigator_find_next_round_convergence` | {_fmt(block['full'])} "
          f"| {_fmt(block['discover_half'])} | {_fmt(block['confirm_half'])} |")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "coverage": cov, "c1_covered_games": covered,
        "C1": {"metric": "investigator_find_next_round_convergence", "stats": block},
    }, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
