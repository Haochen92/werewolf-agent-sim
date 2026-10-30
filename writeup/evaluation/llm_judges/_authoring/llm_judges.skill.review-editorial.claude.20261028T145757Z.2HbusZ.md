<!-- editorial review of writeup/evaluation/llm_judges/llm_judges.skill.md by claude (claude-opus-5-5), 2026-10-28T14:57Z -->

## 1. The argument as I understood it

The page asks when an LLM judge can be trusted, and which judges in this project can be trusted today. Its answer is that trustworthy judges ask one narrow question, are given the facts they need, and are checked against labels they never saw. Broad 1–5 quality rubrics only work as "smoke alarms": they catch gross faults but cannot rank close versions.

The sections build the case in this order:
- when to use a model as judge at all;
- the failure of the 1–5 rubrics;
- the narrow judges that worked (the census reader and the expectation judge);
- how a judge is checked;
- the in-game classifiers, where a verdict changes what players see.

It ends by saying that every judge the current game relies on is provisional until a person's check, already prepared, is done. I could state the central answer. What I had to piece together myself was the setting: what the game is, and which "game" each result comes from.

## 2. Findings

**1.**
- **Where:** Intro: "judges graded the summaries players read about earlier days and checked players' statements against the game record."
- **Kind:** missing connection
- **What broke:** The page never says what the game is: its sides, its day/night cycle, or that the players are LLM agents. After that, "village", "claimed roles", "sentinel", "investigator", "game master", "given the floor", "open floor", "first round" and "a reply owed to a player who named the speaker" all arrive unexplained. A reader who doesn't know Werewolf/Mafia can't follow the rubric excerpt, the sentinel example or the echo gate's exemptions.
- **Repair:** Before the first judge appears, add two or three sentences on the game: LLM agents (and sometimes humans) playing a hidden-role deduction game, the day/night cycle, the two sides, and how speaking turns work.
- **Severity:** blocking

**2.**
- **Where:** Intro: "The judges and in-game classifiers used today have been checked only against other models". Later, under "Checking a judge": "Those checks were made on the earlier nine-player game, with earlier judge models".
- **Kind:** unit or term changes meaning
- **What broke:** The intro reads as "no judge has a person's check". Two sections later, I read 90 messages by hand and saw a precision of 0.8. These only fit together once you notice the "earlier game" versus "current game" split. That split is never introduced: it first appears as "the earlier game's factual-error test set", and later a "ten-player case" turns up. I couldn't tell whether "game" means a single match, a ruleset version or the codebase.
- **Repair:** In the intro, define the earlier game and the current game and what changed between them. Then say which checks belong to which.
- **Severity:** blocking

