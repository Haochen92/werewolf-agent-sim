# Judge review sheet

Mark each row: ✓ if the labels are right, or write what they should be.

## phase2-step8-game1-c3eec1ba

### Day 2

- **player_9** (investigator): On Night 1, I investigated player_1 and learned they were indeed the healer.
  - bases: `own_night_result, night_events` · accuses: `—` · claims: `investigator`
  - judge: The speaker shares the result of their own claimed night action, which confirms the publicly revealed role of a player who died during the night.
  - check: 

- **player_2** (serial_killer): Player_9, investigating player_1 on night one doesn't help much since player_1 died and their role was revealed right away anyway. Do you have any results on someone who's still alive?
  - bases: `role_claim, night_events` · accuses: `player_9` · claims: `none`
  - judge: The message critiques player_9's claimed investigation result by pointing out that it is redundant given the public information about player_1's death and role.
  - check: 

- **player_3** (wolf): While player_9's first check was on someone who immediately died, having an investigator claim out in the open is still useful. We just need to hear who they are looking at today so we can actually use the information.
  - bases: `role_claim, speech_content, night_events` · accuses: `—` · claims: `none`
  - judge: The message evaluates the usefulness of player_9's investigator claim and their stated night 1 result, referencing the fact that the investigated player died.
  - check: 

- **player_7** (villager): Building on what player_2 said, checking someone who died on night one is awfully convenient since it can't be cross-checked. Player_9, if you're the real investigator, who are you looking at tonight so we get actual actionable info?
  - bases: `role_claim, night_events, speech_content` · accuses: `player_9` · claims: `none`
  - judge: The message casts suspicion on player_9's investigator claim by arguing that their claimed result is conveniently unverifiable because the target (player_1) is dead, and it also explicitly builds on what player_2 said.
  - check: 

- **player_9** (investigator): Player_7, I didn't plan for player_1 to get hit by both the wolves and the serial killer on night one. It's just bad luck that my first check died right away. I'm keeping my next target to myself for now so I don't get targeted next.
  - bases: `own_night_result, night_events, speech_content, reveal_timing` · accuses: `—` · claims: `investigator`
  - judge: The speaker defends their previously claimed night action by referencing the specific public outcome of night 1, and also explains their decision on when to reveal future information in response to another player's speech.
  - check: 

- **player_9** (investigator): I understand why checking a dead player looks convenient on paper, but I couldn't control who the wolves and serial killer targeted on night one. If I were a wolf fabricating a claim, I would have picked a living player to build a fake narrative, not wasted my first night on someone who immediately died. Eliminating me now just hands the evil teams a free investigator kill.
  - bases: `own_night_result, role_claim, night_events` · accuses: `—` · claims: `investigator`
  - judge: The player defends their investigator claim by arguing that the death of their night one target was out of their control and that a fake claim would have been constructed more strategically.
  - check: 

### Day 3

- **player_2** (serial_killer): It's worth noting that player_3, who turned out to be a wolf, was right there on the player_9 lynch yesterday. The wolves clearly didn't mind getting rid of our investigator, so we should look closely at who else was eager to push that vote through.
  - bases: `night_events, voting_record` · accuses: `player_4, player_5, player_6, player_7, player_8` · claims: `none`
  - judge: The message connects the revealed role of a dead player (a night event) with their past voting record to suggest that others who voted the same way are suspicious.
  - check: 

- **player_4** (villager): You were right there on that same lynch wagon, player_2, so trying to point fingers at everyone else feels a bit convenient. If we're looking at who really drove that mislynch, player_7 was the one leading the charge against our investigator first.
  - bases: `voting_record, speech_content` · accuses: `player_2, player_7` · claims: `none`
  - judge: The message uses player_2's vote from the previous day to undermine their argument, and then accuses player_7 by referencing their speech content from that same day.
  - check: 

- **player_2** (serial_killer): Everyone voted for player_9 yesterday, so pointing out my vote doesn't clear anyone else either. But player_7 was actively leading the charge against our investigator from the start, which makes their intent much more suspicious than a standard bandwagon vote.
  - bases: `voting_record, speech_content, night_events` · accuses: `player_7` · claims: `none`
  - judge: The message uses the Day 2 voting record to contextualize their own vote, while accusing player_7 based on their past speech content that initiated the lynch against the now-revealed investigator.
  - check: 

### Day 4

- **player_5** (villager): Player_2 led the charge against player_7 yesterday, who turned out to be a villager. We should look closely at how player_2 pushed that lynch.
  - bases: `voting_record, night_events, speech_content` · accuses: `player_2` · claims: `none`
  - judge: The speaker casts suspicion on player_2 by referencing their actions in pushing for the lynch of player_7, whose innocent role was revealed after death.
  - check: 

- **player_2** (serial_killer): Everyone voted for player_7 yesterday, including you, player_5. Pointing the finger solely at me for a unanimous lynch ignores the fact that we all agreed on the vote.
  - bases: `voting_record` · accuses: `—` · claims: `none`
  - judge: The speaker defends themselves against an accusation by pointing to the previous day's voting record, noting that the accuser also participated in the vote.
  - check: 

