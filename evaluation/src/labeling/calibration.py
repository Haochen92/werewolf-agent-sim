"""The acceptance test: how well a model label source agrees with a person's labels.

Reads and validates the person's label file, compares one model source with it (taking the
person as the truth), applies the acceptance gate, and writes a markdown + JSON report.
Label files are read with the pipeline's own loader, so the same files ``pipeline consolidate``
reads work here unchanged. Labels are compared as text (a label of 2 is read as "2").
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

from evaluation.src.core.stats import binomial_ci, cohens_kappa, mcnemar_exact
from evaluation.src.labeling.config import CalibrationConfig
from evaluation.src.labeling.pipeline import Key, load_voters
from evaluation.src.labeling.schemas import (
    BiasTest,
    CalibrationReport,
    Disagreement,
    GateCondition,
    LabelRow,
    StratumAgreement,
)

ALL_ITEMS_STRATUM = "all"
"""The stratum every item is in when no stratum file is given."""
MISSING_STRATUM = "(no stratum)"
"""The stratum of an item the stratum file does not list."""


def read_human_labels(
    path: Path, expected_keys: list[str] | None, allowed_labels: list[str] | None
) -> dict[str, str]:
    """Load a person's label file and check it is complete and clean.

    Every problem is collected before raising, so one run lists everything to fix.

    Args:
        path: the label file, in the simple-golden shape
            ``{"labeler": "owner", "labels": [{"case_index": 0, "key": "g3:12", "label": "accuse", "note": ""}]}``.
        expected_keys: the keys the person was asked to label, e.g. the anchor draw's keys. Every
            one must be labelled and no other key may appear. None skips both checks.
        allowed_labels: the labels the person may use, e.g. ``["accuse", "none"]``. None accepts
            any non-empty label.

    Returns:
        The person's label for each key, e.g. ``{"g3:12": "accuse"}``. Raises ValueError listing
        every problem found: a missing or repeated key, an unknown key, a row with no key or
        case_index, an empty label, or a label outside ``allowed_labels``.
    """
    file_content = json.loads(Path(path).read_text())
    if not isinstance(file_content, dict) or "labels" not in file_content:
        raise ValueError(f"Human label file must be an object with a 'labels' list: {path}")

    # The pipeline loader keeps only the last row per key, so duplicates are counted here first.
    problems: list[str] = []
    times_labelled_by_key: Counter[str] = Counter()
    for row_number, label_row in enumerate(file_content["labels"], start=1):
        if label_row.get("key") is None:
            problems.append(f"row {row_number}: no key")
            continue
        key = str(label_row["key"])
        times_labelled_by_key[key] += 1
        if "case_index" not in label_row:
            problems.append(f"row {row_number} (key {key!r}): no case_index")
        human_label = _label_text(label_row.get("label"))
        if human_label is None:
            problems.append(f"key {key!r}: empty label")
        elif allowed_labels is not None and human_label not in allowed_labels:
            problems.append(f"key {key!r}: label {human_label!r} is not one of {allowed_labels}")

    for key, times_labelled in sorted(times_labelled_by_key.items()):
        if times_labelled > 1:
            problems.append(f"key {key!r}: labelled {times_labelled} times")

    if expected_keys is not None:
        for key in sorted(set(expected_keys) - set(times_labelled_by_key)):
            problems.append(f"key {key!r}: not labelled")
        for key in sorted(set(times_labelled_by_key) - set(expected_keys)):
            problems.append(f"key {key!r}: not one of the expected keys")

    if problems:
        problem_lines = "\n".join(f"  - {problem}" for problem in problems)
        raise ValueError(f"Human label file {path} has {len(problems)} problem(s):\n{problem_lines}")

    voters, _, _ = load_voters(path)
    # A simple-golden file holds one labeller, so the loader returns one column.
    human_column = list(voters.values())[0]
    return _labels_by_item_key(human_column, source_name=f"human labels {path}")


def load_model_labels(model_label_paths: list[Path], model_source: str) -> dict[str, str]:
    """Collect one model source's labels from one or more label files.

    Args:
        model_label_paths: label files in either shape the pipeline loader reads (engine output,
            where each model is a source, or simple golden, where the ``labeler`` is the source).
        model_source: the source to collect, e.g. ``"echo_gate"``.

    Returns:
        The source's label for each key, e.g. ``{"g3:12": "none"}``. Items the source left
        unlabelled (a null label) are absent. Raises ValueError if no file holds the source, or
        if one key appears under two different case indices.
    """
    merged_column: dict[Key, object] = {}
    sources_found: set[str] = set()
    for label_path in model_label_paths:
        voters, _, _ = load_voters(label_path)
        sources_found.update(voters)
        if model_source in voters:
            merged_column.update(voters[model_source])

    if model_source not in sources_found:
        raise ValueError(
            f"Model source {model_source!r} is in none of {[str(p) for p in model_label_paths]}; "
            f"sources found: {sorted(sources_found)}"
        )
    return _labels_by_item_key(merged_column, source_name=model_source)


def calibrate(
    human_labels: dict[str, str],
    model_labels: dict[str, str],
    stratum_by_key: dict[str, str] | None,
    model_source: str,
    config: CalibrationConfig,
) -> CalibrationReport:
    """Compare one model source's labels with a person's, taking the person as the truth.

    Only items both labelled are compared; keys the person labelled but the model did not are
    listed in the report and left out of every number.

    Args:
        human_labels: the person's label per key, e.g. ``{"g3:12": "accuse"}``
            (from ``read_human_labels``).
        model_labels: the model's label per key, same shape (from ``load_model_labels``).
        stratum_by_key: the stratum of each key, e.g. ``{"g3:12": "flagged"}``; None puts every
            item in one stratum.
        model_source: the model source's name, written into the report.
        config: supplies ``allowed_labels``, ``positive_label`` and the gate thresholds.

    Returns:
        The calibration report with the gate's verdict. Raises ValueError if no item was
        labelled by both.
    """
    compared_keys: list[str] = []
    keys_without_model_label: list[str] = []
    for key in sorted(human_labels):
        if key in model_labels:
            compared_keys.append(key)
        else:
            keys_without_model_label.append(key)
    if not compared_keys:
        raise ValueError(f"No item is labelled by both the person and {model_source!r}")

    human_column = [human_labels[key] for key in compared_keys]
    model_column = [model_labels[key] for key in compared_keys]
    items = len(compared_keys)
    agreeing_items = 0
    for human_label, model_label in zip(human_column, model_column):
        if human_label == model_label:
            agreeing_items += 1
    agreement_rate = agreeing_items / items
    agreement_ci = binomial_ci(agreeing_items, items)

    labels = _ordered_labels(config.allowed_labels, human_column + model_column)
    confusion: dict[str, dict[str, int]] = {}
    for human_label in labels:
        confusion[human_label] = {model_label: 0 for model_label in labels}
    for human_label, model_label in zip(human_column, model_column):
        confusion[human_label][model_label] += 1

    stratum_rows = _agreement_by_stratum(compared_keys, human_labels, model_labels, stratum_by_key)

    disagreements: list[Disagreement] = []
    for key in compared_keys:
        if human_labels[key] != model_labels[key]:
            disagreements.append(
                Disagreement(
                    key=key,
                    stratum=_stratum_of(key, stratum_by_key),
                    human_label=human_labels[key],
                    model_label=model_labels[key],
                )
            )

    bias_test, bias_test_skipped_reason = _run_bias_test(
        human_column, model_column, labels, config.positive_label
    )
    gate = _check_gate(agreement_rate, agreement_ci[0], bias_test, config)
    accepted = all(condition.status != "failed" for condition in gate)

    return CalibrationReport(
        model_source=model_source,
        items=items,
        agreeing_items=agreeing_items,
        agreement_rate=agreement_rate,
        agreement_ci=agreement_ci,
        cohens_kappa=cohens_kappa(human_column, model_column),
        confusion=confusion,
        label_rows=_label_rows(labels, confusion),
        stratum_rows=stratum_rows,
        disagreements=disagreements,
        bias_test=bias_test,
        bias_test_skipped_reason=bias_test_skipped_reason,
        keys_without_model_label=keys_without_model_label,
        gate=gate,
        accepted=accepted,
    )


def write_calibration_report(report: CalibrationReport, out_dir: Path) -> tuple[Path, Path]:
    """Write a calibration report as a short markdown summary and a full JSON file.

    Args:
        report: the report from ``calibrate``.
        out_dir: the directory to write into (created if missing).

    Returns:
        ``(markdown_path, json_path)``, named ``calibration_<model source>.md`` / ``.json``
        (characters other than letters, digits, ``-``, ``_`` and ``.`` become ``_``).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    file_stem = "calibration_" + re.sub(r"[^A-Za-z0-9_.-]", "_", report.model_source)
    markdown_path = out_dir / f"{file_stem}.md"
    json_path = out_dir / f"{file_stem}.json"
    markdown_path.write_text(_render_markdown(report))
    json_path.write_text(report.model_dump_json(indent=2) + "\n")
    return markdown_path, json_path


