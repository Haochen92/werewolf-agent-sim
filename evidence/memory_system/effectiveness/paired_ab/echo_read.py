"""Step-3 ECHO READ (free, local) — is myopic outcome-framing the active ingredient?

Decisive test for the wolf/SK day-leak: on decisions where a memory-on wolf DISSENTS
(votes off the day's eventual lynch — the behavior that gets wolves removed next day, see
the unconditioned-blending finding), does the wolf's private updated_strategy ECHO a
retrieved precedent — especially the success-framed dissent episodes (×137 vote-the-accuser,
×75 tie-force)? If dissents don't cite the retrieved approach, framing is NOT the lever and
the v5_0_nethorizon variant build is not worth doing (fall back to the night-only arm).

Pure local reads: arm sidecars (retrieved_observations + updated_strategy per decision)
joined to the batch records' day_resolutions (who the wolves voted vs the day's lynch), with
the same-game_id baseline tagged so we can flag the paired blended->dissented flips.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
BR = REPO / "batch_results"
EC = BR / "eval_cases"
HERE = Path(__file__).resolve().parent

WOLF_ARMS = {  # arm label -> (batch jsonl, sidecar dir)
    "arms_wolf": ("ab_arms_wolf.jsonl", "ab_arms_wolf_wolf_only"),
    "rr_wolf": ("ab_rr_wolf.jsonl", "ab_rr_wolf_wolf_only"),
}
BASELINE = ["ab_baseline.jsonl", "ab_baseline_recovered.jsonl"]


def load_jsonl(p):
    p = Path(p)
    return [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.exists() else []


def wolves_of(rec):
    return {p for p, r in rec["roles"].items() if r == "wolf"}


def baseline_blend_map():
    """(game_id, day) -> 'blend'/'dissent' for the baseline (memory-off) wolves."""
    m = {}
    for f in BASELINE:
        for rec in load_jsonl(BR / f):
            if rec.get("status") != "success":
                continue
            wolves = wolves_of(rec)
            for day in rec["day_resolutions"]:
                t = day.get("voted_player")
                if t is None:
                    continue
                votes = [v for v in day["votes"] if v["voter"] in wolves and v["voter"] != t]
                if not votes:
                    continue
                aligned = sum(v["votee"] == t for v in votes)
                m[(rec["game_id"], day["day"])] = "blend" if aligned > len(votes) / 2 else "dissent"
    return m


def sidecar_index(scdir, gid):
    """(day, voter) -> eval_case for wolf day_vote decisions in one game's sidecar."""
    idx = {}
    for x in load_jsonl(EC / scdir / f"{gid}.jsonl"):
        ec = x.get("output", {}).get("eval_case")
        if ec and ec.get("action_phase") == "day_vote" and ec.get("player_role") == "wolf":
            av = ec.get("agent_vote") or {}
            idx[(ec.get("day"), av.get("voter"))] = ec
    return idx


def collect():
    baseline = baseline_blend_map()
    out = []
    for arm, (bf, scdir) in WOLF_ARMS.items():
        for rec in load_jsonl(BR / bf):
            if rec.get("status") != "success":
                continue
            gid, wolves = rec["game_id"], wolves_of(rec)
            idx = sidecar_index(scdir, gid)
            for day in rec["day_resolutions"]:
                t = day.get("voted_player")
                if t is None:
                    continue
                for v in day["votes"]:
                    if v["voter"] not in wolves or v["voter"] == t or v["votee"] == t:
                        continue  # only DISSENT (off-pile) wolf votes
                    ec = idx.get((day["day"], v["voter"]))
                    if not ec or not ec.get("retrieved_observations"):
                        continue
                    out.append({
                        "arm": arm, "game_id": gid, "day": day["day"], "wolf": v["voter"],
                        "voted_for": v["votee"], "day_lynch": t,
                        "day_lynch_role": day.get("voted_player_role"),
                        "baseline_same_day": baseline.get((gid, day["day"]), "n/a"),
                        "situation": (ec.get("situations") or [None])[0],
                        "previous_strategy": (ec.get("private_context") or {}).get("previous_strategy"),
                        "updated_strategy": ec.get("updated_strategy"),
                        "retrieved": [
                            {"score": o.get("score"), "matched_situation": o.get("matched_situation"),
                             "approach": (o.get("observation") or {}).get("approach"),
                             "outcome": (o.get("observation") or {}).get("outcome")}
                            for o in ec.get("retrieved_observations", [])
                        ],
                    })
    return out


def main():
    recs = collect()
    (HERE / "echo_read_decisions.json").write_text(json.dumps(recs, indent=2))
    flips = [r for r in recs if r["baseline_same_day"] == "blend"]
    print(f"dissent wolf day_vote decisions w/ retrieval: {len(recs)}")
    print(f"  ...of which baseline (same game_id+day) BLENDED -> a paired flip: {len(flips)}")
    print(f"  ...wrote full detail to echo_read_decisions.json\n")
    for r in recs:
        print("=" * 90)
        print(f"[{r['arm']}] {r['game_id'][:8]} day{r['day']} wolf={r['wolf']} "
              f"voted_for={r['voted_for']} | day_lynch={r['day_lynch']}({r['day_lynch_role']}) "
              f"| baseline_same_day={r['baseline_same_day']}")
        for o in r["retrieved"]:
            print(f"  RET score={o['score']:.3f} approach: {str(o['approach'])[:170]}")
            print(f"             outcome : {str(o['outcome'])[:200]}")
        print(f"  UPDATED_STRATEGY: {str(r['updated_strategy'])[:500]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
