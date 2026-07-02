"""Metrics audit — Workstream 1, Idea B: accusation-graph proxies.

Parses the discussion layer (`day_channel` -> `addressed_targets` with stance=='accusation', ordered
by `seq`) into a per-player accusation graph, then computes deterministic, no-LLM candidates that
target the known town-discussion hole and the investigator/vigilante post-find discussion gaps:

  B1 town_accusation_precision      — fraction of town accusations aimed at true threats
  B2 town_first_accuser_credit_rate — town accusations that are on a threat AND early (accuser is one of
                                      the first two distinct accusers of that target)
  B3 town_accusation_to_vote_conversion — town accusations the accuser later backs with a vote
  B4 investigator_postfind_accusation_precision  (exploratory, coverage-limited)
  B5 vigilante_postfind_accusation_precision     (exploratory, coverage-limited)
  B6 wolf_accusation_on_town_rate   (vs wolf win; framing offense, low prior)

Validated by point-biserial vs own-faction win on the N=180 v6ab set + the pre-registered game_id
50/50 split (`evidence/metrics/metrics_audit/proxy_discovery_log.md` §3.0). LABEL-NOISE guard: a
20-row random sample of (message, parsed-accusation) pairs is dumped for human spot-check, because
`addressed_targets` are self-labeled speech acts tuned for scheduling, not measurement.

    poetry run python evaluation/src/audits/accusation_metrics.py
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.src.core.stats import point_biserial
from evaluation.src.audits.metrics_common import (
    REPO_ROOT,
    THREAT_ROLES,
    TOWN_ROLES,
    load_v6ab,
    split_half,
    won,
)

OUT = REPO_ROOT / "evidence/metrics/metrics_audit/data/accusation_metrics.json"
SAMPLE_OUT = REPO_ROOT / "evidence/metrics/metrics_audit/data/accusation_label_sample.json"


def accusations(record: dict) -> list[dict]:
    """Ordered accusation events: (day, seq, accuser, target, message). Skips passed messages and
    self-accusations. Order is (day, seq) — the in-game speaking order."""
    events = []
    for m in record.get("day_channel") or []:
        if m.get("passed"):
            continue
        accuser = m.get("player")
        day = m.get("day")
        seq = m.get("seq")
        for a in m.get("addressed_targets") or []:
            if a.get("stance") != "accusation":
                continue
            target = a.get("target")
            if not target or target == accuser:
                continue
            events.append({"day": day, "seq": seq, "accuser": accuser, "target": target,
                           "message": m.get("message", "")})
    events.sort(key=lambda e: (e["day"] if e["day"] is not None else 0,
                               e["seq"] if e["seq"] is not None else 0))
    return events


def _later_votes(record: dict) -> dict[str, list[tuple[int, str]]]:
    """voter -> [(day, votee)] across all day resolutions (for accusation->vote conversion)."""
    out: dict[str, list[tuple[int, str]]] = {}
    for d in record.get("day_resolutions", []):
        for v in d.get("votes") or []:
            out.setdefault(v["voter"], []).append((d["day"], v["votee"]))
    return out


def game_metrics(record: dict) -> dict:
    roles = record.get("roles") or {}
    evs = accusations(record)
    votes = _later_votes(record)

    # distinct-accuser rank per target (for first-accuser credit): the k-th DISTINCT accuser of a
    # target is "early" if k <= 2 (target had <2 prior distinct accusers when they spoke).
    seen_accusers: dict[str, list[str]] = {}
    town_total = town_on_threat = town_early_credit = town_converted = 0
    wolf_total = wolf_on_town = 0
    inv_after = inv_after_threat = 0
    vig_after = vig_after_threat = 0

    # find-day gates for post-find precision
    inv_find_day = next((n["day"] for n in record.get("night_resolutions", [])
                         if n.get("investigator_target_role") == "wolf"), None)
    vig_shot_day = next((n["day"] for n in record.get("night_resolutions", [])
                         if n.get("vigilante_kill_landed")), None)

    for e in evs:
        accuser, target, day = e["accuser"], e["target"], e["day"]
        arole = roles.get(accuser)
        trole = roles.get(target)
        is_threat = trole in THREAT_ROLES
        prior = seen_accusers.setdefault(target, [])
        is_new_distinct = accuser not in prior
        rank = len(prior) + 1 if is_new_distinct else prior.index(accuser) + 1
        if is_new_distinct:
            prior.append(accuser)

        if arole in TOWN_ROLES:
            town_total += 1
            if is_threat:
                town_on_threat += 1
                if rank <= 2:
                    town_early_credit += 1
            if any(vd >= (day or 0) and vv == target for vd, vv in votes.get(accuser, [])):
                town_converted += 1
            if arole == "investigator" and inv_find_day is not None and (day or 0) > inv_find_day:
                inv_after += 1
                inv_after_threat += int(is_threat)
            if arole == "vigilante" and vig_shot_day is not None and (day or 0) > vig_shot_day:
                vig_after += 1
                vig_after_threat += int(is_threat)
        elif arole == "wolf":
            wolf_total += 1
            if trole in TOWN_ROLES:
                wolf_on_town += 1

    def rate(num, den):
        return (num / den) if den else None

    return {
        "game_id": record.get("game_id"),
        "half": split_half(record.get("game_id")),
        "town_won": won(record, "villagers"),
        "wolf_won": won(record, "wolves"),
        "town_accusation_precision": rate(town_on_threat, town_total),
        "town_first_accuser_credit_rate": rate(town_early_credit, town_total),
        "town_accusation_to_vote_conversion": rate(town_converted, town_total),
        "investigator_postfind_accusation_precision": rate(inv_after_threat, inv_after),
        "vigilante_postfind_accusation_precision": rate(vig_after_threat, vig_after),
        "wolf_accusation_on_town_rate": rate(wolf_on_town, wolf_total),
        "_town_accusations": town_total,
    }


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
    rows = [game_metrics(g) for g in games]

    town_cands = [
        ("B1", "town_accusation_precision", "town_won"),
        ("B2", "town_first_accuser_credit_rate", "town_won"),
        ("B3", "town_accusation_to_vote_conversion", "town_won"),
    ]
    expl_cands = [
        ("B4", "investigator_postfind_accusation_precision", "town_won"),
        ("B5", "vigilante_postfind_accusation_precision", "town_won"),
        ("B6", "wolf_accusation_on_town_rate", "wolf_won"),
    ]

    result: dict = {"n_games": len(rows), "candidates": {}}
    print(f"Idea B accusation-graph — N={len(rows)} v6ab games\n")
    print("PRIMARY town family (vs villagers win)")
    print("| id | metric | full N=180 | discover half | confirm half |")
    print("|---|---|---|---|---|")
    for cid, m, out in town_cands + expl_cands:
        block = {
            "full": corr(rows, m, out),
            "discover_half": corr(rows, m, out, subset=lambda r: r["half"] == 0),
            "confirm_half": corr(rows, m, out, subset=lambda r: r["half"] == 1),
        }
        result["candidates"][cid] = {"metric": m, "outcome": out, "stats": block}
        if cid == "B4":
            print("\nEXPLORATORY (coverage-limited; direction only)")
            print("| id | metric | full | discover half | confirm half |")
            print("|---|---|---|---|---|")
        print(f"| {cid} | `{m}` | {_fmt(block['full'])} | {_fmt(block['discover_half'])} "
              f"| {_fmt(block['confirm_half'])} |")

    # label-noise spot-check sample: 20 random (message, parsed accusation) pairs
    all_evs = []
    for g in games:
        roles = g.get("roles") or {}
        for e in accusations(g):
            all_evs.append({
                "game_id": g.get("game_id"),
                "day": e["day"], "accuser": e["accuser"], "accuser_role": roles.get(e["accuser"]),
                "target": e["target"], "target_role": roles.get(e["target"]),
                "message": e["message"],
            })
    rng = random.Random(20260702)
    sample = rng.sample(all_evs, min(20, len(all_evs)))
    SAMPLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    SAMPLE_OUT.write_text(json.dumps(
        {"note": "human spot-check: is each message actually an accusation of `target`?",
         "total_accusations_parsed": len(all_evs), "sample": sample}, indent=2))

    OUT.write_text(json.dumps(result, indent=2))
    print(f"\ntotal accusations parsed: {len(all_evs)}")
    print(f"wrote {OUT.relative_to(REPO_ROOT)} + {SAMPLE_OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
