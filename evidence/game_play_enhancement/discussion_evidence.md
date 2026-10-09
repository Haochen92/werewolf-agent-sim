# Giving the Day Discussion Something Real to Argue About

> **What this is.** A running record of one gameplay problem and the work to fix it. The problem: the
> agents' daytime discussion keeps falling back on voting records and on who has or hasn't spoken,
> instead of on reasoning from evidence. The work runs in three phases, cheapest first: prompt changes
> (phase 1), changes to the turn-taking scheduler (phase 2), and a new set of roles (phase 3). Each
> phase records its plan, what we found, what we built, and how it turned out. Later entries supersede
> earlier ones. Where a plan changed, the change is shown in place rather than edited away.
>
> **Companion records.** The current 9-player role set was designed in
> [`role_set/`](../role_set/experiment_log.md), and the turn-taking scheduler was built in
> [`sequential_discussion/`](../sequential_discussion/experiment_log.md). Both are closed records; this
> document builds on them without changing them. Only options with a real trade-off are written down
> here. Ideas rejected outright are left out.

---

## 1. The problem

Every game is nine AI players: three villagers, a healer, an investigator and a vigilante on the town
side, two wolves, and a serial killer who plays alone. During the day they talk one at a time, then
vote someone out.

Watching the games, the talk felt thin. Most accusations rested on three things: how people had voted,
who had stayed quiet, and who had spoken first. Little of it was the kind of reasoning that makes the
game interesting to watch or to study, such as weighing two conflicting claims or testing a theory
against what happened overnight.

The current design is a defensible starting point, and that matters for reading what follows. The
nine-player cast was chosen to be the smallest set that made a memory experiment measurable, not to
make the richest conversation. The scheduler's rules were each added to fix a real problem:
- It lets the quietest player speak next, so nobody is shut out.
- It has a "novelty gate": an outside AI judge that silently skips a volunteered message if it only
  repeats what others said. Before the gate, a single day could hold twenty near-identical messages of
  agreement.

So the question was never "is the current design broken?" but "what is the discussion missing, and
which change would supply it?"

Two explanations were on the table at the start:

1. **Too little information.** The investigator is the only role that learns anything at night. The
   working assumption was that the investigator stays hidden for fear of being killed, which leaves
   everyone else with nothing but votes and behaviour to go on.
2. **The engine invents "evidence."** The scheduler decides who speaks and when. The first speaker each
   day is picked at random, and the novelty gate silently skips players. The agents cannot see any of
   this, so they may read the machinery's choices as player behaviour: "player_7 has been very quiet",
   "player_2 jumped in first."

---

## 2. Checking the premise before changing anything (2026-10-03)

Before designing a fix, we checked both explanations against games already on disk. The check cost
nothing, because every game already records the labels it needs.

**The instrument.** At the end of each day, a summary model writes up the discussion for the next
day's prompts. As part of that summary it lists every accusation and labels what the accusation rests
on. There are four labels: the voting record, a behaviour pattern, communication style, or a concrete
claim. Counting these labels is a free first look at what drives suspicion.

The labels have clear limits. They come from the same model that plays the game, not from an
independent judge. They are coarse: "behaviour pattern" covers anything from staying quiet to
reasoning about who survived the night. So this census points a direction. The real before/after
measurement uses an independent judge (§4).

**The data.** The 28 most recent games: four batches of 7, run 2026-09-17 at commit `e1a2e3dd` on
`gemini-3.5-flash-lite` (Vertex), with memory retrieval off. The census script is
`evaluation/experiments/discussion_evidence.py census`.

### 2.1 What accusations rest on

Behaviour and voting carry three quarters of all accusations. Concrete claims carry one fifth.

| Evidence label | Accusations (N=194) | Share |
|---|---:|---:|
| Behaviour pattern | 91 | 47% |
| Voting record | 55 | 28% |
| Concrete claim | 38 | 20% |
| Communication style | 10 | 5% |

The voting share grows as the game goes on, from none on day 2 (no votes exist yet) to 38% by day 4.
That is expected, since the record gets longer every day. The concrete-claim share stays flat at
roughly 18–22% throughout. The game never produces more claims to argue about as it goes on.

### 2.2 The assumption that turned out wrong: the investigator is not hiding

The investigator claimed the role publicly in **24 of 28 games**, usually on day 2, the first day
with a result to share. They survived to the end in 20 of 28 games. Town won 18 of 28.

The "too scared to come out" behaviour most likely dates from an older prompt. Until a prompt audit in
June, the investigator was told that survival came first. That instruction is no longer the default,
in these games or on the live site.

### 2.3 What actually flattens the talk: one source of truth, never contested

When town accuses someone on the strength of a claim, it is almost always right. When it accuses on
anything else, it is barely better than chance.

| Town accusations, by label | Landed on a wolf or the serial killer |
|---|---|
| Concrete claim | 34 / 35 (97%) |
| Behaviour pattern | 25 / 42 (60%) |
| Voting record | 15 / 28 (54%) |
| Communication style | 1 / 5 |

For scale: evil players are 3 of the 9 seats, so a random accusation lands on one about a third of the
time. The "concrete claim" row is in practice the investigator reporting a result. A typical entry,
lifted from a day-2 summary:

> *player_1 claims to be the investigator and states that their night one investigation result
> identified player_2 as the serial killer.*

The other half of the picture: **across 28 games, no wolf and no serial killer ever claimed a role.**
Their only answer to a real investigator was to call the result fabricated, as in this day-3 summary
entry written about a wolf's accusation:

> *Player_2 fabricated an investigator claim and a wolf check on player_4 as a convenient defense when
> cornered about surviving double attacks.*

That defence offers no rival claim. Town has nothing to weigh against the investigator, so it doesn't
have to choose between two stories. A typical game runs: the investigator claims, town follows, and
the rest of the discussion is filler around that. The wolf instructions never mention bluffing or
fake-claiming, although the shared rules do say any player may claim any role.

### 2.4 Most "silence" is the scheduler's doing

Across the 28 games, the agents wrote 1,166 messages and passed 517 times. Of those passes, **367 were
the novelty gate skipping someone**, and only 150 were a player choosing to pass. So 71% of the time a
player was silent, the moderator had silenced them, and nobody at the table could tell.

To see what the vague "behaviour pattern" label actually holds, we read 25 of those accusations,
sampled at random:
- About 5–6 were about silence, such as *"Accused of staying completely silent while the rest of the
  village debated a major discussion topic."*
- About 7 were about someone pushing a lynch too hard.
- About 5 were attacks on an investigator's claim, mostly by evil players.
- About 5 were genuine deductions from what happened at night, such as *"Player_4 was completely
  unharmed on a night when everyone else was targeted, which points straight to them being the serial
  killer."*

At roughly a fifth of that bucket, quietness drives something like one accusation in eight overall.
That is real but not dominant. The night-survival inferences are the reasoning the redesign wants
more of.

Speaking order looks rare as evidence. A crude text search found later messages tying the first
speaker to words like "first" or "opened" on only 5 of 95 days. A keyword search cannot reliably read
meaning, so this stays a guess until the judge checks it (§4).

The summary itself feeds the habit only a little. Its instructions ask *"Who is driving the discussion
vs. staying quiet or deflecting?"*, and that answer goes into the next day's prompts. In practice only
**4 of 124** summaries actually named a quiet player. (A first keyword count reported 32. Most of those
were day-1 lines such as "no players are staying quiet yet". Matches are now read before they are
quoted.)

### 2.5 The root cause, restated

The talk is thin because the game has **one exact source of information and nobody contests it**.
When the investigator speaks, the day is settled. When they don't, there is nothing better than votes
and behaviour to go on. Engine-made silence adds some noise on top of that, but it is not the main
cause.

This changes what the redesign must deliver. Making the investigator braver would not help, because
they are already brave. The game needs several imperfect information sources, and it needs evil to
have a real way to contest them.

---

## 3. Phase 1 design: change only the prompts

Phase 1 changes only the text the agents are given. No scheduler or role changes, and nothing is
deployed to the live site. If the prompts alone make the talk more contested and less meta, phases 2
and 3 can build on that. If they don't, we learn how much the structural changes have to carry.

All the agent-side changes sit behind one switch, `WW_DISCUSSION_PROMPT=v2`, which is off by default.
A switch is used rather than a separate branch because the two versions are small and coexist, and we
expect to compare them more than once. This follows the project's rule for design variants (CLAUDE.md,
"Versioning Design Variants"). The investigator change from June was handled the same way.

### P1. Tell the players how turn-taking works

*Problem:* the agents read the scheduler's choices as player behaviour (§2.4). *Change:* one
sentence added to the game rules every player receives, under how the day works:

> "The moderator decides who speaks next: the first speaker each day is random, players who were
> addressed answer first, and a player whose point has already been made may be skipped. Who spoke
> first, how often someone spoke, or who hasn't spoken yet says nothing about their role."

This is a fact about the world, not a strategy instruction. That distinction matters because the
discussion prompt already says *"don't manufacture suspicion out of how talkative, quiet, aggressive,
or cautious someone is."* That instruction hasn't held. One plausible reading is that a rule against
the only available signal loses to the need to say something. A fact about how silence is produced
removes the signal's meaning instead of forbidding its use.

*Trade-off accepted:* it also removes the rare genuine case of a player dodging the conversation by
passing. That is acceptable because passes are invisible to the agents anyway. The one dodge that
does show (being asked a direct question and not answering it) is unaffected: a player who is
addressed cannot pass, so the dodge appears in the transcript.

### P2. Stop the day summary asking who was quiet

*Problem:* the summary's instructions ask who is "staying quiet or deflecting", and the answer feeds
the next day. *Change:* the field's instruction becomes *"Who is driving the discussion, and what
evidence are they using?"*

This is now a small clean-up rather than a fix for a major cause. Only 4 of 124 summaries named a
quiet player (§2.4). It is kept because it costs one line and points the summary at evidence rather
than at participation. *Cost:* this instruction is part of what the model sees, so the switch has to
choose between two versions of the summary format.

### P3. Tell evil players that claiming a role is an option

*Problem:* evil never claims a role, so the investigator is never contested (§2.3). *Change:* a
paragraph in the wolf and serial-killer instructions, written as facts with a two-sided trade-off
rather than as an order:

> "Claiming a role: you may claim any town role, including investigator, healer or vigilante. A claim
> can discredit a real claimant or give you cover, but the real holder may counter-claim, the town can
> check your story against what happens at night, and your true role is revealed if you're eliminated."

The facts-plus-trade-off form follows the standard the June prompt audit set: instructions should
state how the game works and what an option costs, not tell a faction what wins. Prescribing
fake-claims would bake our own strategy into the agents' play.

*Trade-offs accepted:*
- Town will probably win less often than its current 18 of 28.
- A fake investigator has to invent results that stay consistent across days, with no record of its
  earlier lies. We expect more inconsistency in evil players' messages. That inconsistency is a fair
  tell for town to catch, but the hallucination screen may count some of it.

### P4. Deliberately left unchanged: the voting instructions

An outside review suggested that two existing lines push the talk toward votes. The villager
instructions call the voting record *"the most durable hard evidence you have"*, and the wolf
instructions say *"Blend your vote with the village majority whenever possible."*

Both were tested in the June prompt audit and kept. The voting-record line is simply true. Blending
showed a helpful trend for wolves (p≈0.07 over 122 games). Removing true or helpful instructions to
change the conversation's texture would trade play quality for style. *Revisit if* votes still
dominate the talk after P1–P3.

### P5. Shorter messages

*Problem:* agents are asked to keep messages "under about 120 words", which allows a small speech
every turn. Long messages make transcripts longer, which costs money and makes earlier facts easier
to lose.

On the current model this is less of a problem than it sounds. Across the 28 baseline games,
messages already averaged 43 words, and 90% were under 57. So for flash-lite the new target mostly
writes down what the agents already do. It matters more for wordier seat models. In single-game measurements
from July (`evidence/model_selection/report.md`), DeepSeek V4 Pro averaged 142 words with 300-word
tails before the 120-word limit existed, and 92 words under it. *Change:* the instruction becomes

> "Keep your message short: usually 2–3 sentences, about 40–80 words. Make one main point, with the
> evidence needed to understand it."

It is a target, not a hard cut. A complicated defence sometimes needs more room, and a message cut
too short loses the reasoning that makes it readable. Compare:
- *"You said you protected Birch, but I saw you visit Ash. Which claim are you correcting?"* keeps the
  observation, the contradiction and the question.
- *"Your claim contradicts my result."* saves words but is harder to follow.

An outside review proposed three lengths: shorter for an opening statement, medium for discussion,
and shorter again for a closing one. Opening and closing turns don't exist until phase 2, so only the
discussion length applies now.

**The human player's side.** A human seat writes in a text box and can ask its own agent to draft a
line.
- **The box's limit** drops from 700 to 500 characters, in both the browser and the game engine. The
  old 700 was sized to the agents' 120 words; 500 is about 85 words, a little over the agents' new
  target.
- **The draft helper** is already limited to 60 words, inside the new range, so it is unchanged.
- **One length for humans.** If opening and closing turns arrive in phase 2, humans keep a single
  length limit rather than three.

*Trade-off accepted:* the human limit is not behind the switch. Deploying it while the switch is off
would hold humans to about 85 words while the agents may still write 120. The two should go live
together.

### Considered for phase 1 and deferred

- **Showing passes to the agents.** An outside review proposed telling agents who was offered a turn
  and passed, to separate "never had a turn" from "chose silence". We kept passes hidden. Passing is
  the instructed default, so treating it as evidence would contradict the instruction and recreate
  "player_7 is being quiet". Revisit if the opening round in phase 2 makes "never had a turn" a real
  confusion.

---

## 4. Phase 1 measurement plan

