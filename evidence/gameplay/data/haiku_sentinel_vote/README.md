# Game 403f4dbc: why the vigilante eliminated the sentinel

Investigated 2026-10-16 from the game's persisted events, game row and LangGraph root
checkpoints, using read-only database connections. Full ID:
`403f4dbc-4a16-45fc-bb22-1c5e67bd5936`. Selected source records are in
[source_excerpt.json](source_excerpt.json); event numbers below are durable `seq` values.
No model reruns or gameplay changes were made for this investigation.

The vigilante (player_2) voted out the real sentinel (player_9) on day 5 because it
promoted an unverified claim into positive suspicion. Its saved vote note explicitly
says: "Player_9's sentinel claim is unverified and their watch reports are self-reported,
so I treat them as the leading suspect" (614). There was no sentinel counterclaim or
new contradictory result. This is an unsupported change in the model's assessment;
the recorded rationale does not identify evidence that justifies the reversal.

## How the assessment changed

- On night 3 it said the illusionist's elimination made the investigator's check and
  sentinel's watch "more credible as town claims" (438).
- On day 4 it said the sentinel's roleblock "fits a real town role being targeted"
  (505), and at the vote it still leaned toward believing the sentinel (540–541).
- On day 5's opening it still listed player_9 as sentinel, but emphasized the
  unverified roleblock (583). Its final discussion note said to watch for a
  counterclaim or conflicting account (596); neither arrived.
- At the vote, it changed player_9's suspected role to necromancer, with low
  confidence, solely citing self-reported watches and an unverified roleblock
  (613–614). It then voted player_9 (617).

Player_3 was the human Necromancer, and player_10 the Speculator who had picked Town.
Both passed throughout day 5; the sentinel's watch report was the only public speech
that day (591). Player_10 independently made the same "unverified claim" argument in
its private vote note (609–610), but that note was not public. Votes were fanned out
concurrently: the historical `Agents/nodes/day/flow.py` at `ed1bb4c5^` builds each
voter's payload from the discussion, summaries and its own strategy, without other
players' pending votes or strategies. Thus the event order does not establish that
the vigilante followed the Speculator's ballot.

The vigilante gave the quiet players less scrutiny: player_3 had voted with the
day-3 majority and had no visitors in the sentinel's watch; player_10 had voted with
the majority and made no claims (613). Neither was confirmed town. The practical
effect was to penalize the informative claimant while leaving silence as "no evidence
either way." The tally was player_2 and player_10 → player_9, player_9 → player_3,
player_3 → abstain (615–620). Abstention was available.

An uncontested claim is not mechanically conclusive: two earlier deaths had hidden
roles (player_8 and player_5), so a dead true sentinel was possible from the players'
public perspective. But the vigilante did not offer that argument, and absence of
verification alone does not establish greater suspicion than the alternatives.

## The watch error contributed, but is not the whole explanation

The sentinel incorrectly said its watch saw no visitors to player_3, "so they did
nothing that night" (591). A watch reports incoming visitors, not the watched player's
actions. The vigilante cited the empty watch in its day-5 read of player_3 (613), then
explicitly said on day 6 that "player_3 visited nobody on night 4" (649).

The day-5 vote note does not explicitly say the empty watch cleared player_3, so its
exact causal contribution to that ballot is uncertain. The direct stated reason for
eliminating player_9 remains the unverified claim. The later error confirms that visit
direction was also being mishandled. The sentinel itself corrected the inference in
its private vote read (611), but never said that correction publicly before voting.

## Before or after the updates?

All times in this table are Singapore time (UTC+8). Game/checkpoint times come from
Postgres; update times are Git commit times, not deployment timestamps.

| Event | Time | Relation to this game |
|---|---|---|
| Earlier sentinel rule clarification: watcher excluded from its own visitor list (`d47d751c`); summary/ledger repairs (`0c605e89`) | Oct 10, 15:03 | Committed before the game; those changes address different faults |
| Game started | Oct 12, 12:01:00 | Haiku 5.5; memory disabled |
| Day-5 elimination recorded in root checkpoint | Oct 12, 12:25:45 | The sentinel vote investigated here |
| Game completed | Oct 12, 12:31:05 | Necromancer won |
| Visit-direction, reply repetition and town vote-reason fixes (`ed1bb4c5`) | Oct 12, 14:23:09 | After the game; commit message explicitly cites this game as motivation |
| Reads-first output ordering (`d80ee2d2`) | Oct 13, 22:00:56 | After the game |

The October 12 fixes were a response to this game, not its cause. Memory retrieval
updates cannot explain this game's vote: the persisted game row has `memory=false`.
There is no `prompt_captures` row for this game, so its exact deployed prompt bytes
and runtime SHA cannot be established from that table. Earlier commit dates alone
are not proof of deployment.

The existing [turn replay](../haiku_turn_replay/README.md) tested discussion turns,
not this day-5 ballot. Across sampled visit turns, public direction errors fell from
16/35 to 5/35. The day-5 vigilante still passed 5/5 after the final vote-reason wording.
Those results do not establish that the updates prevent this sentinel elimination.

A focused follow-up would replay the saved day-5 voting state on the relevant prompt
versions, scoring whether the vote weighs corroboration, absence of counterclaims,
hidden-role deaths and alternative suspects without equating "unverified" with
"hostile." That replay was run the same day, after this investigation:
[haiku_vote_replay](../haiku_vote_replay/README.md) (discussion_evidence.md §8.7).
