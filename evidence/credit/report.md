# Credit: scoring each lesson by the decisions it was followed at

**Scope:** how the agents' memory scores its lessons from finished games, without an AI judge: how one decision is graded, how grades become a lesson's score, how that scoring was checked, and the July case where it failed and was fixed. It describes the ten-seat code in `Agents/memory/consolidation/`. The nine-seat research loop of July 2026, where the design was built and measured, appears as history and as the case study.
**Revised against the code:** 2026-10-22 at `e765a18e` (the consolidation package has no uncommitted edits). *Note, 2026-10-28:* since then the day-matched baseline (§3) and grading of wolf-chat lessons by the move they are about (§2) were added; the memory tests (325) pass on the working tree; these changes are not yet committed.
**Companion docs:** [the design record](read_tactic_credit_redesign.md) (why beliefs and actions are scored apart) · [the tell report](../extraction/tell_extraction/report.md) (the research-only tell channel) · [the blind-spot log](blindspot_fix/experiment_log.md) (the §6 investigation in full) · [the ten-seat decisions](../memory_system/v8/decisions.md) §12–14 (why the ten-seat rules are what they are).

> **Orientation: one game's path through credit.**
>
> **a game ends → each "I followed lesson X" decision gets a rule's grade → each lesson's grades are compared with memory-off play → lessons that keep doing worse are pruned, lessons doing better are protected, and synthesis sees each well-used lesson's score**
>
> A *lesson* (stored as a *strategy point*) is a short piece of advice for one role in one kind of situation, written by a model from past games. At a decision, an agent is shown the few lessons that best match its situation. For each one it reports a verdict: it followed the lesson, overrode it, or found it not relevant. Credit reads those reports after the game. Everything below hangs on this path.

---

## 1. Why credit exists, and what it never scores

The memory keeps hundreds of lessons: 498 in the ten-seat store when its first credit pass ran. Some help, some do nothing, and some hurt. A memory that cannot tell them apart keeps serving the harmful ones in every game. Credit is the signal that decides which lessons are removed, which are protected, and which are shown as a track record to the model that writes new lessons (*synthesis*).

Two obvious signals do not work.

- **Winning is too blunt.** A ten-seat game runs for several days and nights, and a lesson may be followed at one decision in it. Whether that side won says little about that one decision. Giving every lesson the winners followed a point would reward lessons that happened to ride along with a win.
- **"I followed it" is not "it helped".** The follow report says the agent adopted the advice. It says nothing about whether the advice was good.

So credit grades the decision itself: the single vote, night action or day's discussion at which the agent said it followed the lesson. The grade comes from a fixed rule in code, applied to what the game record shows happened.

Three things in the memory system are deliberately never credited this way:

- **Observations.** These are short accounts of a play and its effect, extracted from finished games by a model. They are the raw material synthesis writes lessons from. Each carries the extraction model's own verdict on whether the play worked. That verdict reaches synthesis but never credit.
- **Read accuracy.** A *read* is an agent's stated suspicion about another player's hidden role. How often reads match the true roles is measured separately, as a property of the agent, not of any lesson.
- **Diagnostic judgments.** An AI judge can rate how persuasive or credible a day's talk was, or whether one message moved another player's suspicion. These help explain results. They never decide which lesson is pruned.

## 2. How one decision is graded

Grading separates two questions. The first is what happened: the decision's target, the role that target turned out to have, and the outcome (the kill landed, the healer saved them, the vote went the other way). The second is what that meant for the player who acted. The same event can be good for one side and bad for another: a town player lynched is a loss for the town and a gain for the wolves. So one step reads the facts from the game record. A separate rule for each role and action turns them into **good**, **neutral** or **bad** for that player. Good counts +1, neutral 0, bad −1.

The rules come from three questions the project owner asked of every role in October 2026: what outcome is ideal for this role, what is neutral, and what is undesirable. Applying them role by role gave four general reasons, which most rows below follow (added 2026-10-28, from [v8 decisions](../memory_system/v8/decisions.md) §12):

- **Grade what the player controls.** Where the outcome was another player's doing, the rule grades the choice. A vigilante who shoots a wolf the healer then saves still made the right choice.
- **A failure the player could foresee is the player's.** The killers must attack someone every night, so their skill is choosing the target. Attacking someone the healer is likely to protect, or a player immune at night, wastes the night.
- **Being seen is a cost.** A kill witnessed by a Sentinel or a Trailseer is bad for the killer, whom the witness can then name in the day.
- **A limited use spent for nothing is bad**: a watch that saw no one, a sigil on someone who did not attack, a conceal on a body with nothing to hide. An Investigator's check on the Serial Killer is bad too: it spends a check and gives the town a false clear.

