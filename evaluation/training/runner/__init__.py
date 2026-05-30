"""Execution backend for training jobs.

Training runs only on Modal (``modal_runner``) — the L4 GPU container imports the
engine + adapters and calls ``engine.train``. Local machines are inference-only;
use ``evaluation.training.evaluator`` to score a saved model on CPU.
"""
