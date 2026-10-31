<!-- editorial review of writeup/information_boundaries/information_boundaries.md by claude (opus), 2026-10-30T02:12Z -->

## 1. The argument as I understood it

The page asks where the rule "each agent sees only what its seat may know" is enforced, and how the author confirms that it holds. The central answer is that enforcement happens at one point: when each seat's input is built, the code selects only the fields that seat may receive. This is least privilege. No later step is trusted to filter. A post-game audit then checks the recorded inputs against a classification of who may receive what. The page first argues that leaks would invalidate measurements, then classifies information by audience. It then places enforcement at the selection step and describes the audit, including the one real break it caught. It extends the same boundary to the deduction engine, which is tested with a metamorphic test, and closes by listing what the checks do not cover.

## 2. Findings

**1.**
- **Where:** "Checking what was actually sent": "Every model call's prompt variables are recorded before the call." Also "What the checks cover": "Two kinds of call are built from a seat's selected payload but not recorded".
- **Kind:** caveat reverses an earlier claim
- **What broke:** The first sentence reads as complete coverage, and the whole audit argument rests on it. Two sections later, some calls turn out not to be recorded. Because those calls are not named, I can't tell whether the gap is minor or a large part of what agents receive.
- **Repair:** Explain. Qualify the first sentence where it appears (for example, "every call except two kinds, described below"). In the limits section, name the two kinds of call and say why they are not recorded.
- **Severity:** blocking

**2.**
- **Where:** Opening: "Chapter 1 set the rule: each agent's input is built from what its seat may know." Roles such as "Healer", "wolves" and "Investigator", and phases such as "the night", appear throughout.
- **Kind:** term before introduction
- **What broke:** The page is a chapter opened directly, but it never says what the game is or that each player is an LLM agent. It never defines a *seat*, which is the unit of the whole rule. The Healer and the Investigator are named, but the page never says what those roles do. I can guess this is a Werewolf-style game, but I am guessing. Without the Investigator's ability, I also can't tell why "the Investigator's results" count as private.
- **Repair:** Explain. Add one or two orienting sentences before the Healer example. They should name the game type, say that one agent plays each seat, define seat, and give each role named on the page a short gloss.
- **Severity:** worth fixing

**3.**
- **Where:** "Classifying information by who may receive it": "the game sometimes holds back a line that only repeated earlier talk."
- **Kind:** missing connection
- **What broke:** Reads are clearly sensitive, because a wolf's reads name its packmate. A suppressed repetitive line is not obviously sensitive, and the page never says why it must reach no prompt or why leaking it would matter. It returns later as a check ("a held-back line in nobody's") and is never explained. Putting it in the same bullet as reads makes the tier look like a mixed list rather than one category.
- **Repair:** Explain in one clause why a held-back line must stay out of every prompt. If the reason doesn't concern information boundaries, remove it from both places.
- **Severity:** worth fixing

**4.**
- **Where:** "Checking what was actually sent": "a nightly job is built to run the same checks over them."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** "Is built to" could mean the job runs every night or that it exists but isn't running yet. Later the page uses "designed, not built" to mark unbuilt work, which makes me read this job as running, but I'm not sure. It is also the only mention of "the site", so I don't know whether real players use it.
- **Repair:** Explain. State plainly whether the nightly job runs today. Add a few words saying what the site is.
- **Severity:** worth fixing

**5.**
- **Where:** "Holding computed advice to the same boundary": "One test swaps two roles the Investigator cannot see… It shows that the deductions do not depend on hidden information".
- **Kind:** claim reads stronger than its support on the page
- **What broke:** A single swap for a single viewing role is presented as showing independence in general. I can't tell whether the test covers other roles, other swaps or other game states.
- **Repair:** Explain. Either describe the test's real range (which roles, which states) or narrow the claim to the case it covers.
- **Severity:** worth fixing

**6.**
- **Where:** Opening: "three things have to stay distinct: the boundary itself (who may know what), the code that enforces it, and the checks that detect a violation."
- **Kind:** missing connection
- **What broke:** The page asserts that the three must stay distinct but doesn't yet say why. The reason only appears later: template filtering was mistaken for enforcement, and the audit detects but cannot prevent. I had to rebuild this myself. I also didn't see at first that these three items are the plan for the next three sections.
- **Repair:** Explain. Add a clause on what goes wrong when they are conflated, and say that the following sections take them in order.
- **Severity:** worth fixing

**7.**
- **Where:** "Checking what was actually sent": "on the reasoning… that the framework drops fields a step does not declare."
- **Kind:** unit or term changes meaning
- **What broke:** The pipeline section described template filtering as "variables it names". Here an unintroduced "framework" drops fields a "step" doesn't "declare". I had to work out that this is the same third-step behaviour under different words.
- **Repair:** Explain. Use the same vocabulary as the pipeline section, or point back to the third step explicitly.
- **Severity:** worth fixing

**8.**
- **Where:** "Holding computed advice to the same boundary": "so a careless helper could pass a hidden fact straight into its advice."
- **Kind:** other (ambiguous term)
- **What broke:** In a game about players and roles, "helper" could mean a player as easily as a helper function.
- **Repair:** Explain. Say "helper function" or name the component.
- **Severity:** taste

**9.**
- **Where:** "What the checks cover": "Memory sits outside both."
- **Kind:** other (unclear referent)
- **What broke:** "Both" refers to the two questions that set the limits. That only becomes clear on rereading. The paragraph then concludes that a memory mix-up wouldn't reveal a current role, so I wasn't sure whether it is a boundary risk at all or just a different rule ("the retrieval rule", which the page never states).
- **Repair:** Explain. Say directly that neither the audit nor the field checks cover memory, and give the retrieval rule in one clause. If memory isn't an information-boundary concern, shorten the paragraph to a scope note.
- **Severity:** taste

## 3. Highest-impact improvements

1. Fix the conflict between "every model call's prompt variables are recorded" and the two unrecorded kinds of call, and name those two kinds.
2. Open with a short orientation covering the game, one agent per seat, what a seat is, and what the named roles do. Then say why the boundary, the enforcement and the checks must stay separate.
3. Either explain why a held-back line is secret or remove it from the classification and from the audit list.
