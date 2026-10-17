# Reasoning and hallucination failures: case register and experiments

This log is where reasoning and hallucination failures seen in served games are taken seriously. Each
failure is entered as a case, frozen from the game's own checkpoints as a replay case where possible,
and tested. The register below is the index; the sections after it are the experiments, in the order
they were run. A later section can revise an earlier one; earlier sections are left as they were.

Companions: the population census of hallucinations (`evidence/evaluation/hallucination_bench/`), and
the first Haiku 5.5 game's failures (`evidence/game_play_enhancement/discussion_evidence.md` §8.6–8.7),
whose frozen cases are reused here. Data is in `data/`; code and configs are listed in the sources
footer.

## The levers

Four tools have been used against these failures so far. Each experiment below says which one it tests.

| Lever | What it changes | Where tested |
|---|---|---|
| Thinking budget | how long the model reasons before answering | §2 |
| Prompt editing | the wording a seat reads | §8.6–8.7 of discussion_evidence.md; §5–6 |
| Deterministic injection | facts, or certain conclusions, written by code instead of left to the model | §1 (the closing line), §4 |
| A stronger model | Sonnet 5.5 instead of Haiku 5.5 | §3 (summaries only) |

Two more were weighed and not taken. Tool use (a seat calling code for facts on request) was rejected by
the owner: the facts are deterministic and already injected, so a tool adds a round trip per turn and no
information. Majority voting over several samples was checked for free on §2's samples: a majority of
three low-effort votes was right as often as one (39% against 41% of cases), because the errors repeat
across samples. The model holds the same wrong belief each time it reads the same context.

## Case register

| ID | Game, turn | What happened | Status |
|---|---|---|---|
| R1 | 2f19d908 day 2, healer (seat 8) | Roleblocked on night 1; the trailseer saw player_7 visit it and player_7 admitted it. The healer wrote every premise in its notes and passed three times, never naming player_7 as the Chanteuse | Two causes found (§4–5): the missing first step (injection fixes it) and its own carried-forward "stay quiet" note |
| R2 | 2f19d908 day 3, the moderator's closing line | "player_8 has been accused by player_2, player_5 and player_4": one accuser had withdrawn ("player_8's visit checks out"), one had asked a question. The investigator's vote cited "accused by three players" | Fixed in code (§1) |
| R3 | 2f19d908 day 3 votes | The investigator voted out the healer who had protected it; on replay most town voters also voted a claimant whose claim was consistent with the others' | §2 |
| R4 | Day summaries, both Haiku games | `record_check` (meant only for a conflict with the record) written to confirm facts or back an argument | §3 |
| R5 | Day summaries, both Haiku games | An accusation the accuser later withdrew kept as standing | §3 |
| R6 | 2f19d908 day 3, sigilist (seat 4) | Listed the healer among the "unclaimed" after it called its visit protection; argued a protection on a roleblocked player was pointless | Did not reproduce (0 of 10, §2) |
| R7 | 2f19d908 day 3, healer | "I'm not voting player_8" (itself) | 1 of 10 on replay (§2) |
| R8 | 2f19d908 day 2, trailseer | Called the healer "worth watching" because a wolf had visited it | Not reproduced: the trailseer passed in all 10 replays |
| — | 403f4dbc | Visits read the wrong way round; the real sentinel voted out as "unverified"; an uncontested bluff believed | discussion_evidence.md §8.6–8.7 |
| R9 | 645228e7 day 3 votes | The town voted out the real investigator 6–1. It stated its Suspicious check on player_3 (a wolf) four times; no one counterclaimed. The trailseer's, healer's and vigilante's notes read "attacked by the serial killer and saved by the healer" as "player_3 is likely town", and the serial killer pushed "a wolf framing a just-saved player" | Open (§7): the save line and the investigator conditional, both for the deduction block |
| R10 | 645228e7 day 3, illusionist (player_3) | "I'm not the investigator" in three of its four messages, denying a claim no one had put to it | Cause not confirmed (§7) |
| R11 | 645228e7 day 3, several seats | Rule sentences recited as arguments: "a follow only shows where someone went" (two seats, nearly word for word), "a check is a claim, not a fact", "unverified" | Open (§7): an audit of quotable hedges |
| R12 | 645228e7 days 1, 2 and 4 | No speech at all. Day 2: every seat passed both rounds after two deaths. Day 4: all four passed, including the vigilante whose shot had killed the illusionist; it never claimed and was voted out | Open (§7): for the owner to rule |
| R13 | 645228e7 nights 1–3, the wolf chat (a human chanteuse, the AI illusionist) | The AI never answered the human's questions ("who to block", "Do I block 3"), agreed with a proposal no one made, sent near-identical messages in all three rounds, cited a "day 2 push" that never happened, and narrated its own plan | Owner: earlier games were better, probably the model; no prompt change for now |
| R14 | 645228e7 day 3, the moderator's closing line | "player_8 has been accused by player_3 and player_9": player_3 was the wolf player_8 had accused | R2's bug: the game ran on the server deployed 2026-10-15, before the fix |

