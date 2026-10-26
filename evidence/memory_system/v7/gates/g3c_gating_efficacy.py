# ── FROZEN RECORD (stamped 2026-07-05) ──────────────────────────
# Dated evidence artifact, NOT maintained code. It answered its question once
# (verdict: ../README.md); it is kept runnable-as-of last touch (ccd9a8d) but is
# not import-safe against future refactors. Standing apparatus lives in
# evaluation/src/instrument_validation/.
# ────────────────────────────────────────────────────────────────────────────
"""v7 — gating efficacy (the G3c follow-on). Zero spend, no LLM, no re-retrieval.

G3c proved embedding similarity is BLIND to applicability (not_relevant 58%, score can't cut it). The
proposed fix is STRUCTURED dimension-gating. This tests — cheaply — whether a gate dimension actually
SEPARATES applicable from not_relevant, i.e. whether gating would reduce the waste.

⚠ DESIGN (user constraint): we will NOT hard-gate on every dimension. So this measures the MARGINAL
value of each gate dim INDIVIDUALLY (matched vs mismatched not_relevant rate), to learn WHICH dims are
worth (soft) gating on — not an all-dim conjunction.

Cheap-testable gate = CRITICALITY (board-deterministic): query criticality reconstructed from the board
at the decision (`query_criticality`), compared to each retrieved SP's STORED criticality (its
`dimensions`). The semantic gates (exposure_class / info_landscape_class) need the QUERY enum, which is
LLM-extracted and not persisted → re-deriving it is paid → deferred.

Reads: for each retrieved SP (verdict joined by strategy_index → retrieved order), is its criticality
regime matched to the query's, and is it not_relevant? Lower not_relevant when matched ⇒ the criticality
gate carries applicability signal that similarity does not.
"""

import glob
import json
import sys

sys.path.insert(0, "evaluation/src")
sys.path.insert(0, ".")
from evaluation.src.studies.criticality_screen import query_criticality  # noqa: E402

SESSIONS = {
    "v6ab_townsp_town_only": "batch_results/v6ab_townsp.jsonl",
    "v6ab_sksp_serial_killer_only": "batch_results/v6ab_sksp.jsonl",
    "v6ab_skboth_serial_killer_only": "batch_results/v6ab_skboth.jsonl",
}


def alive_bucket(n):
    return "early" if n >= 8 else "mid" if n >= 5 else "late"


def batch_index(path):
    return {g["game_id"]: g for g in (json.loads(l) for l in open(path) if l.strip())}


def eval_cases(path):
    for line in open(path):
        if not line.strip():
            continue
        o = json.loads(line).get("output") or {}
        e = o.get("eval_case") if isinstance(o, dict) else None
        if e:
            yield e


def alive_entering_day(g, day):
    """Players alive entering `day` = all minus lynches on days <day minus night deaths on nights <day."""
    dead = set()
    for d in g["day_resolutions"]:
        if d.get("day", 0) < day and d.get("voted_player"):
            dead.add(d["voted_player"])
    for n in g["night_resolutions"]:
        if n.get("day", 0) < day:
            dead.update(n.get("deaths") or [])
    return [p for p in g["roles"] if p not in dead]


def main():
    # per gate dim: {matched: [nr_count, total], mismatched: [...]}
    dims = {"alive_bucket": {"m": [0, 0], "x": [0, 0]},
            "is_swing": {"m": [0, 0], "x": [0, 0]},
            "dist_parity": {"m": [0, 0], "x": [0, 0]}}
    overall = [0, 0]

    for session, batch_path in SESSIONS.items():
        idx = batch_index(batch_path)
        for f in glob.glob(f"batch_results/eval_cases/{session}/*.jsonl"):
            gid = f.split("/")[-1].replace(".jsonl", "")
            g = idx.get(gid)
            if not g:
                continue
            roles = g["roles"]
            for e in eval_cases(f):
                verds = e.get("strategy_verdicts") or []
                rsp = e.get("retrieved_strategy_points") or []
                if not verds or not rsp:
                    continue
                day = e.get("day", 0)
                alive = alive_entering_day(g, day)
                if len(alive) < 2:
                    continue
                q_alive, q_dist, q_swing = query_criticality(alive, roles)
                for v in verds:
                    idx_sp = v.get("strategy_index")
                    if not isinstance(idx_sp, int) or not (1 <= idx_sp <= len(rsp)):
                        continue
                    sp = (rsp[idx_sp - 1].get("strategy_point") or {})
                    d = sp.get("dimensions") or {}
                    if d.get("players_alive") is None:
                        continue
                    isnr = int(v.get("verdict") == "not_relevant")
                    overall[0] += isnr
                    overall[1] += 1
                    checks = {
                        "alive_bucket": alive_bucket(q_alive) == alive_bucket(d["players_alive"]),
                        "is_swing": bool(q_swing) == bool(d.get("is_swing")),
                        "dist_parity": (d.get("distance_to_parity") is not None
                                        and abs(q_dist - d["distance_to_parity"]) <= 1),
                    }
                    for name, matched in checks.items():
                        cell = dims[name]["m" if matched else "x"]
                        cell[0] += isnr
                        cell[1] += 1

    print(f"joined SP retrievals with reconstructable board: {overall[1]} | "
          f"overall not_relevant {overall[0]/max(1,overall[1]):.0%}\n")
    print("=== MARGINAL value of each criticality gate dim (not_relevant rate: matched vs mismatched) ===")
    print("  (lower not_relevant when MATCHED ⇒ the gate carries applicability signal)\n")
    for name, cells in dims.items():
        m, x = cells["m"], cells["x"]
        mr = m[0] / m[1] if m[1] else float("nan")
        xr = x[0] / x[1] if x[1] else float("nan")
        delta = mr - xr
        verdict = "helps" if delta < -0.03 else ("hurts" if delta > 0.03 else "flat")
        print(f"  {name:12s} matched nr={m[0]:4d}/{m[1]:4d}={mr:.0%}   "
              f"mismatched nr={x[0]:4d}/{x[1]:4d}={xr:.0%}   Δ={delta:+.0%}  [{verdict}]")

    print("\n=== read ===")
    print("  a dim that 'helps' (matched << mismatched not_relevant) is worth (soft) gating on.")
    print("  all 'flat' ⇒ criticality gate alone doesn't cut the waste → the lever is the semantic")
    print("  gates (exposure/info_landscape), which need the query enum (paid) — that's the next test.")


if __name__ == "__main__":
    main()
