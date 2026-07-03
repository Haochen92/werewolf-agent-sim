"""Frozen eval-set builders — freeze captured cases into replayable JSONL datasets.

One builder per case type (parallels ``data/converters/``): agent-decision
``EvalCase`` sets, extraction sets, dedup sets. Each is wired as an
``eval-build-*`` console script and writes a ``<id>.jsonl`` + ``<id>.manifest.json``
pair under ``evaluation/frozen_eval_sets/``.
"""
