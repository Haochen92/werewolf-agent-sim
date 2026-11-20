"""Adoption check for the quoted transcript: does quoting every player's words change ordinary play?

Record: evidence/agent_boundaries/forged_speaker/experiment_log.md (2026-11-17, adoption). The game
now renders each player's line of today's discussion as ``player_3: "..."`` and puts a caption under
the "Today's discussion" heading (format_day_channel and layout.PUBLIC_RECORD), the forged-speaker
probe's ``quoted_and_caption`` arm. There is no attack here. Two parts:

  votes   the probe's three frozen moments with no attack message. The old rendering's votes are the
          probe's control votes, reused; the new rendering is sent here, with the same voters and the
          same number of repeats as each moment's control.
  speech  the frozen day-discussion turns of the Haiku effort replay (turn_cases.jsonl), one sample
          each, under the new rendering and under the old one. The old rendering is rebuilt in this
          process only: the formatter's quoting is switched off and the caption line is taken out of
          the template. Prompt assembly is the bench replay's (evaluation/src/replay/hallucination_bench).

Before any call the dry run checks that the old rendering rebuilt here equals the probe's saved control
prompts byte for byte, and that new and old prompts differ only in the quoted lines and the caption.

  poetry run python -m evaluation.experiments.forged_speaker_adoption_check            # dry run (default)
  poetry run python -m evaluation.experiments.forged_speaker_adoption_check --run      # paid calls, resume-safe
  poetry run python -m evaluation.experiments.forged_speaker_adoption_check --score
"""

from __future__ import annotations

import argparse
import contextlib
import json
import statistics
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

# The probe pins the model environment at import (Haiku 5.5, thinking low, JSON schema, no tracing).
from evaluation.experiments import forged_speaker_probe as probe  # noqa: E402

TURN_CASES = Path("evidence/gameplay/deduction/data/haiku_effort_replay/turn_cases.jsonl")
# The same turns' recorded Haiku 5.5 (thinking low) usage, 2026-10-16: the output basis for the estimate.
SPEECH_USAGE_FILE = Path("evidence/gameplay/deduction/data/haiku_effort_replay/runs/haiku_effort_turns/"
                         "judged_haiku_low.jsonl")
OUT_DIR = probe.OUT_DIR / "adoption_check"
VOTES_FILE = OUT_DIR / "votes.jsonl"
SPEECH_FILE = OUT_DIR / "speech.jsonl"
MANIFEST_FILE = OUT_DIR / "manifest.json"
SCORES_FILE = OUT_DIR / "scores.json"
PROMPTS_DIR = OUT_DIR / "dry_run_prompts"

# Each moment's control repeats in the probe: round 1 sent 9 per voter on moment 1, round 2 sent 3.
VOTE_REPEATS = {probe.MOMENT_1.name: probe.CONTROL_REPEATS, probe.MOMENT_2.name: 3, probe.MOMENT_3.name: 3}
SPEECH_ARMS = ("new", "old")
CAP_USD = 0.30
WORKERS = 4
DOUBLE_QUOTES = ('"', "“", "”")


@dataclass
class SpeechCall:
    """One discussion turn under one rendering."""

    call_id: str
    case: dict
    arm: str
    prompt_text: str


# --- Entry ---------------------------------------------------------------------------------------