---

## §1 The game: 2f19d908 (2026-10-14)

The first memory-on game on the ten-seat cast, Haiku 5.5 in every seat at thinking `low`, the live
setting. Town won on day 3, voting out the serial killer 4–2. The owner flagged the healer's day 3: it
said it protected the investigator, other town seats said it had no claim, and town seats voted for it
after it claimed healer with no counterclaim and the sentinel had reported seeing its visit.

Read against the events and the agents' private notes, the day breaks down as follows:

- **One error came from our code (R2).** The moderator's line before the vote named the accusers from the
  accusation tags each speaker puts on its own message, counted over the whole day. A later message
  never cancels an earlier tag, and a tag can be wrong. The investigator's final read of the healer said
  "they were accused by three players": three, counting itself and the sentinel who had withdrawn. The
  fix, ruled by the owner on 2026-10-16, names only who speaks ("Before the vote: player_8 gets a last
  word."). Who accused whom is in the transcript.
- **The rest was model reasoning.** The sigilist's own read shows it heard "it was protection" and
  still listed the healer as unclaimed (R6). The investigator read player_7's night-1 visit to the healer
  as a point against the healer, though player_7 had since been revealed as the Chanteuse, so the visit
  was a wolf's block on it (R3). The healer itself held back the one fact that would have exposed
  player_7 on day 2 (R1).

## §2 Thinking budget: Haiku at `low` against `medium`

**Question.** Is Haiku's reasoning short of thinking time? Sonnet is ruled out for player turns on cost
(about $2.30 a game against $0.12), so effort is the cheapest lever left.

**Setup.** The frozen cases of 403f4dbc (18 discussion turns, 11 votes) plus 2f19d908's (5 turns: R6,
R7, R8 and two controls; 5 day-3 votes), all from the game checkpoints. The 2f19d908 votes are frozen
twice, with the closing line as played and as the engine writes it now, so the run also measures R2's
fix. Both arms run the current code, memory off; votes 10 samples a case, turns 5. A vote is scored by
its target, an exact match on a structured field. Discussion turns, and the facts in a vote's notes, are
judged by Claude Sonnet 5.5 against hand-written expectations, in one Message Batch.

**What "right" means for a vote.** "Right" is the vote landing on an actual evil player. It is an outcome
measure, not a judgment of the vote: with hidden information a sound vote can land on town, and a rate of
100% is neither expected nor wanted. The cases were chosen where the evidence pointed one way, which
narrows that gap without closing it. For 2f19d908 day 3 the evidence defines a better measure. Four
living players had claims consistent with each other and two had none, so a vote fits the evidence if it
goes to one of the two unclaimed players or abstains.

**Votes: medium was much better.**

| Votes | Low | Medium |
|---|---|---|
| All 16 cases as played, right | 65/160 (41%) | 98/160 (61%) |
| 403f4dbc controls (right in the game), right | 43/70 | 64/70 |
| 403f4dbc day 4 controls, right | 9/30 | 28/30 |
| 2f19d908 day 3, fits the evidence | 17/50 | 29/50 |
| 2f19d908 day 3 with today's closing line, fits the evidence | 17/50 | 32/50 |
| Output tokens per vote | 852 | 2,317 |

Medium did better on 12 of the 16 cases and worse on 1 (sign test p = 0.003). Three things stand out.

- **2f19d908's town win was luck.** Replayed at low, the sigilist voted for the healer 10 times in 10,
  the sentinel 4 in 10, and the healer itself voted for the sigilist 9 in 10. At medium every one of them
  moves toward the unclaimed players.
