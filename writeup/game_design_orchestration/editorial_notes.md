# Editorial revision — 2026-10-27

Scope: the five Level 2 pages and the two existing Level 3 investigations, revised at the owner's
request against the clarity of the root chapter. This is an editorial revision, not independent
verification of code, experiment records or historical deployment. The root's page-status sentence
was updated; its narrative was preserved.

## Structure and selection

| Page | Revised explanatory path | Material shortened or moved to an existing source |
|---|---|---|
| Evidence design | Problem with exact evidence → partial observations → trustworthy engine results → competing claims → replay and game evidence → balance limits | Full role roster and role-intention inventory replaced with a three-observer comparison; detailed balance batches remain in the roles report |
| Conversation | Sequential discussion → opportunities to speak → publication checks → stopping and closing → silence diagnosis and calibration → failure cases | Detailed calibration belongs to the existing Level 3 page; voice studies summarised with their limitations and source links |
| Day and night | Game graph → phase structure → collection and resolution → restricted inputs → state merging → shared records → execution bounds and checks | Factory history condensed and linked; the private-note overwrite remains the worked state-management example |
| Agent turn | Input → contract → validation → retry/fallback → hand-off → structured-response rationale | System-wide decision table removed; tool-loop comparison narrowed to the decision this turn needs |
| Human in the loop | State and answer lifetimes → shared turn pipeline → ballot incident → answer reuse → game boundary → hosting and checks | Cross-game bug condensed with its Level 3 link; thread-pool sizing and hosting options remain in server records |
| Cache key | Scope of reuse → contributing design choices → observed case → reach → fix and control | Repeated parent introduction shortened; transcript distinctiveness no longer presented as guaranteed isolation |
| Silence calibration | Existing investigation retained, with narrower interpretation | Clarified inherited reference labels and assumptions behind the combined estimate |

The original briefs and original source comments remain as historical authoring material. They may
mention omitted tables, earlier headings or claims replaced in this pass; they are not descriptions of
the current page structure. Reader-facing results retain links to their source reports.

## Claim changes and verification questions

- **Claims that fit a record versus convincing deception:** the evidence-design conclusion now says
  the 33 claims fit the public record available to the judges. It does not imply that players would
  believe them. The separate whole-game comparison retains its bundled-intervention limitation.
- **Accusation accuracy versus settling a day:** the nine-seat census heading no longer says claims
  “settled the day”; the supplied counts concern accusations and do not alone establish voting effects.
- **Tool use:** removed the categorical claim that a tool call necessarily adds a model round-trip.
  The rationale now concerns a turn needing one predetermined choice. The 51-call probe remains a
  comparison of the recorded configurations, not a general property of tools. Verify the historical
  configurations and definition of passing before publication.
- **Schema enforcement:** replaced “the reply cannot break it” with a description of constrained
  generation plus application validation. Verify supported-provider behaviour and the historical
  cache-prefix mechanism before treating this as current provider guidance.
- **Cache scope:** replaced “vote payloads never matched” with their transcript making them more
  distinctive. Explicit game identity supplies the boundary; the retained control is five reused
  openings before the fix and zero after. The hosted case remains an inference from logs, not a directly
  recorded cache hit. No new estimate of hosted incidence is made.
- **Silence:** the study conclusion now applies to the tested sample and prompt variants. The later
  variants inherited the original line's judgement; they did not receive fresh quality labels. The
  combined speech/gate estimate is explicitly conditional on label transfer and comparable gate
  behaviour, neither established by that calculation.
- **Balance count conflict:** the earlier draft's closing sentence said “Three evil wins” immediately
  after reporting four wins in the subsequent 18 games. The revised summary uses the explicit supplied
  four-of-18 count and omits the conflicting sentence. Confirm against the batch records before
  publication; no new balance result was calculated.

## Review performed

Read the revised explanations for ordering, repeated context, scope changes and essential limitations.
Checked local Markdown link targets, fenced-block balance and whitespace errors. No runtime code was
changed and no game experiments were run. Factual verification remains a separate task.


## Agent-turn scope revision — 2026-10-28

At the owner's request, shortened the schema/caching subsection around its turn-level purpose:
application validation, the reason for initially unenforced generation, and enforced retry after failure.
Kept the 20-game failure evidence and the unmeasured live effectiveness of the updated retry policy.
Removed the initial 412-call probe and cache-read percentages from page copy; those remain in the
caching experiment log. Provider cache-prefix mechanics, layout comparisons and cost findings belong
in the planned cost-and-latency chapter, with the current evidence link serving until that page exists.
The original drafting brief remains historical; its caching-heavy featured-story specification no
longer describes the revised section. The owner subsequently chose **Structured Agent Execution**, with the subtitle “From model responses
to validated actions, with retries and fallbacks.” Chapter navigation and planning references use the
new title; the `agent_turn/agent_turn.md` path stays unchanged. No runtime
code changed and no experiments rerun.

## Silence policy and calibration revision — 2026-10-28

Reorganised `conversation/silence_calibration.md` at the owner's request. Its scope is now the current
open-floor silence policy and the calibration informing it, rather than the experiment alone. The
page explains participation, the keep/hold rule, implementation, exemptions and consequences before
moving through pass replays, prompt variants, gate calibration and whole-game checks. The title and
file path stay unchanged. The original brief and source comments are preserved as historical material.
Updated the parent subsection and L3 link description to match.

Evidence retained: 40 forced versus 25 posted open-floor lines; the four prompt variants; the gate's
10/29 repetitions and 0/36 worthwhile lines in the game implementation; the four-game publication,
hold and voluntary-pass counts. The full sampling breakdown and removed combined-outcome prediction
remain in supporting comments. The repeated gate example was omitted from page copy; the forced-pass
example remains to show what a withheld opportunity could produce.

