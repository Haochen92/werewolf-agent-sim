# Do "followed" reports match the decision? Ten-seat check (2026-10-28)

Credit trusts a player's report that it followed a lesson. The July check read 15 of 2,387 nine-seat
reports (13 matched); with 15 cases the true mismatch rate could be as high as about 36%. This check reads
100 reports from the current ten-seat system.

**Sample.** `evaluation/experiments/attribution_check_sample.py` (seed 20261028) drew from the 20 ten-seat
demo games (`batch_results/v8_demo`) the reports credit counts: memory-on, the lesson mapped to a store key,
and for discussion only spoken turns. Pool 856 (246 discussion, 135 vote, 475 night); sampled 35 / 30 / 35,
votes oversampled because the abstain cases are vote lessons. The sample leans to the wolves and the
Necromancer, who hold most follows in these games. Files: `cases.json`, `batch_0..4.json`.

**Readers.** Five model readers, 20 cases each, judged whether the decision does what the lesson says
(match / partial / mismatch / uncheckable), using the player's stated reason only to see which part it
meant. Each saw the lesson, the decision and the last 8 public lines. Verdicts: `verdicts_0..4.json`.

| Phase | Match | Partial | Mismatch | Uncheckable |
|---|---|---|---|---|
| Discussion (35) | 30 | 4 | 1 | 0 |
| Vote (30) | 26 | 1 | 1 | 2 |
| Night action (35) | 18 | 0 | 0 | 17 |
| All (100) | 74 | 5 | 2 | 19 |

Of the 81 judgeable cases, 74 matched (91%; Wilson 95% interval 83–96%), and 79 matched at least in part.
The two mismatches: a Serial Killer told to echo the room's demand that evasive players state their role
volunteered its own night visit instead; a Chanteuse told to vote with the majority voted outside it. Most
partials are "one neutral question, nothing more" lessons followed with a question plus a long
self-defence. Ten of the uncheckable cases are wolf night chats: the sample kept only that the wolf chatted,
not what it said, so a lesson about the conceal choice could not be judged. That is a gap in the sampler,
not in the players.

**What it shows.** The follow label is usually honest. It does not show that the lesson caused the move.

**Owner hand-check (done 2026-10-28).** 20 cases (every mismatch and partial, 4 uncheckable, 9 matches) in
`owner_handcheck.md` / `.json`, hand-labelled by the owner against the game records. The owner agreed with every one of the 16 cases the reader judged: all 7
mismatches and partials, all 9 matches. Of the 4 the reader could not judge, 3 became matches once the game
record was read (two wolf night chats whose text is in the record's wolf channel; one vote where the record
shows whose claim was thinner); 1 stayed uncheckable. So the reader's verdicts held where it gave one, and
its "uncheckable" was a gap in what the sample showed it.

The misses have a pattern worth naming: in most of them the player applied a lesson whose premise did not
hold, such as an "unsuspected wolf" lesson used for a last word under accusation, or "vote with the
majority" when the room wanted to hold the vote. That is a fit problem (retrieval and the player's own
judgement of applicability), not a player misreporting what it did.
