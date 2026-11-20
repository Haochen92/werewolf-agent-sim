<!-- editorial review of writeup/context_engineering/day_summaries_and_claim_ledger/previous_days.md by claude (opus), 2026-10-31T03:52Z; parent excerpt supplied by hand because the parent's Explore line is not a Markdown link -->

## 1. The argument as I understood it

The page explains how a game's earlier days reach later prompts without turning a summariser's mistakes into facts. Its answer is that one model call per day writes the discussion into fixed fields: accusations and role claims. The players' prompt then rebuilds that record into three labelled blocks, ordered by trust:
- the engine's exact record;
- a claim ledger that code builds and checks against the record;
- the summariser's account of the accusations.

The rule behind this design is that the summariser records and code judges. The page backs this with two cases where an error spread to every player and each case produced a guard. It also describes an earlier attempt to let the model judge claims, which failed. The page then explains how fixes are checked through replay cases and unit tests. It ends by saying the summary has never been compared with giving players the full transcripts. The central answer is clear. The difficulty is that the speaker's own claim fields are part of the mechanism but only appear late on the page.

## 2. Apply the explanation

**Question:** Suppose that in the roleblocked game the Investigator had filled in its own claim field on day 2, and the summariser still wrote "player_2 claimed chanteuse — Night 1: blocked player_2". What would the day-3 claims block have shown?

**Answer from the page:** The false Chanteuse claim would not have reached the ledger. "The ledger reads those first and the summary's transcription only for a player who filled no field that day." The page traces the failure to that fallback: "the Investigator had described its night without filling in its own claim field, so the ledger fell back on the summary's transcription." Role claims reach players only through the ledger block. The accusations block shows accusations, not role claims. So the line would not have appeared.

**Gaps I had to fill or reread:**
- The mechanism ("reads those first") is in "Why judging left the model", two sections after the case that depends on it. I had to read ahead to answer the question.
- "Reads those first" could mean the speaker's fields take priority, or that both sources are merged with the speaker's fields read first. Only "only for a player who filled no field" settles it as replacement.
- The game is dated 2026-10-10, and the speaker fields have existed "since mid-October". I cannot tell whether the Investigator failed to fill in a field or the field did not exist yet. If it did not exist, my scenario could not have happened in that game.
- I assumed that the "summary's role claims" only reach players through the ledger. The three-block list implies this but does not say it.

## 3. Findings

**1.**
- **Where:** "Why earlier days cannot simply be replayed": "That is why one model call per day records the day in fixed fields, and code builds the rest". Also "Why judging left the model": "Since mid-October a speaking player fills in, as fields of its own answer…"
- **Kind:** section order
- **What broke:** The opening argues that claims must arrive as fields, so the summariser writes them. The first two sections therefore present the summariser as the source of the ledger's claims. The roleblocked case then depends on a fallback ("fell back on the summary's transcription") that has not been explained yet. The parent excerpt said "Each speaker states its own claims in fields", so the page's opening appears to contradict what I had just read. I only reconciled the two in the fifth section.
- **Repair:** Put the speaker-field arrangement in "One call, two lists" or just before the three blocks: speakers supply their own claims, and the summary's claim list is the fallback. The reasoning in "Why judging left the model" can then just give the history.
- **Severity:** blocking

**2.**
- **Where:** "How a carried-forward error cascades": "On 89 replayed turns from earlier games, … bad samples from 36% to 31% of 267". Also "How it is checked": "turning reasoning on cut bad samples from 31% to 10%".
- **Kind:** number before orientation · caveat reverses an earlier claim
- **What broke:** I don't know what makes a sample "bad", who judged it, or how 89 turns became 267 samples. The improvement in "24 cases better and 14 worse" is counted in cases, which may be turns, so the unit changes again. Three sections later, a caveat says the comparison "says little" about models that reason. By then I had already taken the number as weak support for attribution.
- **Repair:** Either remove the number, since the attribution guard rests on the case, or keep it with a one-clause definition of a bad sample and the reasoning caveat placed directly after it.
- **Severity:** worth fixing

**3.**
- **Where:** "the replay caught it before it shipped". Also "In 10 replayed samples of that day". Also "Each summary that went wrong … was frozen as a **replay case**".
- **Kind:** term before introduction · unit or term changes meaning
- **What broke:** The page uses "replay" in the cascade section but defines it two sections later. The word also covers two different methods. "Replayed turns" re-run players' decisions. "Replay cases" re-run the summariser on frozen input. I couldn't tell which method produced each number.
- **Repair:** Define the replay case before the cascade section, and use a distinct name for the replayed player turns.
- **Severity:** worth fixing

**4.**
- **Where:** the "Previous days" sample: "Record: player_9 was revealed as illusionist, as claimed."
- **Kind:** missing connection · term before introduction
- **What broke:** player_5 claimed a Suspicious read, not that player_9 was an illusionist, so "as claimed" doesn't match the claim. I can't tell why an illusionist result confirms a Suspicious read, or whether an illusionist is a wolf, without game knowledge the page never gives. Trailseer, illusionist and serial killer also go unexplained, as does "a visit alone does not establish what they did there". This is the page's main example of the ledger checking a claim, so the gap matters.
- **Repair:** Add one line before or after the sample naming the roles it uses and why this reveal confirms this read. Alternatively, choose a sample whose check needs no role knowledge.
- **Severity:** worth fixing

