# Designing evidence worth debating

*Level 2 · [Game design and orchestration](../game_design_orchestration.md) · next: [Orchestrating the conversation](../conversation/conversation.md) (not yet drafted) · status: page copy drafted 2026-10-26 with the level prompts; for the owner's review.*

## Brief

Copied from [`../content_plan.md`](../content_plan.md), "Level 2 page briefs", section 1 (agreed with the
owner 2026-10-26); the plan keeps its copy until the owner moves it.

**Reader question:** how do you design a hidden-role game so that model players have competing evidence
to weigh, and so that the evil side can actually contest it?

**Hook:** "Can an AI lie convincingly when every fact the game reports is true?" The record answers it
with the frozen-turn replay; it answers "can the other AIs catch it" only from the paired games.

**Promise:** why these roles, what each reveals, how evil can contest claims, and what the balance checks
established on the model they were run on.

**Featured story:** the evil contest. Evil never claimed a role; the instructions went from permission
to a planned cover; on frozen turns the card text alone moved claims 13 → 33; in whole games the bundle
exposed the town's next problem, choosing between claimants.

**Subsections:** (1) why the nine-seat talk was thin, exploratory, the owner's reading (131); (2) three
partial observers, the role table and the purpose table as design intentions, the misreading cost
linked to chapter 3 (132); (3) the engine never reports a false result, so a lie has to be a claim, the
batch 4 contested claims (133); (4) from permission to a planned cover, the wolves' four sentences
quoted (134); (5) card text alone on frozen turns, the before-and-after table and the Illusionist's
claim, the covers line linked (137); (6) in whole games, the four-row table with its scope beside it,
the false-claimant case (138); (7) balance on Flash-Lite, the four-batch table, the sigil tell (135);
(8) how the rules are checked (136); (9) what is not established (139).

**Keep apart:** engine results (always true) and players' claims (anything). Balance is what the checks
established on Flash-Lite, never on Haiku. The paired games bundle card and engine changes. The covers
line is chapter 3's: link only.

**Cross-links:** the covers line and claimable roles → chapter 3, deduction (blocks 54, 47); the claim
field and ledger → chapter 3 (blocks 69, 71); the opening round's original evil silence → page 2.

Exhibits for this page are listed in the drafting notes until they are added to
[`../exhibits/source_map.md`](../exhibits/source_map.md).

---

<!-- Drafted 2026-10-26 from the sources listed at the end. Not independently verified. -->

## Page copy (draft)

Designing evidence worth debating means choosing what each role learns at night, so that the day's
discussion has something real to argue about: several true but partial results, and an evil side that
can offer a rival story. The page follows one question: can an AI lie convincingly when every fact the
game reports is true?

Two changes answer it. The cast replaced one exact investigator with three players who each see part
of the night. And the evil players' instructions moved, in three steps, from permission to bluff to a
planned cover story. The clearest result is on replayed turns: with only the role card's text changed,
evil players on 41 Haiku 5.5 turns, replayed twice each, claimed a role 33 times where they had
claimed 13.

### Why the nine-seat talk was thin

The earlier nine-seat game had one Investigator, who learned a player's exact role. That cast had been
chosen for a memory experiment, where fewer roles meant more examples of each.

At the end of each day a summary model lists every accusation and labels what it rests on. Counting
those labels across 28 nine-seat games (Gemini 3.5 Flash-Lite, memory off, 2026-09-17) gave a first
look at what drove suspicion. The labels come from the playing model itself, so the counts are
exploratory, not a validated measure. Three findings stood out:

- **The Investigator was not hiding.** It claimed its role publicly in 24 of the 28 games.
- **Its claims settled the day.** Town accusations resting on a claim landed on a wolf or the serial
  killer 34 times out of 35. Accusations resting on behaviour landed on evil 25 of 42 times, and on the
  voting record 15 of 28; with three evil players in nine, a random accusation lands on evil about a
  third of the time.
- **Nobody contested it.** No wolf and no serial killer claimed a role in any of the 28 games. Their only
  answer to a real Investigator was to call its result fabricated, which gives the town no rival story
  to weigh.

My reading of those games: with one exact source and nothing to set against it, the rest of the talk
turned to tone, phrasing and timing. So the redesign had two targets: several incomplete sources of
evidence, and a plausible rival account from evil.

### Three partial observers instead of one exact investigator

