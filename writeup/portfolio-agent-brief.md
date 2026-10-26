# Portfolio hub — brief for the building agent

## Task

Build a personal portfolio hub for someone pursuing their first Applied AI engineering role.
The three project applications already have deployed websites. This hub introduces the owner,
explains the projects and links to those applications. Do not rebuild the applications.

Project entry routes:
- `/`
- `/projects/werewolf-agent-sim`
- `/projects/dota-oracle`
- `/projects/nutri-ally`

The portfolio also needs chapter and detail routes. The owner's reading structure (2026-10-25) is:

- Level 1: a chapter page with an overview and substantive summaries of its subjects.
- Level 2: a page per substantial subject, with its own overview, subsections and exhibits.
- Level 3: optional pages for focused investigations or technical explanations.

All selected explanations stay on the portfolio. Repository links provide supporting records and code;
they are not Level 3 and must not be required to understand the work. For Evaluation, use
[`evaluation/content_plan.md`](evaluation/content_plan.md) for the proposed eight subject pages and
selected deep dives. Do not turn its entire outline into one long project page.

Suggested route pattern (publish only pages with reviewed content):

```text
/projects/werewolf-agent-sim/evaluation
/projects/werewolf-agent-sim/evaluation/{subject}
/projects/werewolf-agent-sim/evaluation/{subject}/{investigation}
```

The drafts mirror these routes: `writeup/evaluation/evaluation.md` (chapter),
`writeup/evaluation/{subject}/{subject}.md` and `writeup/evaluation/{subject}/{investigation}.md`;
exhibits and their sources are listed in `writeup/evaluation/exhibits/source_map.md`.

Provide breadcrumbs, previous/next links between subject pages, direct section anchors and descriptive
internal links. Subject pages are reached from their chapter page's sections, not the main navigation; a
chapter page's subheadings are headings only, never pages. Each page must make sense
when opened directly. A deeper page adds detail; its parent retains the finding and essential caveats.

This is a starting content outline, not publication-approved copy. Allow final write-ups and
evidence to arrive later. Do not invent personal background, contributions, measurements, URLs,
screenshots, testimonials or experiment results.

## Visual direction

Neobrutalist-inspired cards and controls with a calm, spacious reading experience. The owner's
references are Codecademy, Figma and the Claude platform; use these as aesthetic references,
not layouts to copy. Warm off-white, charcoal text, strong card outlines, modest offset shadows,
one main accent, and restrained project accents. Readable sans-serif; optional monospace for
small labels. Case-study interiors should have comfortable line lengths and quieter borders.

Prioritize screenshots, diagrams and evidence over decoration. Support mobile, keyboard focus,
accessible contrast and reduced motion. No elaborate loading animation, custom cursor,
decorative terminal or autoplay showcase.

## Homepage

1. Name, short introduction and links to projects, resume, GitHub and contact.
2. Three project cards, all visible by default. Each has a visual, title, one-sentence summary,
   status, 4–5 capability tags and separate Case study / Open app links.
3. A short background paragraph when supplied by the owner.
4. Contact and footer.

Skill filters are optional and secondary with three projects. If implemented, use capability
tags and provide All / Clear. Technology names belong in a smaller stack list. A tag should
lead to a relevant project section or evidence, not merely decorate a card.

## Content shape

Use structured metadata for cards, links, evidence and showcases, with Markdown/MDX or an
equivalent simple content format for prose. No CMS or general page-builder framework is needed.
The project shape below is not the complete page hierarchy. Add chapter metadata and content pages with
stable IDs, slugs, parent IDs, summaries, Markdown/MDX bodies, assets, evidence references and editorial
status. Level 1 summaries link to those pages; do not force a Level 2 page into a single `decisions[]`
entry or flatten it into `sections[]`. Prose and inline exhibits remain the primary content format.
This TypeScript shape describes the project entry content, not a mandatory implementation:

