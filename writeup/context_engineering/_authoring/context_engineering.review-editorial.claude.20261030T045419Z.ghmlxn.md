<!-- editorial review of writeup/context_engineering/context_engineering.md by claude (opus), 2026-10-30T04:54Z -->

## 1. The argument as I understood it

The page asks how to get small, low-cost models playing Werewolf to reason correctly from the game state their prompt already contains. Its central answer is that code works out whatever is certain and labels where each fact came from, while the model keeps the judgement. The opening sorts the factual mistakes into four kinds, and each section pairs one kind with its fix and a before/after replay result:

- **Misread or invented facts:** clearer engine output and complete rules.
- **Distorted earlier days:** summaries that keep the source of each statement, with a guard in code.
- **Information the decision ignored:** the model writes its assessment before it acts.
- **Facts the model didn't connect:** a deduction engine works out certain conclusions in code.

The method paragraph says up front that replays show whether one failure was removed. They do not give an error rate across whole games.

## 2. Apply the explanation

**Probe:** In the Healer case, suppose the Healer is roleblocked on night 1 but nobody reports following anyone to the Healer. What does the deduction engine add to the prompt, and what is still left to the model?

**Answer from the page:** The engine would still print the certain line. "Only the Chanteuse, a wolf, can roleblock, and a block is a visit", so it would write "the Chanteuse came to you that night". It would not name anyone, because "Naming player_7 was still left to the model" even when a visit was reported. The model would have to find the Chanteuse among the other players without that lead.

**Where I had to supply a link:** The engine's lines can be "certain, true if a named claim is true, or the list of possibilities." In the original case, player_7 admitted visiting the Healer. A conditional line such as "if player_7's admission is true, player_7 is the Chanteuse" looks like exactly what the middle level is for, but the engine did not produce it. I can guess why: other visits may have gone unreported, so player_7 is not proven. The page never says this. So I can't tell where the line falls between what the engine concludes and what is left to the model. That line is the chapter's central principle, so this matters.

## 3. Findings

**1.**
- **Where:** "Information the model has but does not use", the passage "a judge reading only the written reasoning could name the player voted for 92.5% of the time"
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The section names its failure as information that decisions did not use. The evidence shows that the vote came to match the written reasoning more closely. The caveat then says this "does not show the reasoning itself got better", so nothing shows the reasoning now uses the information. The fix fits a different failure, "decisions don't follow stated reasoning", from the one the heading announces. I also couldn't tell who or what "a judge" is.
- **Repair:** Either restate the failure as decisions not following the assessment, or explain how writing the assessment first makes the facts get used. Name the judge in a few words (for example, a separate model).
- **Severity:** blocking

**2.**
- **Where:** "Information the model has but does not use", the passage "the game's current model reported no reasoning tokens in 4 samples of 10"
- **Kind:** missing connection
- **What broke:** The paragraph never says why missing reasoning tokens matter, or what was decided. I guessed that the format now goes in the prompt as text, but the page doesn't say so. "Reasoning tokens" is also never tied to the "thinking setting" used in the next section, so I couldn't tell if they are the same mechanism.
- **Repair:** State the consequence (the model skipped its hidden thinking) and the choice that followed. Link "reasoning tokens" to the "thinking setting" vocabulary. Cut "Other low-cost models also…" unless it changed the decision.
- **Severity:** worth fixing

**3.**
- **Where:** Opening paragraph 2 and "Earlier days…", the passages "code works out what is certain, and the model keeps the judgement" and "never judges whether it is true; judging is left to code"
- **Kind:** unit or term changes meaning
- **What broke:** "Judgement" first belongs to the model, then two sections later to code. I worked out that the second use means checking a claim against the record, not strategic judgement. On a first read, the second sentence seems to reverse the principle.
- **Repair:** Use a different word for checking a claim against the record (for example "checking" or "verifying").
- **Severity:** worth fixing

**4.**
- **Where:** "Earlier days…" table, Claims row, the passage "for a player who filled none, such as a human"
- **Kind:** term before introduction
- **What broke:** This is the only sign that humans play, and it is buried in a table cell. "Claim fields" are also undefined. I can't tell whether every AI turn has structured fields for role claims. That affects how I read the Investigator story: if speakers fill their own claim fields, how did a summary misrecord the Investigator's claim? Was this before claim fields existed?
- **Repair:** Say in the opening, or before the table, that humans can play. Define claim fields in one clause. Say whether the Investigator incident came before or after claim fields.
- **Severity:** worth fixing

