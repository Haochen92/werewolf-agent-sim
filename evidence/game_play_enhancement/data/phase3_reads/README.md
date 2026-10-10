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
