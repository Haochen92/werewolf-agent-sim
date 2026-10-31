# Cost and latency: editorial notes

## 2026-10-30 — Self-contained Level 1 draft

The owner approved the workload-first explanation and additional space for an L1 without required L2
pages. Drafted directly, continuing the owner's preference for independent writing rather than the
portfolio skill workflow. Read the local skill instructions but did not invoke its drafting/reviewer process.

The page explains cost and visible waiting before presenting model effort, caching, workload controls
and offline processing. Tables explain workload, timing overlap and trade-offs. Detailed provider
mechanisms, stage reconstruction and batch diagnostics are optional L3 candidates in the revised plan.
The former plan is retained as an explicitly superseded source inventory.

Claims were checked against the cited local reports, not raw traces or provider prices. The low-cost
sample is identified as quiet AI-only games; no 400-call average or general $0.75 cache-loss attribution
is claimed. The October 30 live-output-mode vote replay replaces the older vote numbers; the discussion
latency result is labelled as a different output mode. Local-model training is exploratory, not deployed.
No new model-pricing comparison, numerical reanalysis or independent reviewer pass was performed.

## Cost framing and offline work — owner follow-up

Updated cost_and_latency_codex.md only; the parallel Claude draft is unchanged. Removed the arbitrary
$0.30 target. Used owner-reported frontend averages, with their unverified snapshot details recorded
in the source comment; checked the API separates memory-on/off completed-game means. Added the two
memory-on Haiku costs from the existing plan, without treating the difference as measured overhead.
Named lesson extraction and synthesis and explained batch output discounts before the retry-cost case.
Prompt caching is explicitly limited to input savings. No live dashboard fetch or repricing performed.

## Lever comparison tables — owner-approved follow-up

Added two tables after visible waiting: adjustable trade-offs and optimisations with conditions.
The former workload-control table is replaced by short mechanism paragraphs to avoid duplication.
Model-size/speed tendency links to provider guidance; no project-specific latency ranking is implied.
Checked local links, table structure and whitespace.

## Selected additions from the Claude companion — owner-approved

Strengthened the Codex draft with the input-volume versus output-cost example from caching log
section 17, the shared impact of summary errors as a reason to test additional spending, and the
seat-ID failure that informed extraction model selection (post_game/report.md section 4). Merged
private assessments and strategy notes into the agent-turn row so they cannot be mistaken for
separate calls. No repricing table imported; Claude companion unchanged. Source passages checked,
without rerunning their analysis.

## 2026-10-31 — Level 3: Making prompt caching work across providers (first draft, reviewed)

New page `caching_across_providers.md`, under the Level 1's "Reuse shared input without losing useful
behaviour"; the only Level 1 edit is the plain-text Explore line at the end of that subsection. Written
with the portfolio skill: outline approved in conversation 2026-10-31, brief with a sample passage
(the schema-and-cache-key section), editorial and claims reviews on the Claude CLI, then two further
editorial reads as the Haiku section was reframed. The editorial reviewer's parent excerpt was built by the script's own rule on a
scratch copy of the chapter, because the Explore line is not a markdown link and the parent file's name
does not match the script's convention.

Explanatory path: what each provider stores and what a write costs → measure before relying on it →
the layout that makes every seat and call type share the transcript → marks a growing transcript can
still find → the enforced schema taken out of the cache key → what that did to Haiku's reported
reasoning in replays → the paired games and what remains. Moved out to the source note: the 20-block,
80-breakpoint and four-written figures; the earlier-layout 9,258-of-10,206 check; the healer table's
"spoke" column; the extraction overrun; the participation story (Level 1); the node cache.

Claim changes from the reviews: the opening no longer says four providers reuse the shared input
(Gemini seats get none; the cache object serves extraction); "let the game's model reason more" became
Haiku's reported reasoning tokens with the caveat beside it; "a replay disagreed with live play" became
two replays disagreeing; the 16-vote re-run is compressed to one sentence, stated as not side by side with the enforced run
and not isolating the output mode (the deduction engine may be in the later prompts only; open question for the
owner); the one-in-forty failure rate is scoped to twenty Haiku games and placed before the enforced
retry existed; the enforced-schema cell admits Luna's three content-check failures; Luna's probe rows
are marked as changing layout and mechanism together; the paired-game arms are defined; Luna's earlier-layout 29% is left unexplained rather than given a
derived cause; the legal-target rule is restated as code enforcement, with the text schema carrying the
targets.

Checked against the cited reports, the deduction log §8–9, the catalogue notes and the server's
game-creation schema; no raw probe records or traces were reopened, and no number was re-derived. Page
copy about 2,100 words of prose plus four tables, over the outline's 1,000–1,300 guide; the brief lists
the cuts if the owner wants it shorter. Editorially revised is not factually verified.
