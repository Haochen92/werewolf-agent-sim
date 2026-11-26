# Restart recovery rewrite · 2026-11-22

The reader should be able to predict what a returning player sees and which turn the engine runs. The parent introduces both records. A direct arrival needs a sentence about who can see which messages. The owner requested the rewrite after reviewing the proposed approach.

1. Follow a player back into the game after a disconnect, then explain what the server must restore after a crash.
2. Show the saved human turn in the manual check and the separate integration test. Use a table for the practical limits.
3. Follow one illustrative accusation through two possible crash timings.

Sample passage: Suppose the first speaker accuses Alex. The database saves the speech, but the latest checkpoint still says it is that speaker’s turn. After the restart the model gets another turn and might accuse Sam. The server keeps the first speech in the history because that place in the discussion is already filled. The engine can still pass the second speech to the next AI player.

Evidence comes from the two production reports and the manual run in commit 5d63349a. The open questions are whether a forced stop between writes reproduces the disagreement and how much repeated model work costs on the hosted server.

## Review resolution

The cold reader could explain both speech outcomes. Revised the pending-question row to distinguish seeing a prompt from resubmitting an answer. Limited the speech example explicitly to a checkpoint with the turn still open. The claims reader identified that a disconnected game may pause. Revised the opening to describe what remains in memory.

The page copy is about 729 words, below the Level 2 guide of 1,200–2,000. One worked turn covers both outcomes.