**3.**
- **Where:** "What is established": "Across the project, the judges that held up asked a narrow question against facts they were handed"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** Only the census reader has a check on this page, and that check was on the earlier game. The expectation judge counts as one that "held up", but the only evidence given for it is one anecdote, plus a case where its written expectation was wrong. Never in the body does the page define what "held up" means. So one judge is standing in for a general rule.
- **Repair:** Define "held up" (for example, agreed with a person's labels at a stated rate). Say which judges meet that definition, and report the expectation judge's check or state that it has none.
- **Severity:** worth fixing

**4.**
- **Where:** "When a model should judge": "The judges in the next section met the first two conditions but not the third."
- **Kind:** missing connection
- **What broke:** The third condition is "its answers can be checked". The next section's diagnosis is something else: scores stuck at the ceiling and run-to-run noise. It even says the dimensions checked "against the transcript" worked. A later section says that inputs handed to the judge are not a check, so I had to work out alone that this is why those judges fail condition three.
- **Repair:** In the next section, state which outside check was missing and how that differs from the ceiling and noise problems. Or rewrite the bridge sentence to name the actual failure.
- **Severity:** worth fixing

**5.**
- **Where:** "Quality scores that could not rank versions": "one pair's score moved by a full point between two runs of the same prompt."
- **Kind:** unit or term changes meaning
- **What broke:** The noise is measured on one pair, but the version differences in the table (0.05–0.06) are means over 18 pairs. A one-point swing on one pair shifts an 18-pair mean by about 0.06. The comparison may still hold, but the units don't match, so I couldn't judge it myself.
- **Repair:** Give the run-to-run change in the mean score (the unit the table uses), or say explicitly that one pair's swing moves the mean by about as much as the differences between versions.
- **Severity:** worth fixing

**6.**
- **Where:** Table row 3, "Highest for the slowest model, about 120 minutes for 18 pairs". Later: "The stronger model was still no better, with 18 of 30 summaries flawed on each"
- **Kind:** missing connection
- **What broke:** Two comparisons of which model should write the summary appear in different sections, on different set sizes (18 pairs and 30 summaries) and with different results. One prefers a faster model at a higher thinking setting; the other keeps "the cheaper model". I couldn't tell whether this is one decision or two, or whether "cheaper" is the same model as "faster". "Flawed" has no stated criterion. The table cell gives a time where the column promises a score, and it doesn't say which model was chosen.
- **Repair:** Say whether these are the same decision, name the model that was kept, and define "flawed".
- **Severity:** worth fixing

**7.**
- **Where:** "Narrow questions": "the sentinel, who watches one player at night and sees who visits them, saw player_10 visit"
- **Kind:** term before introduction
- **What broke:** To see why the watch can't support the claim, you need to know that several roles visit at night, and that a rival also claimed to be investigator. Neither is stated. "A rival's counter-claim" arrives without warning, so the expectation's logic is hard to follow.
- **Repair:** Before the expectation, add one clause saying that a visit is consistent with several roles and that two players claimed to be investigator.
- **Severity:** worth fixing

**8.**
- **Where:** "Narrow questions": "It still settled nothing. That design was decided by a set of labelled retrieval cases"
- **Kind:** section order
- **What broke:** The reason the pairwise judge settled nothing (generation and judging ran in one pass) comes after a sentence about how the decision was actually made. "Memory-search queries" are also not introduced: I don't know who writes them or what they retrieve.
- **Repair:** Give the reason directly after "settled nothing", then say what decided it instead. Add one clause on what memory search is.
- **Severity:** worth fixing

**9.**
- **Where:** "Checking a judge": "I read all 90 public messages it flagged, of which 68 were genuine errors." Also: "a sample of 15 rejected statements contained two or three errors it had missed"
- **Kind:** unit or term changes meaning
- **What broke:** Within three sentences the unit moves from public messages to private notes to statements. "Private notes" are never introduced. "Rejected" doesn't say by which stage, the cheap model or the strong one. "Two or three" leaves me unsure whether the labelling was ambiguous. A precision of 68/90 is also not stated alongside the "about 0.8" for private notes.
- **Repair:** Name the unit for each check, say which stage did the rejecting, and give both precisions in the same form.
- **Severity:** worth fixing

**10.**
- **Where:** "When the verdict acts": "A human player's line is never held"
- **Kind:** term before introduction
- **What broke:** This is the first sign that humans play too. It changes what the live classifiers are for, and how much a held line costs.
- **Repair:** Mention human players when the game is introduced.
- **Severity:** worth fixing

**11.**
- **Where:** "What is established": "the tags each speaker writes for whom it accused, which decide who must reply"
- **Kind:** term before introduction
- **What broke:** A third component that needs checking (self-written accusation tags that control who must reply) first appears in the closing section. I can't tell whether it is a judge, a classifier or player output.
- **Repair:** Introduce the tags in the live-game section, or drop them from the summary.
- **Severity:** worth fixing

**12.**
- **Where:** "Quality scores…": "One applied a certainty rule meant only for advice notes to factual observations as well"
- **Kind:** detail that does not change understanding
- **What broke:** Memory notes, advice notes, factual observations and "the field memory search uses" are all undefined. The deltas (1.19, 0.69) don't say which score moved. The paragraph's point, that a judge was being debugged rather than validated, survives without these details.
- **Repair:** Keep the point and the 4.00 clustering. Either cut the two bug specifics or define memory notes first.
- **Severity:** worth fixing

**13.**
- **Where:** Throughout: "screen for factual errors", "census reader", "factual-error judge(s)". Also "game-master announcement" versus "moderator's closing line", and in the Evidence list, "extraction judge: the two 1–5 rubric judges".
- **Kind:** unit or term changes meaning
- **What broke:**
  - It's unclear whether "factual-error judges" (plural) means the two-stage census reader, or the census reader plus the expectation judge.
  - Game master and moderator may or may not be the same role.
  - The body describes a memory-notes judge as the second 1–5 judge, but the evidence list calls it the "extraction judge".
- **Repair:** Use one name per component and say once how the names relate.
- **Severity:** worth fixing

**14.**
- **Where:** "Narrow questions": "Neither is given a model answer to compare against."
- **Kind:** unit or term changes meaning
- **What broke:** On a page where "model" always means an LLM, "model answer" first reads as "an LLM's answer" rather than "a reference answer".
- **Repair:** Say "reference answer".
- **Severity:** taste

## 3. Highest-impact improvements

1. Add a short setup before the first judge: what the game is, its roles and turn structure, that the players are LLM agents (plus humans), and the difference between the earlier and current game.
2. Fix the evidence trail behind the thesis. Define "held up", state which judges have a person's check and on which game, and match the intro's caveat to that list.
3. Keep units steady in the evidence: give rubric noise in the same unit as the version differences, and name the unit for each census-reader check.