Claim changes and limits:

- The entire pass sentence was removed, not just “a pass costs nothing”; the effect of that clause
  alone was not isolated. Source README steps 2–3 checked.
- Prompt variants measure willingness to speak on turns grouped by earlier labels. They do not
  establish the usefulness of the newly generated lines or rule out better self-filtering prompts.
- “Worthwhile” is explicitly the study's A–C category grouping, not strategic correctness or exact
  equivalence to its separate worth-hearing yes/no field.
- Gate figures are calibration results on the same lines used to choose the rule. No independent
  false-hold rate is claimed, and fresh cases plus human-checked labels are identified as next work.
- The old design already called an echo gate. Removed the claim that the revision introduces an
  extra call per open-floor turn; only eligible lines are checked. More published speech is measured;
  more published repetition is a risk, not a measured before/after outcome in this page.
- Current mechanism checked narrowly against `Agents/turn/echo_gate.py` and `Agents/turn/resolve.py`:
  adds-nothing plus valid earlier speaker or filler, invalid-reference keep, human/reactive/tag-based
  reply exemptions, empty-floor bypass and fail-open handling. The gate code's docstring still quotes
  the trial's 12/29; page retains the recorded implementation check's 10/29, not that stale summary.
- Withheld-line consequences retain the supplied source claims. No independent end-to-end audit of
  prompt omission, private-note discard or scheduler re-offer behaviour was performed in this pass.
- Both the prompt and thinking setting changed; the aggregate gate comparison does not isolate either
  change. Small run-to-run differences are not presented as a dependable ranking.

Checked local links and Markdown structure. No new model calls, games or statistical analyses were
run. This is an editorial revision with targeted source/code checks, not a fresh verification of all
historical results. The broad original brief and earlier source mappings should not be read as the
current page outline or as new validation claims.


## Portfolio/evidence separation and silence-page shortening — 2026-10-28

Owner rule added to the general portfolio guide and the L2/L3 guides: complete experiment records live
in evidence; portfolio pages select the methods and results needed to assess a focused explanation.
Material caveats and adverse findings remain with their claims. L3 adds depth, not exhaustive run history.

Shortened the silence page from about 2,130 to 1,610 reader-facing words. Kept the current policy table,
implementation and exemptions, forced-pass example, 23/40 versus 13/25 finding, 20/64 → 41/64 speech
comparison, 10/29 and 0/36 gate result, and four-game check. The full category breakdown, prompt-variant
table and gate-configuration table remain in the linked evidence README; source mappings are preserved.
The policy's central tradeoff now connects the prompt experiment to the separate checker explicitly.

Retained limits: forced speech differs from voluntary speech; labels are model judgements; new prompt
outputs were not relabelled; the whole pass sentence was removed; the gate was tuned and assessed on
one set; prompt and reasoning changes are bundled; whole-game quality is unmeasured. This pass selected
and shortened supplied evidence, without new experiments or a fresh factual audit. Updated the parent's
supporting comment so it no longer promises full experiment tables in L3.


## 2026-10-28: Game orchestration clarity revision

Retained the owner's revised game-loop sequence in `day_and_night/day_and_night.md` and renamed
the page **Multi-Agent Game Orchestration**, with matching navigation and planning references.
Introduced framework terms beside their purpose, clarified eligible participants in parallel rounds,
and distinguished selecting night actions from applying their effects. Connected restricted inputs
to wrapper responsibilities and reducer semantics, retaining the private-note failure and tests.
Qualified the summary/vote example as an observed sequence rather than an isolated causal result;
expressed the execution budget as a design aim rather than an unconditional guarantee. Historical
brief, diagrams and supporting source notes remain. This is an editorial revision, not a fresh code
audit. Checked local page-copy links and Markdown fences; no runtime behaviour changed.


## 2026-10-28: Evidence-design explanation

Rewrote `evidence_design/evidence_design.md` around the agreed six-section progression: diagnosis,
partial and testable evidence, explicit cover instructions, frozen-turn comparison, whole games,
and remaining evaluation. Retained the observer table and selected comparisons; preserved prior
page copy in an HTML comment for source context. Detailed role and balance records remain linked.

Checked the replay README to clarify the original “33 of 33 fit” claim: later pooled judging
explicitly assessed contradictions with reported sightings, found three in that condition, and
changed other labels (including baseline denials). The public table is identified as the initial
assessment, and the prose explains the later result. This is a targeted source check, not a full
factual audit. The behavioural claim is kept separate from cover consistency, persuasion, balance
and discussion quality. Local page links and comment delimiters checked; no runtime changes.


## 2026-10-28: Human-in-the-loop explanation

Rewrote `human_in_the_loop/human_in_the_loop.md` using the owner-agreed progression: shared turn
pipeline, changed-ballot incident and replay cause, cached AI/uncached human turns, replay-safe keys
and ability accounting, persistence boundaries, then verification and event-delivery limits.
Kept the title and added a descriptive subtitle. Retained the diagram and historical page copy
in supporting comments. Detailed interrupt-display incidents, hosting mechanics and the config-helper
unit-test explanation now remain in the linked evidence and supporting history.

Clarified that cache hits avoid model calls rather than making execution free; the replay affects
the interrupted round rather than completed earlier rounds; identity, durability and state effects
are separate responsibilities. Kept the historical scope of the 20-ballot verification, the scripted
5-to-0 cross-game control, unknown incident extent, limited ability test coverage, and crash window.
No claim about post-deployment served games was added. Read the orchestration and server incident
records for these mechanisms; checked page links and comment delimiters. Editorially revised, not
a full factual verification or new runtime test. Owner requested the established writing approach
first rather than trialling the recently added skill; no fresh-agent review workflow was run.