- **The §8.7 lead looks like an effort effect.** §8.7 found 403f4dbc's day-4 votes falling across a
  prompt-layout change and suspected the layout. Here the same votes go from 9/30 at low to 28/30 at
  medium on one layout.
- **R2's fix does not move votes.** With the new closing line the investigator was right 1/10 at low and
  3/10 at medium, against 3/10 and 4/10 with the old one. The fix is kept because it removes a wrong
  statement from the moderator's voice, not for an effect on votes.

The judge's fact checks on the votes' notes moved less: 50% of samples had an error at low, 46% at medium
(11 cases better, 5 worse, p = 0.21). Medium lands the vote more often without making the written
reasoning clean.

**Discussion turns: no change.** 49/115 samples bad at low, 47/115 at medium (6 cases better, 5 worse).
Output rose 1.8× and turns took 11.2 s against 6.7 s. Of 2f19d908's discussion slips, R6 did not
reproduce in 10 samples, R7 came back once in 10, and R8's trailseer passed in all 10. They were one-off
draws; the wrong votes recur.

**Decision (pending).** Medium is the strongest single lever measured, and it acts on votes. At about 2.7×
the output on votes, a game would cost roughly $0.23 instead of $0.12. Moving the house setting to
medium for votes only is the next decision for the owner.

## §3 The day summary on Sonnet

**Question.** The owner allowed Sonnet for the day summary (one call a day) if it judges better. The
summary is the only account of a past day that seats read, so its errors carry forward.

**Setup.** Every day with a spoken line in the two games (6 days) re-summarised from its own checkpoint,
5 times per model, at the live thinking level (`medium`). The 6 summaries the games actually used are a
third arm. Each summary is judged by Sonnet against that day's transcript and the moderator's record, for
errors that would mislead a later reader (misattributed, invented, a claim missed, a rebuttal dropped or a
withdrawn accusation kept, a claim written as fact, a wrong `record_check`).

**A flaw in the first judging.** The first judge saw the moderator's closing line, which still named
accusers in the old wording, and took it as the truth about who accused whom. It flagged correct accuser
lists as wrong. The summariser never sees moderator lines, so the judge was rerun without them; only the
second run is reported. The first run's verdicts are kept beside it.

**Result: Sonnet is not better.**

| | Live (as played) | Haiku | Sonnet |
|---|---|---|---|
| Summaries flawed | 3/6 | 18/30 | 18/30 |
| Errors | 3 | 32 | 25 |
| of which `record_check` | 1 | 20 | 6 |
| of which transcription (misattributed, invented, missed, dropped) | 2 | 11 | 18 |

Sonnet writes fewer bad `record_check`s and more transcription errors. Its most repeated error: on
2f19d908 day 2 it recorded player_7's "I went to player_8, and I'm not claiming a role" as a claimed night
action in 4 of 5 summaries. Both models kept the sentinel's withdrawn accusation of the healer as
standing (R5).

