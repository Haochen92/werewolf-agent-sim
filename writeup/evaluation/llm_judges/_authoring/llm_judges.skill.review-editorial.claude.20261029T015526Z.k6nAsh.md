<!-- editorial review of writeup/evaluation/llm_judges/llm_judges.skill.md by claude (claude-opus-5-5), 2026-10-29T01:55Z -->

## 1. The argument as I understood it

The page asks what made some LLM judges in this project trustworthy and others not, and how far any of them has been validated. Its answer is that broad 1–5 quality rubrics acted only as "smoke alarms". They caught gross faults, but their scores either never moved or moved less than run-to-run noise, so they could not rank versions. The judges that held up asked narrow yes/no questions and were given the facts they needed to answer. The page then argues that handing a judge facts does not check it. A check compares its verdicts with labels it never saw. The best such check here, for the census reader, is partial, not blind, and comes from the older nine-player game. The in-game classifiers also have to fail safe, and they have only been checked against model readers. It ends by saying the current game's judges remain unvalidated until the prepared human review packets are labelled.

## 2. Findings

**1.**
- **Where:** "Checking a judge against something it never sees", quote: "every verdict on the current game's cases was read."
- **Kind:** caveat reverses an earlier claim
- **What broke:** The opening says that on the current game "no judge has yet been checked against a person's labels". The closing section says the factual-error judges' check "comes from the earlier game". Here, though, a person read every verdict on the current game's cases. I could not tell whether one judge has in fact been checked by a person on the current game. If it has, the opening and closing are wrong. If it hasn't, the reason is only implied ("does not give an agreement rate"). The page also gives no outcome for that current-game reading.
- **Repair:** Say explicitly that reading verdicts case by case is a weaker kind of person check than blind labelling. Say which judge this reading covered, report what it found, and make the opening and closing use the same wording.
- **Severity:** blocking

**2.**
- **Where:** same section, quote: "Test-case verdicts are read by hand too: on the earlier game's test set, 10 of 12"
- **Kind:** missing connection
- **What broke:** "Test-case verdicts" is not linked to a named judge. I had to work out that this means the expectation judge from the previous section. Because the paragraph begins "The census reader has the fullest check", I first read these numbers as more census-reader evidence.
- **Repair:** Name the expectation judge at the start of this sentence, and ideally give it its own short paragraph.
- **Severity:** worth fixing

**3.**
- **Where:** opening, quote: "Three distinctions explain the difference, and the sections below take them in turn."
- **Kind:** missing connection
- **What broke:** The opening promises three distinctions that explain why narrow judges worked and broad rubrics did not. The third one (live verdicts must fail safe) has nothing to do with that difference. The second one (facts handed over are not a check) is about how to validate a judge, not why narrow ones worked. The actual reason, narrow questions with facts supplied, is the heading of section 2 but is not one of the three distinctions. So the opening does not state the page's central answer.
- **Repair:** State the central answer first: narrow questions with facts supplied, checked against independent labels. Then present the live-game requirement as a further condition, not an explanation of the narrow/broad difference.
- **Severity:** worth fixing

**4.**
- **Where:** "When the verdict acts", quote: "the gate never judges a reply owed to a player who named the speaker."
- **Kind:** term before introduction
- **What broke:** The reader hasn't been told that players can be obliged to reply, or how. The mechanism (labels players attach to say whom they accuse, which decide who must reply) only appears in the last section, where it is suddenly listed as a subject of the review packets. In both places the reader doesn't know what it is or why it belongs on a page about judges.
- **Repair:** Introduce the accusation labels and the reply obligation in section 4, and say whether a model produces them and so needs checking. Then the closing list can refer back to them.
- **Severity:** worth fixing

**5.**
- **Where:** "Narrow questions, with the facts handed over", quote: "such as a check the player never made."
- **Kind:** unit or term changes meaning
- **What broke:** On this page "check" almost always means validating a judge. Here it suddenly means an in-game action, a role investigating a player. Neither the page nor the excerpt explains that action, so I first read it as a validation check.
- **Repair:** Use a game-specific phrase, such as "a role check the player's role never performed", or gloss it once.
- **Severity:** worth fixing

