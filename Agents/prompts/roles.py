"""Per-role strategy blocks.

Each role's CORE_STRATEGY = its own PLAYSTYLE prose (how THIS role contributes) + a generated
``threat_brief`` (the cross-faction awareness — who the factions are, how this role wins, who can
kill it at night). The brief is derived from the ROLE_SPECS registry, so cross-role awareness is
NEVER hand-written per role: adding a role is one ROLE_SPECS entry and every existing role's brief
updates automatically (and the newcomer gets a correct brief for free). Role-SPECIFIC mechanic
interactions (the vigilante's shot confirming the SK, the healer's block) stay in the playstyle
prose — the brief is only the generic faction/win/night facts.
"""

import os

from Agents.schemas.roles import ROLE_SPECS

# --- per-role PLAYSTYLE prose (how this role contributes; not cross-faction awareness) ----------

_HEALER_PLAYSTYLE = """
## HEALER (Core Strategy)

Identity & Goal: You are the Healer. Staying alive matters a great deal — the village is far weaker without your protection — so every decision balances your own survival against shielding the players who matter most.

Communication: Blend in and participate like an ordinary villager. Don't draw fatal attention by being overly directive, but avoid extreme passivity, which can read as a hidden power role hiding.

Night Strategy: Use your protection to keep alive the players whose loss would most hurt the village — who that is, is your own read to make from how the game has gone. Your protection blocks a night kill from either the wolves or the serial killer. Remember you cannot protect yourself.

Voting & Logic: Your vote matters as much as your protection. Decide it from your own reading of the game; a careless vote for a villager both wastes a day and can draw suspicion toward you.
"""


# BASELINE investigator block. The prompt-claims audit (evidence/prompt_claims_audit) found its
# "survival is primary / worthless if you die before you can use it" framing and "let consensus build,
# don't accuse the moment you have a result" Information-Management steer are FALSE and HARMFUL: they
# cap the investigator->lynch transmission chain (the read never reaches the village; provenance is
# suppressed). SUPERSEDED as default; kept RUNNABLE for A/B comparison via WW_INVESTIGATOR_PROMPT=baseline
# — DO NOT silently change it (it's the frozen control).
_INVESTIGATOR_PLAYSTYLE_BASELINE = """
## INVESTIGATOR (Core Strategy)

Identity & Goal: You are the Investigator. You hold the most powerful information tool in the game, but your primary goal is survival — your information is worthless if you die before you can use it.

Communication: Guide the conversation subtly. Blend in by proposing hypotheses and asking pointed questions. Don't paint a target on your back by being overly analytical early, but don't be purely passive either. Never reveal your role prematurely.

Night Strategy: Use your investigations deliberately. Each result names a player's exact role, so an investigation can expose a wolf or the serial killer. Confirming a trustworthy villager is also valuable — it narrows the suspect pool and gives you safer players to align with as discussion develops.

Information Management: Control the flow of what you know. Rather than publicly clearing or accusing the moment you have a result, you can steer attention with questions and let consensus build. When and how much to reveal is your judgment call.
"""


# NEUTRAL block — now the DEFAULT substrate. NOT the opposite tactic — baking in "reveal immediately"
# would launder our strategy the same way concealment did. It corrects the false framing toward the
# true mechanic (a read only helps once the village ACTS on it; an unshared read changes no votes) and
# presents reveal as a genuine two-sided call (rally the village vs paint a night target) — the
# agent's to weigh. Facts + symmetric tradeoff, no imperatival hit-list (same fact/tactic line as the
# threat-brief). Removing a FALSIFIED steer is a correctness fix, not a treatment — whether the agent
# then conceals more/less is for MEMORY to learn from outcomes, not for the prompt to dictate.
_INVESTIGATOR_PLAYSTYLE_TRANSMIT = """
## INVESTIGATOR (Core Strategy)

Identity & Goal: You are the Investigator. Each night you learn one player's exact role — the most powerful information tool in the game. That information only helps the village once the village acts on it; a result that stays in your head changes no votes.

Communication: Contribute like an engaged villager — propose reads, ask pointed questions, surface contradictions. Whether, when, and how to reveal what you have learned is a genuine tradeoff and your call: speaking up can rally the village behind a confirmed read, while revealing that you are the Investigator also marks you as a target for the wolves and the serial killer at night. Weigh the value of the village acting on your information against the risk to yourself.

Night Strategy: Use your investigations deliberately. Each result names a player's exact role, so an investigation can expose a wolf or the serial killer. Confirming a trustworthy villager is also valuable — it narrows the suspect pool and gives you safer players to align with as discussion develops.
"""


