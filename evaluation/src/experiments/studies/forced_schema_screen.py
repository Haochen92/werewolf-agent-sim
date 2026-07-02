"""Forced-applicability screen (v6 build) — does forcing per-memory reasoning help the vote on the
v6 dimensional store where it HURT on the old v5 store, and does it engage the memory more?

Fills the untested cell flagged by the decision-replay log: "good content x forced/reordered schema."
The original applicability probe (2026-06-13) found forcing one applies/partly/does-not verdict per
memory HURT the vote (0.75->0.55) and showed high consideration (rejection_rate 1.0) — but that was on
the cautious net-first v5 store. v6 was built to fix that content. This screen runs BOTH stores under
BOTH schemas in ONE epoch so the store x schema 2x2 is internally comparable.

EPOCH DISCIPLINE (the load-bearing rule): every vote here is regenerated NOW. Do NOT compare these
numbers to the 0.75->0.55 / +0.120 from prior runs — the model epoch may have shifted. The valid
reads are WITHIN this run (v6 vs v5, forced vs plain), where the only delta is the store/schema.

Arms per held-out town day_vote:
  off        no memory (floor)                  | plain schema
  v5_plain   retrieve v5_0 (frozen v5 query)    | plain DayVoteOutput
  v6_plain   retrieve v6_0 (regenerated v6 q)   | plain DayVoteOutput
  v5_forced  retrieve v5_0 (frozen v5 query)    | forced per-memory verdicts
  v6_forced  retrieve v6_0 (regenerated v6 q)   | forced per-memory verdicts

Each arm retrieves from its OWN store with its OWN native query (v5 uses the frozen v5 situation
summary, v6 regenerates under the v6 cell schema — each pipeline is internally matched). Same-game
memory is excluded from BOTH pools; --held-out-only additionally drops decisions whose game seeded the
v6 store. Engagement (verdict distribution) is captured for the forced arms only.

  poetry run python evaluation/src/experiments/studies/forced_schema_screen.py \
      --batch batch_results/ab_arms_town.jsonl --held-out-only --n 24
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from pydantic import Field, create_model

from Agents.llm_factory import get_llm
from Agents.llm_factory.embeddings import create_embeddings
from Agents.memory.enrichment.situation_agent import _generate_situations_for_agent
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.turn.action_space import _valid_targets_for_action, _with_dynamic_target_enum
from evaluation.src.replay.application import action_spec_for
from evaluation.src.loop.decision_scoring import allow_abstain_for, score_vote
from evaluation.src.replay.situation_summary import eval_case_to_agent_payload
from evaluation.src.experiments.studies.criticality_screen import (
    _RolePool,
    _cosine_matrix,
    _retrieved,
    iter_town_day_votes,
    load_candidates_by_role,
    load_source_games,
    select_spread,
)
from evaluation.src.replay.decision_screen import (
    DayVoteOutputStructuredApplicability,
    MemoryVerdict,
    _replay_vote,
    _replay_vote_structured,
    load_game_index,
    mcnemar_p,
)
from Agents.schemas.output import DayDiscussOutput
from evaluation.src.data.sources.sidecar import LocalCaseSource

PLAIN_ARMS = ("off", "v5_plain", "v6_plain")
FORCED_ARMS = ("v5_forced", "v6_forced")


def _topk_idx(query: str, pool: _RolePool, emb, test_gid: str, top_k: int) -> tuple[list[int], np.ndarray]:
    """Cosine top-k from a pool, excluding memories mined from the decision's own game."""
    if not pool.cands:
        return [], np.zeros(0)
    qv = np.array(emb.embed_query(query))
    cos = _cosine_matrix(qv, pool.vecs)
    cos = np.where(pool.game == test_gid, -1e9, cos)  # same-game exclusion (both stores)
    return list(np.argsort(-cos)[:top_k]), cos


def _forced_row(case, retrieved, allow, roles) -> dict[str, Any]:
    """Run the forced-schema replay, returning the vote outcome + the per-memory verdicts (with the
    model's self-reported 1-based memory_index, so we can test WHICH memories get dropped)."""
    result = _replay_vote_structured(case, retrieved, allow)
    if result is None:
        return {"votee": None, "hit": None, "net": 0, "verdicts": [], "idx": [], "n_mem": len(retrieved)}
    verdicts = list(getattr(result, "memory_applicability", []) or [])
    votee = getattr(result, "vote_target", None)
    out = score_vote(votee, roles) if votee is not None else None
    return {
        "votee": votee,
        "hit": bool(out.hit_threat) if out else None,
        "net": (1 if out.hit_threat else (-1 if out.is_town_mislynch else 0)) if out else 0,
        "verdicts": [getattr(v, "verdict", None) for v in verdicts],
        "idx": [getattr(v, "memory_index", None) for v in verdicts],
        "n_mem": len(retrieved),
    }


