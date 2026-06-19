"""Criticality screen (Phase B dimension build, step 3) — does conditioning retrieval on the v6
criticality regime move villager day-votes vs ignoring it?

Triage, not a verdict: reads DIRECTION + the criticality SIGNATURE (gain concentrated in the
high-criticality strata, ~null mid-game — the falsification hook) + the causal-flip-rate, NOT
significance. If the lever shows -> roll the full DAG to the rest of the town faction + re-extract
(step 4). If conditioned ~= flat everywhere with a dead/incoherent flip-rate -> criticality is not a
retrieval lever for villagers and the structural asymmetry is the headline.

Self-contained retrieval so the ONLY delta between arms is the conditioning: both arms rank the SAME
v6 candidate pool with the SAME embedding; flat ranks by cosine, conditioned adds a criticality
proximity term. The query criticality is computed deterministically from the frozen board (alive list
intersect true roles) — omniscient, offline, never shown to the agent. Memory off is the floor.

  poetry run python evaluation/src/experiments/criticality_screen.py \
      --batch batch_results/ab_arms_town.jsonl --store memory_stores/v6_0 --n 40
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, OrderedDict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from Agents.llm_factory.embeddings import create_embeddings
from Agents.schemas import RetrievedObservation
from Agents.schemas.memory import StoredObservation
from evaluation.src.components.decision_scoring import THREAT_ROLES, allow_abstain_for, score_vote
from evaluation.src.components.situation_summary import eval_case_to_agent_payload
from evaluation.src.data.local_cases import LocalCaseSource
from evaluation.src.experiments.decision_replay import _replay_vote, load_game_index, mcnemar_p
from Agents.memory.enrichment.situation_agent import _generate_situations_for_agent


def load_candidates_by_role(store_dir: Path, roles: frozenset[str]) -> dict[str, list[StoredObservation]]:
    """Per-role v6 DAY candidate pools (both day phases — the v6 day cell is unified; night cells are
    excluded since day-votes retrieve the day cell). Production retrieves from the decision's own role
    namespace, so the screen pools per role too."""
    doc = json.loads((store_dir / "observations.json").read_text())
    out: dict[str, list[StoredObservation]] = {r: [] for r in roles}
    for key, entries in doc.get("namespaces", {}).items():
        _, role, phase = key.split("/")
        if role not in roles or phase == "night_action":
            continue
        for e in entries:
            out[role].append(StoredObservation(**e["value"]))
    return out


class _RolePool:
    """Embedded candidate pool for one role (vectors + criticality arrays + game ids)."""

    def __init__(self, cands: list[StoredObservation], emb) -> None:
        self.cands = cands
        self.alive = np.array([c.players_alive if c.players_alive is not None else -99 for c in cands])
        self.dist = np.array([c.distance_to_parity if c.distance_to_parity is not None else -99 for c in cands])
        self.swing = np.array([1 if c.is_swing else 0 for c in cands])
        self.game = np.array([c.game_id or "" for c in cands])
        self.vecs = np.array(emb.embed_documents([c.situation for c in cands])) if cands else np.zeros((0, 1))


def query_criticality(surviving_players: list[str], roles: dict[str, str]) -> tuple[int, int, bool]:
    """Deterministic query criticality from the frozen board. distance_to_parity is wolf-faction
    parity (non-wolf eliminations until wolves reach parity); is_swing = one result from flipping.
    Town-lensed (wolves are the dominant parity driver; SK is a minority wildcard)."""
    alive = list(surviving_players)
    n = len(alive)
    wolves = sum(1 for p in alive if roles.get(p) == "wolf")
    others = n - wolves
    distance_to_parity = others - wolves
    return n, distance_to_parity, distance_to_parity <= 1


def _cosine_matrix(q: np.ndarray, M: np.ndarray) -> np.ndarray:
    qn = q / (np.linalg.norm(q) + 1e-9)
    Mn = M / (np.linalg.norm(M, axis=1, keepdims=True) + 1e-9)
    return Mn @ qn


def iter_town_day_votes(batch_path: Path, roles: frozenset[str]):
    """Yield (case, game) for every day_vote decision by one of `roles` in the batch (no requirement
    that the frozen case carried retrieved memory — the screen retrieves fresh from v6)."""
    source = LocalCaseSource(batch_path)
    index = load_game_index(batch_path)
    for tid in source.trace_ids():
        game = index.get(tid)
        if not game:
            continue
        for case in source.eval_cases(tid):
            if case.action_phase == "day_vote" and case.player_role in roles and case.situations:
                yield case, game


def select_spread(
    batch_path: Path,
    n: int,
    roles: frozenset[str],
    held_out_only: bool = False,
    source_games: set[str] | None = None,
) -> list[tuple[Any, dict]]:
    """Spread ~n town day-votes across DAYS first (round-robin over day buckets), then across games
    within a day. Day-balanced because the screen is stratified by day and late-game town votes are
    scarce — a game-first round-robin would fill n entirely with day-2 votes and leave the
    high-criticality stratum empty."""
    source_games = source_games or set()
    by_day: dict[int, list] = {}
    for case, game in iter_town_day_votes(batch_path, roles):
        if held_out_only and str(game["game_id"]) in source_games:
            continue
        by_day.setdefault(case.day, []).append((case, game))
    days = sorted(by_day)
    picked, depth = [], 0
    while len(picked) < n:
        added = False
        for d in days:
            pool = by_day[d]
            if len(pool) > depth:
                picked.append(pool[depth])
                added = True
                if len(picked) >= n:
                    break
        if not added:
            break
        depth += 1
    return picked


def _retrieved(cands: list[StoredObservation], idxs: list[int], query: str) -> list[RetrievedObservation]:
    return [
        RetrievedObservation(key=str(i), observation=cands[i], matched_situation=query, score=None)
        for i in idxs
    ]


def load_source_games(source_set: Path | None) -> set[str]:
    """Game_ids the v6 store was extracted from — decisions in these games are 'in-sample' (same-game
    memory is excluded at retrieval, but the game still contributed siblings to the store); decisions
    in any OTHER game are fully held-out (the store never saw them)."""
    if not source_set or not source_set.exists():
        return set()
    return {
        json.loads(l)["game_id"]
        for l in source_set.read_text().splitlines()
        if l.strip()
    }


def run_screen(
    batch_path: Path,
    store_dir: Path,
    n: int = 40,
    top_k: int = 5,
    lam: float = 0.06,
    mu: float = 0.05,
    nu: float = 0.02,
    max_workers: int = 6,
    source_games: set[str] | None = None,
    held_out_only: bool = False,
    roles: frozenset[str] = frozenset({"villager"}),
    regenerate_query: bool = False,
) -> dict[str, Any]:
    source_games = source_games or set()
    emb = create_embeddings()
    pools = {r: _RolePool(c, emb) for r, c in load_candidates_by_role(store_dir, roles).items()}

    cases = select_spread(
        batch_path, n, roles, held_out_only=held_out_only, source_games=source_games
    )

    def one(case, game) -> dict[str, Any] | None:
        try:
            return _one_inner(case, game)
        except Exception:  # noqa: BLE001 — a role the replay harness can't handle (e.g. vigilante
            return None    # day_vote) or a transient failure drops the decision, not the whole run.

    def _one_inner(case, game) -> dict[str, Any] | None:
        pool = pools.get(case.player_role)
        if pool is None or not pool.cands:
            return None  # role has no v6 day store
        roles_map = game["roles"]
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        q_alive, q_dist, q_swing = query_criticality(
            case.private_context.surviving_players, roles_map
        )
        # Faithful v6 end-to-end: REGENERATE the situation summary under the v6 cell schema (so the
        # query is composed in the same dimensions as the v6 store). Default reuses the frozen v5
        # summary (the original, mismatched-base behavior) for comparison.
        if regenerate_query:
            query = " ".join(_generate_situations_for_agent(eval_case_to_agent_payload(case), "day_vote")[0])
        else:
            query = " ".join(case.situations)
        qv = np.array(emb.embed_query(query))
        cos = _cosine_matrix(qv, pool.vecs)
        # Exclude memories mined from THIS decision's own game (a memory from game G knows G's
        # outcome — production never retrieves same-game memory; the screen must not either).
        cos = np.where(pool.game == str(game["game_id"]), -1e9, cos)

        flat_idx = list(np.argsort(-cos)[:top_k])
        cond = (
            cos
            - lam * np.abs(pool.alive - q_alive)
            - nu * np.abs(pool.dist - q_dist)
            + mu * (pool.swing == (1 if q_swing else 0))
        )
        cond_idx = list(np.argsort(-cond)[:top_k])

        arms = {
            "off": [],
            "flat": _retrieved(pool.cands, flat_idx, query),
            "cond": _retrieved(pool.cands, cond_idx, query),
        }
        out = {
            "day": case.day,
            "role": case.player_role,
            "q_alive": q_alive,
            "q_swing": q_swing,
            "held_out": str(game["game_id"]) not in source_games,
        }
        for arm, retrieved in arms.items():
            votee, _ = _replay_vote(case, retrieved, allow)
            out[arm] = score_vote(votee, roles_map)
            out[f"{arm}_vote"] = votee
        out["same_regime_in_flat"] = sum(
            1 for i in flat_idx if abs(int(pool.alive[i]) - q_alive) <= 1
        )
        out["same_regime_in_cond"] = sum(
            1 for i in cond_idx if abs(int(pool.alive[i]) - q_alive) <= 1
        )
        return out

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rows = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]
    rows = [r for r in rows if r is not None]

    n_cands = sum(len(p.cands) for p in pools.values())
    return _aggregate(rows, batch_path, store_dir, n, top_k, lam, mu, nu, n_cands)


def _netval(o: Any) -> int:
    return 1 if o.hit_threat else (-1 if o.is_town_mislynch else 0)


def _aggregate(rows, batch_path, store_dir, n, top_k, lam, mu, nu, n_cands) -> dict[str, Any]:
    # high-criticality stratum = swing OR <=4 alive (endgame); the rest is mid-game.
    def stratum(r) -> str:
        return "high_criticality" if (r["q_swing"] or r["q_alive"] <= 4) else "mid_game"

    arms = ("off", "flat", "cond")
    strata: dict[str, list] = {"all": rows, "mid_game": [], "high_criticality": []}
    for r in rows:
        strata[stratum(r)].append(r)

    def summarize(group: list) -> dict[str, Any]:
        valid = [r for r in group if r["flat_vote"] is not None and r["cond_vote"] is not None]
        d: dict[str, Any] = {"n": len(group)}
        for a in arms:
            nv = [_netval(r[a]) for r in group]
            acc = [int(r[a].hit_threat) for r in group]
            d[a] = {
                "net_value": round(sum(nv) / len(nv), 3) if nv else None,
                "accuracy": round(sum(acc) / len(acc), 3) if acc else None,
            }
        if d["cond"]["net_value"] is not None and d["flat"]["net_value"] is not None:
            d["cond_minus_flat_netvalue"] = round(d["cond"]["net_value"] - d["flat"]["net_value"], 3)
        # causal flip-rate: cond vote != flat vote, and where the flip landed
        flips = [r for r in valid if r["cond_vote"] != r["flat_vote"]]
        toward = sum(1 for r in flips if r["cond"].hit_threat and not r["flat"].hit_threat)
        away = sum(1 for r in flips if r["flat"].hit_threat and not r["cond"].hit_threat)
        d["flip"] = {
            "n_valid": len(valid),
            "flip_rate": round(len(flips) / len(valid), 3) if valid else None,
            "flips_toward_threat": toward,
            "flips_away_from_threat": away,
            "mcnemar_p": round(mcnemar_p(away, toward), 4),
        }
        d["same_regime_topk"] = {
            "flat_avg": round(sum(r["same_regime_in_flat"] for r in group) / len(group), 2) if group else None,
            "cond_avg": round(sum(r["same_regime_in_cond"] for r in group) / len(group), 2) if group else None,
        }
        return d

    by_stratum = {k: summarize(v) for k, v in strata.items()}
    # by-day strata (the spec's falsification axis: cond-flat should grow with the day).
    by_day_rows: dict[int, list] = {}
    for r in rows:
        by_day_rows.setdefault(r["day"], []).append(r)
    by_day = {str(d): summarize(by_day_rows[d]) for d in sorted(by_day_rows)}
    # by-role (town faction): does the lever hold beyond villagers?
    by_role_rows: dict[str, list] = {}
    for r in rows:
        by_role_rows.setdefault(r.get("role", "?"), []).append(r)
    by_role = {role: summarize(by_role_rows[role]) for role in sorted(by_role_rows)}
    # held-out subset = decisions whose game never contributed to the store (independent confirmation).
    held = [r for r in rows if r.get("held_out")]
    insample = [r for r in rows if not r.get("held_out")]
    by_holdout = {
        "held_out": {**summarize(held), "high_criticality": summarize([r for r in held if (r["q_swing"] or r["q_alive"] <= 4)])} if held else {"n": 0},
        "in_sample": {"n": len(insample)},
    }
    sig = _verdict(by_stratum)
    return {
        "batch": batch_path.name,
        "store": str(store_dir),
        "n_requested": n,
        "n_candidates": n_cands,
        "params": {"top_k": top_k, "lambda_alive": lam, "mu_swing": mu, "nu_dist": nu},
        "by_stratum": by_stratum,
        "by_day": by_day,
        "by_role": by_role,
        "by_holdout": by_holdout,
        "criticality_signature": sig,
    }


def _verdict(by_stratum: dict) -> dict[str, Any]:
    """Operationalize the go/no-go signature: conditioning should help where regime-mismatch bites
    (high criticality), be ~null mid-game, and actually flip votes toward threats."""
    high = by_stratum.get("high_criticality", {})
    mid = by_stratum.get("mid_game", {})
    all_ = by_stratum.get("all", {})
    high_d = high.get("cond_minus_flat_netvalue")
    mid_d = mid.get("cond_minus_flat_netvalue")
    flip = all_.get("flip", {})
    flips_changed = (flip.get("flip_rate") or 0) > 0.05
    toward, away = flip.get("flips_toward_threat", 0), flip.get("flips_away_from_threat", 0)
    concentrated = (high_d is not None and mid_d is not None and high_d > 0 and high_d > mid_d)
    go = bool(concentrated and flips_changed and toward >= away)
    return {
        "high_criticality_cond_minus_flat": high_d,
        "mid_game_cond_minus_flat": mid_d,
        "gain_concentrated_in_high_criticality": concentrated,
        "flip_rate_nontrivial": flips_changed,
        "flips_net_toward_threat": toward >= away,
        "VERDICT": "GO (lever shows -> roll full DAG)" if go
        else "NO-GO / inconclusive (triage — read strata + flips by hand)",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", required=True, type=Path)
    ap.add_argument("--store", default="memory_stores/v6_0", type=Path)
    ap.add_argument("--n", type=int, default=40)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--lambda-alive", type=float, default=0.06)
    ap.add_argument("--mu-swing", type=float, default=0.05)
    ap.add_argument("--nu-dist", type=float, default=0.02)
    ap.add_argument(
        "--source-set",
        type=Path,
        default=Path("evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl"),
        help="the extraction set the v6 store was built from; decisions in OTHER games are held-out",
    )
    ap.add_argument(
        "--held-out-only",
        action="store_true",
        help="restrict decisions to games NOT in --source-set (fully held-out; store never saw them)",
    )
    ap.add_argument(
        "--roles",
        default="villager,healer,investigator",
        help="comma-separated town day-voters to screen (each retrieves from its OWN v6 day pool); "
        "vigilante day_vote is not supported by the replay harness (REPLAYABLE_TOWN_ROLES)",
    )
    ap.add_argument(
        "--regenerate-query",
        action="store_true",
        help="regenerate the situation summary under the v6 cell schema (faithful end-to-end v6) "
        "instead of reusing the frozen v5 summary",
    )
    args = ap.parse_args()
    roles = frozenset(r.strip() for r in args.roles.split(",") if r.strip())
    report = run_screen(
        args.batch, args.store, n=args.n, top_k=args.top_k,
        lam=args.lambda_alive, mu=args.mu_swing, nu=args.nu_dist,
        source_games=load_source_games(args.source_set),
        held_out_only=args.held_out_only, roles=roles,
        regenerate_query=args.regenerate_query,
    )
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
