"""Multi-model consensus labeling pipeline.

Provides a reusable, config-driven framework for labeling data with multiple
LLM models, merging with human labels, and resolving disagreements via voting.

Domain-specific behavior is plugged in via ``LabelingAdapter`` subclasses.
"""
