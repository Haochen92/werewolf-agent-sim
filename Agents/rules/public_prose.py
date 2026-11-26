"""The moderator's public prose read back into data: the morning (announcement_from_prose) and the
read-out wills (wills_from_prose), for a payload from before the engine kept them as data.

A live game commits the morning and each will twice, as prose and as data, from the same report
and records (Agents/rules/announcement.py, Agents/rules/night_record.py `read_out_will`). A frozen
replay or a stored game from before carries only the prose, in its game-master summaries; the
deduction engine rebuilds the data from it here (Agents/deduction/seat_view.py). The grammar is
written out on its own, not taken from the code that writes the prose, so the tests that hold prose
and data together (tests/engine/test_night_announcement.py, test_read_out_wills.py) check one
against the other. A sentence it does not recognise raises ValueError: a morning read wrongly is
worse than none.
"""

from __future__ import annotations

import re
from typing import Any

from Agents.schemas.game_events import AnnouncedDeath, AnnouncedSave, NightAnnouncement, ReadOutWill, WillClause
from Agents.schemas.roles import ROLE_SPECS, TOWN, side_of

# --- the morning's grammar, as the players read it --------------------------------------------

ATTACKER_PHRASES = {
    "the wolves": "wolves",
    "the serial killer": "serial_killer",
    "the vigilante": "vigilante",
    "a sigil": "sigilist",
    "a reanimated wolf": "reanimated_wolves",
    "a reanimated vigilante": "reanimated_vigilante",
    "a reanimated sigil": "reanimated_sigilist",
}
VERB_OF_ONE_ATTACKER = {"wolves": "killed", "serial_killer": "stabbed", "vigilante": "shot",
                        "sigilist": "struck down", "reanimated_wolves": "killed",
                        "reanimated_vigilante": "shot", "reanimated_sigilist": "struck down"}
SIDES = {"Town": "town", "the Wolves": "wolves", "the lone killer": "lone_killer", "itself": "self"}
HIDERS = {"an illusionist": "illusionist", "a reanimated illusionist": "reanimated_illusionist"}
SAVERS = {"the healer": "healer", "a reanimated healer": "reanimated_healer"}

PLAYER = r"(?P<player>player_\d+)"
ATTACKED = PLAYER + r" was (?P<verb>killed|stabbed|shot|struck down|attacked) by (?P<attackers>[^.!]+?) last night\. "
SENTENCES = {
    "revealed": re.compile(ATTACKED + r"They were a (?P<role>[a-z ]+)\."),
    "hidden": re.compile(ATTACKED + r"Their role is hidden by (?P<hider>an illusionist|a reanimated illusionist)\."),
    "saved": re.compile(PLAYER + r" was attacked by (?P<attackers>[^.!]+?) but was saved by "
                        r"(?P<saver>the healer|a reanimated healer)!"),
    "self_bet": re.compile(PLAYER + r" was attacked by (?P<attackers>[^.!]+?) but survived: the fortune teller's "
                           r"self-bet saved them\."),
    "no_one_died": re.compile(r"No one died last night\."),
    "pick": re.compile(r"The Speculator has picked (?P<side>Town|the Wolves|the lone killer|itself)\."),
    "will": re.compile(r"The record of " + PLAYER + r", the (?P<role>[a-z ]+): (?P<clauses>[^.]*)\."),
}
MORNING_HEADER = re.compile(r"Night of day (?P<night>\d+): ")


def _role(words: str) -> str:
    return words.replace(" ", "_")


def _attacker_types(match: re.Match) -> list[str]:
    types = []
    for phrase in re.split(r", | and ", match.group("attackers")):
        if phrase not in ATTACKER_PHRASES:
            raise ValueError(f"unknown attacker: {phrase!r}")
        types.append(ATTACKER_PHRASES[phrase])
    if "verb" in match.groupdict():
        expected_verb = VERB_OF_ONE_ATTACKER[types[0]] if len(types) == 1 else "attacked"
        if match.group("verb") != expected_verb:
            raise ValueError(f"verb does not fit the attackers: {match.group(0)!r}")
    return types