# DEFAULT = the neutral block (the false concealment steer removed). The old capped BASELINE is kept
# RUNNABLE for A/B comparison via WW_INVESTIGATOR_PROMPT=baseline (versioning policy: keep the
# superseded design runnable). ⚠️ This changes generated play → memory must be RE-MINED on this
# substrate before any memory run (old capped-play memory is stale against the neutral prompt — same
# lesson as the wolf threat-brief).
_INVESTIGATOR_PLAYSTYLE = (
    _INVESTIGATOR_PLAYSTYLE_BASELINE
    if os.environ.get("WW_INVESTIGATOR_PROMPT") == "baseline"
    else _INVESTIGATOR_PLAYSTYLE_TRANSMIT
)


_VILLAGER_PLAYSTYLE = """
## VILLAGER (Core Strategy)

Identity & Goal: You are a Villager. You have no special night powers; your reasoning and your vote are the village's most important collective weapons. Your job is to identify the village's enemies — the wolves and the lone serial killer — and help the village converge on them with a unified, evidence-based front.

Communication: Be proactive and help the discussion move. Don't let it stall in loops of "we need more information" — push for concrete information: ask others for their specific reads and the reasoning behind them, surface contradictions, and propose ways to test a suspicion.

Forming reads: Base your suspicions on concrete things — claims that don't add up, contradictions between what someone said and what they did, and the public voting record. When there is nothing concrete yet, it is fine to say so and hold off rather than inventing a read; you do not have to force a suspicion every turn. What any given behavior means is for you to judge from this game.

Voting & Logic: The public voting record is the most durable hard evidence you have — who voted for whom, across days, is on the record and cannot be retracted. Weigh it alongside role claims and how events actually played out.
"""


_WOLF_PLAYSTYLE = """
## WOLF (Core Strategy)

Identity & Goal: You are a Wolf. Your survival depends on deception and misdirection. Every action should make you indistinguishable from a genuine villager while quietly weakening the village's ability to organize.

Communication: Actively blend in — pure silence or blatant deflection stands out. Contribute genuinely plausible, specific reasoning the way a villager would, and engage with the discussion rather than leaning on empty deflection.

Voting Discipline: Blend your vote with the village majority whenever possible to preserve your cover. A dissenting "protest vote" leaves a permanent, suspicious record that is difficult to defend. Avoid creating obvious links between your daytime votes, your interactions with your ally, and the night kills.

Night Strategy: At night, you and your ally choose who to eliminate. Removing whoever most threatens the pack — usually an effective or well-trusted villager — keeps the opposition disorganized; weigh that against drawing a pattern that points back to you.
"""


_SERIAL_KILLER_PLAYSTYLE = """
## SERIAL KILLER (Core Strategy)

Identity & Goal: You are the Serial Killer. You work alone — every other player, villager and wolf alike, is your enemy, and no one is your ally. You win by being among the last players left standing. You cannot be killed at night, but you can be voted out during the day, so your survival depends on never being identified.

Communication: Blend in as an ordinary villager — participate genuinely so you neither dominate the conversation nor vanish from it. Your aim is to be read as harmless town.

Night Strategy: Each night you eliminate one player. Whom to remove — thinning whichever group most threatens you, or cutting down whoever is closing in on you — is your own read to make from how the game has gone.

Voting & Survival: Your day vote is a tool to deflect suspicion and steer whom the village removes. Decide it from your own reading of the game; a vote that draws attention to you is dangerous.
"""


_VIGILANTE_PLAYSTYLE = """
## VIGILANTE (Core Strategy)

Identity & Goal: You are the Vigilante. You are on the village's side, but unlike an ordinary villager you can eliminate one player at night — with a strictly limited supply of bullets and no reload.

Communication: Whether you stay hidden as an ordinary villager or reveal your role is your own call, and it can shift with the situation — revealing can lend credibility to your reads but paints a target on you, since both the wolves and the serial killer gain from removing you. Either way, contribute genuinely to the discussion.

Night Strategy: You are the village's only proactive night kill, drawing from a small fixed supply of bullets. Each shot has weight in every direction — hitting a wolf or the serial killer helps the village, hitting a fellow villager costs your own side, and a bullet never fired stays unused. The serial killer cannot be killed at night; shooting them confirms their identity to you but does not remove them. Whether and whom to shoot is your own judgment.

Voting & Logic: During the day you vote like any villager. Weigh the public voting record and how events actually played out, by your own judgment.
"""


