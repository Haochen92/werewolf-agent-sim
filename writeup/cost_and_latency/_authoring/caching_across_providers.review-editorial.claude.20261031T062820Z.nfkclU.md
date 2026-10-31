<!-- editorial review of ../../../../tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/2974547e-8a33-4e2f-82a4-9571ae2b95e4/scratchpad/editorial_tree/writeup/cost_and_latency/caching_across_providers.md by claude (opus), 2026-10-31T06:28Z -->

## 1. The argument as I understood it

The page asks what it took to get real cache reuse from each provider, and what the changes made for caching did to the game. Its answer is that caching works differently with each provider rather than being a switch you turn on. You have to measure reuse, because Gemini's automatic cache never fired. You have to lay the prompt out so every seat and call type shares the transcript. On Claude you have to place marks a growing transcript can still find, and on OpenAI breakpoints. And you have to stop the provider enforcing the per-seat output schema, because the schema was part of what the cache matched. The sections follow that order. A provider table and the write cost come first, then the June measurement failure, the layout change with probe results, the mechanics of marks and breakpoints, and the schema change. The page then turns to a side effect: Haiku reported more reasoning in text-schema mode, and a replayed turn decided better. It ends with paired-game costs and open questions. The central answer is clear. The schema section and the reasoning section are where it is hardest to follow.

## 2. Apply the explanation

**Probe:** Under the current layout, but with the schema still enforced by the provider, seat A votes and then seat B votes a moment later on Claude. Can B's vote read the transcript A's vote stored? What changes once the schema is sent as text?

**Answer from the page:** No. "When the provider enforces the schema, the schema behaves like the start of the prompt: on Claude it is part of what the cache matches." A vote schema lists "the legal targets… That list differs for every seat, since a seat cannot target itself." So "each seat's vote had its own cache." With the schema sent as text after the shared part, "Every call at the same moment, whatever its type" shares a cache, and the marks section confirms "A vote can read it too once its schema is out of the cache key."

**Gaps I hit:**
- The page says "The alternative keeps the rule," meaning the rule against putting legal targets in the prompt as a list. But a per-seat schema written into the prompt as text seems to contain exactly that list. I could not work out how the rule survives. I would have had to assume something the page doesn't say, such as the text schema omitting the targets.
- A related check failed. I tried to explain Luna's 29% different-seat reuse under the earlier layout. The provider table says OpenAI stores "only prompts that end at a boundary," and in the earlier layout the role card sat in the system message. By the page's own mechanism, a different seat should therefore match nothing, as Haiku's 0% did. Yet the explanation says Luna's automatic cache "could reuse whatever opening two prompts shared." I could not reconcile these from the page.

## 3. Findings