**5.**
- **Where:** Claims row example, the passage "says they read Suspicious. Record: player_9 was revealed as illusionist, as claimed."
- **Kind:** missing connection
- **What broke:** To check this example you need to know what an Illusionist is and that it reads Suspicious. The page explains neither, so "as claimed" can't be checked and the example doesn't show how the record check works.
- **Repair:** Use an example whose logic is visible on the page, or add a short note saying why the record confirms the claim.
- **Severity:** worth fixing

**6.**
- **Where:** Opening paragraph 1, the passage "did not stop a player hunting for 'the remaining wolf' when none was left"
- **Kind:** missing connection
- **What broke:** This is the first example of failure, but no section returns to it. I couldn't tell which of the four kinds it belongs to (misread? not connected?) or whether it was fixed.
- **Repair:** Assign it to one of the four kinds and show its fix, or replace it with an example that a later section resolves.
- **Severity:** worth fixing

**7.**
- **Where:** Opening paragraph 2, the passage "they had information their decisions did not use; and they had the facts but did not connect them"
- **Kind:** missing connection
- **What broke:** Kinds 3 and 4 sound the same when introduced. The difference only appears after reading both sections: kind 3 is the decision departing from the assessment, kind 4 is a missing inference.
- **Repair:** Sharpen the wording of those two kinds in the list so the difference is visible up front.
- **Severity:** worth fixing

**8.**
- **Where:** "Facts the model has but does not connect", the passage "Larger models made the link with the engine off (9 and 10 in 10)… nearly three times as long"
- **Kind:** missing connection
- **What broke:** The comparison is laid out, but the conclusion isn't drawn. I inferred that the engine was preferred over a bigger model or higher thinking setting because of cost and speed. "The engine works out the certain step once, in code" hints at this without saying it.
- **Repair:** State in one sentence the criterion that decides between the engine and a bigger model or higher thinking setting.
- **Severity:** worth fixing

**9.**
- **Where:** "Facts the model has but does not connect", last paragraph, the passage "A test that swaps roles a player cannot see requires the engine's lines to stay the same."
- **Kind:** more than one job in a paragraph
- **What broke:** The sentence is dense. I had to connect it back to "what that player is allowed to know" to see that it tests the engine for leaks of hidden information. It then shares a paragraph with an unrelated statement about who wrote the code.
- **Repair:** Say what the test guards against (the engine using hidden roles). Then either separate the authorship statement or move it to a project or method page.
- **Severity:** worth fixing

**10.**
- **Where:** Diagram and opening, the passages "the game master's record" and "a read of every player"
- **Kind:** term before introduction
- **What broke:** "Game master" first appears as if it were a separate actor. Only the later table shows it is the engine. "A read" is used as a noun before section 3 explains it. "The deduction engine" also appears in the diagram before section 4 explains it, though the caption partly covers that.
- **Repair:** Say "the engine's public record" or define "game master" at first use. Gloss "read" as "an assessment of each player."
- **Severity:** taste

**11.**
- **Where:** "Facts the model misreads or invents", the passage "words each of the player's night results as its own action on a named night"
- **Kind:** other (ambiguous wording)
- **What broke:** "Its own action" could mean a separate line for each result or a first-person phrasing of the player's action. A short before/after example would settle it.
- **Repair:** Show one night result before and after the change.
- **Severity:** taste

**12.**
- **Where:** Opening paragraph 1, the passage "Each AI player's turn is one model call"
- **Kind:** missing connection
- **What broke:** The page has no parent, so it is opened directly, but the game isn't named until "Lying is part of Werewolf". The basic setup (hidden roles, wolves against everyone else, voting players out) is never given. Most readers can fill this in, but "wolf" and "roles" come before any orientation.
- **Repair:** Name Werewolf and its win condition in the first sentence.
- **Severity:** taste

## 4. Highest-impact improvements

1. Make the "information not used" section's evidence match its stated failure, or reframe the failure. Say what the reasoning-token result led to.
2. Make the boundary between code and model concrete. Say why the engine stops at "the Chanteuse came to you" and doesn't print a conditional about player_7. Use separate words for checking claims and strategic judgement.
3. Tie up the loose ends: assign the opening "remaining wolf" example to one of the four kinds, introduce human players and claim fields before the table, and state why the engine was chosen over larger models.