**Scale, and why it is small.** Phase 1 is checked on a handful of games: two or three run by hand
with the switch on, against the same number with it off. A full experiment (30 games a side, about $16)
is affordable, but the project has already run many experiments at that scale, and time is the binding
constraint. What this phase demonstrates is the method: a working judge, a stated question, and an
honest read of what a small sample can and cannot show. At N≈3 per side, a result can show a
*direction*: "evil started claiming roles", "silence stopped appearing in accusations". It cannot give
a reliable *size* of the effect.

**The judge.** An independent model reads every message in the day discussion and records:
- what the message rests on (it may be several things);
- whom it accuses, if anyone;
- whether the speaker claims a role for themselves, and which one.

The categories a message can rest on:
- the speaker's own night result;
- someone's role claim or claimed result;
- public night events (who died, who survived, revealed roles);
- the voting record;
- what someone said (a contradiction, a change of story, pushing a lynch);
- participation itself (quietness, speaking order, how much someone talks);
- nothing at all (procedure, general advice, agreement with no new reason).

The judge is shown the public facts as of that day and the day's transcript up to the message. It is
*not* shown anyone's true role, so knowing who is evil cannot colour how it labels the evidence. True
roles are joined in afterwards by code, to compute two things: how often accusations of each kind
land on an evil player, and which self-claims are fake.

**What counts as better:**
- The "participation" share falls.
- Evil players make role claims that town then has to argue about.
- Message length falls toward the new target.
- The hallucination screen does not jump.

The owner also hand-checks the judge's labels on these games. That check is how far the judge's
numbers can be trusted.

**Runner:** `evaluation/experiments/discussion_evidence.py` (`census` for the free label count in §2,
`judge` for the independent read).

---

## 5. Phase 1 build (2026-10-03)

**The switch.** `WW_DISCUSSION_PROMPT=v2` is read once when the prompts load, the same way the June
investigator switch works. Each change is written as an addition applied only when the switch is on.
With it off, the prompts are unchanged; a check confirmed the shared game preamble is byte-identical
to the previous commit.

| Change | Where the agents meet it |
|---|---|
| P1, the turn-taking fact | A "Turn order" line in the shared game rules, just before the night rules. Every prompt that carries the rules gets it, including the day summary and the post-game memory extraction. |
| P2, the summary's "drivers" field | A second summary format whose only difference is the field's instruction. The summary step picks the format by the switch. The stored keys are identical, so everything downstream reads both versions the same way. |
| P3, the claiming option | A "Claiming a role" paragraph appended to the wolf and serial-killer instructions only. |
| P5, the length target | The 120-word line in the discussion's tone instructions is replaced by the 40–80-word target. |
| Human line limit | 700 → 500 characters in both the game engine (which refuses a longer line) and the browser's text box, whose counter appears in the last 100 characters. |

**Verification.**
- A new test runs the prompts in a fresh process with the switch off and with it on. Off, nothing
  changes. On, all four changes land, and only the wolf and the serial killer get the claiming
  paragraph.
- The full Python suite passes (1,074 tests). So do the browser's unit tests for the text box and
  the end-to-end test that typing stops at the new limit.

**The measurement runner** is `evaluation/experiments/discussion_evidence.py`.
- `census` reproduces §2's numbers from the in-game summary labels, plus the counts no model is needed
  for: passes by kind, messages per day, words per message.
- `judge` sends every discussion message to the project's standard judge model (`gemini-2.5-pro`).
  It writes three files: one judged record per message, a summary, and a review sheet with space to
  mark each label right or wrong.

A first run of the judge on one baseline game read all 37 messages with no errors. The labels looked
sensible on a skim, including a wolf turning silence into a weapon: *"player_5 and player_6 haven't
chimed in yet today. We should see where they stand."* One label may be over-applied: "something a
player said" is attached to messages that merely open with "building on X's point". The owner's
hand-check (§6) will settle that. Output: `data/baseline_smoke/`.

**An end-to-end game with the switch on** (`batch_results/discussion_v2_smoke`, one memory-off game)
ran cleanly; town won on day 4. The new summary format worked with the live model. Its "drivers"
answers now name evidence, for example *"…focusing scrutiny on player_2 based on the investigator's
voting history…"*, and none of its 4 summaries named a quiet player. No evil player claimed a role in
this one game. With one game that is not a result either way; it only shows the switch runs. The
leak checker flagged wolves receiving the wolf channel during their night vote, but it flags the same
thing in every baseline game. It predates this work and is left for a separate look.

---

**Switched on at the live site (2026-10-03).** The owner chose to play the v2 prompts through the
website rather than in scripted batches, and the site was in development with no outside players.
So both containers were rebuilt at `9ae5056` with `WW_DISCUSSION_PROMPT=v2` set for the server
(deploy record: `frontend/docs/build_plan.md`). Removing that one setting and restarting the server
returns the site to the old prompts.

The judge was extended to read website games. A finished game's public replay holds every event
(speeches, passes, votes, night deaths with attacker, summaries, roles), and the runner rebuilds
the same record a batch game produces (`--replays <id>` or `--latest N`). Human seats are kept in
the transcript the judge reads but are not themselves judged, because the agents are what is being
measured.

---

## 6. Phase 1 outcome

