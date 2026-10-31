<!-- editorial review of ../../../../tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/2974547e-8a33-4e2f-82a4-9571ae2b95e4/scratchpad/editorial_tree/writeup/cost_and_latency/caching_across_providers.md by claude (opus), 2026-10-31T06:18Z -->

## 1. The argument as I understood it

The page asks what it took to get real cache reuse across several providers, and what side effects that work had. Its answer is that caching works differently with each provider and is not something you simply switch on. Getting reuse meant four steps: measure reuse instead of assuming it, put the rules and transcript first so every seat and call type shares them, place cache marks so a growing transcript can still be found, and take the enforced output schema out of the cache key. The page then follows the last change into gameplay. With the schema sent as text, Haiku reasoned more and did better on replayed decisions. In paired games that extra reasoning cancelled Haiku's input saving, while Luna's cost per call fell by 28%. Two side lessons appear along the way: a replay must use the output mode the live game uses, and several providers and effects remain unmeasured.

## 2. Apply the explanation

**Question:** A new model is added for vote calls on DeepSeek. Should its votes send the schema as text, as Luna and Haiku do?

**What the page supports:** The deciding rule is whether a provider-enforced schema becomes part of what the cache matches. The page says: "on Claude it is part of what the cache matches, on OpenAI it is rendered before the messages," and "Two requests with identical text and different schemas share nothing." The cost of switching to text is replies that fail validation ("1 in about 400 trial calls … about one seat decision in forty") plus a fallback call that "reads no cache." So for Claude and OpenAI the trade is clear: cross-seat reuse in exchange for occasional retries.

**Where the page runs out:**
- The page never says whether DeepSeek, or Gemini, includes an enforced schema in its cache key. The provider table says nothing about schemas, so the deciding rule can't be applied to DeepSeek.
- The page doesn't say which output mode the DeepSeek, GLM and Gemini seats use now. "Luna and Haiku switched" suggests the others didn't, but I'm guessing.
- I had to work out for myself that Luna is an OpenAI model and Haiku a Claude model, from "Haiku's rows use cache marks" and "OpenAI stores… so Luna had reused…".
- The reasoning gain might look like a second reason to switch. The page limits it to "one model's evidence," so it can't be used as a general rule.

My answer: only "it depends on the provider's cache key, which the page doesn't describe for DeepSeek."

## 3. Findings

**1.**
- **Where:** "What it did to Haiku's reasoning": "Two weeks later a replay disagreed with live play."
- **Kind:** missing connection · term before introduction
- **What broke:** The page never says what disagreed: which result the replay gave, and what live play showed instead. The next sentence then introduces the healer turn, chapter 3's deduction engine, "blocked" overnight, the Chanteuse role, a "read" and "engine on" in one paragraph, and later "uptake results." Neither the parent nor the page says what the deduction engine does, so "engine on" means nothing to me. I lost the thread of why this section exists until its last paragraph.
- **Repair:** Open the section with the lesson and the actual discrepancy: the engine's measured effect came from a replay pinned to the retired enforced mode, and live play differed in a specific way. Then give the healer turn in one plain sentence: the correct answer, and what the engine is supposed to help with. Drop or gloss "uptake."
- **Severity:** blocking

**2.**
- **Where:** Opening and throughout: "The first design, in June, assumed the then game model's automatic cache"
- **Kind:** term before introduction
- **What broke:** Luna, Haiku, "the then game model" and GLM are never matched to providers. The provider table is organised by provider, but every result is reported by model. I had to infer Luna = OpenAI and Haiku = Claude from captions, and "the then game model" = Gemini from the parent. GLM appears in the last section but not in the "four providers." The page also never says that games mix models across seats, which the caveats about "seats on DeepSeek, GLM and Gemini" assume.
- **Repair:** Near the provider table, add one line or column saying which model runs on which provider, which seats use it, and which output mode each uses.
- **Severity:** blocking

