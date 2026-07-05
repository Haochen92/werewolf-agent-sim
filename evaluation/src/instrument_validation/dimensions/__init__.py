"""Situation-dimension validation — are the v6 dims accurate enough to gate retrieval on?

``dimension_audit`` scores each query-side fill against the deterministically-knowable truth from the
case's own board; ``dimension_gating_screen`` re-tests whether soft dimension-gating cuts the
not-relevant retrieval waste (concluded negative, then RE-OPENED by the audit → standing-again).
"""