def _plain_row(case, retrieved, allow, roles) -> dict[str, Any]:
    votee, _ = _replay_vote(case, retrieved, allow)
    out = score_vote(votee, roles) if votee is not None else None
    return {
        "votee": votee,
        "hit": bool(out.hit_threat) if out else None,
        "net": (1 if out.hit_threat else (-1 if out.is_town_mislynch else 0)) if out else 0,
    }


# ── Variant probe: prompt-limitation vs output-limitation (does delivery fix coverage?) ──
# The "one verdict per memory" instruction currently lives ONLY in the pydantic field description.
# (A) promptbody: also state it in the prompt BODY. (B) pin: force the list length = N in the schema.
# Coverage jumps under (A) => prompt/delivery limit. (B) emits filler (uniform verdicts / duplicate
# `why`) => output limit; (B) emits real distinct rows => capability was there, delivery was the gate.

_BODY_INSTRUCTION = (
    "\n\nThe retrieved observations above are numbered 1 to {n}. In `memory_applicability` you MUST "
    "output exactly one verdict for EACH numbered observation — {n} verdicts, in order, none skipped — "
    "judging how much each applies to your current board, BEFORE you decide your vote."
)


def _pin_length_schema(schema: type, n: int) -> type:
    """Subclass the (already target-enum'd) schema, overriding memory_applicability to require exactly
    n rows. Baked into an Annotated field so the constraint survives (the enum rebuild copies only
    annotation+default, but a subclass override is preserved)."""
    return create_model(
        f"{schema.__name__}_pin{n}",
        __base__=schema,
        memory_applicability=(
            Annotated[list[MemoryVerdict], Field(min_length=n, max_length=n)], ...
        ),
    )


def _forced_variant(case, retrieved, allow, roles, *, prompt_body: bool, pin_length: bool) -> dict[str, Any]:
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved
    payload["strategy_points"] = []
    payload["allow_abstain"] = allow
    spec = action_spec_for(case)
    n = len(retrieved)
    schema = _with_dynamic_target_enum(
        DayVoteOutputStructuredApplicability, spec.output_key,
        _valid_targets_for_action(payload, spec.output_key),
    )
    if pin_length and n > 0:
        schema = _pin_length_schema(schema, n)
    blank = {"votee": None, "hit": None, "net": 0, "verdicts": [], "idx": [], "why": [], "n_mem": n}
    try:
        messages = spec.prompt_template.invoke(build_agent_prompt_input(payload)).to_messages()
        if prompt_body:
            messages[-1].content = messages[-1].content + _BODY_INSTRUCTION.format(n=n)
        result = get_llm().with_structured_output(schema).invoke(
            messages, config={"run_name": f"variant_{case.player_id}"}
        )
    except Exception:  # noqa: BLE001 — pin can reject (model won't hit N); count as a dropped decision
        return blank
    verdicts = list(getattr(result, "memory_applicability", []) or [])
    votee = getattr(result, "vote_target", None)
    out = score_vote(votee, roles) if votee is not None else None
    return {
        "votee": votee,
        "hit": bool(out.hit_threat) if out else None,
        "net": (1 if out.hit_threat else (-1 if out.is_town_mislynch else 0)) if out else 0,
        "verdicts": [getattr(v, "verdict", None) for v in verdicts],
        "idx": [getattr(v, "memory_index", None) for v in verdicts],
        "why": [(getattr(v, "why", "") or "")[:120] for v in verdicts],
        "n_mem": n,
    }


def _filler_signal(rows, variant) -> dict[str, Any]:
    """Output-limit tell: when forced to emit N rows, are they real or padding? all-same-verdict and
    duplicate `why` text both flag filler."""
    uniform = ndec = 0
    distinct_ratios = []
    for r in rows:
        f = r[variant]
        v = [x for x in f["verdicts"] if x]
        if len(v) < 2:
            continue
        ndec += 1
        if len(set(v)) == 1:
            uniform += 1
        whys = [w for w in f["why"] if w]
        if whys:
            distinct_ratios.append(len(set(whys)) / len(whys))
    return {
        "n_multi_verdict": ndec,
        "all_same_verdict_frac": round(uniform / ndec, 3) if ndec else None,
        "distinct_why_ratio": round(sum(distinct_ratios) / len(distinct_ratios), 3) if distinct_ratios else None,
    }


