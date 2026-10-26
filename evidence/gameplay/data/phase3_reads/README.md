# Phase 3: five games read by hand (2026-10-10)

The balance batches were first read by counting fields in the records. After the owner asked
whether anyone had read the transcripts, five games were rendered as readable transcripts
(`transcripts/`, by `evaluation/experiments/phase3_render_transcript.py`: every public line with
the speaker's true role and claim field, the summaries, the votes, the pack's chat, every real
night action, each private record and the evil seats' strategy notes; the pack's chat lines appear
twice, a rendering artifact of the subgraph and parent updates). Claude read e04; four Opus agents
read e06, c01, d03 and b02 against one rubric; their decisive quotes were checked against the
transcripts before use.

| Game | Batch | Winner | What decided it, per the read |
|---|---|---|---|
| b02 | 1 (baseline) | town | the sigil's "immune" record named the serial killer on day 2; the trailseer's two-visit sighting and the vigilante took the chanteuse; counting took the illusionist |
| c01 | 2 | serial killer | the town's information pointed at nobody evil; the table voted out the speculator on an inverted clean read; the wolves split their day-4 vote while knowing who the killer was |
| d03 | 3 | town | a sentinel sighting the chanteuse could not explain (no cover); the serial killer claimed vigilante against a morning report that named the serial killer |
| e04 | 4 | town | the chanteuse took an investigator cover and the table voted out the real investigator; the town recovered through the investigator's will and the vigilante's shots |
| e06 | 4 | necromancer | the summariser recorded a chanteuse claim the investigator never made; the investigator accepted it about itself and was voted out; a trailseer went on no evidence |

## What the reads found, across the five

1. **The summariser invents a claim, and the ledger lets it stand (e06).** Day 2, the
   investigator: "I was roleblocked last night, which confirms we have an active Chanteuse in
   play." The summary: "player_2 claimed chanteuse — Night 1: blocked player_2". The speaker set
   no claim field, so the ledger's fallback took the summariser's role. Day 3, the sigilist opened
   on it, and the investigator answered "I claimed chanteuse yesterday to draw fire away from town
   PRs", accepting a false premise about its own past, against its own private record. Voted out
   7 to 1, with a true Suspicious read on the chanteuse.
