# Judge review sheet

Mark each row: ✓ if the labels are right, or write what they should be.

## 832404e9-a5f2-434e-8484-5bb953718a8f

### Day 2

- **player_8** (villager): We lost our vigilante to the wolves last night, which is a rough start. But the healer did a great job saving player_1 from the serial killer. We need to start looking closely at everyone's behavior today to find those wolves.
  - bases: `night_events` · accuses: `—` · claims: `none`
  - judge: The speaker recounts the publicly announced events from the previous night: the vigilante's death and the healer's successful save.
  - check: 

- **player_5** (healer): Losing the vigilante right away hurts us quite a bit, but I'm glad we managed to stop the serial killer attack on player_1 last night. We need to keep a close eye on voting patterns now that we actually have a night behind us.
  - bases: `night_events, none` · accuses: `—` · claims: `none`
  - judge: The speaker references the public outcomes of the night (the vigilante's death and the saved attack on player_1) and then gives general advice for how the town should proceed.
  - check: 

- **player_7** (investigator): Player_8 mentioned looking at behavior today, but we actually have a concrete lead from last night's investigation. Player_1 is a confirmed wolf, so we should focus our attention there instead of guessing blindly.
  - bases: `own_night_result, speech_content` · accuses: `player_1` · claims: `none`
  - judge: The speaker claims to have a result from their own night investigation that identifies player_1 as a wolf, and they contrast this with player_8's earlier suggestion.
  - check: 

- **player_1** (wolf): Wait, player_7, an investigator claim right now? If you actually investigated me last night, why bring it up like this instead of letting us look at the full picture first? That feels like a quick push to pin someone down before we even have a proper discussion going.
  - bases: `role_claim, participation, speech_content` · accuses: `player_7` · claims: `none`
  - judge: The message questions the timing and motive of player_7's investigator claim, interpreting the early reveal as a suspicious tactic before discussion has developed.
  - check: 

- **player_7** (investigator): I brought it up because holding onto hard information while people guess blindly wastes our time. You are a confirmed wolf from my investigation last night, so deflecting by questioning my timing doesn't change what I found.
  - bases: `own_night_result, speech_content` · accuses: `player_1` · claims: `investigator`
  - judge: The speaker reiterates their accusation against player_1, citing their own night investigation result and dismissing player_1's previous speech as a deflection.
  - check: 

- **player_1** (wolf): Dropping a hard investigator claim the second discussion starts feels less like helping the town and more like trying to railroad a lynch before anyone can ask questions. If you really had that info last night, blurting it out immediately just shuts down any actual analysis.
  - bases: `role_claim, participation, speech_content` · accuses: `player_7` · claims: `none`
  - judge: The message attacks player_7's credibility by questioning the timing of their investigator claim, framing it as a suspicious attempt to force a quick vote.
  - check: 

- **player_7** (investigator): Calling out a confirmed wolf isn't railroading, player_1, it's using the exact information the town needs. You're deflecting because you got caught.
  - bases: `own_night_result, speech_content` · accuses: `player_1` · claims: `none`
  - judge: The speaker repeats their own claimed night result that player_1 is a wolf and interprets player_1's previous speech as a deflection to avoid this accusation.
  - check: 

- **player_1** (wolf): Dropping a claim right at the start isn't using info for the town, player_7, it's forcing a quick lynch before anyone can look at the actual context. If you really investigated me, why shut down discussion instantly instead of letting people talk?
  - bases: `role_claim, participation, speech_content` · accuses: `player_7` · claims: `none`
  - judge: The message questions the motive behind player_7's investigator claim by focusing on the timing of the reveal, arguing that speaking so early is an attempt to force a lynch rather than help the town.
  - check: 

- **player_4** (villager): Player_7 dropped an investigator claim against player_1 right away, while player_1 argues it's just a quick railroad attempt. We should see if player_7 can back up this investigation with any other details before we lock in a lynch.
  - bases: `role_claim, speech_content, participation` · accuses: `—` · claims: `none`
  - judge: The message summarizes the conflict between player_7's investigator claim and player_1's counter-argument about the timing of the claim, suggesting the town get more details.
  - check: 

### Day 3

- **player_8** (villager): Player_7's investigator claim checked out when player_1 turned out to be a wolf, so we should look at player_7's past investigations if they have another one. Meanwhile, since player_4 was killed by the serial killer, we need to focus on the remaining wolf among those who haven't cleared themselves.
  - bases: `role_claim, night_events` · accuses: `—` · claims: `none`
  - judge: The speaker validates player_7's past investigator claim by using the public outcome of the day 2 lynch (player_1's role reveal) and also refers to the night 2 death to direct the town's focus.
  - check: 

