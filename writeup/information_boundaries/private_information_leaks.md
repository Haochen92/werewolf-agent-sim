# Preventing private information leaks between agents

*Level 3 · [Information boundaries](information_boundaries.md) · the owner's short version, 2026-10-31, replacing the drafted incident page of the same day (kept as `_authoring/wrong_agent_inputs.reviewed-draft.md`); file renamed from `wrong_agent_inputs.md`.*

## The problem

During a refactor of the game's discussion system, I discovered that agents were receiving private information they shouldn't have access to.

For example, a Healer's input could contain the identities of the wolves and the Investigator's private results.

**The models weren't necessarily seeing this information.** Each role had its own prompt template, which only used the fields relevant to that role. A review of the templates at the time found that the unauthorized fields were not rendered into the models' prompts.

However, the underlying information boundary was still broken. A future template change could accidentally expose those fields.

## Why it happened

Previously, the system built separate input payloads for each role. During the refactor, I changed this to a shared payload containing information for multiple roles.

I assumed LangGraph would automatically ignore fields that an agent didn't need. However, the `Send` mechanism used here forwarded the entire payload without filtering it.

**The mistake was relying on downstream prompt templates to hide private information instead of restricting what each agent received.**

## How I fixed it

I made two changes:

1. **Role-based filtering:** The system now constructs each agent's payload using shared public information plus only the private fields that role is authorized to receive. For example, wolves receive the wolf roster, while the Healer does not.
2. **Automated leak detection:** I connected existing checks to the batch runner and added coverage for previously unchecked fields. These checks inspect the recorded agent inputs, independently of the prompt templates, and flag unauthorized information.

A game played after the fix produced no leak warnings.

A later review also revealed that some checks were running without the game-state inputs they needed. I corrected this and added tests that deliberately introduce forbidden information to verify that the checks detect it.

## What I learned

The main lesson was that **information access must be enforced at the data layer, not left to prompt templates.**

Prompt templates determine what information gets displayed to a model, but they shouldn't be responsible for deciding what information an agent is authorized to receive.

I also learned that having automated checks isn't sufficient. They need to run as part of the normal workflow, receive the necessary inputs, and be tested to ensure they actually detect violations.

<!-- Sources (checked 2026-10-31 against the record and the code).
The incident: evidence/agent_boundaries/report.md §4 and experiment_log.md §2 (the shared payload of the
sequential-discussion rewrite, 2026-06-03/04; the docstring "LangGraph ignores extra keys on a Send
payload"; a Send delivers its payload verbatim, the node's TypedDict enforces nothing at runtime; 109 flag
lines on 2026-06-06 = 76 wolf-roster + 33 investigator-result, all discussion inputs; the Vigilante's shot
feedback leaked uncounted and was found by inspection; the template grep found each private placeholder
only in its own role's templates; "none rendered" is one search on that day). The Healer example: the
healer's input carried the wolf roster (leakwire_smoke.log) and investigator_results reached every
non-investigator input.
The fix: commits ef43342 (role-gated private fields in the speaker builder, mirroring the vote fan-out;
the Vigilante field out of the shared vote payload) and 8008623 (the Vigilante check); the checks wired
into the batch runner the same day (e9d30ba). "A game played after the fix", not "the first game": the
record says a post-fix live game flagged none (0 flags, batch exit 0); the exact game order is not
recorded.
Today's code: Agents/nodes/day/flow.py `_private_fields` (shared by the speaker builder and the vote
fan-out); Agents/nodes/night/solo.py and pack.py (pack roster to wolves only); tests/leak_test.py (the
checks, `run_leak_tests`, `leak_inputs`); scripts/run_batch.py passes `leak_inputs(result)`;
server/housekeeping/leak_audit.py runs the same checks over the website's saved games.
October: experiment_log.md §6 and report §5 "Closed" (three checks fed nothing by the runner: eliminated
players, held lines, night records; night-result isolation had no live check 2026-10-03 to 10-14;
`leak_inputs` lifts the inputs from the final state; tests plant a night record and require the flag).
The long version of this page, with the count's arithmetic, the three-day timeline, the two log exhibits
and the October detail, is `_authoring/wrong_agent_inputs.reviewed-draft.md`, with its own sources. -->
