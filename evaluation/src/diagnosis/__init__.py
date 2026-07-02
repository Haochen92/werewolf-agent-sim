"""Diagnosis apparatus — tooling that decides WHICH cases a human/pro-LLM should read.

Currently: the ``sampler`` (rung ② of the eval modality ladder — sampled human review). It turns the
ad-hoc "eyeball a few cases" habit into a deterministic, recorded select -> cohort -> (guarded) replay
-> review-packet -> verdict-JSONL pipeline. See ``evidence/evaluation/sampled_human_review/``.
"""