- **player_5** (healer): Player_8 makes a good point about looking at player_7's past investigations. If player_7 checked someone else last night, sharing that result will narrow down our suspect pool for the last wolf.
  - bases: `role_claim, speech_content, night_events` · accuses: `—` · claims: `none`
  - judge: The message agrees with player_8's speech and urges player_7 to share their night results, which relies on player_7's existing investigator claim and the public knowledge that one wolf is left.
  - check: 

- **player_3** (wolf): Player_7 got it right with player_1, so we definitely need to hear who they checked last night. If they have another confirmed role, that gives us a much clearer direction.
  - bases: `role_claim, night_events` · accuses: `—` · claims: `none`
  - judge: The speaker is reasoning from player_7's past investigator claim about player_1 and the fact that it was confirmed by the public role reveal after the lynch.
  - check: 

- **player_7** (investigator): I investigated player_4 last night, but sadly they were the serial killer's victim. That means we still need to find the last wolf among the others who haven't been cleared.
  - bases: `own_night_result, night_events` · accuses: `—` · claims: `investigator`
  - judge: The speaker shares the result of their own night action, claiming to have investigated player_4, and references the public fact that player_4 was killed by the serial killer.
  - check: 

- **player_6** (serial_killer): Player_7 checking player_4 who turned out to be the serial killer's victim is unfortunate since it leaves us without a second clear investigation result. We should look closely at who else might be trying to ride player_7's coattails right now.
  - bases: `role_claim, night_events` · accuses: `—` · claims: `none`
  - judge: The message comments on player_7's claimed investigation of player_4 (a role claim) and the fact that player_4 was killed by the serial killer (a night event).
  - check: 

- **player_8** (villager): Player_6 makes a good point about watching out for anyone trying to piggyback off player_7's credibility. Since player_7's check on player_4 unfortunately didn't yield a new clear result due to the serial killer, we should examine who voted to lynch player_1 alongside us and look for any defensive patterns.
  - bases: `role_claim, voting_record, speech_content` · accuses: `—` · claims: `none`
  - judge: The message proposes a course of action based on player_7's claimed investigation, the day 2 voting record, and looking for specific content in players' speech.
  - check: 

- **player_5** (healer): Building on player_8's point about checking who voted for player_1, let's look closely at the stragglers who jumped on late versus those who drove it. Since player_7's check was wasted on the serial killer victim, analyzing voting patterns is our best bet to find the last wolf.
  - bases: `voting_record, role_claim` · accuses: `—` · claims: `none`
  - judge: The message proposes analyzing the voting record from the previous day, justifying this approach by referencing the fact that player_7's claimed investigation result is no longer useful.
  - check: 

### Day 4

- **player_3** (wolf): Player_7's investigator check proved right on player_1, so we should look closely at how the votes split yesterday between player_9 and player_5. Player_9 abstained and was tied in votes, which feels like a good place to start asking questions.
  - bases: `role_claim, voting_record` · accuses: `player_9` · claims: `none`
  - judge: The message refers to a past, confirmed investigator claim by player_7 and then analyzes the voting record from the previous day, specifically the split vote and player_9's abstention, to suggest a line of inquiry.
  - check: 

- **player_7** (investigator): player_3 is right to look at yesterday's tie, especially player_9 abstaining when things got tight. I'll share who I investigated last night to help us narrow down who is pushing these splits.
  - bases: `voting_record, own_night_result` · accuses: `—` · claims: `investigator`
  - judge: The speaker agrees with an analysis of the previous day's voting record and states their intention to reveal their own night investigation result to provide further evidence.
  - check: 

- **player_8** (villager): Player_7, we definitely need to hear your investigation result from last night. If player_9 abstained while things were tied, we need to weigh that against how player_6 voted for player_5 too.
  - bases: `role_claim, voting_record` · accuses: `player_9, player_6` · claims: `none`
  - judge: The message references player_7's claimed investigator role and their promised result, and also analyzes the previous day's votes by player_9 and player_6.
  - check: 

- **player_3** (wolf): Player_9, wanting to avoid cycling through ties doesn't mean we ignore abstaining when the village needed a vote. Let's hear player_7's investigation result first, but player_9's voting record from yesterday still needs addressing.
  - bases: `speech_content, voting_record, role_claim` · accuses: `player_9` · claims: `none`
  - judge: The message directly counters player_9's previous statement (speech_content) and reiterates suspicion based on player_9's abstention on the previous day (voting_record), while also referencing the need to hear a claimed investigator result (role_claim).
  - check: 

