"""Level 5 of the deduction engine: public events and what they imply (Agents/deduction/public/;
rows B1–B33 of evidence/reasoning_failures/deduction_catalogue.md, Table B).

Every game here runs through the real engine: each night through the resolution node, each lynch
through the day-resolution node, so the mornings and the wills are the ones a game commits. Per row:
a game where it fires, with the exact sentence; games that differ in one respect where it must not
fire or must say less (bodies, the living against the reanimated conceal, self-bets, deaths on the
same night, a will before its reveal, a payload with no morning). Then the leak boundary (the items
are the same for every seat and use nothing private) and soundness over 20,000 random nights: every
fact an item states holds in the real game.
"""

from __future__ import annotations

import random

from Agents.config.game import GameConfig
from Agents.deduction import own_result_lines, public_items, public_record, seat_view_from_payload
from Agents.deduction.public.wills import will_items
from Agents.schemas.deduction import (
    AttacksOnlyOn,
    BlockedBy,
    PublicRecord,
    RoleIn,
    SilentAttack,
)
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import cast_role_counts
from tests.engine.deduction.test_own_results import _game
from tests.factories.random_nights import (
    lynch_through_the_node,
    public_fact_holds,
    random_game,
    resolve_through_the_node,
)


class Story:
    """A constructed game in a fixed seat order (player_1 the Investigator, player_2 the Sentinel,
    player_3 the Trailseer, player_4 the Vigilante, player_5 the Sigilist, player_6 the Healer,
    player_7 the Chanteuse, player_8 the Illusionist, player_9 the lone killer, player_10 the
    neutral), each night and lynch through the real nodes."""

    def __init__(self, killer: str, neutral: str):
        self.roles, self.of = _game(killer, neutral)
        self.counts = cast_role_counts(self.roles)
        self.uses = {role: n for role, n in GameConfig().starting_uses().items() if role in self.counts}
        self.dead, self.records, self.mornings, self.wills = [], [], [], []

    def act(self, role: str, kind: str, target_role: str | None, via: str | None = None) -> NightChoice:
        target = self.of.get(target_role, target_role)
        return NightChoice(self.of[role], role, kind, target, via=self.of[via] if via else None)

    def night(self, night: int, *choices: NightChoice) -> Story:
        alive = [p for p in self.roles if p not in {d.player for d in self.dead}]
        update = resolve_through_the_node(list(choices), self.roles, night, alive, earlier_records=self.records,
                                          uses_left=self.uses)
        self.records += update["night_actions"]
        self.dead += update.get("dead_roster", [])
        self.mornings += update["night_announcements"]
        self.wills += update["read_out_wills"]
        self.uses = update["uses_left"]
        return self

    def lynch(self, role: str, day: int) -> Story:
        update = lynch_through_the_node(self.of[role], self.roles, day, self.dead, self.records)
        self.dead += update["dead_roster"]
        self.wills += update["read_out_wills"]
        return self

    def public(self, without_mornings: bool = False) -> PublicRecord:
        return PublicRecord(cast_role_counts=self.counts, dead_roster=list(self.dead),
                            announcements=[] if without_mornings else list(self.mornings), wills=list(self.wills))

    def texts(self, row: str, **kw) -> list[str]:
        return [item.text for item in public_items(self.public(**kw)) if row in item.row.split("+")]


def _sk_sp() -> Story:
    return Story("serial_killer", "speculator")


def _ne_sp() -> Story:
    return Story("necromancer", "speculator")


# --- B1, B2: killed by the wolves, revealed or hidden by the living Illusionist ----------------

def test_a_wolf_kill_shows_the_wolf_at_the_door_and_no_protection():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "kill", "sentinel"))
    assert story.texts("B1") == [
        "A wolf went to player_2 on night 1 to attack them, and a watch on player_2 that night would have shown "
        "that visit.",
        "No protection went ahead on player_2 on night 1: one would have saved player_2.",
    ]