```ts
type Project = {
  slug: string;
  title: string;
  summary: string; // One plain-language sentence for the hub.
  status: 'deployed' | 'in-development' | 'archived';
  tags: string[];  // Capabilities; roughly 4–5.
  stack: string[];
  cover: Media | null;
  links: { app: string | null; repository: string | null };
  contribution: string | null; // Owner-reviewed; don't infer from the repo.
  overview: string;
  problem: string;
  architecture: { explanation: string; diagram: Media | null } | null;
  showcase: {
    title: string;
    explanation: string;
    kind: 'recorded' | 'precomputed' | 'interactive';
    media: Media | null;
    artifactUrl: string | null;
  } | null;
  decisions: Array<{
    id: string;
    title: string;
    problem: string;
    choice: string;
    alternative: string;
    tradeoff: string;
    evidenceIds: string[];
  }>;
  findings: Array<{
    statement: string;
    kind: 'measured' | 'observed' | 'mechanism';
    scope: string; // Game/model version, dataset, dates, etc.
    caveat: string;
    evidenceIds: string[];
    metric?: {
      label: string;
      baseline: string;
      result: string;
      sample: string;
      uncertainty: string | null;
    };
  }>;
  limitations: string[];
  nextSteps: string[];
  sections: Array<{ id: string; title: string; body: string }>;
  evidence: Array<{
    id: string;
    title: string;
    description: string;
    kind: 'report' | 'code' | 'experiment' | 'demo';
    url: string | null;
    sourcePath?: string; // Authoring reference only, never a public URL.
  }>;
  editorial: {
    state: 'draft' | 'reviewed';
    sourceNotes: string[]; // Internal; never render in the public page.
  };
};

type Media = {
  src: string;
  alt: string;
  caption: string;
  type: 'image' | 'video';
};
```

Use stable section IDs for direct links. Keep limitations adjacent to the findings they qualify.
Do not force every project to have a headline statistic or identical section counts.

## Example: Werewolf Agent Sim

- **Slug:** `werewolf-agent-sim`
- **Summary:** A playable social-deduction game with LLM agents, replay inspection and experiments
  on cross-game memory.
- **Status:** deployed; confirm the deployed revision and enabled memory features.
- **Tags:** Agent orchestration, Evaluation, Retrieval, Streaming UX, Reliability.
- **Stack candidates:** Python, LangGraph, FastAPI, PostgreSQL, Next.js, React, TypeScript.
- **Contribution:** awaiting the owner's wording.

**Problem:** Build agents that play a hidden-information game, make their behavior inspectable,
and investigate whether memories from previous games improve their decisions. The application
and research program have different success criteria.

**Architecture:** actor-visible state → optional memory retrieval → agent decision → game engine
→ filtered events → live viewer/replay. Show post-game extraction and reviewed store-building
separately; do not imply every served game automatically teaches the shared library.

**Showcase candidate:** A short recorded replay moment with public dialogue and an explanation
of what the acting player knew. Add a memory-inspection example when a verified current
memory-on run is supplied. Never fabricate a trace.

**Decision stories:**
1. Measuring memory: outcomes, proxies, replay screens and the limits of each instrument.
2. Live delivery: SSE + POST, private-event filtering, reconnect/catch-up and presenting completed
   speech events rather than raw generated tokens.
3. Frontend performance: stable scene identity, bounded repaint regions and phone image sizing.

**Results framing:** Historical static-memory benefits belong to their original experimental
conditions. Later procedural-memory experiments include harm and diagnosed credit limitations.
The ten-seat memory demo is not a newly measured effectiveness result. Historical memory game
turns generated no reasoning tokens; do not generalize the findings to all reasoning settings.
Do not publish a win-rate headline without reviewing its exact arm, sample and uncertainty, or
claim demonstrated compounding improvement in the current system.

**Optional subsection:** Earlier fine-tuning exploration. The owner does not intend to present
the AI-generated training scripts as implementation they deeply own. Emphasize understood
trade-offs and historical findings, not current production training expertise.

**Authoring sources:**
- `/home/ubuntu/projects/werewolf-agent-sim/writeup/eval_exhibits.md`
- `/home/ubuntu/projects/werewolf-agent-sim/writeup/server_talking_points.md`
- `/home/ubuntu/projects/werewolf-agent-sim/evidence/credit/blindspot_fix/experiment_log.md`
  (research closure §⑥, reasoning-scope addendum §⑦)
- `/home/ubuntu/projects/werewolf-agent-sim/evidence/memory_system/v8/README.md`
- `/home/ubuntu/projects/werewolf-agent-sim/frontend/docs/frontend_lessons.md`
- `/home/ubuntu/projects/werewolf-agent-sim/frontend/docs/server_client_transport.md`