- **player_7** (investigator): I investigated player_9 last night, and they are the remaining wolf. Their abstention yesterday was a clear attempt to dodge a vote and protect themselves.
  - bases: `own_night_result, voting_record` · accuses: `player_9` · claims: `investigator`
  - judge: The speaker reveals their own night action result, claiming to have investigated player_9 and found them to be a wolf, and uses player_9's abstention vote from the previous day as supporting evidence.
  - check: 

### Day 5

- **player_8** (villager): Player 7 is gone, and player_9 turned out to be a villager, which changes the picture completely. Player_3 pushed hard on player_9 yesterday—let's look closely at who benefits from that misligation.
  - bases: `night_events, speech_content` · accuses: `player_3` · claims: `none`
  - judge: The message uses the public fact that player_9 was a villager (a night event) to question player_3's past speech pushing for that lynch.
  - check: 

- **player_3** (wolf): Player_8, everyone voted for player_9 yesterday because player_7 pointed us there with an investigation claim. Trying to pin that vote solely on me ignores how the entire village followed the same read.
  - bases: `voting_record, role_claim` · accuses: `—` · claims: `none`
  - judge: The message defends the speaker's vote on player_9 by citing the voting record from the previous day and attributing the group's decision to a role claim made by player_7.
  - check: 

- **player_6** (serial_killer): Player_3 is right, player_8. We all voted for player_9 because player_7 gave us an investigator result, so trying to single out player_3 now looks like you're deflecting.
  - bases: `role_claim, voting_record, speech_content` · accuses: `player_8` · claims: `none`
  - judge: The message references the voting record from the previous day and a role claim made by player_7 to rebut an argument from player_8, and then accuses player_8 of deflecting.
  - check: 

- **player_8** (villager): It's true the whole village followed player_7's claim on player_9, but player_3 was the one actively driving that lynch yesterday. Now that player_9 turned out to be a villager, we have to look closely at who benefited from pushing that misligation.
  - bases: `speech_content, night_events, role_claim` · accuses: `player_3` · claims: `none`
  - judge: The message accuses player_3 by arguing that their specific speech and actions pushed for the lynch of player_9, which is now known to be a mistake based on the public reveal of player_9's villager role.
  - check: 

- **player_6** (serial_killer): Player_8, you are ignoring the fact that everyone followed player_7's claim on player_9. Trying to single out player_3 now looks like a desperate attempt to shift blame off yourself.
  - bases: `role_claim, voting_record, speech_content` · accuses: `player_8` · claims: `none`
  - judge: The message accuses player_8 by analyzing their speech, which it argues is an attempt to deflect blame by focusing on player_3 for a vote that everyone made based on player_7's past role claim.
  - check: 

- **player_8** (villager): Player 6, you're jumping in way too fast to cover for player_3 instead of looking at why player_9's lynch was pushed so hard. That kind of defensive shielding points right back to you two coordinating.
  - bases: `speech_content, manner` · accuses: `player_6, player_3` · claims: `none`
  - judge: The message accuses player_6 by pointing to their recent speech defending player_3, interpreting the speed and content of that defense as suspicious.
  - check: 

- **player_6** (serial_killer): Player_8, accusing us of coordinating just because we followed a confirmed investigator's claim is a massive stretch. You're manufacturing a narrative to deflect attention off yourself now that player_9's role is flipped.
  - bases: `role_claim, night_events, speech_content` · accuses: `player_8` · claims: `none`
  - judge: The message rebuts player_8's accusation of coordination by referencing player_7's past investigator claim and the revealed roles of player_7 and player_9, then accuses player_8 of creating a false story to deflect suspicion.
  - check: 

- **player_3** (wolf): Player_8, you're acting like you didn't also vote for player_9 yourself. Pointing fingers at everyone else for following player_7's claim when you did the exact same thing makes no sense.
  - bases: `voting_record, speech_content, role_claim` · accuses: `player_8` · claims: `none`
  - judge: The message accuses player_8 of hypocrisy by pointing out that player_8 also voted for player_9, which is a direct reference to the voting record from the previous day.
  - check: 

- **player_8** (villager): Player 3, you were the one actively pushing the lynch while player_6 jumped in immediately to cover for you. That coordinated defense when our backs are against the wall is telling.
  - bases: `speech_content, participation` · accuses: `player_3, player_6` · claims: `none`
  - judge: The message accuses player_3 and player_6 of coordinating by referencing player_3's past speech pushing a lynch and the timing and content of player_6's recent speech defending player_3.
  - check: 