### The ten-seat rule table

The game deals ten seats from twelve roles, split across four sides (role glosses added 2026-10-28, from [the role sheet](../gameplay/roles/role_sheet.md)):
- the town, six roles:
  - **Investigator**: checks one player at night; wolves read "Suspicious", everyone else (the Serial Killer included) "Not suspicious". Two checks a game.
  - **Sentinel**: watches one player's door at night and learns everyone who visited. Two watches a game.
  - **Trailseer**: follows one player each night and learns whom they visited, or "no one".
  - **Vigilante**: shoots one player at night. Two bullets.
  - **Sigilist**: places a sigil on one player; if that player attacks anyone that night, the Sigilist kills them. Two sigils.
  - **Healer**: protects one other player from attacks each night.
- two wolves, who kill together each night and each have one skill:
  - **Chanteuse**: blocks one player's night action.
  - **Illusionist**: hides the pack's victim's role and night record. Two conceals.
- a lone killer, one of:
  - **Serial Killer**: attacks every night; immune at night.
  - **Necromancer**: from night 2, uses a dead player's night ability.
- two neutrals who bet on others, one of which is dealt:
  - **Speculator**: once, privately picks the side it predicts will win, and wins when that side does.
  - **Fortune Teller**: each night bets on who will die; wins at two points.

The rules below are read from `Agents/memory/consolidation/grading.py`.

**Day votes**

| Who votes | Good | Neutral | Bad |
|---|---|---|---|
| Town (and a Speculator that bet on the town) | votes for a wolf or the lone killer | abstains on a day when someone was lynched | votes for a town player or a neutral; abstains on a day that ended with no lynch |
| A wolf (and a Speculator that bet on the wolves) | votes with the room's largest bloc (abstaining counts as a bloc) | | votes any other way |
| The lone killer (and a Speculator that bet on itself or on the killer) | votes for anyone but itself (or the killer it backs) | abstains | votes for itself (or the killer it backs) |
| The Fortune Teller; a Speculator before it bets | unscored | | |

**Day discussion.** A lesson is graded once per player per day, and only if the player actually spoke on a turn where it said it followed the lesson.

| Situation | Grade |
|---|---|
| The speaker was lynched that day | bad |
| The speaker accused the player who was lynched, on a turn that followed the lesson | good for a wolf, the lone killer or a Speculator that has bet; for a town speaker, good if the lynched player was evil, otherwise left out (§4) |
| Otherwise | the day's lynch graded as if it were the speaker's own vote (a wolf is graded on whether a packmate died; a day with no lynch is neutral) |
| An evil player's lesson about keeping a low profile | its own rule, on a day the player spoke: drawing at most half its fair share of the day's accusations is good, at least twice its share is bad, anything between is neutral; a day with no accusations at all is unscored |

**Night actions.** A blocked action is neutral for every role: it spent nothing and was not the player's choice. An action whose result was never made public (the player died that night) is unscored.

| Role and action | Good | Neutral | Bad |
|---|---|---|---|
| Wolves' kill | lands on a town player or the lone killer | lands on a neutral | the healer saved the victim; the victim was immune; the kill was seen by a Sentinel or a Trailseer |
| Chanteuse block | blocks a town action that would have hurt the wolves | blocks a town action that changed nothing; the block did not take | blocks someone who had no action that night, or a non-town player |
| Illusionist conceal (hides a dead victim's role and night record) | hides a town victim who had a record to read out | the victim survived, so the conceal is kept; declined while the victim's record was harmless | spent on a body with nothing to hide; declined while the victim's record named a wolf |
| Serial Killer kill | lands on a non-neutral | lands on a neutral | saved, immune, or seen |
| Necromancer | unscored: its borrowed actions interact too much for one grade | | |
| Investigator check | the result reads Suspicious | any other result; declined | checked the Serial Killer, who reads as clear (a false clear and a spent check) |
| Sentinel watch | saw an evil visitor, or a dead player's body (the Necromancer's) | saw only town visitors; declined | saw no one |
| Trailseer follow | followed an evil player who went somewhere | followed a town player who went somewhere | followed someone who went nowhere |
| Healer protect | saved a town player from an attack | no attack came; saved a neutral | saved an evil player |
| Vigilante shot | shot an evil player, even one the healer saved or who was immune | held fire; shot a neutral | shot a town player |
| Sigilist sigil | placed on an evil attacker | | placed on someone who did not attack; placed on the Vigilante, who then shot |
| Speculator bet | the side it bet on won | declined to bet yet | the side it bet on lost; died on its last night without ever betting |
| Fortune Teller bet | scored one or two points; bet on itself on a night it was attacked | | a miss; bet on itself on a night no one attacked it |

