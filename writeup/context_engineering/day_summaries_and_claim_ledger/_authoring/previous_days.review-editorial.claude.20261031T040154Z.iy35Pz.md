<!-- editorial review of writeup/context_engineering/day_summaries_and_claim_ledger/previous_days.md by claude (opus), 2026-10-31T04:01Z; parent excerpt supplied by hand because the parent's Explore line is not a Markdown link -->

## 1. The argument as I understood it

The page explains how earlier days of discussion reach later prompts without a summary's mistakes turning into facts. Its answer has three parts. Once per day, one model call records two lists in fixed fields: accusations, and role claims. Each prompt then rebuilds a "Previous days" section in three labelled blocks, one per author:
- the engine's record, which is exact;
- a claim ledger that code builds and checks against that record;
- the model-written accusations.

The page next shows how one summary error spreads to every player, using two cases. Each case produced a guard: first attribution, then a code rule that drops actions done to the speaker. It explains that judging moved from the model into code because the model's verdicts were useless or wrong. It describes replay cases as regression checks and closes with what is untested: whether a summary loses anything compared with the full transcript, and the error rate.

## 2. Apply the explanation

**Question:** On day 3 a model player says only "I was protected last night". It claims nothing and leaves its claim field empty. The summariser records "player_X claimed healer — Night 2: protected player_X". What reaches the claim ledger?

**Answer from the page:**
- The speaker gave no field of that kind, so the ledger uses the summary's transcription: "from the summary's transcription only where the speaker gave no field of that kind".
- The summariser's instruction says "I was protected" claims no role. But the page says "The code rule is the guard, not the instruction". So the instruction alone may not stop the claim.
- The code rule "drops a claimed action that can only have been done to the speaker (a block, a watch, a check on oneself)". Self-protection is not on that list. The claimed role is dropped "only for the one case seen here, a Chanteuse claim resting on a self-block".

So as far as the page lets me tell, "claimed healer" would reach every player's ledger as a claim.

**Gaps I had to work around:**
1. The page doesn't say whether a protection can count as something that "can only have been done to the speaker". That depends on whether a healer can protect itself, which the page never covers.
2. The probe only works because the Chanteuse case shows that model players can trigger the fallback. The earlier description implied they can't (Finding 1).

## 3. Findings

**1.**
- **Where:** One call, two lists: "a human player, whose typed line has no fields, or a game recorded before the fields existed"
- **Kind:** caveat reverses an earlier claim
- **What broke:** The colon reads as a complete list of when the fallback applies, so I took the summary's claims to be a rare backup. Later the Chanteuse case shows it applies to any model player who leaves its claim field empty: "it left the field empty… so for that player the ledger fell back on the summary's transcription". That includes every player who makes no claim, which is exactly where an invented claim does the most harm.
- **Repair:** Where the fallback is introduced, state its actual scope: any seat that fills no claim field that day, with humans and older games as examples.
- **Severity:** blocking

**2.**
- **Where:** One call, two lists: "Since mid-October a speaking player states… the role it claims and the night actions"
- **Kind:** unit or term changes meaning
- **What broke:** This reads as though speaker fields didn't exist before mid-October. Then the early-October Chanteuse game has "a claim field", and the case ends: "fields were extended from its role to its claimed night actions". I had to work out that a role field came first and night-action fields were added in mid-October.
- **Repair:** Date the two fields separately where they are introduced.
- **Severity:** worth fixing

**3.**
- **Where:** Why earlier days cannot simply be replayed: "That is why one model call per day records the day in fixed fields, and code builds the rest."
- **Kind:** section order
- **What broke:** This section argues that claims must arrive as fields and that this is why the summary uses them. The next section then says the speaker's own fields are the "better source" and the summary is only the fallback. The opening reason therefore justifies a role the summary has mostly lost. What the summary alone now supplies (accusations, retractions, plans, and the fallback) only appears afterwards.
- **Repair:** In the opening, say that claims come from speaker fields first, then the summary, and what the summary is the only source for.
- **Severity:** worth fixing

**4.**
- **Where:** The cascade section, "The guard was attribution: I changed the summariser…", and Why judging left the model, "The attribution rewrite also gave the summariser the game master's record"
- **Kind:** section order
- **What broke:** The design history is spread across three sections:
  - the story-retelling section was removed (cascade section);
  - the verdicts and the accusation record check came and went (judging section);
  - speaker fields arrived in mid-October (two lists section).

  "The accusation's record check stayed" sent me back to find which check stayed. "The summary then still had prose sections" requires a timeline the page never gives.
