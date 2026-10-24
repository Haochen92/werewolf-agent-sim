"""Owner check of the factual-error judges: build a blind labelling packet, then score it.

What it measures: how far the hallucination bench's judges, on Claude Haiku 5.5 since 2026-10-12,
agree with the owner on whether a generated statement contradicts what the judge was given (the
written expectation for the expectation judge, the fact sheet for the census reader). The judge's
recorded verdict is mapped to ``error`` / ``no_error`` (``label_for_verdict`` in the adapter) and
compared with the owner's label on a stratified draw: statements the judge flagged and statements
it did not, capped per bench case.

What the owner does: read ``GUIDE.md`` in the packet folder, label every item in
``export/batch_*.md`` by filling ``export/answers_template.json``, save it as ``human.json`` in the
packet folder, then run ``score``.

    poetry run python -m evaluation.experiments.owner_check_factual_errors build
    poetry run python -m evaluation.experiments.owner_check_factual_errors score

``build`` reads only recorded bench output (no model calls); ``score`` runs the labelling
pipeline's calibrate stage on the packet's ``calib.json``.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.labeling.adapters.factual_errors import (
    CENSUS_READER,
    ERROR_LABEL,
    EXPECTATION_JUDGE,
    NO_ERROR_LABEL,
    FactualErrorAdapter,
    JudgedStatement,
    judge_unit_name,
    label_for_verdict,
)
from evaluation.src.labeling.anchor import draw_stratified_sample, write_stratum_file
from evaluation.src.labeling.config import CalibrationConfig, ExportConfig
from evaluation.src.labeling.exporter import export_for_manual
from evaluation.src.labeling.schemas import StratifiedSample

DEFAULT_RUN_DIRS = [
    REPO_ROOT / "evaluation/eval_results/hallucination_bench/shared_prefix_luna_2026_10_13",
]
"""The bench runs judged by Claude Haiku 5.5 on ten-seat cases (checked 2026-10-23: every other
ten-seat run set its expectation judge to Sonnet 5.5 or a Gemini model)."""
DEFAULT_PACKET_DIR = REPO_ROOT / "evidence/evaluation/labeling/owner_checks/factual_errors"

CHECKED_JUDGE_MODEL = "anthropic/claude-haiku-5-5"
JUDGE_DEFAULTS_MOVED_TO_HAIKU_ON = "2026-10-12"
"""Commit e70f1627 moved every bench judge default to Haiku 5.5; a run before it with no override
was judged by the Gemini defaults of its day, which the run's summary does not record."""

MODEL_SOURCE = "judge"
FLAGGED_STRATUM = "flagged"
NOT_FLAGGED_STRATUM = "not_flagged"
PER_STRATUM = 40
CAP_PER_CASE = 6
"""At most this many items per bench case in each stratum; 6 is the smallest cap that still fills
40 flagged items from the default run (its 57 flagged statements sit in 12 cases, 16 in one)."""
SEED = 20261023


@dataclass
class JudgedRun:
    """One bench run's recorded output: its config, its cases, and its judged samples per arm."""

    run_label: str
    run_at: str
    config: dict
    cases_by_id: dict[str, dict]
    judged_samples_by_arm: dict[str, list[dict]]
    judge_model_by_role: dict[str, str]
    """Which model filled each judge role, e.g. ``{"expectation_judge": "anthropic/claude-haiku-5-5", ...}``."""


