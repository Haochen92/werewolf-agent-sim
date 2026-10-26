# The day summary: build journey (May to October 2026)

> **What this is.** The chronological path from a free-text summary that had never been evaluated to
> today's design, where the model only transcribes and code checks. Later entries supersede earlier
> ones. A design that was falsified is shown where it happened, not edited away.
>
> **Companion docs.** The current design, stated destination-first: [`report.md`](report.md).
> This log condenses the folder's earlier `experiment_log.md` (the May series, with its raw notebook)
> and the October entries of
> [`../../gameplay/discussion_evidence.md`](../../gameplay/discussion_evidence.md)
> (§6.4–6.6, §8.4) and [`../../gameplay/deduction/experiment_log.md`](../../gameplay/deduction/experiment_log.md)
> (§3). The earlier versions of this folder's log and report are in git history at `2382b34c`. The commit messages quoted below are in git history.
>
> **A naming note.** The May prompts were numbered v1 to v4b. The October schemas restart at v3 and
> v4 in the code (`DaySummaryOutputV3`, `V4`). This log names each design by what it does.

---

## ① Motivation: the only window onto a past day

**2026-05-27.** At the end of each day's discussion, one model call condensed the day into a summary.
Seats never saw an earlier day's discussion again, only its summary. So every later decision about
a past day rested on this one call, and it had never been evaluated.

The first template was a reasonable starting point. It asked for four fixed sections: accusations,
defences, role reveals and alliances, in free text. Three things were unknown: whether it kept what
mattered, whether it attributed statements to the right players, and whether its omissions changed
later decisions.

## ② May: tuning the free-text summary with a judge

**2026-05-27 · a situation section and a quality judge.** The prompt was given the project's shared
standards for describing a game situation, and a "village dynamics" section (how informed the
village was, how aligned, who was driving). A hand comparison of 8 summary pairs showed the new
section adding that signal. To score at scale, a judge was built: Gemini 2.5 Pro read each transcript
and its summary and scored five dimensions from 1 to 5, over 18 transcript–summary pairs.

**Catches:** whether the judge can rank prompt versions. Its first run already showed the limit. The
village-dynamics score was 5.00 on every pair, because the prompt forced the section to exist and the
judge checked that it did. Completeness was lowest (4.56), with accusers and votes dropped in 5 of 18
pairs.

**2026-05-27 · the word-limit hypothesis, falsified.** The reading at the time was that the 400-word
limit forced the model to drop secondary accusers. *Catches:* whether length was the constraint.
Raised to 500 words, the model still wrote 130 to 230 words, and completeness did not move (4.44 to
4.39). The limit was reverted. The gaps were the model's choices of what to include, not a budget.

**2026-05-27 · "list all accusers", and the noise floor.** The prompt was told to keep votes cited as
evidence and to list every accuser in a pile-on. It fixed the two worst pairs and regressed others.
The finding was about the instrument: one pair's score moved by ±1 between runs of the same prompt,
so at 18 pairs with one run each, the differences being chased (−0.11, −0.22) were smaller than the
noise.

**2026-05-27 · structured output.** *Problem:* in free text the model chose what to include, and "list
every accuser" did not hold. *Change:* the summary became structured output, one entry per
accusation, role claim and alliance, with code rendering the text. Scores moved within noise
(completeness 4.44 to 4.50). *Decision:* keep structured output for architectural reasons, not
scores: a fixed format, forced enumeration, and fields later code can read. A follow-up added a
"confirmed by death reveal" tier after the model labelled a dead investigator's revealed role
"unverified".

**2026-05-27 · the model choice.** Four generation models were scored on the final prompt.
Gemini 2.5 Pro scored highest but took about 120 minutes for 18 pairs. *Catches:* the failures that
would mislead a later seat most, read by hand rather than averaged. Gemini 3.1 Flash-Lite at medium
thinking removed the two worst failures of its minimal setting, a fabricated game-master announcement
and a dropped primary accuser, at about 10 minutes. *Decision:* Flash-Lite with medium thinking.

At this point the summary had four sections, in prose, and seats read the rendered text.

## ③ October: the summary passes on a premise as fact

**2026-10-03 · game `46355b89`.** The owner played the serial killer. On day 3 a wolf argued from
something only the wolves knew (their attack on the serial killer had failed, which the game never
announces). Two villagers called it a fabricated case, and the wolf was voted out. On day 4 three town
players treated "player_2 survived multiple night attacks" as fact. They had not seen day 3's
discussion, only its summary:

> "Player_2 has survived night attacks and remained unharmed without claiming a healer, which these
> players argue points to serial killer night immunity."

The conclusion was attributed; the premise was stated as fact. Seats who rejected the claim while
reading the discussion accepted it from the summary.