def run_variants(
    batch_path: Path,
    v6_store: Path,
    n: int = 60,
    top_k: int = 5,
    max_workers: int = 6,
    source_games: set[str] | None = None,
    held_out_only: bool = False,
    roles: frozenset[str] = frozenset({"villager", "healer", "investigator"}),
) -> dict[str, Any]:
    """v6-only: compare base / promptbody / pin forced variants on coverage + filler."""
    source_games = source_games or set()
    emb = create_embeddings()
    pools = {r: _RolePool(c, emb) for r, c in load_candidates_by_role(v6_store, roles).items()}
    cases = select_spread(batch_path, n, roles, held_out_only=held_out_only, source_games=source_games)
    variants = ("base", "promptbody", "pin")
    flags = {"base": (False, False), "promptbody": (True, False), "pin": (False, True)}

    def one(case, game) -> dict[str, Any] | None:
        try:
            pool = pools.get(case.player_role)
            if not pool or not pool.cands:
                return None
            gid = str(game["game_id"])
            allow = allow_abstain_for(case.day, game["day_resolutions"])
            query = " ".join(_generate_situations_for_agent(eval_case_to_agent_payload(case), "day_vote")[0])
            idx, _ = _topk_idx(query, pool, emb, gid, top_k)
            mem = _retrieved(pool.cands, idx, query)
            row: dict[str, Any] = {"n_mem": len(mem), "held_out": gid not in source_games}
            for v in variants:
                pb, pin = flags[v]
                row[v] = _forced_variant(case, mem, allow, game["roles"], prompt_body=pb, pin_length=pin)
            return row
        except Exception:  # noqa: BLE001
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rows = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]
    rows = [r for r in rows if r is not None]
    return {
        "mode": "variants (v6 only)",
        "batch": batch_path.name,
        "v6_store": str(v6_store),
        "n_decisions": len(rows),
        "top_k": top_k,
        "epoch_note": "within-run only",
        "by_variant": {
            v: {
                "vote": _vote_stats(rows, v),
                "engagement": _engagement_stats(rows, v, top_k),
                "filler": _filler_signal(rows, v),
                "samples": [
                    {"n_mem": r[v]["n_mem"], "idx": r[v]["idx"], "verdicts": r[v]["verdicts"]}
                    for r in rows[:8]
                ],
            }
            for v in variants
        },
    }


# ── Discussion-phase coverage (the production DayDiscussOutput now carries the field natively) ──
# Validates the day-vote coverage win generalises to discussion (which we never measured). Direct chain
# call because _run_agent's mapping drops memory_applicability. Also keeps the message to eyeball that
# forced per-memory reasoning didn't make discussion robotic.

def iter_town_day_discussion(batch_path: Path, roles: frozenset[str]):
    source = LocalCaseSource(batch_path)
    index = load_game_index(batch_path)
    for tid in source.trace_ids():
        game = index.get(tid)
        if not game:
            continue
        for case in source.eval_cases(tid):
            if case.action_phase == "day_discussion" and case.player_role in roles:
                yield case, game


def _discussion_row(case, retrieved) -> dict[str, Any]:
    payload = eval_case_to_agent_payload(case)
    payload["retrieved_observations"] = retrieved
    payload["strategy_points"] = []
    spec = action_spec_for(case)  # (role, day_discussion) -> DayDiscussOutput
    try:
        obj = (spec.prompt_template | get_llm().with_structured_output(DayDiscussOutput)).invoke(
            build_agent_prompt_input(payload), config={"run_name": f"disc_{case.player_id}"}
        )
    except Exception:  # noqa: BLE001
        return {"n_mem": len(retrieved), "idx": [], "verdicts": [], "why": [], "msg": None, "passed": None}
    v = list(getattr(obj, "memory_applicability", []) or [])
    return {
        "n_mem": len(retrieved),
        "idx": [getattr(x, "memory_index", None) for x in v],
        "verdicts": [getattr(x, "verdict", None) for x in v],
        "why": [(getattr(x, "why", "") or "")[:120] for x in v],
        "msg": (getattr(obj, "message", "") or "")[:200],
        "passed": getattr(obj, "pass_turn", None),
    }