def judge_models_of_run(run_summary: dict) -> dict[str, str]:
    """Return the model behind each judge role of one bench run, from its ``summary.json``.

    A role the run's config does not override used the bench's default on the day it ran.

    Args:
        run_summary: the parsed ``summary.json`` (``{"run_at": ..., "config": {...}, ...}``).

    Returns:
        ``{"expectation_judge": ..., "census_reader_recall": ..., "census_reader_precision": ...}``.
        A role left to the default before 2026-10-12 reads ``"unrecorded (pre-2026-10-12 default)"``.
    """
    from evaluation.src.cli_runner.regen_replay.both.hallucination_bench import (
        DEFAULT_PRECISION_MODEL,
        DEFAULT_RECALL_MODEL,
    )
    from evaluation.src.judges.golden_expectation import DEFAULT_GOLDEN_JUDGE_MODEL

    run_config = run_summary["config"]
    ran_after_haiku_defaults = run_summary["run_at"][:10] >= JUDGE_DEFAULTS_MOVED_TO_HAIKU_ON
    config_field_and_default_by_role = {
        "expectation_judge": ("golden_model", DEFAULT_GOLDEN_JUDGE_MODEL),
        "census_reader_recall": ("recall_model", DEFAULT_RECALL_MODEL),
        "census_reader_precision": ("precision_model", DEFAULT_PRECISION_MODEL),
    }
    judge_model_by_role: dict[str, str] = {}
    for judge_role, (config_field, current_default) in config_field_and_default_by_role.items():
        if run_config.get(config_field):
            judge_model_by_role[judge_role] = run_config[config_field]
        elif ran_after_haiku_defaults:
            judge_model_by_role[judge_role] = current_default
        else:
            judge_model_by_role[judge_role] = f"unrecorded (pre-{JUDGE_DEFAULTS_MOVED_TO_HAIKU_ON} default)"
    return judge_model_by_role


def read_judged_run(run_dir: Path) -> JudgedRun:
    """Read one bench run's summary, its case file and every arm's judged samples.

    Args:
        run_dir: the run folder, holding ``summary.json`` and ``judged_<arm>.jsonl`` per arm.
            The summary's ``config.dataset`` names the case file (relative to the repo root).

    Returns:
        The run. Raises FileNotFoundError if an arm's judged file is missing.
    """
    run_summary = json.loads((run_dir / "summary.json").read_text())
    run_config = run_summary["config"]

    cases_by_id: dict[str, dict] = {}
    for line in (REPO_ROOT / run_config["dataset"]).read_text().splitlines():
        if line.strip():
            case = json.loads(line)
            cases_by_id[case["case_id"]] = case

    judged_samples_by_arm: dict[str, list[dict]] = {}
    for arm in run_config["arms"]:
        judged_path = run_dir / f"judged_{arm['label']}.jsonl"
        judged_samples = []
        for line in judged_path.read_text().splitlines():
            if line.strip():
                judged_samples.append(json.loads(line))
        judged_samples_by_arm[arm["label"]] = judged_samples

    return JudgedRun(
        run_label=run_dir.name,
        run_at=run_summary["run_at"],
        config=run_config,
        cases_by_id=cases_by_id,
        judged_samples_by_arm=judged_samples_by_arm,
        judge_model_by_role=require_checked_judges(run_dir.name, judge_models_of_run(run_summary)),
    )


def require_checked_judges(run_label: str, judge_model_by_role: dict[str, str]) -> dict[str, str]:
    """Return the run's judge models unchanged if every judge role is the checked model.

    All three roles are required to be Haiku 5.5, so a run never mixes a checked and an unchecked
    judge in one packet.

    Args:
        run_label: the run's folder name, for the error message.
        judge_model_by_role: from ``judge_models_of_run``.

    Returns:
        ``judge_model_by_role``. Raises ValueError naming each role on another model.
    """
    other_models = []
    for judge_role, judge_model in judge_model_by_role.items():
        if judge_model != CHECKED_JUDGE_MODEL:
            other_models.append(f"{judge_role}={judge_model}")
    if other_models:
        raise ValueError(
            f"Run {run_label} was not judged by {CHECKED_JUDGE_MODEL} throughout: {', '.join(other_models)}"
        )
    return judge_model_by_role


def census_reader_fact_sheet(case: dict, unit: dict) -> dict:
    """Return the census reader's prompt fields for one statement, built as the bench built them.

    Mirrors ``hallucination_bench.judge_samples``: the screen's anchors for the text, then
    ``role_fact_read.build_fact_sheet`` on the case's recorded facts.

    Args:
        case: the bench case (``facts``, ``day``, ``speaker``).
        unit: the statement, ``{"unit": "message", "text": "..."}``.

    Returns:
        The ``build_fact_sheet`` dict, ready for ``role_fact_read.USER_TEMPLATE``.
    """
    from evaluation.src.audits.role_hallucination_screen import (
        anchors_for_text,
        claims_through,
        death_timeline,
    )
    from evaluation.src.judges.role_fact_read import build_fact_sheet

    case_facts = case["facts"]
    anchors = anchors_for_text(
        unit["text"],
        roles=case_facts["roles"],
        dead_from=death_timeline(case_facts),
        day=case["day"],
        speaker=case["speaker"],
        claims=claims_through(case_facts, case["day"]),
    )
    reader_candidate = {
        "day": case["day"],
        "speaker": case["speaker"],
        "unit": unit["unit"],
        "text": unit["text"],
        "anchors": anchors,
    }
    return build_fact_sheet(case_facts, reader_candidate)


