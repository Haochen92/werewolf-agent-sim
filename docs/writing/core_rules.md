# Core writing rules

*In use from 2026-11-17. Tested on real note sections before adoption. Change an existing rule when
a recurring failure shows it is wrong; do not add rules.*

These rules apply to every document in this repository: study notes, experiment logs and reports,
portfolio pages, plans. Read this page first. Then read the short guide for the type of document:

- portfolio pages: `.agents/skills/write-portfolio-page/references/voice.md`;
- experiment logs and reports: `docs/writing/report_guide.md` when it exists, and until then the
  sections of `evidence/experiment_report_style_guide.md` for the document type;
- study notes: the "Study notes" column of the table below, and the notes' own template.

Which document wins when two disagree: this page, then the guide for the type of document, then
approved example pages. The older long guides are reference only.

The goal is that the reader spends as little effort as possible on each idea. The goal is not the
fewest words. The aim is a writer who explains naturally and accurately, not one who applies
formatting rules mechanically.

Accuracy always comes first. Among accurate explanations, choose the one that is easiest to
understand on the first read. If another rule below makes an explanation unnecessarily difficult,
rule 1 takes precedence over that rule.

## The rules

**1. Write each sentence so that it is understood on the first read.** Say who or what acts, what
it acts on, and what result the action has. State the cause and the consequence instead of leaving
a step for the reader to work out.

- Before: "A spending cap is only as good as the record it counts from."
- After: "To enforce the daily limit on free games, count the game records created that day.
  Unlike a counter held in memory, this count is still correct after the server restarts."

**2. Explain concepts in the order the reader needs them.** Start with the problem and the simplest
account of how the mechanism works. Establish how the main concepts relate before introducing
exceptions, failure cases or implementation details. For a study note the usual order is: the
problem, the simple model, the mechanism, the ways it fails, how my application does it, and the
trade-offs. This is a guide, not a template. A document can obey every sentence rule and still be
hard to learn from if the information arrives in the wrong order.

**3. Use words in their literal meaning.** Do not use a figure of speech, a phrase invented for the
document, or a maxim in place of an explanation. Established technical terms are fine, including
ones that began as metaphors ("race condition", "blast radius"). An analogy is fine when it helps
and the literal statement is given with it. A short sentence needs no rewriting if its meaning is
already literal, such as "A permitted action can still be wrong." When rewriting, a word the
source uses in a private sense, such as "a steered model", is replaced, not defined and kept.

- Before: "Delimiters raise the cost."
- After: "Delimiters help the model distinguish instructions from outside content, but they cannot
  guarantee that the model ignores a malicious instruction."

**4. Give each sentence one main idea, and each paragraph one question to answer.** A cause and its
consequence belong in the same sentence. Do not split an explanation into fragments.

- Too packed: several unrelated points joined by semicolons or by stacked modifiers such as
  "criticality-ordered, freshness-dated".
- Too fragmented: "The counter is stored in memory. The server restarts. The counter resets."
- Right: "A counter held in memory resets when the server restarts, so more requests can be
  allowed than the daily limit permits."

Keep tables easy to scan. Give each cell one main point, in a complete sentence when that is
clearer. Group a long table by meaningful categories when that helps the reader understand or
compare the information. Move a lengthy explanation out of the table when it interrupts scanning.

**5. Make each claim exactly as strong as its evidence.** Give the sample size where a result is
first stated and wherever the reader needs it to interpret a number. With a small sample, say
whether the result shows only which way an effect goes or also how large it is. For an explanation
that was not tested, choose the word that matches the evidence: "suspected" when the evidence
points to it, "possible" when it is merely consistent with what was seen. When one check is
missing, name that check; do not call the whole system untested.

**6. Explain a term where it first appears, and use one name for each thing.** Use the standard
technical term in place of a home-made label ("data exfiltration", not "data sent out"). Explain it
in the same sentence, or in the next sentence when the first is already long. Internal names need
the same. Do not call one thing by two names, or two things by one name.

- "The query writer is an LLM call that converts the current game state into a search query for
  retrieving relevant memories."

**7. Give the context before the number.** Say what was measured, against what, and in which unit
(turns, games, messages). Prefer counts a reader can picture, such as "a loser's good move was
called positive 23% of the time, a winner's 83%". Keep a statistical estimate as well when the
finding depends on it.

**8. Keep a needed qualification next to the claim it limits.** State it once, where it changes how
the result should be read. Do not repeat it in every section.

**9. Replace a word that only judges quality with what was observed.** "Cleanly", "robust" and
"works well" say the writer was satisfied. Write the observation, such as "15,001 of 15,005 prompt
tokens served from cache".

**10. Reduce length by removing repetition or by moving less relevant topics elsewhere, not by
compressing explanations.** Keep the details needed to understand the central argument. Move
material that answers a different question to a separate page, the experiment log or a note.

**11. Do not invent anything.** When rewriting existing material, keep its numbers, verdicts and
statuses, and do not silently recalculate or change them. When new analysis needs a calculation,
show its inputs and say that the result is newly derived. Rewording a supplied result is not the
same as verifying it: say which you did. If a clear explanation needs a fact the source does not
give, do not supply one: leave it out and list it as a question for the owner. Label a made-up
example as illustrative. Say which stage the work reached: built, run, deployed, or validated
(shown to work by a test or a measurement). Use "I" for work the records show the owner did, and
never "we"; explanatory text often needs no pronoun at all.

**12. Have a fresh reader check the finished text.** The writer already knows what each sentence
means and cannot tell which ones are hard to read. Give the text alone to a person, or to a model
in a new session. Ask the reviewer to identify four things: sentences likely to need a second
read, unusual or unnecessarily figurative word choices, explanations that are missing, and concepts
introduced before the reader has enough context to understand them. Then fix what it lists. An
item may be rejected when fixing it would add an unsupported claim; say which items and why.

## Rules that depend on the type of document

| | Study notes | Experiment reports | Public portfolio pages |
|---|---|---|---|
| How much general background | Teach the general concept and mechanism first, then connect it to my application | Only what is needed to understand this experiment | Only what is needed to understand the architecture, findings and decisions |
| What it is organised by | The concepts and questions the reader must understand | The findings: question, answer, then evidence. The order in which the work was done belongs in the experiment log | The same as reports |
| Question headings | Use a heading phrased as a question when it is a real question the reader needs answered | The same | The same. Do not use a rhetorical question in the prose as a dramatic opening |
| Guidance about the document itself | A suggested reading path is useful | A log's header says that where entries disagree, the later one is correct | Keep to what helps the reader find their way |
| Facts kept off the page | None | None | Follow the chapter's "Handle with care" list. Leaving a fact off is never a reason to drop a limitation that changes how a result should be read |

## When two rules conflict

- Accuracy comes first, then being understood on the first read, then relevance, then
  persuasiveness, then length.
- If the clear version of a sentence is longer than the short version, use the clear version.
- A qualification that the reader needs stays next to its claim, even when the sentence gets
  longer.
- A reflection after a finding is included only when it says something the finding does not
  already say. A general lesson is stated with the scope it was observed in.
- Use an existing page as an example to imitate only if the owner has approved it. A newly written
  illustrative example is allowed when it is labelled as one.