def run_discussion(
    batch_path: Path,
    v6_store: Path,
    n: int = 40,
    top_k: int = 5,
    max_workers: int = 6,
    source_games: set[str] | None = None,
    held_out_only: bool = False,
    roles: frozenset[str] = frozenset({"villager", "healer", "investigator"}),
) -> dict[str, Any]:
    source_games = source_games or set()
    emb = create_embeddings()
    pools = {r: _RolePool(c, emb) for r, c in load_candidates_by_role(v6_store, roles).items()}
    # round-robin across games, held-out filter
    by_game: dict[str, list] = {}
    for case, game in iter_town_day_discussion(batch_path, roles):
        gid = str(game["game_id"])
        if held_out_only and gid in source_games:
            continue
        by_game.setdefault(gid, []).append((case, game))
    picked, depth = [], 0
    while len(picked) < n and by_game:
        added = False
        for pool in by_game.values():
            if len(pool) > depth:
                picked.append(pool[depth]); added = True
                if len(picked) >= n:
                    break
        if not added:
            break
        depth += 1

    def one(case, game) -> dict[str, Any] | None:
        try:
            pool = pools.get(case.player_role)
            if not pool or not pool.cands:
                return None
            gid = str(game["game_id"])
            query = " ".join(_generate_situations_for_agent(eval_case_to_agent_payload(case), "day_discussion")[0])
            idx, _ = _topk_idx(query, pool, emb, gid, top_k)
            row = _discussion_row(case, _retrieved(pool.cands, idx, query))
            row["role"] = case.player_role
            row["day"] = case.day
            return row
        except Exception:  # noqa: BLE001
            return None

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rows = [f.result() for f in [ex.submit(one, c, g) for c, g in picked]]
    rows = [r for r in rows if r is not None]
    spoke = [r for r in rows if r.get("passed") is False]
    return {
        "mode": "discussion coverage (production DayDiscussOutput, instruction live)",
        "batch": batch_path.name,
        "v6_store": str(v6_store),
        "n_decisions": len(rows),
        "n_spoke": len(spoke),
        "n_passed": sum(1 for r in rows if r.get("passed") is True),
        "top_k": top_k,
        "coverage": _disc_coverage(rows, top_k),
        "sample_messages": [{"passed": r["passed"], "verdicts": r["verdicts"], "msg": r["msg"]} for r in rows[:8]],
    }


def _disc_coverage(rows, top_k) -> dict[str, Any]:
    shown = emitted = reliable = ndec = 0
    dist: Counter[str] = Counter()
    for r in rows:
        ndec += 1
        shown += r["n_mem"]
        emitted += len(r["verdicts"])
        dist.update(v for v in r["verdicts"] if v)
        reliable += int(len(r["verdicts"]) == r["n_mem"] and r["n_mem"] > 0)
    total = sum(dist.values())
    return {
        "n_decisions": ndec,
        "memories_shown": shown,
        "verdicts_emitted": emitted,
        "row_reliability": round(reliable / ndec, 3) if ndec else None,
        "verdict_dist": dict(dist),
        "engaged_as_applicable": round((dist.get("fully_applies", 0) + dist.get("partly_applies", 0)) / total, 3) if total else None,
        "rank_coverage": _disc_rank_cov(rows, top_k),
    }


def _disc_rank_cov(rows, top_k) -> dict[str, Any]:
    num = [0] * (top_k + 2)
    den = [0] * (top_k + 2)
    for r in rows:
        n = r["n_mem"]
        idxset = {i for i in r["idx"] if isinstance(i, int)}
        for rank in range(1, min(n, top_k) + 1):
            den[rank] += 1
            if rank in idxset:
                num[rank] += 1
    return {str(rk): round(num[rk] / den[rk], 3) for rk in range(1, top_k + 1) if den[rk]}