**3.**
- **Where:** "Taking the schema out of the cache key": "That one call reads no cache, and how often it fires is unmeasured."
- **Kind:** caveat reverses an earlier claim
- **What broke:** The table just above reports failures of "about one seat decision in forty across twenty real games," and the retry fires on a failure. So I read the retry rate as about 1 in 40, and "unmeasured" then contradicts the table. Possibly the 1-in-40 figure predates the retry, or counts something else, but the page doesn't say.
- **Repair:** Say how the 1-in-40 figure relates to retry frequency, for example whether it was measured before the retry existed. Also say what happened to a failed reply before the retry was added.
- **Severity:** worth fixing (high)

**4.**
- **Where:** Opening: "This page is about what it took to make four providers actually reuse it"
- **Kind:** caveat reverses an earlier claim · claim reads stronger than its support on the page
- **What broke:** The last section says "the seats on DeepSeek, GLM and Gemini run the layout but were never measured under it." For Gemini the page shows only a one-off explicit-cache test and never says whether games create explicit caches. Only two providers are shown achieving reuse under the current layout. My first reading of the opening was wrong.
- **Repair:** In the opening, limit the claim to what was shown: reuse was demonstrated on Claude and OpenAI, the rules for the other providers are described, and their reuse in play is unmeasured. Say whether Gemini seats use explicit caches in games.
- **Severity:** worth fixing

**5.**
- **Where:** Layout table caption: "Luna's earlier row is its automatic cache, its current row explicit breakpoints (next section)."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The table is introduced as "the same three prompts, before and after" the layout change. For Luna, the caching mechanism changed as well, so its 29% → 69% gain can't be credited to the layout alone. The paired games have the same problem: "the layout with the text schema" bundles two changes, and the arms are never defined, while the parent credits "the revised layout."
- **Repair:** Say plainly that Luna's rows change two things. Define the two arms of the paired games: what the baseline was and what the treatment changed.
- **Severity:** worth fixing

**6.**
- **Where:** "Marks a growing transcript can still find": "in one check a seat's next turn read 9,258 of 10,206 input tokens from cache"; also "a seat's next turn read 2,561 of 2,678 tokens"
- **Kind:** number before orientation
- **What broke:** These checks give about 91% (Haiku) and about 96% (Luna) for the same probe type the table puts at 77% and 75%. Luna's 2,678-token total is also smaller than the 4,582-token system message it supposedly cached before. I couldn't tell whether these are different prompts, game stages or models, so the numbers seem to disagree.
- **Repair:** Name the probe and model for each standalone figure and say why it differs from the table, or drop the figures that the table already covers.
- **Severity:** worth fixing

**7.**
- **Where:** "Taking the schema out of the cache key": "A vote or night action's reply is checked against a schema"
- **Kind:** unit or term changes meaning
- **What broke:** The schema is defined as applying to votes and night actions. Yet discussion turns are affected too: "votes, night actions and discussion turns could not read one another's copy," Haiku "reasoned about 1.5 times as much on discussion turns," and the healer turn's "read" is structured output. I couldn't tell whether discussion turns carry a per-seat schema and whether it changes.
- **Repair:** State that every call type returns structured output, and say which parts vary by seat or call type.
- **Severity:** worth fixing

**8.**
- **Where:** Opening: "That last change, made for cost, also let the game's model reason more."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The opening and the section heading present a mechanism: an enforced schema suppresses reasoning. The later caveat, "Zero reported reasoning tokens do not show that no reasoning happened," undercuts it. What the page actually shows is that, for one model, reported reasoning tokens and decision quality both rose in replay. "The game's model" is also singular, while the effect is shown only for Haiku.
- **Repair:** Present it as an observed association for Haiku in the opening and heading, and keep the caveat next to the first claim.
- **Severity:** worth fixing

