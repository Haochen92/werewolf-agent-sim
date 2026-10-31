<!-- editorial review of ../../../../tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/2974547e-8a33-4e2f-82a4-9571ae2b95e4/scratchpad/editorial_tree/writeup/information_boundaries/wrong_agent_inputs.md by claude (opus), 2026-10-31T06:15Z -->

## 1. The argument as I understood it

The page asks how a June 2026 discussion rewrite came to put every role's private fields into every speaker's inputs, and what that incident shows about the leak checks. The central answer is that the checks were correct but useless until they ran where games actually ran, and that they caught the leak only because they inspect inputs one step before rendering, not the rendered prompts. The page first explains what the 109 flags counted and shows log excerpts. It then traces the bug to a code comment that wrongly assumed the framework strips undeclared fields. Next it explains how a search of the templates showed that no model saw the leaked fields, and why three days passed before anything fired. Finally, it describes an October recurrence in which the checks were on the execution path but were given no data, and ends with three short lessons and the limits of the evidence.

## 2. Apply the explanation

**Question:** Suppose the checks had read the rendered prompts instead of the recorded inputs. Would the June mistake have been caught on 6 June?

**Answer from the page:** No. "The checks read the inputs one step before rendering, so they flagged a violation that the rendered prompts would have hidden." The template search found that each private placeholder "appeared only in its own role's templates," so a rendered prompt would have contained none of the leaked fields. That is why the page calls June "an early warning rather than a silent fault."

**What I supplied:** The page never says what the "silent fault" would have become. I inferred that the shared bundle would have stayed in place, harmless, until some later template change named a private placeholder in another role's template, and then models would have received private data without any check noticing. That consequence is what makes the lesson matter, and it is left implicit. I also had to reread to work out whether "the bundle" is the thing that gets recorded or the thing that comes before the recorded prompt variables (finding 2).

## 3. Findings

**1.**
- **Where:** "Where the bundle came from" / "What the checks found": "through the vote step as well as the discussion turns"
- **Kind:** missing connection
- **What broke:** The page explains the discussion leak's cause in detail. The Vigilante feedback also leaked through the vote step, and the page never says why. I can't tell whether the same rewrite caused it, an older design did, or something else did. The fix section then says "The vote step stopped putting the Vigilante's feedback in every voter's bundle," which fixes a cause the page never named.
- **Repair:** In "Where the bundle came from," add one sentence giving the vote-step source and whether it shares the discussion bug's origin.
- **Severity:** worth fixing

**2.**
- **Where:** "What the checks found": "Each agent turn records the bundle of inputs built for it just before the model is called"
- **Kind:** unit or term changes meaning
- **What broke:** The parent's diagram separates a seat-specific *payload* from *prompt variables* and says the *prompt variables* are recorded. This page uses "bundle" for what is recorded. Later it says "the code that turns the bundle into prompt variables," which makes the bundle the payload. So it's unclear whether the audit reads the payload or the prompt variables, and that matters for the "data layer, not presentation layer" lesson.
- **Repair:** Map "bundle" to the parent's term (payload) once, and state which diagram stage the records capture.
- **Severity:** worth fixing

**3.**
- **Where:** "What the checks found", after-fix log: "Completed leakfix_smoke_all_disabled_001"
- **Kind:** other (an unexplained label invites a misreading)
- **What broke:** The text calls this the clean run "with every check active," but the run name says "all_disabled." A sceptical reader may conclude that the checks were off, which would undercut the evidence.
- **Repair:** Say in a clause what "all_disabled" refers to, or trim the line from the excerpt.
- **Severity:** worth fixing

**4.**
- **Where:** "The same shape, four months later": "the boundary record was re-read"; "when the game grew to ten seats"; "the game master's prose"; "since 3 October"
- **Kind:** term before introduction
- **What broke:** "The boundary record," the ten-seat expansion, the "game master," and why 3 October matters are all new to the reader. I also had to work out which "three of them" were meant (I guessed the night-record, withheld-speech and eliminated-player checks), and what the eliminated-player check verifies. I inferred "dead players get no inputs" from the parent's last line.
- **Repair:** Name the three checks and give each a five-word purpose. Gloss "game master" and "boundary record." Tie 3 October to the ten-seat change explicitly.
- **Severity:** worth fixing