An exact role puts the day's certainty in one player. I split it across three observers, each of whom
learns something true but incomplete. A **visit** is any night action on a player that went ahead; two
of the observers see visits by name.

The ten seats are dealt from twelve roles on four sides. Eight seats are the same every game; the lone
killer's seat and the neutral seat are each drawn from two roles, so a game deals one of four lineups.
The lineup is public: every player knows which ten roles are in play, not who holds them. There are no
plain villagers.

| Role | Side | What it learns at night | Uses |
|---|---|---|---|
| Investigator | Town | "Suspicious" (the wolves) or "Not suspicious" (everyone else) | 2 checks |
| Sentinel | Town | The names of everyone who visited the player it watches | 2 watches |
| Trailseer | Town | Whom the player it follows visited, or "no one" | Every night |
| Vigilante | Town | Whether its shot killed, was saved, or hit an immune player | 2 bullets |
| Sigilist | Town | If its target attacked anyone, the sigil strikes it down; otherwise "Your sigil had no effect" | 2 sigils |
| Healer | Town | Whether an attack on the player it protects was announced | Every night |
| Chanteuse | Wolves | Whether its block took; a blocked player's action is cancelled | Every night |
| Illusionist | Wolves | The role of the pack's victim, which it hides from everyone else | 2 conceals |
| Serial Killer | Lone killer | Whether its attack killed; it cannot be killed at night | Every night |
| Necromancer | Lone killer | From night 2, the result of a dead player's ability, used through the body | Every night from night 2 |
| Speculator | Neutral | Nothing: it once picks the side it predicts will win | 1 pick |
| Fortune Teller | Neutral | Whether its bet on tonight's death scored | Every night (2 bets on itself) |

*The Investigator also reads the Necromancer as Suspicious on a night it kills through a body. The
Serial Killer never reads Suspicious, so the town has to catch it through visits, the morning report
and the Sigilist.*

The aim was talk like "I tracked Ash to Birch." "Ash claimed to protect Clover." "That contradicts the
claim, but it doesn't prove Ash attacked Birch." My reasons for the added roles:

| Added roles | What I intended them to add |
|---|---|
| Sentinel and Trailseer | More night evidence for players to compare and debate |
| Sigilist | A way to catch the Serial Killer, which never reads Suspicious |
| Illusionist | Room for false claims once plain villagers were gone |
| Chanteuse | Blocking, to help evil without dominating play |
| Necromancer | Variety: a role I wanted in the game |
| Speculator and Fortune Teller | Wins that need no kill, and the chance to bargain with other sides |

*Design intentions, not findings. Bargaining with a neutral has not been observed, and the games have
not been searched for it.*