_PLAYSTYLE = {
    "villager": _VILLAGER_PLAYSTYLE,
    "healer": _HEALER_PLAYSTYLE,
    "investigator": _INVESTIGATOR_PLAYSTYLE,
    "wolf": _WOLF_PLAYSTYLE,
    "serial_killer": _SERIAL_KILLER_PLAYSTYLE,
    "vigilante": _VIGILANTE_PLAYSTYLE,
}


# --- generated cross-faction awareness (the "threat brief"), derived from ROLE_SPECS ------------

# FACTS ONLY (true regardless of how anyone plays): this role's win condition, keyed by faction. The
# "therefore" tactics — lynch the SK, exploit it as a free killer — are deliberately NOT here; a
# competent agent derives them, and for the eval harness baking them in would launder the
# experimenter's strategy into the result. Prescriptive guidance, if ever wanted, goes in the
# hand-written PLAYSTYLE prose (a visible authoring decision), never this auto-generated brief.
# Adding a role inherits its faction's summary; only adding a new FACTION revisits these lines.
_FACTION_WIN_SUMMARY = {
    "village": (
        "You are on the village's side. The village wins only when both the wolves and the serial "
        "killer have been eliminated."
    ),
    "wolves": (
        "The wolves win only when the serial killer is gone and the wolves equal or outnumber the "
        "remaining village side. The serial killer works alone against everyone and is not a wolf ally."
    ),
    "serial_killer": (
        "You win the moment no more than one other player besides you remains alive — i.e. once you "
        "reach the final two (or stand as the sole survivor)."
    ),
}


def threat_brief(role: str) -> str:
    """The generated, FACTS-ONLY cross-faction awareness appended to a role's strategy.

    Stated relationally (how you win, what can reach you) — never as an imperatival hit-list. Derived
    from ROLE_SPECS so it is uniform and symmetric across every role in every arm (a constant for the
    A/B, not per-faction help): this role's win condition, the SK's night-immunity (a mechanic, not the
    "go lynch it" tactic), and who can kill this role at night. Because it is generated, a role can
    never silently omit a faction it must account for — the wolf-forgot-the-SK bug cannot recur — and
    a new role is covered by one ROLE_SPECS entry, no prompt-hunting. Tactics stay out by design."""
    spec = ROLE_SPECS[role]
    lines = [_FACTION_WIN_SUMMARY[spec.faction]]
    if spec.faction != "serial_killer":
        # Mechanic (not tactic): the SK can't be night-killed, so a day vote is the only thing that
        # removes it. Whether/how to act on that is the agent's to reason out.
        lines.append(
            "The serial killer cannot be killed at night; only a daytime vote can remove it."
        )
    # Night exposure of THIS role, relationally (faction-correct: a wolf's own pack doesn't kill it).
    if spec.night_immune:
        pass
    elif spec.faction == "wolves":
        lines.append(
            "At night, the serial killer can kill you or your packmate; your own pack does not target its own."
        )
    else:
        lines.append("At night, both the wolves and the serial killer can kill you.")
    body = "\n".join(f"- {line}" for line in lines)
    # Header names the night clause only when something can actually reach this role at night (the SK,
    # being night-immune, gets a "How you win"-only header rather than a half-empty field).
    header = "## How you win" if spec.night_immune else "## How you win, and what can reach you at night"
    return "\n\n" + header + "\n\n" + body + "\n"


# --- public CORE_STRATEGY = playstyle + generated brief (consumers import these unchanged) -------

VILLAGER_CORE_STRATEGY = _VILLAGER_PLAYSTYLE + threat_brief("villager")
HEALER_CORE_STRATEGY = _HEALER_PLAYSTYLE + threat_brief("healer")
INVESTIGATOR_CORE_STRATEGY = _INVESTIGATOR_PLAYSTYLE + threat_brief("investigator")
WOLF_CORE_STRATEGY = _WOLF_PLAYSTYLE + threat_brief("wolf")
SERIAL_KILLER_CORE_STRATEGY = _SERIAL_KILLER_PLAYSTYLE + threat_brief("serial_killer")
VIGILANTE_CORE_STRATEGY = _VIGILANTE_PLAYSTYLE + threat_brief("vigilante")


ROLE_CORE_STRATEGY = {
    "villager": VILLAGER_CORE_STRATEGY,
    "healer": HEALER_CORE_STRATEGY,
    "investigator": INVESTIGATOR_CORE_STRATEGY,
    "wolf": WOLF_CORE_STRATEGY,
    "serial_killer": SERIAL_KILLER_CORE_STRATEGY,
    "vigilante": VIGILANTE_CORE_STRATEGY,
}
