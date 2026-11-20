# Level 2 writing prompt and review rubric

Status: provisional, 2026-10-25. Based on the revised
[factual-errors page](../../../../writeup/evaluation/factual_errors/factual_errors.md), which the owner preferred to the
earlier draft. A first transfer draft, [code checks](../../../../writeup/evaluation/code_checks/code_checks.md), followed the structure
but needed an editorial pass on claim scope and explanatory density. Neither the prompt nor these
pages are being marked publication-approved here.

Use with the [general portfolio prompt](portfolio-writing-prompt.md) for shared evidence and publication
rules. This file adds Level 2 guidance. The copyable block is also usable on its own with supplied sources,
an outline and constraints. It is a writing prompt, not a skill.

## What the earlier draft taught

The original had useful research, a sound overall sequence and a strong featured experiment. Its weakness
was explanatory organisation, not a lack of technical terms or a need to shorten everything.

| Weakness | Specific change | Rule to carry forward |
|---|---|---|
| The workflow appeared before the diagnostic question | Opened with missing/wrong information, ambiguous presentation and reasoning failure | State the decision or distinction the reader must understand before listing the process |
| Input problems dominated the explanation | Added reasoning failure as a separate possibility, supported by separate model/budget experiments | Check conceptual coverage: the lead story must not imply that its cause explains every failure |
| Dense paragraphs stacked method, counts, results and caveats | Split discovery by live play from frequency estimation; retained meaningful counts near the finding | Give each paragraph one explanatory job; select numbers by what they establish |
| Diagnosis, fixes and downstream errors repeated across sections | Combined them into matching the intervention to the source, with one downstream example | Give each explanation a primary home; cross-reference instead of restarting it |
| “Facts present” became “good input” | Distinguished presence, correctness and clarity | Preserve distinctions on which the intervention depends |
| A useful fix became an overly certain causal explanation | Separated observed result, plausible mechanism and scope | An intervention working does not necessarily identify the internal mechanism |
| Reasoning budget and a stronger model read like one experiment | Named the different inputs, interventions and scopes | Connect studies through the question they inform, not an unsupported pooled result |
| Slogans replaced conclusions | Replaced “the model fixes reasoning, the pipeline fixes input” with a conditional diagnostic approach | Explain what to inspect or test next; avoid universal rules from a few cases |
| Small observations read like general rates | Changed “three in four” to “three of four observed errors” | Preserve the actual sampling unit and denominator |
| A section recounted the investigation instead of explaining the finding (chapter 1, "Why silence needed more than one fix", owner 2026-10-28) | Rebuilt as one path: the causes → the evidence that tells them apart → a different fix for each; side investigations moved to notes | Organise by the finding, not by the order the work was done; the problem is organisation, not word count, and shortening without restoring the path makes prose denser |
| One word carried two meanings: a “pass” was sometimes the player's choice and sometimes the engine withholding speech | Split the term before using it: held, never offered, chose to pass | Draw the distinction before using the shared label; one term, one meaning |
| Units changed every sentence (passes, players, games, voting days, sampled accusations) | Kept one unit per claim; moved the other counts to notes | Keep one denominator per paragraph where possible; never make the reader re-work what a number counts |
| A paragraph switched questions midway (why silent → did silence draw suspicion → why the talk was thin) | Kept the first question; the others moved to notes or their own page | One question per paragraph; a related investigation gets its own explanation or a link |
| One sentence carried version history, mechanism and context before the finding (“On the June design, the first sequential one, …”) | Opened with the mechanism in plain terms; dates and models went to the sources comment | Give each sentence one job; lead with the point, put provenance in notes |
| Every paragraph tried to explain the design, report the experiment and qualify the evidence at once, so the reader kept switching between understanding the system and auditing the research (chapter 1 review, owner 2026-10-28) | Calibration section rewritten to lead with the decision and its strongest evidence, in words; the experiments, counts and limits moved to the Level 3 page and supporting notes | Level 2 explains the decision and its strongest evidence; Level 3 carries the detailed comparisons. Give each passage one primary job |
| Several experiments and denominators arrived with no hierarchy (23/40, 13/25, 20/64, 41/64, 10/29, 0/36, 41/100, 54/93 before the reader knew what changed) | Named the separate questions first, kept the conclusion of each in words, moved the counts down a level | Before writing, list the separate questions a passage answers; a reader must understand what changed before meeting any number |
| An observation became a general cause (“with nothing to go on, the model takes the lowest player number” from four games) | — (flagged; not yet rewritten) | Keep what happened apart from the suspected explanation; call a mechanism “suspected” unless a test isolated it |
| Different kinds of verification were one inventory (rule tests, behavioural checks, whole-game reads) | — (flagged) | Say what each kind of test establishes: rule tests show the rules run as written; behavioural evaluations show whether the result is useful; passing the first does not establish the second |
| A limits list mixed evaluation gaps, a failure story, tuning history and a known bug | — (flagged) | Group limits by purpose; put a failure story beside the mechanism it exposes; a known mismatch is a fix to make, not something “not established” |