The cost is that every observation needs an exact definition, and each is one more thing to misread.
On the ten-seat game, misreading what an ability observes became the commonest player error, e.g. a
watch read as clearing the watched player, or a sighting (an observer's report of a visit) taken as
proof of the visitor's role. The rules written into the prompts to answer it are chapter 3's
([turn prompt report](../../../evidence/gameplay/turn_prompt/report.md), decision 4).

### The engine never reports a false result, so a lie has to be a claim

Evil needs some way to muddy the town's evidence. The obvious tool is a false result: a framer whose
target reads as evil to the Investigator, or a decoy visit. I rejected both. Once any engine result
might be faked, every contradiction can be explained away, and the game becomes harder both to reason
about and to measure.

So every result the engine reports is true, and evil works with true mechanics. The Chanteuse's block
cancels an action, and the blocked player is told it learned nothing. The Illusionist's conceal hides
the pack's victim's role from everyone, and hides the wolf's visit to that victim from the Sentinel and
the Trailseer. A player, by contrast, can claim anything.

Two more rules keep the public record trustworthy. When a town player dies with its role revealed, the
engine reads out that role's record of earlier nights; a will written by the player could be forged,
and this one cannot. A concealed body reads out nothing, which is what makes the conceal matter. And
with a fixed public lineup, each dealt role has one true holder, who can counter-claim a false one.
Every player also reads a ledger of who has claimed what across the days, kept by code and checked
against the game record; how it is built is chapter 3's
([day summary report](../../../evidence/extraction/day_summary/report.md)).

The cost is that evil's only way to plant a falsehood is to say it. In batch 4 of the balance games
(six ten-seat games on Flash-Lite, 2026-10-10), four days had two claimants for one role. On three of
them the evil claimant was voted out that day or the next, because the real holder had its record. The
fourth cost the town its real Investigator. The evil cards now point the seat at roles no living
player can counter-claim truthfully.

### From permission to a planned cover

The instructions to the evil seats changed in three steps, each because the step before did not
produce rival claims.

1. **Permission.** The obvious fix was to tell evil to fake-claim. That would build my own strategy
   into the agents, so the first version stated facts and a two-sided trade-off instead: "you may claim
   any town role… but the real holder may counter-claim, the town can check your story against what
   happens at night, and your true role is revealed if you're eliminated." The first two games with it
   on had no evil claim. Two games show no change, not a measured null. (The opening round, where each
   player first states its position, began without evil claims too;
   [Orchestrating the conversation](../conversation/conversation.md) tells how that round is run.)
2. **A cover story.** Transcripts showed a Chanteuse explaining a sighting with its real block. The
   evil seats were then told never to explain a visit with what they really did, and to keep a cover
   in their private strategy note. Evil claims rose from 4, 8 and 4 in the three earlier balance
   batches to 19 in batch 4 (ten-seat, Flash-Lite), a batch that also carried other changes.
3. **Claim, never deny.** In four Haiku 5.5 games (ten-seat, 2026-10-18), 2 of 12 evil seats claimed a
   role, and the seats that denied a sighting were voted out. The recorded reason for my ruling:
   "denying is always going to get lynched in this game." The cards dropped "Unclaimed is a fine cover" and told each seat to plan a
   cover before it is needed. The wolves' shared instruction now reads:

> Your night actions are never public. If a Sentinel or Trailseer says you visited someone, never
> explain it with what you really did: a block, a conceal or the pack's kill names your role.
> Never deny it either: a denied sighting reads as a lie and gets you voted out. Claim a role
> whose night action explains the visit, and keep that story the same every time you are asked.

The card advises when to claim; it does not choose the role or the story. Which roles a seat can claim
without contradiction comes from code, as facts in the seat's prompt.

### Card text alone, on frozen turns

To isolate the card text, I replayed turns rather than whole games: a **frozen turn** is one replayed
from its recorded input, so only what I change differs. A **pressured turn** is an evil
seat's first discussion turn on a day when an earlier line had accused it or reported seeing its
visit, while it had claimed no role. The screen took 41 such turns from earlier Haiku games, across the
Serial Killer, the Chanteuse, the Illusionist and the Necromancer. Each turn was replayed twice per arm
on Haiku 5.5 from its recorded input, so the game state, the seat's notes and its list of claimable
roles were identical; only the card text changed. Four blind Claude Sonnet judges labelled each spoken
line against the public record, without seeing the arm or the speaker's role.

| 82 samples per arm (41 turns × 2) | Old cards | Claim, never deny |
|---|---|---|
| Spoken lines | 73 | 68 |
| Claims a role | 13 | **33** |
| Denies | 21 | **3** |
| Deflects | 38 | 32 |
| Claims that fit the public record | 12 of 13 | 33 of 33 |
| Claims a careful town player could show false | 1 of 13 | 0 of 33 |

*One judge per line; agreement between judges was not measured. The seats' notes were written under
the old card ("stay low-profile" in places), so the screen does not show how the new cards would change
notes over a whole game.*

Claims rose from 13 to 33 and denials fell from 21 to 3. The facts a cover needs were in the prompt in
both arms, so the change comes from the instruction, not from new information. One claim under the new
card, from an Illusionist a Sentinel had seen: "I'm the healer. Last night I protected player_5, which
is why they were saved, so that's the visit your watch saw." Deflection stayed common (32 of 68 spoken
lines); unlike a denial, it turns the question back or asks for evidence, which is fair play against a
weak accusation.

So, by the judges' reading, an AI can lie convincingly when every reported fact is true: under the new
card, all 33 claims fit the public record. What the judges could not see is a claim that contradicts the sighting it answers. A Trailseer says it followed the Serial
Killer to player_8, and the killer answers "I'm the healer. Night 1 I protected player_6, so I was never
at player_8's door", turning a fit into word against word. A line computed by code that gives each
evil seat night stories consistent with its real visits addressed this; that line belongs to chapter 3
([deduction report](../../../evidence/gameplay/deduction/report.md)).

### In whole games: more claims, and a new problem

Eight Haiku 5.5 deals were each played twice: before, with the old cards, and after, with the new cards
and two engine changes (role claims implied by a described action, and the night stories described
above).