**`record_check` is wrong whenever it is written.** Across all arms 27 `record_check`s were non-empty, and
the judge found all 27 wrong: 20 from Haiku, 6 from Sonnet, 1 live (R4, 2f19d908 day 3, "consistent with
the nothing-to-protect premise"). None reported a real conflict. The claim ledger already checks claims
against the record in code (`Agents/rules/claim_ledger.py`).

**Decision.** The summary stays on Haiku. `record_check` was removed on 2026-10-16 (owner): the summary no
longer writes it, and seats no longer see it from older summaries. It had been added on 2026-10-03, when the
summary became the only account of a past day the seats read and no code yet checked claims; a day later the
claim ledger took over checking claims in code, and `record_check` stayed on for accusations.

## §4 R1: injecting the roleblock's certain consequence

**The failure.** On night 1 the healer tried to protect the investigator and was roleblocked. On day 2
the trailseer said it had followed player_7 to player_8, and player_7 admitted the visit and refused to
claim a role. In this cast only the Chanteuse, a wolf, can roleblock, and blocking is a visit. The healer
had every premise. Its notes set them side by side three times ("player_7 visited me, which is consistent
with player_3's follow") and drew no conclusion. It passed all three turns of day 2. It reached "likely
the chanteuse" only in a private note on night 2, and never said it.

**The design.** The first step of the deduction needs no reasoning: a roleblocked player was visited by
the Chanteuse. The engine knows this from the rules and the cast. The healer's night record said instead
"You were roleblocked: your action was not carried out and you learned nothing tonight." The last clause
is false and works against the deduction. The injected line replaces it with what is certain, naming no
player and revealing no seat's role:

> You were roleblocked: your action was not carried out. Only the Chanteuse can roleblock in this game,
> and blocking is a visit, so the Chanteuse, a wolf, visited you that night.

This tests the owner's principle for the deterministic-injection lever: hand a seat any conclusion that
is certain from public rules and its own private result, instead of relying on it to deduce. The
remaining step is left to the model, and it is a suspicion, not a deduction. "The Chanteuse visited me"
and "the trailseer says player_7 visited me, and player_7 agrees" make player_7 a strong suspect. They
do not prove its role (another player could also have visited), and the block does not prove the
trailseer honest: a wolf could report a real visit. (Correction, 2026-10-16: an earlier draft of this
section and the chat said the block "confirms the trailseer"; the owner pointed out it only supports
the report.)

**Setup.** The healer's three passed turns on day 2 (the opening, right after player_7's admission, and
the last sweep), each frozen as played and with the injected line, 10 samples, at low and medium. The
measures were fixed before the run: whether it spoke, whether it claimed healer, whether its private read
of player_7 says chanteuse, and whether its message names player_7 as the blocker.

**Result: the fact is absorbed, the behaviour does not change.**

| Turn after player_7's admission | Spoke | Claimed healer | Read: player_7 is the chanteuse |
|---|---|---|---|
| Low, as played | 0/10 | 0/10 | 0/10 |
| Low, injected | 0/10 | 0/10 | 2/10 |
| Medium, as played | 1/10 | 0/10 | 3/10 |
| Medium, injected | 1/10 | 0/10 | 4/10 |

The opening and last-sweep turns spoke 0–1 times in 10 in every cell.

- **The injected fact was taken up every time.** All ten low-effort notes on the injected turn now say
  the Chanteuse visited the healer; none did without it.
- **The second link was rare.** "player_7 visited me, so player_7 is the chanteuse" appeared in 2–4
  reads of 10.
- **Even then it stayed silent.** Every note ended with "stay quiet unless addressed" and "do not reveal
  my role without need". The one injected sample that spoke made the inference: "I was roleblocked
  last night, so the chanteuse visited me. player_7 says they went to player_8, and the trailseer
  confirmed that visit. … I'd vote player_7 if the vote were today." Its "confirmed" overstates: the
  trailseer reported the visit and player_7 admitted it.

**Decision.** The injection removes the step it targets, so it is not wasted. But R1's bottleneck is the
choice to stay silent, not the missing fact. The wider audit of other certain conclusions waits until
the silence is understood (§5).

## §5 R1: why the healer stays silent

**Question.** §4 left the healer knowing the Chanteuse had visited it and still passing. The owner asked
whether the healer's card tells it to stay quiet. It does not say so in words: no prompt contains "stay
quiet unless addressed". Three sources could produce the silence:

1. **The healer card.** Its playstyle opens "Staying alive matters a great deal … so every decision
   balances your own survival against shielding the players who matter most." That pushes toward hiding
   the role.
2. **The healer's own note.** Each turn shows a seat the strategy note it wrote last. The healer wrote "Stay
   quiet on day 2 unless addressed … do not reveal my role without need" at the day-2 opening, and every
   later note repeated it.
3. **Haiku's disposition, with the turn's permission to pass.** The open floor ends "a pass costs nothing
   here"; the town vote-reason line ends "If you would abstain, you may pass". Haiku passes on most turns
   whatever the role: on days 2–3 of this game the vigilante passed 4 of 5 turns and the sentinel 3 of 5.

**Setup.** The injected turn right after player_7's admission, 2×2, 10 samples a cell at low. The note:
as played, or neutral (the same facts, no stance: "I am the healer. Night 1 I tried to protect player_5 and
was roleblocked, so I have no results. Player_1 died …"). The card: as is, or without its survival
sentence (from a temporary worktree with `healer.py` edited). Every cell has the injected night record.
Measures as §4; whether a message ties player_7 to the block is read by hand.

**Result: the note matters, the card does not.**

| | Card as is | Card without the survival sentence |
|---|---|---|
| Note as played | spoke 2/10; ties player_7 to the block 0 | spoke 1/10; 0 |
| Neutral note | spoke 4/10; 2 | spoke 5/10; 1 |

- **The card made no difference.** It spoke 6 of 20 times with the sentence and 6 of 20 without it.
- **The carried-forward note did.** With the note as played the healer spoke 3 times in 30 (this run
  and §4's same cell); with the neutral note, 9 in 20 (Fisher p = 0.007; this run alone, 3/20 against 9/20,
  p = 0.08). The stance a seat wrote for itself early in the day, re-read every turn, keeps it silent.
- **Speaking did not mean reasoning well.** Of the 12 messages, three tie player_7 to the block ("player_3's
  follow says player_7 went to player_8, and player_8 was roleblocked that night. That fits player_7 as the
  Chanteuse."). Others garble the visit: "I was roleblocked, so that visit did not happen", "I did not get a
  visit from you", and a conflict between the trailseer and the investigator that does not exist. Haiku
  still misreads what a block does to a visit, even with the certain conclusion in its record.

**Decision.** R1 has two causes. A note that fixes a stance and is re-read every turn keeps a seat silent
after new evidence arrives; that is a cross-role issue in how notes are carried forward, not a healer-card
issue, and its fix is for the owner to rule on. Separately, injecting a certain conclusion is taken up
reliably (§4) but does not by itself produce the next inference. So the wider audit for other certain
conclusions stays open: worth doing, but not expected to change behaviour on its own.


## §6 Rewriting the private note (not adopted)

**Why.** §5 found the healer's own note keeping it silent. The note block told every seat to "update your
strategy notes based on new information", which adds facts but never asks whether an old stance still
holds. The owner and Claude drafted a replacement in three parts (the owner's review shaped it): *Changed*
(new evidence, or a mistake now noticed), *Reasoning* (the conclusions the evidence supports, with reads
treated as hypotheses and claims kept apart from facts), and *Plan* (whether the updated conclusions change
the value of speaking, voting or acting). It keeps the vote prompt's guard that the new note replaces the old
one, so conclusions that still hold must be carried forward. The tested text is in
`prompt_versions/note_v1_changed_reasoning_plan.py`.

**Setup.** A screen, not a verdict: 14 frozen cases, Haiku at low, 4 samples a case, the current wording
(from a worktree) against the new one, with each case's previous note identical in both arms. The cases are
R1's 2×2 (the healer turn as played and injected, × the two wordings), controls where passing or keeping the
earlier plan is right (the healer's opening turn, three 2f19d908 seats whose reasoning still held, a 403f4dbc
watch read correctly, three right votes), and positives (seat 4's "unclaimed", a visit read the wrong way
round, the investigator's vote for the healer, seat 4's replayed vote for the healer, 403f4dbc's day-5
vigilante). Per the owner's budget rule, no API judge: two Claude subagents launched from the chat judged
every sample blind (arms relabelled X/Y per case) on the owner's rubric. The rubric scores whether the action
is justified by the evidence at the time, whether certainty is calibrated (a supported suspicion, not
proof), whether the content is useful or garbled, fact errors, and whether the note keeps valid conclusions
or carries a wrong one. The blinding was partial: the new notes' layout is visible, and both judges noticed it.

**Result: worse on the judged measures, unchanged on behaviour.**

| 56 samples per arm | Current wording | New wording |
|---|---|---|
| Fact or rule errors | 15 | 27 |
| Note keeps or adds a wrong deduction | 15 | 28 |
| Overclaims | 6 | 11 |
| Unjustified action | 10 | 13 |
| Note drops a still-valid conclusion | 3 | 7 |
| R1: calibrated certainty (of 8) | 0 | 3 |
| R1: passed (of 8) | 7 | 7 |
| Output tokens per call | 1,128 | 1,127 |

Caching and output cost were unaffected (cached input 6,359 against 6,729 tokens a call; notes about a
quarter longer, reasoning a little shorter). R1 moved toward calibrated certainty, and one injected sample
shared the block and pressed player_7, but the healer still passed in 7 of 8 samples under both wordings.

**Reading.** Asking Haiku to write out its conclusions produced more conclusions, and a larger share of them
were wrong. The commonest invented error, in both arms, is a conflict between claims that agree: on
2f19d908 day 3 the votes call the healer's claim "unverified" or "in conflict with" the sentinel's, though
the sentinel's watch matches it. The new wording gives that mistake a dedicated line to be written in. The
judged differences are large for n=4 but not tested for significance, and a judge who can see the layout
may lean either way; this is a screen that found no gain, not a measured harm.

**Decision.** Not adopted; the live note wording is unchanged and the continuation run was not worth doing.
Two directions follow from the reading:

1. **State in code when today's claims agree.** The invented conflict is checkable: the claim ledger already
   matches claims against the record across days, but today's claims sit only in the transcript. A line
   such as "player_2 says its watch on player_5 saw player_7 and player_8; player_8 says it protected
   player_5: these agree" is a certain consequence of the two claims (not a judgment of their truth), so it
   falls under the owner's rule for deterministic injection.
2. **Medium thinking for votes.** The owner approved it once a prompt attempt had been tried first; this
   was that attempt.

---

## §7 The game: 645228e7 (2026-10-16)

A served game, Haiku 5.5 in nine seats at thinking `low`, memory off, the owner in seat 1 as the
Chanteuse. The serial killer won on day 4. It ran on the server deployed on 2026-10-15, so none of
this day's changes were in it: the old closing line (R14), `record_check`, no deduction lines. Its
public events are in `data/game_645228e7/events.jsonl`; its prompts are in the server database's
`prompt_captures` (game id `645228e7-a75b-4a57-a6e2-1a569838bf31`).

- **The decisive misread (R9).** On night 2 the serial killer attacked player_3 and the healer saved
  it. A save shows only that player_3 is not the serial killer: the pack's wolves can be attacked and
  saved like anyone. Three town seats wrote that it made player_3 "likely town", and from there
  read the investigator's Suspicious check on player_3 as a frame. The certain line was never
  stated: in this cast a Suspicious check means a wolf, so "if player_8's check is true, player_3 is
  a wolf", and no one else claimed investigator. Both belong to the deduction block (the save to the
  public facts, the conditional to Table F, F5), in the agent-only part of the prompt; the owner ruled
  they must not appear in the moderator's public messages.
- **Quoted hedges (R11).** The recited sentences come from three places in the turn prompt: the rules'
  visit paragraph ("A watch on a player shows who came to them, never where they went…"), the
  system prompt's rule to keep facts, claims and hypotheses apart, with the rules' "anything a player
  says about the night is a claim", and the summary header "(claims, not facts)". The memory
  system's EPISTEMIC_STATUS_RULE (`standards.py`) is not among them: it rides every turn's input
  dictionary but only the memory lookup, extraction and dedup templates render it, and this game
  had memory off. Each hedge was added against a hallucination; the seats now use them as all-purpose
  reasons to discount evidence. The deduction lines carry the same risk and must state conclusions
  about players, not rules.
- **Silent days (R12).** The opening round's rule says passing is the normal answer, and most notes
  say "stay hidden". Together they emptied three of the four days.
- **The wolf chat (R13).** The pack prompt was built for two AI wolves proposing and agreeing on a
  target. The illusionist's note on night 1 says "agree with player_1's proposed kill on player_10";
  the human had proposed nothing. The owner sees the wolf-chat UX on a phone (the chat window is too
  small) as the larger problem; a design is for the owner's review.

## Sources

- Code: `evaluation/experiments/haiku_effort_cases.py`, `haiku_effort_score.py`,
  `haiku_summary_compare.py`, `deduction_injection_cases.py`, `deduction_injection_score.py`; the
  checkpoint reader is `haiku_game_turn_cases.day_states`.
- Configs: `evaluation/config/hallucination_bench_haiku_effort_{votes,turns}.json`,
  `hallucination_bench_deduction_injection.json`, `hallucination_bench_healer_silence.json`.
- Data: `data/haiku_effort_replay/` (cases), `data/haiku_summary_compare/` (summaries and verdicts),
  `data/deduction_injection/` (cases); bench samples and verdicts in
  `evaluation/eval_results/hallucination_bench/{haiku_effort_votes,haiku_effort_turns,deduction_injection,healer_silence}/`.
- The R2 fix: `Agents/rules/closing.py` (2026-10-16). `record_check` removed from the day summary (2026-10-16, §3).
- §6: `evaluation/experiments/note_prompt_cases.py`; samples in `evaluation/eval_results/note_prompt_screen/`;
  judging packets, blind key and verdicts in `data/note_prompt/judging/`.
