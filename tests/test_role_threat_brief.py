"""Guard the registry-derived cross-faction awareness (Agents/prompts/roles.threat_brief).

The wolf SK-blindness bug was: a role's strategy silently omitted a faction it must account for
(the wolf never operationalized the serial killer). The brief is generated from ROLE_SPECS so this
can't recur — these tests lock that invariant, including for any role added later."""

from Agents.prompts.roles import ROLE_CORE_STRATEGY, threat_brief
from Agents.schemas.roles import ROLE_SPECS, RoleSpec


def test_every_role_strategy_names_the_serial_killer_and_wolves():
    # Every role must be aware of the other factions; the wolf forgetting the SK was the bug.
    for role in ROLE_SPECS:
        s = ROLE_CORE_STRATEGY[role].lower()
        assert "serial killer" in s, f"{role} strategy omits the serial killer"
        assert "wolf" in s or "wolves" in s, f"{role} strategy omits the wolves"


def test_wolf_brief_operationalizes_the_sk():
    # The specific regression: the wolf must know the SK blocks its win, kills at night, and is
    # removable only by a daytime vote.
    brief = threat_brief("wolf").lower()
    assert "serial killer" in brief
    assert "night" in brief                      # SK as a night threat to the pack
    assert "vote" in brief                       # vote-only removal path


def test_non_sk_roles_get_the_vote_only_removal_mechanic_sk_does_not():
    # Everyone who needs the SK gone is told the FACT that only a day vote removes it (not the tactic
    # "go lynch it"); the SK itself gets no such line.
    for role, spec in ROLE_SPECS.items():
        brief = threat_brief(role).lower()
        if spec.faction == "serial_killer":
            assert "daytime vote" not in brief
        else:
            assert "daytime vote can remove it" in brief


def test_night_exposure_is_faction_correct():
    # Town can be killed by wolves + SK; the wolf by the SK (not its own pack); the SK by no one at night.
    assert "both the wolves and the serial killer can kill you" in threat_brief("villager")
    assert "serial killer can kill you or your packmate" in threat_brief("wolf")
    sk = threat_brief("serial_killer").lower()
    assert "can kill you" not in sk              # SK is night-immune — no exposure line


def test_sk_win_condition_is_concrete_not_fuzzy():
    # The SK lives in the endgame; its win threshold must be precise (matches determine_winner:
    # sk wins when at most one other player remains), not the fuzzy "among the last standing".
    brief = threat_brief("serial_killer").lower()
    assert "no more than one other player" in brief and "final two" in brief
    assert "among the last" not in brief


def test_header_names_night_clause_only_when_a_night_threat_exists():
    # Night-immune SK gets a "How you win"-only header (no half-empty night field); others name it.
    assert threat_brief("serial_killer").strip().startswith("## How you win\n")
    assert "what can reach you at night" not in threat_brief("serial_killer")
    assert "what can reach you at night" in threat_brief("villager")


def test_brief_is_facts_not_tactics():
    # The content line: no prescriptive SK-handling baked in (that would launder strategy into the
    # eval). These tactic phrasings from the first draft must stay OUT of every generated brief.
    for role in ROLE_SPECS:
        brief = threat_brief(role).lower()
        for tactic in ("steering the village's vote", "rival to be removed", "lynch", "hunt", "exploit"):
            assert tactic not in brief, f"{role} brief leaked a tactic: {tactic!r}"


def test_new_role_is_covered_without_touching_prompts():
    # A role added to ROLE_SPECS gets a correct brief purely from its faction — no prompt edits.
    spec = RoleSpec("tracker", "village", night_action="investigate")
    # threat_brief reads ROLE_SPECS, so register then compose (mirrors how a real role would be added)
    ROLE_SPECS["tracker"] = spec
    try:
        brief = threat_brief("tracker").lower()
        assert "serial killer" in brief and "wolves" in brief
        assert "village wins only when both" in brief
    finally:
        del ROLE_SPECS["tracker"]
