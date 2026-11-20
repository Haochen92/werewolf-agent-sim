<!-- editorial review of writeup/context_engineering/day_summaries_and_claim_ledger/previous_days.md by claude (opus), 2026-10-31T04:07Z; parent excerpt supplied by hand because the parent's Explore line is not a Markdown link -->

## 1. The argument as I understood it

The page explains how a player's prompt gets earlier days' discussion, and how that is done without passing summary errors on as fact. Its answer is that earlier days are condensed because of size. At the end of each day, one model call records two lists: accusations, and role claims written in fixed words. The summariser records only and never judges. Code then builds a claim ledger. It takes claims from the speaker's own answer fields first and from the summary only when the speaker left a field empty. It checks those claims against the engine's record and shows them in a third prompt block. The three blocks are labelled by how far to trust them. The page then:
- gives two real cascades and the guard each produced;
- explains why judging moved from the model to code;
- shows the replay checks;
- lists what has not been established.

I could state the central answer. Most of the difficulty is in the history and the numbers, not in the design.

## 2. Apply the explanation

**Question:** Take the Chanteuse game again, with one change. Suppose the Investigator had filled its role field with "investigator", but its answer still had no night-action field. Would the false Chanteuse claim have reached the other players?

**Answer from the page:**
- **The role:** The ledger "takes each player's role claims and claimed night actions from the speaker's own fields first and from the summary's transcription only where the speaker gave no field of that kind". The role would come from the field, so it would be "investigator". This fits the page's statement that "the line got through because the Investigator's answer had a claim field and it left the field empty". So the false role would probably not appear.
- **The action:** "Night 1: blocked player_2" has no field to override it, so it would come from the summary. The page then says the ledger "drops a claimed action that can only have been done to the speaker (a block…)". So the action would be dropped as well.

**Gap I had to fill:** The page doesn't say what happens when a role from the field is combined with a night action the summary filed under a different role. Would "blocked player_2" be attached to the investigator claim at all? The phrase "of that kind" says the two kinds are handled separately, but not how the results are merged. I assumed they are merged per player ("folds them into one history per player"). The answer holds, but I had to reread that sentence three times: in the opening, in "a second, better source" and in authors item 2.

## 3. Findings

**1.**
- **Where:** Why judging left the model — "Each model had such an error in 18 of its 30 summaries"
- **Kind:** more than one job in a paragraph
- **What broke:** One paragraph reports a model comparison, gives an error rate, and removes the record check. The list of counted errors includes "a wrong record check", and all 27 record checks were judged wrong. So I can't tell how much of the 18/30 came from the record check, which no longer exists. The natural reading is that about 60% of today's summaries mislead the next reader. Two sections later, "there is no error rate for today's prompt" contradicts that reading without linking back to it. The judge is also unclear: is "a model judged" here the same as "the quality judge built in May"?
- **Repair:** Split the paragraph: first the record-check removal, then the model choice. State plainly that 18/30 measures the old prompt, which still had the record check, and whether it counted record-check errors. Name which judge was used.
- **Severity:** blocking

**2.**
- **Where:** One call, two lists — "Role claims also have a second, better source."
- **Kind:** section order
- **What broke:** The opening section already said speaker fields come first and the summary second. This section describes the fallback (the summary's transcription) in detail, and then calls the primary source "a second, better source". The order of priority flips back and forth, and the source rule is repeated a third time in authors item 2.
- **Repair:** Explain once, in priority order, where claims come from (field first, then summary transcription), before describing the two lists. Then the two lists can be presented as the fallback plus the summary-only material (accusations, retractions, plans).
- **Severity:** worth fixing

**3.**
- **Where:** What a player reads — "player_3 … Night 1: followed player_7; says they visited player_8"
- **Kind:** missing connection
- **What broke:** The summary's role-claim line above says only "followed player_7". The result "visited player_8" appears only in the accusations text. The page says this section is "built in part from the summary above", so I tried to trace each ledger line to its source and couldn't. Was the visit taken from player_3's own field, or from the accusation? The example is meant to show the source rule, but it hides it.
- **Repair:** Say which line came from a speaker field and which from the summary, or use an example whose lines can be traced.
- **Severity:** worth fixing

**4.**
- **Where:** Cascade section, "That rewrite kept the summary's prose sections…", and Why judging left the model, "The attribution rewrite of early October did more than attribute"
- **Kind:** section order
- **What broke:** The history of the two rewrites is told in two pieces, two sections apart. Each piece adds facts the other leaves out: one says the prose sections were removed, the other says verdicts and a record check were added and later removed. I had to rebuild the timeline myself. The dates ("early October", "mid-October", the origin of the labels in a code review) add more history that doesn't change how the design is understood.
- **Repair:** Keep only the rewrite history needed for each guard, and tell the judging history in one place. Cut dates that support no claim.
- **Severity:** worth fixing

**5.**
- **Where:** How it is checked — "7 of 30 on one summariser model and 0 of 30 on another"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The two models aren't named, so I can't tell whether the production model is the one still losing 7 of 30 denials. The "before" figures are also uneven: one figure in row 1, two in row 2.
- **Repair:** Say which model runs in games (the page says it is "the model the seats play on"), and give before and after for the same models.
- **Severity:** worth fixing

**6.**
- **Where:** Authors item 2, "a shot player who lived", and the cascade section, "lost a true Vigilante whose 'held my fire'"
- **Kind:** term before introduction
- **What broke:** Shooting and the Vigilante appear without introduction, although the page carefully lists "the examples below use four roles". The same applies to wolves and the town as sides. The parent mentions only "the town".
- **Repair:** Add the Vigilante (a town shooter) and the sides to the roles paragraph, or link the role list once.
- **Severity:** worth fixing

**7.**
- **Where:** Why earlier days cannot simply be replayed — "and code can gather claims and check them against the record only if they arrive as fields"
- **Kind:** repeats parent context
- **What broke:** Size versus form, and fields being needed for code checks, are both in the parent almost word for word. The paragraph also defines claims, gives the reason they span days, names both sources and the accusations, and ends with "Code builds the rest", which is unclear: the rest of what?
- **Repair:** Shorten this to the new point (claims span days, so they must be gathered per player) and leave the sources to the reordered section in finding 2.
- **Severity:** worth fixing

**8.**
- **Where:** What is not established — "Three gaps follow from the design."
- **Kind:** other
- **What broke:** The third gap, no error rate, is a gap in the evidence, not a consequence of the design. Calling it something that "follows from the design" muddles the list.
- **Repair:** Separate design limits from evidence gaps.
- **Severity:** taste

**9.**
- **Where:** How it is checked — "A call that stalls or fails goes to the game's rescue model"
- **Kind:** detail that does not change understanding
- **What broke:** The fallback path in production doesn't affect the argument here, and the page already points to the production chapter for it.
- **Repair:** Cut it to the pointer, or keep only the raw-transcript fallback, since that changes what players read.
- **Severity:** taste

## 4. Highest-impact improvements

1. Separate the model-comparison result from the record-check removal, and say whether 18/30 describes the current summary. As written, it reads like the current error rate.
2. State the claim-source rule once, field first then summary, before the two lists, and make the day-3 example traceable line by line to its source.
3. Combine the rewrite history into one place and remove dates and origin stories that support no claim. This shortens the cascade and judging sections without losing the guards.
