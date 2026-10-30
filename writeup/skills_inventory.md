# Portfolio skills: public tags and the evidence behind them

Reviewed 2026-10-26 against the map, the gameplay reports and targeted observability code. This is a
curated vocabulary, not an automatic export of every block tag. The map retains narrow keywords to
help organise evidence; the public portfolio should expose a smaller set of substantial capabilities.

A tag describes work demonstrated by the project, not proof that every feature is complete or that
all code was written unaided. AI-assisted implementation and validation limits belong beside the
relevant case study. Standard terms make the work easier to identify, but do not guarantee any
particular automated-screening result. Use the terms in concrete descriptions as well as tags.

## Public tags

Use the relevant two or three tags on a chapter card, rather than repeating this whole list everywhere.
The home chapter explains the capability; other chapters link to the same evidence or show an application.
Block references are pointers, not proficiency scores. Repeated mentions of one component do not count
as independent demonstrations.

| Public tag | What supports it | Evidence blocks | Main home |
|---|---|---|---|
| **Multi-agent orchestration** | Explicit graph routing, shared state, parallel rounds and sequential discussion | 102–104, 107–113 | 1: Game design and orchestration |
| **Human-in-the-loop systems** | Interrupt/resume, persisted checkpoints and reuse of completed AI turns on cache hits | 105–106, 115 | 1 |
| **Context engineering** | Clear private history, source hierarchy, summaries, conditional context and replayed input fixes | 68–72, 140–146 | 3: Context engineering |
| **Structured outputs and validation** | Typed decisions, legal-target constraints, claim fields, validation and fallbacks | 69, 71, 103–104, 120, 147 | 1: output contract; 3: prompt/schema behaviour |
| **Symbolic reasoning** | Constraint propagation and conditional deductions from a seat's allowed information | 48–52 | 3; prominent only if the owner can explain the algorithm and its limits |
| **Retrieval-augmented generation (RAG)** | Retrieval filtering, reranking, query/document preparation and evaluation | 35–46, 85–93 | 4: Memory |
| **Agent memory** | Extraction, deduplication, consolidation and testing of lessons across games | 17–23, 56–62, 73–78, 94 | 4; does not imply demonstrated continual improvement |
| **LLM evaluation** | Judge design, labelled references, frozen-turn comparisons and regression benchmarks | 22, 28–29, 45, 53, 79, 81–89, 128, 137, 150–151 | 5: Evaluation |
| **Experimental design** | Paired comparisons, pre-registration, power analysis and explicit treatment of confounds | 9, 63–67, 82, 88, 138, 142 | 5; applications in 3, 4 and 6 |
| **Software testing** | Unit, integration, regression, property-based and metamorphic checks, with scope stated | 3, 47, 52, 70, 114, 129, 136, 151, 160, 162 | Each chapter's verification; method overview in 5 |
| **LLM inference optimisation** | Prompt caching, offline batch inference, model selection by job and cost attribution | 6–11, 74, 96, 100, 159 | 6: Cost and latency |
| **Reliability engineering** | Time budgets, provider fallback, graceful degradation and cache-resume incidents | 97, 101, 104–106, 115 | 7: Production; execution mechanics in 1 |
| **LLM observability** | Trace instrumentation, case persistence, prompt capture, provenance, usage and error monitoring | 153–163 | 7; evaluation consumers linked from 5 |

## Supporting keywords and tools

These belong in the relevant chapter or project description. They should not all become global badges.
A method or tool deserves a keyword when the page explains what it did, the decision involved and the
verification available.

| Capability | Supporting terms | Placement and limits |
|---|---|---|
| Orchestration | **LangGraph**, state machines, fan-out/fan-in, asynchronous programming, checkpointing, cache-key design | Chapter 1. Name the framework, then explain the application decisions. Checkpointing is demonstrated; exactly-once execution is not claimed. |
| Context and outputs | Prompt engineering, conditional prompt composition, schema validation, source attribution, dialogue management | Chapters 1 and 3. Field ordering is a prompt/schema technique; a semantic echo gate is a model judgement, not a deterministic safety guarantee. |
| Symbolic reasoning | Constraint propagation, rule-based inference, conditional reasoning, oracle testing | Chapter 3. “Neuro-symbolic system” may describe the overall combination of LLMs and a solver, but is broader than the implemented mechanism. Prefer the precise algorithm in public descriptions. |
| Retrieval and memory | Embeddings, semantic similarity, reranking, query rewriting, deduplication, memory consolidation, credit assignment | Chapter 4. Document normalisation concerns retrieval inputs; faithfulness concerns content quality. Neither should be treated as a synonym for agent memory. |
| Evaluation | **LLM-as-a-judge**, reference datasets, annotation rubrics, blind evaluation, offline replay evaluation, ablation studies, paired A/B testing | Chapter 5. State when labels came from models rather than people. A golden prompt snapshot is a software regression test, not an annotated quality dataset. |
| Statistical methods | Power analysis, Monte Carlo simulation, bootstrap resampling, stratification | Chapter 5, attached to the specific studies. A mention of a statistical concept alone is not a skill demonstration. |
| Inference optimisation | Prompt caching, batch inference, model selection, model routing, token/cost accounting | Chapter 6. Fixed per-job selection is not adaptive routing; API inference optimisation is not model quantisation or GPU-kernel optimisation. |
| Observability and data | **Langfuse**, LLM tracing, experiment tracking, data provenance, evaluation data pipelines, audit logging, **Sentry** | Chapter 7. The case sink and artifact manifests are data-engineering evidence. Traces here do not by themselves demonstrate cross-service distributed tracing. |
| Security-related implementation | Credential redaction, secrets handling, context isolation | Context isolation in chapter 2; secrets handling and credential redaction in chapter 7 (moved with the secrets material, owner 2026-10-29). Promote a broader security tag only after the browser/access-control material is reviewed. Prompt injection is currently a documented gap, not an implemented defence. |
| Simulation | Simulation environment design, dialogue scheduling, evaluation of deceptive gameplay | Chapter 1. These explain the domain and agent behaviour; they do not establish adversarial ML, red teaming or game-theoretic optimisation. |