def test_a_kill_hidden_by_the_living_illusionist_hides_the_killer_and_narrows_the_body():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "kill", "sentinel"), story.act("illusionist", "conceal", None))
    assert story.texts("B1") == []
    assert story.texts("B2") == [
        "The wolf who killed player_2 on night 1 went to player_2 unseen: the living Illusionist's conceal hides "
        "that visit from every watch and follow.",
        "player_2's role was hidden by the living Illusionist, so the Illusionist was alive at the start of night "
        "1 and went to player_2 that night.",
        "player_2 was killed at night, so player_2 is not the Serial Killer. The wolves attacked player_2, so "
        "player_2 is not a wolf.",
        "No protection went ahead on player_2 on night 1: one would have saved player_2.",
    ]
    role_item = next(item for item in public_items(story.public()) if isinstance(item.conclusion[0], RoleIn))
    assert role_item.conclusion[0].roles == frozenset(
        {"investigator", "sentinel", "trailseer", "vigilante", "sigilist", "healer", "speculator"})


def test_a_hidden_body_on_night_one_in_the_necromancer_casts_is_not_the_necromancer_and_later_may_be():
    story = _ne_sp()
    story.night(1, story.act("chanteuse", "kill", "sentinel"), story.act("illusionist", "conceal", None))
    assert ("player_2 was killed at night, so player_2 is not the Necromancer (it cannot be killed on night 1). "
            "The wolves attacked player_2, so player_2 is not a wolf.") in story.texts("B2")
    later = _ne_sp()
    later.night(2, later.act("illusionist", "kill", "sentinel"), later.act("illusionist", "conceal", None))
    assert "The wolves attacked player_2, so player_2 is not a wolf." in later.texts("B2")


# --- B3, B4: the Serial Killer's and the Vigilante's attacks --------------------------------------

def test_the_serial_killer_and_the_vigilante_are_seen_at_their_victims():
    story = _sk_sp()
    story.night(2, story.act("serial_killer", "kill", "investigator"), story.act("vigilante", "kill", "trailseer"),
                story.act("chanteuse", "kill", "healer"))
    assert story.texts("B3")[0] == ("The Serial Killer went to player_1 on night 2 to attack them, and a watch on "
                                    "player_1 that night would have shown that visit.")
    assert story.texts("B4")[0] == ("The Vigilante went to player_3 on night 2 to shoot them, and a watch on "
                                    "player_3 that night would have shown that visit.")


# --- B5, B10: what a sigil's strike shows about the attacker --------------------------------------

def test_a_vigilante_struck_down_by_a_sigil_shot_someone_and_its_shot_was_announced():
    story = _sk_sp()
    story.night(2, story.act("vigilante", "kill", "trailseer"), story.act("sigilist", "sigil", "vigilante"),
                story.act("chanteuse", "kill", "healer"))
    texts = story.texts("B5")
    assert texts == [
        "The Sigilist went to player_4 on night 2 to set a sigil on them, and a watch on player_4 that night would "
        "have shown that visit.",
        "The Vigilante is struck by a sigil only when it shoots, so player_4 shot someone on night 2.",
        "No protection went ahead on player_4 on night 2: one would have saved player_4.",
    ]


def test_a_vigilante_struck_down_whose_shot_was_not_announced_shot_the_serial_killer():
    story = _sk_sp()
    story.night(2, story.act("vigilante", "kill", "serial_killer"), story.act("sigilist", "sigil", "vigilante"),
                story.act("chanteuse", "kill", "healer"))
    assert ("No shot by the Vigilante was announced on night 2, so the Vigilante's target could not be killed: it "
            "was the Serial Killer.") in story.texts("B5")


