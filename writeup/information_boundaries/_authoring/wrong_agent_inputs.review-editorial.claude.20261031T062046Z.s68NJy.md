<!-- editorial review of ../../../../tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/2974547e-8a33-4e2f-82a4-9571ae2b95e4/scratchpad/editorial_tree/writeup/information_boundaries/wrong_agent_inputs.md by claude (opus), 2026-10-31T06:20Z -->

## 1. The argument as I understood it

The page answers four questions about the June incident from the parent page: what the audit's 109 flags counted, how private fields got into every speaker's input, how the author established that no model saw them, and why the existing checks didn't catch it sooner. The central answer is that one shared bundle replaced selection by role. A code comment justified this by describing a framework behaviour that didn't apply on this path. The data-layer checks were correct but didn't run until they were wired into the batch runner, and when they ran they found the problem straight away. The October section then describes a related failure: the checks ran on every game but were never given three of their inputs, so some boundaries had no working check. The closing section draws the lessons: checks must run on every execution, and auditing variables before rendering gives early warning. It also restates the limits: the audit detects but doesn't prevent, and the "nothing rendered" finding comes from a single search.

## 2. Apply the explanation

**Probe:** Suppose the shared bundle had stayed in place in mid-May, and a template edit made the healer's discussion template name the wolf-roster placeholder. What would have happened, and would the checks have caught it?

**Answer from the page:**
- The healer's model would have seen the wolf roster. A template "fills in only the placeholders it names", and the bundle's values pass to the variables "unchanged".
- Nothing would have flagged it. Until 6 June the checks ran "from a notebook cell after a game", and "Nothing runs the checks".
- Once the checks were wired in, they would have produced the same two `LEAK:` lines as in the exhibit. "A flag says private data crossed the boundary… not that a model saw it." So the flag can't tell a rendered leak from an unrendered one. Telling them apart needs a template search like the June one.
- Even then, it would have been reported after the game: "it detects rather than prevents."

**Links I supplied:**
- The page says auditing at the data layer "made June an early warning". It doesn't say that this design gives up the ability to tell a real exposure from a latent one. I worked that out by combining the first paragraph of "What the checks found" with "Did any model see it?".
- The closing lesson "a boundary that does not reject is not a boundary" appears to argue against the audit's own detect-only design. The page never resolves that, so I couldn't say whether anything in the system now rejects.

## 3. Findings

**1.**
- **Where:** "The same shape, four months later": "those three checks ran on every game, received nothing, and reported nothing."
- **Kind:** missing connection
- **What broke:** The page never says what happened when the three checks were finally given their inputs. Did they find violations in October games, or nothing? I also can't tell how long the dead-player and withheld-line checks were inert. The phrase "an optional input since the checks were first wired in" hints it was since 6 June, but the page doesn't say so. Without the outcome and the time window, the section establishes a risk but not whether that risk caused any harm, unlike the June section, which answered "did any model see it?".
- **Repair:** State how long each of the three checks was inert, and what the checks reported once they were fed (or that no past games were re-checked).
- **Severity:** blocking

**2.**
- **Where:** "The same shape, four months later": "a check that is present but receives nothing from the path that actually runs."
- **Kind:** missing connection
- **What broke:** In June the checks weren't on the running path at all. In October they were on the path but weren't given their inputs. The page calls these "the same shape", but its own definition of that shape fits October better than June. I had to reconstruct the shared principle myself: a check that is never fed real data from the running path gives false confidence.
- **Repair:** Name the common pattern in one sentence that covers both cases, and say plainly how the two differ.
- **Severity:** worth fixing

**3.**
- **Where:** "Where the bundle came from": "put it into the common part of both builders, the discussion's and the vote's"
- **Kind:** missing connection
- **What broke:** The opening says the rewrite gave speakers one bundle carrying three roles' private fields. This paragraph says a separate change put the Vigilante feedback into the common part of both builders. So I can't tell whether the Vigilante leak in discussion came from the shared bundle, from this second change, or from both. "A new field that day" isn't tied to a date in the timeline either, so I don't know whether the "three days" applies to this field.
- **Repair:** Date the change that added the Vigilante field, and say which mechanism carried that field into speakers' inputs and which carried it into voters' inputs.
- **Severity:** worth fixing

