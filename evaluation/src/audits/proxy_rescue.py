"""Metrics audit — Workstream 1, Idea A: rescue pass on muted proxies.

Re-tests the rejected/null WOLF-night proxies and the wrong-sign INVESTIGATOR find-rate cluster
against faction win, under two conditionings the flat point-biserial never applied:
  (i)  stratify / partial on `sk_lynched` — the +0.455 environmental dominator that swamps wolf-skill
       variance (a wolf barely influences whether the town removes the SK for it);
  (ii) game-length normalization — the confound that made `investigator_found_wolf_day` wrong-sign
       (villager wins take longer -> later finds AND more wins).
Per-stratum r + N are reported so a muted-but-real signal is separated from a still-null one.

Pre-registration: `evidence/metrics/metrics_audit/proxy_discovery_log.md` §3.0. Deterministic, ZERO
LLM, recompute-only over the N=180 v6ab set. Split-half confirmation on `game_id` parity.

    poetry run python evaluation/src/audits/proxy_rescue.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.src.core.stats import partial_correlation, point_biserial
from evaluation.src.audits.metrics_common import (
    REPO_ROOT,
    load_v6ab,
    split_half,
    won,
)

POWER_ROLES = {"healer", "investigator", "vigilante"}
OUT = REPO_ROOT / "evidence/metrics/metrics_audit/data/proxy_rescue.json"


def _power_role_alive_nights(record: dict) -> int:
    """Nights entered with >=1 town power role (healer/investigator/vigilante) still alive.

    Mirrors compute_metrics._dead_before_each_night: within a day the lynch happens before the
    night's kills, so entering night d = lynches(1..d) + night kills(1..d-1).
    """
    roles = record.get("roles") or {}
    power_ids = {p for p, r in roles.items() if r in POWER_ROLES}
    day_res = {d["day"]: d for d in record.get("day_resolutions", [])}
    night_res = {n["day"]: n for n in record.get("night_resolutions", [])}
    days = sorted(set(day_res) | set(night_res))
    dead: set[str] = set()
    alive_nights = 0
    for day in days:
        dr = day_res.get(day)
        if dr and dr.get("voted_player"):
            dead.add(dr["voted_player"])
        if day in night_res:
            if any(pid not in dead for pid in power_ids):
                alive_nights += 1
            dead |= set(night_res[day].get("deaths") or [])
    return alive_nights


def candidate_rows(games: list[dict]) -> list[dict]:
    """Per-game values for every Idea-A candidate + the two conditioning variables."""
    rows = []
    for g in games:
        cm = g.get("computed_metrics") or {}
        pran = _power_role_alive_nights(g)
        prk = cm.get("power_roles_killed_by_wolves")
        found_day = cm.get("investigator_found_wolf_day")
        length = cm.get("game_length") or g.get("current_day")
        rows.append({
            "game_id": g.get("game_id"),
            "half": split_half(g.get("game_id")),
            "wolf_won": won(g, "wolves"),
            "town_won": won(g, "villagers"),
            "sk_lynched": int(cm.get("serial_killer_lynched") or 0),
            "game_length": length,
            # A1-A3 (wolf night offense / targeting)
            "power_roles_killed_by_wolves": prk,
            "wolf_power_kill_rate": (prk / pran) if (prk is not None and pran) else None,
            "wolf_power_role_targeting_rate": cm.get("wolf_power_role_targeting_rate"),
            # A4-A6 (investigator find-rate cluster)
            "investigator_found_wolf_day": found_day,
            "investigator_found_wolf_day_frac": (found_day / length) if (found_day and length) else None,
            "investigator_threat_find_rate": cm.get("investigator_threat_find_rate"),
            "investigator_wolf_find_rate": cm.get("investigator_wolf_find_rate"),
        })
    return rows


def _pairs(rows, metric, outcome, extra_control=None):
    """Aligned (value, outcome, [controls]) dropping rows where any is missing."""
    out = []
    for r in rows:
        v = r.get(metric)
        y = r.get(outcome)
        if v is None or y is None:
            continue
        ctrls = []
        ok = True
        for c in (extra_control or []):
            cv = r.get(c)
            if cv is None:
                ok = False
                break
            ctrls.append(cv)
        if ok:
            out.append((float(v), int(y), ctrls))
    return out


def raw_r(rows, metric, outcome, subset=None):
    rr = [r for r in rows if subset is None or subset(r)]
    pairs = _pairs(rr, metric, outcome)
    if len(pairs) < 3:
        return {"r": None, "p": None, "n": len(pairs)}
    r, p = point_biserial([o for _, o, _ in pairs], [v for v, _, _ in pairs])
    return {"r": r, "p": p, "n": len(pairs)}


def partial_r(rows, metric, outcome, controls):
    pairs = _pairs(rows, metric, outcome, controls)
    if len(pairs) < len(controls) + 3:
        return {"r": None, "p": None, "n": len(pairs)}
    x = [v for v, _, _ in pairs]
    y = [o for _, o, _ in pairs]
    ctrl_cols = [[c[i] for _, _, c in pairs] for i in range(len(controls))]
    r, p, n = partial_correlation(x, y, ctrl_cols)
    return {"r": r, "p": p, "n": n}


def _fmt(d):
    if d["r"] is None or d["r"] != d["r"]:
        return f"— (n={d['n']})"
    p = d["p"]
    ps = "nan" if (p is None or p != p) else f"{p:.3f}"
    return f"{d['r']:+.3f} (p={ps}, n={d['n']})"


def main() -> None:
    games = load_v6ab()
    rows = candidate_rows(games)
    result: dict = {"n_games": len(rows), "candidates": {}}

    wolf_cands = [
        ("A1", "power_roles_killed_by_wolves", "wolf_won"),
        ("A2", "wolf_power_kill_rate", "wolf_won"),
        ("A3", "wolf_power_role_targeting_rate", "wolf_won"),
    ]
    inv_cands = [
        ("A4", "investigator_found_wolf_day", "town_won"),
        ("A4n", "investigator_found_wolf_day_frac", "town_won"),
        ("A5", "investigator_threat_find_rate", "town_won"),
        ("A6", "investigator_wolf_find_rate", "town_won"),
    ]

    print(f"Idea A rescue — N={len(rows)} v6ab games\n")
    print("WOLF candidates (vs wolves win); conditioning on sk_lynched (+0.455 dominator) & game_length")
    print("| id | metric | raw | sk_lynched=0 | sk_lynched=1 | partial\\|sk | partial\\|len | partial\\|both | disc-half | conf-half |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for cid, m, out in wolf_cands:
        stats_block = {
            "raw": raw_r(rows, m, out),
            "sk_lynched=0": raw_r(rows, m, out, subset=lambda r: r["sk_lynched"] == 0),
            "sk_lynched=1": raw_r(rows, m, out, subset=lambda r: r["sk_lynched"] == 1),
            "partial|sk_lynched": partial_r(rows, m, out, ["sk_lynched"]),
            "partial|game_length": partial_r(rows, m, out, ["game_length"]),
            "partial|both": partial_r(rows, m, out, ["sk_lynched", "game_length"]),
            "discover_half": raw_r(rows, m, out, subset=lambda r: r["half"] == 0),
            "confirm_half": raw_r(rows, m, out, subset=lambda r: r["half"] == 1),
            # split-half of the CONDITIONED signal (within sk_lynched=1, the only stratum with wolf wins)
            "sk1_discover": raw_r(rows, m, out, subset=lambda r: r["sk_lynched"] == 1 and r["half"] == 0),
            "sk1_confirm": raw_r(rows, m, out, subset=lambda r: r["sk_lynched"] == 1 and r["half"] == 1),
        }
        result["candidates"][cid] = {"metric": m, "outcome": out, "stats": stats_block}
        print(f"| {cid} | `{m}` | {_fmt(stats_block['raw'])} | {_fmt(stats_block['sk_lynched=0'])} "
              f"| {_fmt(stats_block['sk_lynched=1'])} | {_fmt(stats_block['partial|sk_lynched'])} "
              f"| {_fmt(stats_block['partial|game_length'])} | {_fmt(stats_block['partial|both'])} "
              f"| sk1: {_fmt(stats_block['sk1_discover'])} / {_fmt(stats_block['sk1_confirm'])} |")

    print("\nINVESTIGATOR find-rate cluster (vs villagers win); length-normalization diagnosis")
    print("| id | metric | raw | partial\\|game_length | disc-half | conf-half |")
    print("|---|---|---|---|---|---|")
    for cid, m, out in inv_cands:
        stats_block = {
            "raw": raw_r(rows, m, out),
            "partial|game_length": partial_r(rows, m, out, ["game_length"]),
            "discover_half": raw_r(rows, m, out, subset=lambda r: r["half"] == 0),
            "confirm_half": raw_r(rows, m, out, subset=lambda r: r["half"] == 1),
        }
        result["candidates"][cid] = {"metric": m, "outcome": out, "stats": stats_block}
        print(f"| {cid} | `{m}` | {_fmt(stats_block['raw'])} | {_fmt(stats_block['partial|game_length'])} "
              f"| {_fmt(stats_block['discover_half'])} | {_fmt(stats_block['confirm_half'])} |")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO_ROOT)}")


if __name__ == "__main__":
    main()
