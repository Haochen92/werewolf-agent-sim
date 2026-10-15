"""Tag already-extracted observations with the decision each describes (decisions §13; plan §9.6 item 11).

One Claude request per game (a Message Batch; a request that fails is retried directly), over the
offline job's ``extracted.jsonl`` files. Writes ``decisions.jsonl`` next to each (one row per
observation: its tag, the tag's status against the decisions the saved input records, the day its
own text states) and prints the free checks: how many tags match a recorded decision, and how often a
tag agrees with the day the observation's own text states.

  poetry run python scripts/tag_observation_decisions.py \\
      --extracted batch_results/extraction_runs/flash_seed_gate_2026-10-12/extracted.jsonl \\
                  batch_results/extraction_runs/sonnet_rest_2026-10-12/extracted.jsonl
"""

from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path


def checks(rows: list[dict]) -> dict:
    """Tag status counts, and agreement with the day the observation's text states, by phase."""
    out: dict = {"status": dict(collections.Counter(r["status"] for r in rows))}
    for phase in ("night_action", "day_vote", "day_discussion"):
        stated = [r for r in rows if r["action_phase"] == phase and r["stated_day"] is not None
                  and r["decision_day"] is not None]
        agree = sum(r["decision_day"] == r["stated_day"] for r in stated)
        out[phase] = {"with_stated_day": len(stated), "agree": agree,
                      "agree_rate": round(agree / len(stated), 3) if stated else None}
    return out


def main() -> None:
    from dotenv import load_dotenv

    load_dotenv()
    from Agents.llm_factory.providers.anthropic import batch_parse, parse_with_claude, usage_cost_usd
    from Agents.memory.extraction.decision_tags import tag_prompt, tag_rows
    from Agents.schemas.decision_tags import DecisionTags

    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--extracted", nargs="+", required=True)
    ap.add_argument("--model", default="claude-haiku-5-5")
    ap.add_argument("--thinking", default=None)
    ap.add_argument("--dry-run", action="store_true", help="build the prompts and stop")
    args = ap.parse_args()

    runs = {path: [json.loads(line)["output"]["extraction_case"] for line in Path(path).read_text().splitlines()]
            for path in args.extracted}
    requests = {f"r{i}_g{j}": (tag_prompt(case), DecisionTags)
                for i, cases in enumerate(runs.values()) for j, case in enumerate(cases) if case["observations"]}
    print(f"{len(requests)} games, {sum(len(p) for p, _ in requests.values()):,} prompt characters")
    if args.dry_run:
        return
    tagged = batch_parse(requests, args.model, args.thinking)
    all_rows = []
    for i, (path, cases) in enumerate(runs.items()):
        rows = []
        for j, case in enumerate(cases):
            key = f"r{i}_g{j}"
            result = tagged.get(key)
            if result is None and key in requests:
                result = parse_with_claude(requests[key][0], DecisionTags, args.model, args.thinking)[0]
            rows.extend(tag_rows(case, result))
        (Path(path).parent / "decisions.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
        all_rows.extend(rows)
    summary = {"model": args.model, "observations": len(all_rows), **checks(all_rows),
               "cost_usd": round(usage_cost_usd(), 4)}
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