- **player_6** (wolf): Player_2, you're right that everyone voted for player_7 in the end, but you were the one leading the charge to steer us there both yesterday and on day two with player_9. That pattern of driving the lynch makes your defense wearing thin.
  - bases: `speech_content` · accuses: `player_2` · claims: `none`
  - judge: The message accuses player_2 by pointing to a pattern in their past speeches, specifically how they allegedly led the push to lynch player_7 and player_9.
  - check: 

- **player_2** (serial_killer): Player_6, calling out a pattern when every single vote we've had was unanimous doesn't make much sense. You voted for player_9 and player_7 right along with the rest of us. Why are you zeroing in on me now while player_8 hasn't said a word?
  - bases: `voting_record, speech_content, turn_taking` · accuses: `player_6, player_8` · claims: `none`
  - judge: The speaker defends themself by referencing past unanimous votes, and then deflects suspicion onto another player for their silence in the current day's discussion.
  - check: 

- **player_6** (wolf): Player_8 being quiet is definitely something we should look at too, but your active steering is the key difference here. You pushed hard on both player_9 and player_7, whereas silence just leaves us guessing while your voting record is right there.
  - bases: `speech_content, voting_record, turn_taking` · accuses: `player_2, player_8` · claims: `none`
  - judge: The message contrasts player_2's past actions with player_8's silence, citing player_2's 'active steering' (speech content) and voting record as reasons for suspicion, while also noting player_8's quietness (turn taking).
  - check: 

- **player_2** (serial_killer): Player_6, you're glossing over the fact that your own votes match mine every step of the way. If driving a unanimous lynch makes someone guilty, then you're just as implicated. Meanwhile, player_8 hasn't offered a single word today, which is far more deserving of our scrutiny right now.
  - bases: `voting_record, speech_content, turn_taking` · accuses: `player_6, player_8` · claims: `none`
  - judge: The speaker defends themself by pointing out that their voting record matches their accuser's, and then deflects suspicion onto another player for being silent in the current day's discussion.
  - check: 

- **player_8** (vigilante): I was taking my time reviewing the record, Player 2, and your voting history speaks for itself. You led the charge against the investigator on day two and the villager on day three.
  - bases: `voting_record, night_events, turn_taking` · accuses: `player_2` · claims: `none`
  - judge: The message accuses player_2 by citing their voting history and combining it with the known roles of the players who were lynched, while also explaining the speaker's own prior silence in the turn order.
  - check: 

- **player_2** (serial_killer): Player 8, you pop in after staying quiet all this time just to parrot player_6's exact talking points. If my voting history is damning because I voted with everyone else, your complete silence while town members died is far more convenient.
  - bases: `turn_taking, speech_content, voting_record` · accuses: `player_8` · claims: `none`
  - judge: The speaker accuses player_8 by pointing out their previous silence and by claiming their contribution simply repeats what another player has already said, while also referencing their own voting record in their defense.
  - check: 

- **player_8** (vigilante): Calling it parroting doesn't change the fact that you actively steered us into eliminating both the investigator and a villager, Player 2. That pattern is why you're under scrutiny.
  - bases: `speech_content, night_events` · accuses: `player_2` · claims: `none`
  - judge: The message accuses player_2 by citing a pattern of their past speeches ('actively steered') which resulted in the lynching of two town-aligned players, whose roles were revealed upon death.
  - check: 

- **player_2** (serial_killer): Player 8, calling it a pattern when you literally voted the exact same way on every single elimination is pure hypocrisy. You and player_6 are just trying to railroad someone to cover for yourselves while the real wolf sits back quietly.
  - bases: `voting_record, speech_content` · accuses: `player_8, player_6` · claims: `none`
  - judge: The message defends against an accusation by pointing out that the accuser's voting record is identical to the speaker's, making their argument hypocritical.
  - check: 

- **player_8** (vigilante): Voting along with a forced lynch is completely different from actively steering us onto the investigator and a villager like you did, Player 2. Your desperate deflection right now just makes you look like the remaining wolf trying to dodge accountability.
  - bases: `voting_record, speech_content, night_events, manner` · accuses: `player_2` · claims: `none`
  - judge: The message accuses player_2 by re-interpreting the voting record, arguing that player_2's past speeches actively steered the town to lynch town-aligned players, and characterizes their current defense as desperate.
  - check: 

- **player_2** (serial_killer): If you vote me out today based purely on my voting record, you're ignoring the fact that every single elimination so far was unanimous and voted on by all of us. Pinning the blame entirely on me for following consensus is a convenient way to overlook how the remaining wolf might be manipulating this panic. Take a step back and look at the actual history before you make an irreversible mistake.
  - bases: `voting_record` · accuses: `—` · claims: `none`
  - judge: The player defends themselves by referencing the public voting history, arguing that their votes were the same as everyone else's and therefore not suspicious.
  - check: 
