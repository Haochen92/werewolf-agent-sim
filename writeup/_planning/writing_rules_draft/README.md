> **2026-11-17: adopted.** `core_rules.md` moved to `docs/writing/core_rules.md`, and `voice.plain.md` replaced
> `.agents/skills/write-portfolio-page/references/voice.md`. What remains here is the record of how they were made.

# Writing rules: short draft (2026-11-17)

Nothing existing was changed. This folder holds four new draft files only; the style guide, the
write-report skill and the portfolio skill are untouched.

## The files

- `core_rules.md` is one page of 13 rules that a writer keeps in mind while drafting any document in
  this repository, with five before → after pairs quoted from the existing guides and three
  tie-break rules. It is about 900 words, over the 700 asked for (see decision 2).
- `voice.plain.md` is `.agents/skills/write-portfolio-page/references/voice.md` reworded into plain
  sentences, with the same rules, numbers and owner quotations. Four places are marked `[unclear: …]`.
- `coverage.md` lists 398 rules and requirements from the twelve guide and skill files, each marked
  as in `core_rules.md`, reference only, a duplicate, in conflict, or proposed for removal. The ten
  conflicts and three removals come first.

## How I chose the core rules

I kept a rule if it applies to every document type and if breaking it has made a document hard to
read or wrong. I ordered them by how often the files record that kind of failure. "Read this first"
and the anti-pattern list both call dense, compressed prose the most common failure, so the
sentence-level rules come first. Claim strength comes fourth, because the style guide calls small-sample
over-claiming the project's most likely way to be wrong. Rules for one document type or one workflow
step stay in the long files.

## The five decisions I was least sure of

1. **Readability above accuracy in the order.** A wrong claim may do more harm than a hard sentence.
   If the owner weighs it that way, rule 4 should move to the top.
2. **Length.** After the fresh reader's review, rewording made the page longer, from about 750 to
   about 900 words. I kept the clearer version, following the tie-break rule, rather than cut back.
3. **Example choice.** Rule 4's pair was first the caching example from the style guide. The fresh
   reader pointed out that it uses an internal name ("tell detector") without explaining it, which
   breaks rule 5, so I replaced it with "three in four" → "three of four observed errors" from the
   Level 2 prompt. Rule 3 has no pair, and rule 5's pair needed an explanatory sentence.
4. **What counts as a conflict.** K3 ("show the path" against "do not retell the investigation") and
   K9 ("explain our system, not the field" against "explain standard terms") may be meant for
   different document types rather than in conflict. I listed them as conflicts because the files do
   not say so.
5. **Additions in `voice.plain.md`.** To make the rules usable without other files, I added a short
   paragraph defining Level 2, Level 3 and "source notes", and short glosses (fan-out, nominalisation,
   defensive negation, trade-off jargon). These explain terms; they add no rule. The gloss for
   trade-off jargon is my reading of the owner's example.

## Fresh-reader check

One subagent with no context read the text of `core_rules.md` and `voice.plain.md`. It listed 48
sentences it had to read twice (19 in `core_rules.md`, 29 in `voice.plain.md`), 49 words or phrases
used in a non-literal sense, and 22 rules it could not apply without guessing. I reworded every
listed sentence except the owner's quotations and the quoted "before" examples. The main changes:

- `core_rules.md`: a new heading (the rules whose breach did the most harm come first); "what
  follows" became "what result the action has"; one sentence of context for the prompt-injection
  pair; "one question in each paragraph" became "one question to answer"; the "direction of an
  effect" became "which way an effect goes"; "isolated" became "a controlled test ruled out the other
  explanations"; the rule 4 and rule 5 pairs were replaced or explained; the sample size is now
  stated to be part of the result, not a repeated caveat; "validated" is defined; the fresh reader is
  named as a person or a model; and a line says what to do when this page and a long guide disagree.
- `voice.plain.md`: rule 1 now says "open with a sentence that says what the subject is"; rule 11's
  long heading was split into separate sentences; rule 12 now says that prose explaining why cannot be
  replaced by a figure; rule 14 now reads "do not present an observed pattern as if its cause were
  known"; "tests of the rules" became "tests of the game's rules in code"; the habits list became one
  item per habit with a gloss; the checking advice now says it is addressed to whoever checks a page;
  "never invent a number or change one without saying so" became two sentences; and "held spend" is
  now marked unclear.

Some of the reader's points remain open because they need the owner: the four `[unclear]` markers,
which chapter's "Handle with care" list applies to a page outside any chapter, and how small a sample
must be before only its direction can be claimed.

## Recommended next step

Point both skills (`write-report` and `write-portfolio-page`) at `core_rules.md` first and treat the
long files as reference for their document type or step. Before that, rule on the ten conflicts in
`coverage.md` and the three proposed removals, and settle the four `[unclear]` items in
`voice.plain.md`. Then try the short page on one report and one portfolio page, and run the fresh-reader
check on both results.