The wolves' night chat decides nothing itself, so a lesson followed there takes the row of the move it is about: the kill, the Chanteuse's block or the Illusionist's conceal. Until 2026-10-28 every lesson followed in the chat took the kill's grade, so a lesson about when to spend a conceal was scored on whether the kill landed. (Source: each wolf night lesson records its move in the `pack_move` tag; v8 decisions §18.)

Two rows need a word.

**A wolf's vote scores well for voting with the room, even when the room is lynching the wolf's own packmate.** The rule measures one skill, blending in, because a wolf who votes against a clear majority draws attention to itself. Losing the packmate is a real cost to the wolves, but it shows up in the game's outcome, not in this vote's grade. The grade measures one skill, not the full value of the move.

**A harsh "bad" does not bias a lesson's score.** A role whose turns mostly grade bad simply has a low memory-off average, and a lesson is scored against that average (§3).

### One decision, graded

This lesson and decision come from a July nine-seat game, one of fifteen sampled for the attribution check in §5. Here is the lesson's text as stored in the check's record, which cuts it at 120 characters:

> *Lesson (vigilante, night):* "Do not shoot. Firing while under direct suspicion is extremely risky. If you hit a villager, you confirm the accusations"
>
> *Decision:* the vigilante, under active accusation, held fire that night and reported following the lesson.

Under the ten-seat table a vigilante who holds fire scores **neutral** (0). The July rule scored it the same way. The lesson's score then depends on how memory-off vigilantes do at night. If they usually shoot and hit evil players, their average is above 0, and a lesson that only ever holds fire falls below it. If their shots usually go wrong, their average is below 0, and holding fire comes out ahead. The rule does not decide whether caution was wise. The comparison with play without memory does.

## 3. From grades to a lesson's score

A lesson's grades are averaged, then compared with the same role's same kind of decision in games played with memory off. A vigilante's night lesson is compared with memory-off vigilante nights; a wolf's chat lesson about the kill with memory-off wolf chats, and one about a conceal or a block with memory-off conceal or block turns. This comparison matters because some decisions succeed most of the time anyway. Without it, a lesson attached to an easy decision would look excellent for doing nothing.

The memory-off games must be graded by exactly the same rules. A memory-off average computed any other way would differ from the lesson's average for reasons that have nothing to do with the lesson. Sometimes a lesson has followed decisions of a kind for which no memory-off games exist. It is then left unscored, and an unscored lesson is never pruned. A missing baseline is not treated as a baseline of zero.

The difference is then damped toward zero when the lesson has few uses. With one follow, a lesson keeps a sixth of its difference; with five, half; with twenty, four fifths. One lucky game therefore cannot make a lesson a star, and one unlucky game cannot sink it.

A few counting rules keep the evidence honest:

- **One grade per lesson per decision.** A player sees the same lessons on every turn of one day's discussion, one day's vote, one night's wolf chat, or one night's action. The lesson is graded once in each, at the first graded decision that followed it, so one decision is not counted several times.
- **Recomputed, not accumulated.** Each credit pass recounts every lesson over the window of games it is given. Old evidence leaves when the window moves.
- **Only AI seats' decisions are graded.** A game with a human seat is read, and the human seat's own decisions are dropped before grading (`credit_rules.iter_eval_cases`); a game whose human seats are not named is dropped whole. A human's play is not the agents' play. Until 2026-10-26 any game with a human seat was dropped; the owner relaxed the rule because most served games will have one, and credit can only grade the agents' own moves by fixed rules (v8 decisions §15). Extraction, which writes lesson text, stays AI-only.
- **A merged duplicate's follows count for the lesson it was merged into.**
- **Compared on the same game day (since 2026-10-28).** Each followed decision is compared with memory-off play by the same role, in the same kind of decision, on the same game day (days 1 to 3 each, later days together). Lessons fire at particular stages, and an average over all days mixes easy late days with hard early ones. A day with fewer than 20 memory-off decisions falls back to all days (`TickConfig.baseline_by_day`, `baseline_min_n`). On the ten-seat demo no day reaches 20 (12 memory-off seed games), so every follow still falls back and the demo pass's results are unchanged; why the day matters, and the nine-seat re-scoring that found it, are in [`day_matched_baseline/`](day_matched_baseline/README.md).

