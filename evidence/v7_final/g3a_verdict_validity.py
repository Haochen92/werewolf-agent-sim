"""v7 Gate G3a — verdict-validity (plan §5-G3, §10b). Zero spend, on the v6ab eval-case dumps.

The consolidation loop wants to DECAY overridden memories and PROMOTE followed-and-good ones. That is
only valid if the follow/override verdict carries real signal about memory quality. Two reads:

  §10b APPLICABILITY FUNNEL — the per-SP verdict distribution. not_relevant is a RETRIEVAL failure
    (don't blame the lesson); follow/override are the content verdicts. Confirms the ~50% not-relevant
    waste and how often applicable advice is actually overridden.

  VERDICT VALIDITY — does OVERRIDE beat FOLLOW on decision quality, at matched boards? If the agent
    overrides exactly the bad advice, override-decisions outperform follow-decisions → the verdict
    tracks memory quality → decay-on-override is real. The confound: the agent overrides more on
    easy/info-rich boards, so we control for board (day stratum). Channel = TOWN day-vote (clean
    ground-truthed proxy: hit a wolf/SK). Abstains are reported separately (following the cautious SP
    often → abstain, itself a signal).
"""

import glob
import json
import sys

sys.path.insert(0, "evaluation/src")
sys.path.insert(0, ".")
from core.stats import compare_proportions  # noqa: E402

from evaluation.src.components.decision_scoring import score_vote  # noqa: E402

# town SP arm = the verdict-rich town channel; pool the town obs arm too (a few SP verdicts there).
TOWN_SESSIONS = {
    "v6ab_townsp_town_only": "batch_results/v6ab_townsp.jsonl",
    "v6ab_townobs_town_only": "batch_results/v6ab_townobs.jsonl",
}
TOWN_ROLES = {"villager", "healer", "investigator", "vigilante"}


def batch_index(path):
    idx = {}
    for line in open(path):
        if line.strip():
            g = json.loads(line)
            idx[g["game_id"]] = g
    return idx


def eval_cases(path):
    for line in open(path):
        if not line.strip():
            continue
        o = json.loads(line).get("output") or {}
        e = o.get("eval_case") if isinstance(o, dict) else None
        if e:
            yield e


def main():
    funnel = {"follow": 0, "override": 0, "not_relevant": 0}
    # decision rows: (stance, hit_threat|None, is_abstain, day)
    rows = []

    for session, batch_path in TOWN_SESSIONS.items():
        idx = batch_index(batch_path)
        for f in glob.glob(f"batch_results/eval_cases/{session}/*.jsonl"):
            gid = f.split("/")[-1].replace(".jsonl", "")
            g = idx.get(gid)
            if not g:
                continue
            roles = g["roles"]
            for e in eval_cases(f):
                if e.get("action_phase") != "day_vote":
                    continue
                verds = e.get("strategy_verdicts") or []
                for v in verds:
                    funnel[v.get("verdict", "not_relevant")] = funnel.get(v.get("verdict"), 0) + 1
                applicable = [v["verdict"] for v in verds if v.get("verdict") in ("follow", "override")]
                if not applicable:
                    continue
                if all(a == "follow" for a in applicable):
                    stance = "follow"
                elif all(a == "override" for a in applicable):
                    stance = "override"
                else:
                    stance = "mixed"
                av = e.get("agent_vote") or {}
                ov = score_vote(av.get("votee"), roles)
                rows.append((stance, None if ov.is_abstain else int(ov.hit_threat),
                             ov.is_abstain, e.get("day", 0)))

    total_v = sum(funnel.values())
    print("=== §10b APPLICABILITY FUNNEL (per-SP verdicts, town day-vote+others) ===")
    for k in ("follow", "override", "not_relevant"):
        print(f"  {k:13s} {funnel[k]:4d}  ({funnel[k]/max(1,total_v):.0%})")
    print(f"  total verdicts: {total_v}")

    def slice_stats(stance, day_lo=0, day_hi=99):
        sel = [r for r in rows if r[0] == stance and day_lo <= r[3] <= day_hi]
        n = len(sel)
        nab = sum(1 for r in sel if r[2])
        nonab = [r[1] for r in sel if not r[2]]
        hit = sum(nonab)
        return n, nab, len(nonab), hit

    print("\n=== decision stance distribution (town day-votes with applicable verdicts) ===")
    for st in ("follow", "override", "mixed"):
        n, nab, nnon, hit = slice_stats(st)
        ab_rate = nab / n if n else 0
        ht = hit / nnon if nnon else 0
        print(f"  {st:9s} n={n:3d} | abstain={ab_rate:.0%} | hit_threat(non-abstain)={hit}/{nnon}={ht:.2f}")

    print("\n=== VERDICT VALIDITY: override vs follow hit_threat (non-abstain), by board (day) ===")
    for lo, hi, label in ((1, 2, "early d1-2"), (3, 4, "mid d3-4"), (5, 99, "late d5+"), (1, 99, "ALL")):
        nf, _, nnf, hf = slice_stats("follow", lo, hi)
        no, _, nno, ho = slice_stats("override", lo, hi)
        line = f"  {label:11s} follow {hf}/{nnf}" + (f"={hf/nnf:.2f}" if nnf else "=—")
        line += f"  override {ho}/{nno}" + (f"={ho/nno:.2f}" if nno else "=—")
        if nnf >= 5 and nno >= 5:
            cmp = compare_proportions(ho, nno, hf, nnf)
            line += f"  Δ={ho/nno - hf/nnf:+.2f} p={cmp.fisher_p:.3f}"
        print(line)

    print("\n=== interpretation ===")
    print("  override>follow at matched boards → override rejects bad advice → decay-on-override valid.")
    print("  override≈follow → verdict uninformative for content credit (decay signal weak).")


if __name__ == "__main__":
    main()