*In progress: two v2 games judged so far (only the first matches the baseline's model), and a third read by hand for hallucinations (§6.4).*

**The comparison set.** The "before" side is three website games from before the switch, all on
`gemini-3.5-flash-lite` with memory off, judged by the same judge model as the "after" side:
- `500b5167` (2026-10-03) and `965b8148` (2026-09-27), each with human players at the table, the
  closest match to how the v2 games will be played;
- `ff26faff` (2026-09-15), all agents.

Both sides come from the same site and model. What the comparison does not hold fixed: the code
changed between those dates in ways unrelated to the prompts (for example the stall-rescue model,
added 2026-10-01), and the human seats play differently from game to game, which shapes what the
agents respond to. At three games a side,
any difference is a direction to look into, not a measured effect. Output: `data/live_baseline/`.

### 6.1 The first v2 game (`832404e9`, 2026-10-03)

The owner played seat 9, a villager. The serial killer won on day 5. Output: `data/live_v2/`.

| Measure | Before (3 games, 117 agent messages) | v2 (1 game, 30 agent messages) |
|---|---|---|
| Words per message, mean / 90th percentile | 43 / 56 | 36 / 47 |
| Messages using participation | 9% | 17% |
| Accusing messages using participation | 3% | 22% (4 of 18) |
| Fake role claims by evil players | 0 | 0 |

- **Shorter messages: the expected direction.** One game is not enough to say more.
- **Participation went up, but not in the way P1 targets.** Four of the five messages carrying the
  label are one wolf attacking *when* the investigator revealed its result: *"Dropping a hard
  investigator claim the second discussion starts feels less like helping the town and more like
  trying to railroad a lynch."* That rests on a choice the investigator made, not on an order the
  scheduler imposed. The judge's "participation" category lumps the two together. It needs
  splitting, into turn order and silence (the engine's doing) versus the timing of a reveal (the
  player's choice), before it can measure P1.
- **No evil player claimed a role** in this game.

**Re-judged with the category split.** The judge's "participation" label became two: *turn taking*
(how often or in what order someone has spoken, which the moderator decides) and *reveal timing*
(when a player chose to share something). Both sides were judged again with the new rubric:

| Measure | Before (3 games, 117 agent messages) | v2 (1 game, 30 agent messages) |
|---|---|---|
| Messages using turn taking | 7 (6%) | 0 |
| Accusing messages using turn taking | 0 of 78 | 0 of 19 |
| Messages using reveal timing | 19 (16%) | 5 (17%) |

Turn taking falls to zero in the v2 game, the direction P1 aims at, but one game cannot carry that.
Reveal timing is unchanged, as expected, since P1 says nothing about it. Re-judging also moved other
shares by several points (the baseline's "something a player said" went from 74% to 63% of
messages), which is a reminder that the judge's labels shift with its rubric. That is why both sides
must always be judged with the same rubric in the same run.

### 6.2 An investigator invented a result, and believed it

On day 4 the investigator said: *"I investigated player_9 last night, and they are the remaining
wolf."* It never checked player_9. Its three checks were player_1 (wolf), player_4 (villager) and
player_5 (healer), and its prompt listed all three every day. The village voted player_9 out 4 to 1;
they were a villager, and the serial killer went on to win.

Its own records show a belief, not a planned lie:
1. **Before the claim, its private read of player_9 was "serial killer, low confidence".**
2. **On its turn before, it promised:** *"I'll share who I investigated last night."*
3. **It then made the claim.**
4. **It adopted its own claim.** Its read at the vote became *"wolf, high: investigated last night and
   confirmed as a wolf."*
5. **It never noticed the contradiction.** After player_9 was revealed as a villager, its note says
   only *"Player_9 was a villager, meaning one wolf and the serial killer remain"*.

None of the v2 changes touch the investigator: the claiming option went only to the wolves and the
serial killer. False statements in messages are a known problem; the earlier hallucination count put
them at about 3% of messages. This one is severe because a fake investigator result decides the vote.

**How the prompt may have set it up.** These are readings of the prompt's structure, not
measurements:

- **Its own note fed the claim back to it.** Near the end of each turn's message, after the
  transcript, the agent is shown its private note from its previous turn, under "You have a private
  strategy note from your previous turns". Only the standing speaking rules come after it. On day 4
  that note read: *"Continue leading the village using my investigation result from last night.
  Address player_3's point on the voting split and press player_9 on the abstention."* The note welds
  "my investigation result" and "press player_9" into one instruction. Nothing in the prompt says
  the note is the agent's own earlier plan rather than a record of what it knows.
- **The real result looked like public news.** The private results are rendered as
  *"Day 3: player_5 was revealed as healer"*. "Revealed" is the same word the rules use for roles
  shown at death, and player_5 did die that night with the healer role announced. The line does not
  say "you investigated", and it labels the check by day rather than by night, although it is now
  day 4 and the check was "last night". So the one private fact the agent had for that night looked
  like a repeat of public information, which may have left it believing it had nothing new to share
  after promising to share something.
- **The results sit far from the decision.** They come near the top of the turn message, ahead of
  the whole transcript. The promise and the note come at the end.
- **Committed reads did not prevent it.** The agent records a read of every player before it writes
  its message, and that read still said "serial killer, low" moments before the claim. Reading
  first was meant to tie the message to the agent's actual belief, and here it did not.

**The replay test (2026-10-03).** The investigator's exact day-4 turn was rebuilt from the game's saved
engine state (its LangGraph checkpoint, read without writing), using the engine's own builder for the
turn's inputs. The same template and model (`gemini-3.5-flash-lite` on Vertex, default temperature)
were then sampled 20 times under each of four variants. The note was removed rather than reworded,
because removal is the cleaner test of whether it matters at all. Runner:
`evaluation/experiments/investigator_claim_replay.py`; every prompt and sample is in
`data/investigator_replay/`.

| Variant | Invented a check | Reported its real check (player_5, healer) |
|---|---|---|
| A. As played | 20 / 20 | 0 / 20 |
| B. Results reworded | 0 / 20 | 20 / 20 |
| C. Previous note removed | 20 / 20 | 0 / 20 |
| D. Reworded and note removed | 0 / 20 | 20 / 20 |

The counts come from reading every sampled message. A keyword screen flagged 19 of 20 in A and in C,
but missed one in each that used other words (*"my investigation last night targeted player_9"*).

**The wording of the results is the cause; the note is not.** As played, the investigator never once
recognised player_5 as its night-3 check. In most samples it invented a check on player_8, a safe
"cleared villager" claim, and in some it invented a wolf or serial-killer result, as in the live
game. With the results reworded, every sample reported player_5 correctly, often adding *"who
unfortunately was killed by the wolves"*. Removing the note changed nothing, so the first reading
above (the note fed the claim back) is not supported. The note may still steer who gets suspected,
but it did not cause the invention.

What the test does and does not show:
- **It pins one turn exactly.** Same board, same prompt, same model. Only the sampling varies, which
  is what the 20 draws average over.
- **It is one turn from one game.** It shows the old wording can make invention near-certain in the
  right situation: a check whose target also died that night and was revealed. It does not measure
  how often that happens across games.
- **The new wording changed two things at once.** It names the check as a night and as the player's
  own action ("you investigated"). The test cannot say which of the two mattered. For the fix it
  doesn't need to.

**The fix.** The engine now writes every investigator result the reworded way, for all games and not
only behind the v2 switch, because the old wording is a correctness bug rather than a design variant.
For example: *"Night 3 (last night): you investigated player_5, who is the healer"*. "(last night)"
appears only when the check really was the night before the current day. The exact-prompt golden test
was regenerated on purpose; its only change is that one line.

*Effect on the comparison:* v2 games played after the fix differ from the first v2 game in this line
as well. The baseline games all had the old wording. This mainly affects the investigator's own
messages (the "own night result" category).

### 6.3 The second v2 game (`8e26fd3b`, 2026-10-03)

The owner played seat 6, the vigilante. The serial killer won on day 3. Output: `data/live_v2_game2/`.

**This game ran on a different model,** `gemini-3.6-flash`, chosen in the lobby, not the
`gemini-3.5-flash-lite` of the baseline and the first v2 game. It played with the old investigator
wording (the fix in §6.2 is not deployed yet). So it can't be pooled with the first game for the
comparison; it is a look at v2 on a stronger model.

| Measure | Before (3 games, flash-lite) | v2 game 1 (flash-lite) | v2 game 2 (3.6-flash) |
|---|---|---|---|
| Agent messages | 117 | 30 | 36 |
| Words per message, mean | 43 | 36 | 51 |
| Messages using turn taking | 6% | 0 | 3% (1) |
| Messages using reveal timing | 16% | 17% | 19% |
| Messages using manner | 5% | 3% | 19% |
| Fake role claims by evil players | 0 | 0 | 0 |

- **Turn taking stays near zero,** the direction P1 aims at.
- **Messages were longer, not shorter.** 51 words sits inside P5's 40-80 target but above the
  baseline's 43. With a different model, this says nothing about P5 itself.
- **Manner rose to 19%,** mostly in accusations. One game on another model; worth watching, not more.
- **Evil still never claimed a role,** two v2 games out of two. If the next flash-lite games show the
  same, P3's wording is too weak to change behaviour.
- **Day 1 had eight messages,** unlike almost every other website game, where day 1 ends after
  three passes (§7.1).

### 6.4 A game the town won on a fabricated premise (`46355b89`, 2026-10-03)

The owner played seat 2, the serial killer, on `gemini-3.5-flash-lite` with memory off. The village
won on night 4. Read from day 3 on, with every agent's private notes and reads.

**Day 3: the wolves knew something true and lied about where it came from.** On night 2 the wolves
attacked the serial killer. The serial killer is immune at night, and the game does not announce a
failed attack on it; the public heard only that the investigator was stabbed. The wolves' private
reasoning was right ("player_2 is confirmed as the serial killer since our night kill bounced off
them"). In public, player_8 then claimed *"the game master and the night outcomes make it clear who
survived"*. The moderator never said so, and the argument only made sense to someone who knew about
the attack. Two villagers called it a fabricated case, and player_8 was voted out.

**Day 4: real hallucinations, all by town players.**
1. The healer: *"Player_4 defended you yesterday."* The vote record shows player_4 voted to
   eliminate player_2. Corrected by the owner, the healer conceded.
2. The vigilante (and a villager, in a held-back draft): *"you voted to protect player_2 instead of
   lynching player_8"*. The same misreading: a vote *for* player_2 read as support.
3. Three town players treated "player_2 survived multiple night attacks" as fact, though no public
   record shows any attack on player_2, and the same players had rejected it on day 3.
4. The healer and a villager privately read player_2 as "caught in a lie about healer protection".
   Player_2 was right (the moderator announced saves on player_1 only); player_4 had lied that the
   healer protected them. The healer itself made this read, though it had protected player_1 every
   night.

The village eliminated the real serial killer, but for a reason a wolf had leaked and the town had
rejected the day before.

**Likely causes, all in what reaches the agents, not in how much context the model can hold.**
- *A failed attack on the serial killer is silent, and the rules never say so.* They say healer
  saves are announced, so agents can't tell their failed attack is private knowledge, and they cite
  it as public. (First seen in June from the vigilante's side: a true failed-shot claim was called
  impossible.)
- *The day summary passes on a claim as if it were narration.* On day 4 the agents had not seen
  day 3's dialogue, only its summary: *"Player_2 has survived night attacks and remained unharmed
  without claiming a healer, which these players argue points to serial killer night immunity."*
  The conclusion is attributed; the premise is stated as fact. Agents who rejected the claim while
  reading the dialogue accepted it from the summary (cause of item 3).
- *"voted for" is ambiguous.* Later days read the vote as *"player_4 voted for player_2"*, which in
  everyday English means supported (likely cause of items 1 and 2; untested).
- *The healer has no record of its own protections in its day prompt.* The investigator gets its
  results and the vigilante its shots; the healer gets nothing, only its own note (part of item 4).
  The public saves were announced, but the healer believed a confident lie over them.

**Revisions for information fidelity** (all matter more once phase 3 adds roles that act at night).
A code audit the same day ([`code_audit_2026_10_03.md`](../evaluation/hallucination_bench/code_audit_2026_10_03.md))
found more of the same kind: information an agent needed that it was never given, or was given
without saying how far to trust it. All were built on 2026-10-03 (commits `f1b3017`..`c9dbc79`,
baseline tag `fidelity-baseline`), as the new default rather than behind a switch:
- R-a. The rules say which night events are announced and which are silent (an attack on the serial
  killer, an unneeded protection, a vigilante holding fire), and that what a player did or learned at
  night is their own claim, never public record. The healer is said to stop any night kill.
- R-b. **Day summary v3.** The summary is the only account of a past day agents ever see. It is now
  written as attributed claims: the summariser is given the game master's record and the claims
  already on record, and records who disputed each accusation, where it conflicts with the record,
  and each role claim's results and whether it is new, repeated, changed or retracted.
- R-c. Votes are written "voted to eliminate" / "voted to abstain".
- R-d. A private night record for the healer, vigilante and serial killer (and the pack's kills for
  every wolf): what each did each night and what it may know of the result, written by the engine.
- R-e. Earlier days are shown in three labelled blocks: the game master's exact record first (it
  outranks anything said), then the claims on record per player (built by code from the
  summaries), then the discussion summaries.
- R-f. The vote turn sees the private note it is about to replace (it used to overwrite it unseen),
  and every note is labelled as the agent's own fallible working notes.
- R-g. A message the echo filter held back is shown to its author as never seen by anyone.
- R-h. Smaller fixes: a healer save no longer listed as a role reveal in the shared standards, the
  wolves' "villagers" list renamed non-wolf players (it includes the serial killer), the census in
  the wolf night prompts, and the vigilante's bullets shown by day.

The bench comparison (before vs after, and after with the earlier days re-summarised by v3) is in
§6.5.

### 6.5 The fidelity pass on the hallucination bench (2026-10-03)

Three arms on `hallucination_bench_v2`, `gemini-3.5-flash-lite`, v2 prompts, memory off, 3 samples
per case, on the curated (44), pinned (5) and control (40) slices, one judge for all:
- *before:* the code at `fidelity-baseline`, run from a worktree;
- *after:* the new code, with the summaries the games were played with;
- *after, re-summarised:* the new code, with every earlier day rewritten by summary v3. This is the
  arm a live game would match, since its summaries would be v3 from day 1.

| | before | after | after, re-summarised |
|---|---|---|---|
| All samples bad | 97/267 (36%) | 86/267 (32%) | 82/267 (31%) |
| Curated | 85/132 (64%) | 75/132 (57%) | 71/132 (54%) |
| Pinned | 11/15 (73%) | 9/15 (60%) | 8/15 (53%) |
| Controls (false alarms) | 1/120 | 2/120 | 3/120 |
| Messages: bad / checkable | 21/122 (17%) | 32/129 (25%) | 21/127 (17%) |
| Notes: bad / checkable | 77/155 (50%) | 64/154 (42%) | 67/151 (44%) |
| Cases better / worse than before | | 18 / 11 (p = 0.26) | 24 / 14 (p = 0.14) |

- **The direction is right, but not established.** With the summaries rewritten, about a sixth fewer
  bad samples and 24 cases better against 14 worse. That is not significant at this size; it is a
  direction, like the rest of phase 1.
- **Notes improved most** (50% to 42–44% of checkable statements bad), consistent with the private
  night record and the labelled record giving agents facts they used to reconstruct.
- **Messages got worse in the frozen-summary arm only** (17% to 25%). The new errors are mostly votes
  misquoted ("the entire table voted for player_7") and the old miscount of who is left. With the
  game master's record at the top of the prompt, agents cite the vote record more, and get some of
  it wrong. With v3 summaries the rate is back to 17%. Worth watching in played games.
- **Vote turns' notes now carry more claims,** since the vote sees the note it rewrites (R-f). In the
  frozen-summary arm, vote turns went from 4 to 9 bad samples, all in the note; with v3 summaries 3.
- **The pinned cases, read by hand:**
  - *the vigilante's "voted to protect player_2":* 3/3 before, 0/3 after; with v3 summaries 2/3, now
    in the note ("player_4's vote supporting player_2"), so the misreading isn't gone.
  - *the healer's day-4 message:* 3/3 in every arm, but the content changed. Before, the healer
    repeated the wolf's premise and the vote misread. After, it disputes the premise ("player_8 did
    the exact same thing yesterday before turning out to be a wolf"). The judge still counts a
    message that names the premise to reject it, so this case now under-reports the fix.
  - *the wolf's "the game master makes it clear":* 3/3 in every arm. The wolf stopped citing the game
    master, but still states as fact that player_2 survived attacks. R-a moved the wording, not the
    claim.
  - *the healer's vote turn:* 1/3 before, 3/3 after, 0/3 with v3 summaries. At least one of the
    "after" verdicts is a judge error (the read it flagged doesn't call player_2 a liar).
- **The golden judge needs work before it can carry these cases:** flash-lite reads presupposition as
  assertion and makes outright errors on long reads. Re-judging the pinned slice with a stronger
  model, or tightening the expectations to name exactly what counts, comes before trusting their
  numbers.

*Run: `evaluation/config/template/hallucination_bench_fidelity_pass.json`; output
`evaluation/eval_results/hallucination_bench/fidelity_pass_flashlite35/` (not tracked).*

**Bench cases from this game** (pinned, with written expectations): the healer's and the
vigilante's first day-4 messages (items 1 and 2), the healer's day-4 vote turn (item 4; the bench
will need to judge private reads, not only messages and notes), and player_8's day-3 "the game
master makes it clear" (a guard for R-a).

### 6.6 Day summary v4: the summariser transcribes, code checks (2026-10-04)

**Why.** Three things about v3 (R-b, R-e) came up the day after it was built:
- *Its verdict on a claim was its own judgement, and then got lost.* Each role claim carried
  "supported / contradicted / unverified", written by the summariser. Nearly all were "unverified",
  and the compact claim record built from them dropped the field, so the next day's summariser
  never saw an earlier verdict (verification note
  [`fix_verification_2026_10_04.md`](../evaluation/hallucination_bench/fix_verification_2026_10_04.md),
  item 3).
- *Two sections retold the day.* "Alliances and blocs" restated the accusations, and "village
  dynamics" retold the day as a story, which is how the wolf's premise in §6.4 entered the summary
  as narration.
- *It was long.* In 46355b89, the healer's day-4 prompt spent 4,911 characters on previous days,
  most of it the summaries' prose, with each claim appearing both in the claim record and in its
  day's summary.

**What changed** (built as the default; the code before it is tagged `summary-v3-baseline`, at
`e53cb1e`):
- *The summariser only transcribes.* Summary v4 writes two things: the day's accusations (with the
  defence, who else disputed it, and `record_check`), and each role claim with the night actions
  the player claimed, in fixed words (investigate / protect / shoot / kill; results such as a role
  name, `saved_from_attack`, `died`, `not_said`). A claim is `claimed` or `retracted`; whether it is
  new, repeated or changed is worked out by code. Alliances, village dynamics and the per-claim
  verdict are gone.
- *`record_check` is narrowed.* In a live test of v4, it flagged "the game master never announced
  any investigation results" against an investigator's true claim. Investigations are never
  announced. It now counts only an event the game master would have announced (a death, a save, a
  vote), and says so.
- *A claim ledger, kept by code* (`Agents/rules/claim_ledger.py`). It folds every day's claims per
  player. A changed claim keeps the earlier one, and a claim repeated or later given its night is
  merged. Each claim is checked against engine facts:
  - the claimant's revealed role once they are dead;
  - an investigation result against the target's revealed role;
  - a claimed save against the announced saves, and a claimed kill against the deaths;
  - more living claimants of a role than the cast holds (counting revealed holders);
  - the rules (a healer protecting itself).

  A check states the fact and nothing more. It stays silent where the record fits more than one
  reading: a shot player who lived may have been saved, or may be the serial killer, whose survival
  is never announced. The ledger is never stored. Every prompt rebuilds it from the summaries and
  the dead roster, so a role revealed overnight shows in the next prompt's checks.
- *What agents read about earlier days:*
  - the game master's record, unchanged;
  - "Claims made in the day discussion": the ledger, its checks marked "Record:" or "Rules:";
  - "Accusations in the day discussion", each player tagged with their revealed role once dead.

  The summaries' prose, alliances, village dynamics and evidence types are not shown, except for a
  day stored only as text (a failed summary, or a game from before structured summaries). On the
  46355b89 prompt, previous days went from 4,911 to about 2,600 characters.
- *Memory instructions only with memories.* The instructions for retrieved observations and
  strategy points appear only when some are shown. That's about 1,200 characters off every
  memory-off turn, which is every turn on the live site.
- *The healer's core strategy* now says its protection stops any night kill (verification note,
  item 1).
- *Frontend.* An old replay shows its summaries as before. A v4 summary shows accusations with their
  disputes and record checks, and claims with their night actions, without the blocs and mood
  sections. The workbench draws the fixture in the v4 shape with `summary=v4`.

Not done, from the same verification note: a held-back draft is shown to its author on that day
only (item 2), and an investigator's result from the night it died is still missing from
post-game extraction (item 4). Message IDs and revision links for claims were deferred; the
natural keys (a role claim by player, a night action by player and night) carry the history
without them.

This and the fidelity pass are one prompt epoch: neither had been deployed when this was built.

**Bench result.** Two arms on `hallucination_bench_v2`, set up as in §6.5 (`gemini-3.5-flash-lite`,
v2 prompts, memory off, 3 samples, curated + pinned + control), both with every earlier day
re-summarised. *v3* is §6.5's "after, re-summarised" arm: the same code, its generations reused.
*v4* is this build. Both were judged in one run.

| | v3 | v4 |
|---|---|---|
| All samples bad | 82/267 (31%) | 85/267 (32%) |
| Curated | 70/132 (53%) | 71/132 (54%) |
| Pinned | 9/15 (60%) | 9/15 (60%) |
| Controls (false alarms) | 3/120 | 5/120 |
| Messages: bad / checkable | 21/127 (17%) | 34/128 (27%) |
| Notes: bad / checkable | 65/151 (43%) | 62/153 (41%) |
| Cases better / worse | | 11 / 11 (p = 1.0) |

- **No change in hallucination overall.** v4 cut what agents read, not what they get wrong.
- **Messages may have got worse** (17% to 27% of checkable messages; 15 cases worse, 7 better on
  messages alone, p ≈ 0.13). It is not established, but it repeats §6.5's frozen-summary arm (25%),
  and the errors are of the same kind. They are mostly late-game vote and push history misquoted:
  "Player 2 voted to eliminate player_3 just like I did", from a player whose own day-4 vote went
  elsewhere, and "you were pushing against the investigator from day two". The record is in the
  prompt, but each day's votes are listed one voter per line and agents recall them wrongly. A
  compact per-player vote history (code-built, like the ledger) is the obvious next thing to try.
  The follow-up below tests that index.
- **The summariser behaves better.** Across the 104 re-summarised days there were no failures. The
  "investigations are never announced" false flags went from six to none, while the 46355b89
  premise and a misquoted abstention were still caught. Of v4's two other flags, one is a
  confirmation and one is weak. The stored summaries are 55% shorter (113,526 to 50,629 characters).
- **Notes are flat** (43% to 41%). Re-judging the reused v3 arm gave notes 65/151 against §6.5's
  67/151: that is the judge's own noise on identical samples.

*Run: `evaluation/config/template/hallucination_bench_summary_v4.json`; output
`evaluation/eval_results/hallucination_bench/summary_v4_flashlite35/` (not tracked).*

**Follow-up: per-player vote history (2026-10-04).** A deterministic index in
`Agents/prompts/prompt_formatters.py` groups published ballots by voter, in day order:
`player_4: day 2 abstained; day 3 voted to eliminate player_3; day 4 voted to eliminate player_2.`
It follows the original game-master announcements, before claims and accusations. It accepts both
the current and legacy engine ballot wording, ignores discussion summaries and missing ballots,
and inherits the renderer's exclusion of current and future days. No model calls or stored-state
changes are needed. Across all 89 selected cases, the index preserves exactly the published ballot
count. Its body averages 500 characters (maximum 987), plus its heading; four cases have no index.

The follow-up reuses both earlier arms' 267 generated answers and all 104 v4 summaries, generates
267 valid answers with the index, and judges all three arms together. The summary cache was checked
for equality after the run: no summaries changed. The baseline counts move slightly because their
unchanged answers were judged again. There were no judge read errors in this run.

| | v3, re-judged | v4, re-judged | v4 + vote history |
|---|---|---|---|
| All samples bad | 83/267 (31%) | 87/267 (33%) | 80/267 (30%) |
| Messages: bad / checkable | 22/127 (17%) | 33/128 (26%) | 26/125 (21%) |
| Notes: bad / checkable | 66/151 (44%) | 64/154 (42%) | 59/153 (39%) |
| Controls (false alarms) | 3/120 | 6/120 | 4/120 |

As above, message/note rates count fact-sheet hallucinations over successfully checked fact-sheet
units, excluding unanchored units and the separately judged golden expectations. All-sample and
control counts also include golden violations.

- **Numerically better than v4, but inconclusive.** On messages, 14 cases improved and 11 worsened
  versus v4 (two-sided sign p = 0.6900). Against v3, 11 improved and 13 worsened (p = 0.8388).
  On all-sample errors versus v3, 17 improved and 16 worsened (p = 1.0).
- **The proposed deployment target was not met.** Messages remain at 21%, above the roughly 17%
  v3 baseline. This run does not establish a hallucination reduction or equivalence to v3.
- **Recommendation:** restore the v3-style agent view for the next release while retaining the
  v4 summariser, ledger, and frontend improvements, then validate that combination. This experiment
  does not test that hybrid: the v3 baseline used v3 summaries as well as the old view. The candidate
  vote-history patch remains local for review; no rollback, push, or deployment was performed.

Validation: 44 targeted formatter, claim-ledger, information-fidelity, and benchmark tests passed.

*Run: `evaluation/config/template/hallucination_bench_vote_history.json`; output
`evaluation/eval_results/hallucination_bench/summary_v4_vote_history_flashlite35/` (not tracked),
including `summary.json` and `unit_comparison.json`. To reproduce this isolated experiment, first
copy `generations_v3.jsonl` and `generations_v4.jsonl` from the earlier run into the new output
directory, and copy its `summaries_v4.json` as `summaries_v4_votes.json`, then run
`poetry run eval-hallucination-bench --config evaluation/config/template/hallucination_bench_vote_history.json`.
The cached baseline generations are required: generating a v4 baseline from the changed working
tree would include the vote index and invalidate the comparison.*

**Follow-up: a rule to cite the record exactly (2026-10-04).** Every day discussion and vote turn was
told, at its end: when the message or the note mentions a past vote, death or healer save, check it
against the record and keep every name and day as the record has them, in your own words; if the
record doesn't show it, it is at most a player's claim (commit `bc4100a`). Against v4 + vote
history, with its generations reused, the same 104 summaries, and both arms judged together:

| | v4 + vote history | + citation rule |
|---|---|---|
| All samples bad | 80/267 (30%) | 81/267 (30%) |
| Messages: bad / checkable | 27/125 (22%) | 27/130 (21%) |
| Bad messages that mention a vote | 24 | 24 |
| Notes: bad / checkable | 60/153 (39%) | 66/166 (40%) |
| Controls (false alarms) | 5/120 | 1/120 |
| Messages mentioning a vote | 158/199 | 156/197 |
| Median message length | 42 words | 44 words |
| Cases better / worse | | 16 / 18 (p = 0.86) |

- **No effect.** The vote misquotes it targeted were unchanged (24 and 24), and so was everything
  else: agents cite votes as often as before, at the same length, and still write "you voted to
  eliminate player_9 yesterday just like I did" where the record says otherwise.
- **What that says about the misquotes.** Laying the votes out per player, and now telling agents to
  copy them, have both left the rate where it was. It looks like this model writing the point it
  wants to make and filling in the supporting vote from impression, rather than any problem with how
  the record is shown. A stronger model on the same cases would test that. It has not been run.

*Run: `evaluation/config/template/hallucination_bench_record_citation.json`; output
`evaluation/eval_results/hallucination_bench/summary_v4_cite_flashlite35/` (not tracked).*

### 6.7 The agents were not reasoning at all (2026-10-04)

**The finding.** Game turns run at thinking level "minimal" (`DEFAULT_GAME_THINKING_LEVEL`), which on
Vertex is a 128-token budget. A probe with the game's structured output found that `gemini-3.5-flash-lite`
then reasons for 0 tokens, and also at "low" (1,024), passed as a budget or as the native level alike.
It reasons only from "medium" (4,096). `gemini-3.1-flash-lite`, the game model until 2026-09-10, also
reasons 0 tokens at minimal but does reason at low. So every game so far was played with no
reasoning step on its turns. The Google AI backend was not tested (no key in this environment).

**The bench.** Same code (main after `ed7fb76c`, day summary v4), same 104 cached summaries, and only
the thinking budget differs. Both arms freshly generated with token recording, and judged together:

| | minimal (the game default) | medium |
|---|---|---|
| All samples bad | 82/267 (31%) | 27/267 (10%) |
| Curated | 70/132 (53%) | 17/132 (13%) |
| Pinned (golden judge) | 9/15 (60%) | 8/15 (53%) |
| Controls (false alarms) | 3/120 | 2/120 |
| Messages: bad / checkable | 27/129 (21%) | 7/143 (5%) |
| Bad messages that mention a vote | 22 | 5 |
| Notes: bad / checkable | 59/153 (39%) | 15/162 (9%) |
| Cases better / worse | | 36 / 4 (p < 0.0001) |
| Reasoning tokens per turn | 0 | 1,365 |
| Output tokens per turn | 399 | 1,747 |
| Cost per turn (at $0.30 / $2.50 per million) | $0.0025 | $0.0059 |
| Time per turn | 2.3 s | 7.5 s |

- **Reasoning is the lever.** Errors fall by about two-thirds, in messages (21% to 5%) and notes
  (39% to 9%) alike. That is the first effect on this bench that is not noise, and it is larger than
  everything in §6.4–6.6 put together. The vote misquotes that no layout or instruction moved fell
  from 22 to 5.
- **It reads as better play, not only fewer errors.** The serial killer at minimal asks how to tell
  "the wolf versus the killer" when both wolves are dead. At medium it counts the dead and uses the
  miscount against its accuser. Messages are the same length (median 42 and 41 words), mention
  votes about as often, and more of their statements are checkable (143 against 129).
- **The cost is about 2.4× per turn and 3.3× the time.** Reasoning tokens are billed as output.
  Over a game that is roughly $0.27 to $0.65 if every turn reasons, and about 5 seconds more per turn.
- **The pinned cases barely moved** (9 to 8 of 15). They are judged by the golden judge, which §6.5
  already found unreliable, so this says more about that judge than about the pinned cases.
- **What this does to §6.4–6.6.** Every comparison there ran at minimal, with no reasoning. They
  measured layout and wording for a model that wasn't checking anything, which may be why they
  stayed within noise. They are not re-run here.
- **It reaches past this bench.** Every memory experiment (the June static A/B, the v7 loop runs, the
  v7 endpoint) also played its games at minimal on 3.1 flash-lite. The scope this puts on their
  verdicts is recorded in `evidence/credit/blindspot_fix/experiment_log.md` §⑦.

*Run: `evaluation/config/template/hallucination_bench_thinking.json`; output
`evaluation/eval_results/hallucination_bench/thinking_flashlite35/` (not tracked). The minimal arm
could have reused the earlier v4 arm's generations (same code); it was regenerated to record its
tokens.*

**The cheaper reasoning model: `gemini-3.1-flash-lite` at "low".** 3.1 does reason at low (1,024),
and its tokens cost less ($0.25 / $1.50 per million). One arm was added to the same run, with the
same summaries and the other two arms' verdicts reused:

| | 3.5, minimal | 3.5, medium | 3.1, low |
|---|---|---|---|
| All samples bad | 82/267 (31%) | 27/267 (10%) | 39/267 (15%) |
| Curated | 53% | 13% | 26% |
| Messages: bad / checkable | 21% | 5% | 15/130 (12%) |
| Notes: bad / checkable | 39% | 9% | 25/145 (17%) |
| Bad messages that mention a vote | 22 | 5 | 12 |
| Median message length | 42 words | 41 words | 61 words |
| Reasoning tokens per turn | 0 | 1,365 | 820 |
| Cost per turn | $0.0025 | $0.0059 | $0.0032 |
| Time per turn | 2.3 s | 7.5 s | 6.2 s |

- **It halves the errors at almost no extra cost** (15% against 31%; 32 cases better and 6 worse,
  p < 0.0001), for 1.3× the cost per turn.
- **It is behind 3.5 at medium** (15% against 10%), though not significantly at this size (12 cases
  better and 19 worse, p = 0.28). It is barely faster (6.2 against 7.5 seconds), since it reasons too.
- **Its messages are longer** (median 61 words against 42), and the owner's earlier reading put 3.5's
  dialogue clearly above 3.1's (`evidence/model_selection/report.md`). Neither was re-judged here.

The bigger Flash models are no cheaper route to reasoning. A two-turn probe each found
`gemini-3.5-flash` and `gemini-3.6-flash` reasoning even at minimal (about 600–1,100 tokens, past
the 128-token budget), but at $1.50 per million input tokens a turn costs about $0.016–0.020:
three times 3.5 flash-lite at medium, and slower.

---

## 7. Phase 2 plan: how the day runs (started 2026-10-07; build order in §7.4)

Phase 2 changes how a day is run: the engine's turn-taking, plus the events and stage scenes that show
it. The owner writes the code and Claude writes the tests; this section is the brief.

### 7.1 What the game records say (2026-10-03)

Before building anything, the June games (28 games, 96 voting days) and the website games (9 games,
26 voting days) were checked for the problems phase 2 is meant to fix. These are counts from the
records, with no model involved, except the last row.

| Question | June games | Website games |
|---|---|---|
| Day 1 ended after the first three players passed, with nothing said | 28 of 28 | 8 of 9 |
| Voting days where a living player was never offered a turn | 8 of 96 | 3 of 26 |
| Voting days ending on three passes / on the message cap | 71 / 25 | 14 / 12 |
| Days ending with an accusation still unanswered (all on capped days) | 10 | 10 |
| Investigator holding a result: turn it was first offered (median) | 4th | 4th |
| ... and days it was never offered a turn at all | 1 of 82 | 3 of 18 |
| Lynched player was among the day's most-accused | 61 of 67 | 18 of 20 |
| Days with a player accused by at least two different players | 54 of 96 | 17 of 26 |

- **Day 1 is usually empty.** The scheduler ends a day after three passes in a row, and on day 1
  almost everyone passes, so the day ends after three players. The other six, often including the
  human, are never offered a turn.
- **The same rule cuts some voting days short.** Every voting day that missed a player was one where
  the first few players passed and the day ended; two website days had no messages at all.
- **The investigator is not usually kept waiting.** Its first turn comes around the fourth turn of the
  day. What an opening round adds is the guarantee: it is asked at the start of every day, including
  the days it would otherwise never be asked.
- **A closing defence needs a different trigger.** The scheduler always lets an accused player reply
  before the day can end on passes, so an "unanswered accusation" exists only on days that hit the
  message cap. "Most-accused" works better: the lynched player was among the most-accused on almost
  every day, so it picks the players the vote is really about.
- **The accusation tags are good enough to count with.** Each message records whom it accuses; the
  speaker fills this in with its own output. On the 183 agent messages the evidence judge read, the
  tags named the same accused player (or none) as the judge on 145 (79%). On 24 (13%) the tags missed
  an accusation the judge saw; only once did a tag name an accusation the judge did not. Counts of
  accusers may run slightly low, but rarely high.

### 7.2 What to build

**No switch.** Phase 2 is built as the new default. Before merging it, the last commit without it
gets an annotated tag (`git tag -a phase2-baseline`), per the repo's rule for structural changes
compared once; the v2 games already played are the comparison. If it plays worse, revert to the tag.

**The day becomes:**
- *Day 1:* opening round → summary → night. No discussion after the opening and no vote.
- *Day 2 on:* opening round → discussion (today's scheduler, unchanged) → closing defence → summary →
  vote.
- *Revised 2026-10-07 (§7.4 step 4b):* from day 2 the discussion's proactive picks become a
  parallel proactive round between the reactive chains; the scheduler keeps the reactive queue only.

**D1/S1. The opening round: everyone at once.** Every living player is sent an opening turn at the same
time, the way the vote is. The instructions are strict: the only things allowed are a role claim
(or a counterclaim), one's own night action or result, or a challenge to an earlier claim with a
reason. Deductions wait for the discussion, where they can answer today's claims. Anything else is a
pass, and passing is the default. The stage shows "everyone is preparing their opening" while the calls
run, then plays the openings that were made one by one in a seeded order, with the passes as one line.
- *Why at once:* a round of mostly passes played one seat at a time is close to a minute of "player_x
  passes" before anything happens. At once, the wait is about one model call.
- *Why this is safe now, when simultaneous openings were rejected before:* the earlier simultaneous
  turns were open statements, and came out near-identical. These are restricted to private facts and
  claims, and a filter afterwards removes everything else (below).
- *Responses come from the existing scheduler.* Opening messages go into the transcript with their
  accusation tags like any message, so a player named in a claim ("I checked player_5: wolf") is
  first in the reply queue when discussion starts. No new summariser or planning step. If the tags'
  misses (§7.1) turn out to matter, an LLM step can be added later.
- *Cost:* one call per living player per day for the opening (day 1 today makes three).

**The opening filter: one call, an allow-list.** Agents often speak when told to pass, so the
instructions need a backstop. After the openings are collected, one cheap call sees all of them in
the seeded order and labels each with what kind of statement it is. It keeps only the allowed kinds:
- a role claim, or a counterclaim to an earlier one;
- the speaker's own night action or result;
- a challenge to an earlier claim, with a reason.

Everything else becomes a pass: general advice, padding (*"good that the healer protected player_2;
now let's look at the voting records"*), and deductions. The call also drops a repeat of an earlier
opening, except a claim: two players claiming the same role is a counterclaim, the contest phase 1
wants. It judges only the kind of statement, never whether it is true, so a fake claim is kept.
- *Why an allow-list and not the echo filter:* "is this one of these kinds?" is a steadier question
  for a cheap model than "is this new?", and it enforces what the opening is for.
- *Failure:* verdicts are keyed by player, not position; a missing verdict or an error keeps the
  opening, as the echo filter keeps a message when it errors. Human openings are never filtered.
- *The kind label is recorded* on the entry for analysis (observer only).
- *Deduction left out for now.* If openings turn out too thin, a very strict deduction rule (names a
  player and cites a specific night fact, not already made) can be added.
- The mid-day echo filter is unchanged.

**S2. The closing defence: the most-accused, at once.** When discussion would end (passes or cap), the
one or two players accused by the most different players today, with at least two accusers, get one
last turn, sent at the same time, through the same mechanism as the opening. No new accusations;
anything they say gets no reply. If nobody qualifies, the day goes straight to the summary.
- *The moderator announces the closing, written by code, with no model call:* *"Before the vote:
  player_5 has been accused by player_2, player_4 and player_7; player_8 by player_1 and player_3.
  Each gets a last word."* The names come from the accusation tags, so it costs nothing and cannot
  misstate anything (it can miss an accuser the tags missed, §7.1). It tells everyone, the human
  and viewers included, who is on trial and who is pressing; the reasons are already in the
  transcript, which the accused agents read in full.
- *Not a model-written summary of the case.* The moderator's lines are taken as fact by agents and
  humans alike, so a summary of opinions in its voice would turn any mistake into a "fact" and read
  as the game endorsing the case. Considered and dropped: a closing turn for each accused player's
  top accuser before the defence (adds two calls and gives a pushing wolf one more prominent turn).
- *Ties:* the more recently accused player first.
- *Don't use the agents' private suspicion reads* to pick the accused. Who gets a closing turn is
  public, so it would leak what the agents secretly think.

**S3. Lengths per turn type.** Opening: one or two sentences, or pass. Closing: two to four sentences.
Discussion keeps the P5 line. Humans keep one limit.

**Where each piece goes:**
1. **Day graph** (`Agents/graphs/day.py`). New steps on the vote's pattern (`START_VOTING` →
   `fan_out_vote` → `vote` / `vote_human` → `COLLECT_VOTES`): one sends the round out, then the
   per-seat turn node (cached for agents, with an uncached twin for the human, for the same resume
   reason as the vote), then a collecting step. The same steps serve the opening and the closing,
   given which round it is. The day starts at the opening instead of `SCHEDULE`; `route_speaker`
   (`Agents/nodes/day/flow.py:57`) goes to the closing instead of the summary when the day would end;
   day 1 goes from the opening straight to the summary.
2. **Turn payload.** `fan_out_day(state, "discuss")` (`flow.py:198`) already builds one discussion
   Send per survivor; add the round (`opening` / `closing`) to the payload. The prompt reads it, as it
   reads `voting_available` for day 1 today.
3. **Collecting step.** The parallel turns must not write into `day_channel` themselves (each would
   claim the same position). They return their candidate lines to a holding field; the collecting step
   orders them by the day's seed, runs the opening filter (opening only), and writes the speeches
   and pass markers into `day_channel` in sequence.
4. **Opening filter** (new, beside `Agents/turn/novelty_agent.py`): one prompt and an output schema
   with one verdict per speaker (player, kind, keep), every field required (flash-lite fails on
   optional fields). The output schema is model-visible: field descriptions, no class docstring.
5. **Closing speakers and announcement.** A small helper: for each living player, the set of
   different players who tagged an accusation against them today (`addressed_targets`, stance
   `accusation`, not themselves); keep those with at least two; sort by count, then latest
   accusation; take two. The collecting step's partner at the start of the closing writes the
   announcement from the same sets as a `game_master` line in `day_channel`, so agents, the summary
   and the replay all see it.
6. **Prompts** (`Agents/prompts/day_discuss.py`, `prompt_inputs.py`): an opening block and a closing
   block, chosen by the round in the payload, carrying S3's lengths. The day-1 block
   (`OPENING_NO_VOTE_DISCUSSION_RULES`) merges into the opening block. The golden in
   `tests/fixtures/day_discuss_prompt_golden.json` changes on purpose.
7. **Server events** (`server/game/translate.py` and `server/schemas/events.py`): the new steps need
   translator entries, and the scene needs a public event marking "openings are being prepared" (for
   example a new `phase_change` value). Both change the event contract the frontend reads, and the
   translator's exact goldens. The closing announcement reaches the frontend as an ordinary moderator
   line, as long as the new step's translator entry emits `day_channel`'s moderator lines
   (`_gm_messages`, as the existing day steps do).
   - *Knock-on for the hallucination bench:* its builder drops every same-day moderator line from a
     replayed vote turn (the vote-result leak fix). After phase 2 that would also drop the closing
     announcement, which a voter really did see. It should drop only the lines posted after the
     votes. This only matters once phase 2 games are added to the bench.
8. **Frontend** (`frontend/src/stage/beats/beatsFor.ts`, `frontend/docs/beat_sheet.md`): the
   "preparing" scene, the openings played in order, and a run of passes shown as one beat. Grouping
   consecutive passes also shortens today's mid-day passes.
9. **The human seat.** In the opening the human gets an ordinary turn request, in parallel with the
   agents. The vote's known delay applies (§9 item 5): the human's request appears only once every
   agent's call has finished. Here that is hidden by the "preparing" scene, but fixing it for the vote
   fixes it here too.
10. **Tests** (written by Claude once the code is in): day 1 is the opening only; every living player is
    sent exactly one opening turn; openings land in `day_channel` in seeded order with distinct
    positions; the opening filter drops padding and a repeat, keeps a counterclaim, and keeps everything when its call fails; a player named in an opening
    accusation replies first in discussion; the closing announcement names exactly the accusers the tags record; the closing runs after passes and after the cap, picks by
    distinct accusers, is skipped when nobody has two, and gets no replies; the translator emits the
    new events.

### 7.3 How to tell whether it worked

Play two or three games on `gemini-3.5-flash-lite` (the baseline's model), judge them, and compare
with v2 game 1 (`832404e9`):
- what the openings contain: how many players speak, whether evil uses them to claim, and whether
  counterclaims appear;
- whether the opening feels slow: how long it takes, and how the "preparing" scene and grouped passes
  play;
- how often a closing defence runs, and whether the defended player is still voted out;
- calls per day (the cost);
- the judge's turn-taking and reveal-timing labels.

*Counts: one-off scripts (not kept), run 2026-10-03 over the 28 June batch
records and the website replays (9 games: `8e26fd3b`, `832404e9`, `500b5167`, `7bdb16bd`,
`553a1875`, `35e3677c`, `965b8148`, `9369a5c1`, `ff26faff`).*

### 7.4 Build order (2026-10-07)

Phase 2 started on 2026-10-07. The owner writes the code, step by step, after a few months away
from hand-coding; Claude reviews each step, and the tests (§7.2 item 10) are written after a step
lands, not before. Each step names what to read first and what to change. A game is playable after
step 4. Three choices this order makes for the brief, open to objection:

- The engine marks a round on the transcript entry (`DayChannel.day_round`, and `opening_kind`
  from the filter), not through new `FiringReason` tiers. The firing reason stays the scheduler's.
- The wire gets one new public event, `round_opened` (the round and its players). Passes in a
  round are derived on the stage as "players of the round with no speech", so there is no new
  pass event and the X-ray's `pass_marker` is unchanged.
- The opening's lines are collected in plain seat order (owner, 2026-10-07: nobody saw anyone
  else's line, so the order is only for the reader; a seeded shuffle was not worth a seed).

**Step 0. Housekeeping, no Phase 2 code.**
- Tag the baseline before anything lands: `git tag -a phase2-baseline 84328b79` (annotate with the
  backend and model: Vertex, `gemini-3.5-flash-lite`).
- The uncommitted role edits in `frontend/src/stage/roles.ts`, `paint/materials.ts` and the token
  files (the eight 1920s roles) are Phase 3 work. Commit them on their own first, so no Phase 2
  commit carries them.
- Deploying the 2026-10-06 batch is independent of all this; do it whenever.

**Step 1. The closing-speaker rule (pure code; the warm-up).**
- Read: `Agents/schemas/game_events.py` (`DayChannel`, `AddressedTarget`), `Agents/rules/seats.py`
  and `Agents/rules/claim_ledger.py` (the shape of a rules helper: deterministic, no model).
- Write: `Agents/rules/closing.py` with two functions. `closing_speakers(day_channel, current_day,
  surviving_players)` returns up to two `(player, accusers)` pairs: over today's spoken,
  non-moderator entries, each `addressed_targets` item with stance `accusation` whose target is a
  living player other than the speaker counts one accuser; keep targets with at least two distinct
  accusers; sort by count, then by the latest accusing `seq`; take two. `closing_announcement(pairs)`
  renders the moderator line from §7.2 S2 ("Before the vote: player_5 has been accused by player_2,
  player_4 and player_7; ... Each gets a last word.").
- Review: the tie rule, the self-accusation filter, the accuser order inside the line.

**Step 2. The round rides the payload; the prompts read it.**
- Read: `Agents/nodes/day/flow.py` (`build_speaker_send`, `fan_out_day`: the two payload builders,
  the leak boundary), `Agents/state/day.py` (the payload TypedDicts), `Agents/prompts/prompt_inputs.py`
  (`build_agent_prompt_input`, the `discussion_stage_rules` key), `Agents/prompts/day_discuss.py`
  (`OPENING_NO_VOTE_DISCUSSION_RULES`, `TONE_INSTRUCTION`, `_discuss_template`).
- Write: a `day_round` payload key (`opening` / `discussion` / `closing`, default `discussion`) in
  both builders, with a `day_round` parameter on `fan_out_day`, and the field documented on the
  payload TypedDicts. In `day_discuss.py`, `OPENING_ROUND_RULES` (the allowed kinds from §7.2, one or
  two sentences, passing is the default; the day-1 no-vote sentence folds in, so
  `OPENING_NO_VOTE_DISCUSSION_RULES` goes away) and `CLOSING_ROUND_RULES` (S3: two to four sentences,
  no new accusations, nobody replies). `prompt_inputs.py` picks the block by `day_round`, with
  `voting_available` only choosing the day-1 sentence. `DayDiscussOutput` is unchanged: `pass_turn`,
  `message` and `addressed_targets` are what a round turn needs.
- Then regenerate the golden (`poetry run python -m tests.fixtures.day_discuss_prompt_golden`) and
  read its diff: for the existing discussion board nothing should move but the stage-rules block.
- Review: the two prompt blocks (wording is the epoch bump), the default so nothing else changes.

**Step 3. The round's nodes: fan out, turn, collect.**
- Read: `flow.py` again for the vote's pattern (`start_voting`, `fan_out_vote`, `collect_votes`),
  `Agents/nodes/day/actors.py` (`discuss`, `DiscussDelta`), `Agents/turn/resolve.py` lines 60-150
  (`seq` is counted from the payload's channel, so every parallel turn would claim the same
  position: that is why the collector re-numbers), `Agents/turn/human_turn.py`
  (`announce_human_turn`, `_PHASE_INSTRUCTION`), `Agents/graphs/parent.py` `day_phase` (the day
  state is rebuilt every day and only four keys come back, so a holding field never reaches the
  parent).
- Write, in `Agents/schemas/game_events.py`: `RoundCandidate` (day, round, entry), internal, attribute
  docstrings; `DayChannel.day_round` (default `discussion`). In `Agents/state/day.py`: `day_round: str`
  and `round_candidates: Annotated[list[RoundCandidate], add]`. In `flow.py`: `start_opening` sets
  `day_round`; `start_closing` sets it and writes the moderator announcement (step 1) into
  `day_channel` as a `game_master` entry; `fan_out_round` calls `fan_out_day(state, "round_turn",
  day_round=...)`, keeps only the accused for the closing, and announces the human twin
  (`announce_human_turn`, phase `day_channel`); `collect_round` takes the candidates of
  (today, this round), orders them by the seeded seat order, re-numbers `seq` from today's count,
  and writes them to `day_channel` (the filter of step 5 slots in before the write). In
  `actors.py`: `round_turn`, the same engine call as `discuss`, returning `round_candidates` instead
  of `day_channel`. `_PHASE_INSTRUCTION` gets an opening and a closing ask.
- Check: `server/game/game_session.py` finds a seat's paused turn by the task's node name
  generically (`_paused_task`), so the draft endpoint should work for a round turn unchanged; confirm
  while reviewing.
- Review: no parallel node writes `day_channel`; the human twin is the uncached one; the collector's
  order and numbering.

**Step 4. Wire the day graph (a game is playable after this).**
- Read: `Agents/graphs/day.py` (all of it), `flow.py` `route_speaker`, `route_after_day_summary`,
  `discussion_stage_controls`, `Agents/config/langgraph.py` `discussion_recursion_limit`,
  `Agents/nodes/__init__.py` (exports).
- Write: nodes `START_OPENING`, `START_CLOSING`, `round_turn` (cached, the vote's `CachePolicy`),
  `round_turn_human` (uncached), `COLLECT_ROUND`. Edges: `START` to `START_OPENING`; both start
  nodes fan out through `fan_out_round` to the two turn nodes, which join at `COLLECT_ROUND`;
  `COLLECT_ROUND` routes to `SCHEDULE` after an opening on a voting day, else to
  `SUMMARIZE_DAY_DISCUSSION` (day 1, or any closing); `route_speaker` returns `START_CLOSING` on
  terminate when `closing_speakers` is non-empty, else the summary. A fan-out edge must always
  produce at least one Send: the opening has every survivor, and `START_CLOSING` runs only when
  someone qualifies. Day 1 never reaches `SCHEDULE` now, so the pre-voting cap in `route_speaker`
  and `discussion_stage_controls` are dead: delete them here. Two more supersteps per round fit in
  the recursion limit's headroom; say so in its docstring.
- Then play one cheap headless game and read the transcript: day 1 is opening, summary, night.
- Review: the topology against §7.2 "the day becomes", the dead code gone.
- *Played 2026-10-07* (`data/phase2_step4_smoke_game_2026-10-07.json`; flash-lite, memory off,
  no filter yet): villagers won in 5 days, 743 s. Day 1 = nine opening passes, summary, night.
  Days 2–5 each ran opening → discussion → closing → vote, and every voting day produced a
  closing with exactly one accused. The openings were used as meant: the investigator claimed
  with its night-1 result on day 2, the healer and investigator on day 3, the investigator (the
  serial killer found) and a vigilante "held fire" on day 4. Day 2's discussion ran to 36
  entries (the cap), which step 4b's rounds address.

**Step 4b. The proactive round replaces the scheduler's proactive tier (owner, 2026-10-07).**
Decided after step 3, before the graph was wired. On 96 June voting days the scheduler offered
a median 16 turns: 5 reactive, about 10 proactive picks of which 4 passed, and the day ended on
three passes in a row; 5 of about 7 survivors spoke. The proactive tier picks one quiet player at
a time; a round asks all of them at once. The day becomes: opening → reactive chains →
proactive round → reactive chains → (another proactive round while the last one produced a new
line, at most two or three) → closing → summary → vote. The scheduler keeps only the reactive
queue, which is the part that makes a conversation.
- *The risk is the one that ended concurrent discussion in Phase A:* simultaneous open
  statements came out near-identical. The opening escapes it by being restricted to private
  facts and claims; a proactive round does not. So the round gets a filter on the opening
  filter's shape: one cheap call over the round's lines, groups near-duplicate points, keeps the
  first of each group in seat order, turns the rest into passes. A held player is told on its
  next turn that its line was not said (the fidelity audit's finding 2: a suppressed line must
  not survive as a private belief that it was spoken).
- *Test the filter offline first:* take a June day's spoken proactive lines as if said at once,
  run the call, read what it would have held. Runs alongside step 4; no graph change needed.
- *Code:* `select_next_speaker` drops the trailing-pass and proactive steps and terminates when
  the reactive queue is empty (`rank_proactive`, `proactive_budget`, `opener_floor` and the
  proactive novelty-gate path go; the `proactive` tier stays a Literal value for old records);
  `DayRound` gains `proactive`; a `START_PROACTIVE` entry node; `fan_out_round` narrows to the
  players who have not spoken since the last round; a router after the chains picks the next
  round, the closing, or the summary; a proactive-round prompt block carries the engage rule's
  content for a round nobody has seen yet; `test_scheduler.py` is largely rewritten; the
  sequential-discussion study's quality gate is superseded in part (a note there).
- *Order:* step 4 as briefed first (one game shows the opening and closing on the round
  machinery), then 4b, so the comparison games in step 8 measure the whole new day once.
- *Built 2026-10-07 (first half: scheduler reactive-only + the proactive round; no echo filter
  yet).* Smoke game `data/phase2_step4b_smoke_game_2026-10-07.json` (flash-lite, memory off):
  villagers won in 4 days, 305 s against 743 s for the step-4 game, since the quiet players'
  turns now run in parallel. Day 2 ran opening (1 claim, 8 passes) → proactive round (7 lines,
  1 pass) → 1 reply → a second proactive round → 2 replies; day 3 ran two proactive rounds and
  a closing with two accused; day 4 one round and a closing. Two findings: (1) a BUG, the second
  proactive round re-published the first round's lines word for word, because the collector
  picked candidates by round kind and both rounds are "proactive"; fixed the same day by
  stamping each candidate with its round number (`RoundCandidate.round_no`). (2) The echo
  problem is visible as predicted: day 2's seven proactive lines were all reactions to the one
  opening claim, several making the same "convenient timing" point, which is what the second
  half's filter is for.
- *The cap drains instead of cutting (owner, 2026-10-07; built the same day).* The scheduler
  used to check the utterance cap first, so an open accusation or question died when the cap
  hit (the "unanswered accusation on capped days" of §7.1). Now, once the cap-th real utterance
  is in, only debts opened at or before that point are answered, each debtor answers at most
  once more (a reply that fails to tag its creditor cannot re-fire), anything a post-cap reply
  opens is left for the closing, and no proactive round runs. `select_next_speaker`'s drain is
  pure and bounded by the survivors; the recursion limit allows one extra turn per survivor.
- *Second half built 2026-10-07: the echo filter.* `Agents/turn/round_filter.py`: one call per
  proactive round reads the lines in seat order and names, per line, the earlier line that makes
  the same point; the first of each group is kept, the others become `round_echo` pass markers
  that keep the held text, which the existing held-back marker shows to the author on its next
  turn (the fidelity audit's finding 2, already fixed for the novelty gate, covers this for free).
  A human's line is never held. The offline check (`data/round_echo_check/`, runner
  `evaluation/experiments/round_echo_filter_check.py`, final prompt): June pseudo-rounds
  93 rounds, 638 lines, 107 held (17%); the smoke games' real rounds 5 blocks,
  32 lines, 9 held (28%; two blocks are the bug's duplicates). Nearly every hold is
  "X makes a good point about..." followed by X's conclusion. One false-positive class was found and
  put into the prompt: a player's claim about their own role or night action, or confirming or
  denying what was said about themselves, is never a duplicate (the vigilante's "I can confirm your
  read on me" had been held). Ruled the same day: a held line keeps its accusation tags, so two players
  independently accusing the same target for the same reason count as two accusers for the
  closing (`closing_speakers` counts held echoes; the reactive queue skips them, so nobody is
  asked to answer a line that was never shown). Also ruled as built: a drained reactive turn
  gets the ordinary "respond" brief; the first proactive round always runs when anyone is
  silent; a player who claimed in the opening is not asked in proactive round 1 unless addressed.

**Step 4c. The proactive sweep goes sequential; the per-line echo gate returns (owner, 2026-10-07).**
- Decided after reading the step 6 capture: the parallel proactive round generated seven lines to keep
  two in a day's first round, because seven players reading the same board at once reach the same
  conclusion, and the aggregated filter existed only because parallel turns cannot see each other.
  The owner chose the old schedule's shape for the sweep with the per-line gate kept, under the
  step 4b criterion (the same point, not "nothing new"), not the old "adds nothing" one.
- The scheduler gets a proactive tier back (`next_sweep_speaker`): when nobody owes an answer, the
  floor goes to the survivors who have not spoken since the day began, one at a time in seat order,
  each line's chains running before the next player is asked (a reactive debt always outranks the
  sweep). A second sweep goes round those silent since the first began (so a player who spoke only
  in the opening, or whose first-sweep line was held, is asked once more), only if the first
  produced a new line; `GameConfig.max_proactive_sweeps` (default 2). Still stateless: which sweep
  is running and where it began are read back from `FiringReason.sweep` on the proactive entries.
  A sweep turn carries `day_round="proactive"`, so the open-floor rules block and the human's ask
  stay. The cap's drain is unchanged; sweep turns that pass consume no cap, so the recursion budget
  gained a term for them.
- The gate (`Agents/turn/echo_gate.py`, called from `resolve_decision` on a proactive turn by an
  agent): one cheap call judging the new line against the day's spoken lines; a repeat becomes a
  `novelty_gated` pass marker that keeps the text for its author (its accusation tags counted for
  the closing until the step 8 ruling, below), and that the reactive queue skips. Two deterministic exemptions the judge is not
  trusted with: a human seat, and a line tagged as a response to a player whose earlier line named
  the speaker (the "about themselves" rule). An empty sweep line is recorded as a voluntary pass so
  the stateless scheduler does not re-ask at once.
- Gone: `START_PROACTIVE`, the proactive branch of the round nodes, `RoundCandidate.round_no` and the
  payload's `round_no`, `max_proactive_rounds`, the second-round rule in `route_after_discussion`
  (now closing-or-summary only), `filter_round_echoes` with its schemas, the `round_echo` wire value's
  producer (the value stays in the vocabularies for records). `round_opened` is `opening|closing`
  now; the OpenAPI snapshot and frontend contract were regenerated. The parallel design is tagged
  `phase2-parallel-proactive` (f6d539b6) for a one-shot comparison if wanted.
- Offline check of the gate (`evaluation/experiments/line_echo_gate_check.py`, replacing the round
  filter's runner; results and lineage in `data/line_echo_check/README.md`): on the first 20 June
  voting days the first prompt held 29% of lines the old gate had kept, and reading them showed the
  small judge treating "player_5 is right that..., so let's also..." as a repeat of player_5. Spelling
  the criterion out changed little (27%); restructuring the verdict so the judge states what the
  line adds before it may name a repeat, with the code holding only when it adds nothing, brought it
  to 18%, about half of them clear repeats on reading. A small judge errs toward holding; step 8
  should count held and restated lines per day before tuning further.
- The live game under this shape (the recaptured chunk catalogue, played under the first prompt):
  3 days, serial killer won, 244 chunks in 289 s. Sweep turns 16 (day 2: 7 in sweep 1, 2 in sweep
  2; day 3: 5 and 2), 6 held, 10 spoken, with reactive answers landing between sweep turns the way
  the old schedule did; closings on both voting days. Openings: 1 spoken line in 22 turns (the
  investigator's result on day 2), the rest voluntary passes, as in the parallel game. One hold was
  a player denying they led a lynch, which the response-to-my-accuser exemption now covers.
- Read in full (owner's question, 2026-10-07): the cap never bit (9 of 24 real lines on day 2, 8 of
  15 on day 3); the days ended because the sweeps ran out. Each day was one topic (player_4's claim;
  who pushed that lynch), coherent but narrow, and the best rebuttal of day 2 (night actions are
  simultaneous, so a check on a player who then died is normal) drew no reply because its tags
  opened no debt (§9.8 again: the chains are starved by tagging more than by the cap). The holds
  were genuine repeats. The second sweep re-asked the two players held in the first and they
  repeated themselves again (four calls, nothing kept), so a player held by the gate is no longer
  asked again that day (owner ruling). Levers kept in view, not pulled: how easily a reactive
  chain opens (a defence that re-engages the accuser, tag accuracy), the gate's strictness (would
  buy repetition while the holds are genuine), and the open-floor prompt's "one most useful point",
  which makes every sweep speaker pick the same hottest topic.

**Step 5. The opening filter.**
- Read: `Agents/turn/novelty_agent.py` (the shape to copy: one prompt, `get_llm_judge`, fail open),
  `Agents/schemas/output.py` (`NoveltyJudgment`; the model-visible rule: `Field(description=)`,
  no class docstring, every field required because flash-lite fails on optional ones),
  `Agents/prompts/prompt_formatters.py` (`format_day_channel`).
- Write: `Agents/turn/opening_filter.py`, `filter_openings(entries, day)`: one call over the openings
  in order; output `OpeningVerdicts` with one `OpeningVerdict` (player, kind, keep) per speaker, kind
  in claim / counterclaim / own_night_action / challenge / repeat / other; verdicts keyed by player;
  a missing verdict or any exception keeps the entry; a dropped entry becomes a pass marker with a
  new `DiscussionPassReason.OPENING_FILTERED`; a human's entry is never sent to the filter; the kind
  is recorded on the entry (`DayChannel.opening_kind`). `collect_round` calls it for the opening only.
- Review: the prompt judges the kind of statement, never its truth; the schema is all-required.
- *Built 2026-10-07*, beside the echo filter in `Agents/turn/round_filter.py` (one module for the
  filters a collected round goes through, sharing the held-marker mechanics): kinds claim /
  night_action / challenge kept, repeat / other held as `opening_filtered` pass markers with the
  text kept for the author; the kind is recorded on the entry (`DayChannel.opening_kind`). Checked
  offline on the two smoke games' 13 real openings (all kept, labelled as expected) plus one
  planted padding line (held as other). Held lines of either filter are skipped by the reactive
  queue; their accusation tags stay on the marker for records only (the code never counted the
  opening filter's holds for the closing, and since the step 8 ruling it counts no held line).

**Step 6. The wire: events and the translator.**
- Read: `server/schemas/events.py` (`PhaseChange`, `PassMarker`, `InputRequest`),
  `server/game/translate.py` (the `node` registry, `_discuss`, `_start_voting`, `_turn_tick`,
  `_input_request`, `_gm_messages`), `tests/fixtures/translator_golden.py`,
  `tests/server/test_event_schema_contract.py`, `test_openapi_snapshot.py`, and the chain in commit
  `1c137c16` (the frontend's generated contract).
- Write: `RoundOpened` (round, players) in `events.py`; `opening_filtered` on `PassMarker.pass_reason`;
  the round on `InputRequest` so the composer can label the ask. In `translate.py`: `START_OPENING`
  emits `round_opened` for the survivors; `START_CLOSING` (writes `day_channel`, `day_round`) emits
  the moderator line through `_gm_messages` and `round_opened` for the accused; `round_turn` and
  `round_turn_human` (writes `round_candidates`, `agent_strategies`) emit strategy updates only;
  `COLLECT_ROUND` (writes `day_channel`) emits the entries with `_discuss`'s loop, factored into a
  helper both use. Every node the graph has must be registered, or the translator raises.
- Regenerate the OpenAPI snapshot and the frontend contract. The translator goldens replay captured
  chunks with no rounds in them, so capture a Phase 2 game into the fixture catalogue before trusting
  them (see `notebooks/fixtures`).
- Later, when Phase 2 games enter the hallucination bench: `evaluation/src/data/builders/
  hallucination_bench.py` line 115 drops every same-day moderator line; it should drop only the
  lines after the vote, so the closing announcement stays.
- *Built 2026-10-07.* The round's players became a state field, `round_players`, written by the
  round's entry node (seat order for the opening, the silent players for a proactive round, the
  accused as called for the closing); `fan_out_round` sends to exactly that list and
  `collect_round` plays the lines in that order, so the three places that used to recompute the
  list agree by construction, and the translator reads it off the entry node's chunk (it reads
  nothing else). `round_opened {round, players}` is public; the entry nodes emit it (START_CLOSING
  after its moderator line). The human's ask carries its round: `fan_out_round` passes
  `day_round` into the early announcement, `HumanTurnRequest` carries it on the interrupt, and
  `input_request.round` is set for a discuss ask (None for every other kind). The bench builder
  keeps a same-day moderator line when its `day_round` is `closing`. OpenAPI snapshot and the
  frontend contract regenerated; the frontend typechecks (the fold's default case records
  `round_opened` as an unknown type until step 7 handles it).
- *The captured game.* `notebooks/fixtures/chunk_catalogue_phase2.jsonl`: one AI-only game on
  the default slate, memory off, streamed the production way. First captured under the parallel
  proactive round (299 chunks, 311 s, villagers on day 4): the opening round was nearly silent (1
  spoken opening in 26 turns over 4 days), the first proactive round of a day was held hard by the
  echo filter (5 of 7 on day 2, 4 of 6 on day 3), and the closing fired once. Reading those held
  lines (all but one genuinely the same point, made by seven players reading the same board at
  once) is what led to step 4c; the catalogue was then recaptured under the sequential sweep (244
  chunks, 289 s, serial killer on day 3; a vote turn ran on the rescue model after a 429). The
  2026-08 catalogue stays, since the index-pinned spot checks and the session suites' FakeGraph
  are built on it; the translator now has a third golden (`translator_golden_phase2.jsonl`, 317
  events) and the scripted human path was rewritten to the day with rounds (two humans in the
  opening round: the early announcement, the interrupt, the cached siblings' re-stream, the
  uncached twin, then a reactive chain).

**Step 7. The stage.**
- Read: `frontend/docs/beat_sheet.md` §2, `frontend/src/stage/beats/beatsFor.ts` (the
  `turn_started`, `phase_change`, `speech`, `pass_marker` cases), `frontend/src/game/types.ts` and
  `foldEvents.ts` (where the new event folds), `frontend/docs/frontend_lessons.md`.
- Write the beat sheet rows first, then the code: `day.opening-prepares` (on `round_opened`
  opening, "everyone is preparing their opening", held until the round's first speech or the next
  event), each opening as `day.speech`, `day.round-passes` (one beat for the round's players with no
  speech), `day.closing-called` (the moderator line with the accused on the stand), and the
  composer's label for a human's opening or closing turn. Grouping a run of mid-day passes into
  one beat is the same beat. Then the Playwright benches.

**Step 8. Tests, then play.**
- After each step is reviewed, Claude writes its tests from §7.2 item 10 (`tests/engine/`,
  `tests/server/`), plus a `tests/leak_test.py` check that the round payload is built by
  `fan_out_day`, so private fields stay gated.
- Then §7.3: two or three games on `gemini-3.5-flash-lite`, judged against `832404e9`.
- *Built 2026-10-07* (an Opus subagent wrote the tests and played the games; reviewed): 81 new
  pytest cases (`tests/engine/test_{sweep,closing,opening_filter,echo_gate,day_rounds,
  round_payload_leaks}.py` plus cases in the translator, announcement, prompt, fallback and bench
  tests; 1259 passing) and 16 vitest cases (the round beats, the fold's rounds, the dock heading,
  the seat capitalisation; 1089 passing). Four bugs found and fixed the same day: the stage closed
  a round at the human's ask, which arrives before the round's lines; a turn that failed every
  attempt lost its round; the leak check's wolf output keys lacked `wolf_vote`, so every game
  reported a false leak; an orphaned docstring in `DayChannel`. Four games on flash-lite, memory
  off, 380–494 s and $0.34–0.55 each, about 30 calls a voting day: `data/phase2_step8_games/`
  (README, `counts.md`, the judge's reads, `report.md`). The reading: the mechanics work as
  designed and the cap never bit; the opening produced no contest (5 of 106 opening turns spoken,
  only the investigator and the vigilante, no evil claim, no counterclaim); the closing changed no
  vote (7 of 7 defended players lynched); the gate still errs toward holding (about 12 of 19 holds
  clear repeats) and once held an accused player's own defence because the accusations against
  them were untagged (§9.8 again); the moderator named accusers whose lines had been held.
- *Ruling 2026-10-07:* **held lines count for nothing in the closing.** `closing_speakers` counts
  spoken lines only; the tags stay on the marker for records.
- *The investigator finding.* In every Phase 2 game where the investigator claimed in a day 2
  opening it was lynched that day (games 1 and 4 and the step 6 capture, 7–1 each time), where the
  June games had 1 such lynch in 18 day 2 claims. Read in full, the chain is: (1) **seat 1 draws
  every night 1 action.** The night prompts list the survivors in seat order and nobody has a read
  yet, so the first name is picked: over the 28 June games the investigator checked `player_1` on
  night 1 in 21, the serial killer hit it in 26, the wolves in 20, the healer protected it in 25;
  in the four step 8 games the investigator checked `player_1` in all four. (2) So the
  investigator's first result is about the player most likely to be dead by morning, and the
  opening rule asks it to state that result even when the morning already revealed it: "I
  investigated player_1, the healer" after player_1 flipped healer. (3) Everyone else passes the
  opening, so the sweep hands seven players the same single topic and the open floor asks for "a
  contradiction you noticed": seven versions of "a convenient claim", held or not. (4) The
  closing named three to six accusers, held lines included. (5) The vote asks for the most
  suspicious player and the only name on the table is the investigator's; its defenders voted
  with the rest ("drawing universal suspicion and a massive bandwagon" was the healer's own stated
  reason in game 4). The June game with the same claim on a dead player (`228eb3f8`) ended the
  same way, 6 votes, but there it was one claim in eighteen; the rounds made it three in three.
  Levers, not pulled (owner to rule): the night prompts' target list (shuffled or without a
  fixed first name; a prompt-input change, so an epoch), an opening rule that a result the
  morning already made public is not worth an opening, and the vote's "most suspicious" ask
  when one name is on the table.

### 7.5 Two prompt biases found by the step 8 games (2026-10-07)

Two things in the prompts, not in the design, decided who was picked whenever the agents had no
reason to pick anyone. Both were invisible in a single game and plain across thirty.

**1. A fixed list order: everyone picks the first name.** Every prompt listed the survivors in
seat order (made deliberate on 2026-10-06, when the wolves-first order had leaked the faction).
On night 1 nothing distinguishes the seats, and a model with no reason takes the first name it
reads. Over the 28 June games the investigator checked `player_1` on night 1 in 21, the serial
killer hit it in 26, the wolves in 20, the healer protected it in 25; in the four step 8 games the
investigator checked `player_1` in all four. The wolves' chat shows the mechanism in words: "any
thoughts on player_1 or player_2?", "player_1 sounds like a reasonable target, keeping things
standard". Consequences: the investigator's first result is about the player most likely to be
dead or revealed by morning (the lynch chain of §7.4 step 8); in June the healer's seat 1 habit
saved most night 1 kills, so night 1 almost never killed; a human dealt seat 1 is the night 1
target in most of their games.

**2. A seat named in the response example: the example player is picked.** Every JSON example
in the night and day prompts carried one sample read, `{"player": "player_2", "why": "pushed the
only counted lynch with no evidence", ...}`. When the investigator did not pick seat 1 it picked
seat 2 all 7 times; the serial killer's two exceptions were seat 2; on day 2 across the 32
games `player_2` drew 40 accusation tags and 41 votes against a median of about 8 and 12 for
the other seats (the lynch count over whole games is spread, so the day corrects itself later,
but day 2 leans on the example). The example was meant to show the shape of a read; the model
read it as a hint.

**Settled (owner's rulings, 2026-10-07), in two steps.** The first fix was a seeded shuffle of
every player list per agent (the human's board kept in seat order), on the reading that the model
took the first name it read. Checked offline before any game (`data/night1_target_bias/
results_order_check.jsonl`, 192 calls: night 1 of the investigator, the healer and the serial
killer on 32 recorded boards, seat order against the shuffle), it was wrong: with the lists
shuffled the first name shown was seat 1 in 1 to 9 of 32 calls per role, and the target was
still the lowest-numbered other seat in 95 of 96 calls (94 of 96 in seat order). Every actor in
seat 1 took seat 2, whatever was shown first. **The model follows the number, not the order:**
ordinal ids are an order in themselves, and with nothing to go on it takes the smallest. The
shuffle was taken out again (the owner: simpler to remove what made no difference) and replaced
by **a default drawn by lot on night 1 only**: the engine draws a seat per game, night and player
(`Agents/prompts/prompt_inputs.night_one_lot`, seeded like the role draw; the game id rides the
prompt payload from `Agents/turn/pipeline._with_game_id`), and the night prompt of the
investigator, the healer and the serial killer says "Night 1: nothing in the record points
anywhere yet, so a lot has been drawn for you: player_N. Take it unless you have a reason to
prefer someone else." The pack draws one lot, shown in the wolves' chat prompt. The vigilante
draws none (a shot with no evidence is bad play). Nothing on later nights. The example read
names no seat: `"player": "<exact player_id>"`, the wording the target fields already used; no
read copied the placeholder in 192 calls. Both are one prompt epoch (the day-discuss prompt
golden was regenerated on purpose). Checked on the same 32 boards (`data/night1_target_bias/
results.jsonl`, 192 calls, the lot line empty against the lot): without it seat 1 took 78 of 96
night 1 actions and on 16 of 32 boards the check, the protection and the kill all fell on one
player; with it the agents took the lot in 95 of 96 calls, the actions landed on all nine seats
(6 to 16 each) and no board had the three roles on one player.

**The lesson, for every prompt after this.** An example must not name a legal answer, since a
sample value the model can return is a hint however it is labelled; ordinal ids are themselves
an order the model falls back on, whatever order a list comes in; and a choice with no evidence
behind it needs its randomness supplied by the engine, not asked of the model. Measure before
fixing: the first fix here was the obvious one and did nothing.

---

## 8. Phase 3 plan: roles and cast

Phase 3 is the large one. It touches the engine, the prompts, the website and the artwork. §2.5 sets
its target: several imperfect information sources, and a real way for evil to contest them.

*Status 2026-10-07: the owner's role sheet (`role_sheet.md`, dated 6 Oct 2026) is the ruling for
this phase and wins over R1–R7 below where they differ. R1–R7 are kept as the plan of 2026-10-03; the
build order agreed on the sheet is §8.1.*

**R1. Replace the single exact investigator with several narrower observers.** Today the investigator
learns a player's exact role, which concentrates all the certainty in one player. Candidate observers,
each giving a truthful but incomplete fact:

| Role | What it learns | What stays open |
|---|---|---|
| Tracker | "A visited B last night." | Was it an attack, a protection, or an investigation? |
| Watcher | "B received two visitors last night." | Who visited, and why? |
| Comparer | "A and B are / are not on the same side." | Which side? |

The aim is conversations like: *"I tracked Ash to Birch." "Ash claimed to protect Clover." "That
contradicts the claim, but it doesn't prove Ash attacked Birch. Can anyone confirm either visit?"*
- *Trade-off:* every observation needs a short, exact definition. "Visit" in particular must be
  defined so the agents don't misread it, and each new role is one more thing that can be
  hallucinated.

**R2. One way for evil to create ambiguity: a decoy visit.** A wolf may make a harmless visit instead
of carrying out the pack's kill, so a tracker who sees that wolf visiting a survivor cannot clear
them. This creates doubt without the engine ever reporting something false.
- *Alternative held back:* a "framer" whose target shows as evil to an investigation. It is stronger,
  but it makes the engine's own results untrustworthy. Once any result might be faked, every
  contradiction can be explained away, and the game gets harder both to reason about and to measure.

**R3. Public categories instead of a public role list, and no plain villagers.**
- The public list would say "3 town information roles, drawn from these four" rather than naming
  every role in play.
- Every town role would then have a night action.
- Dead players' exact roles stay revealed, which gives the game regular firm facts.
- Games are dealt from a few tested line-ups, not free random draws, so no game accidentally becomes
  a confirmation machine.
- *The coupling:* plain villagers exist partly to give evil believable roles to fake. Remove them while
  every role stays public and checkable, and evil has nowhere to hide. Categories restore that room. So
  removing villagers only works together with categories.

**R4. Ten players to prototype, twelve as the target, and fewer kills per night.**
- Ten is enough to test whether richer evidence changes the conversation. Twelve leaves room for
  overlapping roles and believable false claims.
- Today up to three players can die in one night (wolves, serial killer, vigilante). Information roles
  need several nights to build up results, so a bigger cast with the same kill rate is the same short
  game. Options: no vigilante shot on night one, a serial killer who kills every other night, or one
  fewer killing role.
- *Trade-off:* each extra player lengthens every prompt; twelve players cost roughly 1.6–1.8 times
  as many tokens per day.

**R5. A claim ledger in the day summary.** More roles mean more claims to track across days. The
existing summary already lists role claims. It would add, for each claim, which night it concerns, the
claimed action and result, any retraction, and a short list of open contradictions. The summary's
prose shrinks to match, so total length doesn't grow. A player's own night results stay
engine-written and separate, so they can never be confused with someone else's public claim.
- *Trade-off:* the ledger is written by a model and can misattribute a claim over a long day. If a
  check finds that happening, the claims field can move into the per-message call that already records
  whom each message addresses, at no extra call.

**R6. A last will (lower priority).** On death, a player's private results would be revealed. This was
first proposed to ease the investigator's supposed fear, which the data didn't show (§2.2). It stays as
an option to keep information alive after a death.
- *Trade-off:* written by the engine, it is truthful and can't be forged. Written by the agent, it
  allows wolves to leave fake wills, which is more interesting but adds another surface for invented
  facts.

**R7. New characters for the cast.** About five new character designs, so a 12-seat game draws from a
pool of about 16. They are non-human creatures in the existing felt-and-brass noir style.
- *Mechanics:* new characters are added at the end of the cast list, because reordering it would
  recast every past game. A game loads only the characters it actually casts, so a larger pool adds
  no browser memory. The phone memory check is re-run with 12 seats on screen.
- *Trade-off, the owner's call:* the cast must never hint at a role. Dogs and foxes (shiba, kitsune)
  may read as "the wolf" to a human viewer, even though casting is independent of roles. Good fits
  include pig, robot, lion, unicorn, tortoise and toad. A yeti and a dinosaur would need clearly
  different silhouettes from the existing polar bear and dragon.

### 8.1 The build order (agreed 2026-10-07, on the role sheet)

**What the sheet settles against R1–R7.** The Seer (comparer) is deferred. The decoy visit is dropped;
evil muddies the evidence through the Illusionist's conceal and the Chanteuse's block instead. The
lineup is fixed (10 seats, no plain villagers, the sheet's table), not drawn from public categories.
The investigator becomes a pure wolf detector ("Suspicious" / "Not suspicious"). The claim ledger
already exists (the fidelity pass), so R5 reduces to logging formal claims as actions. Wills (R6) are
replaced by the engine's own disclosure, below. The cast (R7) is a separate track.

**Rulings taken on the day (owner):**
- The vigilante stays as built (bullets and misfire penalty unchanged).
- **No wills. The engine discloses a dead town role's record instead.** When a town player dies and
  the role is revealed, the moderator publishes what that role received each night (its checks,
  what it saw, whom it protected and whether a save happened, where a sigil was placed and what
  came of it) as a public fact, with the reveal and before the next death's reveal. Today the table
  only has the player's own account of those results in the transcript, which can be invented or
  forgotten; the disclosure is engine-written, so it is true and cannot be forged. A concealed body
  (the Illusionist) discloses nothing, which is what makes the conceal matter. *Assumptions to
  confirm:* town roles only; the record is the role's own actions and results, never what the player
  said; the day summary and claim ledger take the disclosure as facts.
- The balance run (about 20 agent-only games, one dial at a time, the sheet's dials) comes **after
  level 2 is built**, not after level 1.

**The order.** Level 1 first; each step is reviewed before the next (the Phase 2 working mode, §7.4).

0. **Record.** This section; the sheet is the design. Open items go into §9 as they appear.
1. **Shared rules as one resolution layer**, before any role card: a per-night visit record (who
   visited whom; the carrier is the only wolf who visits; bets are not visits), attacks collected
   from it, the roleblock applied before actions resolve, night immunity, the morning report by
   attacker type, death reveal with a concealed flag, the dead role's disclosure. Every role card
   then reads from this layer, which is where the token cost is decided.
2. **Ten seats, no villagers**, the sheet's lineup as the casting; the config's required-role checks
   change; a census of the nine-seat assumptions on the stage and in the server.
3. **The investigator's result** becomes suspicious / not suspicious, with the Necromancer's
   attack-night rule left as a hook.
4. **The three cheap town roles:** Sentinel and Trailseer read the visit record; the Sigilist reads
   the attack record (2 sigils, retaliation after the victim dies). One choice per night each; the
   prompt carries uses left and past results, never left to memory.
5. **The wolf skills and the carrier.** Pack chat and the target vote as today, then the carrier
   (rotating by default, overridable in chat, the survivor if one wolf is dead), then one short
   skill prompt per wolf: the Chanteuse's block (town only, same target allowed) and the
   Illusionist's conceal (2 uses, learns the role privately). The main extra-token item: up to two
   more calls a night.
6. **The Speculator:** one private pick by the end of day 2, announced in the next morning report
   without the seat; a fourth winning side in the win logic; "made no choice" when it never picks.
7. **Formal claims and accusations as logged actions**, feeding the claim ledger.
8. **Level 1 tests, then a few games** read in full, as §7.3 did for Phase 2.
9. **Level 2:** the Necromancer (borrowed bodies from night 2, the stealth and trace rules) and the
   Fortune Teller (bets, points, self-bets). Each behind a casting choice, not a flag.
10. **The balance run and the dials**, tracking faction win rates, the day games end, the nights the
    investigator gets results, and how often the Illusionist conceals an info role.

**Frontend.** The stage already names and sides all fourteen roles (`frontend/src/stage/roles.ts`),
and the sigils and faction marks landed on 2026-10-07; the stage work this phase is the ten-seat
census, the new morning-report lines (blocked, concealed, the disclosure), and the night rooms for
the new roles, each as beat-sheet rows first.

### 8.2 The wiring and the first ten-seat games (2026-10-09)

The prompt side (the role cards, the composed rules block, the per-lineup output schemas) and the
wiring landed together on 2026-10-09; the plan and the census of every nine-seat assumption are in
`phase3_wiring_census.md`, the rulings taken on the way in the role sheet's change log. What was
built, in the plan's order: the role registry (twelve roles, four sides; the retired villager and
wolf kept for old records), the deal with the two drawn seats (a solo human's request forces its
draw), one shared night turn behind a named node per role, the pack's night as chat (three rounds,
the carrier first, a pass, an early end on a round of passes) then the carrier's kill then each
wolf's skill, the night resolved once for every role with the public outcome committed as a night
report the wire reads, the four-side win with the neutral's result beside the winner, the day
flow seating every dealt role, the translator and the wire events, and the deletion of the
nine-seat game's templates, schemas, rules and core strategy (the tag goes on the commit before
this one).

Three AI-only games on gemini-3.5-flash-lite, memory off, read in full
(`data/phase3_games/README.md`): the town won all three (days 3, 5 and 4); every mechanic ran as
the sheet says (the sigil's strike, the conceal and the hidden body, the carrier's visits seen by
the sentinel and the trailseer, a will read out, the necromancer acting through three bodies, the
fortune teller's two points, the speculator's pick announced without the seat). The games found
two bugs, fixed before game3: the per-lineup read class was rejected by the turn effects, and a
blocked action spent its use. The leak check passed on all three once the pack's chat was added
to its shared-vocabulary corpus (a chat line had shared its phrasing with another player's read).
Open for the reading pass: the day 1 opening is still thin on claims; the vigilante held fire all
of game3; the lone killer survived to the last votes in every game.

---

## 9. Open questions (as of 2026-10-03)

1. **Does the investigator's certainty, not just evil's silence, flatten the talk?** P3 tests the second
   half with prompts alone. If evil starts contesting claims and the talk is still thin, the exact
   investigator itself (R1) is the next suspect.
2. **How reliable is the judge?** It is unvalidated until the owner's hand-check in §6.
3. **Whether speaking order is ever used as evidence** rests only on a crude keyword count (§2.4). The
   judge's "participation" label can answer it once it separates turn order and silence from the
   timing of a reveal (§6.1).
4. ~~Why the investigator invented a result~~ Answered by the replay (§6.2): the wording of its
   results. The turn is now a seeded case, with a hand-written expectation, in the standing
   hallucination bench (`eval-hallucination-bench`). Still open is how often other private facts are misread the same way. The vigilante's
   shot results are the obvious next place to look.
5. **A human's vote waits on the slowest agent (2026-10-03).** In the first v2 game, the owner's
   ballot was not offered until all seven agents had voted. One agent's call hit two Google timeouts
   and was rescued by the fallback model after about a minute, so the owner waited that minute with
   no vote on screen. The rescue worked as designed. The fix is to offer the human's ballot first
   instead of after the agents' step completes. This is a server and graph change, outside phase 1.
6. **Deferred idea: a public evidence board in place of raw dialogue (2026-10-03).** The owner's
   idea: a summariser keeps a structured board of every player's claims and actions, and agents read
   the board instead of the dialogue, to cut context and hallucination. Measured on the 28 June games:
   - *Where the context goes.* Earlier days already reach agents as summaries; today's dialogue is
     about 15% of a day's input. Most of the rest is the fixed rules and role guidance, read on
     every call.
   - *Cost.* A board updated after every message comes out between +0% and +18% on these games,
     depending on how fast the board grows and how long its update prompt is. That is an estimate in
     characters that ignores output and reasoning, so the claim is only that there is no cost-saving
     case under these assumptions. The one real chance of a saving is a compact claim record
     replacing the earlier days' summaries (about a quarter of a discussion prompt), which needs no
     new calls. A larger cast (phase 3) should be measured, not extrapolated.
   - *What the board would cost in play.* Most messages rest on what someone said (contradictions,
     changed stories), replies need the accuser's words, and a human player would reach the agents
     only through the summariser. One summariser mistake reaches every agent at once.
   - *If taken up:* first a "summary v3": public facts written by code (deaths, revealed roles,
     votes, roles still unaccounted for) plus a running per-player claim record, updated by the
     existing end-of-day summary call, with today's dialogue kept. Test it on the hallucination
     bench, reporting errors per checkable statement as well as per sample (a terser prompt can
     score better just by saying less), then in played games. Per-message updates only if v3 helps
     and dialogue later grows long.
7. **Deferred idea: a rephrasing layer for what humans read (2026-10-04).** The owner's idea: the
   agent decides what to say, and a second small call rewrites the wording to sound more human,
   optionally with a per-character personality. Shape agreed for when it is taken up:
   - *Display only.* Humans see the rephrased line; agents, summaries, the ledger and the bench keep
     the original, so a rephrasing error never enters the game, and it is not a prompt epoch.
   - *Agents keep temperature 1.0.* Gemini 3 is meant to run at its default, temperature 0 is not
     deterministic anyway, and the bench needs the variety. The wording varies through the second
     call, not through the decision.
   - *Facts guarded by code.* The rewrite must keep exactly the original's player IDs, day numbers
     and role words; otherwise the original is shown.
   - *Personas by character, never by role* (the cast-costume rule). The tone instructions could
     move from the agent prompt into the rephraser.
   - *First step:* rephrase messages from existing replays offline, then read them for fidelity and
     naturalness, before any server change.

8. **The accusation and response tags carry more rules than they were measured for
   (2026-10-07).** The reactive queue, the closing pick (§7.2 S2), the proactive round's "who has
   spoken" and the post-cap drain all read `addressed_targets`, which each speaker writes about
   its own message. The only measurement is the one-off census in §7.1 (79% agreement with the
   judge on accusations, 183 messages; misses outnumber inventions 24 to 1), and no standing test
   or eval checks the tags. Candidate: a frozen set of messages with hand-labelled targets, form
   and stance, scored like the other judge cases, so a prompt or model change that degrades the
   tags is caught before it degrades the scheduler.

---

*Sources: census over `batch_results/wolf_sk_mining_p{1..4}/games/*.jsonl` (28 games, commit
`e1a2e3dd`, `gemini-3.5-flash-lite` on Vertex, memory retrieval off); the June prompt audit is
[`generation_prompt/prompt_claims_audit/`](../generation_prompt/prompt_claims_audit/experiment_log.md).*
