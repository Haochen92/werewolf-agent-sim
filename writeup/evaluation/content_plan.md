# Evaluation: portfolio content plan

Editorial assessment, 2026-10-25. This maps the existing evidence into portfolio pages; it is not
publication copy or a claim that these pages have been built. The owner chose the three-level reading
structure. The eight-page grouping below is the recommendation from this pass.

## Reading structure

**Level 1 is the chapter page:** “Evaluation: assessing the agents and the systems around them”. It
contains an overview, a compact method diagram and a short, substantive account of each Level 2 subject.
The project case-study page sits above it and links here with a shorter introduction.

**Level 2 contains complete explanations of substantial subjects.** Each page has its own overview,
subsections, examples and exhibits. A visitor arriving directly should understand its question, the
approach, what was learned and the limits without reading the chapter first.

**Level 3 is optional, curated detail on the portfolio.** It develops a particular investigation that
would interrupt the Level 2 explanation. It must add a method, analysis or useful exhibit, not merely
repeat the parent with more words. Necessary conclusions and limitations remain on the parent page.

Repository links provide records and code. No explanation worth reading is assigned to GitHub merely
because it is detailed. A reader can understand all selected work without leaving the portfolio.

## Recommendation: eight Level 2 pages in three groups

Eight subjects earn pages through distinct decisions and evidence, not through their source word counts.
On the Level 1 page they appear as eight sections under three question subheadings (owner 2026-10-25),
the hub's three questions. The subheadings are headings only: no grouping page, no navigation item.

| Question subheading | Level 2 page | Why it deserves a page |
|---|---|---|
| **Does each part do its job?** | **1. Finding and fixing factual errors** | A complete workflow: finding, counting, diagnosing and checking failures; the distinction between bad input and bad reasoning matters beyond one prompt fix |
| | **2. Measuring play quality beyond win rate** | Defines what “better” means, distinguishes accurate counts from useful proxies, and tests whether those proxies transfer when the game changes |
| **Can the checks be trusted?** | **3. Checking agent outputs with code** | Three distinct approaches: recompute facts, test against an independent oracle, and verify that a checker detects planted faults |
| | **4. Designing and validating LLM judges** | Rubric design, context, choice of labels and calibration are substantial engineering decisions; high scores that could not rank versions provide a concrete failure story |
| | **5. Building reference labels and reviewing outputs** | Sampling, blinding, adjudication and agreement determine the reference against which judges are measured; the model-panel review is a separate story from judge design |
| **Does a change make it better?** | **6. Choosing between turn replays and whole games** | Explains what is held fixed, what is allowed to unfold and which claims each scope supports; includes the missing day scope |
| | **7. Designing fair comparisons** | Configuration guards, current baselines, sampling variation and paired analysis need their own explanation rather than a paragraph appended to scope |
| | **8. Evaluating models before switching** | Integrates quality, structured output, cost, latency and live behaviour into practical model decisions, while separating measurement from current admission policy |

The former “Making the evaluators trustworthy” section becomes pages 3–5. The former combined
scope-and-controls section becomes pages 6–7. Factual errors, metrics and model admission retain their
own subjects. This gives readers specific entry points without asking one page to explain several
different kinds of validation.

## Level 1 presentation

Use the agreed evaluation-focused overview: agent decisions and supporting components; varying and
cascading behaviour; code versus readers; controlled comparisons and model choices. Do not lead by
retelling the game or by making the investigation example stand for the entire chapter.

The introduction also carries a compact form of the hub's "Why evaluating an LLM system is different"
table (`evidence/evaluation/report.md`): four or five rows, each a challenge, how it shows in this
project, and the section that answers it. Candidate rows: outputs vary between runs (sections 6, 7);
the evaluator can be wrong (4, 5); the model service can change with no code change (7); a setting can
fail silently (7, 8); errors pass from one component to the next (1, 6).

Layout (owner 2026-10-25): introduction → eight sections under the three question subheadings, each a
short explanation and main finding ending in a link to its Level 2 page. Level 2 pages are reached from
those links, with breadcrumbs back to Evaluation and previous/next links between subjects; they are not
main-navigation items. On a Level 2 page, an optional Level 3 link sits beneath the subsection it deepens.