def test_a_carrier_struck_down_whose_kill_was_not_announced_attacked_the_serial_killer_said_once():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "kill", "serial_killer"), story.act("sigilist", "sigil", "chanteuse"))
    assert story.texts("B5")[1:3] == [
        "A wolf is struck by a sigil only when it carries the pack's kill, so player_7 carried the pack's kill on "
        "night 1.",
        "No attack by the wolves was announced on night 1, so the pack's target could not be killed: it was the "
        "Serial Killer.",
    ]
    # B13 reaches the same proposition; it is kept once.
    silent = [item for item in public_items(story.public()) if item.conclusion == (
        SilentAttack("wolves", frozenset({"serial_killer"})),)]
    assert len(silent) == 1


def test_saved_from_the_wolves_and_a_sigil_is_the_vigilante():
    story = _sk_sp()
    story.night(1, story.act("vigilante", "kill", "trailseer"), story.act("chanteuse", "kill", "vigilante"),
                story.act("sigilist", "sigil", "vigilante"), story.act("healer", "protect", "vigilante"))
    assert story.texts("B10") == [
        "A protection saved player_4, so player_4 could be killed that night: player_4 is not the Serial Killer. "
        "The Healer cannot protect itself, so player_4 is not the Healer. The wolves attacked player_4, so "
        "player_4 is not a wolf. A sigil strikes back only at a player who attacked someone in their own name "
        "that night, so player_4 is the Vigilante.",
        "The Vigilante is struck by a sigil only when it shoots, so player_4 shot someone on night 1.",
    ]


def test_saved_from_the_vigilante_and_a_sigil_is_a_wolf_that_carried_the_kill():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "kill", "investigator"), story.act("vigilante", "kill", "chanteuse"),
                story.act("sigilist", "sigil", "chanteuse"), story.act("healer", "protect", "chanteuse"))
    assert story.texts("B10") == [
        "A protection saved player_7, so player_7 could be killed that night: player_7 is not the Serial Killer. "
        "The Healer cannot protect itself, so player_7 is not the Healer. The Vigilante shot at player_7, so "
        "player_7 is not the Vigilante. A sigil strikes back only at a player who attacked someone in their own "
        "name that night, so player_7 is a wolf.",
        "A wolf is struck by a sigil only when it carries the pack's kill, so player_7 carried the pack's kill on "
        "night 1.",
    ]


def test_a_sigil_on_a_player_whose_attack_was_blocked_strikes_nothing():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "block", "vigilante"), story.act("vigilante", "kill", "trailseer"),
                story.act("sigilist", "sigil", "vigilante"), story.act("chanteuse", "kill", "healer"))
    assert story.texts("B10") == [] and story.texts("B5") == []


# --- B6–B9, B12: the Necromancer's one action through a body --------------------------------------

def test_a_reanimated_wolf_kill_left_unhidden_means_the_conceals_are_used_up():
    story = _ne_sp()
    story.night(1, story.act("chanteuse", "kill", "sentinel"), story.act("illusionist", "conceal", None))
    story.night(2, story.act("illusionist", "kill", "trailseer"), story.act("illusionist", "conceal", None))
    story.lynch("illusionist", 3)
    story.night(3, story.act("necromancer", "kill", "investigator", via="illusionist"),
                story.act("chanteuse", "kill", "healer"))
    assert story.texts("B6") == [
        "The Necromancer attacked player_1 on night 3 through player_8's body (the Illusionist): it was alive "
        "that night, and a kill through a body makes it read Suspicious that night. It acts once a night, so it "
        "did nothing else.",
        "player_1 was killed through the dead Illusionist's body and their role was not hidden, so the Illusionist's conceals are used up: no death will be hidden again.",
        "No protection went ahead on player_1 on night 3: one would have saved player_1.",
    ]


