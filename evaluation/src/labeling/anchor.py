"""Choosing what a person labels: a seeded stratified draw of item keys, and the sample size
needed for a given precision on the agreement rate.

The draw's keys feed ``ExportConfig.keys`` (what the person sees) and its stratum file feeds
``CalibrationConfig.stratum_path`` (how the agreement is broken down afterwards).
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path
from statistics import NormalDist

from evaluation.src.labeling.schemas import StratifiedSample


def draw_stratified_sample(
    candidate_keys: list[str],
    stratum_by_key: dict[str, str],
    per_stratum: int,
    seed: int,
) -> StratifiedSample:
    """Draw up to ``per_stratum`` keys at random from each stratum, reproducibly for a seed.

    The draw depends only on the set of candidates, their strata and the seed: the order of
    ``candidate_keys`` does not matter, and adding a new stratum does not change what is drawn
    from the existing ones.

    Args:
        candidate_keys: every item key that may be drawn, e.g. ``["g3:12", "g3:14", "g4:2"]``.
            Duplicates are ignored.
        stratum_by_key: the stratum of each candidate, e.g. ``{"g3:12": "flagged", ...}``. Every
            candidate must have one.
        per_stratum: how many keys to draw from each stratum (at least 1).
        seed: the random seed.

    Returns:
        The drawn keys sorted by key, the count drawn per stratum, and a note for each stratum
        that had fewer candidates than ``per_stratum`` (all of its candidates are then drawn).
        Raises ValueError if ``per_stratum`` is below 1 or a candidate has no stratum.
    """
    if per_stratum < 1:
        raise ValueError(f"per_stratum must be at least 1, got {per_stratum}")

    keys_without_stratum = sorted(key for key in set(candidate_keys) if key not in stratum_by_key)
    if keys_without_stratum:
        raise ValueError(f"Candidate keys with no stratum: {keys_without_stratum}")

    keys_by_stratum: dict[str, list[str]] = {}
    for key in sorted(set(candidate_keys)):
        keys_by_stratum.setdefault(stratum_by_key[key], []).append(key)

    drawn_keys: list[str] = []
    drawn_count_by_stratum: dict[str, int] = {}
    short_stratum_notes: list[str] = []
    for stratum in sorted(keys_by_stratum):
        stratum_keys = keys_by_stratum[stratum]
        if len(stratum_keys) < per_stratum:
            short_stratum_notes.append(
                f"{stratum}: asked for {per_stratum}, only {len(stratum_keys)} candidates"
            )
        # One generator per stratum, seeded by seed and stratum name, so strata draw independently.
        stratum_rng = random.Random(f"{seed}:{stratum}")
        stratum_draw = stratum_rng.sample(stratum_keys, min(per_stratum, len(stratum_keys)))
        drawn_keys.extend(stratum_draw)
        drawn_count_by_stratum[stratum] = len(stratum_draw)

    # Sorted by key rather than grouped by stratum: a grouped order would tell the person
    # which items the model flagged.
    return StratifiedSample(
        drawn_keys=sorted(drawn_keys),
        drawn_count_by_stratum=drawn_count_by_stratum,
        short_stratum_notes=short_stratum_notes,
    )


def write_stratum_file(
    drawn_keys: list[str], stratum_by_key: dict[str, str], path: Path
) -> Path:
    """Write the stratum of each drawn key as a JSON object, the file ``CalibrationConfig.stratum_path`` reads.

    Args:
        drawn_keys: the keys the person will label, e.g. ``StratifiedSample.drawn_keys``.
        stratum_by_key: the stratum of each key (may hold more keys than were drawn).
        path: where to write the file.

    Returns:
        The path written, holding e.g. ``{"g3:12": "flagged", "g4:2": "unflagged"}``.
        Raises KeyError if a drawn key has no stratum.
    """
    drawn_stratum_by_key = {key: stratum_by_key[key] for key in drawn_keys}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(drawn_stratum_by_key, indent=2, sort_keys=True) + "\n")
    return path


def read_stratum_file(path: Path) -> dict[str, str]:
    """Read a stratum file written by ``write_stratum_file``.

    Args:
        path: the JSON file, an object mapping item key to stratum name.

    Returns:
        The stratum of each key, e.g. ``{"g3:12": "flagged"}``. Raises ValueError if the file is
        not a JSON object of strings.
    """
    stratum_by_key = json.loads(Path(path).read_text())
    if not isinstance(stratum_by_key, dict):
        raise ValueError(f"Stratum file must hold a JSON object (key -> stratum): {path}")
    for key, stratum in stratum_by_key.items():
        if not isinstance(stratum, str):
            raise ValueError(f"Stratum of key {key!r} must be a string, got {stratum!r}: {path}")
    return stratum_by_key


def sample_size_for_ci(
    half_width: float, expected_agreement: float = 0.8, confidence: float = 0.95
) -> int:
    """Return how many labelled items give an agreement interval of ± ``half_width``.

    Uses the normal approximation n = z² · p · (1 − p) / h², rounded up, where p is the
    expected agreement rate and z the two-sided normal quantile for ``confidence``.
    At p = 0.8 and 95%: ±10% → 62, ±8% → 97, ±5% → 246.

    Args:
        half_width: the wanted half-width of the interval, as a proportion (0.08 for ±8%).
        expected_agreement: the agreement rate you expect to see (0.8 = 80%).
        confidence: the interval's confidence level.

    Returns:
        The number of items. Raises ValueError if an argument is outside (0, 1).
    """
    for argument_name, argument_value in (
        ("half_width", half_width),
        ("expected_agreement", expected_agreement),
        ("confidence", confidence),
    ):
        if not 0.0 < argument_value < 1.0:
            raise ValueError(
                f"{argument_name} must be between 0 and 1 (exclusive), got {argument_value}"
            )

    z_score = NormalDist().inv_cdf(1 - (1 - confidence) / 2)
    exact_size = z_score**2 * expected_agreement * (1 - expected_agreement) / half_width**2
    # Round off float noise first, so a size that is exactly whole is not pushed up by one.
    return math.ceil(round(exact_size, 9))