Sources contain historical sections and stale summaries. Reconcile claims against dated records;
do not assume every present-tense statement describes today's deployment.

## Example: Dota Oracle (dota2pred)

- **Slug:** `dota-oracle`
- **Summary:** A Dota 2 prediction platform combining live match tracking, an interactive draft
  predictor and model-performance reporting.
- **Status:** deployed, per the owner. Details below are repository-documented; the deployed
  version and quantitative results have not been independently verified for this brief.
- **Tags:** Prediction, Data pipelines, Evaluation, Streaming UX, Reliability.
- **Stack candidates:** Python, scikit-learn, FastAPI, BentoML, Redis, PostgreSQL, Prefect, Next.js.
- **Contribution:** awaiting the owner's wording.

**Problem:** Turn external match data and historical team/player/hero information into usable
predictions while handling ingestion failures and measuring model behavior. Distinguish the
professional-match predictor from the hero-only draft predictor.

**Architecture:** Steam/OpenDota → ingestion and time-aware feature engineering → inference →
stored prediction/outcome → API → dashboard. Distinguish Redis Streams for pipeline work from
Pub/Sub and SSE for frontend updates.

**Showcase candidate:** A recorded ten-hero draft interaction and probability output, followed
by a performance chart. Do not attach professional-model metrics to the hero-only draft tool.

**Decision stories:**
1. Time-decayed features and historical lookups restricted to information available at prediction
   time: the leakage risk and the implementation/checks addressing it.
2. Retryable stream processing and idempotent writes: explain the guarantee's boundaries rather
   than broadly promising exactly-once execution.
3. Model complexity versus measured improvement: verify the chosen artifact and evaluation setup.
4. Streaming a snapshot and updates to the dashboard, including reconnect behavior.

**Evaluation:** Separate test results, production monitoring, public matches and professional
matches. Show sample, dates, split, baseline and calibration/Brier score where supported. Matching
test and production accuracy alone is not proof of no overfitting.

**Editorial caution:** The ML summary calls logistic regression production near the beginning,
but later uses a LightGBM-associated figure in a production-model comparison. Resolve this before
publishing an algorithm label or performance headline. No verified headline number is supplied here.

**Authoring sources:**
- `/home/ubuntu/projects/dota2pred/README.md`
- `/home/ubuntu/projects/dota2pred/model_factory/ML_EXPLORATION_SUMMARY.md`

The optional paper-betting experiment is not needed for the main story. Do not add profit claims.

## Starter: nutri_ally

- **Slug:** `nutri-ally`
- **Summary draft:** An in-development AI application exploring document retrieval and tool use,
  with MCP integration in scope.
- **Status:** in-development; an application is deployed, but the project is unfinished.
- **Candidate tags:** Retrieval, Tool use, MCP, Evaluation. Verify implemented capabilities first.
- **Contribution, stack and results:** awaiting verified content.

Use the shared layout without inventing finished capabilities. Explain a verified working path
and distinguish remaining work. This repository was not reviewed for the present brief.

**Future showcase candidate:** A document question → retrieved passages → answer with source
attribution, plus a tool interaction if implemented. Populate from a real example.

## Missing content and publication

- Unknown links, media and contribution statements remain null in source data.
- Hide missing links and empty sections publicly. No buttons linking to `#`.
- A development preview may show neutral layout placeholders. Do not ship fake screenshots,
  fabricated charts, editorial TODOs or verification notes as real evidence.
- Keep source paths and editorial metadata out of the public UI and client data bundle.
- Convert approved evidence paths into real public repository/report links before publishing.
- Store factual text separately from components so revisions do not require layout edits.
- Support architecture media, a short showcase, a results table and long prose on one page.
  Core content must remain readable without opening every accordion or switching tabs.

## Build order

Build one Werewolf card and case-study page first, with real prose, one decision, a caveated
finding and an evidence link. Then build the Evaluation chapter and one Level 2 subject page to validate
the reading hierarchy before populating the rest. Reuse the layout for Dota Oracle and nutri_ally.
Use reusable content components; no portfolio-specific backend is necessary. The four project entry
routes are a starting point, not a limit on chapter and detail pages.

Check direct project/section links, mobile readability, keyboard navigation and missing-content
behavior. The final personal introduction, resume, contributions, media, external URLs and
quantitative headlines require the owner's real content before publication.