def test_a_reanimated_illusionist_conceal_hides_no_visit_and_the_body_may_be_a_wolf():
    story = _ne_sp()
    story.lynch("illusionist", 2)
    story.night(2, story.act("necromancer", "kill", "chanteuse", via="illusionist"))
    assert story.texts("B7") == [
        "player_7's role was hidden through the dead Illusionist's body, which hides no visit: every visit to "
        "player_7 on night 2 would have shown on a watch or a follow.",
        "The Necromancer attacked player_7 on night 2 through player_8's body (the Illusionist): it was alive "
        "that night, and a kill through a body makes it read Suspicious that night. It acts once a night, so it "
        "did nothing else.",
        "The Necromancer acted on player_7 through a body, and it cannot act on itself, so player_7 is not the "
        "Necromancer.",
        "No protection went ahead on player_7 on night 2: one would have saved player_7.",
    ]
    assert not any("used up" in text for text in story.texts("B6") + story.texts("B7"))  # spent, not used up
    # No line says the body is not a wolf: a reanimated conceal can hide one.
    assert not any("not a wolf" in text for text in story.texts("B7"))


def test_a_reanimated_vigilante_shot_names_the_body():
    story = _ne_sp()
    story.lynch("vigilante", 2)
    story.night(2, story.act("necromancer", "kill", "investigator", via="vigilante"),
                story.act("illusionist", "kill", "healer"))
    assert story.texts("B8")[0] == (
        "The Necromancer attacked player_1 on night 2 through player_4's body (the Vigilante): it was alive that "
        "night, and a kill through a body makes it read Suspicious that night. It acts once a night, so it did "
        "nothing else.")


def test_a_reanimated_sigil_strikes_the_carrier_and_the_necromancer_made_no_kill():
    story = _ne_sp()
    story.lynch("sigilist", 2)
    story.night(2, story.act("illusionist", "kill", "investigator"),
                story.act("necromancer", "sigil", "illusionist", via="sigilist"))
    assert story.texts("B9") == [
        "The Necromancer set a sigil on player_8 on night 2 through player_5's body (the Sigilist): it acts once a "
        "night, so it made no kill and read Not suspicious that night.",
        "A wolf is struck by a sigil only when it carries the pack's kill, so player_8 carried the pack's kill on "
        "night 2.",
        "No protection went ahead on player_8 on night 2: one would have saved player_8.",
    ]


def test_a_save_by_the_living_healer_and_one_through_its_body():
    living = _sk_sp()
    living.night(1, living.act("chanteuse", "kill", "investigator"), living.act("healer", "protect", "investigator"))
    assert living.texts("B11") == [
        "A wolf went to player_1 on night 1 to attack them, and a watch on player_1 that night would have shown "
        "that visit.",
        "The living Healer protected player_1 on night 1: it was alive and not roleblocked that night, and a watch "
        "on player_1 would have shown its visit.",
        "A protection saved player_1, so player_1 could be killed that night: player_1 is not the Serial Killer. "
        "The Healer cannot protect itself, so player_1 is not the Healer. The wolves attacked player_1, so "
        "player_1 is not a wolf.",
    ]
    body = _ne_sp()
    body.lynch("healer", 2)
    body.night(2, body.act("illusionist", "kill", "investigator"),
               body.act("necromancer", "protect", "investigator", via="healer"))
    assert body.texts("B12") == [
        "A wolf went to player_1 on night 2 to attack them, and a watch on player_1 that night would have shown "
        "that visit.",
        "The Necromancer protected player_1 on night 2 through player_6's body (the Healer): it acts once a night, "
        "so it made no kill and read Not suspicious that night.",
        "The wolves attacked player_1, so player_1 is not a wolf. The Necromancer acted on player_1 through a "
        "body, and it cannot act on itself, so player_1 is not the Necromancer.",
    ]


