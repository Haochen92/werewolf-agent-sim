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

*In progress: one v2 game played and judged so far.*

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

**How to test it.** Rebuild the investigator's exact day-4 prompt from the game record and resample
the message many times: as it was; with the results reworded (*"Night 3 (last night): you
investigated player_5, who is the healer"*); and with the previous note marked as the agent's own
past plan rather than a fact. If the invented claims fall under a variant, that variant is the fix.
It is a cheap offline test on the player model and leaves the live site alone.

---

## 7. Phase 2 plan: the scheduler (not started)

Phase 2 changes the game engine's turn-taking. It does not change the server. Each item is written
down now and taken up one at a time after phase 1.

**S1. An opening round.** Every player is offered one turn at the start of each day before the normal
back-and-forth begins. Passing is the default. The prompt says to speak only to share information that
isn't public yet, or a new deduction from the night's results.
- *Why:* everyone gets a guaranteed chance to put information on the table, and "hasn't spoken yet"
  can no longer mean "is avoiding the discussion".
- *Mechanics:* the current scheduler already favours players who haven't spoken, so it is most of an
  opening round already. Two things break it: replies to accusations jump the queue, and three passes
  in a row can end the day before everyone has been offered a turn. During the opening, replies wait
  until every player has been offered a turn, and passes don't count toward ending the day.
- *Trade-offs:* up to one extra model call per player per day, since a pass still costs a full prompt.
  An accusation made early in the opening waits longer for its reply.
- *Rejected form:* everyone writing an opening statement at the same time, revealed together. Earlier
  experience with simultaneous turns showed they produce near-identical statements.

**S2. A closing defence, only for the accused.** Before the vote, players with an open accusation
against them get one last chance to defend. No new accusations are allowed.
- *Why only the accused:* offering a closing turn to everyone costs one call per player even when they
  all pass, and invites a dozen summaries of the same discussion. The purpose is a last defence, and
  bystanders already state their conclusion through their vote.
- *Open edge:* a human can still type a new accusation in a closing turn. It needs a capped,
  one-reply rule rather than another full round.

**S3. Let the novelty gate tell corroboration from echo.** *"I also saw Ash visit Birch"* sounds
like repetition but is new evidence: a second, independent source. The gate's instructions need to
keep corroborating messages while still skipping plain agreement.

**S4. Separate lengths for opening, discussion and closing turns** for the agents (P5 covers
discussion). Humans keep one limit.

---

## 8. Phase 3 plan: roles and cast (not started)

Phase 3 is the large one. It touches the engine, the prompts, the website and the artwork. §2.5 sets
its target: several imperfect information sources, and a real way for evil to contest them.

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

---

## 9. Open questions (as of 2026-10-03)

1. **Does the investigator's certainty, not just evil's silence, flatten the talk?** P3 tests the second
   half with prompts alone. If evil starts contesting claims and the talk is still thin, the exact
   investigator itself (R1) is the next suspect.
2. **How reliable is the judge?** It is unvalidated until the owner's hand-check in §6.
3. **Whether speaking order is ever used as evidence** rests only on a crude keyword count (§2.4). The
   judge's "participation" label can answer it once it separates turn order and silence from the
   timing of a reveal (§6.1).
4. **Why the investigator invented a result** (§6.2). Hypotheses about the prompt's structure, with an
   offline replay test to tell them apart.
5. **A human's vote waits on the slowest agent (2026-10-03).** In the first v2 game, the owner's
   ballot was not offered until all seven agents had voted. One agent's call hit two Google timeouts
   and was rescued by the fallback model after about a minute, so the owner waited that minute with
   no vote on screen. The rescue worked as designed. The fix is to offer the human's ballot first
   instead of after the agents' step completes. This is a server and graph change, outside phase 1.

---

*Sources: census over `batch_results/wolf_sk_mining_p{1..4}/games/*.jsonl` (28 games, commit
`e1a2e3dd`, `gemini-3.5-flash-lite` on Vertex, memory retrieval off); the June prompt audit is
[`generation_prompt/prompt_claims_audit/`](../generation_prompt/prompt_claims_audit/experiment_log.md).*