**Design: every statement attributed, and the summary given the record** (code: `V3`). The summariser
was given the game master's record and the claims already on record. It wrote each statement as
something a named player said, recorded who disputed each accusation, checked each accusation
against the record (`record_check`), and gave each role claim a verdict (supported, contradicted,
unverified). The shared situation standards were removed from its prompt, because they told it never
to use player IDs, against its own rule to use them. Earlier days were now shown in labelled blocks:
the game master's exact record first.

*Verify, on the hallucination bench (89 frozen moments from nine-seat games, 3 samples each,
Gemini 3.5 Flash-Lite).* *Catches:* whether a more faithful summary reduces the seats' own errors.
Bad samples went from 36% to 31% of 267, with 24 cases better and 14 worse (p = 0.14). That is a
direction, not an established effect.

## ③ The summariser transcribes; code checks

**2026-10-04 · the attributed summary's own judgements were the problem.** Three things showed the
day after. Nearly every claim verdict was "unverified", and the claim record built from them dropped
the field. "Alliances" restated the accusations, and "village dynamics" retold the day as a story,
which is how the wolf's premise had entered as narration. And it was long: the healer's day-4 prompt
in `46355b89` spent 4,911 characters on previous days.

**Design: transcription plus a claim ledger** (code: `V4`, commit `2b24936c`). The summariser writes
two lists: accusations, and role claims with their night actions in fixed words (action, night,
target, a result from a fixed list). Alliances, village dynamics and the verdicts were removed. A
claim ledger, kept by code, folds every day's claims per player and checks each against engine facts
(revealed roles, announced saves and deaths, the cast). A check states the fact and stays silent
where the record fits more than one reading. The ledger is rebuilt for every prompt, never stored.
Seats read three blocks: the game master's record, the ledger, the accusations. The owner ruled that
the summariser gives no verdict of its own: "supported" was a subjective call.

*Verify, same bench.* *Catches:* whether removing the summariser's judgement costs fidelity. No change
in the seats' errors: 31% against 32%, 11 cases better and 11 worse. Messages may have got worse (17%
to 27% of checkable messages, p ≈ 0.13), mostly late-game votes misquoted. Across 104 re-summarised
days the summariser never failed. Its false flags that "investigations were never announced" (they
never are) went from 6 to 0, and stored summaries were 55% shorter. *Decision:* keep. The design cut
what seats read without changing what they got wrong.

**2026-10-04 · the bench's seats were not reasoning.** A probe found every game turn so far had run
with zero reasoning tokens. Turned on, bad samples fell from 31% to 10% on the same summaries. Every
comparison above ran without reasoning, so they say little about how the summary's design matters to
a model that reasons. They were not re-run.

**2026-10-04 · a plan is not an action** (commits `ace0cf6e`, `d78c0bb3`, `a3fb32fd`). *Problem:* a
decoy "I'll check player_2 tonight" was logged as a night-2 investigation. *Fix:* a claimed night
action is one the player says already happened; plans go in their own list, and the ledger sets them
beside what the player later says they did, as fact, never as a broken promise. A vague result is
recorded as `not_said`. Each written accusation field was capped at 30 words, after DeepSeek wrote a
median of 40 and up to 92.

## ③ The ten-seat game: what the summary got wrong

**2026-10-09 · the ten-seat game.** The cast grew to ten seats from twelve roles, with more night
actions to claim: watches, follows, sigils, blocks. A speaking seat also filled in a claim field for
the role it claimed, and the ledger took role claims from that field first, falling back on the
summary's transcription only when the field was empty.