def main() -> None:
    """Parse the mode and run it: the dry run (default), the paid run, or the scoring."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--run", action="store_true", help="make the paid Haiku calls (resume-safe)")
    mode.add_argument("--score", action="store_true", help="vote distributions and speech counts")
    args = parser.parse_args()

    if args.score:
        score()
        return
    vote_calls = build_vote_calls()
    speech_calls = build_speech_calls()
    checks = verify(vote_calls, speech_calls)
    write_prompts(vote_calls, speech_calls)
    estimate = estimate_cost(vote_calls, speech_calls)
    write_manifest(vote_calls, speech_calls, checks, estimate)
    if not args.run:
        print("Dry run: no model call made. Pass --run for the paid run.")
        return
    if estimate["usd_upper_bound"] > CAP_USD:
        raise SystemExit(f"upper bound ${estimate['usd_upper_bound']:.3f} is over the ${CAP_USD} cap")
    run_votes(vote_calls)
    run_speech([c for c in speech_calls if c.arm == "new"])
    with old_rendering():
        run_speech([c for c in speech_calls if c.arm == "old"])


# --- Building the calls --------------------------------------------------------------------------

def build_vote_calls() -> list:
    """The new rendering's vote calls: each moment's control (no attack), every voter, the control's
    repeats. The probe's control arm adds nothing to the prompt, so the text is production's.

    Returns:
        The probe's PlannedCall list; ids are ``moment|new|voter|repeat``.
    """
    calls = []
    for moment in probe.MOMENTS.values():
        frozen_case = probe.load_frozen_case(moment)
        for repeat in range(VOTE_REPEATS[moment.name]):
            for voter in moment.voters:
                call = probe.plan_call(moment, frozen_case, "control", "none", voter, repeat)
                call.call_id = f"{moment.name}|new|{voter}|{repeat}"
                calls.append(call)
    return calls


def build_speech_calls() -> list[SpeechCall]:
    """Every frozen discussion turn of TURN_CASES under both renderings, one sample each.

    Returns:
        The SpeechCall list; ids are ``case_id|arm``.
    """
    cases = [json.loads(line) for line in TURN_CASES.read_text().splitlines()]
    calls = []
    for case in cases:
        assert case["phase"] == "day_discussion", case["case_id"]
        calls.append(SpeechCall(f"{case['case_id']}|new", case, "new", speech_prompt(case)))
        with old_rendering():
            calls.append(SpeechCall(f"{case['case_id']}|old", case, "old", speech_prompt(case)))
    return calls


def speech_prompt(case: dict) -> str:
    """The discussion turn's prompt as the bench replay builds it, under the rendering now in force.

    Args:
        case: a frozen discussion turn.

    Returns:
        The rendered prompt, each message under a "=== <type> ===" header.
    """
    from Agents.prompts.prompt_inputs import build_agent_prompt_input
    from evaluation.src.replay import hallucination_bench as bench

    payload = bench.turn_payload(case)
    template, _schema, _key = bench.turn_template(case, payload)
    return probe.render_prompt(template, build_agent_prompt_input(payload))


@contextlib.contextmanager
def old_rendering():
    """The transcript as it was before the change, in this process only: player text unquoted
    (``_quoted_text`` replaced by ``_spoken_text``) and the caption line taken out of the templates
    the bench replay and the probe read. Restored on exit."""
    from Agents.nodes.day import actors
    from Agents.prompts import prompt_formatters

    saved = (prompt_formatters._quoted_text, dict(actors.DISCUSS_PROMPTS), dict(actors.VOTE_PROMPTS))
    prompt_formatters._quoted_text = prompt_formatters._spoken_text
    for prompts in (actors.DISCUSS_PROMPTS, actors.VOTE_PROMPTS):
        for role, template in list(prompts.items()):
            prompts[role] = without_caption(template)
    try:
        yield
    finally:
        prompt_formatters._quoted_text = saved[0]
        actors.DISCUSS_PROMPTS.clear()
        actors.DISCUSS_PROMPTS.update(saved[1])
        actors.VOTE_PROMPTS.clear()
        actors.VOTE_PROMPTS.update(saved[2])


def without_caption(template):
    """A copy of a seat template with the caption line under the heading removed.

    Args:
        template: a ChatPromptTemplate built from (role, text) pairs.

    Returns:
        The same messages, the caption line gone; raises if a template does not hold it once.
    """
    from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate

    caption_line = probe.CAPTION_QUOTED + "\n"
    messages = []
    found = 0
    for message in template.messages:
        text = message.prompt.template
        found += text.count(caption_line)
        role = "system" if isinstance(message, SystemMessagePromptTemplate) else "human"
        messages.append((role, text.replace(caption_line, "")))
    if found != 1:
        raise SystemExit(f"caption found {found} times in a template")
    return ChatPromptTemplate.from_messages(messages)


# --- Checks --------------------------------------------------------------------------------------

def verify(vote_calls: list, speech_calls: list[SpeechCall]) -> dict:
    """Check, before any call, that the comparison differs only in the rendering.

    Votes: the old rendering rebuilt here equals the probe's saved control prompt byte for byte, so the
    reused votes were cast on it; the new prompt differs from it only in today's player lines (quoted)
    and the caption line. Speech: the same two-way diff, new against old, for every case.

    Args:
        vote_calls: the new vote calls.
        speech_calls: both renderings of every discussion turn.

    Returns:
        {check name: "ok"}; raises SystemExit on the first failure.
    """
    checks = {}
    for call in vote_calls:
        if call.repeat != 0:
            continue
        moment = call.moment
        frozen_case = probe.load_frozen_case(moment)
        with old_rendering():
            old = probe.plan_call(moment, frozen_case, "control", "none", call.voter, 0).prompt_text
        files = probe.ROUND_FILES[1] if moment is probe.MOMENT_1 else probe.ROUND_FILES[2]
        folder = files.prompts_dir if moment is probe.MOMENT_1 else files.prompts_dir / moment.name
        saved = (folder / "control" / "none" / f"{call.voter}.txt").read_text()
        if old != saved:
            raise SystemExit(f"{moment.name} {call.voter}: the old rendering differs from the saved control prompt")
        expect_only_rendering_changes(old, call.prompt_text, f"vote {moment.name} {call.voter}")
        checks[f"vote {moment.name} {call.voter}"] = "ok"
    by_case = {}
    for call in speech_calls:
        by_case.setdefault(call.case["case_id"], {})[call.arm] = call.prompt_text
    for case_id, prompts in by_case.items():
        expect_only_rendering_changes(prompts["old"], prompts["new"], f"speech {case_id}")
        checks[f"speech {case_id}"] = "ok"
    print(f"checks passed: {len(checks)}")
    return checks


def expect_only_rendering_changes(old: str, new: str, label: str) -> None:
    """Fail unless ``new`` is ``old`` with the caption line added under the heading and each player
    line of today's discussion quoted (double quotes inside turned into single ones).

    Args:
        old: the prompt under the old rendering.
        new: the prompt under the new rendering.
        label: names the comparison in a failure message.
    """
    today = probe.today_section(old)
    player_lines = [line for line in today if not line.startswith("game_master: ") and ": " in line
                    and line.split(": ", 1)[0].startswith("player_")]
    quoted_lines = []
    for line in player_lines:
        speaker, text = line.split(": ", 1)
        quoted_lines.append(f'{speaker}: "{probe.quote_safe(text)}"')
    probe.expect_changes(old, new, removed=player_lines, added=[probe.CAPTION_QUOTED] + quoted_lines, label=label)


# --- Dry-run outputs -----------------------------------------------------------------------------

def write_prompts(vote_calls: list, speech_calls: list[SpeechCall]) -> None:
    """Write one prompt per (moment, voter) and per (case, arm)."""
    for call in vote_calls:
        if call.repeat == 0:
            path = PROMPTS_DIR / "votes" / call.moment.name / f"{call.voter}.txt"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(call.prompt_text)
    for call in speech_calls:
        path = PROMPTS_DIR / "speech" / call.arm / f"{call.case['case_id']}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(call.prompt_text)
    print(f"prompts -> {PROMPTS_DIR}")


def estimate_cost(vote_calls: list, speech_calls: list[SpeechCall]) -> dict:
    """Price the run from the probe's recorded usage on the same model and settings.

    Every prompt is priced at round 1's highest input tokens per prompt character. The upper bound
    bills it all uncached, each vote's output at round 1's largest and each discussion turn's output
    at the largest of the Haiku effort replay's low arm (the same turns, 2026-10-16). The expected
    figure uses the means and round 1's cached share.

    Args:
        vote_calls: the new vote calls.
        speech_calls: both renderings of every discussion turn.

    Returns:
        The counts, the token bases and the costs in USD.
    """
    from Agents.llm_factory.pricing import cost_usd

    basis = probe.round_1_usage_basis()
    speech_rows = [json.loads(line) for line in SPEECH_USAGE_FILE.read_text().splitlines()]
    speech_outputs = [row["usage"]["output"] for row in speech_rows if row.get("usage")]
    vote_chars = sum(len(call.prompt_text) for call in vote_calls)
    speech_chars = sum(len(call.prompt_text) for call in speech_calls)
    input_tokens = round((vote_chars + speech_chars) * basis["max_input_tokens_per_char"])
    upper_output = len(vote_calls) * basis["max_output"] + len(speech_calls) * max(speech_outputs)
    mean_output = round(len(vote_calls) * basis["mean_output"]
                        + len(speech_calls) * statistics.mean(speech_outputs))
    now = datetime.now(timezone.utc)
    billed = probe.MODEL.split("/", 1)[1]
    estimate = {
        "vote_calls": len(vote_calls),
        "speech_calls": len(speech_calls),
        "round_1_basis": basis,
        "speech_output_basis": {"file": str(SPEECH_USAGE_FILE), "max": max(speech_outputs),
                                "mean": round(statistics.mean(speech_outputs), 1)},
        "input_tokens": input_tokens,
        "usd_upper_bound": cost_usd(billed, now, input=input_tokens, cached=0, output=upper_output),
        "usd_expected": cost_usd(billed, now, input=input_tokens,
                                 cached=round(input_tokens * basis["cached_share"]), output=mean_output),
        "cap_usd": CAP_USD,
    }
    print(json.dumps(estimate, indent=1))
    return estimate



def write_manifest(vote_calls: list, speech_calls: list[SpeechCall], checks: dict, estimate: dict) -> None:
    """Write the provenance manifest: run fingerprint, the pinned config, the checks and the estimate."""
    from Agents.llm_factory.accessors import _game_model, game_thinking_level
    from Agents.run_fingerprint import runtime_fingerprint

    assert _game_model() == probe.MODEL and game_thinking_level(probe.MODEL) == "low", (_game_model(),)
    manifest = {
        "written_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "runner": "evaluation/experiments/forged_speaker_adoption_check.py",
        "runtime_fingerprint": runtime_fingerprint(),
        "config": {
            "vote_moments": {name: {"voters": list(probe.MOMENTS[name].voters), "repeats": repeats,
                                    "old_votes": "the probe's control votes, reused"}
                             for name, repeats in VOTE_REPEATS.items()},
            "speech_cases": str(TURN_CASES), "speech_arms": list(SPEECH_ARMS), "speech_samples_per_arm": 1,
            "caption": probe.CAPTION_QUOTED, "model_env": probe.MODEL_ENV, "memory": "none",
        },
        "checks": checks,
        "estimate": estimate,
        "planned_call_ids": [c.call_id for c in vote_calls] + [c.call_id for c in speech_calls],
    }
    MANIFEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"manifest -> {MANIFEST_FILE}")


# --- The paid run --------------------------------------------------------------------------------

def run_votes(calls: list) -> None:
    """Send every vote call not already recorded with a vote, through the probe's call_vote."""
    done = {row["call_id"] for row in probe.read_votes(VOTES_FILE)}
    todo = [call for call in calls if call.call_id not in done]
    print(f"votes: {len(done)} done, {len(todo)} to send")
    run_in_pool(todo, VOTES_FILE, probe.call_vote, lambda row: row.get("vote"))


