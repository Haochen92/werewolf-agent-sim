"""The game's rules, as the text every prompt opens with. Three slots are filled from the dealt
cast by ``compose.py``: the lineup, each side's and role's paragraph, and the win lines. Each
role's own words are on its card in ``roles/``. Everything else is written here, as prose, to be
true for any cast, so no role is named except through its side."""

from __future__ import annotations

SIDES = {
    "town": {
        "heading": "Town (wins as a side):",
        "win": "Town wins when BOTH the wolves and the lone killer are gone.",
    },
    "wolves": {
        "heading": "Wolves (know each other and win as a team):",
        "rules": (
            "The wolves know each other and talk privately at night. Each night one of them, the carrier, "
            "kills one player; the carrier rotates unless the pack agrees otherwise, and is the only wolf who "
            "visits for the kill. Every wolf knows the pack's kill. A wolf may carry the kill and use its own "
            "ability on the same night."
        ),
        "win": "The wolves win when the lone killer is gone and they equal or outnumber everyone else still alive.",
    },
    "lone_killer": {"heading": "Lone killer (works alone against everyone):"},
    "neutral": {"heading": "Neutral (has no side; wins by meeting its own win condition):"},
}
"""The sides in lineup order: the heading each prints, and for a team its rules and its win line.
A seat of one (the lone killer, the neutral) keeps those on the role's card."""

# The block the model reads. compose.py fills the three slots with pre-wrapped text: {lineup} is the
# "Team composition" header and lines, {roles} one paragraph per dealt side and role, {wins} one line
# per team or seat of one.
RULES_TEMPLATE = """\
{lineup}

How each side and role works:
{roles}

How a day and a night run, in order (the Game Master narrates and manages the flow):
Day, the discussion:
- Players speak one at a time, never over each other. The day opens with an opening round: every living
    player is given one turn, in an order drawn at random that day, to speak or to pass. After the
    opening round the moderator decides who speaks next: a player who was addressed answers first, a
    player with something to add may be asked, and a player whose point has already been made may be
    skipped. The discussion winds down once players stop having new things to say.
- The order of speech is the moderator's doing: who spoke first, how often someone spoke, or who hasn't
    spoken yet says nothing about their role.
- A player can claim any role or any night result. A claim is recorded, but nothing a player says is
    verified unless the Game Master announced it; a night result a player brings up is their claim, not
    an announcement, and saying the Game Master announced it is false. Everything else is for the
    players to work out by deduction and by elimination.
Day, the vote:
- Day 1 has no vote: it is discussion only, then night. From day 2 on, each day ends in a vote.
- Before the vote, the most accused player gets a last word. Then everyone votes. You may vote to
    eliminate a player, or abstain when abstaining is offered; if no single player gets the most votes
    (a tie, or an abstain majority), no one is eliminated. After two days in a row with no elimination,
    abstaining is no longer offered and everyone must name a player.
- Votes are public and permanent — who voted to eliminate whom each day stays on the record. An
    eliminated player's role is revealed, and their will read out, by the same rule as a night death.
Night, the actions:
- Every role with a night action acts, all at once. A night action that is carried out on a player is a
    visit, unless the role's rules say it is not; an action that was blocked is not carried out and is
    not a visit. Roles that watch or follow see visits.
- An attack kills its target unless the target is protected that night (a save, announced in the
    morning) or cannot be killed at night (nothing announced). A player attacked by more than one
    attacker still dies once.
- What a player did or learned at night is known only to them. Town players do not share their results
    with each other; the wolves share only the pack's kill, each wolf's own ability and result stay its
    own. Night actions are hidden; only the outcomes are announced in the morning.
Morning, the report:
- Players receive public and private information about the night. Public: every player who was attacked,
    unless they cannot be killed at night (that attack is never mentioned); whether an attacked player
    was saved; each dead player's role, unless a role listed above hid it; and, for each dead Town
    player whose role was revealed, their record read out as their will. Private: each surviving
    player's own night action and its result. A player who died in the night learns nothing from it, so
    that night is not in their will either.
- The order: the Game Master goes through the attacked players in seat order; for a death, the kind of
    attacker, then the role, then the will of a revealed Town player; for a save, that they were
    attacked and saved. A night where no one died and no one was saved is announced as "No one died last
    night."
- Nothing else about the night is announced, beyond what a role's rules above say is announced: not a
    protection where no attack came, not an ability held back, not who did what. Only Town wills are read out, and a hidden role has none. Once read out, a will is
    announced fact; anything a player says about the night is a claim.

Win conditions:
{wins}

The world is closed: the only roles and abilities in this game are the ones listed above."""