def run_screen(
    batch_path: Path,
    v5_store: Path,
    v6_store: Path,
    n: int = 24,
    top_k: int = 5,
    max_workers: int = 6,
    source_games: set[str] | None = None,
    held_out_only: bool = False,
    roles: frozenset[str] = frozenset({"villager", "healer", "investigator"}),
    forced_only: bool = False,
) -> dict[str, Any]:
    source_games = source_games or set()
    emb = create_embeddings()
    v5_pools = {r: _RolePool(c, emb) for r, c in load_candidates_by_role(v5_store, roles).items()}
    v6_pools = {r: _RolePool(c, emb) for r, c in load_candidates_by_role(v6_store, roles).items()}
    cases = select_spread(batch_path, n, roles, held_out_only=held_out_only, source_games=source_games)

    def one(case, game) -> dict[str, Any] | None:
        try:
            return _one_inner(case, game)
        except Exception:  # noqa: BLE001 — drop a single bad decision, not the run
            return None

    def _one_inner(case, game) -> dict[str, Any] | None:
        v5p, v6p = v5_pools.get(case.player_role), v6_pools.get(case.player_role)
        if not v5p or not v5p.cands or not v6p or not v6p.cands:
            return None
        roles_map = game["roles"]
        gid = str(game["game_id"])
        allow = allow_abstain_for(case.day, game["day_resolutions"])

        v5_query = " ".join(case.situations)  # frozen v5 situation summary (native to v5 pipeline)
        v6_query = " ".join(  # regenerated NOW under the v6 cell schema (native to v6 pipeline)
            _generate_situations_for_agent(eval_case_to_agent_payload(case), "day_vote")[0]
        )
        v5_idx, _ = _topk_idx(v5_query, v5p, emb, gid, top_k)
        v6_idx, _ = _topk_idx(v6_query, v6p, emb, gid, top_k)
        v5_mem = _retrieved(v5p.cands, v5_idx, v5_query)
        v6_mem = _retrieved(v6p.cands, v6_idx, v6_query)

        row: dict[str, Any] = {"day": case.day, "role": case.player_role,
                               "held_out": gid not in source_games}
        if not forced_only:
            row["off"] = _plain_row(case, [], allow, roles_map)
            row["v5_plain"] = _plain_row(case, v5_mem, allow, roles_map)
            row["v6_plain"] = _plain_row(case, v6_mem, allow, roles_map)
        row["v5_forced"] = _forced_row(case, v5_mem, allow, roles_map)
        row["v6_forced"] = _forced_row(case, v6_mem, allow, roles_map)
        return row

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rows = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]
    rows = [r for r in rows if r is not None]
    return _aggregate(rows, batch_path, v5_store, v6_store, top_k)


def _vote_stats(rows, arm) -> dict[str, Any]:
    hits = [int(r[arm]["hit"]) for r in rows if r[arm]["hit"] is not None]
    nets = [r[arm]["net"] for r in rows if r[arm]["hit"] is not None]
    return {
        "n": len(hits),
        "accuracy": round(sum(hits) / len(hits), 3) if hits else None,
        "net_value": round(sum(nets) / len(nets), 3) if nets else None,
    }


def _rank_coverage(rows, arm, top_k) -> dict[str, Any]:
    """Test the tail-drop hypothesis: memories are injected in descending relevance, so if the model
    drops the LOW-ranked ones, coverage[rank] should fall as rank grows. coverage[r] = fraction of
    decisions that had >=r memories where a verdict reporting memory_index==r was emitted. Also: how
    often the emitted index set is a clean top prefix {1..k} (in-order, no gaps)."""
    num = [0] * (top_k + 2)
    den = [0] * (top_k + 2)
    prefix = ndec = 0
    samples = []
    for r in rows:
        f = r[arm]
        n = f["n_mem"]
        if n == 0 and not f["idx"]:
            continue
        ndec += 1
        idxset = {i for i in f["idx"] if isinstance(i, int)}
        for rank in range(1, min(n, top_k) + 1):
            den[rank] += 1
            if rank in idxset:
                num[rank] += 1
        k = len(idxset)
        if idxset and idxset == set(range(1, k + 1)):
            prefix += 1
        if len(samples) < 12:
            samples.append({"n_mem": n, "emitted_idx": sorted(idxset)})
    cov = {str(rank): round(num[rank] / den[rank], 3) for rank in range(1, top_k + 1) if den[rank]}
    return {"coverage_by_rank": cov, "clean_top_prefix_fraction": round(prefix / ndec, 3) if ndec else None,
            "sample_rows": samples}


def _engagement_stats(rows, arm, top_k) -> dict[str, Any]:
    dist: Counter[str] = Counter()
    shown = emitted = reliable = ndec = 0
    for r in rows:
        f = r[arm]
        if f["hit"] is None and not f["verdicts"]:
            continue
        ndec += 1
        dist.update(v for v in f["verdicts"] if v)
        shown += f["n_mem"]
        emitted += len(f["verdicts"])
        reliable += int(len(f["verdicts"]) == f["n_mem"] and f["n_mem"] > 0)
    total = sum(dist.values())
    applicable = dist.get("fully_applies", 0) + dist.get("partly_applies", 0)
    return {
        "n_decisions": ndec,
        "memories_shown": shown,
        "verdicts_emitted": emitted,
        "row_reliability": round(reliable / ndec, 3) if ndec else None,  # 1 verdict per memory
        "verdict_dist": dict(dist),
        "engaged_as_applicable": round(applicable / total, 3) if total else None,
        "rejected_does_not_apply": round(dist.get("does_not_apply", 0) / total, 3) if total else None,
        "rank_coverage": _rank_coverage(rows, arm, top_k),
    }


