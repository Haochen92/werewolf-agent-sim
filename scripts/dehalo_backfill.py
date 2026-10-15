"""Run the de-halo pass on saved games where it did not run, and fix their stored verdicts.

For each game's eval-case file without a de-halo record: re-run the pass on the extraction case's
observations (the verdicts as extracted), rewrite the matching observations' verdicts in the dump
store (matched by game and approach; ones dedup dropped are skipped), and append the de-halo record
to the file, marked as backfilled. One-off ops for the v8 seeding (2026-10-11), where the call's
16k token cap cut off long games (fixed in efa232de).

    poetry run python scripts/dehalo_backfill.py <store_dir> <eval_cases.jsonl> [...]
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

from dotenv import load_dotenv

load_dotenv(".env")

from Agents.memory.extraction.dehalo import dehalo_observations  # noqa: E402
from Agents.memory.extraction.inputs import extraction_inputs_from_frozen_case  # noqa: E402
from Agents.memory.persistence.config import DehaloConfig  # noqa: E402


def _fix_store(store_dir: Path, game_id: str, judgments: list[dict]) -> int:
    path = store_dir / "observations.json"
    store = json.loads(path.read_text())
    revised = {(j["perspective"], j["approach"]): j["revised_verdict"] for j in judgments
               if j["revised_verdict"] != j["original_verdict"]}
    fixed = 0
    for ns, records in store["namespaces"].items():
        role = ns.split("/")[1]
        for r in records:
            v = r["value"]
            verdict = revised.get((role, v.get("approach")))
            if v.get("game_id") == game_id and verdict is not None:
                v["net_verdict"] = verdict
                v.setdefault("dimensions", {})["net_verdict"] = verdict
                fixed += 1
    path.write_text(json.dumps(store, indent=2))
    return fixed


def backfill(store_dir: Path, cases_path: Path) -> None:
    records = [json.loads(line) for line in cases_path.open()]
    if any(r["kind"] == "dehalo" for r in records):
        print(cases_path.name, "already de-haloed")
        return
    case = next(r["output"]["extraction_case"] for r in records if r["kind"] == "postgame_extraction")
    observations = [SimpleNamespace(**o) for o in case["observations"]]
    record = dehalo_observations(observations, extraction_inputs_from_frozen_case(case), DehaloConfig())
    if record is None:
        print(cases_path.name, "de-halo did not run")
        return
    record["backfilled"] = True
    fixed = _fix_store(store_dir, case["game_id"], record["judgments"])
    with cases_path.open("a") as f:
        f.write(json.dumps({"kind": "dehalo", "id": "", "name": f"dehalo_{case['game_id']}", "trace_id": "",
                            "parent_observation_id": None, "metadata": {"backfilled": True}, "input": None,
                            "output": {"dehalo": record}}) + "\n")
    print(cases_path.name, f"{record['revised']} of {len(observations)} verdicts revised, "
          f"{fixed} stored records fixed, usage {record['usage']}")


if __name__ == "__main__":
    for p in sys.argv[2:]:
        backfill(Path(sys.argv[1]), Path(p))
