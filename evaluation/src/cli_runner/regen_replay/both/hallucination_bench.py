"""eval-hallucination-bench: replay frozen hallucination cases under arms (model × prompt version),
judge every output, and compare the arms.

Each arm runs in its own process, because the prompt version is chosen by env flags read at import
(``WW_DISCUSSION_PROMPT``, ``WW_INVESTIGATOR_PROMPT``) and the seat model by ``GOOGLE_GENAI_MODEL``.
A worker regenerates every case ``n`` times (``replay/hallucination_bench.py``) and writes its
samples; the parent then judges them all the same way:

- fact-sheet cascade (cases without a golden): every unit is screened for the checkable facts it
  touches (``audits/role_hallucination_screen.anchors_for_text``); anchored units are read by the
  cheap census reader, and its positives re-read by the stronger one (``judges/role_fact_read``).
  A unit is bad on a ``hallucination`` verdict. ``deliberate_deception`` (misstating one's own
  private knowledge) is counted separately, as the census did.
- golden (cases with a hand-written expectation): ``judges/golden_expectation``; bad on ``violates``.

A sample is bad if any of its units is. Per arm: bad rate over all samples, over positives and over
controls, and per phase / role. Every later arm is compared with the first, case by case: a sign
test over the cases whose bad rate differs between the two.

  poetry run eval-hallucination-bench --config evaluation/config/template/hallucination_bench_example.json
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from math import comb
from pathlib import Path

from evaluation.src.core.settings import REPO_ROOT

DEFAULT_RECALL_MODEL = "gemini-3.1-flash-lite"
DEFAULT_PRECISION_MODEL = "gemini-3.5-flash"


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


# --- worker: one arm, one process ------------------------------------------------

def run_worker(dataset: Path, out: Path, n: int, memory: str, workers: int, limit: int | None) -> None:
    from evaluation.src.replay.hallucination_bench import generate

    cases = _read_jsonl(dataset)[:limit] if limit else _read_jsonl(dataset)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        results = list(ex.map(lambda c: (c, generate(c, n, memory)), cases))
    with open(out, "w") as f:
        for case, samples in results:
            for s in samples:
                f.write(json.dumps({"case_id": case["case_id"], **s}) + "\n")


def spawn_arm(arm: dict, cfg: dict, out: Path) -> None:
    env = {**os.environ, **{k: str(v) for k, v in (arm.get("env") or {}).items()}}
    env["GOOGLE_GENAI_MODEL"] = arm["model"]
    cmd = [sys.executable, "-m", "evaluation.src.cli_runner.regen_replay.both.hallucination_bench",
           "--worker", "--dataset", cfg["dataset"], "--out", str(out),
           "--n", str(cfg.get("n", 3)), "--memory", arm.get("memory", "captured"),
           "--workers", str(cfg.get("workers", 8))]
    if cfg.get("limit"):
        cmd += ["--limit", str(cfg["limit"])]
    subprocess.run(cmd, cwd=REPO_ROOT, env=env, check=True)


# --- judging ------------------------------------------------------------------

def judge_samples(samples: list[dict], cases: dict[str, dict], cfg: dict) -> None:
    """Mark every sample with its unit verdicts and ``bad`` (in place)."""
    from evaluation.src.audits.role_hallucination_screen import (
        anchors_for_text, claims_through, death_timeline,
    )
    from evaluation.src.judges.golden_expectation import DEFAULT_GOLDEN_JUDGE_MODEL, judge_golden
    from evaluation.src.judges.role_fact_read import read_candidates

    records = {(cid, "bench"): c["facts"] for cid, c in cases.items()}
    cands, golden_jobs = [], []
    for i, s in enumerate(samples):
        case = cases[s["case_id"]]
        s["unit_verdicts"] = ["no_anchor"] * len(s["units"])
        for j, u in enumerate(s["units"]):
            if case["golden"]:
                golden_jobs.append((i, j, case["golden"], u))
                continue
            facts = case["facts"]
            anchors = anchors_for_text(u["text"], roles=facts["roles"], dead_from=death_timeline(facts),
                                       day=case["day"], speaker=case["speaker"],
                                       claims=claims_through(facts, case["day"]))
            if anchors:
                cands.append({"game_id": s["case_id"], "arm": "bench", "day": case["day"], "seq": None,
                              "phase": case["phase"], "speaker": case["speaker"],
                              "speaker_role": case["role"], "unit": u["unit"], "text": u["text"],
                              "anchors": anchors, "_i": i, "_j": j})
    print(f"  judging: {len(cands)} anchored units (fact sheet), {len(golden_jobs)} units (golden)")
    if cands:
        lite = read_candidates(cands, records, cfg.get("recall_model", DEFAULT_RECALL_MODEL))
        for c in lite:
            samples[c["_i"]]["unit_verdicts"][c["_j"]] = (c.get("read") or {}).get("verdict", "read_error")
        pos = [c for c in lite if (c.get("read") or {}).get("verdict") in ("hallucination", "deliberate_deception")]
        if pos:
            for c in read_candidates(pos, records, cfg.get("precision_model", DEFAULT_PRECISION_MODEL)):
                samples[c["_i"]]["unit_verdicts"][c["_j"]] = (c.get("read") or {}).get("verdict", "read_error")
    if golden_jobs:
        model = cfg.get("golden_model", DEFAULT_GOLDEN_JUDGE_MODEL)
        with ThreadPoolExecutor(max_workers=8) as ex:
            verdicts = list(ex.map(lambda job: judge_golden(job[2], job[3]["unit"], job[3]["text"], model),
                                   golden_jobs))
        for (i, j, _, _), v in zip(golden_jobs, verdicts):
            samples[i]["unit_verdicts"][j] = "golden_" + v.verdict
            samples[i].setdefault("golden_reasons", {})[j] = v.reason
    for s in samples:
        s["bad"] = any(v in ("hallucination", "golden_violates") for v in s["unit_verdicts"])
        s["deception"] = "deliberate_deception" in s["unit_verdicts"]


# --- summary --------------------------------------------------------------------

def _rate(rows: list[dict]) -> str:
    valid = [r for r in rows if r["valid"]]
    bad = sum(r["bad"] for r in valid)
    return f"{bad}/{len(valid)} ({bad / len(valid):.0%})" if valid else "0/0"


def summarize(by_arm: dict[str, list[dict]], cases: dict[str, dict]) -> dict:
    summary: dict = {"arms": {}, "paired_vs_first": {}}
    case_rate: dict[str, dict[str, float]] = {}
    for label, rows in by_arm.items():
        groups: dict[str, list[dict]] = defaultdict(list)
        per_case: dict[str, list[bool]] = defaultdict(list)
        for r in rows:
            c = cases[r["case_id"]]
            for g in ("all", c["kind"], f"phase:{c['phase']}", f"role:{c['role']}", f"source:{c['source']}"):
                groups[g].append(r)
            if r["valid"]:
                per_case[r["case_id"]].append(r["bad"])
        summary["arms"][label] = {
            "bad": {g: _rate(rs) for g, rs in sorted(groups.items())},
            "deception": sum(r.get("deception", False) for r in rows),
            "invalid": sum(not r["valid"] for r in rows),
        }
        case_rate[label] = {cid: sum(v) / len(v) for cid, v in per_case.items()}
    labels = list(by_arm)
    for label in labels[1:]:
        base, other = case_rate[labels[0]], case_rate[label]
        shared = set(base) & set(other)
        better = sum(other[c] < base[c] for c in shared)  # fewer bad samples than the first arm
        worse = sum(other[c] > base[c] for c in shared)
        k, m = min(better, worse), better + worse
        p = min(1.0, 2 * sum(comb(m, i) for i in range(k + 1)) / 2 ** m) if m else 1.0
        summary["paired_vs_first"][label] = {"cases": len(shared), "better": better, "worse": worse,
                                            "two_sided_sign_p": round(p, 4)}
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config")
    ap.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--dataset"), ap.add_argument("--out")
    ap.add_argument("--n", type=int, default=3), ap.add_argument("--memory", default="captured")
    ap.add_argument("--workers", type=int, default=8), ap.add_argument("--limit", type=int)
    args = ap.parse_args()
    if args.worker:
        run_worker(REPO_ROOT / args.dataset, Path(args.out), args.n, args.memory, args.workers, args.limit)
        return

    cfg = json.loads(Path(args.config).read_text())
    out_dir = REPO_ROOT / cfg.get("output_dir", "evaluation/eval_results/hallucination_bench") / cfg["label"]
    out_dir.mkdir(parents=True, exist_ok=True)
    cases = {c["case_id"]: c for c in _read_jsonl(REPO_ROOT / cfg["dataset"])}

    by_arm: dict[str, list[dict]] = {}
    for arm in cfg["arms"]:
        gen_path = out_dir / f"generations_{arm['label']}.jsonl"
        if not gen_path.exists():  # a rerun reuses an arm's generations; delete the file to redo it
            print(f"arm {arm['label']}: generating ({arm['model']}, env {arm.get('env') or {}})")
            spawn_arm(arm, cfg, gen_path)
        by_arm[arm["label"]] = _read_jsonl(gen_path)

    for label, samples in by_arm.items():
        print(f"arm {label}:")
        judge_samples(samples, cases, cfg)
        with open(out_dir / f"judged_{label}.jsonl", "w") as f:
            f.writelines(json.dumps(s) + "\n" for s in samples)

    result = {"label": cfg["label"], "run_at": datetime.now(timezone.utc).isoformat(), "config": cfg,
              "n_cases": len(cases), **summarize(by_arm, cases)}
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ("arms", "paired_vs_first")}, indent=2))


if __name__ == "__main__":
    main()