## Terms corrected or held back

| Previous term or grouping | Recommended treatment | Reason |
|---|---|---|
| “Multi-tenant isolation” for the cache fix | **Cache-key design**, under reliability and orchestration | The demonstrated boundary is between game runs. A full tenant model, access-control boundary and isolation guarantees were not established by that incident. |
| “Event sourcing” for the discussion scheduler | **Event-driven scheduling** or **shared-state architecture** | Recomputing speaking obligations from a transcript does not alone show an event-sourced system. Review the authoritative event-store/recovery design before using that broader term. |
| “Calibrated output” for deduction wording | **Conditional reasoning** and **structured outputs** | Labelling a claim conditional or certain is not statistical confidence calibration. |
| “Chain-of-thought prompting” for field order | **Prompt engineering** and **structured outputs** | Ordering reads and notes before an action shows an output-order intervention; it does not establish how the model internally reasons. |
| “Adversarial agents” as a public skills badge | **Simulation environment design**; describe deceptive agents in the case study | A role-playing agent that lies is not evidence of adversarial robustness or security testing. |
| “Faithfulness” folded into agent memory | Discuss as a content-quality requirement | Preserving a persona's meaning and preserving a lesson's meaning are applications of a quality criterion, not the same memory mechanism. |
| “Schema design” folded into RAG | Place under structured data/context design, linked to retrieval where used | The skill is not inherently retrieval-specific. |
| “Baseline comparison” folded into credit assignment | Distinguish an algorithmic reward baseline from an experimental control | They answer different questions even when both appear in a memory study. |
| “Prompt injection” listed as a security skill | Keep as a gap until mitigation is implemented and evaluated | Recognising the limitation is useful judgement; it is not a deployed protection. |
| Block counts as evidence of skill depth | Link selected design, verification and incident blocks | Counts reflect how the map was split, and can reward repetition instead of depth. |

## Chapter assignments

- **Chapter 1:** multi-agent orchestration, human-in-the-loop systems, structured outputs and validation.
  Keep simulation design as a supporting term. The cache mechanism and fix belong here.
- **Chapter 2:** context isolation is currently supported; secrets handling moved to chapter 7 with the
  secrets material (owner 2026-10-29). Browser access control needs its own evidence pass before any
  chapter is given broader security tags.
- **Chapter 3:** context engineering, structured outputs and validation, symbolic reasoning. Thinking
  effort is a supporting topic spanning correctness here and inference cost in chapter 6.
- **Chapter 4:** RAG and agent memory. Show credit assignment and learning-loop results without implying
  reinforcement-learning training or a proven self-improving system.
- **Chapter 5:** LLM evaluation, experimental design and software testing. Topic chapters still present
  the checks for their own claims.
- **Chapter 6:** LLM inference optimisation. Model admission's quality criteria stay in Evaluation;
  selection by cost and latency belongs here.
- **Chapter 7:** LLM observability and reliability engineering, with secrets handling and credential
  redaction (moved from chapter 2, owner 2026-10-29). Experiment provenance serves Evaluation;
  the recording pipeline and operational failures have their main home here.

These assignments do not require another chapter. The new observability blocks fit chapter 7 well:
153–154 introduce the recording needs and paths; 155–156 explain case capture; 157 supplies provenance;
158–159 cover audit and operational records; 160 verifies them; 161–163 are optional incident details;
164 states limitations. Block 163 links to chapter 1's cache case instead of retelling its mechanism.
Block 162 is supporting provenance/refactor evidence, not a second headline observability achievement.

## Pending evidence reviews

| Candidate terms | Source still to review | Expected home |
|---|---|---|
| Model fine-tuning, cross-encoder reranking, ONNX inference benchmarking | `fine_tuning/report.md`; include only the training/deployment methods actually exercised | 4 |
| Access control, authenticated streams, viewer-specific data filtering | Server and frontend reports/code | 2 |
| Frontend engineering and its concrete framework/tool terms | Frontend evidence, owned by the other session | 8 |

Python, PostgreSQL, FastAPI, Docker and other implementation tools can appear in a separate technology
stack when their supporting implementation is reviewed. Do not confuse a dependency list with the
project's key engineering contributions, and do not omit substantial tool experience merely because it
is not a conceptual chapter tag.