**9.**
- **Where:** "Marks a growing transcript can still find": "a long gap between two calls can leave the old boundary too far back to find"
- **Kind:** unit or term changes meaning
- **What broke:** The walk-back is measured in content blocks, that is, transcript lines, but "long gap between two calls" reads as time. I couldn't tell whether the risk is many new lines or a long wait.
- **Repair:** State the gap in blocks or lines added between calls, and give the limit if it's known.
- **Severity:** worth fixing

**10.**
- **Where:** "Lay the prompt out…": "a seat used to see its own held-back lines marked as unpublished"
- **Kind:** term before introduction
- **What broke:** This is one of the "two details [that] decide what can share," but "held-back lines" is never explained. Nearby, "memory lookups" and the diagram's "brief" are also new.
- **Repair:** Gloss "held-back lines" in one clause, and either define "brief" or swap it for a term the page already uses.
- **Severity:** worth fixing

**11.**
- **Where:** "Lay the prompt out…": "two seats' prompts diverged there, sharing about 800 tokens"
- **Kind:** missing connection
- **What broke:** Under the same earlier layout, a different seat read 0% on Haiku but 29% on Luna. With 800 shared tokens, I couldn't explain either number.
- **Repair:** Add one clause explaining why Haiku read nothing and Luna read 29% under the old layout.
- **Severity:** worth fixing

**12.**
- **Where:** "Marks a growing transcript…": "Luna had reused only the fixed system message: exactly 4,582 cached tokens"
- **Kind:** missing connection
- **What broke:** The table says OpenAI stores prompts only up to the end of the latest user message. I couldn't see how Luna then read back just the system message, which is a shorter prefix. The Claude explanation suggests reads must end at a stored boundary.
- **Repair:** Add one line on how OpenAI matches a request against stored entries, for example whether a read can stop partway through a stored entry.
- **Severity:** worth fixing

**13.**
- **Where:** Haiku table header: "Spoke"
- **Kind:** detail that does not change understanding
- **What broke:** The table reports the "Spoke" column, but the text never explains or uses it. It may connect to the parent's point that Haiku "participated more," but the page doesn't make that link.
- **Repair:** Either tie it in one clause to the parent's participation finding or remove the column.
- **Severity:** worth fixing

**14.**
- **Where:** "What it did to Haiku's reasoning": "named the actual threat in 62% of valid samples at the low thinking setting"
- **Kind:** term before introduction
- **What broke:** "Reasoning tokens" is defined only after the table that uses it. "Live thinking setting" and "low" are never stated to be the same thing. "Actual threat" and "valid samples" are undefined.
- **Repair:** Define reasoning tokens before the table, and state once that Haiku's live setting is "low."
- **Severity:** worth fixing

**15.**
- **Where:** "What each provider stores…": "An entry also belongs to one model."
- **Kind:** missing connection
- **What broke:** The fact is stated and then never used. Its consequence presumably matters in mixed-model games (seats on different models can't share a cache), but I had to supply that myself.
- **Repair:** Connect it to mixed seats in one clause, or remove it.
- **Severity:** taste

**16.**
- **Where:** Final section: "where only a regression of about ten points would have shown"
- **Kind:** unit or term changes meaning
- **What broke:** I don't know what the "points" measure or what the "factual-error bench" scores.
- **Repair:** Name the metric and unit.
- **Severity:** taste

## 4. Highest-impact improvements

1. Add one place that says which model runs on which provider, in which seats and in which output mode. Then limit the opening's "four providers" claim to what was actually measured (Findings 2, 4).
2. Rebuild the Haiku section around its conclusion: say what the replay and live play disagreed about, give the healer turn in one plain sentence, and present the reasoning effect as an observation for one model rather than a mechanism (Findings 1, 8, 14).
3. Reconcile the numbers that conflict: retry rate versus 1 in 40, standalone checks versus the layout table, and Luna's two simultaneous changes. Remove standalone figures that add nothing beyond the table (Findings 3, 5, 6).
