# Choose the explanation the reader needs

Level and purpose are separate. L1 orients the reader across a chapter, L2 develops a substantial
subject, and L3 adds optional focused depth. Investigations often fit L3, but a mechanism walkthrough
or incident analysis can also be L3; an investigation can carry an entire L2 page.

Choose a primary purpose from the reader's question, not the filename or the format of the sources.
These are useful modes, not an exhaustive taxonomy or mandatory heading templates. A hybrid page
keeps one central question and uses a different mode locally when needed.

| Purpose | Reader's question | Useful progression | Evidence that earns space | Main failure to avoid |
|---|---|---|---|---|
| Architecture or mechanism explanation | How does this work, and why is it arranged this way? | Requirement → dependencies or data flow → choices → failure boundaries → checks | Diagrams, concrete input/output examples, invariants, a failure exposing a mechanism | Touring implementation components before explaining their purpose; treating tests as proof of all behaviour |
| Design decision or trade-off | Why choose this approach over the alternatives? | Need and constraints → viable alternatives → choice → consequences → conditions for revisiting | Actual constraints, decision-changing observations, comparisons where available | Inventing measured superiority for a reasoned choice; presenting an obvious straw-man alternative |
| Diagnostic investigation | What went wrong, and what explains it? | Symptom → competing explanations → discriminating checks → finding → intervention and verification | Reproductions, failed hypotheses that affect the conclusion, before/after traces | Recounting all debugging steps; claiming a cause from an association or a successful fix alone |
| Comparative evaluation or calibration | Does this help, how much, or where should a threshold sit? | Decision to inform → comparison and measure → results → uncertainty and error costs → supported decision | Controls, units, baselines, adverse cases, validation scope | Equating proxy improvement with end-to-end benefit; confusing calibration with held-out evaluation |
| Incident and reliability case study | What failed in operation, how was it contained, and what prevents recurrence? | Impact → failure mechanism → containment versus permanent fix → verification → remaining exposure | Timeline only when causal, logs, reproduction, regression checks, deployment scope | Mixing mitigation with root-cause repair; confusing deployed with validated; claiming exactly-once from correct final state |
| Chapter overview or synthesis | What problems does this area solve, and how do its parts connect? | Shared context → distinct responsibilities or questions → selected findings → links to depth | One representative example per subject, relationships and boundaries | A catalogue of pages, or compressing full investigations into disconnected result lists |

## Choose the opening from the reader's missing understanding

Before the first result or implementation detail, establish the foundation needed to assess it.
These are flexible patterns, not mandatory sections or a universal what/why/how checklist.

| Subject | Opening establishes | Possible route |
|---|---|---|
| Approach or technique | What it does, why it is needed, when to choose it | LLM judges: code vs interpretation, scale, checkability, then rubric failures |
| Architecture or mechanism | Required behaviour and execution constraints | Orchestration: sequential discussion vs independent votes vs simultaneous night actions |
| Testing strategy | The decision to make and the distinct questions tests answer | Model admission: integration, representative behaviour, real-game operation, then coverage limits |
| Design choice | Desired behaviour and competing requirements | Evidence design or conversation policy: what agents need to do and what prevents it |
| Investigation or incident | Observed problem, consequence and unresolved cause | Cache-key incident: unexpected reuse before explaining the key |
| Cost or performance | Resource consumption or delay and the trade-off to assess | Prompt-cache layout: repeated input, reuse boundaries and costs |

Parent context prevents repeated project introductions; it does not prohibit a concise definition
that makes the subject page readable independently. A model-admission page can be organised by what
each check establishes even though the runner executes them in sequence.

Use the chapter plan as a routing aid, not separate workflows: information boundaries explain allowed
knowledge, enforcement and checks; frontend pages connect user understanding/control to interface
behaviour; memory pages may explain mechanisms, choices or effectiveness depending on their question.
Choose one main question, then borrow another mode locally if needed.

## Adapt without fragmenting the page

- `day_and_night.md` is primarily architecture: execution dependencies determine the order. The
  private-note bug is a local diagnostic example, not a reason to recount the whole development.
- `evidence_design.md` combines design decisions with evaluation: explain why partial evidence and
  competing claims matter, then distinguish replay evidence from whole-game evidence.
- `human_in_the_loop.md` explains a mechanism through a reliability incident: human turn → replay
  failure → reuse and safe updates → persistence limits. The incident gives the mechanism a purpose.
- A silence-policy page can explain the policy first, then use calibration to explain its choice.
  A complete calibration log remains in evidence; moving it to L3 does not make it an explanation.

For a hybrid, record the main purpose and which sections use another mode in the brief. Do not add a
section for each mode, and do not import every suggested stage if it does not help the reader.

## The same principles apply to every mode

State the reader's question and central answer. Explain concepts before using them; choose details
by what they help establish. Connect sections through reasoning. Preserve technical distinctions,
source support and material limitations. Distinguish observation, interpretation, design intent,
implementation and validated behaviour. Make the page understandable without following its links.

Evidence logs and reproduction instructions are different deliverables. Logs preserve chronology,
complete variants and raw results; instructions organize executable steps and prerequisites. Keep
them in their appropriate source locations and link them. Do not force them through the portfolio
workflow unless the user asks to turn them into a reader-facing explanation.

Review according to purpose: a design rationale need not invent an experiment; a comparative claim
needs an adequate comparison; a mechanism needs enough detail to follow its operation. Depth is the
explanation needed for the claim, not a fixed number of sections, studies or words.
