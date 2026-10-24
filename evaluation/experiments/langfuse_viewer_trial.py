"""Try Langfuse's dataset-run comparison on the Phase 3 turn replay, before building any viewer.

The ten frozen Phase 3 turns (evidence/game_play_enhancement/data/phase3_turn_replay/cases.jsonl,
the ``pinned`` and ``control`` slices) go up as a Langfuse dataset, and each of the bench's three
arms becomes one dataset run. Nothing is generated: the task hands back the five samples the bench
recorded on 2026-10-10 (``runs/phase3_turns/judged_<arm>.jsonl``), so the trial costs no model
calls and touches no game code. The scores are the recorded golden-judge verdicts plus code checks.

The question is the owner's, in the UI: can the three runs, side by side, carry the review the
README's table was made for? If yes, no custom viewer; if not, the reason names what one must show.

    poetry run python evaluation/experiments/langfuse_viewer_trial.py
    poetry run python evaluation/experiments/langfuse_viewer_trial.py --replace   # redo the runs
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.core.settings import load_project_env  # noqa: E402

load_project_env()

from langfuse import Evaluation, get_client  # noqa: E402

DATA = Path(__file__).resolve().parents[2] / "evidence/game_play_enhancement/data/phase3_turn_replay"
RUN = DATA / "runs/phase3_turns"
DATASET = "phase3_turn_replay"
EXPERIMENT = "Phase 3 turn replay"
SOURCE = "replayed from recorded output (bench run of 2026-10-10)"

# The README's names for the turns, so a row in the UI reads as the case it is.
SITUATIONS = {
    "83300b199a175ab3": "a sighting taken as support for an investigator claim",
    "cc56ed2046f3f402": "the same evidence (control)",
    "b862bd15a5b82193": '"a watch and a protection prove my results"',
    "1802f1e99ed17696": "an empty watch read as an empty house",
    "da55aa8b666d42e7": "an empty watch read as an empty house",
    "e4c192a2939d6751": "an empty trail read as no night ability",
    "282e2bd964a73304": "a necromancer using a body the night its owner died",
    "183500fda11b66d6": "the same timeline (control)",
    "804a99a855ecb1e2": "repeating the invented chanteuse claim",
    "2ae4571be87b642d": "accepting the invented claim about itself",
}


def load_cases() -> list[dict]:
    with open(DATA / "cases.jsonl") as f:
        return [c for c in map(json.loads, f) if c["case_id"] in SITUATIONS]


def load_samples(arm: str) -> dict[str, list[dict]]:
    by_case: dict[str, list[dict]] = {}
    with open(RUN / f"judged_{arm}.jsonl") as f:
        for row in map(json.loads, f):
            by_case.setdefault(row["case_id"], []).append(row)
    return {cid: sorted(rows, key=lambda r: r["sample"]) for cid, rows in by_case.items()}


def upload_dataset(lf, cases: list[dict]) -> None:
    """Item ids are fixed per case, so a second upload updates the items rather than adding more."""
    lf.create_dataset(
        name=DATASET,
        description="Ten Phase 3 discussion turns frozen from the ten-seat games: eight that went "
        "wrong in the hand-read games, two controls. Built by evaluation/experiments/phase3_turn_cases.py.",
    )
    for c in cases:
        lf.create_dataset_item(
            dataset_name=DATASET,
            id=f"phase3-turns-{c['case_id']}",
            input={
                "case": f"{c['game_id']} d{c['day']} {c['speaker']} ({c['role']})",
                "kind": c["kind"],
                "situation": SITUATIONS[c["case_id"]],
                "line_in_the_game": c["original"],
            },
            expected_output=c["golden"],
            metadata={
                "case_id": c["case_id"],
                "original_round": c["original_round"],
                "firing_reason": c["firing_reason"],
                "facts": c["facts"],
                "state": c["state"],
            },
        )


def _unit(row: dict, name: str) -> str | None:
    return next((u["text"] for u in row["units"] if u["unit"] == name), None)


def _message_broke(row: dict) -> bool:
    return any(u["unit"] == "message" and v != "golden_meets" for u, v in zip(row["units"], row["unit_verdicts"]))


def make_task(lf, samples: dict[str, list[dict]], model: str):
    """One generation per recorded sample, carrying its model and token usage, under the item's trace."""

    def task(*, item, **_):
        out = []
        for row in samples[item.metadata["case_id"]]:
            texts = {
                "message": _unit(row, "message") or "(passed)",
                "strategy": _unit(row, "updated_strategy"),
                "reads": _unit(row, "reads"),
                "vote": row["vote"],
            }
            u = row["usage"]
            with lf.start_as_current_observation(
                as_type="generation",
                name=f"sample {row['sample']}",
                model=model,
                output=texts,
                usage_details={"input": u["input"], "output": u["output"], "reasoning": u["reasoning"]},
                metadata={"source": SOURCE, "seconds": u["seconds"], "valid": row["valid"]},
            ):
                pass
            out.append({"sample": row["sample"], **texts})
        return {"note": SOURCE, "samples": out}

    return task