Below the overview, separate scope from scoring in the diagram; show validation and experimental
controls alongside them. Mark day replay as designed, not implemented, and current judge calibration
as pending. Avoid costs from incomparable historical runs.

Each subject summary gives the question, the main decision and one finding with its essential scope,
followed by a descriptive link to its Level 2 page. Start around 90–130 words per subject (the authoring prompt's
length guides, owner 2026-10-25). These are drafting guides, not caps. Eight summaries
must remain a quick read; put fuller setup and results tables on the destination pages.

The earlier §1 draft (now the featured story in [factual_errors/factual_errors.md](factual_errors/factual_errors.md)) remains a useful source. Its opening and main
finding can supply the chapter summary; its four-version table and diagnostic explanation belong on
the Level 2 page. This is a presentation choice, not a ban on tables at Level 1.

## Level 2 page briefs

Each brief lives at the top of its page file, with its Level 3 briefs beside it. Page 1 is drafted
(2026-10-25): its page copy replaces its brief.

| # | Level 2 page · Level 3 pages |
|---|---|
| 1 | [Finding and fixing factual errors](factual_errors/factual_errors.md) |
| 2 | [Measuring play quality beyond win rate](play_metrics/play_metrics.md) · Level 3: [`metric_transfer.md`](play_metrics/metric_transfer.md) |
| 3 | [Checking agent outputs with code](code_checks/code_checks.md) · Level 3: [`field_audit.md`](code_checks/field_audit.md) |
| 4 | [Designing and validating LLM judges](llm_judges/llm_judges.md) |
| 5 | [Building reference labels and reviewing outputs](reference_labels/reference_labels.md) · Level 3: [`model_panel_review.md`](reference_labels/model_panel_review.md) |
| 6 | [Choosing between turn replays and whole games](replays_and_games/replays_and_games.md) |
| 7 | [Designing fair comparisons](fair_comparisons/fair_comparisons.md) · Level 3: [`paired_baseline.md`](fair_comparisons/paired_baseline.md) |
| 8 | [Evaluating models before switching](model_admission/model_admission.md) |

## Level 3 candidates (assessed 2026-10-25)

Every plausible Level 3 candidate across the eight pages, assessed against the six selection criteria
and two tests in [`../../.agents/skills/write-portfolio-page/references/portfolio-level-3-writing-rubric.md`](../../.agents/skills/write-portfolio-page/references/portfolio-level-3-writing-rubric.md),
"Selecting a Level 3 page". The pool: the four earlier selections, the examples proposed in earlier
passes, and implementation walkthroughs, which the rules now admit.

Every candidate must also be anchored in a Level 2 subsection that covers the same finding (owner
2026-10-25); the link sits there, and the two are kept in sync. Anchors as briefed:

| Level 3 page | Anchoring subsection on its Level 2 page |
|---|---|
| The field audit | Code checks: the lead story (recomputing structured fields from game state) |
| Metric transfer | Play metrics: "what transferred to the expanded game" |
| The model-panel review | Reference labels: the lead story ("using model panels without treating agreement as truth") |
| The paired baseline | Fair comparisons: the lead story (the shifted baseline and the paired reanalysis) |
| The census (possible) | Factual errors: "Estimating frequency with a systematic screen" (drafted) |
| Testing the test (possible) | **No anchor yet.** If chosen for page 7, add a subsection on how many games a test needs, with the power result in brief |
| Single-case noise (possible) | Partly: replays and games, "repeated responses versus case coverage"; fair comparisons, the noise floor. Name one as its anchor if chosen |

### Selected