def _label_text(raw_label: object) -> str | None:
    """Return a label as stripped text, or None when it is missing or blank.

    Args:
        raw_label: a label as read from JSON, e.g. ``"accuse"``, ``2`` or ``None``.

    Returns:
        The label text (``2`` becomes ``"2"``), or None for a null or whitespace-only label.
    """
    if raw_label is None:
        return None
    label_text = str(raw_label).strip()
    return label_text or None


def _labels_by_item_key(column: dict[Key, object], source_name: str) -> dict[str, str]:
    """Re-key one loader column from ``(case_index, key)`` to the item key alone.

    Calibration, the anchor draw and the export filter all name an item by its key, so a key
    must mean one item across all cases.

    Args:
        column: one source's labels from ``load_voters``, e.g. ``{(3, "g3:12"): "accuse"}``.
        source_name: the source's name, used in the error message.

    Returns:
        The label text per key, leaving out null or blank labels. Raises ValueError if a key
        appears under two different case indices.
    """
    labels_by_key: dict[str, str] = {}
    case_index_by_key: dict[str, int] = {}
    for (case_index, key), raw_label in column.items():
        if key in case_index_by_key and case_index_by_key[key] != case_index:
            raise ValueError(
                f"{source_name}: key {key!r} appears under case {case_index_by_key[key]} and "
                f"case {case_index}; calibration needs keys that are unique across cases"
            )
        case_index_by_key[key] = case_index
        label_text = _label_text(raw_label)
        if label_text is not None:
            labels_by_key[key] = label_text
    return labels_by_key


