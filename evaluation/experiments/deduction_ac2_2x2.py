"""AC2 2x2, interleaved: seat block (current / trimmed of player_8's two sentences) x deduction_placement.

Record: evidence/gameplay/deduction/data/deduction_ac2_2x2/ (README there). Generation only. Reuses
deduction_placement_screen.py (AC2 case, ``_turn``, legal-target schema, cost accounting, SDK-retry
counter) and deduction_ac2_ablation.py (the removed strings E1 and WILL, ``_ablate``). The four prompts
are rendered ONCE, verified and saved to prompts/; every call then sends those saved texts (system +
human), so a concurrent edit to Agents/ cannot change a prompt mid-run. All 100 (arm, sample) jobs run in
one schedule shuffled with a fixed seed; invalid samples are rerun at the end, inside the same cap.

  poetry run python evaluation/experiments/deduction_ac2_2x2.py --render-only
  LANGFUSE_TRACING_ENABLED=false GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low \
    GAME_LLM_ATTEMPTS=1 GAME_LLM_TIMEOUT_S=180 poetry run python evaluation/experiments/deduction_ac2_2x2.py --run
  poetry run python evaluation/experiments/deduction_ac2_2x2.py --count
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import random
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from evaluation.experiments import deduction_ac2_ablation as ablation
from evaluation.experiments import deduction_placement_screen as screen
from evaluation.src.replay.hallucination_bench import _usage_totals

OUT = screen.DATA / "deduction_ac2_2x2"
N10_PROMPTS = screen.DATA / "deduction_placement_n10" / "prompts"
REMOVALS = (ablation.E1, ablation.WILL)
BLOCKS = {"current": (), "trimmed": REMOVALS}
ARMS = [(b, p) for b in BLOCKS for p in screen.ARMS]  # (block, placement)
N = 25
SEED = 20261018
WORKERS = 3
MAX_CALLS = 115


def _arm(block: str, placement: str) -> str:
    return f"{block}_{placement}"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def render() -> dict:
    name, source, case_id, fields, _ = next(c for c in screen.CASES if c[0] == "AC2")
    turns = {p: screen._turn(name, source, case_id, fields, p) for p in screen.ARMS}
    a, b = turns["before_note"], turns["after_note"]
    systems = {p: t["system"] for p, t in turns.items()}
    from Agents.turn.action_space import valid_targets_for_action

    targets = {p: list(valid_targets_for_action(t["payload"], t["key"])) for p, t in turns.items()}
    check: dict = {
        "same_system_both_placements": a["system"] == b["system"],
        "same_schema_key_targets_both_placements": (a["schema"] is b["schema"] and a["key"] == b["key"]
                                                    and targets["before_note"] == targets["after_note"]),
        "legal_vote_targets": targets["before_note"],
        "live_render_equals_n10_file": {p: t["human"] == (N10_PROMPTS / f"AC2_{p}.txt").read_text()
                                        for p, t in turns.items()},
        "system_chars": len(a["system"]), "system_sha256": _sha(a["system"]),
        "removed_strings": list(REMOVALS), "removed_chars": [len(s) for s in REMOVALS],
        "arms": [],
    }
    ok = check["same_system_both_placements"] and check["same_schema_key_targets_both_placements"]
    humans, blocks = {}, {}
    for block, removals in BLOCKS.items():
        for p in screen.ARMS:
            live = turns[p]["human"]
            counts_before = [live.count(s) for s in removals]
            in_seat_block = [turns[p]["seat_block"].count(s) for s in removals]
            human = ablation._ablate(live, removals)
            seat = ablation._ablate(turns[p]["seat_block"], removals)
            humans[_arm(block, p)], blocks[_arm(block, p)] = human, seat
            row = {"arm": _arm(block, p), "chars": len(human), "chars_removed": len(live) - len(human),
                   "occurrences_before_removal": counts_before, "occurrences_in_seat_block": in_seat_block,
                   "occurrences_after_removal": [human.count(s) for s in removals],
                   "equals_sum_of_removals": len(live) - len(human) == sum(map(len, removals)),
                   "seat_block_chars": len(seat), "seat_block_in_prompt_once": human.count(seat) == 1,
                   "sha256": _sha(human)}
            ok &= (all(c == 1 for c in counts_before) and all(c == 1 for c in in_seat_block)
                   and not any(row["occurrences_after_removal"]) and row["equals_sum_of_removals"]
                   and row["seat_block_in_prompt_once"])
            check["arms"].append(row)
    pairs = []
    for block in BLOCKS:
        hb, ha = humans[_arm(block, "before_note")], humans[_arm(block, "after_note")]
        sb, sa = blocks[_arm(block, "before_note")], blocks[_arm(block, "after_note")]
        rest_b, rest_a = hb.replace(sb, "", 1), ha.replace(sa, "", 1)
        note = "Adaptive Strategic thinking:"
        pair = {"block": block, "same_seat_block": sb == sa,
                "only_the_block_moves": rest_b.split() == rest_a.split(),
                "same_multiset_of_chars": sorted(hb) == sorted(ha),
                "block_before_note_in_before": hb.find(sb) < hb.find(note),
                "block_after_note_in_after": ha.find(sa) > ha.find(note)}
        ok &= all(v for k, v in pair.items() if k != "block")
        pairs.append(pair)
    check["placement_pairs"] = pairs
    check["all_ok"] = bool(ok)
    (OUT / "prompts").mkdir(parents=True, exist_ok=True)
    (OUT / "prompts" / "system.txt").write_text(a["system"])
    for arm, human in humans.items():
        (OUT / "prompts" / f"AC2_{arm}.txt").write_text(human)
    (OUT / "prompt_check.json").write_text(json.dumps(check, indent=1) + "\n")
    print(json.dumps(check, indent=1))
    if not ok:
        raise SystemExit("verification failed: see prompt_check.json; no model call made")
    return {"turn": a, "case_id": case_id}


def _frozen() -> dict[str, list]:
    """The saved texts, read back: these are what every call sends."""
    from langchain_core.messages import HumanMessage, SystemMessage

    system = (OUT / "prompts" / "system.txt").read_text()
    return {_arm(b, p): [SystemMessage(content=system),
                         HumanMessage(content=(OUT / "prompts" / f"AC2_{_arm(b, p)}.txt").read_text())]
            for b, p in ARMS}


def schedule() -> list[tuple[str, int]]:
    jobs = [(_arm(b, p), i) for b, p in ARMS for i in range(N)]
    random.Random(SEED).shuffle(jobs)
    return jobs


def run(rendered: dict) -> None:
    from langchain_core.callbacks import UsageMetadataCallbackHandler

    from Agents.llm_factory import get_llm
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.llm_factory.pricing import cost_usd
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action

    model = _game_model()
    assert model == "anthropic/claude-haiku-5-5" and game_thinking_level(model) == "low", (model,)
    t = rendered["turn"]
    retry_log = screen._RetryCounter()
    for logger in ("anthropic", "anthropic._base_client"):
        logging.getLogger(logger).addHandler(retry_log)
        logging.getLogger(logger).setLevel(logging.INFO)
    bound = output_schema_with_legal_targets(t["schema"], t["key"], valid_targets_for_action(t["payload"], t["key"]))
    llm = get_llm().with_structured_output(bound)
    messages = _frozen()
    jobs = schedule()
    (OUT / "schedule.json").write_text(json.dumps({"seed": SEED, "jobs": jobs}) + "\n")
    lock = threading.Lock()
    state = {"calls": 0, "order": 0, "cost": 0.0}
    fh = (OUT / "samples.jsonl").open("a")

    def one(arm: str, i: int, position: int, rerun: bool) -> dict | None:
        with lock:
            if state["calls"] + retry_log.retries >= MAX_CALLS:
                return None
            state["calls"] += 1
            order = state["order"]
            state["order"] += 1
        msgs = messages[arm]
        assert msgs[1].content == (OUT / "prompts" / f"AC2_{arm}.txt").read_text()
        usage, started_at, started, out, err = (UsageMetadataCallbackHandler(), datetime.now(timezone.utc),
                                                time.monotonic(), None, "")
        try:
            out = llm.invoke(msgs, config={"callbacks": [usage]})
        except Exception as e:  # recorded; the sample counts as invalid
            err = str(e)[:300]
        tokens = _usage_totals(usage, time.monotonic() - started)
        written = sum((d.get(k) or 0) for u in usage.usage_metadata.values()
                      for d in [u.get("input_token_details") or {}]
                      for k in ("cache_creation", "ephemeral_5m_input_tokens", "ephemeral_1h_input_tokens"))
        cost = cost_usd(model.removeprefix("anthropic/"), datetime.now(timezone.utc),
                        input=tokens["input"], cached=tokens["cached"], output=tokens["output"],
                        written=written) or 0.0
        block, placement = arm.split("_", 1)
        row = {"case": "AC2", "case_id": rendered["case_id"], "arm": arm, "block": block, "placement": placement,
               "sample": i, "schedule_position": position, "call_order": order, "rerun": rerun,
               "started_utc": started_at.isoformat(timespec="seconds"),
               "finished_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
               "valid": out is not None, "error": err}
        if out is not None:
            row |= {"vote_target": getattr(out, "vote_target", None),
                    "updated_strategy": out.updated_strategy,
                    "reads": [r.model_dump() for r in out.reads]}
        row["usage"] = {**tokens, "cache_written": written, "cost_usd": round(cost, 6)}
        with lock:
            state["cost"] += cost
            fh.write(json.dumps(row) + "\n")
            fh.flush()
        print(f"[{order}] pos {position} {arm} #{i}: valid={row['valid']} vote={row.get('vote_target')} "
              f"{err[:80]} ${cost:.4f}", flush=True)
        return row

    with ThreadPoolExecutor(WORKERS) as pool:
        list(pool.map(lambda job: one(job[1][0], job[1][1], job[0], False), enumerate(jobs)))
        # reruns: the still-invalid samples, in schedule order, until all valid or the cap is reached
        position = {job: k for k, job in enumerate(jobs)}
        while True:
            rows = [json.loads(line) for line in (OUT / "samples.jsonl").read_text().splitlines()]
            latest = {(r["arm"], r["sample"]): r for r in rows}
            invalid = sorted((k for k, r in latest.items() if not r["valid"]), key=position.__getitem__)
            if not invalid or state["calls"] + retry_log.retries >= MAX_CALLS:
                break
            done = list(pool.map(lambda k: one(k[0], k[1], position[k], True), invalid))
            if all(d is None for d in done):
                break
    fh.close()
    print(f"model requests: {state['calls']} invokes + {retry_log.retries} SDK retries; cost ${state['cost']:.4f}")


def count() -> None:
    rows = [json.loads(line) for line in (OUT / "samples.jsonl").read_text().splitlines()]
    latest_valid = {}
    for r in rows:
        if r["valid"]:
            latest_valid[(r["arm"], r["sample"])] = r
    pos = {tuple(j): k for k, j in enumerate(json.loads((OUT / "schedule.json").read_text())["jobs"])}
    result: dict = {"rows": len(rows), "calls_by_arm": Counter(r["arm"] for r in rows),
                    "cost_by_arm": {}, "per_arm": {}}
    for r in rows:
        result["cost_by_arm"][r["arm"]] = round(result["cost_by_arm"].get(r["arm"], 0) + r["usage"]["cost_usd"], 6)
    for b, p in ARMS:
        arm = _arm(b, p)
        got = {i: latest_valid[(arm, i)] for i in range(N) if (arm, i) in latest_valid}
        result["per_arm"][arm] = {
            "valid": len(got), "missing": [i for i in range(N) if i not in got],
            "votes": dict(Counter(r["vote_target"] for r in got.values()).most_common()),
            "first_half": dict(Counter(r["vote_target"] for i, r in got.items() if pos[(arm, i)] < 50).most_common()),
            "second_half": dict(Counter(r["vote_target"] for i, r in got.items() if pos[(arm, i)] >= 50).most_common()),
            "slots_first_half": sum(pos[(arm, i)] < 50 for i in range(N)),
            "counted_rows_that_are_reruns": sorted(i for i, r in got.items() if r["rerun"]),
        }
    totals = {k: sum(r["usage"][k] for r in rows) for k in ("input", "cached", "cache_written", "output",
                                                           "reasoning", "cost_usd")}
    result["totals"] = totals
    result["invalid_rows"] = [{"arm": r["arm"], "sample": r["sample"], "position": r["schedule_position"],
                               "rerun": r["rerun"], "error": r["error"][:160]} for r in rows if not r["valid"]]
    result["window_utc"] = [min(r["started_utc"] for r in rows), max(r["finished_utc"] for r in rows)]
    print(json.dumps(result, indent=1, default=dict))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--count", action="store_true")
    args = parser.parse_args()
    if args.count:
        count()
        return
    rendered = render()
    if args.run:
        if (OUT / "samples.jsonl").exists():
            raise SystemExit("samples.jsonl exists: this runner makes one run only")
        run(rendered)


if __name__ == "__main__":
    main()