def make_evaluators(samples: dict[str, list[dict]]):
    def message_broke(*, metadata, **_):
        rows = samples[metadata["case_id"]]
        broke = [r for r in rows if _message_broke(r)]
        reasons = [
            f"sample {r['sample']}: {r['golden_reasons'][str(i)]}"
            for r in broke
            for i, (u, v) in enumerate(zip(r["units"], r["unit_verdicts"]))
            if u["unit"] == "message" and v != "golden_meets"
        ]
        return Evaluation(
            name="mistake rate: spoken line",
            value=len(broke) / len(rows),
            comment=f"{len(broke)}/{len(rows)} spoken messages broke the expectation (recorded golden judge)"
            + ("\n" + "\n".join(reasons) if reasons else ""),
        )

    def any_unit_broke(*, metadata, **_):
        rows = samples[metadata["case_id"]]
        k = sum(r["bad"] for r in rows)
        return Evaluation(
            name="mistake rate: anywhere (line, notes or reads)",
            value=k / len(rows),
            comment=f"{k}/{len(rows)} samples broke it in the message, strategy note or reads",
        )

    def spoke(*, metadata, **_):
        rows = samples[metadata["case_id"]]
        k = sum(_unit(r, "message") is not None for r in rows)
        return Evaluation(name="share of plays that spoke", value=k / len(rows), comment=f"{k}/{len(rows)} samples spoke (code check)")

    def output_tokens(*, metadata, **_):
        rows = samples[metadata["case_id"]]
        return Evaluation(
            name="output tokens (mean)",
            value=sum(r["usage"]["output"] for r in rows) / len(rows),
            comment="code check: recorded usage",
        )

    return [message_broke, any_unit_broke, spoke, output_tokens]


RUN_SCORE = {
    "positive": "mistake rate: failed turns (spoken line)",
    "control": "mistake rate: control turns (spoken line)",
}


def make_run_evaluators(samples: dict[str, list[dict]]):
    """The README table's two bottom rows, as run-level scores."""

    def by_kind(*, item_results, **_):
        evals = []
        for kind in ("positive", "control"):
            rows = [
                r for res in item_results if res.item.input["kind"] == kind
                for r in samples[res.item.metadata["case_id"]]
            ]
            k = sum(map(_message_broke, rows))
            evals.append(Evaluation(name=RUN_SCORE[kind], value=k / len(rows), comment=f"{k}/{len(rows)}"))
        return evals

    return [by_kind]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--replace", action="store_true", help="delete and redo runs that already exist")
    args = ap.parse_args()

    lf = get_client()
    config = json.loads((RUN / "summary.json").read_text())["config"]
    upload_dataset(lf, load_cases())
    dataset = lf.get_dataset(DATASET)
    existing = {r.name for r in lf.get_dataset_runs(dataset_name=DATASET).data}

    for arm in config["arms"]:
        name = arm["label"]
        if name in existing:
            if not args.replace:
                print(f"{name}: run exists, skipped (--replace to redo)")
                continue
            lf.delete_dataset_run(dataset_name=DATASET, run_name=name)
        samples = load_samples(name)
        result = dataset.run_experiment(
            name=EXPERIMENT,
            run_name=name,
            description=f"{arm['model']}, {SOURCE}",
            task=make_task(lf, samples, arm["model"]),
            evaluators=make_evaluators(samples),
            run_evaluators=make_run_evaluators(samples),
            max_concurrency=5,
            metadata={"model": arm["model"], "source": SOURCE, "memory": arm["memory"]},
        )
        run_scores = {e.name: e.comment for e in result.run_evaluations}
        print(f"{name}: {len(result.item_results)} items, {run_scores}")
    lf.flush()


if __name__ == "__main__":
    main()
