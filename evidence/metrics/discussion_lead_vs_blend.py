"""Phase 1 / Gate A prototype: wolf day-offense as LEAD-vs-BLEND from the discussion layer.

The existing wolf_steering_rate is VOTE-level (on a town-mislynch day, did the majority of
wolves vote the lynched town player?). It conflates two very different things: a wolf who
*started* the pile-on (lead = active offense) and a wolf who *joined* an already-forming
bandwagon (blend = camouflage). This prototype separates them using the discussion layer
(day_channel.addressed_targets, stance=accusation, ordered by seq):

  on each town-mislynch day, among everyone who accused the lynched target, was the wolf
  EARLY in that accusation sequence (lead) or LATE (blend)?

Gate A (go/no-go for the discourse layer, no new infra, no LLM spend):
  (a) does lead-vs-blend decorrelate from unconditioned blending (i.e. is it a distinct signal)?
  (b) does it beat wolf_steering_rate's win-correlation (+0.17, n.s.)?

Reads the v6ab batch (180 games) we already have. Deterministic; recompute-only.
"""

import glob
import json
import sys

sys.path.insert(0, "evaluation/src")
from core.stats import point_biserial  # noqa: E402

TOWN_ROLES = {"villager", "healer", "investigator", "vigilante"}

ARMS = sorted(glob.glob("batch_results/v6ab_*.jsonl"))


def load_games() -> list[dict]:
    games = []
    for f in ARMS:
        for line in open(f):
            line = line.strip()
            if line:
                games.append(json.loads(line))
    return games


def first_accusations(day_channel: list[dict], day: int, target: str) -> list[str]:
    """Distinct accusers of `target` on `day`, ordered by their FIRST accusation seq."""
    first_seq: dict[str, int] = {}
    for e in day_channel:
        if e.get("day") != day:
            continue
        speaker = e.get("player")
        seq = e.get("seq")
        if speaker is None or seq is None:
            continue
        for a in e.get("addressed_targets") or []:
            if a.get("stance") == "accusation" and a.get("target") == target:
                if speaker not in first_seq or seq < first_seq[speaker]:
                    first_seq[speaker] = seq
    return [s for s, _ in sorted(first_seq.items(), key=lambda kv: kv[1])]


def game_signals(g: dict) -> dict | None:
    roles = g["roles"]
    wolves = {p for p, r in roles.items() if r == "wolf"}
    if not wolves:
        return None
    winner = (g.get("computed_metrics") or {}).get("winner") or g.get("winner")
    wolf_won = 1 if winner == "wolves" else 0
    dc = g["day_channel"]

    lead_scores: list[float] = []          # per (wolf, mislynch-target) accusation instance
    lead_binary: list[int] = []            # 1 = earlier half of accusers, 0 = later half
    # re-derive the existing vote-level steering + unconditioned blending for the SAME games
    mislynch_days_total = mislynch_days_steered = 0
    blend_aligned = blend_total = 0

    for d in g["day_resolutions"]:
        vp = d.get("voted_player")
        if vp is None:
            continue
        wolf_votes = [v for v in d["votes"] if roles.get(v["voter"]) == "wolf"]
        # unconditioned blending: each living wolf's vote aligns with the lynch (excl. self)
        for v in wolf_votes:
            if v["voter"] == vp:
                continue
            blend_total += 1
            if v["votee"] == vp:
                blend_aligned += 1

        if d.get("voted_player_role") not in TOWN_ROLES:
            continue  # lead-vs-blend defined on TOWN mislynch days only (matches steering)
        mislynch_days_total += 1
        if wolf_votes:
            aligned = sum(1 for v in wolf_votes if v["votee"] == vp)
            if aligned > len(wolf_votes) / 2:
                mislynch_days_steered += 1

        accusers = first_accusations(dc, d["day"], vp)
        n = len(accusers)
        if n == 0:
            continue
        for w in wolves:
            if w not in accusers:
                continue
            rank = accusers.index(w)  # 0-based; 0 = first accuser
            score = 1.0 if n == 1 else 1.0 - rank / (n - 1)
            lead_scores.append(score)
            lead_binary.append(1 if rank < n / 2 else 0)

    return {
        "game_id": g["game_id"],
        "wolf_won": wolf_won,
        "wolf_lead_score": sum(lead_scores) / len(lead_scores) if lead_scores else None,
        "wolf_lead_binary": sum(lead_binary) / len(lead_binary) if lead_binary else None,
        "n_lead_instances": len(lead_scores),
        "wolf_steering_rate": (mislynch_days_steered / mislynch_days_total) if mislynch_days_total else None,
        "wolf_blend_rate": (blend_aligned / blend_total) if blend_total else None,
    }


def corr(rows: list[dict], metric: str, against: str = "wolf_won"):
    pairs = [(r[against], r[metric]) for r in rows if r[metric] is not None]
    if len(pairs) < 5:
        return None
    binary = [p[0] for p in pairs]
    vals = [p[1] for p in pairs]
    r, p = point_biserial(binary, vals)
    return r, p, len(pairs)


def main():
    games = load_games()
    rows = [s for g in games if (s := game_signals(g)) is not None]
    print(f"games loaded: {len(games)} | with wolves: {len(rows)}")
    print(f"games with >=1 wolf accusation on a mislynch day: "
          f"{sum(1 for r in rows if r['wolf_lead_score'] is not None)}")
    print(f"total lead instances: {sum(r['n_lead_instances'] for r in rows)}")
    print()

    print("=== win-correlation (point-biserial vs wolf_won) ===")
    for m in ["wolf_steering_rate", "wolf_blend_rate", "wolf_lead_score", "wolf_lead_binary"]:
        c = corr(rows, m)
        if c:
            r, p, n = c
            print(f"  {m:22s} r={r:+.3f} p={p:.4f} n={n}")
        else:
            print(f"  {m:22s} insufficient n")

    print()
    print("=== decorrelation: lead_score vs the two existing wolf metrics ===")
    for other in ["wolf_steering_rate", "wolf_blend_rate"]:
        pairs = [(r["wolf_lead_score"], r[other]) for r in rows
                 if r["wolf_lead_score"] is not None and r[other] is not None]
        if len(pairs) >= 5:
            # pearson via point_biserial trick won't work (not binary); quick manual pearson
            xs = [p[0] for p in pairs]
            ys = [p[1] for p in pairs]
            mx = sum(xs) / len(xs)
            my = sum(ys) / len(ys)
            cov = sum((x - mx) * (y - my) for x, y in pairs)
            sx = sum((x - mx) ** 2 for x in xs) ** 0.5
            sy = sum((y - my) ** 2 for y in ys) ** 0.5
            r = cov / (sx * sy) if sx and sy else float("nan")
            print(f"  lead_score ~ {other:22s} pearson={r:+.3f} n={len(pairs)}")


if __name__ == "__main__":
    main()