def _read_morning(message: str) -> tuple[NightAnnouncement, list[ReadOutWill]]:
    """The morning and the wills read out in it, sentence by sentence."""
    header = MORNING_HEADER.match(message)
    if not header:
        raise ValueError(f"not a morning: {message!r}")
    night = int(header.group("night"))
    position = header.end()
    deaths, saves, pick, no_one_died, wills = [], [], None, False, []
    while position < len(message):
        for kind, pattern in SENTENCES.items():
            match = pattern.match(message, position)
            if match:
                break
        else:
            raise ValueError(f"unrecognised morning sentence: {message[position:]!r}")
        position = match.end() + (1 if message[match.end():match.end() + 1] == " " else 0)
        if kind == "revealed":
            death = AnnouncedDeath(player=match.group("player"), attacker_types=_attacker_types(match),
                                   role=_role(match.group("role")))
            deaths.append(death)
            if _is_town(death.role):
                wills.append(ReadOutWill(holder=death.player, role=death.role, day=night, phase="night"))
        elif kind == "hidden":
            deaths.append(AnnouncedDeath(player=match.group("player"), attacker_types=_attacker_types(match),
                                         role="", hidden_by=HIDERS[match.group("hider")]))
        elif kind == "saved":
            saves.append(AnnouncedSave(player=match.group("player"), attacker_types=_attacker_types(match),
                                       saver=SAVERS[match.group("saver")]))
        elif kind == "self_bet":
            saves.append(AnnouncedSave(player=match.group("player"), attacker_types=_attacker_types(match),
                                       saver="self_bet"))
        elif kind == "no_one_died":
            no_one_died = True
        elif kind == "pick":
            pick = SIDES[match.group("side")]
        else:
            _fill_will(match, wills)
    announcement = NightAnnouncement(night=night, deaths=deaths, saves=saves, pick=pick, no_one_died=no_one_died)
    return announcement, wills


def announcement_from_prose(message: str) -> NightAnnouncement:
    """The moderator's morning ("Night of day n: …") as data. Raises ValueError on a sentence it
    does not recognise."""
    return _read_morning(message)[0]


# --- the read-out wills -----------------------------------------------------------------------

NAMES = r"(?P<names>player_\d+(?:(?:, | and )player_\d+)*)"
TARGET = r"(?P<target>player_\d+)"
CLAUSES = [
    (re.compile(r"was roleblocked"), None, "roleblocked"),
    (re.compile(r"protected " + TARGET + r", who was attacked and saved by the fortune teller's self-bet"),
     "protect", "self_bet_saved"),
    (re.compile(r"protected " + TARGET + r", who was attacked and saved"), "protect", "saved"),
    (re.compile(r"protected " + TARGET + r"; no attack on them was announced"), "protect", "no_attack"),
    (re.compile(r"held fire"), "hold_fire", "held"),
    (re.compile(r"shot " + TARGET + r", who died"), "shoot", "killed"),
    (re.compile(r"shot " + TARGET + r", who was saved by the fortune teller's self-bet"), "shoot", "self_bet_saved"),
    (re.compile(r"shot " + TARGET + r", who was saved"), "shoot", "saved"),
    (re.compile(r"shot " + TARGET + r", who was unharmed"), "shoot", "immune"),
    (re.compile(r"checked " + TARGET + r": Suspicious"), "investigate", "suspicious"),
    (re.compile(r"checked " + TARGET + r": Not suspicious"), "investigate", "not_suspicious"),
    (re.compile(r"watched " + TARGET + r"; saw " + NAMES + r" visit them"), "watch", "seen"),
    (re.compile(r"watched " + TARGET + r"; saw no one"), "watch", "seen"),
    (re.compile(r"followed " + TARGET + r"; they visited " + NAMES), "follow", "seen"),
    (re.compile(r"followed " + TARGET + r"; they visited no one"), "follow", "seen"),
    (re.compile(r"set a sigil on " + TARGET + r", who attacked and was struck down"), "sigil", "hit"),
    (re.compile(r"set a sigil on " + TARGET + r", who attacked and was saved"), "sigil", "saved"),
    (re.compile(r"set a sigil on " + TARGET + r"; it had no effect"), "sigil", "miss"),
]
"""Each night of a read-out record (`_disclosed` in Agents/rules/night_record.py): the sentence,
the action and the result word it stands for."""


