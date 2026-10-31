<!-- editorial review of ../../../../tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/2974547e-8a33-4e2f-82a4-9571ae2b95e4/scratchpad/editorial_tree/writeup/cost_and_latency/caching_across_providers.md by claude (opus), 2026-10-31T06:24Z -->

## 1. The argument as I understood it

The page asks what each provider needed before prompt caching actually reused input, and what the changes made for caching did to the game. Its central answer is that caching is "a contract with each provider, not a flag." Reuse came from four steps: measuring it (because the Gemini automatic cache never fired), putting shared content first so every seat and call type shares the transcript, placing cache marks that a growing transcript can still find, and taking the provider-enforced schema out of the cache key. The sections follow those four steps. The page then reports a side effect of the schema change: Haiku reasoned more, and on one replayed turn and a vote re-run its decisions improved. It closes with the paired-game cost result and what remains unmeasured. I can state the central answer. The last two sections loosen the link between the argument and its evidence, because the reasoning finding is framed as a deduction-engine result and the quality claims are bounded differently in different places.

## 2. Apply the explanation

**Probe:** Under the current layout on Claude, suppose votes still had their schema enforced by the provider. Could a vote read the transcript entry that a discussion turn had just written?

**Answer from the page:** No. "When the provider enforces the schema, the schema behaves like the start of the prompt: on Claude it is part of what the cache matches," and "Two requests with identical text and different schemas share nothing." A vote's schema lists legal targets, so it differs from a discussion turn's schema and the vote would not find the entry.

**Rereading needed:** I first answered "yes," because the marks section says "turn 2 can be any seat's turn, or a vote, and still read the entry; that is the 71% in the table above." That sentence only holds once the text schema is in place, which is introduced two sections later. Until then, the layout section reads as if moving the role card alone let votes share. I also could not tell whether the 71% "different seat" figure was measured with the text schema or the enforced one. The page doesn't say, and I didn't fill that in.

## 3. Findings

**1.**
- **Where:** "What it did to Haiku's reasoning": "replaying the same turn in the live output mode disagreed with that earlier replay."
- **Kind:** missing connection
- **What broke:** The earlier replay measured the engine's effect (the conclusion reached the notes, but the decision barely moved). The table that follows keeps the engine on in every row and varies only the output mode. It never shows engine-off against engine-on in the live mode. So I can't tell whether the engine now moves the decision, or whether the text schema improves the read on its own. The section opens by framing a deduction-engine question and then answers an output-mode question.
- **Repair:** Either add the engine-off comparison in the live mode, or reframe the section's opening around output mode and state the engine-related consequence separately: replays must pin the output mode.
- **Severity:** blocking