- **Repair:** Move "Why judging left the model" directly after the attribution case, since it describes the same rewrite. Alternatively, give the sequence of versions once in a short dated list.
- **Severity:** worth fixing

**5.**
- **Where:** Why judging left the model, "Across those 66 summaries the record check was written 27 times", and How it runs, "flawed as often (18 of 30 summaries each…)"
- **Kind:** number before orientation
- **What broke:** The two-model comparison appears first only as a source for the record-check count. Its main result, which model to use, comes two sections later. That result uses "flawed", which is never defined. I couldn't tell whether the 27 wrong record checks are part of the 18 flawed summaries per model.
- **Repair:** Report the comparison in one place: what was compared, what counted as flawed, then both results.
- **Severity:** worth fixing

**6.**
- **Where:** One call, two lists (the summary excerpt) and What a player reads (the prompt block): "investigator", "trailseer", "Suspicious", "illusionist", "serial killer"
- **Kind:** term before introduction
- **What broke:** Both examples use roles that are only defined after the prompt block. The serial killer is never defined. I pieced together that attacks on it fail from the first case, and "A lone killer, playing for neither side" may or may not be the same role. Without these definitions, the prompt block's "Record: … as claimed" can't be read on first pass.
- **Repair:** Move the roles paragraph before the first example, add the serial killer and its survival of attacks, and use one name for it throughout.
- **Severity:** worth fixing

**7.**
- **Where:** What a player reads: "Night 1: followed player_7; says they visited player_8"
- **Kind:** missing connection
- **What broke:** The block is "built in part from the summary above". But the summary excerpt has no player_8, and "they" could mean player_3 or player_7. I couldn't trace this ledger line back to its source, though tracing it is the point of showing both examples.
- **Repair:** Say where the player_8 detail came from (speaker field or the part of the summary that was cut), and name the subject of "visited".
- **Severity:** worth fixing

**8.**
- **Where:** The cascade section, "A premise returned as narration": "since the same players had rejected the claim while reading the discussion"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** Two villagers rejected the argument. Three town players accepted it on day 4. "The same players" doesn't fit those numbers, so I couldn't tell how much evidence there is for the summary being "the likely route".
- **Repair:** Say which of the three had rejected it during the discussion.
- **Severity:** worth fixing

**9.**
- **Where:** The cascade section, "A speaker's own words misread": "In 10 re-runs of that day's summary, before and after the fix"
- **Kind:** unit or term changes meaning
- **What broke:** Is this 10 in total (5 before, 5 after) or 10 each? Elsewhere replays use "five samples a case". This matters for "it is rare".
- **Repair:** Give the split.
- **Severity:** worth fixing

**10.**
- **Where:** Why judging left the model: "and the verdicts were lost between game days anyway"
- **Kind:** missing connection
- **What broke:** This is one of three reasons judging left the model, but it isn't explained. I couldn't tell whether this was a bug or a consequence of the design.
- **Repair:** Explain it in one clause, or drop it if the other two reasons are enough.
- **Severity:** taste

**11.**
- **Where:** How it runs: "A stalled or failed call goes to the game's rescue model where one is assigned"
- **Kind:** detail that does not change understanding
- **What broke:** "Rescue model" is undefined, and the failure path doesn't affect the summary's design or the evidence. The page also points to another chapter for it.
- **Repair:** Cut it to a pointer, or move it into the production chapter.
- **Severity:** taste

**12.**
- **Where:** How it is checked: "a copied record-check line"; Evidence: "the e06 case"
- **Kind:** term before introduction
- **What broke:** Neither label is explained. The first probably relates to the removed record check, but the page doesn't say so.
- **Repair:** Gloss the first in a few words, and replace "e06" with a description.
- **Severity:** taste

## 4. Highest-impact improvements

1. Where the fallback is introduced, state its actual scope (any seat that fills no claim field, including model players making no claim) and date the role field and the night-action fields separately.
2. Put the design history in one ordered place, with judging-left-the-model next to the attribution rewrite, and report the two-model comparison once, with "flawed" defined.
3. Define the roles, including the serial killer, before the first example, so the summary excerpt and the prompt block can be read when they first appear.