def _ordered_labels(allowed_labels: list[str] | None, used_labels: list[str]) -> list[str]:
    """Return the labels to tabulate: the allowed labels in their given order, then any other used label, sorted.

    Args:
        allowed_labels: the configured labels, or None.
        used_labels: every label the person or the model used.

    Returns:
        The labels, each once, e.g. ``["accuse", "none"]``.
    """
    ordered_labels = list(allowed_labels or [])
    for label in sorted(set(used_labels)):
        if label not in ordered_labels:
            ordered_labels.append(label)
    return ordered_labels


def _stratum_of(key: str, stratum_by_key: dict[str, str] | None) -> str:
    """Return an item's stratum.

    Args:
        key: the item key.
        stratum_by_key: the stratum map, or None when no strata were given.

    Returns:
        The stratum name; ``ALL_ITEMS_STRATUM`` without a map, ``MISSING_STRATUM`` if the map
        lacks the key.
    """
    if stratum_by_key is None:
        return ALL_ITEMS_STRATUM
    return stratum_by_key.get(key, MISSING_STRATUM)


def _agreement_by_stratum(
    compared_keys: list[str],
    human_labels: dict[str, str],
    model_labels: dict[str, str],
    stratum_by_key: dict[str, str] | None,
) -> list[StratumAgreement]:
    """Return the agreement rate within each stratum.

    Args:
        compared_keys: the keys both the person and the model labelled.
        human_labels: the person's label per key.
        model_labels: the model's label per key.
        stratum_by_key: the stratum map, or None.

    Returns:
        One row per stratum present among ``compared_keys``, sorted by stratum name.
    """
    items_by_stratum: Counter[str] = Counter()
    agreeing_by_stratum: Counter[str] = Counter()
    for key in compared_keys:
        stratum = _stratum_of(key, stratum_by_key)
        items_by_stratum[stratum] += 1
        if human_labels[key] == model_labels[key]:
            agreeing_by_stratum[stratum] += 1

    stratum_rows: list[StratumAgreement] = []
    for stratum in sorted(items_by_stratum):
        stratum_rows.append(
            StratumAgreement(
                stratum=stratum,
                items=items_by_stratum[stratum],
                agreeing_items=agreeing_by_stratum[stratum],
                agreement_rate=agreeing_by_stratum[stratum] / items_by_stratum[stratum],
            )
        )
    return stratum_rows


