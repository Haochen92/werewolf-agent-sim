# Phase 3: the fourth balance batch (the cover story and the ledger's sightings)

Six AI-only games on the ten-seat cast, 2026-10-10, on the committed discussion-quality epoch
(d066d1b3) over the third batch's rules: the wolves and the serial killer are told never to
explain a visit with their real action and to keep a cover in their strategy note; the claim
field counts a role claimed by describing its action; the summariser transcribes the players a
claimed watch or follow saw, and the ledger writes them as the claimant's word with what a visit
does not establish. Three serial killer and three necromancer lineups, two games at a time, the
same model and capture. Six games are a coarse read.

| Game | Drawn seats | Winner | Neutral | Days | Calls | Cost | Rescued turns |
|---|---|---|---|---|---|---|---|
| e01 | serial killer, speculator | town | won | 4 | 152 | $0.76 | 0 |
| e02 | necromancer, fortune teller | town | lost (0 points) | 4 | 158 | $0.77 | 0 |
| e03 | serial killer, fortune teller | town | lost (0 points) | 4 | 123 | $0.66 | 0 |
| e04 | necromancer, speculator | town | lost | 3 | 119 | $0.65 | 0 |
| e05 | serial killer, speculator | town | won | 4 | 124 | $0.64 | 1 |
| e06 | necromancer, fortune teller | necromancer | lost (1 points) | 5 | 170 | $0.80 | 0 |

Total cost $4.29. A quiet hour: one rescued turn in the six.

## The reading

**Town five, necromancer one.** e06 is the first necromancer win on the cast, on day 5 with the
town down to two votes against it after it killed through the dead vigilante's and illusionist's
bodies on three nights running. Over the eighteen games on the second batch's base rules the
score is town 14, evil 4.

**The evil seats now claim.** Their claim fields went from 4, 8 and 4 in the three earlier
batches to 19 here: the chanteuse claimed sigilist or investigator, the illusionist sentinel, the
serial killer healer. Four days had two claimants for one role, against 0 to 2 before, and in
three of the four the evil claimant was voted out that day or the next. The cover story works as
a prompt, in that evil seats take a cover instead of explaining their visits, and the one-against-
one it creates is resolved against them nearly every time: the real holder has its record, and
the summariser's `seen` names let the table check a sighting against the claimed role.

**What the table voted on.** Two of the twelve evil lynches followed a naming result (a sentinel's
and a trailseer's sighting at a death); the other ten came from the day, mostly the contested
claims above and visits argued from the trails. Three town seats were voted out, two of them
investigators (e04 on day 2, e06 on day 3), which is the cover claim doing its work.

**On admissions.** A regular-expression search for an evil seat saying "I blocked", "I concealed"
or "I attacked" in public finds none in any batch, this one included, so that measure is too
narrow to show the change the transcript review described; a first-person sentence using the
role's own verb ("I" and "block" in one sentence, and so on) counts 3 of 67 evil lines in the third batch and 6 of 49 here, so by that crude measure the admissions did not fall. A judged read of the evil lines is the
honest instrument for this and is not done here.

## Run notes

Two at a time, one rescued turn, nothing crashed. The run script is `logs/run_batch.sh`, the
timings `logs/waves.log`. The games ran on the committed tree.