**2.**
- **Where:** Opening: "a replay found its decisions better for it". Also the closing section: "The only quality check, 18 Luna discussion turns…"
- **Kind:** claim reads stronger than its support on the page / caveat reverses an earlier claim
- **What broke:** The parent excerpt says "an improvement in play quality was not established." The page's opening says decisions were better. The reasoning section narrows that to "one turn and a vote re-run," and the last section calls a Luna bench "the only quality check." That last phrase contradicts the healer replay and the vote re-run, which are also quality checks. I end up with three different scopes for what has been shown about quality.
- **Repair:** Bound the opening claim to "one replayed Haiku turn." Say what "only" covers in the closing (for example, the only check of the layout on Luna's play). Then say briefly how this reconciles with the parent's statement.
- **Severity:** worth fixing

**3.**
- **Where:** "Marks a growing transcript can still find": "turn 2 can be any seat's turn, or a vote, and still read the entry"
- **Kind:** section order
- **What broke:** See the probe above. The claim relies on the schema change, which hasn't been introduced yet. The layout section's account of why votes, night actions and memory lookups "each started from a prompt of their own" also gives no cause. I couldn't tell whether the cause was the role card, the schema or the instructions.
- **Repair:** Give a one-clause forward reference ("once the schema is moved out of the key; see below"), or move the schema section before the marks section. In the layout section, name what made each call type diverge.
- **Severity:** worth fixing

**4.**
- **Where:** Schema table, "Replies that failed validation": "3 of 170 Luna trial replies" / "1 in about 400 trial calls" / "about one seat decision in forty"
- **Kind:** unit or term changes meaning
- **What broke:** One cell uses three units: replies, trial calls and seat decisions in games. Failures in games run about ten times the trial rate, and the page doesn't explain why. "A content check" in the enforced column is never defined. The section also poses an open question ("whether unenforced replies would fail often enough to slow the live game") and never answers it. The reader has to infer the verdict from the fact that the switch happened.
- **Repair:** Use one unit per comparison, or label each figure. Explain or note the gap between trials and games. Define "content check." State the answer to the retry question before "switched to the text schema."
- **Severity:** worth fixing

**5.**
- **Where:** Marks section, OpenAI paragraph: "exactly 4,582 cached tokens on each of seven discussion calls" … "read 2,561 of 2,678 tokens"
- **Kind:** number before orientation
- **What broke:** The paragraph doesn't say which layout the 4,582-token case used. The probe prompt (2,678 tokens) is smaller than the cached system message from the game case (4,582), so these are clearly different prompts, but the page doesn't say so. 2,561 of 2,678 is about 96%, while the table shows Luna at 75% for the same seat's next turn. The reader can't reconcile the two figures. It is also unexplained why OpenAI needs a breakpoint on every transcript line when Claude needs a mark only on the last one.
- **Repair:** Name the layout and the prompt for each figure, and relate the 96% to the 75% in the table (or drop one of them). Add a clause on why OpenAI needs per-line breakpoints.
- **Severity:** worth fixing

**6.**
- **Where:** After the provider table: "Most of what follows was measured on the two seat models… the June game model was a Gemini model on Vertex."
- **Kind:** more than one job in a paragraph
- **What broke:** This paragraph introduces Haiku and Luna (the parent used both without introducing them), explains the model menu, mentions GLM, and sets up the June Gemini history. GLM doesn't appear in the four-provider table, so I can't place it. The pricing paragraph ("Writing is not free") belongs with the table but is separated from it by this paragraph. The opening's "Each… charges more to write" covers all four providers, but the page only supports it for Claude and OpenAI.
- **Repair:** Put the pricing paragraph directly after the table, and cover only Claude and OpenAI in the cost claim. Introduce Haiku and Luna with the provider rows they belong to. Say which provider GLM uses, or leave it out until the closing section.
- **Severity:** worth fixing

**7.**
- **Where:** "What the paired games showed": "found no difference beyond noise where only about ten percentage points more replies marked wrong would have shown"
- **Kind:** other (unparseable sensitivity statement; undefined term)
- **What broke:** "Factual-error bench" is not defined. The detection threshold is phrased so that I had to reread it to see what size of effect the check could have found.
- **Repair:** Say in one plain clause what the bench scores and the smallest difference it could detect.
- **Severity:** worth fixing

**8.**
- **Where:** Reasoning section: "other low-cost models had reported none under structured output or a forced tool call, but none was compared…"
- **Kind:** detail that does not change understanding
- **What broke:** This brings in other models and an undefined "forced tool call," then says they weren't compared. It doesn't affect the Haiku finding or the lesson to pin the output mode.
- **Repair:** Keep the caveat "zero reported does not mean no reasoning" and remove the rest of the clause.
- **Severity:** taste

**9.**
- **Where:** "What the paired games showed": "On Haiku the cost per call stayed at $1.10"
- **Kind:** missing connection
- **What broke:** The parent excerpt attributed Haiku's higher whole-game cost to more participation. This section covers the same paired games but doesn't mention participation. A reader moving between the two pages may wonder whether that finding still holds.
- **Repair:** Add one clause pointing back to the participation result, or say that this page covers cost per call only.
- **Severity:** taste

## 4. Highest-impact improvements

1. Reframe the reasoning section around output mode, or add the missing engine-off rows, so that the table answers the question the section opens with.
2. Set one consistent scope for the quality claims across the opening, the reasoning section and the closing, and reconcile it with the parent's "not established."
3. Give each failure-rate and cache-share figure a single labelled unit and prompt. Make the schema decision explicit before the marks section relies on it, either by moving the section or with a forward reference.