2. **The summariser's record check marks true claims false.** Its accusation field
   `record_check` carries the example "no attack on player_2 was ever announced", and the summaries
   repeat it against claims of an attack on an immune player, which by rule is never announced
   (b02 day 2, on the sigilist's true claim; b09 day 2 before it). The example phrase is copied.
3. **Consistent read as proof, everywhere.** "That physical trace corroborates player_9's
   investigator claim" (d03); "my results are genuine" from a watch and a save (d03); in e04 the
   trailseer took the sentinel's sighting of the chanteuse as support for its fake investigator
   claim, the step that lost the real investigator, while the sentinel itself had said the right
   thing: "my watch only proves they visited, not that they are the investigator."
4. **Rule misreads, some unchallenged.** A sigil triggered by visits to the target (c01, three
   times, never corrected); "every role only makes a single visit" (b02, corrected); a watch read
   as "your empty house" (b02, on the deciding day); a necromancer using a body on a night its
   owner was alive (e04, corrected); a clean investigator read turned into suspicion (c01).
5. **The cover epoch works as written.** Before it (b02, c01, d03) the evil seats either had no
   cover ("I'll confirm I was looking their way", d03) or claimed vigilante against a morning
   report naming the serial killer (b02, d03). After it (e04, e06) no evil seat explained a visit
   with its real action; the e04 chanteuse's investigator cover won the day-2 claim contest. The
   notes copy the template blindly ("Do not disclose: my block, my conceal" on roles without them),
   which did not leak into speech.
6. **Real information roles withhold.** e04's investigator counter-claimed without ever stating
   its check, and lost the contest to a fake claim that stated one.
7. **Thin and repetitive days.** About a third of the heard lines restate something already said
   (b02, d03); c01 and e06 heard few lines at all, with several held by the filter; votes land on
   the right seat with no line naming it that day (e04 day 3).

## The answer to the question asked

Night information still decides most games where it lands on an evil seat (b02, d03), and its
absence decides the rest (c01). The day is weak in both directions: shallow, repetitive, and
quick to take a consistent sighting as proof. The complex roles add a handful of rule misreads,
but the two failures that changed outcomes in the latest batch were record errors (items 1 and 2),
not role complexity.

## The audit of ten more games (2026-10-10)

Ten further games were rendered (`transcripts/b05, b10, c02, c04, c05, d02, d05, e01, e03, e05`,
spread across the four batches, lineups and winners) and read by five Opus agents, two games each,
against one rubric that keeps apart: **A** invented fact (contradicted by the record, the transcript
or the speaker's own private record), **B** summary error, **C** invalid deduction (true premises,
wrong inference, chiefly about what an ability observes), **D** evil deception (a deliberate lie is
not an error; a lie the speaker's own notes show it believes is), **E** night error (a night action
or night-written note against the actor's own record or the rules). Spot quotes from every report
were checked against the transcripts.

| Game | Batch | Winner | Heard lines | A | B | C | D, self-misunderstood | E | D, deliberate |
|---|---|---|---|---|---|---|---|---|---|
| b05 | 1 | town | ~46 | 0 | 3 | 2 | 1 | 0 | 2 seats |
| b10 | 1 | town | ~50 | 0 | 2 | 2 | 0 | 0 | 1 seat |
| c02 | 2 | wolves | ~20 | 0 | 2 | 6 | 0 | 1 | 3 lines |
| c04 | 2 | town | ~25 | 0 | 3 | 4 | 0 | 0 | 4 lines |
| c05 | 2 | serial killer | ~17 | 0 | 3 | 5 | 0 | 1 | 1 line |
| d02 | 3 | town | ~52 | 0 | 3 | 2 | 1 | 1 | 3 seats |
| d05 | 3 | town | ~37 | 0 | 1 | 3 | 0 | 1 (borderline) | 3 lines |
| e01 | 4 | town | ~30 | 1 | 2 | 1 (held) | 0 | 0 | 1 episode |
| e03 | 4 | town | ~36 | 1 | 1 | 3 | 0 | 1 | 3 seats |
| e05 | 4 | town | ~32 | 0 | 2 | 0 | 0 | 1 | 2 seats |
| **Total** | | | **~345** | **2** | **22** | **28** | **2** | **6** | |

**Invented facts are rare.** Two in ten games: a vigilante saying "my final shot" with a bullet left
(e03), a sigilist saying "we still need to find their remaining partners" after both wolves were
revealed (e01). Nobody misstated a death, an announcement or their own result.

**Invalid deductions are the commonest player error**, about one heard line in twelve, and nearly all
are about what an ability observes: a watch read as clearing or confirming the watched player ("your
watch on me lines up since I stayed put", c05; "Player_6's sentinel check clearing them", c02), a
sighting taken as proof of a role (d05), a visitor read as the attacker when the target was saved
(d05), night timing (a victim cannot visit, e03; a block on night 1 means a necromancer, c04), and a
vote on the serial killer taken as proof of town (c02). The new roles' mechanics proper (the
necromancer's bodies, the conceal hiding the carrier, a block landing the night the chanteuse dies)
were reasoned correctly where they came up (b10, e05).

**Summary errors are the commonest error overall**, two a game, mostly omissions and distortions of
plain information-role claims: a watch's "no one visited" written as "says there was no attack"
(b10, d02), sightings dropped from the claims line (batches 1 and 2, before the summariser's `seen`
field), a role claim attributed to the wrong player or an accusation nobody made (c05, b05), and the
self-block transcription twice more (b05 day 3 "Night 2: blocked", e01 day 3), which the ledger rule
of 6248fc58 now drops.

**Deliberate deception is common and mostly sound**, as it should be: fake claims kept consistent with
the notes (e01's chanteuse as sigilist, e05's illusionist as sentinel, d02's necromancer as healer,
c04's necromancer as trailseer). Two evil seats misstated a rule they appeared to believe (b05, d02).
The pre-epoch chanteuse in c04 outed herself with "I spent that entire night blocking player_8".

**Night errors** are evil notes planning an action that cannot work (blocking a sentinel whose watches
were spent, c02 and d05; attacking the immune serial killer, c05) and a template echo: both wolves'
notes copy "Do not disclose: my block, my conceal, the pack's kill" whatever their role (e03, e05),
which is the shared cover paragraph of d066d1b3 listing every wolf action. No echo reached speech.

**Downstream use observed.** A town win does not show that an error had no effect: an error can change
votes, survival, later information and targets while the same side still wins, and "the winner would
have been the same" needs a counterfactual these records do not hold. What can be said is where an
error's downstream use is visible: c02 day 4, a vigilante taking a player's vote on the serial killer as
proof of town, opened the healer's lynch the wolves went on to win from (with an unexplained vigilante
shot on the fortune teller); b05's day-2 deduction moved a night target; d05's and c04's fed lynches
that landed on evil. Several deciding moves had no stated reason (votes with no heard line, vigilante
shots), which no rubric can classify.

**How to read these counts (after review, 2026-10-10).** Three limits apply. (1) **Corrupted context.**
A player reasoning correctly from a summary that dropped or distorted a claim is not making a reasoning
error; the summary errors are counted apart (B), but which later invalid deductions (C) ran on corrupted
context was not traced, so C mixes the two. (2) **Defeasible reads.** "They helped catch a killer, so I
trust them more" is ordinary social deduction; "that proves they are town" is the error. The readers did
not always keep the two apart, so C is probably high. (3) **Role complexity.** Most C errors are about
what a new role's ability observes; they are general over-inference, made more likely by a cast with
more interacting observations and exceptions. Reasoning some new mechanics correctly (b10, e05) does not
show the added complexity is free.

**Two engine questions the reads raised, not agent errors.** (1) When the illusionist carries the
kill and conceals the same victim (d05 night 2), the sentinel watching the victim saw neither of its
visits: the conceal's hidden carrier visit and the illusionist's own conceal visit are the same door,
and the engine hides both, while the sheet then said the illusionist's own visit is still seen. The
owner ruled on 2026-10-10 that such an illusionist is invisible at that door, and the rules now say so;
but d05's players were told the opposite (the illusionist's card then said its own visit is still seen),
so d05 is judged against what they were told: the sentinel's day-3 inference from the empty door
followed the rules as given, and counts against the specification, not the model. (2) The
morning "saved by the healer" when the necromancer protected through the dead healer's body (b10)
told the table a healer was alive; a player read it correctly as a borrowed protect.

## The six flash games (2026-10-10)

Rendered as `transcripts/f01` to `f06` and audited on the same rubric; the table and reading are in
`../phase3_flash_games/README.md`. Per game: f01 A0 B1 C3 D-self 1 E0 (~31 lines); f02 A0 B3 C4
D-self 2 E0 (~53); f03 A1 B1 C2 D-self 1 E0 (~36); f04 A0 B1 C3 D-self 0 E2 (~37); f05 A0 B2 C2
D-self 1 E0 (~42); f06 A0 B1 C2 D-self 1 E0 (~41).

## The odd votes, read against the voters' own reasoning (2026-10-10)

The audits flagged lynches that looked unexplained (the investigator lynched right after the table
said it trusted it, a player nobody discussed, a healer lynched on a vote record). Eleven of those votes,
in f04, f03, c02 and e04, were read against what each voter could see and wrote: its lines that day, its
strategy note going into the vote, the reads it wrote in the vote call itself, and its first note after
(`votes/dossiers.md`). **None was an unexplained change of mind**: every voter voted for the player its
own vote-time reads rated most likely evil, or, with no read above low, for a quiet player. What went
wrong sits in what the reads rested on:

- **A rule the prompts did not state (f04 day 5, the investigator lynched 2–1).** Both town voters
  reasoned from "the Illusionist's visit to hide a body is always seen by a Trailseer": from the dead
  trailseer's will, the sigilist cleared itself and the real illusionist (an illusionist that carried
  its own kill and concealed it, so the trailseer saw no visit), which left the investigator. The
  earlier "we trust player_6's investigation" was overridden by what read as a mechanical proof. The
  same unstated rule decided f02, so it turned two of the six flash games; the owner's ruling and the
  sentence in the rules came after both.
- **A quiet-player heuristic (f03 day 3, the fortune teller lynched undiscussed).** No voter read anyone
  as evil above low; all three chose "one of the completely silent players… to apply pressure" over
  abstaining. The vote prompt's abstain line ("a wrong elimination is costly, but so is letting the
  killers act another night unchecked") may lean them toward voting; that is a possibility, not shown.
- **An invalid inference held consistently (c02 day 4, the healer lynched).** Two voters read the healer
  as the chanteuse at high confidence because it had voted for the real chanteuse instead of the serial
  killer the day before.
- **A sighting taken as proof, exploited by a cover (e04 day 2, the investigator lynched).** All three
  town voters read the chanteuse's fake investigator claim as "verified by the sentinel's watch".

So the voting anomalies fold into the categories already counted (an unstated rule, invalid deductions,
a weak default when nothing points anywhere) rather than a separate failure of carrying reasoning to the
vote.

## The four GPT-6 Luna games (2026-10-10)

Rendered as `transcripts/l01` to `l04` and audited by two readers; the table and reading are in
`../phase3_luna_games/README.md`. The sentinel self-visit chain (an unstated rule) accounts for 11 of the
14 invalid deductions, and the summary's roleblock-as-denial filing (a regression from claim retention)
fed one invalid deduction in each of two games.