def run_speech(calls: list[SpeechCall]) -> None:
    """Send every discussion turn not already recorded, one sample through the bench replay's generate."""
    done = {row["call_id"] for row in read_rows(SPEECH_FILE) if row.get("valid")}
    todo = [call for call in calls if call.call_id not in done]
    print(f"speech: {len(done)} done, {len(todo)} to send")
    run_in_pool(todo, SPEECH_FILE, speech_row, lambda row: row.get("passed"))


def speech_row(call: SpeechCall) -> dict:
    """One discussion turn: the spoken message, or a pass, and its usage.

    Args:
        call: the SpeechCall.

    Returns:
        The row to record.
    """
    from evaluation.src.replay.hallucination_bench import generate

    (sample,) = generate(call.case, 1)
    message = next((u["text"] for u in sample["units"] if u["unit"] == "message"), None)
    return {"call_id": call.call_id, "case_id": call.case["case_id"], "arm": call.arm,
            "valid": sample["valid"], "error": sample.get("error"), "passed": sample["valid"] and message is None,
            "message": message, "usage": sample.get("usage"),
            "at": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def run_in_pool(calls: list, out_file: Path, send, show) -> None:
    """Send ``calls`` WORKERS at a time, appending one JSON line per call as it lands."""
    lock = threading.Lock()

    def send_and_record(call) -> None:
        row = send(call)
        with lock, out_file.open("a") as out:
            out.write(json.dumps(row) + "\n")
        print(f"{call.call_id}: {show(row)}", flush=True)

    out_file.parent.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        list(pool.map(send_and_record, calls))


def read_rows(path: Path) -> list[dict]:
    """The rows of a JSON-lines file, the last per call id; empty when it does not exist."""
    if not path.exists():
        return []
    rows = {}
    for line in path.read_text().splitlines():
        row = json.loads(line)
        rows[row["call_id"]] = row
    return list(rows.values())


# --- Scoring -------------------------------------------------------------------------------------

def score() -> None:
    """Vote distributions old against new per moment, speech counts per rendering, and the cost from
    recorded usage; written to SCORES_FILE."""
    votes = score_votes()
    speech = score_speech()
    cost = score_cost()
    result = {"votes": votes, "speech": speech, "cost": cost}
    print(json.dumps(result, indent=1))
    SCORES_FILE.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")


def score_votes() -> dict:
    """Per moment and rendering: the count of each vote target, for town voters and wolf voters apart.

    Returns:
        {moment: {"old" | "new": {"town" | "wolf": {target: count}}}}.
    """
    old_rows = [{**row, "moment": probe.MOMENT_1.name} for row in probe.read_votes(probe.ROUND_FILES[1].votes_file)
                if row["arm"] == "control"]
    old_rows += [row for row in probe.read_votes(probe.ROUND_FILES[2].votes_file) if row["arm"] == "control"]
    new_rows = probe.read_votes(VOTES_FILE)
    table = {}
    for rendering, rows in (("old", old_rows), ("new", new_rows)):
        for row in rows:
            moment = probe.MOMENTS[row["moment"]]
            side = "wolf" if row["voter"] in moment.wolf_voters else "town"
            cell = table.setdefault(row["moment"], {}).setdefault(rendering, {"town": {}, "wolf": {}})
            cell[side][row["vote"]] = cell[side].get(row["vote"], 0) + 1
    return table


def score_speech() -> dict:
    """Per rendering: turns, passes, messages that start or end with a double quotation mark or are
    wrapped in them, messages holding any double quotation mark, and message length in characters
    (with the paired difference, new minus old, over cases where both spoke).

    Returns:
        The counts per rendering and the paired length difference.
    """
    rows = [row for row in read_rows(SPEECH_FILE) if row.get("valid")]
    by_arm = {}
    for arm in SPEECH_ARMS:
        arm_rows = [row for row in rows if row["arm"] == arm]
        messages = [row["message"].strip() for row in arm_rows if row["message"]]
        lengths = [len(message) for message in messages]
        by_arm[arm] = {
            "turns": len(arm_rows),
            "passed": sum(row["passed"] for row in arm_rows),
            "spoke": len(messages),
            "starts_or_ends_with_double_quote": sum(m.startswith(DOUBLE_QUOTES) or m.endswith(DOUBLE_QUOTES)
                                                    for m in messages),
            "wrapped_in_double_quotes": sum(m.startswith(DOUBLE_QUOTES) and m.endswith(DOUBLE_QUOTES)
                                            for m in messages),
            "contains_double_quote": sum(any(q in m for q in DOUBLE_QUOTES) for m in messages),
            "length_mean": round(statistics.mean(lengths), 1) if lengths else None,
            "length_median": statistics.median(lengths) if lengths else None,
        }
    spoken = {(row["case_id"], row["arm"]): len(row["message"].strip()) for row in rows if row["message"]}
    paired = [spoken[case, "new"] - spoken[case, "old"] for case, arm in spoken
              if arm == "new" and (case, "old") in spoken]
    by_arm["paired_length_new_minus_old"] = {
        "cases": len(paired),
        "mean": round(statistics.mean(paired), 1) if paired else None,
        "median": statistics.median(paired) if paired else None,
        "new_longer": sum(d > 0 for d in paired),
        "old_longer": sum(d < 0 for d in paired),
    }
    return by_arm


def score_cost() -> dict:
    """This run's recorded usage and its price."""
    from Agents.llm_factory.pricing import cost_usd

    totals = {"calls": 0, "input": 0, "cached": 0, "output": 0}
    for row in probe.read_votes(VOTES_FILE) + [r for r in read_rows(SPEECH_FILE) if r.get("usage")]:
        totals["calls"] += 1
        for field in ("input", "cached", "output"):
            totals[field] += row["usage"][field]
    totals["usd"] = round(cost_usd(probe.MODEL.split("/", 1)[1], datetime.now(timezone.utc),
                                   input=totals["input"], cached=totals["cached"], output=totals["output"]), 4)
    return totals


if __name__ == "__main__":
    main()