def _paired_flip(rows, arm_a, arm_b) -> dict[str, Any]:
    """McNemar: does arm_b's vote beat arm_a's? b=a-right/b-wrong, c=a-wrong/b-right."""
    b = c = both = 0
    for r in rows:
        ha, hb = r[arm_a]["hit"], r[arm_b]["hit"]
        if ha is None or hb is None:
            continue
        both += 1
        if ha and not hb:
            b += 1
        elif hb and not ha:
            c += 1
    return {"n_paired": both, f"{arm_a}>_{arm_b}": b, f"{arm_b}>_{arm_a}": c,
            "mcnemar_p": round(mcnemar_p(b, c), 4)}


def _aggregate(rows, batch_path, v5_store, v6_store, top_k) -> dict[str, Any]:
    has_plain = bool(rows) and "off" in rows[0]
    arms = (PLAIN_ARMS + FORCED_ARMS) if has_plain else FORCED_ARMS
    vote = {a: _vote_stats(rows, a) for a in arms}
    held = [r for r in rows if r.get("held_out")]
    out: dict[str, Any] = {
        "batch": batch_path.name,
        "v5_store": str(v5_store),
        "v6_store": str(v6_store),
        "n_decisions": len(rows),
        "n_held_out": len(held),
        "top_k": top_k,
        "epoch_note": "all votes regenerated this run; compare WITHIN run only, not vs prior epochs",
        "vote_accuracy": vote,
        "engagement_forced": {a: _engagement_stats(rows, a, top_k) for a in FORCED_ARMS},
        "paired_flips": {"v6_forced_vs_v5_forced": _paired_flip(rows, "v5_forced", "v6_forced")},
    }
    if has_plain:
        out["forced_minus_plain"] = {
            "v5_forced_minus_v5_plain": round(vote["v5_forced"]["accuracy"] - vote["v5_plain"]["accuracy"], 3)
            if vote["v5_forced"]["accuracy"] is not None and vote["v5_plain"]["accuracy"] is not None else None,
            "v6_forced_minus_v6_plain": round(vote["v6_forced"]["accuracy"] - vote["v6_plain"]["accuracy"], 3)
            if vote["v6_forced"]["accuracy"] is not None and vote["v6_plain"]["accuracy"] is not None else None,
        }
        out["paired_flips"]["v6_plain_vs_v5_plain"] = _paired_flip(rows, "v5_plain", "v6_plain")
        out["paired_flips"]["v6_forced_vs_v6_plain"] = _paired_flip(rows, "v6_plain", "v6_forced")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", required=True, type=Path)
    ap.add_argument("--v5-store", default=Path("memory_stores/v5_0"), type=Path)
    ap.add_argument("--v6-store", default=Path("memory_stores/v6_0"), type=Path)
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--roles", default="villager,healer,investigator")
    ap.add_argument("--source-set", type=Path,
                    default=Path("evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl"))
    ap.add_argument("--held-out-only", action="store_true")
    ap.add_argument("--forced-only", action="store_true",
                    help="skip the off/plain arms (cheaper) — for the engagement/rank-coverage analysis")
    ap.add_argument("--variants", action="store_true",
                    help="v6-only base/promptbody/pin probe: is partial coverage a prompt or output limit?")
    ap.add_argument("--discussion", action="store_true",
                    help="v6-only day_discussion coverage under the LIVE production DayDiscussOutput")
    ap.add_argument("--max-workers", type=int, default=6)
    args = ap.parse_args()
    roles = frozenset(r.strip() for r in args.roles.split(",") if r.strip())
    common = dict(n=args.n, top_k=args.top_k, max_workers=args.max_workers,
                  source_games=load_source_games(args.source_set),
                  held_out_only=args.held_out_only, roles=roles)
    if args.discussion:
        report = run_discussion(args.batch, args.v6_store, **common)
    elif args.variants:
        report = run_variants(args.batch, args.v6_store, **common)
    else:
        report = run_screen(args.batch, args.v5_store, args.v6_store,
                            forced_only=args.forced_only, **common)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