def test_a_self_bet_save_names_the_fortune_teller_and_a_plain_save_does_not():
    story = Story("serial_killer", "fortune_teller")
    story.night(1, story.act("serial_killer", "kill", "fortune_teller"),
                story.act("fortune_teller", "bet", "fortune_teller"))
    assert ("player_10 survived on their own self-bet, so player_10 is the Fortune Teller and bet on themselves "
            "on night 1.") in story.texts("B33")
    plain = Story("serial_killer", "fortune_teller")
    plain.night(1, plain.act("serial_killer", "kill", "fortune_teller"),
                plain.act("healer", "protect", "fortune_teller"))
    assert plain.texts("B33") == []
    assert not any("Fortune Teller" in text for text in plain.texts("B11"))


# --- B13, B14: what an absence shows --------------------------------------------------------------

def test_no_wolf_attack_announced_in_sk_casts_means_the_pack_attacked_the_serial_killer():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "kill", "serial_killer"), story.act("serial_killer", "kill", "investigator"))
    assert story.texts("B13") == [
        "A wolf was alive at the start of night 1, and the wolves must attack every night, but no attack by the "
        "wolves was announced: their target could not be killed, so it was the Serial Killer."]
    assert story.texts("B13", without_mornings=True) == []  # no morning on the payload: no absence


def test_no_wolf_attack_from_night_two_in_ne_casts_means_the_carrier_was_blocked_through_the_chanteuse():
    story = _ne_sp()
    story.lynch("chanteuse", 2)
    story.night(2, story.act("illusionist", "kill", "investigator"),
                story.act("necromancer", "block", "illusionist", via="chanteuse"))
    assert story.texts("B13") == [
        "A wolf was alive at the start of night 2, and the wolves must attack every night, but no attack by the "
        "wolves was announced: the Chanteuse was already dead, so the Necromancer blocked the wolf carrying the "
        "kill through her body."]
    assert story.texts("B14") == ["No one died and no one was saved on night 2, so no attack went ahead that night."]
    item = next(item for item in public_items(story.public()) if item.row == "B13")
    assert item.conclusion == (BlockedBy("wolves", through_body=True),)


def test_no_absence_line_when_a_hidden_body_may_have_been_the_last_wolf():
    """The Chanteuse hidden through the Illusionist's body may be a wolf, so on night 3 no wolf is
    certainly alive, and the silent night says nothing about the pack."""
    story = _ne_sp()
    story.lynch("illusionist", 2)
    story.night(2, story.act("necromancer", "kill", "chanteuse", via="illusionist"))
    story.night(3, story.act("vigilante", "kill", "investigator"))
    assert story.texts("B13") == []


def test_no_one_died_on_night_one_in_ne_casts():
    story = _ne_sp()
    story.night(1, story.act("chanteuse", "kill", "necromancer"))
    assert story.texts("B14") == [
        "No one died and no one was saved on night 1, so every attack that night, if any, was on a player who could "
        "not be killed: the Necromancer (it cannot be killed on night 1)."]
    item = next(item for item in public_items(story.public()) if item.row == "B14")
    assert item.conclusion == (AttacksOnlyOn(frozenset({"necromancer"})),)


# --- B15–B24, B32: the read-out wills --------------------------------------------------------------

def test_a_check_in_a_will_is_public_from_its_reveal_and_not_before():
    story = _sk_sp()
    story.night(1, story.act("investigator", "investigate", "chanteuse"), story.act("chanteuse", "kill", "healer"))
    assert story.texts("B18") == []  # the Investigator is alive: its check is private
    story.night(2, story.act("illusionist", "kill", "investigator"))
    assert story.texts("B18") == [
        "player_1's will shows that on night 1 player_1 checked player_7: Suspicious. Only a wolf reads Suspicious "
        "in this game, so player_7 is a wolf."]