def _label_rows(labels: list[str], confusion: dict[str, dict[str, int]]) -> list[LabelRow]:
    """Return one row per label with the person's and model's counts and the model's precision/recall.

    Args:
        labels: the labels to report, in order.
        confusion: person label → model label → count, holding every pair of ``labels``.

    Returns:
        One ``LabelRow`` per label, in the order of ``labels``.
    """
    label_rows: list[LabelRow] = []
    for label in labels:
        human_count = sum(confusion[label].values())
        model_count = 0
        for human_label in labels:
            model_count += confusion[human_label][label]
        both_count = confusion[label][label]
        label_rows.append(
            LabelRow(
                label=label,
                human_count=human_count,
                model_count=model_count,
                both_count=both_count,
                precision=both_count / model_count if model_count else None,
                recall=both_count / human_count if human_count else None,
            )
        )
    return label_rows


def _run_bias_test(
    human_column: list[str],
    model_column: list[str],
    labels: list[str],
    positive_label: str | None,
) -> tuple[BiasTest | None, str | None]:
    """Test whether the model calls the positive label more or less often than the person.

    Exact McNemar on the paired "person said positive" / "model said positive" outcomes: only
    the items where they differ count, and a lopsided split between misses and false alarms is
    a directional bias.

    Args:
        human_column: the person's labels, one per compared item.
        model_column: the model's labels for the same items, in the same order.
        labels: every label in play (allowed or used).
        positive_label: the label counted as positive, or None.

    Returns:
        ``(bias_test, None)`` when the test ran, or ``(None, reason)`` when it was skipped
        because no positive label is set, the labels are not exactly two, or the positive label
        is not one of them.
    """
    if positive_label is None:
        return None, "no positive label configured"
    if len(labels) != 2:
        return None, f"labels are not binary ({len(labels)} labels: {labels})"
    if positive_label not in labels:
        return None, f"positive label {positive_label!r} is not one of the labels {labels}"

    human_positive = [1 if human_label == positive_label else 0 for human_label in human_column]
    model_positive = [1 if model_label == positive_label else 0 for model_label in model_column]
    mcnemar = mcnemar_exact(off=human_positive, on=model_positive)
    bias_test = BiasTest(
        positive_label=positive_label,
        human_positive_rate=mcnemar.off_rate,
        model_positive_rate=mcnemar.on_rate,
        human_only_positive=mcnemar.b_off_only,
        model_only_positive=mcnemar.c_on_only,
        p_value=mcnemar.p_value,
    )
    return bias_test, None


def _check_gate(
    agreement_rate: float,
    ci_lower_bound: float,
    bias_test: BiasTest | None,
    config: CalibrationConfig,
) -> list[GateCondition]:
    """Apply the acceptance gate: enough agreement, a tight enough interval, no directional bias.

    Args:
        agreement_rate: the observed agreement rate.
        ci_lower_bound: the lower bound of its 95% interval.
        bias_test: the bias test, or None when it was skipped (that condition is then
            ``not_applicable`` and does not fail the gate).
        config: supplies ``min_agreement``, ``min_ci_lower`` and ``bias_alpha``.

    Returns:
        Three conditions, in order: ``agreement``, ``ci_lower_bound``, ``no_directional_bias``.
    """
    agreement_passed = agreement_rate >= config.min_agreement
    ci_passed = ci_lower_bound >= config.min_ci_lower
    gate = [
        GateCondition(
            name="agreement",
            threshold=config.min_agreement,
            observed=agreement_rate,
            status="passed" if agreement_passed else "failed",
            explanation=(
                f"agreement {agreement_rate:.1%} {'>=' if agreement_passed else '<'} "
                f"{config.min_agreement:.1%}"
            ),
        ),
        GateCondition(
            name="ci_lower_bound",
            threshold=config.min_ci_lower,
            observed=ci_lower_bound,
            status="passed" if ci_passed else "failed",
            explanation=(
                f"95% interval lower bound {ci_lower_bound:.1%} {'>=' if ci_passed else '<'} "
                f"{config.min_ci_lower:.1%}"
            ),
        ),
    ]

    if bias_test is None:
        gate.append(
            GateCondition(
                name="no_directional_bias",
                threshold=config.bias_alpha,
                observed=None,
                status="not_applicable",
                explanation="bias test skipped",
            )
        )
        return gate

    bias_passed = bias_test.p_value >= config.bias_alpha
    explanation = (
        f"McNemar p = {bias_test.p_value:.3f} {'>=' if bias_passed else '<'} {config.bias_alpha} "
        f"(false alarms: {bias_test.model_only_positive}, misses: {bias_test.human_only_positive})"
    )
    # A direction is only a finding when the split is significant.
    if not bias_passed:
        if bias_test.model_only_positive > bias_test.human_only_positive:
            explanation += f": the model says {bias_test.positive_label!r} more often than the person"
        else:
            explanation += f": the model says {bias_test.positive_label!r} less often than the person"
    gate.append(
        GateCondition(
            name="no_directional_bias",
            threshold=config.bias_alpha,
            observed=bias_test.p_value,
            status="passed" if bias_passed else "failed",
            explanation=explanation,
        )
    )
    return gate