| Page | Reader question | Added value ("Readers will learn how…") | Why separate | What stays on Level 2 | Verification needed |
|---|---|---|---|---|---|
| [The field audit](code_checks/field_audit.md) (page 3; drafted) | Could an earlier negative retrieval result be trusted, given the fields it ranked on? | …field definitions, reference calculations, exclusions and a rule fixed in advance decided whether the result stood | The units, the three-way rule and the wolf/town scope need sustained attention the parent cannot give | The audit's finding (direct-copy fields right, derived fields wrong), that it reopened the result, and that the fields moved into code | The June-era gating configuration (candidates re-scored, then the top five kept); checked against today's code only |
| [Metric transfer](play_metrics/metric_transfer.md) (page 2) | When the game changed, how do you tell which play scores still track winning? | …within-batch and memory-off checks, rare-role samples and intervals separated scores that carried over from those that did not | The checks and intervals would bury the parent's point that counting a move and validating a proxy differ | The healer and lynch contrast and what it means | That the 2026-10-24 ten-seat check ran on scorers already switched to the role registry (three scorers scored the new evil roles as town until that day) |
| [The model-panel review](reference_labels/model_panel_review.md) (page 5) | When three models agree on a label, what does a review of their agreement find? | …a review of agreed as well as split cases exposed a bias three same-vendor models shared, class by class | The 619/244 split, what was reviewed and what was trusted, and the class-specific errors need a table and a careful scope | That agreement looked like reliability and was not; the 37% figure; later panels mixed vendors | Which cases the review covered (617 records; the 246 unanimous keeps trusted) and who reviewed them (the owner with Claude) |
| [The paired baseline](fair_comparisons/paired_baseline.md) (page 7) | Did the shifted baseline show that the model service changed? | …treating the 20 shared deals as pairs changed a dramatic independent reading into a bounded uncertainty | The two analyses and the transition table need room; the parent needs only the corrected conclusion | That a baseline shifted, that the cause was not established, and the same-window rule it produced | The deal pairing in the 2026-10-25 reanalysis script and its inputs |

### Possible (pass the criteria; owner to decide home or priority)

| Candidate | Reader question | Added value ("Readers will learn how…") | Open point |
|---|---|---|---|
| Counting rare errors: the census (page 1) | How do you estimate a rate of rare errors when reading everything is too expensive? | …a layered screen (code narrows, models read, a person checks) produced a rate, why its counts are floors, and what its rules could not see | Lower priority: the parent already states the rate, the floor and the blind spot; worth a page only if the layered design is wanted as a showcase |
| Testing the test before paying for it (page 7, or Memory) | Could the planned trend test have seen a realistic improvement at an affordable size? | …planting known improvements in pretend runs built from real games measured the test's power before any spend | Its subject is the memory loop's measurement plan; the content plan sends loop results to Memory. Decide its home |
| How noisy is one replayed case? (page 6 or 7) | How far does one frozen turn's result swing with nothing changed? | …running the unchanged arm twice and shuffling all arms into one schedule measured single-case noise (8 of 10 one run, 1 of 10 the next; about one in three at 25 per arm) | Needs deduction-engine context (the case is a deduction acceptance turn); may fit better as page 7's noise-floor subsection |

### Deferred to another topic's pages

- **Testing the deduction engine against every possible deal** (an implementation walkthrough): the
  deduction topic owns the solver; check what the tests' authorship allows the page to claim.
- **Rebuilding a turn from saved state** (an implementation walkthrough): the observability topic.
- **Deciding the analysis before the data: the endpoint test**: its result belongs to Memory; page 7
  keeps the method as a subsection.
- **A labelled ranking overturning a design intuition** (the query field that lowered retrieval): the
  retrieval topic.

### Kept on Level 2 (fails a criterion)

| Example | Criterion it fails |
|---|---|
| The invented investigation | Optional for the parent: it is page 1's argument |
| The quality rubric whose scores bunched at the top | Reason to separate, for now: the parent's lead story needs the same excerpt and scores; reassess once page 4 is drafted |
| The summary's invented roleblock claim; the night-1 fix; the probe-passing model that answered in prose; the forced tool call that turned thinking off; the thinking budget; the live classifiers failing open; the leak checks fed no input; model readers drifting between reads | Substantial additional value: each is one result that fits in a paragraph |
| The code audit of prompt assembly (12 places facts were lost) | One-sentence test: as proposed it is "see the full list" |
| Does a labeller need the game context? (the May context-labelling study, `context_eval`; assessed 2026-10-26) | Defensible content and reason to separate: the "ceiling" (80.5% binary) is agreement between two models, the human anchor was deferred, the substrate is the superseded nine-seat store, and the two golds were never built; the model-panel review already carries the "agreement is not truth" lesson. Kept as a paragraph on page 5 (what the labeller sees changes the label; flash-lite with context at 77%). Reassess if the deferred labelling with a human anchor is run |