def test_a_watch_in_a_will_names_the_dead_watcher_not_you():
    story = _sk_sp()
    story.night(1, story.act("serial_killer", "kill", "investigator"), story.act("sentinel", "watch", "investigator"),
                story.act("chanteuse", "kill", "healer"))
    story.night(2, story.act("illusionist", "kill", "sentinel"))
    assert story.texts("B19") == [
        "player_2's will shows that on night 1 player_2 watched player_1; saw player_9 visit them. A visit does not "
        "show which action was taken. player_9 is not the Speculator: the Speculator never visits. Everyone who "
        "attacked player_1 came to player_1, and player_2's watch saw every visitor but player_2. Of the players "
        "player_2 saw, only player_9 can be the Serial Killer, so player_9 is the Serial Killer."]


def test_a_follow_in_a_will():
    story = _sk_sp()
    story.night(1, story.act("trailseer", "follow", "chanteuse"), story.act("chanteuse", "kill", "healer"),
                story.act("chanteuse", "block", "investigator"))
    story.night(2, story.act("illusionist", "kill", "trailseer"))
    assert story.texts("B20") == [
        "player_3's will shows that on night 1 player_3 followed player_7; they visited player_6 and player_1. Only "
        "a wolf who carries the pack's kill and also blocks someone visits two players, so player_7 is the "
        "Chanteuse and carried the kill that night: one of player_6 and player_1 was the pack's target, the other "
        "the player she tried to block."]


def test_a_saved_sigil_in_a_will_names_the_dead_sigilist():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "kill", "investigator"), story.act("sigilist", "sigil", "chanteuse"),
                story.act("healer", "protect", "chanteuse"))
    story.night(2, story.act("illusionist", "kill", "sigilist"))
    assert [item.text for item in will_items(story.public())] == [
        "player_5's will shows that on night 1 player_5 set a sigil on player_7, who attacked and was saved. "
        "player_7 attacked someone and needed saving from player_5's sigil, so player_7 is a wolf or the "
        "Vigilante."]
    # The morning already said the same of player_7 (B11 with B10): the proposition is kept once.
    assert story.texts("B21") == []
    assert len([item for item in public_items(story.public())
                if item.conclusion == (RoleIn("player_7", frozenset({"chanteuse", "illusionist", "vigilante"})),)]) == 1


def test_a_roleblock_in_a_will_by_the_living_chanteuse_and_through_her_body():
    living = _sk_sp()
    living.night(1, living.act("chanteuse", "block", "investigator"), living.act("investigator", "investigate", "healer"),
                 living.act("chanteuse", "kill", "healer"))
    living.night(2, living.act("illusionist", "kill", "investigator"))
    assert living.texts("B22") == [
        "player_1's will shows that on night 1 player_1 was roleblocked. Only the Chanteuse could roleblock that "
        "night, and a block is a visit, so the Chanteuse, a wolf, came to player_1 that night."]
    body = _ne_sp()
    body.lynch("chanteuse", 2)
    body.night(2, body.act("necromancer", "block", "investigator", via="chanteuse"),
               body.act("investigator", "investigate", "healer"), body.act("illusionist", "kill", "healer"))
    body.night(3, body.act("illusionist", "kill", "investigator"))
    assert body.texts("B22") == [
        "player_1's will shows that on night 2 player_1 was roleblocked. The Chanteuse was already dead, so the "
        "Necromancer blocked player_1 through her body; a watch on player_1 would have shown the Chanteuse's name, "
        "not the Necromancer's."]


def test_shots_and_protections_in_wills():
    story = _sk_sp()
    story.night(1, story.act("vigilante", "kill", "serial_killer"), story.act("healer", "protect", "investigator"),
                story.act("chanteuse", "kill", "trailseer"))
    story.night(2, story.act("illusionist", "kill", "vigilante"), story.act("serial_killer", "kill", "healer"))
    assert story.texts("B16") == [
        "player_4's will shows that on night 1 player_4 shot player_9, who was unharmed. Only the Serial Killer "
        "could survive that attack, so player_9 is the Serial Killer."]
    assert story.texts("B15") == [
        "player_6's will shows that on night 1 player_6 protected player_1; no attack on them was announced. "
        "Either no attack reached player_1 that night, or player_1 could not be killed: player_1 would then be "
        "the Serial Killer."]