**4.**
- **Where:** "What this establishes": "'a boundary that does not reject is not a boundary'" next to "it detects rather than prevents"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The first lesson reads as a rule that boundaries must reject. Two sentences later the page states that its own mechanism only detects. The page doesn't say whether this lesson led to anything that rejects (for example, the input builder or the step's declared field list) or is an unmet goal. "The record" whose words are quoted is also never identified.
- **Repair:** Link each quoted lesson to the incident detail that supports it, and say whether anything now rejects or what does the job of rejection. Identify the record.
- **Severity:** worth fixing

**5.**
- **Where:** "What the checks found", first paragraph: "after each game the batch runner plays (the script that plays games in bulk) the checks read those records"
- **Kind:** repeats parent context / other
- **What broke:** The parenthetical breaks the sentence, so I had to reread it to parse it. Most of the paragraph also re-explains what the parent already covered: payload, recorded variables, post-game checks. The new content is the point that a flag means the bundle carried the data, not that a model saw it, plus the `LEAK:` label note, and those get buried.
- **Repair:** Cut the restated mechanism down to a pointer to the parent and keep the "flag ≠ seen" point. Define the batch runner in a separate clause or drop the definition.
- **Severity:** worth fixing

**6.**
- **Where:** Opening, and the table's third row: "the Vigilante's shot feedback" … "The Vigilante is a town role that may shoot at night"
- **Kind:** term before introduction
- **What broke:** The parent never mentions the Vigilante. Here it appears in the opening and in the table before it is defined in the paragraph after the table. "Town" as a faction is also not defined by the parent, whose audiences are everyone, one faction (wolves) and one seat.
- **Repair:** Define the Vigilante, in a clause, at its first mention.
- **Severity:** worth fixing

**7.**
- **Where:** "What the checks found": "the first batch run … reported 109 flags" (opening) and "the first game played with the checks … produced 109 flags"
- **Kind:** unit or term changes meaning
- **What broke:** The opening says "batch run" and this section says "game", so I wasn't sure they were the same thing until I read the later log line "1 succeeded". I also can't tell which inputs the 38 and 33 come from: discussion turns only, or votes too. The page implies discussion only, because only speakers got the shared bundle, but doesn't say so.
- **Repair:** State once that the batch was a single game, and say which turns the "inputs caught" column counts.
- **Severity:** taste

**8.**
- **Where:** "Why it went unnoticed, and the fix": "The checks that existed were correct and present the whole time." / "The checks that existed were right; nothing fired for three days…"
- **Kind:** detail that does not change understanding
- **What broke:** The section opens and closes with the same point, and the timeline in between already shows it.
- **Repair:** Remove one of the two statements.
- **Severity:** taste

**9.**
- **Where:** "The same shape, four months later": "the boundary's evidence report was re-read against the code before this write-up"; "narrator's announcements"; "situation-summary templates"
- **Kind:** term before introduction
- **What broke:** "Evidence report", "narrator" and "situation-summary" templates are internal names that appear once and are never explained. The narrator one matters because the eliminated-player fix depends on it.
- **Repair:** Gloss "narrator" in a clause. Replace the other two with plain descriptions, or drop them.
- **Severity:** taste

**10.**
- **Where:** "Why it went unnoticed, and the fix": "the same block is empty between its banners"
- **Kind:** other
- **What broke:** "The same block" points back to an earlier exhibit, but that exhibit showed only `LEAK:` lines, not the banners.
- **Repair:** Show the banners around the earlier flag pair, or describe the block without "same".
- **Severity:** taste

## 4. Highest-impact improvements

1. Finish the October section: say how long each check was inert and what the checks reported once they were fed.
2. State one pattern that covers both the June and October failures, and tie each closing lesson (especially "does not reject") to what the system now does.
3. Shorten the first paragraph of "What the checks found" to its new point (a flag means the bundle carried the data, not that a model saw it) and remove the mechanism the parent already explained.
