<!-- editorial review of writeup/game_design_orchestration/human_in_the_loop/cache_key.skill.md by claude (claude-opus-5-5), 2026-10-28T14:05Z -->

## 1. The argument as I understood it

The page asks how a cache meant to stop AI players re-answering after a human pauses the game ended up giving a turn from one game to another, and what the fix proves. Its answer is that the cache key was built only from a turn's input. That input never named the game, yet one in-memory cache served every game on the server. Once day-1 openings were cached, two games could produce identical keys for a seat, because an opening's input depends only on the roles dealt and the rules. The sections build in this order:
- why the cache exists;
- the five design choices that combined into the bug;
- an offline test showing that matching openings are easy to produce;
- one hosted game that appears to have received another game's cached fallback pass;
- the fix (the game's id goes into the input) and its tests;
- what is still unknown about how far the bug reached, plus a short lesson about key scope and cached failures.

## 2. Findings

**1.**
- **Where:** What remains unknown: "Every recorded batch game and every captured game made all of its own day-1 calls."
- **Kind:** caveat reverses an earlier claim
- **What broke:** The game in the central case had a prompt capture (8 of 9 seats), so it is a "captured game". It did *not* make all its own day-1 calls. Read literally, this sentence contradicts the page's main evidence. I couldn't tell whether "every other captured game" was meant, or whether the case is being retracted.
- **Repair:** Exclude the identified game explicitly ("every other captured game"), and say how many games that covers.
- **Severity:** blocking

**2.**
- **Where:** Opening paragraphs and throughout: "dealt the same set of roles, received one of those failed passes at one seat"
- **Kind:** term before introduction
- **What broke:** The page never says what the game is. Seat, role, opening, pass, wolves, night, and Serial Killer are all used as if I already know them. Most importantly, the intro gives "dealt the same set of roles" as the reason for the collision, but I only learn why roles decide an opening's input in choice 5. Until then the case reads as a coincidence.
- **Repair:** Add one or two sentences early on: the game is a Werewolf-style social deduction game with seats and hidden roles; day 1 opens with each seat speaking or passing; and that opening's input is fixed by the deal.
- **Severity:** worth fixing

**3.**
- **Where:** The game that received another game's failure: "One hosted game shows a collision happening" vs. "That is an inference from records consistent with the mechanism, not an observed cache hit."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The intro and the section opener state the replay as a fact. Three paragraphs later it is downgraded to an inference. Also, the page never says whether the two games were confirmed to run in the same process with no restart between them. The previous section listed those as preconditions, and the unknowns section admits restart times were not checked.
- **Repair:** Word the case as "records indicate" from the start, and say whether the same-process, no-restart conditions were confirmed for this pair.
- **Severity:** worth fixing

**4.**
- **Where:** Adding the game to the key: "in the production image, two freshly dealt games shared no opening key."
- **Kind:** claim reads stronger than its support on the page
- **What broke:** The page's own offline result was that 59 of 66 random pairs shared no key even *without* the fix. So two fresh deals sharing no key is what you would expect from the old code too. It shows little about the deployed build.
- **Repair:** Either say these deals were chosen to share roles, as in the before-and-after check, or state what this check does and does not show.
- **Severity:** worth fixing

**5.**
- **Where:** How easily two openings matched: "A hosted game could receive another game's turn only if both ran in the same server process". Also What remains unknown: "Every recorded batch game"
- **Kind:** term before introduction
- **What broke:** "Hosted game" and "batch game" are treated as different populations but never defined. I can't tell whether batch games ran through the shared server cache, so I can't tell whether "every batch game made its own calls" is reassuring.
- **Repair:** Define hosted and batch games where "hosted" first appears, and say whether batch games share the server's cache.
- **Severity:** worth fixing

**6.**
- **Where:** The game that received another game's failure: "held opening prompts for 8 of its 9 AI seats". Adding the game to the key: "made all ten opening calls in each game."
- **Kind:** number before orientation
- **What broke:** Games appear to have 9 AI seats in one place and 10 opening calls in another. I don't know how many seats a game has, whether humans occupy some of them, or whether the test games are a different size. That makes it hard to read "five of the second game's openings" or "8 seats in all".
- **Repair:** State the seat count, and how many seats are AI, once before the first per-seat number. Then note any difference in the test setup.
- **Severity:** worth fixing

**7.**
- **Where:** Five choices, item 3: "and the model was not in the input either."
- **Kind:** missing connection
- **What broke:** The model's absence from the key is raised as part of the bug, and the central case stresses "a different model". But the fix adds only the game id. Until the last section, I assumed the fix was incomplete.
- **Repair:** In the fix section, say why leaving the model out is safe once the game is in the key (a game keeps one model), and point forward to the stated assumption.
- **Severity:** worth fixing

**8.**
- **Where:** Opening: "For nearly three weeks, that cache could also give a turn from one game to another."
- **Kind:** number before orientation
- **What broke:** The page never says what started or ended the three weeks. I inferred from choice 5 that it began when openings were cached, but I had to rebuild that myself.
- **Repair:** Tie the window to its start and end events (opening rounds cached → fix deployed).
- **Severity:** worth fixing

**9.**
- **Where:** Front matter: "with the write-portfolio-page skill, 2026-10-28; not yet reviewed."
- **Kind:** other
- **What broke:** A sentence fragment opens the page. It contains authoring metadata, a path to an internal brief, and "not yet reviewed". A hiring reader takes this as a draft label, and it weakens trust in everything that follows.
- **Repair:** Remove it, or turn it into a complete byline with no internal status or paths.
- **Severity:** worth fixing

**10.**
- **Where:** Adding the game to the key: "Two deals chosen to share six seats' roles" … "Matching roles do not guarantee matching inputs, since a wolf's input names its partners."
- **Kind:** section order
- **What broke:** Six shared roles produced five hits. The explanation for the gap comes two sentences later, after "on the fixed code, none", so for a moment it looked like the check under-counted.
- **Repair:** Put the wolf-partner explanation right after "five".
- **Severity:** taste

**11.**
- **Where:** Opening: "The record holds one such case." Also "The record identifies this as a replay"
- **Kind:** term before introduction
- **What broke:** "The record" could mean the logs, an evidence report, or the set of hosted games. In the second sentence it sounds like an independent authority confirming the replay.
- **Repair:** Name what "the record" is (e.g. the logs of the 68 hosted games), or say "the evidence".
- **Severity:** taste

**12.**
- **Where:** What remains unknown: "The lesson is about scope."
- **Kind:** more than one job in a paragraph / section order
- **What broke:** The heading promises open questions. The section also holds a remaining design assumption and the takeaway lesson. The point that a fallback is stored like a real answer appears for the third time here.
- **Repair:** Move the lesson into its own short closing section, and drop the repeat about fallbacks.
- **Severity:** taste

**13.**
- **Where:** The game that received another game's failure: "recorded 142 calls and no failures."
- **Kind:** detail that does not change understanding
- **What broke:** 142 has no reference point. Only "no failures" carries the argument.
- **Repair:** Drop the count, or say it covers the whole game.
- **Severity:** taste

## 3. Highest-impact improvements

1. Fix the "every captured game made all of its own day-1 calls" sentence, which currently contradicts the central case.
2. Introduce the game early (seats, roles, day-1 openings, passes), and explain that an opening's input is fixed by the deal.
3. Match the strength of the claims to the evidence: call the case an inference from the start, say whether same-process conditions were confirmed, and either qualify the production check or use matched deals for it.
