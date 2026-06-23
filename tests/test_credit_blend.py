"""Guard tests for the bussing-aware WOLF day-vote credit (B): wolf is graded by BLENDING with the
room's plurality (the validated signal — G2 day-blend r=+0.22), not by the vote target. This makes
bussing a doomed ally a POSITIVE (cover preserved), which the old 'ally=negative' rule mis-scored.
Town / SK / no-consensus fallback stay as before.
"""

from __future__ import annotations

import unittest

from evaluation.src.loop.credit_backfill import _majority_vote, _vote_credit

# player_1/2 are wolves; the rest town. score_vote only needs the votee's role to exist here.
ROLES = {"player_1": "wolf", "player_2": "wolf", "player_3": "villager", "player_9": "villager"}


class MajorityVoteTests(unittest.TestCase):
    def test_plurality_picks_top(self) -> None:
        self.assertEqual(_majority_vote({"vote_counts": {"player_3": 5, "abstain": 2}}), "player_3")

    def test_abstain_majority_counts(self) -> None:
        # voted_player is None on no-lynch days; vote_counts still carries the consensus
        self.assertEqual(_majority_vote({"vote_counts": {"abstain": 8, "player_9": 1}}), "abstain")

    def test_no_vote_is_none(self) -> None:
        self.assertIsNone(_majority_vote({"vote_counts": {}}))
        self.assertIsNone(_majority_vote({}))


class WolfBlendCreditTests(unittest.TestCase):
    def test_blend_with_room_is_positive(self) -> None:
        self.assertEqual(_vote_credit("wolf", "player_3", ROLES, majority="player_3"), "positive")

    def test_bussing_a_doomed_ally_is_positive(self) -> None:
        # the room is lynching an ally; voting the ally too = blend = correct cover (NOT negative)
        self.assertEqual(_vote_credit("wolf", "player_2", ROLES, majority="player_2"), "positive")

    def test_off_consensus_is_negative(self) -> None:
        self.assertEqual(_vote_credit("wolf", "player_3", ROLES, majority="player_9"), "negative")

    def test_blend_by_abstain_is_positive_not_neutral(self) -> None:
        # the answer to "why is blend neutral?" — it isn't: the wolf branch precedes the abstain bucket
        self.assertEqual(_vote_credit("wolf", "abstain", ROLES, majority="abstain"), "positive")

    def test_abstain_against_a_lynching_room_is_negative(self) -> None:
        self.assertEqual(_vote_credit("wolf", "abstain", ROLES, majority="player_3"), "negative")

    def test_no_consensus_falls_back_to_old_rule(self) -> None:
        self.assertEqual(_vote_credit("wolf", "player_2", ROLES, majority=None), "negative")  # ally
        self.assertEqual(_vote_credit("wolf", "player_3", ROLES, majority=None), "positive")  # townie


class NonWolfCreditUnchangedTests(unittest.TestCase):
    def test_town_scored_by_threat_regardless_of_majority(self) -> None:
        # town wants threats lynched; majority is irrelevant to town credit
        self.assertEqual(_vote_credit("villager", "player_1", ROLES, majority="player_9"), "positive")
        self.assertEqual(_vote_credit("villager", "player_3", ROLES, majority="player_3"), "negative")

    def test_sk_any_non_self_lynch_is_positive(self) -> None:
        self.assertEqual(_vote_credit("serial_killer", "player_3", ROLES, majority="player_9"), "positive")

    def test_abstain_neutral_for_town(self) -> None:
        self.assertEqual(_vote_credit("villager", "abstain", ROLES), "neutral")


if __name__ == "__main__":
    unittest.main()