def _is_town(role: str) -> bool:
    return role in ROLE_SPECS and side_of(role) == TOWN


def _clause(text: str) -> WillClause:
    night_match = re.fullmatch(r"night (?P<night>\d+), (?P<rest>.+)", text)
    if not night_match:
        raise ValueError(f"unrecognised will clause: {text!r}")
    rest = night_match.group("rest")
    for pattern, action, result in CLAUSES:
        match = pattern.fullmatch(rest)
        if match:
            groups = match.groupdict()
            names = groups.get("names")
            return WillClause(night=int(night_match.group("night")), action=action, target=groups.get("target"),
                              result=result, seen=re.split(r", | and ", names) if names else [])
    raise ValueError(f"unrecognised will clause: {text!r}")


def _fill_will(match: re.Match, wills: list[ReadOutWill]) -> None:
    """A record sentence belongs to the revealed death just announced, of the same player."""
    if not wills or wills[-1].holder != match.group("player") or wills[-1].clauses:
        raise ValueError(f"a record read out with no revealed death before it: {match.group(0)!r}")
    if wills[-1].role != _role(match.group("role")):
        raise ValueError(f"a record read out under another role: {match.group(0)!r}")
    wills[-1].clauses = [_clause(text) for text in re.split(r"; (?=night \d+, )", match.group("clauses"))]


LYNCH = re.compile(r"Player " + PLAYER + r" has been voted out and was a (?P<role>[a-z ]+)\.")
VOTE_HEADER = re.compile(r"\s*Here's the vote result for day (?P<day>\d+):")


def wills_from_prose(message: str) -> list[ReadOutWill]:
    """The wills a game-master message read out: a morning's, one for each revealed town death,
    or a vote result's, for a lynched town player. A revealed town role with nothing on record
    gets a will with no clauses. Raises ValueError on a morning or a record it does not recognise."""
    if MORNING_HEADER.match(message):
        return _read_morning(message)[1]
    header = VOTE_HEADER.match(message)
    lynch = LYNCH.search(message)
    if header is None or lynch is None or not _is_town(_role(lynch.group("role"))):
        return []
    will = ReadOutWill(holder=lynch.group("player"), role=_role(lynch.group("role")), day=int(header.group("day")),
                       phase="day")
    record = SENTENCES["will"].search(message, lynch.end())
    if record is not None:
        _fill_will(record, [will])
    return [will]


# --- a payload from before the data was kept ----------------------------------------------------

def _game_master_texts(day_summaries: list[Any]) -> list[str]:
    texts = []
    for summary in day_summaries:
        if isinstance(summary, dict):
            source, text = summary.get("source"), summary.get("summary", "")
        else:
            source, text = summary.source, summary.summary
        if source == "game_master" or text.lstrip().startswith(("Night of day", "Here's the vote result")):
            texts.append(text)
    return texts


def public_data_from_summaries(day_summaries: list[Any]) -> tuple[list[NightAnnouncement], list[ReadOutWill]]:
    """The mornings and the read-out wills a payload's game-master summaries hold, in order. A
    message it cannot read is left out, with whatever it held: the rows that need it then say
    nothing, which is safe; reading it wrongly would not be."""
    announcements: list[NightAnnouncement] = []
    wills: list[ReadOutWill] = []
    for text in _game_master_texts(day_summaries):
        try:
            if MORNING_HEADER.match(text):
                announcement, morning_wills = _read_morning(text)
                announcements.append(announcement)
                wills.extend(morning_wills)
            else:
                wills.extend(wills_from_prose(text))
        except ValueError:
            continue
    return announcements, wills