def test_a_shot_saved_through_the_healers_body_reads_the_saver_from_the_morning():
    """Follow-up (slice 5): A12 reads who saved the target from the morning, not from the prose of
    a record; a will's record has no prose at all."""
    story = _ne_sp()
    story.lynch("healer", 2)
    story.night(2, story.act("vigilante", "kill", "investigator"),
                story.act("necromancer", "protect", "investigator", via="healer"),
                story.act("illusionist", "kill", "trailseer"))
    story.night(3, story.act("chanteuse", "kill", "vigilante"))
    assert story.texts("B17") == [
        "player_4's will shows that on night 2 player_4 shot player_1, who was saved. A reanimated healer is the "
        "Necromancer acting through the dead Healer's body: the Necromancer protected player_1 that night."]


def test_a_payload_with_no_morning_no_longer_names_the_protector_of_a_saved_shot():
    story = _sk_sp()
    story.night(1, story.act("vigilante", "kill", "investigator"), story.act("healer", "protect", "investigator"),
                story.act("chanteuse", "kill", "trailseer"))
    payload = {"player_id": "player_4", "player_role": "vigilante", "cast_role_counts": story.counts,
               "dead_roster": story.dead, "night_actions": [r for r in story.records if r.actor == "player_4"],
               "night_announcements": [], "read_out_wills": []}
    line = own_result_lines(seat_view_from_payload(payload))[0]
    assert line.text == "player_1 can be killed at night, so player_1 is not the Serial Killer."
    assert [type(fact).__name__ for fact in line.facts] == ["RoleIn"]


def test_held_fire_in_a_will():
    story = _sk_sp()
    story.night(1, story.act("vigilante", "hold_fire", None), story.act("chanteuse", "kill", "trailseer"))
    story.night(2, story.act("illusionist", "kill", "vigilante"))
    assert story.texts("B23") == [
        "player_4's will shows that on night 1 player_4 held fire. So player_4 shot no one that night."]


def test_a_night_missing_from_a_will_is_a_night_with_no_choice():
    story = _sk_sp()
    story.night(1, story.act("investigator", "investigate", "chanteuse"), story.act("chanteuse", "kill", "trailseer"))
    story.night(2, story.act("illusionist", "kill", "healer"))  # the Investigator declines
    story.night(3, story.act("chanteuse", "kill", "investigator"))
    assert story.texts("B32") == [
        "player_1's will has nothing for night 2, so player_1 made no choice that night: it used no ability and "
        "went to no one."]  # never the fatal night 3


def test_a_town_role_revealed_with_nothing_on_record_made_no_choice_on_the_nights_it_lived():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "kill", "trailseer"))  # the Investigator declines
    story.night(2, story.act("illusionist", "kill", "investigator"))
    assert story.texts("B24") == [
        "player_1 was revealed as the Investigator with nothing on record, so player_1 made no choice on night 1: "
        "it used no ability and went to no one."]
    first_night = _sk_sp()
    first_night.night(1, first_night.act("chanteuse", "kill", "investigator"))
    assert first_night.texts("B24") == []


def test_a_must_act_role_missing_a_night_gives_no_line():
    story = _sk_sp()
    story.night(1, story.act("chanteuse", "kill", "trailseer"))  # the Healer makes no choice: an input error
    story.night(2, story.act("illusionist", "kill", "healer"))
    assert story.texts("B24") == [] and story.texts("B32") == []


# --- B25–B27: the roster and the pick --------------------------------------------------------------

def test_a_lynched_body_with_an_ability_is_usable_from_that_night_in_ne_casts_only():
    story = _ne_sp()
    story.lynch("illusionist", 2)
    assert story.texts("B25") == [
        "player_8 was voted out on day 2 as the Illusionist, so from night 2 on the Necromancer can use player_8's "
        "body to attack someone."]
    sk = _sk_sp()
    sk.lynch("illusionist", 2)
    assert sk.texts("B25") == []
    neutral = _ne_sp()
    neutral.lynch("speculator", 2)
    assert neutral.texts("B25") == []


