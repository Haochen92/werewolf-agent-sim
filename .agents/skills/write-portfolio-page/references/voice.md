# The owner's voice and page rules

Rules the owner gave across review rounds (2026-10-13 to 2026-10-28) that are not all written in the
three `portfolio-*` guides in this folder. The guides win if the two ever disagree.

## Voice

1. **Name the thing first.** "The Ninth Express is a variant of the Mafia-style game played with AI
   agents."
2. **Familiar → specific, one layer at a time.** No term before its base. On technical pages, the
   game's need comes before the framework term (votes must be collected independently → fan-out).
3. **Define by what each party knows and wants;** explain a design by the tension it resolves.
4. **Frame, then parts:** "usually through two basic mechanisms" → the day → the night.
5. **Plain, owned, conversational.** Always "I", never "we" (solo developer), but never claim
   AI-written code as hand-written. Counts a reader can picture.
6. **Put material scope beside the claim it limits.** Keep dates and versions in source notes unless
   they change the interpretation. Avoid repeated generic disclaimers; never postpone a qualification
   needed to understand the explanation accurately.

## What a page holds

7. **Select evidence by its purpose.** Keep findings that explain a decision, support a mechanism,
   test a result or expose a limitation. Full run histories belong in evidence reports.
8. **Give each passage one main job.** Level 2 explains the decision and its strongest evidence.
   Keep essential comparison conditions, denominators and limitations on the page so its claim can
   be assessed without opening links. Introduce the comparison before its numbers; move exhaustive
   variants and reproduction details to evidence or focused L3 depth.
9. **Explain the finding, don't recount the investigation.** One path: causes → the evidence that
   tells them apart → what was done about each. Organise by the finding, not by the order the work
   was done. This is an organisation problem, not a word-count problem.
10. **Topic selection over compression.** A detail that answers a different question than the
    page's moves to a deeper page or a note, even if true and impressive. Do not shorten the
    remaining explanations to compensate.
11. **One term, one meaning; one unit per paragraph; one question per paragraph; one job per
    sentence, point first.** Split a shared term before using it. Explain necessary changes of unit.
    Keep full provenance in source notes and essential identifying context beside the claim.
12. **Diagrams carry what; prose keeps why.** Cut a passage only when a figure shows the same facts.
    A link to a deeper page follows a stated problem, never a bare caption.
13. **Every sentence advances understanding.** Context, connections, reasoning, evidence and
    consequences all earn space. Remove empty repetition and theatrical framing; do not remove the
    connective explanation that makes facts coherent.
14. **Observation ≠ cause.** Call a mechanism "suspected" unless a test isolated it. Rule tests show
    the rules run as written; they do not show the behaviour is useful.

## Words to avoid

- **Technical language:** retain established terms when they help the reader understand or discuss
  the engineering. Explain them on first use; use plain descriptions when terminology adds no value.
  This applies to statistical methods too: do not erase a meaningful distinction to avoid a word.
- **Model names and versions:** avoid a catalogue of names in explanatory passages. Keep names when
  model-specific results or changes would otherwise be ambiguous; full configuration goes in sources.
  Do not substitute “stronger” or “cheaper” unless the evidence supports that description.
- **Habits the owner rewrote out:** abstract nominalisations ("that distinction creates the central
  design problem"), defensive negations ("it was not a comparison of …"), trade-off jargon ("taking
  responsibility for validation in exchange for …"), promotional adjectives, rhetorical
  question-and-answer, repeated "Problem / Decision / Result" labels.

## Care on a public page

- Repository bookkeeping that is honest in `evidence/` but reflects poorly stays off: unaudited
  AI-written tests, missing CI, uninstalled jobs, missing scripts, untracked records, runs from
  uncommitted code, held spend, retracted numbers. Follow the chapter's Handle-with-care list exactly.
- A fault the project caught is told as caught and what changed, with its scope; never hidden, never
  dramatised.
- A limitation that changes how to read a result always stays.
- The reader will not open the evidence. Spend checking effort on whether the reasoning holds
  (experiments kept apart, cause not overstated, scope beside the claim), not on re-auditing every
  figure; still never invent or silently change a number.