The scores then act. The thresholds were carried over from July and are labelled unvalidated for ten seats (`TickConfig` in `config.py`):

- **Prune** a lesson whose score is below −0.15 after at least 8 follows.
- **Protect** a lesson whose score is above 0 after at least 2 follows. A protected lesson is never removed.
- **Evict** a lesson shown at least 8 times, never followed, and overridden at least as often as marked not relevant. A lesson mostly marked "not relevant" is spared: that points to the search serving it in the wrong situation, not to bad advice.
- **Give synthesis a track record**: when it rewrites a cell (one role's one kind of decision), it sees each lesson there with at least 5 follows, alongside its score.

These steps run as a command that makes no model call: `tick credit`, in `Agents/memory/consolidation/tick.py`. It reads batch-run game files and the server's finished games. It rewrites every lesson's counts, prunes and evicts, and records each change with its numbers. The paid steps (extracting observations and synthesizing lessons) run separately, in batches.

> **The formula**, over a lesson's followed decisions:
>
> ```text
> raw average  = (good − bad) / follows
> difference   = raw average − memory-off average
>                (each follow compared with memory-off play by the same role, in the
>                 same kind of decision, on the same game day (since 2026-10-28); all
>                 days when that day has fewer than 20 memory-off decisions; the lesson
>                 is unscored if any of those kinds has no memory-off games)
> score        = difference × follows / (follows + 5)
> ```
>
> Code: `SPCredit.base` in `credit_rules.py`; `sp_lift` in `credit.py`.

## 4. Beliefs and actions are scored apart

Before acting, an agent answers two questions: what to believe about the other players, and what to do given that belief. These fail independently. A good tactic carried out on a wrong belief still ends badly. "Shoot the player you most strongly suspect" is sound advice, and it still kills a villager when the suspicion is wrong. Credit therefore tries not to let a wrong belief sink a sound tactic.

Take a town player's night action that grades bad. If the player had stated a high-confidence belief that its target was evil, and the target turned out not to be, the bad grade is left out of the lesson's score. The failure belongs to the belief, which is measured separately as read accuracy (§1). The same applies when a town speaker's accusation landed on a player who was not evil; there the accusation itself is the stated belief. At night, with no stated read, the bad grade stands.

Before this design, credit came from an AI judge that read each player's whole day and gave one verdict. It could not say whether the belief or the action had gone wrong, so it was replaced by the rules above.

**Tells: research only, not served.** The redesign's other half stores beliefs as *tells*: public behaviors counted against the roles revealed at game end. One example from the 34-entry seed book reads: "A player asserts high confidence in an accusation while refusing to disclose the source of their information." Ten of the eleven players detected doing this in the sampled July games were investigators. A tell is scored by how much more often one role shows the behavior than that role's share of the seats, damped for small counts. Tells were built and tested in the July research loop, and the ten-seat game does not use them. The prompt hook (`Agents/memory/tell_book.py`) adds nothing unless the `WW_TELL_BOOK` environment variable points at a book, and nothing in the server's code or configuration sets it. Detection, scoring and evidence are in the [tell report](../extraction/tell_extraction/report.md).

## 5. How we know the scoring works

Three checks bear on whether the scores mean what they say, and one run shows the ten-seat pass working. None of them shows that memory guided by credit plays better (§7).

**Do "followed" claims match what the agent did?** Credit trusts the agent's report that it followed a lesson. In July, 15 such claims were drawn at random from 2,387 in the nine-seat runs. A model then compared each lesson with the decision actually taken. In **13 of the 15** the action matched the advice. Fifteen cases are few: by the standard one-sided 95% bound, the true mismatch rate could be as high as about 36%. So the check shows attribution was usually right in the sample, not that it is reliable. The two misses differed:

- A serial killer said it was following advice to discredit its accuser aggressively, then passed its speaking turn and said nothing.
- A villager said it was following advice to turn on its accuser, then gave a conciliatory defence and pointed at other players instead.

The first kind is now closed: a discussion lesson is credited only on a turn where the player actually spoke (`_spoke` in `credit.py`). The second is not; a spoken turn can still contradict the lesson it claims to follow. Source: [the 15 cases and verdicts](attribution_spot_check.json).

*Larger check, 2026-10-28.* 100 follow reports from the ten-seat demo games (35 discussion, 30 vote, 35 night), read by model readers: of the 81 they could judge, 74 matched (91%; 95% interval 83–96%) and 5 matched in part; 19 could not be judged, 10 of them wolf night chats whose content the sample left out. The owner hand-labelled 20 of them against the game records and agreed with every case the readers judged; 3 of the 4 they could not judge were matches once the record was read. Record: [`attribution_check_ten_seat/`](attribution_check_ten_seat/README.md).

**Are the scores repeatable?** If scores were noise, a lesson's score from one set of games would not predict its score from another. In July, the archive of games was split in half by game, and each lesson was scored on each half separately. For the **31 lessons** with enough follows in both halves, the two sets of scores agreed (correlation r = +0.54, where noise would give about 0).

The second question is whether a lesson flagged as a loser stays a loser. Nine lessons scored below the prune line (−0.15) on the first half. On the second half, 8 of those 9 (89%) still scored below memory-off play (but see the 2026-10-28 note below). For comparison, 61% of all 31 lessons scored below memory-off play on the second half, whatever their first-half score. A flagged lesson was therefore more likely than a typical one to stay negative: 89% against 61%. With nine lessons, that shows the direction, not the size. The one lesson that flipped had only 3 follows, fewer than the 8 the prune rule requires; all 4 flagged lessons with 8 or more follows stayed negative.

This shows the ranking repeats across games. It does not show that removing the losers improves play.

*Note, 2026-10-28.* Repeating is reliability, not correctness. Four of the nine flagged lessons score identically in both halves because every follow got the same grade against a baseline both halves share, so "8 of 9" is partly built in; and a systematic error repeats in both halves too, as the all-days baseline did (§3, [`day_matched_baseline/`](day_matched_baseline/README.md)). What the split supports is the follow floor: the one lesson that flipped had 3 follows. Record: [the strategy-point store](../store_curation/strategy_points.md) §6.

**Do the rules do what the table says?** Unit tests pin the ten-seat table. `tests/memory/test_ten_seat_grading.py` has a test for each row that has a case of its own. It also covers the once-per-decision count, the unscored baseline, and the prune and evict lists. `tests/memory/test_consolidation_graduation.py` covers three things: the town abstain rule (§6), that only the AI seats of a game with a human seat are graded (since 2026-10-26; before then such a game taught nothing), and a full credit pass with no model calls. The 50 test cases in these two files passed at `e765a18e`; the human-seat tests were added with the 2026-10-26 change. *Note, 2026-10-28:* the two files now hold 54 tests, and the whole memory suite (325) passes on the working tree with the day-matched baseline and the chat-lesson grading, not yet committed.

**Does the ten-seat pass run end to end?** Once, as a demonstration. In October 2026, Claude Haiku 5.5 played 20 memory-on games, compared with the 12 memory-off games that seeded the store. Of 498 lessons, 148 were followed and scored; the pass pruned 4, evicted 4 and protected 50. Twenty games give at most a few dozen follows per lesson. So these numbers show the mechanism working, not which lessons are good ([the v8 log](../memory_system/v8/experiment_log.md), 2026-10-14). *Note, 2026-10-28:* that pass graded every lesson followed in the wolves' chat by the kill (§2). One of the four pruned lessons is about the conceal, so a rerun under the current rule may not prune it.

## 6. Case study: a harmful lesson the score could not see

**The lesson.** The July nine-seat research loop kept this lesson for the vigilante's day vote:

> "Abstain from voting when the information landscape is entirely speculative and no clear consensus exists, in order to preserve your vigilante identity and avoid creating a public voting record that can be scrutinized by wolves."

Agents followed it 19 times. The store it sat in was then tested on 30 paired boards, each board dealt once and played twice, with memory and without. The town did worse with memory on 19 of the 30. In the memory games, 111 of 117 town abstains fell on a day that ended with nobody voted out.

**Why credit missed it.** Two gaps in the scoring code worked together:

1. **Every town abstain was graded neutral.** An abstain's harm is a vote that never happened, so there was nothing for the rule to grade. The lesson's 19 follows came out 2 good, 15 neutral, 2 bad: an average of exactly zero.
2. **The comparison with memory-off play was missing, and the code used zero in its place.** An average of zero compared with zero gives a score of 0.00, which never reaches the prune line (−0.15). Compared with how memory-off vigilantes actually voted, the lesson would have scored −0.16, only just past the line.

**The fix.** The ten-seat code closes both gaps:

1. A town abstain on a day that ended with nobody voted out is graded bad. The same 19 follows become 2 good and 17 bad, and the lesson scores −0.62, far past the line.
2. A lesson with no memory-off comparison is left unscored instead of being compared with zero (§3).

**What it shows.** A score can stay safe while the play it produces gets worse, if the score cannot see the harm. This is Goodhart's law: a measure that becomes the target stops tracking what it was meant to track.

**Limits.**
- The town result leans negative but is not statistically established: a gap that size would appear about 6% of the time by chance (p ≈ .06).
- The July players answered with no reasoning step (zero reasoning tokens), so it is a result for players that do not reason.
- The fix was checked on recorded games only: re-scoring pruned this lesson and kept three lessons chosen in advance as good. It was never tested in new games.
- *Note, 2026-10-28.* Matched by day ([`day_matched_baseline/`](day_matched_baseline/README.md)): against memory-off vigilante votes on the lesson's own days (15 follows on day 2, 4 on day 3), the lesson scores −0.08 under the July grades (kept) and −0.38 under the corrected rule (pruned), beside the all-days −0.16 and −0.62 above. The −0.62 was still computed against zero: the lesson is typed as concealment, and no memory-off concealment comparison existed for the vigilante's vote. Against all memory-off vigilante votes under the corrected rule it is −0.64. The three control lessons were re-scored against all days only. Day matching alone would have kept this lesson; only the grading rule removes it. Case write-up: [`writeup/memory/curating_lessons/abstention_credit.md`](../../writeup/memory/curating_lessons/abstention_credit.md).
- Until 2026-10-27 the ten-seat game showed town players no lessons on day turns, so the abstain rule graded only memory-off votes. Town vote lessons are served since then ([v8 decisions](../memory_system/v8/decisions.md) §17), so it now grades served lessons too; no served game has been credited yet.

## 7. What is not established

- **No gameplay benefit has been shown** for memory guided by credit. The July test leaned negative before the fix, and the fixed version was never played live. The ten-seat version has run once as a demonstration and has not been tested at scale.
- **Attribution errors are not shown to be random.** Agents might claim to follow lessons more often on decisions that went well. That would bias the scores, and the 15-case check cannot rule it out.
- **Tells are not served** in the ten-seat game.
- **On the live site, memory is a per-game choice that starts off.** A player can switch it on because the production settings turn on the deployment's switch (`WW_MEMORY_ENABLED`, `server/config.py`); where that switch is off, a request for a memory-on game is refused. So the site offers a memory whose benefit to play has not been shown.

## Sources and implementation

| What | Where |
|---|---|
| Decision grades (the §2 table) | `Agents/memory/consolidation/grading.py` |
| Counting, baselines, the belief exclusion, the human-seat rule | `Agents/memory/consolidation/credit_rules.py` |
| Discussion and low-profile rules; writing counts into the store; the score | `Agents/memory/consolidation/credit.py` |
| Prune, protect, evict, the synthesis track record | `Agents/memory/consolidation/store_ops.py`; thresholds in `config.py` |
| The credit pass and the learning step | `Agents/memory/consolidation/tick.py` (`tick credit`, `tick learn`) |
| Tests | `tests/memory/test_ten_seat_grading.py`, `tests/memory/test_consolidation_graduation.py` |
| Why the ten-seat rules are what they are; the credit-pass split | [v8 decisions](../memory_system/v8/decisions.md) §12–14 |
| The ten-seat demonstration run | [v8 log](../memory_system/v8/experiment_log.md), 2026-10-14 |
| Why beliefs and actions are scored apart | [Design record](read_tactic_credit_redesign.md) |
| Attribution check (15 cases, 2026-07-13, seed 20260713) | [attribution_spot_check.json](attribution_spot_check.json) |
| Repeatability check (31 lessons) | [Strategy-point store](../store_curation/strategy_points.md) §6 |
| The abstain blind spot, its fix and checks | [Blind-spot log](blindspot_fix/experiment_log.md); [step-1 table](blindspot_fix/step1_validation.md); the lesson's record in `blindspot_fix/scored_stores/loop_run__neutral/strategy_points.json`; base averages in `blindspot_fix/scored_stores/loop_run__neutral/base_rates.json` |
| Tells | [Tell report](../extraction/tell_extraction/report.md); `Agents/memory/tell_book.py` |
| The July nine-seat code (frozen, kept so old runs reproduce) | `evaluation/src/loop/` (`credit`, `credit_backfill`) |