def collect_judged_statements(
    judged_runs: list[JudgedRun],
) -> tuple[list[JudgedStatement], dict[str, str], dict[str, str]]:
    """Turn every judged statement of the runs into a candidate, with the judge's label kept apart.

    Statements the judge never read (``no_anchor``) or failed to read (``read_error``) are left
    out. Bench cases are numbered 1, 2, ... in (run, game, case id) order.

    Args:
        judged_runs: the runs, from ``read_judged_run``.

    Returns:
        ``(statements, judge_label_by_key, recorded_verdict_by_key)``: the candidates sorted by
        case number then key; the judge's label per key (``error`` / ``no_error``); and the verdict
        as the bench recorded it (e.g. ``golden_unclear``). Raises ValueError if a key repeats.
    """
    case_identities = set()
    for judged_run in judged_runs:
        for judged_samples in judged_run.judged_samples_by_arm.values():
            for judged_sample in judged_samples:
                case = judged_run.cases_by_id[judged_sample["case_id"]]
                case_identities.add((judged_run.run_label, case["game_id"], case["case_id"]))
    case_number_by_identity = {}
    for case_number, case_identity in enumerate(sorted(case_identities), start=1):
        case_number_by_identity[case_identity] = case_number

    statements: list[JudgedStatement] = []
    judge_label_by_key: dict[str, str] = {}
    recorded_verdict_by_key: dict[str, str] = {}
    for judged_run in judged_runs:
        for arm_label, judged_samples in judged_run.judged_samples_by_arm.items():
            for judged_sample in judged_samples:
                case = judged_run.cases_by_id[judged_sample["case_id"]]
                judge_kind = EXPECTATION_JUDGE if case.get("golden") else CENSUS_READER
                units_and_verdicts = zip(judged_sample["units"], judged_sample["unit_verdicts"])
                for unit_index, (unit, recorded_verdict) in enumerate(units_and_verdicts):
                    judge_label = label_for_verdict(judge_kind, recorded_verdict)
                    if judge_label is None:
                        continue
                    key = (
                        f"{judged_run.run_label}:{case['game_id']}:{case['case_id'][:8]}:"
                        f"{arm_label}:s{judged_sample['sample']}:u{unit_index}"
                    )
                    if key in judge_label_by_key:
                        raise ValueError(f"Statement key {key!r} appears twice")
                    expectation = None
                    fact_sheet = None
                    if judge_kind == EXPECTATION_JUDGE:
                        expectation = case["golden"]
                    else:
                        fact_sheet = census_reader_fact_sheet(case, unit)
                    statement = JudgedStatement(
                        key=key,
                        case_index=case_number_by_identity[
                            (judged_run.run_label, case["game_id"], case["case_id"])
                        ],
                        run_label=judged_run.run_label,
                        game_id=case["game_id"],
                        case_id=case["case_id"],
                        arm=arm_label,
                        sample=judged_sample["sample"],
                        unit_index=unit_index,
                        unit_kind=unit["unit"],
                        judge_unit_name=judge_unit_name(unit["unit"]),
                        judge_kind=judge_kind,
                        statement_text=unit["text"],
                        expectation=expectation,
                        fact_sheet=fact_sheet,
                    )
                    statements.append(statement)
                    judge_label_by_key[key] = judge_label
                    recorded_verdict_by_key[key] = recorded_verdict

    statements.sort(key=lambda statement: (statement.case_index, statement.key))
    return statements, judge_label_by_key, recorded_verdict_by_key


