<!-- claims review of writeup/cost_and_latency/caching_across_providers.md by claude (opus), 2026-10-31T06:19Z -->

## 1. Findings

- **Claim:** "Votes moved the same way: 16 recorded vote cases from two games, replayed 10 times each in the live mode, named the actual threat in 62% of valid samples at the low thinking setting against 41% under the enforced schema, and rose at the medium setting too. The change made for cost helped the replayed decisions" (§ What it did to Haiku's reasoning)
  - **Source checked:** `evidence/gameplay/deduction/experiment_log.md` §2 (run_at 2026-10-16 in `data/haiku_effort_replay/runs/haiku_effort_votes/summary.json`), §8 Setup ("today's code renders the engine's roleblock line … the §4 injection has shipped"), §9 (run 2026-10-30, "same working tree as §8"); `evaluation/config/hallucination_bench_haiku_effort_votes_live_mode.json`; `Agents/config/run.py` (`DEFAULT_DEDUCTION_MODE = "full"`); `vote_cases.jsonl` (no deduction-mode field).
  - **Verdict:** unsupported inference
  - **Why:** The 41% and 62% come from two runs two weeks apart. Only the healer turn (Result 1) was replayed side by side. Between the two vote runs the deduction engine shipped, and its seat block renders into vote prompts by default, so the 41→62 gap likely mixes the output mode with the engine and other prompt changes. The log's "unchanged except the output mode" covers the run config, not the code. The map's handle-with-care list also makes side-by-side comparison the standard.
  - **Suggested scope:** Report the vote re-run as a later live-mode run (62% at low, 77% at medium) that was not run side by side with the enforced 41%/61% and so does not isolate the output mode. Limit "helped the replayed decisions" to the healer turn. Ask the owner to confirm from a rendered §9 prompt whether the engine block was present.

- **Claim:** "This page is about what it took to make four providers actually reuse it" (opening), with the Gemini row "Create the object from the shared input, reference it from later calls, delete it afterwards", introduced by "Seat A sends its turn; a minute later seat B…" (§ What each provider stores)
  - **Source checked:** `evidence/caching/report.md` §1 table ("Gemini gameplay gets no reuse … the game creates no cache objects for turns"); §3.1 (cache objects are for extraction); §6.
  - **Verdict:** overstated
  - **Why:** For game turns, reuse was set up and measured on Claude and OpenAI only. DeepSeek is automatic and was not measured under the layout. Gemini seats get no reuse at all, because cache objects are used only for post-game extraction. Since the table is framed around two seats' turns, a reader will assume the game creates Gemini cache objects for turns.
  - **Suggested scope:** Say the work made Claude and OpenAI reuse the shared transcript in play, and DeepSeek reuses it automatically. Note in the Gemini row that the cache object serves post-game extraction, and that Gemini seats get no reuse because its automatic cache never fired in the tests.

- **Claim:** "Two weeks later a replay disagreed with live play." (§ What it did to Haiku's reasoning)
  - **Source checked:** deduction log §4 (2026-10-16 replay, enforced) and §8 (2026-10-30 replay, both modes).
  - **Verdict:** conflicts with source
  - **Why:** Two replays disagreed with each other: the earlier one pinned to the enforced mode, the later one in the live mode. No live-play observation was involved, and in the played game the healer stayed silent.
  - **Suggested scope:** "Two weeks later, replaying the turn in the live output mode disagreed with the earlier replay, which had pinned the enforced schema."

- **Claim:** "That last change, made for cost, also let the game's model reason more." (opening)
  - **Source checked:** deduction log §8 Result 1; caching report §4.3 (Luna's output per call fell 10%; Haiku's reasoning about 1.5× on discussion).
  - **Verdict:** overstated
  - **Why:** The evidence is about Haiku only and counts reported reasoning tokens. Luna, the other model switched, shows no such effect. "The game's model" reads as all seat models, and "let … reason more" states a mechanism the page later hedges.
  - **Suggested scope:** "also made Haiku spend more reasoning tokens."

- **Claim:** "Because the system message holds only the rules, turn 2 can be any seat's turn, or a vote, and still read the entry; in one check a seat's next turn read 9,258 of 10,206 input tokens from cache." (§ Marks a growing transcript can still find)
  - **Source checked:** caching log §9 (2026-10-12, earlier layout, before the shared-prefix build of §13); report §4.2 (current-layout Haiku same-seat 77%).
  - **Verdict:** unsupported inference
  - **Why:** The 9,258/10,206 (91%) check ran under the earlier layout, when the system message still held the role card. Placed after "holds only the rules … any seat", it reads as current-layout evidence and conflicts with the page's own 77% same-seat figure.
  - **Suggested scope:** Date it as an earlier-layout check of the same-seat path, or move it before the layout change. Cite the 71% different-seat probe for the "any seat" claim.

- **Claim:** "Replies that failed | The provider guarantees the shape" (§ Taking the schema out of the cache key, table)
  - **Source checked:** caching log §12 trial table (Luna enforced 167/170; "Luna's three enforced misses were empty reads lists, a content check").
  - **Verdict:** overstated
  - **Why:** The row compares failure rates, and the cell implies zero failures under enforcement. Enforced Luna replies still failed validation 3 times in 170, on content rather than shape.
  - **Suggested scope:** "The provider enforces the shape; content checks can still fail (3 of 170 enforced Luna trial replies)."

- **Claim:** "1 in about 400 trial calls on each of Luna and Haiku; about one seat decision in forty across twenty real games" (§ Taking the schema out of the cache key, table)
  - **Source checked:** caching log §16 / report §3.5 (20 Haiku games, memory demo run).
  - **Verdict:** overstated
  - **Why:** The twenty games were all Haiku. Sharing a cell with "each of Luna and Haiku", the one-in-forty rate reads as applying to both models.
  - **Suggested scope:** "about one seat decision in forty across twenty Haiku games."

- **Claim:** "other low-cost models had shown the same direction in earlier checks without a like-for-like comparison" (§ What it did to Haiku's reasoning)
  - **Source checked:** deduction log §8 "What it shows".
  - **Verdict:** overstated
  - **Why:** The source calls these "related observations": Gemini Flash-Lite reported zero reasoning tokens under structured output, and a forced tool call turned thinking off for DeepSeek and Haiku. None compared enforced and text modes, so they don't show "the same direction".
  - **Suggested scope:** "other low-cost models had reported no reasoning tokens under structured output or a forced tool call, though none was compared against the schema sent as text."

## 2. Checked and supported

- Provider table, "tested integrations … read on 2026-10-13", 1.25× write and about 0.1× read on Claude and OpenAI, one entry per model: report §2.
- June probe (four identical 15k prompts, 0 cached; 2 of 600 production calls; explicit object 15,001 of 15,005), scoped to the tested models and backend: log §3–4, report §4.1.
- Admission check measuring three real prompts (seat turn, same seat's next turn, different seat): log §8, report §4.2.
- Earlier layout (role card before the transcript; votes, night and lookups on separate prompts); dead roster below the boundary; held-back drafts no longer shown: report §3.2.
- Probe table 90/0, 77/71, 57/29, 75/69, its mechanism caption and "one probe sequence per row; not a whole-game discount": report §4.2. The explanation of Haiku's lower same-seat share: report §3.2.
- Claude mechanism (mark per request, walk-back by content block, one block per line, marks on the system message and last line, two-turn diagram, long-gap miss unmeasured): report §3.3, log §9; code `Agents/llm_factory/providers/anthropic.py:59,74–76` and `common.py:93` (per-line split).
- OpenAI: 4,582 tokens on seven calls, most input written and not read; explicit breakpoints on the system message and each line; 2,561 of 2,678; private part never written: log §12–13, report §3.4; code `openai_compat.py:65–80`.
- Schema acting as the start of the prompt on Claude and OpenAI; per-seat legal targets split the cache; the owner's rule on targets (first-person ownership is supported): report §2, §3.5, log §12.
- The text-schema alternative validated against the same per-seat schema; the trial counts 1/388 and 1/412 counted as calls; different units named: log §12, report §3.5.
- Enforced retry once on the same model, uncached, frequency unmeasured; switch on 2026-10-14 for caching: report §3.5, log §15–16; `common.py::enforced_output`.
- Healer-turn table (2/10, 5/10, 0 reasoning tokens in 4 of 10 samples and at most 1,312; 8/10, 7/10, 409–1,233; 10/10, 8/10, 2,933–5,042), run side by side, plus the "zero tokens ≠ no reasoning" caveat: deduction log §8 Result 1.
- The engine's earlier uptake result was measured in the enforced mode: deduction log §4 note and §8.
- Paired games (Luna $0.89 → $0.64, −28%; votes and night 0% → about 60% read; Haiku level at $1.10 with 1.5× and several-times reasoning; two games per arm cannot size Haiku's differences): report §4.3, log §13.
- Bench (18 Luna discussion turns, no difference beyond noise, about ten points detectable) and the open items: report §4.4, §6.

## 3. Not checked

- "Sharing about 800 tokens" between two seats in the earlier layout: log §8 says it comes from working notes with no data file, so it cannot be checked. The brief already flags it for the owner (Open question 1).
- The probe records under `evaluation/eval_results/model_admission/` and the paired-game data in `batch_results/cache_ab_2026_10_13/` were not opened. The figures were taken from the report and log as they stand, per the owner's ruling against a number-by-number audit.
- The provider documentation itself, as read on 2026-10-13: the mechanism rows were checked against the report's account of it, not against the providers' docs.
- Whether the 2026-10-30 vote prompts actually contained the deduction-engine block. This is inferred from the run dates, the default `deduction_mode = "full"` and the absence of a mode field in the cases, not from a captured prompt. The owner should confirm it before the first finding is resolved.