**5.**
- **Where:** "The same shape, four months later" (heading and first paragraph)
- **Kind:** missing connection
- **What broke:** The heading promises "the same shape," but the section never says what that shape is. June was "checks not on the path that ran"; October was "checks on the path but fed nothing." I had to work out the shared pattern myself, and only "What this establishes" names it, as "a check outside the execution path verifies nothing."
- **Repair:** Open the section with one sentence naming the shared pattern: a check that is present but receives nothing from the path that actually runs.
- **Severity:** worth fixing

**6.**
- **Where:** "The same shape, four months later": "The fix the same day lifted the three inputs out of the finished game's state"
- **Kind:** missing connection
- **What broke:** June ends with a verdict ("the next game flagged none"), but October does not. After the fix, I don't know whether the newly fed checks found any night-result leaks from the period since 3 October, or ran clean.
- **Repair:** State the outcome of the first run after the October fix.
- **Severity:** worth fixing

**7.**
- **Where:** "Why it went unnoticed, and the fix": "The checks were correct and present the whole time."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The same page shows that no check covered the Vigilante feedback ("no check yet") and that a check had to be added for it. "Correct" over-reaches. The narrower claim the page supports is that the checks that existed were right.
- **Repair:** Qualify the sentence to cover the checks that existed, and note the coverage gap.
- **Severity:** worth fixing

**8.**
- **Where:** "What the checks found", the after-fix log block, placed before "Where the bundle came from"
- **Kind:** section order
- **What broke:** The clean after-fix result appears before the cause and the fix are explained, so the reader sees the resolution two sections before learning what was changed. The opening roadmap also lists "where the bundle came from" before "what the 109 counted," which is the reverse of the actual order.
- **Repair:** Move the after-fix log to the fix section, and make the roadmap match the section order.
- **Severity:** taste

**9.**
- **Where:** "Where the bundle came from": "That was true of a boundary the bundle never crossed."
- **Kind:** other (abstract phrasing obscures the mechanism)
- **What broke:** The key mechanism is two ways of connecting steps, only one of which strips undeclared fields. The opening sentence is a riddle, and I had to read the paragraph twice to see that the comment was true of the *other* connection method.
- **Repair:** Lead with the contrast stated plainly: one connection type strips undeclared fields, and this path used the one that doesn't.
- **Severity:** worth fixing

**10.**
- **Where:** "What this establishes", final paragraph: "Games played on the site save the same inputs, and a nightly job is built…"
- **Kind:** repeats parent context; also missing connection
- **What broke:** This repeats the parent nearly word for word. More importantly, after the October finding, a reader will want to know whether the nightly job passes the three game-state inputs or has the same gap. The page doesn't say.
- **Repair:** Replace the repetition with one sentence on whether the nightly job receives the full set of inputs.
- **Severity:** worth fixing

**11.**
- **Where:** "Did any model see it?": "That finding is scoped to the templates as they were that day."
- **Kind:** empty repetition
- **What broke:** The same caveat is repeated almost verbatim in the final section.
- **Repair:** Keep it in one place.
- **Severity:** taste

**12.**
- **Where:** Table row "Vigilante's shot feedback"
- **Kind:** term before introduction
- **What broke:** The parent never mentions the Vigilante, and "shot feedback" is unexplained. I inferred a role with a limited night kill and a private result, but that is my reconstruction.
- **Repair:** Gloss the role in one clause where it first appears.
- **Severity:** taste

## 4. Highest-impact improvements

1. Settle the terminology: map "bundle" to the parent's payload / prompt-variables stages, and say which one the audit records. The page's main lesson depends on this.
2. Make the October section stand alone. Name the shared failure pattern up front, introduce its new terms (ten seats, game master, which three checks), and report what the fixed checks found.
3. Close the evidence gaps: explain where the vote-step leak came from, explain or trim "all_disabled," and replace the repeated nightly-job line with whether that job has the October gap.