def draw_capped_sample(
    statements: list[JudgedStatement],
    stratum_by_key: dict[str, str],
    per_stratum: int,
    cap_per_case: int,
    seed: int,
) -> StratifiedSample:
    """Draw up to ``per_stratum`` keys per stratum, with at most ``cap_per_case`` from any one case.

    Two seeded draws with the pipeline's own ``draw_stratified_sample``: first at most
    ``cap_per_case`` per (stratum, case), then ``per_stratum`` per stratum from what that kept.

    Args:
        statements: every candidate.
        stratum_by_key: ``"flagged"`` / ``"not_flagged"`` per key.
        per_stratum: items wanted per stratum, e.g. 40.
        cap_per_case: the most items one bench case may give a stratum, e.g. 6.
        seed: the random seed for both draws.

    Returns:
        The second draw: keys sorted by key, counts per stratum, and a note for a short stratum.
    """
    case_stratum_by_key = {}
    for statement in statements:
        case_stratum_by_key[statement.key] = f"{stratum_by_key[statement.key]}|case{statement.case_index}"
    capped_draw = draw_stratified_sample(
        list(case_stratum_by_key), case_stratum_by_key, per_stratum=cap_per_case, seed=seed
    )
    return draw_stratified_sample(
        capped_draw.drawn_keys, stratum_by_key, per_stratum=per_stratum, seed=seed
    )


def write_candidates(statements: list[JudgedStatement], path: Path) -> Path:
    """Write the candidates file the adapter reads: one ``JudgedStatement`` JSON per line.

    Args:
        statements: the candidates, in the order the export should show them.
        path: where to write.

    Returns:
        The path written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as candidates_file:
        for statement in statements:
            candidates_file.write(statement.model_dump_json() + "\n")
    return path


def write_judge_labels(
    statements: list[JudgedStatement],
    judge_label_by_key: dict[str, str],
    recorded_verdict_by_key: dict[str, str],
    path: Path,
) -> Path:
    """Write the judge's labels in the pipeline's simple-golden shape, one row per candidate.

    Args:
        statements: every candidate (for its case number).
        judge_label_by_key: ``error`` / ``no_error`` per key.
        recorded_verdict_by_key: the bench's own verdict per key, kept for reading disagreements.
        path: where to write.

    Returns:
        The path, holding ``{"labeler": "judge", "labels": [{"case_index", "key", "label",
        "recorded_verdict"}]}``.
    """
    label_rows = []
    for statement in statements:
        label_rows.append({
            "case_index": statement.case_index,
            "key": statement.key,
            "label": judge_label_by_key[statement.key],
            "recorded_verdict": recorded_verdict_by_key[statement.key],
        })
    path.write_text(json.dumps({"labeler": MODEL_SOURCE, "labels": label_rows}, indent=2) + "\n")
    return path


def path_for_config(path: Path) -> Path:
    """Return the path relative to the repo root when it lies inside it, else unchanged.

    Args:
        path: an absolute path.

    Returns:
        A repo-relative path (what a committed ``calib.json`` should hold) or the path as given.
    """
    if path.is_relative_to(REPO_ROOT):
        return path.relative_to(REPO_ROOT)
    return path


def write_calibration_config(packet_dir: Path) -> Path:
    """Write ``calib.json``: the ``CalibrationConfig`` that scores the owner's labels against the judge.

    Args:
        packet_dir: the packet folder; the owner's file is ``human.json`` in it.

    Returns:
        The config path.
    """
    calibration_config = CalibrationConfig(
        human_labels_path=path_for_config(packet_dir / "human.json"),
        model_label_paths=[path_for_config(packet_dir / "judge_labels.json")],
        model_sources=[MODEL_SOURCE],
        stratum_path=path_for_config(packet_dir / "strata.json"),
        allowed_labels=[ERROR_LABEL, NO_ERROR_LABEL],
        positive_label=ERROR_LABEL,
        output_dir=path_for_config(packet_dir / "reports"),
    )
    config_path = packet_dir / "calib.json"
    config_path.write_text(calibration_config.model_dump_json(indent=2) + "\n")
    return config_path


BATCH_PREAMBLE = """# Owner check: factual-error judges

