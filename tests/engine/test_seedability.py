"""Role-draw seedability: the initial-condition parity the paired memory A/B relies on.

game_id is the single master seed — the scheduler's turn-order tie-break already derives
from it (cycle_seed), and the role draw now does too. Pinning game_id across two runs must
reproduce the role assignment; distinct game_ids must (overwhelmingly) differ.
"""

from __future__ import annotations

import unittest

from Agents.nodes.orchestrator import initialize_game


def _draw(game_id: str) -> dict[str, str]:
    config = {"configurable": {"game_id": game_id, "game_config": {}}}
    return initialize_game({}, config)["roles"]


class RoleDrawSeedabilityTests(unittest.TestCase):
    def test_same_game_id_reproduces_role_draw(self) -> None:
        self.assertEqual(_draw("seed-abc"), _draw("seed-abc"))

    def test_distinct_game_ids_differ(self) -> None:
        # Not guaranteed in principle, but collision is astronomically unlikely for a
        # 9-slot shuffle across two unrelated crc32 seeds.
        self.assertNotEqual(_draw("seed-abc"), _draw("seed-different"))

    def test_full_valid_assignment(self) -> None:
        roles = _draw("seed-abc")
        self.assertEqual(len(roles), 9)
        self.assertEqual(sorted(roles), [f"player_{i}" for i in range(1, 10)])

    def test_empty_game_id_unseeded_but_valid(self) -> None:
        # No game_id → unseeded (preserves prior nondeterminism); still a full draw.
        roles = _draw("")
        self.assertEqual(len(roles), 9)


if __name__ == "__main__":
    unittest.main()