def test_the_speculators_pick_and_a_speculator_that_never_picked():
    story = _sk_sp()
    story.night(1, story.act("speculator", "pick", "town"), story.act("chanteuse", "kill", "trailseer"))
    assert story.texts("B26") == [
        "The Speculator picked Town on night 1, so it was alive at the start of that night, and it will not pick "
        "again."]
    story.lynch("speculator", 2)
    assert story.texts("B27") == []

    never = _sk_sp()
    never.night(1, never.act("chanteuse", "kill", "trailseer"))
    never.lynch("speculator", 2)
    assert never.texts("B27") == ["player_10 was the Speculator and never picked a side, so it has lost."]
    assert never.texts("B27", without_mornings=True) == []


def test_a_speculator_killed_the_night_it_picked_did_pick():
    story = _sk_sp()
    story.night(1, story.act("speculator", "pick", "wolves"), story.act("chanteuse", "kill", "speculator"))
    assert story.texts("B27") == []


# --- the leak boundary -------------------------------------------------------------------------------

def test_every_living_seat_gets_the_same_public_items_from_its_own_payload():
    """Seats with different roles, records and packs: the same items, equal to those of the public
    record alone. Planted hidden state on a payload changes nothing."""
    rng = random.Random(20261017)
    for _ in range(300):
        game = random_game(rng)
        for snapshot in game.snapshots:
            expected = public_items(snapshot)
            alive = [p for p in game.roles if p not in {d.player for d in snapshot.dead_roster}]
            for player in alive:
                payload = game.payload_of(player, snapshot)
                planted = {**payload, "roles": game.roles, "all_night_actions": game.records}
                assert public_items(public_record(seat_view_from_payload(payload))) == expected
                assert public_items(public_record(seat_view_from_payload(planted))) == expected


def test_the_public_record_has_no_private_field():
    # claims (slice 9a): what players said in the discussion, which every seat heard
    assert set(PublicRecord.__dataclass_fields__) == {"cast_role_counts", "dead_roster", "announcements", "wills",
                                                      "living", "claims"}


def test_a_will_item_never_reaches_a_record_from_before_its_reveal():
    rng = random.Random(11)
    for _ in range(300):
        game = random_game(rng)
        for snapshot in game.snapshots:
            holders = {will.holder for will in snapshot.wills}
            for item in public_items(snapshot):
                for source in item.sources:
                    if source.kind == "will":
                        assert source.player in holders


# --- soundness over random legal games -----------------------------------------------------------

ROWS_BUILT = {"B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12", "B13", "B14", "B15",
              "B16", "B17", "B18", "B19", "B20", "B21", "B22", "B23", "B24", "B25", "B26", "B27", "B32", "B33"}
"""The rows the random games must reach. B28–B30 give no line; B31 has no reader."""


def test_every_fact_a_public_item_states_holds_in_the_real_game():
    """Random legal games (the pack always attacks, abilities stop when spent), at every point a
    seat reasons from: every fact holds on its night, until 20,000 nights have been played."""
    rng = random.Random(20261016)
    nights_played = 0
    times_each_row_fired: dict[str, int] = {}
    while nights_played < 20000:
        game = random_game(rng)
        nights_played += len(game.nights)
        for snapshot in game.snapshots:
            for item in public_items(snapshot):
                for row in item.row.split("+"):
                    times_each_row_fired[row] = times_each_row_fired.get(row, 0) + 1
                for fact in item.conclusion:
                    assert public_fact_holds(fact, item.night, game), (item, fact, game.roles)
    assert set(times_each_row_fired) >= ROWS_BUILT, times_each_row_fired