**1.**
- **Where:** Lay the prompt out…, "Luna's automatic cache could reuse whatever opening two prompts shared"
- **Kind:** missing connection
- **What broke:** The provider table and the later OpenAI paragraph both say OpenAI stores entries only at boundaries: the end of the system message, the latest user message, or a breakpoint. In the earlier layout the per-seat role card was in the system message, so a different seat should have shared no stored boundary. The table nonetheless shows Luna at 29% for a different seat, and the prose describes behaviour that sounds like DeepSeek's any-shared-prefix rule. The OpenAI paragraph adds that in games Luna reused "only the system message," which deepens the puzzle. I could not tell which description of OpenAI is right.
- **Repair:** Explain in one clause which stored boundary the earlier Luna different-seat probe matched, or correct the "whatever opening" wording so it agrees with the table.
- **Severity:** blocking (for this section's mechanism)

**2.**
- **Where:** Taking the schema out…, "The alternative keeps the rule and moves the schema out of the key: write it as text"
- **Kind:** missing connection
- **What broke:** The rule is stated just before: targets are "never written into the prompt as a list the model could misread." A per-seat schema written as text appears to put that list into the prompt. The reader can't see how both statements hold.
- **Repair:** State whether the text schema includes the legal targets. If it does, say how that squares with the rule. If it doesn't, say where the model learns its options.
- **Severity:** blocking

**3.**
- **Where:** Taking the schema out…, "The question was whether unenforced replies would fail often enough for retries to slow the live game."
- **Kind:** missing connection
- **What broke:** The section asks a latency question and the parent cares about responsiveness. The answer comes only as failure rates: 1 in 400, then 1 in 40, six turns failing twice. The page never says whether the live game got slower or what a retry costs in waiting time. The current fallback's "frequency… has not been measured," so the question is left open without being called open.
- **Repair:** Close the question explicitly. Say what one retry costs in wait time, or list the latency effect among the open items.
- **Severity:** worth fixing

**4.**
- **Where:** Taking the schema out… trial table, "3 of 170 Luna replies still failed a content check" vs "1 in about 400 calls on each of Luna and Haiku"
- **Kind:** unit or term changes meaning
- **What broke:** The two columns count different things: a content check on Luna replies only, against validation failures on Luna and Haiku calls. Read across, the enforced mode looks worse than the text mode, which is probably not the intended comparison. The text then switches units again to "seat decisions" for the 74/3,118 figure.
- **Repair:** Compare like with like (the same check, models and unit), or say plainly that the enforced cell measures something else. Name the unit once.
- **Severity:** worth fixing

**5.**
- **Where:** What it did to Haiku's reported reasoning, "One recorded turn had been replayed with the schema enforced, and Haiku had taken in a conclusion without acting on it."
- **Kind:** section order / term before introduction
- **What broke:** This opening refers to a "recorded turn," a "conclusion" Haiku took in, and the deduction engine before any of them is defined. The definitions arrive one and two paragraphs later. I had to reread after reaching the healer-turn paragraph. The section also never says why a decision-quality result belongs on a cost page until the final section ties extra reasoning to Haiku's flat cost.
- **Repair:** Open with why this matters for cost: the text schema raised billed reasoning output. Then define the healer turn and the engine, then give the result.
- **Severity:** worth fixing

**6.**
- **Where:** Healer-turn table, "None reported in 4 of 10 samples; at most 1,312" vs "409–1,233, every sample"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The introduction says the change "made Haiku report more reasoning tokens." In this table the enforced mode's maximum is higher than the text mode's. "More" rests only on the four zero-reasoning samples, and no average or median is given. The 1.5× figure appears only in the last section.
- **Repair:** Give a comparable central figure, such as the median, for both rows, or point to the paired-game 1.5× as the evidence for "more."
- **Severity:** worth fixing

**7.**
- **Where:** Still open, "the other listed models (DeepSeek, GLM and Gemini) run the layout but their reuse… never measured"
- **Kind:** term before introduction / missing connection
- **What broke:** GLM appears for the first time here. It is not in the four-provider table, and I can't tell who serves it. This paragraph also seems to contradict the earlier statement that a model's admission check "now measures caching on three real prompts." If every model must pass that check to play, its reuse has been measured.
- **Repair:** Say whether the admission check gates on caching and when it started applying, and introduce GLM in the provider section or the orientation paragraph.
- **Severity:** worth fixing

**8.**
- **Where:** What each provider stores, "Most of what follows was measured on the two seat models… the June game model was a Gemini model on Vertex."
- **Kind:** more than one job in a paragraph / section order
- **What broke:** This paragraph does three jobs: scope (Haiku and Luna), how seats get their model ("chosen from the menu," which is not defined), and setup for the next section (June's Gemini). It comes after the pricing paragraph, so the reader meets the provider table before knowing which rows the page actually tests.
- **Repair:** Move the scope sentence into the introduction or just before the table. Move the June sentence into "Measure before relying on it."
- **Severity:** taste

**9.**
- **Where:** What it did…, "A later re-run of 16 recorded vote cases… 62%… 77%, against 41% and 61%"
- **Kind:** detail that does not change understanding
- **What broke:** This paragraph gives four percentages and then says the runs "do not isolate the output mode." It adds numbers to remember but no evidence the reader can rely on, and "valid samples" is not defined.
- **Repair:** Cut it to one clause saying a confounded vote re-run pointed the same way, or remove it.
- **Severity:** taste

**10.**
- **Where:** Marks a growing transcript…, "nothing is stored on the application's side, and the code that builds each request places the mark again"
- **Kind:** detail that does not change understanding
- **What broke:** I couldn't tell what misunderstanding this sentence prevents. It interrupts the move from where marks go to how the walk-back works.
- **Repair:** Remove it, or say what would go wrong if the reader assumed otherwise.
- **Severity:** taste

**Not assessed:** The page includes no images. The text-diagram of the walk-back was clear and was read in full.

## 4. Highest-impact improvements

1. Reconcile the two accounts of OpenAI's automatic cache ("only at boundaries" vs. "whatever opening two prompts shared") so the Luna earlier-layout numbers can be explained from the page.
2. Say how sending the schema as text keeps the "targets never written as a list" rule, and close or explicitly leave open the latency question the schema section asks.
3. Reorder the reasoning section so it opens with the cost link and the definitions, give comparable central figures for reasoning tokens, and cut or compress the confounded vote re-run.