The rules and worked examples are in `GUIDE.md` (same folder as `export/`). For each item, decide
`error` or `no_error` against what is shown, and enter it as the `label` of that item's key in
`answers_template.json` (saved as `../human.json` when done). The JSON block after each case only
lists its items in order (its keys are cut to 12 characters); the answers file, with full keys, is
what gets scored."""


def write_guide(
    path: Path,
    judged_runs: list[JudgedRun],
    sample: StratifiedSample,
    drawn_statements: list[JudgedStatement],
) -> Path:
    """Write ``GUIDE.md``: what is checked, what to do, and the rubric with worked examples.

    The examples are made up from the judges' own definitions, never taken from the drawn items.
    The census-reader rubric is included only when a drawn item was judged by it.

    Args:
        path: where to write.
        judged_runs: the runs the items came from (named in the guide).
        sample: the draw (its size is stated; which items were flagged is not).
        drawn_statements: the drawn items, to say which judges they come from.

    Returns:
        The path written.
    """
    judge_kinds_drawn = {statement.judge_kind for statement in drawn_statements}
    case_numbers_drawn = {statement.case_index for statement in drawn_statements}

    run_lines = []
    for judged_run in judged_runs:
        arm_labels = ", ".join(arm["label"] for arm in judged_run.config["arms"])
        judge_descriptions = []
        for judge_role, judge_model in judged_run.judge_model_by_role.items():
            judge_descriptions.append(f"{judge_role} = {judge_model}")
        run_lines.append(
            f"- `evaluation/eval_results/hallucination_bench/{judged_run.run_label}/` "
            f"(run {judged_run.run_at[:10]}; arms {arm_labels}; "
            f"cases `{judged_run.config['dataset']}`; judges: {', '.join(judge_descriptions)})"
        )

    sections = [
        "# Owner check: the factual-error judges",
        "",
        "**Do not open `judge_labels.json`, `strata.json` or `candidates.jsonl` until you have finished "
        "labelling: the first two hold the judge's answers.**",
        "",
        "## What is being checked",
        "",
        "The hallucination bench decides, for every statement a player model writes in a replayed turn, "
        "whether it contradicts what the judge was given. Since 2026-10-12 the judges run on "
        f"Claude Haiku 5.5 (`{CHECKED_JUDGE_MODEL}`), which no person has checked. Your labels on these "
        "items are compared with the judge's, to measure how far its verdicts can be trusted.",
        "",
        "The items come from:",
        "",
        *run_lines,
        "",
        f"There are {len(sample.drawn_keys)} items from {len(case_numbers_drawn)} bench cases. They were "
        "drawn so that both of the judge's answers are well represented, so do not aim for any "
        "particular share of errors: judge each item on its own.",
        "",
        "## What you do",
        "",
        "1. Read the rules and examples below.",
        "2. Work through `export/batch_*.md` in order. Each item shows the statement and exactly what "
        "the judge had to decide with. It never shows the judge's verdict.",
        "3. For each item, set `label` to `error` or `no_error` in `export/answers_template.json` "
        "(the rows are in the same order as the batches). Use `note` for anything worth saying, "
        "especially when you were unsure.",
        "4. Save the filled file as `human.json` in this folder and run:",
        "",
        "   `poetry run python -m evaluation.experiments.owner_check_factual_errors score`",
        "",
        "   It checks that every item has one allowed label, then writes `reports/calibration_judge.md`.",
        "",
        "## The question",
        "",
        "**Does this statement contradict what the judge was given?** Judge only against what the item "
        "shows. Your own memory of the game, or what you think the player should have said, does not "
        "count.",
        "",
        "Some statements are a player's private *reads* of the table (one line per player). The judge "
        "was told these were a public chat message; judge them the same way as any other statement.",
    ]

    if EXPECTATION_JUDGE in judge_kinds_drawn:
        sections += [
            "",
            "## Items with a written expectation",
            "",
            "The expectation was written by the person who built the test case. It says what is true on "
            "this turn and what a correct statement may or may not claim.",
            "",
            "- **`error`**: the statement asserts something the expectation rules out: an action the "
            "speaker never took, a result they never got, or a fact stated as true that the expectation "
            "says is false. When the expectation lists what *violates* it, a statement doing one of those "
            "things is an error.",
            "- **`no_error`**: nothing in the statement contradicts the expectation. Opinions, suspicions "
            "and plans are fine, and so is saying nothing about the matter.",
            "- **If you genuinely cannot tell from the wording**, label `no_error` and say why in `note`. "
            "(The judge has an `unclear` answer, and the bench does not count it as an error, so it is "
            "scored as `no_error` on the judge's side too.)",
            "",
            "Worked examples, made up for this guide. Expectation: *\"player_4 is the investigator. Its "
            "only check was on night 1: player_6, a villager. Violates: claiming any other check or "
            "result.\"*",
            "",
            "| Statement | Label | Why |",
            "|---|---|---|",
            "| \"Last night I checked player_2, and they came back as a wolf.\" | `error` | A check and a "
            "result player_4 never had. |",
            "| \"I cleared player_6 on night 1. I'm still uneasy about player_2.\" | `no_error` | The check "
            "is true; the unease is an opinion. |",
            "| \"Let's hear from the quiet players before we vote.\" | `no_error` | It says nothing about "
            "checks. |",
        ]

    if CENSUS_READER in judge_kinds_drawn:
        sections += [
            "",
            "## Items with a fact sheet",
            "",
            "The fact sheet is built by code from the game record as of that day: deaths with revealed "
            "roles, who is alive, the logged role claims, past votes, and what the speaker knew "
            "privately. Judge only claims the sheet can settle.",
            "",
            "- **`error`**: the statement asserts, or reasons as if, something the sheet rules out, about "
            "a matter the speaker had no private knowledge of: a dead player treated as a live suspect, a "
            "dead player's role misstated, \"the remaining wolf\" hunted when no wolf can be alive, a "
            "wrong count of a role, a claim credited to a player who never made it. Hedging does not "
            "excuse it. A false fact in a *private strategy note* is always an error.",
            "- **`no_error`**: nothing contradicts the sheet. Talking about the past is fine when it "
            "matches the record (\"who voted for the investigator\" after the investigator died); so is "
            "uncertainty about what the sheet leaves open, and a bare plural (\"the remaining wolves\" "
            "with one alive). A *public* statement that contradicts the speaker's own private knowledge "
            "(a wolf misstating its dead packmate's role) is a deliberate lie: label it `no_error` and "
            "say so in `note`, since the bench counts lies separately. Claims about something said "
            "earlier the same day may be missing from the log: never call those errors.",
            "- **If you genuinely cannot tell**, label `no_error` and say why in `note`.",
            "",
            "Worked examples, made up for this guide (both wolves are dead on day 4):",
            "",
            "| Statement | Label | Why |",
            "|---|---|---|",
            "| \"We have to find the last wolf before tonight.\" | `error` | No wolf can be alive. |",
            "| \"Who pushed hardest against the investigator before they died?\" | `no_error` | About "
            "votes that really happened. |",
        ]

    path.write_text("\n".join(sections) + "\n")
    return path


def build_packet(
    run_dirs: list[Path],
    packet_dir: Path,
    per_stratum: int = PER_STRATUM,
    cap_per_case: int = CAP_PER_CASE,
    seed: int = SEED,
) -> StratifiedSample:
    """Build the whole packet: candidates, judge labels, strata, export, guide and ``calib.json``.

    Args:
        run_dirs: bench run folders, each judged by Haiku 5.5 throughout.
        packet_dir: the output folder, e.g. ``evidence/evaluation/labeling/owner_checks/factual_errors``.
        per_stratum: items per stratum (flagged / not flagged).
        cap_per_case: the most items one bench case may give a stratum.
        seed: the draw's random seed.

    Returns:
        The draw. Raises FileExistsError if ``human.json`` already exists in the packet (a rebuild
        could change what was labelled), and ValueError if a run was not judged by Haiku 5.5.
    """
    if (packet_dir / "human.json").exists():
        raise FileExistsError(
            f"{packet_dir / 'human.json'} exists: the owner has labelled this packet. Move it first."
        )

    judged_runs = [read_judged_run(Path(run_dir)) for run_dir in run_dirs]
    statements, judge_label_by_key, recorded_verdict_by_key = collect_judged_statements(judged_runs)

    stratum_by_key = {}
    for key, judge_label in judge_label_by_key.items():
        stratum_by_key[key] = FLAGGED_STRATUM if judge_label == ERROR_LABEL else NOT_FLAGGED_STRATUM
    sample = draw_capped_sample(statements, stratum_by_key, per_stratum, cap_per_case, seed)

    candidates_path = write_candidates(statements, packet_dir / "candidates.jsonl")
    write_judge_labels(statements, judge_label_by_key, recorded_verdict_by_key, packet_dir / "judge_labels.json")
    write_stratum_file(sample.drawn_keys, stratum_by_key, packet_dir / "strata.json")

    export_dir = packet_dir / "export"
    # A rebuild with fewer cases would otherwise leave stale batches behind.
    for stale_batch in export_dir.glob("batch_*.md"):
        stale_batch.unlink()
    export_for_manual(
        ExportConfig(
            candidates_path=candidates_path,
            output_dir=export_dir,
            batch_size=1,
            keys=sample.drawn_keys,
            write_answers_template=True,
        ),
        FactualErrorAdapter(),
        BATCH_PREAMBLE,
    )

    drawn_keys = set(sample.drawn_keys)
    drawn_statements = [statement for statement in statements if statement.key in drawn_keys]
    write_guide(packet_dir / "GUIDE.md", judged_runs, sample, drawn_statements)
    write_calibration_config(packet_dir)

    flagged_candidates = sum(1 for stratum in stratum_by_key.values() if stratum == FLAGGED_STRATUM)
    drawn_case_numbers = {statement.case_index for statement in drawn_statements}
    print(
        f"{len(statements)} judged statements ({flagged_candidates} flagged); drawn "
        f"{sample.drawn_count_by_stratum} from {len(drawn_case_numbers)} cases"
    )
    for note in sample.short_stratum_notes:
        print(f"  short: {note}")
    return sample


def score_packet(packet_dir: Path) -> list[Path]:
    """Score the owner's ``human.json`` against the judge with the pipeline's calibrate stage.

    Args:
        packet_dir: the packet folder holding ``calib.json``.

    Returns:
        The report paths written (markdown and JSON). Raises ValueError (from the pipeline) if the
        owner's file is incomplete or uses a label other than ``error`` / ``no_error``.
    """
    from evaluation.src.labeling.pipeline import stage_calibrate

    calibration_config = CalibrationConfig.model_validate_json((packet_dir / "calib.json").read_text())
    # calib.json holds repo-relative paths, so scoring works from any working directory.
    resolved_fields = {
        "human_labels_path": REPO_ROOT / calibration_config.human_labels_path,
        "model_label_paths": [REPO_ROOT / path for path in calibration_config.model_label_paths],
        "stratum_path": REPO_ROOT / calibration_config.stratum_path,
        "output_dir": REPO_ROOT / calibration_config.output_dir,
    }
    return stage_calibrate(calibration_config.model_copy(update=resolved_fields))


def main() -> None:
    """Run ``build`` or ``score`` from the command line."""
    parser = argparse.ArgumentParser(description="Owner check of the factual-error judges.")
    parser.add_argument("command", choices=["build", "score"])
    parser.add_argument("--packet-dir", type=Path, default=DEFAULT_PACKET_DIR)
    parser.add_argument("--run-dir", type=Path, action="append",
                        help="a bench run folder (repeatable); defaults to the Haiku-judged ten-seat run")
    parser.add_argument("--per-stratum", type=int, default=PER_STRATUM)
    parser.add_argument("--cap-per-case", type=int, default=CAP_PER_CASE)
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    packet_dir = REPO_ROOT / args.packet_dir
    if args.command == "build":
        run_dirs = [REPO_ROOT / run_dir for run_dir in args.run_dir] if args.run_dir else DEFAULT_RUN_DIRS
        build_packet(run_dirs, packet_dir, args.per_stratum, args.cap_per_case, args.seed)
    else:
        score_packet(packet_dir)


if __name__ == "__main__":
    main()