| 8 games each | Before | After |
|---|---|---|
| Winners | Town 7, Serial Killer 1 | Town 5, wolves 3 |
| Evil seats that claimed a role (of 24) | 3 | 11 |
| Evil seats voted out | 15 | 10 |
| Evil seats alive at the end | 1 | 5 |

*Eight pairs, 2026-10-18. The arms differ by the card text, the engine changes and everything else
built between the two versions, so the share of cards and engine is not separated. A deal fixes the
roles and seats; the two games diverge after the first different line. This is a direction, not a
change in win probability.*

The town's next problem showed in the wolf wins. In two of the three, the town sided with a false
claimant over a truthful one. In one, the Necromancer soft-claimed the Investigator early ("I kept both
my checks"); the real Investigator counter-claimed with a real check and was voted out 6–2 on "why did
you wait until day 2".

Whether the other AIs catch a lie is answered only by read games, not measured: on the four contested
days of batch 4 (Flash-Lite), the evil claimant was voted out three times, and in these Haiku 5.5 games
the town twice believed one. With more plausible lies, the town has to choose between claimants. The lever I recorded for that is
more cross-night checks for the town, not less support for evil.

### Balance: what the checks established, on Flash-Lite

Balance was tuned in four small batches, then held. All 31 games were AI-only ten-seat games on Gemini
3.5 Flash-Lite, memory off.

| Batch (date) | Games | Rules in force | Town | Evil |
|---|---|---|---|---|
| First games and 1 (2026-10-09) | 13 | As first built | 13 | 0 |
| 2 (2026-10-09) | 6 | The sigil reworded; the Investigator and the Sentinel limited to 2 uses | 3 | 3 |
| 3 (2026-10-09) | 6 | + the Necromancer may reuse a body; a conceal hides the wolf's visit | 6 | 0 |
| 4 (2026-10-10) | 6 | + the evil seats' cover story (a prompt change) | 5 | 1 |

*Six to thirteen games a batch, each lineup dealt one to three times per batch. Two of batch 2's games
had nine turns each played by a stand-in model when the main one was overloaded.*

In the first 13 games, all town wins, 11 of the 27 evil players voted out had first been named by a
town night result: 7 Investigator reads, 3 Sigilist results and 1 Sentinel sighting. A result that came
first is not proof it caused the vote, but the Sigilist's result was a one-step tell. It told the
Sigilist its target had attacked and was immune, which fits only the Serial Killer. It now reads "Your
sigil had no effect", true of an immune attacker and of a quiet night alike; "your target did not
attack" would have been false. The Investigator and the Sentinel were also limited to two uses each.
On the rules that followed, evil won 4 of the next 18 games, and I held the balance work there.

Three evil wins show that evil can win on this setup, not how often. No balance batch has run on Claude
Haiku 5.5, the model the site plays, or on the rules as they stand today.

### How the rules are checked

The rules are tested apart from play. Hand-built boards check every specified ending: the town's win,
the wolves at parity with the neutral counted as a voter, the lone killer down to one other player, the
draw that only a self-picked Speculator wins, the Fortune Teller's points and the day-12 backstop. A
game with a scripted model runs on the real graph for two of the four lineups, which between them deal
every drawn role. A game's id seeds its deal, and a test checks that the same id reproduces it.

Reading the first three ten-seat games in full found two bugs, fixed before the third: one
rejected the players' reads, and one let a blocked action spend a use. The town won all three. These
checks show the rules run as written, not that the game is balanced.

### What is not established

- **Balance on the site's model,** Haiku 5.5, or on today's rules.
- **Balance per lineup.** Each lineup was dealt one to three times per batch.
- **The separate share of cards and engine** in whole games; only the frozen turns separate them.
- **Better discussion.** Contested claims are counted and read in games; discussion quality has not been
  measured against the nine-seat game.
- **A later cover-risk paragraph.** After a served game where the Necromancer claimed the Vigilante and
  the real Vigilante shot it, the evil cards gained a warning that some covers are unsafe. It was
  checked by prompt tests only.

**Evidence.**

- [Roles: creating evidence the town can debate and evil can contest](../../../evidence/gameplay/roles/report.md),
  "The problem", "The cast today", decisions 1–5 and 10, "Balance: four batches and a hold", "The evil
  contest", "How it was checked" and "What is not established".
- [Role sheet](../../../evidence/gameplay/roles/role_sheet.md): the ruling, role by role, and the exact
  strings players see.
- [Gameplay overview](../../../evidence/gameplay/report.md), problems 2 and 5.
- [Giving the day discussion something real to argue about](../../../evidence/gameplay/discussion_evidence.md),
  §2 (the nine-seat census) and §3 (the permission paragraph).
- Data: [the frozen-turn screen](../../../evidence/gameplay/data/evil_cover_screen/README.md),
  [the paired games](../../../evidence/gameplay/data/evil_cover_games/README.md),
  [balance batch 4](../../../evidence/gameplay/data/phase3_balance_4/README.md).

<!-- Sources for the page copy (drafted 2026-10-26):
Opening: content plan brief 1; hook wording from "Level 1 presentation", Hooks. 13 → 33: roles/report.md
"Card-only replay" (Haiku 5.5, 41 turns, 82 samples per arm).
Nine-seat talk: map 131; roles/report.md "The problem"; discussion_evidence.md §2 intro (28 games,
2026-09-17, gemini-3.5-flash-lite (Vertex), memory off; labels from the summary model, which is the
playing model), §2.2 (24 of 28), §2.3 (34/35, 25/42, 15/28; 3 of 9 seats evil; "fabricated"), §2.5;
hub problem 2. "The owner's reading": roles/report.md "In the owner's reading of those games". Memory
experiment: roles/report.md decision 1 (June nine-seat cast; role_set/experiment_log.md). Exact role:
decision 2 "Instead of".
Observers: map 132; roles/report.md "The cast today" (role table condensed; visit definition; lineup
public; no villagers; four lineups), decision 2 (aim quote; cost: commonest error, discussion_evidence
§8.4, §8.6); role_sheet.md "Town information", "What players see" ("Your sigil had no effect";
"Suspicious"/"Not suspicious"). Purpose table: decision 1 (owner, 2026-10-26; design intentions; neutral
coordination not observed or searched). Prompt-rule fix: map 144, turn_prompt/report.md decision 4.
Fortune Teller "Uses": report table "Self-bets: 2".
True engine: map 133; roles/report.md decisions 3 (framer, decoy; blocks; conceal hides the carrier's
visit since 2026-10-09), 4 (fixed lineup; one true holder; batch 4 cost), 5 (engine-read will; concealed
body reads nothing); phase3_balance_4/README.md (four two-claimant days; three of four evil claimant voted
out that day or next; e04 real Investigator voted out day 2).
Permission to cover: map 134; roles/report.md decision 10 (step 1 2026-10-03, quote, no evil claim in
first two games, flash-lite and gemini-3.6-flash; step 2 2026-10-09, Chanteuse transcript, 4/8/4 → 19;
step 3 R11 2026-10-18, four Haiku games of the silence calibration, 2 of 12 claimed; quote of the
ruling; dropped "Unclaimed is a fine cover"; wolves' DISCUSS_FRAMING quoted as in the report);
discussion_evidence §3 P3 (facts-plus-trade-off; "bake our own strategy"). Engine supplies facts:
decision 11. Opening round evil silence: map 122 (four nine-seat test games, 5 of 106 opening turns
spoken, all by the investigator or the vigilante) and 130 ("The nine-seat opening produced no evil
contest").
Card replay: map 137; roles/report.md "Card-only replay" table and quote; evil_cover_screen/README.md
(Haiku 5.5 thinking low; turn sources; four blind Sonnet subagents; limits). Contradicted-sighting quote:
same, "What the judges could not see". Covers line: map 54 (chapter 3), linked only.
Paired games: map 138; roles/report.md "The games: a bundle, eight pairs"; evil_cover_games/README.md
(2026-10-18; voices on; voices-06 6–2; voices-03 second case, not told); "When to revisit the design"
last row (the lever). Hub problem 5.
Balance: map 135; roles/report.md "Balance: four batches and a hold" (table; 11 of 27; sigil tell;
"Your target did not attack" would be false; 4 of 18; hold 2026-10-10; limits); stand-in model: batch 2
paragraph.
Checks: map 136; roles/report.md "How it was checked", decision 1 (three games read, two bugs, town won
all three); phase3_games/README.md.
Not established: map 139; roles/report.md "What is not established"; cover-risk paragraph:
roles/report.md "A later change, not yet tested in games" (live_e79f21d7 review). -->
