"""Thin CLI for the diagnosis case sampler (sampled human + pro-LLM review, rung ②).

Runs select -> cohort -> review-packet -> verdict-scaffold on REAL local sidecar data, $0. All logic
lives in ``evaluation.src.diagnosis.sampler`` (reusable/importable); this file only wires args → the
pipeline → files. The optional replay step is GUARDED and refuses to run without spend sign-off.

  poetry run python evaluation/src/cli_runner/diagnosis/case_sampler.py \
      --batch batch_results/ab_nh_town.jsonl --out evidence/.../sampler_smoke --n-outliers 8
  # add --replay to see it REFUSE (paid live-LLM regeneration; wired, not run)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from evaluation.src.diagnosis.sampler import (
    DETERMINISTIC_SIGNAL,
    append_verdict,
    cohort_strata,
    load_cases_and_index,
    render_packet,
    replay_case_stage,
    select_review_cases,
    verdict_for,
)

DEFAULT_QUESTION = (
    "Does this decision + its retrieval read right to a person — is the situation the right query, "
    "did retrieval surface applicable memory, and is the call defensible on this board?"
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--batch", type=Path, required=True, help="batch_results/<run>.jsonl (read-only)")
    ap.add_argument("--out", type=Path, required=True, help="output dir for packets + verdicts.jsonl")
    ap.add_argument("--outlier-source", default=DETERMINISTIC_SIGNAL,
                    help=f"outlier signal (default {DETERMINISTIC_SIGNAL!r}, deterministic $0). Any "
                    "other name is treated as an OPT-IN, UNCALIBRATED judge/metric key and needs "
                    "--judge-scores. An outcome signal (winner/won/...) is refused.")
    ap.add_argument("--judge-scores", type=Path, default=None,
                    help="JSONL/JSON map {observation_id: score} for the opt-in judge source")
    ap.add_argument("--n-outliers", type=int, default=12)
    ap.add_argument("--n-leverage", type=int, default=12,
                    help="top-K most-pivotal (nearest-parity swing) cases for the leverage channel")
    ap.add_argument("--cohort-per-bucket", type=int, default=1)
    ap.add_argument("--cohort-max", type=int, default=None)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--phases", nargs="*", default=None,
                    help="action phases for the stratified cohort (default day-only)")
    ap.add_argument("--emit-demo-verdict", action="store_true",
                    help="append ONE placeholder verdict (reviewer=model:demo, verdict=pending) to "
                    "exercise the record path — $0, no LLM; for smoke-testing the artifact")
    ap.add_argument("--replay", action="store_true",
                    help="GUARDED PAID STEP — regenerate a sampled decision via a live LLM. Wired but "
                    "OFF: this flag makes the run REFUSE, printing the sign-off requirement.")
    args = ap.parse_args()

    if args.replay:
        raise SystemExit(
            "REFUSED: --replay is a PAID live-LLM step (regenerates decisions through the production "
            "prompt) and is intentionally not auto-run. Building/selecting/rendering is $0. Get "
            "explicit spend sign-off, then call sampler.replay_case_stage(case, enabled=True)."
        )

    judge_scores = None
    if args.judge_scores:
        raw = args.judge_scores.read_text(encoding="utf-8").strip()
        if raw.startswith("{"):
            judge_scores = {k: float(v) for k, v in json.loads(raw).items()}
        else:  # JSONL rows: {"observation_id": ..., "score": ...}
            judge_scores = {}
            for line in raw.splitlines():
                line = line.strip()
                if line:
                    row = json.loads(line)
                    judge_scores[row["observation_id"]] = float(row["score"])

    cases, index, game_lengths = load_cases_and_index(args.batch)
    selected = select_review_cases(
        cases,
        index,
        game_lengths,
        outlier_source=args.outlier_source,
        judge_scores=judge_scores,
        n_outliers=args.n_outliers,
        n_leverage=args.n_leverage,
        cohort_per_bucket=args.cohort_per_bucket,
        cohort_max=args.cohort_max,
        seed=args.seed,
        action_phases=args.phases,
    )
    strata = cohort_strata(selected, game_lengths)

    args.out.mkdir(parents=True, exist_ok=True)
    packets_path = args.out / "review_packets.md"
    with packets_path.open("w", encoding="utf-8") as fh:
        fh.write(f"# Review packets — {args.batch.name}\n\n")
        fh.write(f"cohort strata: `{json.dumps(strata)}`\n\n")
        for sc in selected:
            roles = index.get(sc.case.trace_id, {}).get("roles", {}) or {}
            fh.write(render_packet(sc, roles, question=DEFAULT_QUESTION))
            fh.write("\n---\n\n")

    (args.out / "cohort_strata.json").write_text(json.dumps(strata, indent=2))

    verdicts_path = args.out / "verdicts.jsonl"
    verdicts_path.touch()  # durable artifact exists even before any review
    if args.emit_demo_verdict and selected:
        append_verdict(
            verdicts_path,
            verdict_for(
                selected[0],
                reviewer="model:demo",
                question=DEFAULT_QUESTION,
                verdict="pending",
                notes="placeholder emitted by --emit-demo-verdict to exercise the record path ($0).",
            ),
        )

    print(f"selected {len(selected)} cases from {args.batch.name}")
    print(f"strata: {json.dumps(strata)}")
    print(f"packets   -> {packets_path}")
    print(f"strata    -> {args.out / 'cohort_strata.json'}")
    print(f"verdicts  -> {verdicts_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