## Copyable Level 2 prompt

```text
Write a Level 2 engineering portfolio page for a hiring reader who is technically curious but new to
the project. Develop the subject beyond its Level 1 summary without turning it into a chronological
research log or a catalogue of everything in the sources. Make the engineering reasoning easy to follow.

INPUTS
Subject and reader question: [INSERT]
Approved outline and parent Level 1 summary: [ATTACH]
Source reports, relevant experiment records and explicit corrections: [ATTACH]
Ownership, publication and editorial constraints: [ATTACH]
Existing draft and authorised output file, if any: [INSERT]
Optional approved whole-page exemplar, page copy only: [ATTACH]

BEFORE DRAFTING
Read the inputs. Make a short authoring outline that identifies:
- The central question and the distinctions needed to answer it.
- What the parent summary already explains, and the new understanding this page adds.
- One featured story that connects problem, intervention, evidence and consequence.
- Other examples only where they demonstrate a distinct cause, decision, limitation or method.
- For each experiment: situation, intervention, comparison, measure, sample, result and supported claim.
  Do not combine different experiments into a single apparent result.
- Missing evidence, disputed claims or unverified ownership. Omit or qualify affected claims; do not
  fill gaps with plausible details. Keep unresolved notes outside public prose.

Do not write the entire page around the featured story's mechanism if the subject has other important
mechanisms. In factual-error diagnosis, for example, missing facts, ambiguous presentation and faulty
reasoning on correct information must remain distinguishable. For another subject, identify its own
relevant distinctions rather than copying those categories.

PAGE DESIGN
- Open with the problem and the central engineering question or decision. Briefly explain the approach.
  Do not begin with a full project introduction or an unexplained list of methods.
- Organise subsections in the order a reader needs to understand the decision. Workflow order can help,
  but chronology is not mandatory. Preserve the supplied outline unless a local change clearly improves
  clarity; report material structural changes in the authoring note.
- Give each subsection one main purpose. Put the fullest explanation in one place. Other sections can
  refer back briefly without repeating the story, numbers and caveat.
- Keep complete experiment logs in evidence/: run histories, full variant tables and reproduction
  details. Portfolio pages select evidence to explain decisions. Optional L3 pages add focused depth,
  not exhaustive records. Keep enough method, results and limitations on this page for the reader to
  assess its claims without following a link; never move an adverse finding out just to simplify it.
- Develop the featured story with enough context to understand the competing explanations, the test
  and the result. Integrate exhibits where the reader needs them. A prompt excerpt, screenshot and
  results table should each serve a distinct purpose; do not force all three onto every page.
- For a workflow with handoffs or branching decisions, consider a compact labelled diagram before
  writing several paragraphs of process description. Introduce the problem, show the flow, then use
  prose and one short supporting result to explain the choice and its limits. Mark historical,
  current and proposed behaviour explicitly. Do not duplicate the diagram step by step in prose;
  deeper case analysis can sit in a focused L3 investigation while L2 retains the decisive evidence.
- An optional Level 3 link sits beneath the subsection it deepens. This page still states that
  finding and its essential evidence; the Level 3 page adds method and analysis. Every Level 3 page
  has such a subsection in its L1 or L2 parent (or a passage in one); not every subsection has a
  Level 3 page. A self-contained L1 can link directly to L3 without an intervening L2.
- Keep the result, implication and material scope together. Conclude with the remaining limits or next
  evaluation step, not a repeated summary of every method.
- Keep substantive explanation on the portfolio. Evidence links establish provenance, not an obligation
  for the reader to open GitHub to understand the work.

SELECTION AND AUDIENCE CHECK
- The target is entry-to-mid-level AI engineering. Does the page demonstrate practical judgement at
  the strength actually supported, rather than defend an unnecessary research-level claim?
- Does the opening establish what the reader needs before methods, results or implementation detail?
  Evaluator choice needs purpose and selection criteria; an admission strategy needs the distinct
  questions its checks answer. Adapt the opening instead of applying one sequence to every topic.
- Can the core argument be stated without listing experiments? Which example carries each point?
  Remove secondary branches before compressing necessary explanation; do not preserve all results
  as disconnected one-sentence summaries.
- For reviewer requests for context, decide whether to explain, relocate or remove the passage.
  Check the remaining transitions after cuts. L3 needs a follow-up question, not just overflow.

DEPTH WITHOUT DENSITY
- Aim initially for roughly 1,200–2,000 words of reader-facing content, including captions and tables.
  This is a guide, not a limit. Cut repetition before technical substance. Do not pad a short subject,
  or create Level 3 solely because a word count was exceeded.
- Each paragraph should develop one idea. Separate setup, method and interpretation when combining
  them makes the paragraph difficult to read. Vary paragraph length naturally; do not impose two
  paragraphs on every subsection.
- Include details that help the reader understand a choice, assess evidence or recognise a transferable
  lesson. Intermediate processing counts and version history need a reason to appear.
- Use technical terms precisely, with a short explanation on first use. Do not erase distinctions for
  simplicity or add terminology as decoration. Let the example demonstrate the method.
- Follow a number with its meaning for the decision. Preserve denominator, unit and relevant conditions.
  Explain “noise floor”, for example, through what was repeated and how much its result varied.
- State the practical limit instead of saying only “directional”, “robust”, “proven” or “validated”.
- Use supported first-person contributions. A source saying “read by hand” does not identify the author
  as that reader. Do not invent personal implementation or review work.
- Use natural prose rather than repeated “Problem / Decision / Example / Result” labels. Headings can
  be descriptive or questions, but must tell the reader what the subsection explains.

CAUSAL AND EVIDENTIAL PRECISION
- Separate observation (what happened), interpretation (why it might have happened), and intervention
  evidence (what changed when a variable was altered).
- Correct information being present does not establish that it was unambiguous or used correctly.
  A false answer alone does not identify a model capability limitation.
- If an intervention changes two details together, do not claim to have isolated either detail.
- Do not infer a general rate from selected failures, repeated samples of one case or a tiny anecdotal
  set. “Three of four observed errors” is not a general 75% recurrence estimate.
- Distinguish more reasoning on one model from a different model, selected-case replays from ordinary
  games, judge variation from generation variation, and exact counts from validated outcome proxies.
- Model labels are not human validation; human review also has scope and uncertainty. Code is not
  automatically correct because it is deterministic. A test retained for regression checks does not
  guarantee the failure never returns.
- Describe built, run, deployed and validated as separate states. Do not turn an intended practice into
  “every change is tested” unless the records establish that coverage.
- Avoid a universal lesson such as “instructions do not work” when only particular instructions failed.
  Describe what the result makes worth inspecting or testing next.

FOCUSED ONE-SHOT EXAMPLE

Input facts:
The investigator's prompt contained all its real checks. The night-3 result concerned a player who also
died that night. Its private result used “revealed”, the word used for public death announcements, and
was dated by day. Its previous private note referred to “my investigation result from last night”.
Reading the prompt suggested two candidate influences; only subsequent replays tested interventions.

Weak framing to avoid:
“The model failed on good input. Replaying it separated a misleading wording from a reasoning slip.”
This conflates the presence of facts with clear presentation and overstates the mechanism identified.

Desired output:

#### The facts were present, but were they clear?

The investigator's input listed all its real checks. That ruled out a missing result, but did not
establish that the result was clearly presented.

Its night-3 check concerned player_5, who died that same night. The game publicly announces dead players'
roles, and the private check used the same word, “revealed”, without saying “you investigated”. It was
also dated by day rather than night. A second possible influence was the agent's previous private note,
which referred to “my investigation result from last night”. Reading the prompt suggested both
possibilities; it could not establish which change would help.

Use this example for clarity and reasoning, not as a mandatory wording template or a source of facts
about the new subject. A whole-page exemplar, if supplied, teaches the broader progression and depth.

REVIEW BEFORE RETURNING
Apply the rubric below to the draft. Fix any missing distinction, unsupported claim or misleading
aggregation before polishing the prose. Then read only headings, opening sentences and exhibit captions:
can the reader follow the problem, intervention and conclusion?
Run three additional checks:
- Universal wording: inspect “every”, “only”, “exact”, “proves” and “establishes”. Does the evidence
  support that scope? Put the tested conditions beside the claim; repeatability does not establish
  correctness or exhaustive coverage.
- Competing explanations: could both be true? State which question the test actually answers.
  An input audit can reveal unreliable inputs without showing that corrected inputs improve outcomes.
- Caveat reversals: does a later qualification undo the natural reading of an earlier sentence?
  Rewrite the earlier claim so the qualification refines it rather than retracting it. For example,
  distinguish a private field in an intermediate payload from one reaching the final prompt immediately.
Finally read the full text for gaps
that the skim cannot reveal. Do not use a fluent sentence to conceal missing evidence.

Three interpretation checks, applied sentence by sentence:
1. Universal language: for every "every", "all", "only", "never", "exact", "proves" or "establishes",
   state its scope in the same passage. Deterministic execution is not correctness: "code checks it
   the same way every time" is not "code shows it is right".
2. False alternatives: when the page offers explanations as alternatives, ask whether both could be
   true, and whether the experiment actually distinguishes them.
3. Caveat reversal: if a later qualification undoes what a reader would take from an earlier sentence,
   rewrite the earlier sentence instead of leaning on the caveat.

OUTPUT
Produce the requested page copy or edit only authorised files. Separate authoring notes, source mappings
and exhibit specifications from public prose. Include a short completion note identifying material
changes and unresolved verification needs. Do not include self-scores, the authoring outline or rubric
in the public page. Do not mark the draft approved or publish it without instruction.
```

