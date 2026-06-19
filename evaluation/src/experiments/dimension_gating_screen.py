"""v7 — does SOFT dimension-gating cut the not-relevant retrieval waste? (LLM-judge replay screen.)

G3c showed embedding similarity is blind to applicability (~58% not_relevant, score can't separate);
the gating-efficacy screen showed criticality dims help only modestly and couldn't test the SEMANTIC
gate (exposure_class / info_landscape_class) because the query enum wasn't persisted. This screen
regenerates the query (so the semantic enums exist), retrieves WIDE from the v6_1 store, builds two
top-k sets — UNGATED (cosine) vs GATED (cosine soft-reweighted by query↔stored dim alignment, the
production `dimension_gating.reweight` logic) — and runs the forced per-memory applicability judge
(`DayVoteOutputStructuredApplicability`, prompt-body + length-pinned = the validated full-coverage
config) on each. Headline = does GATED have a lower `does_not_apply` rate than UNGATED?

Held-out: town day-votes from a v6ab batch (NOT in v6_1's 20 source games); same-game candidates
excluded at retrieval. Reuses criticality_screen (pools/retrieve/select) + forced_schema_screen (judge).

  poetry run python evaluation/src/experiments/dimension_gating_screen.py \
      --batch batch_results/v6ab_townsp.jsonl --store memory_stores/v6_1 --n 24
"""

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from Agents.llm_factory.embeddings import create_embeddings  # noqa: E402
from Agents.memory.enrichment.situation_agent import _generate_situations_for_agent  # noqa: E402
from Agents.memory.retrieval.dimension_gating import WEIGHT, alignment  # noqa: E402
from evaluation.src.components.decision_scoring import allow_abstain_for  # noqa: E402
from evaluation.src.components.situation_summary import eval_case_to_agent_payload  # noqa: E402
from evaluation.src.experiments.criticality_screen import (  # noqa: E402
    _RolePool, _cosine_matrix, _retrieved, load_candidates_by_role, load_source_games, select_spread,
)
from evaluation.src.experiments.decision_replay import load_game_index  # noqa: E402
from evaluation.src.experiments.forced_schema_screen import _forced_variant  # noqa: E402
from evaluation.src.experiments.reextract_villager_day import DEFAULT_SOURCE  # noqa: E402

ROLES = frozenset({"villager", "healer", "investigator"})  # the replayable town day-vote roles


def _stored_dims(c) -> dict:
    return {"exposure_class": c.exposure_class, "info_landscape_class": c.info_landscape_class,
            "players_alive": c.players_alive, "is_swing": c.is_swing}


def run(batch: Path, store: Path, n: int, top_k: int = 5, wide: int = 10, workers: int = 4) -> dict:
    emb = create_embeddings()
    pools = {r: _RolePool(c, emb) for r, c in load_candidates_by_role(store, ROLES).items()}
    src = load_source_games(Path(DEFAULT_SOURCE))
    cases = select_spread(batch, n, ROLES, held_out_only=True, source_games=src)
    print(f"selected {len(cases)} held-out town day-votes (n requested {n})", flush=True)

    def _one(case, game):
        pool = pools.get(case.player_role)
        if not pool or not pool.cands:
            return None
        strs, dims = _generate_situations_for_agent(eval_case_to_agent_payload(case), "day_vote")
        if not strs or not dims or not dims[0]:
            return None  # need the regenerated query dims to gate
        qdims, query = dims[0], " ".join(strs)
        gid = str(game["game_id"])
        cos = _cosine_matrix(np.array(emb.embed_query(query)), pool.vecs)
        cos = np.where(pool.game == gid, -1e9, cos)  # same-game exclusion
        wide_idx = [i for i in np.argsort(-cos)[:wide] if cos[i] > -1e8]
        if len(wide_idx) < 2:
            return None
        ungated = wide_idx[:top_k]
        gated = sorted(
            wide_idx,
            key=lambda i: cos[i] * (1 + WEIGHT * alignment(qdims, _stored_dims(pool.cands[i]))),
            reverse=True,
        )[:top_k]
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        rmap = game["roles"]
        ung = _forced_variant(case, _retrieved(pool.cands, ungated, query), allow, rmap,
                              prompt_body=True, pin_length=True)
        gat = _forced_variant(case, _retrieved(pool.cands, gated, query), allow, rmap,
                              prompt_body=True, pin_length=True)
        return {"ungated": ung, "gated": gat, "changed": len(set(ungated) - set(gated))}

    def one(case, game):
        try:
            return _one(case, game)
        except Exception as e:  # noqa: BLE001
            print(f"  drop {getattr(case,'player_id','?')}: {e}", flush=True)
            return None

    rows = []
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(one, c, g) for c, g in cases]
        for f in as_completed(futs):
            r = f.result()
            if r:
                rows.append(r)

    def rates(arm):
        v = [x for r in rows for x in r[arm]["verdicts"] if x]
        nr = sum(1 for x in v if x == "does_not_apply")
        fa = sum(1 for x in v if x == "fully_applies")
        hits = [r[arm]["hit"] for r in rows if r[arm]["hit"] is not None]
        return nr, fa, len(v), (sum(hits) / len(hits) if hits else float("nan"))

    print(f"\nscored cases: {len(rows)} | gating changed the top-{top_k} in "
          f"{sum(1 for r in rows if r['changed'])} / {len(rows)}\n")
    print("=== applicability (forced per-memory judge), UNGATED vs GATED ===")
    for arm in ("ungated", "gated"):
        nr, fa, tot, hr = rates(arm)
        print(f"  {arm:8s} verdicts={tot:3d}  does_not_apply={nr/tot:.0%}  "
              f"fully_applies={fa/tot:.0%}  vote_hit_rate={hr:.2f}")
    nu, _, tu, _ = rates("ungated")
    ng, _, tg, _ = rates("gated")
    print(f"\n  Δ not_relevant (gated − ungated) = {ng/tg - nu/tu:+.0%}")
    print("  gated << ungated → SOFT dimension-gating cuts the dominant retrieval waste → the v7")
    print("  retrieval-precision fix works. Δ≈0 → semantic gating doesn't help either (harder problem).")
    return {"n": len(rows)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", default="batch_results/v6ab_townsp.jsonl")
    ap.add_argument("--store", default="memory_stores/v6_1")
    ap.add_argument("--n", type=int, default=24)
    ap.add_argument("--workers", type=int, default=4)
    args = ap.parse_args()
    run(Path(args.batch), Path(args.store), args.n, workers=args.workers)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