def _render_markdown(report: CalibrationReport) -> str:
    """Render a calibration report as markdown: verdict and headline numbers first, then the tables.

    Args:
        report: the report from ``calibrate``.

    Returns:
        The markdown text.
    """
    verdict = "ACCEPT" if report.accepted else "REJECT"
    ci_low, ci_high = report.agreement_ci
    lines = [
        f"# Calibration: {report.model_source} vs the person",
        "",
        f"**Verdict: {verdict}**",
        "",
        f"- Items compared: {report.items} ({report.agreeing_items} agree)",
        f"- Agreement: {report.agreement_rate:.1%} (95% interval {ci_low:.1%} to {ci_high:.1%})",
        f"- Cohen's kappa: {report.cohens_kappa:.2f}",
    ]
    if report.bias_test is not None:
        lines.append(
            f"- Saying {report.bias_test.positive_label!r}: person "
            f"{report.bias_test.human_positive_rate:.1%}, model {report.bias_test.model_positive_rate:.1%}"
        )
    else:
        lines.append(f"- Bias test skipped: {report.bias_test_skipped_reason}")
    if report.keys_without_model_label:
        lines.append(
            f"- Left out, no model label: {len(report.keys_without_model_label)} "
            f"({', '.join(report.keys_without_model_label)})"
        )

    lines += ["", "## Gate", "", "| Condition | Result | Detail |", "|---|---|---|"]
    for condition in report.gate:
        lines.append(f"| {condition.name} | {condition.status} | {condition.explanation} |")

    lines += [
        "",
        "## Per label",
        "",
        "| Label | Person | Model | Both | Precision | Recall |",
        "|---|---|---|---|---|---|",
    ]
    for label_row in report.label_rows:
        precision_text = "–" if label_row.precision is None else f"{label_row.precision:.1%}"
        recall_text = "–" if label_row.recall is None else f"{label_row.recall:.1%}"
        lines.append(
            f"| {label_row.label} | {label_row.human_count} | {label_row.model_count} | "
            f"{label_row.both_count} | {precision_text} | {recall_text} |"
        )

    labels = list(report.confusion)
    lines += [
        "",
        "## Confusion (rows: person, columns: model)",
        "",
        "| Person \\ Model | " + " | ".join(labels) + " |",
        "|---|" + "---|" * len(labels),
    ]
    for human_label in labels:
        counts = [str(report.confusion[human_label][model_label]) for model_label in labels]
        lines.append(f"| {human_label} | " + " | ".join(counts) + " |")

    lines += ["", "## Agreement per stratum", "", "| Stratum | Items | Agree | Rate |", "|---|---|---|---|"]
    for stratum_row in report.stratum_rows:
        lines.append(
            f"| {stratum_row.stratum} | {stratum_row.items} | {stratum_row.agreeing_items} | "
            f"{stratum_row.agreement_rate:.1%} |"
        )

    lines += ["", f"## Disagreements ({len(report.disagreements)})", ""]
    if report.disagreements:
        lines += ["| Key | Stratum | Person | Model |", "|---|---|---|---|"]
        for disagreement in report.disagreements:
            lines.append(
                f"| {disagreement.key} | {disagreement.stratum} | "
                f"{disagreement.human_label} | {disagreement.model_label} |"
            )
    else:
        lines.append("None.")
    return "\n".join(lines) + "\n"