**2026-10-10 · fifteen games read by hand.** *Catches:* what actually goes wrong, by kind, rather than
by count of fields. Over ten audited games (about 345 heard lines), summary errors were 22, the most
common error of any kind: omissions and distortions of plain claims. One decided a game (`e06`). The
investigator said "I was roleblocked last night, which confirms we have an active Chanteuse in play".
The summary wrote "player_2 claimed chanteuse — Night 1: blocked player_2". The speaker had set no
claim field, so the ledger's fallback took it. The investigator accepted the false premise about
itself the next day and was voted out 7 to 1. Separately, the record check copied its own example ("no
attack on player_2 was ever announced") against an announced death and against attacks on players who
cannot be killed at night.

*Fix* (commit `6248fc58`): the summariser is told that something done to a player is not their claim.
The ledger drops a claimed action that can only have been done to the speaker, and drops the claimed
role too only for a Chanteuse claim resting on a self-block. The record check's example was removed.

*Verify, by replay.* Each faulty summary was frozen as a case and replayed with exactly the inputs it
had in the game, five samples a case, scored on the structured fields and the ledger built from them.
*Catches:* whether each fix holds without new games. A first, broader ledger rule also lost a true
Vigilante, whose "held my fire" the summariser had written as shooting itself; the replay caught it,
and the rule was narrowed. The copied record-check line came back in 2 of 15 samples before the fix
and 0 of 15 after. The invented Chanteuse claim did not recur in 10 samples on either arm. It is rare,
so the ledger rule and a test are what guard it.

**2026-10-10 · keeping what was denied** (commit `0c605e89`). *Problem:* the summary had no field for
a denial. Every spoken denial in the later games had been dropped (30 of 30 replayed samples), one of
them the counter-evidence to the same player's claim the next day. *Fix:* a "did not act" night
action, an instruction to keep every rebuttal, and result words for what the record could not hold:
`no_visitors`, `no_effect`, `roleblocked`. *Verify:* Gemini 3.5 Flash-Lite then lost 7 of 30 denials,
Gemini 3.5 Flash none. A roleblock had been filed as a denial by GPT-6 Luna in 15 of 15 samples; after
the fix, 0 of 15.

**2026-10-10 · roles inferred from a described action** (commit `d066d1b3`). *Problem:* across 71
summarised days, the summariser never contradicted a claim field the speaker had set, and sixteen of
its own role claims were roles inferred from a described watch or follow. *Fix:* the speaker's claim
field now counts a role claimed by describing its action, so the speaker's own account takes the
place of the summariser's inference.

## ③ A stronger summariser, and the record check removed

**2026-10-16 · Claude Haiku 5.5 against Claude Sonnet 5.5.** The owner allowed Sonnet for the summary,
one call a day, if it judged better. *Catches:* whether a stronger model writes summaries with fewer
errors that would mislead a later seat. Every day with speech in two Haiku games (6 days) was
re-summarised five times per model, and Sonnet judged all 66 summaries against the transcript and the
record. A first judging was discarded: the judge had treated the moderator's closing line, which still
named accusers in an old wording, as the truth about who accused whom.

Both models wrote flawed summaries in 18 of 30. Sonnet made fewer bad record checks (6 against 20) and
more transcription errors (18 against 11). Every one of the 27 record checks written across all arms
was judged wrong; none reported a real conflict. *Decision:* the summary stays on the game's model.
The record check was removed (commit `d4f14fa7`). It had been added on 2026-10-03, when no code yet
checked claims; the ledger had done that since 2026-10-04.

## ③ The speaker's own account, and a rescue model

**2026-10-18 · the speaker fills in its claimed night actions** (commit `c957fdb5`). A speaking seat now
fills in the night actions its line claims, as well as the role. The ledger takes both from the
speaker first. The summary's transcription of claims became a cross-check, used for a player who
filled no field that day (a human, or a game from before the fields). The summary remains the source
of the accusations, the retractions and the plans.

**2026-10-21 · the summary gets a rescue model** (commits `cc4977ea`, `957d0b2e`). *Problem:* a stalled
provider could hold a request for a long time before failing. Outside Gemini, a client waited up to
600 seconds a try, with up to three tries, before anything else was tried. *Fix:* the summary waits up to 90 seconds, does not retry
a stall on the same model, and goes to the game's rescue model, a different model assigned to the
game. While the primary keeps stalling, later summaries start on the rescue model. The raw transcript
remains the last resort. Deployed the same day.

## ④ Remaining questions

- Whether seats reason better from the raw earlier transcripts than from the summary. No comparison
  has been run.
- The summary's error rate on today's prompt and today's default model. The counts above come from
  replayed cases and small samples.
- The May judge still exists in code but scores sections the summary no longer writes. No judge has
  replaced it; the October checks were field-level replays and one Sonnet-judged comparison.

---

**Sources.** [`experiment_log.md`](experiment_log.md) §0–7 and Appendix A (May) · this folder's
`eval_summary*.txt`, `eval_results*.jsonl`, `regen_comparison.json`, `prompt_versions/` ·
discussion_evidence.md §6.4 (game `46355b89`), §6.5 (attributed summary on the bench), §6.6 (transcription
and the ledger), §6.7 (reasoning), §8.4 (the ten-seat audit and replays) ·
`../../gameplay/data/phase3_reads/README.md` · `../../gameplay/data/phase3_summary_replay/README.md` ·
`../../gameplay/deduction/experiment_log.md` §3 and `data/haiku_summary_compare/` · the change history in
`Agents/prompts/extraction/day_summary.py` · commits `c9dbc79b`, `2b24936c`, `ace0cf6e`, `d78c0bb3`,
`a3fb32fd`, `6248fc58`, `0c605e89`, `d066d1b3`, `d4f14fa7`, `c957fdb5`, `cc4977ea`, `957d0b2e`.