**6.**
- **Where:** "Checking a judge…", quote: "moved the count of bad samples by only one or two"
- **Kind:** number before orientation
- **What broke:** I don't know how large the test set is, what a "sample" is (a reply? a turn?), or what "bad" means. So "one or two" can't be read as a noise floor, and "only larger differences meant anything" has no scale. This sentence also sits inside a paragraph that otherwise describes the ideal procedure, so it mixes prescription and result.
- **Repair:** Give the set size and the unit, and move the result out of the procedure paragraph.
- **Severity:** worth fixing

**7.**
- **Where:** "Checking a judge…", quote: "I read all 90 public messages it flagged: 68 were genuine errors."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** All the figures measure precision, or misses by the second stage. Nothing measures errors in statements the cheap first stage never flagged. The closing defines "held up" as "most of their verdicts stood", which only covers flagged items. A reader could take "the fullest check" to cover missed errors too. In addition, "A 23-case labelled set chose its two-stage design" gives no result, and "two or three" leaves open why the count is uncertain.
- **Repair:** State that misses among never-flagged statements were not measured. Say in one clause what the 23-case set showed. Explain the "two or three".
- **Severity:** worth fixing

**8.**
- **Where:** "Quality scores that could not rank versions", quote: "Two early decisions did rest on 1–5 judges of this kind, both on few games"
- **Kind:** caveat reverses an earlier claim / unit or term changes meaning
- **What broke:** The unit changes from transcript–summary pairs to "games" without explanation. The next sentence says "None of the project's current results rests on them". If the memory-note model chosen this way is still in use, then a current design rests on them. I couldn't tell whether those decisions still stand. "Memory notes" is also new here.
- **Repair:** Say whether those two choices are still in effect. Gloss memory notes briefly, or link them to "a player's private note to itself" in the next section, if that is the same thing.
- **Severity:** worth fixing

**9.**
- **Where:** same section, quote: "its later structured output required an evidence label on every accusation."
- **Kind:** term before introduction
- **What broke:** Structured output is only explained further down, in the table ("one entry per accusation and role claim, rendered by code"). Here, "later" is unclear: later in time, or later in the pipeline?
- **Repair:** Add one clause, such as "a later version that emitted one entry per accusation".
- **Severity:** taste

**10.**
- **Where:** same section, table row 3, quote: "Highest overall for the slowest model"
- **Kind:** term before introduction
- **What broke:** "Overall" is not defined (a mean of the five dimensions?). There's also no number, unlike the other rows, so I can't see how big the lead was.
- **Repair:** Define "overall" and give the score difference.
- **Severity:** taste

**11.**
- **Where:** "When the verdict acts", quote: "Four model readers labelled 65 lines of the gate's kind"
- **Kind:** missing connection
- **What broke:** I don't know how four readers' labels were combined into "the lines they called restatements" (majority? unanimous?). That affects how much the 10/29 and 0/36 figures mean.
- **Repair:** State the aggregation rule in one clause.
- **Severity:** taste

**12.**
- **Where:** "Narrow questions…", quote: "read the same situation and certainty rules as the models that wrote the notes"
- **Kind:** term before introduction
- **What broke:** "Situation and certainty rules" sounds like an internal name and is never explained. The point about the judge and the writer sharing one source of rules still comes through, but this example is opaque.
- **Repair:** Gloss it, e.g. "the rules for what a note may state as certain".
- **Severity:** taste

## 3. Highest-impact improvements

1. Make the opening, section 3 and the closing agree on whether any person has checked a judge on the current game, and name the expectation judge where its hand-read verdicts are reported.
2. Rewrite the opening so it states the central answer (narrow questions with supplied facts, checked against independent labels) instead of three distinctions that don't all explain the narrow/broad difference.
3. Introduce the accusation labels and reply obligation before section 4 relies on them, and give units and set sizes for the noise-floor and census-reader figures, including that misses among never-flagged statements were not measured.