## Disposition of every report

Paths below are relative to `evidence/evaluation/`. All 15 `report.md` files are accounted for.

| Source | Portfolio treatment | Reason |
|---|---|---|
| `report.md` | Source for Level 1 and navigation | Explains the overall system; its inventory is not the portfolio's reading order |
| `factual_errors/report.md` | Own Level 2: page 1 | Substantial diagnosis and regression workflow |
| `metrics/report.md` | Own Level 2: page 2; selected Level 3 transfer study | Metric design and validation are distinct decisions |
| `deterministic_audits/report.md` | Own Level 2: page 3; selected Level 3 field audit | Multiple useful validation approaches; distribute overlapping workflows to their primary homes |
| `llm_judge/report.md` | Own Level 2: page 4 | Judge design deserves more than a paragraph under generic trust |
| `labeling/report.md` | Own Level 2: page 5; selected Level 3 panel review | Construction of the reference is a substantial subject |
| `labeling/sampled_reads/report.md` | Full subsection on page 5 | Shares sampling, blinding and rubrics; one-off use versus reuse supplies the distinction |
| `evaluation_scopes/report.md` | Framework for page 6 | A scope decision, not a separate overview page below the overview |
| `evaluation_scopes/turn/report.md` | Combine on page 6 | Explain replay design and limits beside the alternative |
| `evaluation_scopes/game/report.md` | Combine on page 6 | Explain cascades, statistical unit and live integration beside replay limits |
| `experimental_controls/report.md` | Own Level 2: page 7; selected Level 3 paired reanalysis | Fairness and statistical interpretation are not the same question as scope |
| `model_admission/report.md` | Own Level 2: page 8 | Distinct operational decisions across several checks |
| `scoring/report.md` | Distributed across pages 2, 4, 5 and 7 | Explain each score where it supports a decision; no statistics glossary page required |
| `loop/report.md` | Memory chapter; selected guards cross-referenced on page 7 | Its question is the learning loop; the owner's ruling keeps the outcome under Memory |
| `hardening_pass/report.md` | Not used (owner ruling, 2026-10-23); dated history retained in evidence | The field audit's source is `deterministic_audits/report.md`, case 3, and its experiment log |

Supporting notes under `llm_judge/` feed page 4; the retired discussion tagger stays excluded under the
owner's earlier ruling. `labeling/dedup.md` feeds page 5's scoring example. Experiment logs and the source
map supply provenance and any selected explanations needed on the website; they are not mandatory reading.
Retrieval-quality results remain in Memory/Retrieval. If the incomplete-label example is used here, page 5
owns the labelling lesson and links internally to the retrieval result.

## Boundaries and drafting checks

- **Keep one primary explanation per subject.** Failure propagation: page 1. Oracle validation: page 3.
  Judge calibration: page 4. Constructing reference labels: page 5. Scope limits: page 6. Experiment
  configuration and paired analysis: page 7. Cross-link within the portfolio instead of retelling each.
- **Selected Level 3 pages are candidates for drafting, not required routes at launch.** If the complete
  explanation fits comfortably in Level 2, keep it there. Never move essential caveats down a level.
- **Exhibits are part of the argument.** Introduce what the reader should notice, show the artifact,
  then explain the consequence. No separate exhibit gallery or sample viewer is required.
- **Source corrections survive publication.** The field-audit thresholds are not one universal 80% bar:
  bucketed players alive uses 90%, swing vote 80%; bullets left is outside that predeclared rule. Use
  the corrected experiment log and the map's verification notes, not the compressed report sentence.
- **The baseline's corrected paired reading takes precedence over older report summaries.** The
  whole-game report still repeats the independent headline. Use the current controls report for this case.
- **Check personal ownership before first-person claims.** Some records say “read by hand” without
  identifying the reader. Do not silently convert that to “I personally labelled every response”.
- **The page plan is not completed content.** Draft Level 1 summaries and one full Level 2 page first
  to establish the editorial example; then develop the other pages and only the deep dives that earn it.
