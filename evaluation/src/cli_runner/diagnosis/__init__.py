"""CLI for the diagnosis modality (rung ② of the eval ladder — sampled human + pro-LLM review).

The sampler *logic* lives in the ``evaluation.src.diagnosis`` package (reusable/importable);
this subpackage is only its command wiring, mirroring the ``regen_replay/judge`` (CLI) ↔
``judges/`` (logic) split. ``case_sampler`` selects an outcome-blind review cohort off real
local sidecar data ($0) and renders review packets + a verdict scaffold.
"""