**5.**
- **Where:** "One call, two lists": "writes two lists and nothing else" … "A plan for the coming night goes in a separate list"
- **Kind:** unit or term changes meaning
- **What broke:** A third list appears straight after "two lists and nothing else". "Retracted" and the plans list come back later as summary-only sources. It's unclear whether the plans list is part of the role-claims list or separate from it.
- **Repair:** State the structure exactly: two lists, with plans as a sub-list of claims, or else three lists.
- **Severity:** worth fixing

**6.**
- **Where:** "But size is not the deciding reason". Also "What is not established": "kept for the two reasons the page opened with: it bounds the prompt…". Also "That objection stands."
- **Kind:** caveat reverses an earlier claim · missing connection
- **What broke:** The page first sets size aside, then lists it as one of the two reasons. "That objection" has no antecedent on this page. It only makes sense through the parent's "has not been shown to produce better play".
- **Repair:** Make the two passages agree on whether size is a reason or a side benefit, and replace "That objection" with the objection itself.
- **Severity:** worth fixing

**7.**
- **Where:** "In a ten-seat game read on 2026-10-10". Also "Since mid-October a speaking player fills in…"
- **Kind:** other (ambiguity)
- **What broke:** I can't tell whether the field existed in that game, so I can't tell whether the cause was a player not filling the field or a field that did not yet exist. "Read on" also suggests the game was reviewed on that date rather than played.
- **Repair:** Say whether the claim field existed in that game.
- **Severity:** worth fixing

**8.**
- **Where:** "In 10 replayed samples of that day, before and after the fix, the invented claim never recurred". Also the table row "'I was roleblocked' filed as a denial: 15 of 15".
- **Kind:** missing connection
- **What broke:** The same phrase causes two different failures. One case was never reproduced. The other reproduced 15 out of 15 times. On first reading I took the table row as the Chanteuse case and thought the numbers contradicted each other.
- **Repair:** In the table row, say this is a separate failure from the Chanteuse misreading.
- **Severity:** worth fixing

**9.**
- **Where:** "Why judging left the model": "Across the 66 summaries judged … Both models were flawed in 18 of 30 summaries, so the summary stayed on the game's own model."
- **Kind:** more than one job in a paragraph · number before orientation
- **What broke:** The paragraph mixes two decisions: removing the record check, and choosing a model. 6 days × 5 samples × 2 models gives 60, and I can't reconcile that with 66 or with 30 per model. It's also unclear why an equal flaw rate means keeping the game's model. Model choice doesn't affect the argument that the model should record rather than judge.
- **Repair:** Keep the record-check result (27 written, all wrong) here. Move the model choice to "how it runs", or remove it, and reconcile the counts.
- **Severity:** worth fixing

**10.**
- **Where:** "the claim record built from the summaries dropped the field so the next day's summariser never saw an earlier verdict … The next day the verdicts went"
- **Kind:** unit or term changes meaning · detail that does not change understanding
- **What broke:** "Next day" means a game day in the first clause and a calendar day in the second. The dropped-field bug is a side issue next to the two reasons that carry the point: the verdicts were nearly all "unverified", and "supported" was subjective.
- **Repair:** Remove the dropped-field clause and date the change in calendar terms.
- **Severity:** taste

**11.**
- **Where:** "The headers came in with the October pass that gave each night actor its own record"
- **Kind:** detail that does not change understanding
- **What broke:** "October pass" and "night actor its own record" are unexplained, and the paragraph breaks the step from the blocks to the cascades. The useful content is the reason the headers exist: engine facts and model text looked the same once rendered.
- **Repair:** Reduce it to that reason and attach it to the sentence introducing the labelled blocks.
- **Severity:** taste

**12.**
- **Where:** "dropped the story-telling section where the premise had entered as narration"
- **Kind:** term before introduction
- **What broke:** The page has described the summary only as two lists, so I didn't know a narrative section had existed.
- **Repair:** State briefly that the summary used to include a narrative section.
- **Severity:** taste

**13.**
- **Where:** the table, "30 of 30 samples lost" … "7 of 30 on one summariser model and 0 of 30 on another"
- **Kind:** number before orientation
- **What broke:** At "five samples a case", 30 implies six cases, but the page doesn't say so. I also can't tell whether the "before" figure covers one model or both.
- **Repair:** Give the case count and the models in the row or the lead-in.
- **Severity:** taste

**14.**
- **Where:** opening: "The agent's own earlier thinking returns as a private note it wrote last turn"
- **Kind:** repeats parent context
- **What broke:** It closely restates the parent and adds nothing new. It is short, though.
- **Repair:** Cut it to one clause or remove it.
- **Severity:** taste

**15.**
- **Where:** "(evidence type: concrete_claim)", "a note starting 'Record:' or 'Rules:'", "against its own private record", "three town players, who had seen only this summary"
- **Kind:** term before introduction · unit or term changes meaning
- **What broke:** Several small snags:
  - "evidence type" and "Rules:" notes are never explained.
  - "Private record" seems to mean the private note, which risks confusion with the game master's record.
  - "Had seen only this summary" reads as if those players never saw day 3, when presumably they mean that on day 4 they were shown only the summary.
- **Repair:** Gloss these terms or remove them, keep "private note", and say "on day 4 were shown only this summary".
- **Severity:** taste

## 4. Highest-impact improvements

1. Introduce speaker claim fields and the summary-as-fallback before the three blocks and the cascades, so the opening, the parent and the roleblocked case all describe the same mechanism.
2. Define the replay case before the cascade section, and separate it by name from the replayed player turns. Then either remove the 36%→31% figure or keep it with its reasoning caveat beside it.
3. Make the sample "Previous days" block readable without game knowledge: name its roles and why "as claimed" holds. Also move the summariser-model choice and the headers history out of the argument.
