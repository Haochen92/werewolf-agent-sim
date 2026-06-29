"""Standalone interactive human-labelling CLIs (one per domain).

These are *not* part of the generic engine+adapter pipeline. The human labels
directly in the terminal (``show`` → ``label`` → ``progress``) — no model panel
and no copy-paste export batch. Their label shapes (cluster MERGE-ops;
golden-query authoring + live-retrieval grading; summary coverage) don't fit the
per-item adapter pattern, so they live here as bespoke per-domain tools rather
than in the pipeline proper. See ``../report.md`` (mode 3) in the evidence hub.
"""
