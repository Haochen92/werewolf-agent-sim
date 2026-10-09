"""Role-draw seedability: the initial-condition parity the paired memory A/B relies on.

game_id is the single master seed, and the role draw derives from it. Pinning game_id across
two runs must reproduce the role assignment; distinct game_ids must (overwhelmingly) differ.
(The scheduler's seeded proactive tie-break, the seed's first user, went with the proactive
tier on 2026-10-07; the rounds that replaced it order by seat.)
"""

from __future__ import annotations

import unittest

from collections import Counter

from Agents.nodes.orchestrator import initialize_game
from Agents.schemas.roles import ALL_LINEUPS, LONE_KILLER_ROLES, NEUTRAL_ROLES, SEATS


def _deal(game_id: str, **game_config) -> dict:
    config = {"configurable": {"game_id": game_id, "game_config": game_config}}
    return initialize_game({}, config)


def _draw(game_id: str, **game_config) -> dict[str, str]:
    return _deal(game_id, **game_config)["roles"]


class RoleDrawSeedabilityTests(unittest.TestCase):
    def test_same_game_id_reproduces_role_draw(self) -> None:
        self.assertEqual(_draw("seed-abc"), _draw("seed-abc"))
        self.assertEqual(_deal("seed-abc")["lineup"], _deal("seed-abc")["lineup"])

    def test_distinct_game_ids_differ(self) -> None:
        # Not guaranteed in principle, but collision is astronomically unlikely for a
        # 10-slot shuffle across two unrelated crc32 seeds.
        self.assertNotEqual(_draw("seed-abc"), _draw("seed-different"))

    def test_full_valid_assignment(self) -> None:
        deal = _deal("seed-abc")
        roles = deal["roles"]
        self.assertEqual(SEATS, 10)
        self.assertEqual(len(roles), 10)
        self.assertEqual(sorted(roles, key=lambda p: int(p.split("_")[1])), [f"player_{i}" for i in range(1, 11)])
        # The seats hold exactly the dealt lineup, one of the four a game can deal.
        self.assertIn(deal["lineup"], ALL_LINEUPS)
        self.assertEqual(Counter(roles.values()), Counter(deal["lineup"]))

    def test_empty_game_id_unseeded_but_valid(self) -> None:
        # No game_id → unseeded (preserves prior nondeterminism); still a full draw.
        deal = _deal("")
        self.assertEqual(len(deal["roles"]), 10)
        self.assertIn(deal["lineup"], ALL_LINEUPS)

    def test_both_drawn_seats_vary_with_the_seed(self) -> None:
        lineups = [_deal(f"seed-{i}")["lineup"] for i in range(40)]
        self.assertEqual({lineup[-2] for lineup in lineups}, set(LONE_KILLER_ROLES))
        self.assertEqual({lineup[-1] for lineup in lineups}, set(NEUTRAL_ROLES))

    def test_a_chosen_drawn_seat_forces_the_draw_without_moving_the_other_seats(self) -> None:
        # The draw is made even when the config fixes it, so the shuffle after it is the same:
        # forcing the other lone killer swaps that one role and leaves every other seat alone.
        natural = _deal("seed-abc")
        other = next(r for r in LONE_KILLER_ROLES if r not in natural["lineup"])
        forced = _deal("seed-abc", lone_killer=other)
        self.assertIn(other, forced["lineup"])
        differing = [p for p in natural["roles"] if natural["roles"][p] != forced["roles"][p]]
        self.assertEqual(len(differing), 1)
        self.assertEqual(forced["roles"][differing[0]], other)


if __name__ == "__main__":
    unittest.main()