## Review rubric

Use **0 = fails, 1 = partly clear, 2 = clear** for each criterion. This is an editorial aid, not a
validated metric. Do not average scores: good prose cannot compensate for an unsupported claim.

| Criterion | What a score of 2 requires | Symptom requiring revision |
|---|---|---|
| Reader orientation | The opening establishes the problem and the decision the page helps explain | A list of methods before the reader knows why they matter |
| Added depth | The page explains setup, choices and interpretation beyond Level 1 | A longer paraphrase of the overview |
| Conceptual coverage | Relevant mechanisms and alternatives are represented and distinguishable | One vivid example silently stands for every kind of failure |
| Paragraph clarity | Each paragraph develops one idea with clear connections | Several experiments or stages compressed into one paragraph |
| Narrative economy | Each subsection has a distinct purpose; repetition is purposeful and brief | Diagnosis and fix sections retell the same incident |
| Experimental separation | The reader can identify each intervention, comparison, sample and setting | A stronger-model result appears to confirm a different reasoning-budget experiment |
| Interpretation | Observations support the stated conclusion; hypotheses are labelled as such | “It fixed the output” becomes “we proved the internal cause” |
| Evidence and ownership | Claims, numbers, scope and personal contributions match the records | Missing denominators, unverified “I”, planned work described as completed |
| Technical accessibility | Terms identify real methods and are explained through context | Jargon without explanation, or simplification that erases a key distinction |
| Exhibits and links | Each exhibit advances the argument; the finding is understandable on-page | Decorative charts or essential caveats only in linked reports |

**Required before calling a draft review-ready:** experimental separation, interpretation, and evidence
and ownership must each score 2. Every other score below 2 needs a concrete edit or an explicit authoring
note explaining the remaining issue. This is a revision rule, not a numeric quality guarantee.

## Testing whether the prompt transfers

Apply it to a different Level 2 subject, such as LLM judges, using that subject's own evidence. Review the
result against the same rubric and record recurring defects before changing the prompt. The current
example was revised with substantial feedback; one successful rewrite does not establish that the prompt
will reproduce that quality without review. Preserve the approved reference separately once approved.


## Drafting and editorial review handoff

The drafting agent prepares the page and checks its factual claims against the supplied evidence.
The editorial reviewer focuses on structure, phrasing, reader comprehension and whether the wording
claims more than the described evidence supports. An editorial pass is not factual verification.

Keep a short authoring note for changes that affect a mechanism, comparison, measurement or scope.
The verifying agent checks those changes before approval. Preserve legitimate differences in voice,
heading style and paragraph rhythm when they remain clear and meet the rubric; do not rewrite them
solely to resemble the exemplar.
