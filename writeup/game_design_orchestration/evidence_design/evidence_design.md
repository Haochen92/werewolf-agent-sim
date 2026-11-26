# Designing evidence worth debating

*Level 2 · [Game design and orchestration](../game_design_orchestration.md) · next: [Orchestrating the conversation](../conversation/conversation.md) · status: page copy drafted 2026-10-26 with the level prompts; for the owner's review.*

## Original drafting brief

This brief records the earlier outline. The 2026-10-27 editorial revision and verification questions
are recorded in [the editorial notes](../editorial_notes.md).

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

In the earlier game, an Investigator could identify a player's exact role, while evil agents rarely
claimed roles of their own. That left the town with a strong source of information and few competing
accounts to evaluate.

I redesigned the information available to both sides. Town roles now observe different, incomplete
parts of the night. Evil agents can explain those observations through false role claims, while the
engine's reports remain truthful. But providing that opportunity was not enough: the agents also
needed instructions that made them use it.

The tests examined two questions: whether revised instructions produced more competing claims, and
what happened when those claims entered whole games.

### The earlier game gave agents little to contest

The nine-seat game had originally been chosen for a memory experiment, where fewer roles meant more
examples of each. Its Investigator learned exact roles, concentrating reliable information in one
agent player.

An exploratory analysis of 28 games on Gemini 3.5 Flash-Lite, with memory off, found that the
Investigator claimed publicly in 24 games. No wolf or Serial Killer claimed a role in any of them.
Evil could call the Investigator's account fabricated, but supplied no competing role claim for the
town to evaluate. The analysis used model-generated summaries and labels rather than validated
human annotations.

My reading was that this combination left little room for evidence-based disagreement: one exact
source supplied answers, while other discussion turned to tone, phrasing and timing. That motivated
two changes—distribute incomplete information across several roles, and give evil a plausible rival
account to offer. It did not establish that the information design was the only cause of thin talk.

### Give the town partial evidence it can cross-check

The ten-seat redesign replaces exact identification with three observers. Each learns something
true but incomplete. A **visit** is a night action on a player that went ahead; observing a
visit does not by itself reveal what the visitor did.

| Observer | What it learns | What remains uncertain |
|---|---|---|
| Investigator | Whether its target reads Suspicious | Some evil roles read Not suspicious |
| Sentinel | Who visited the player it watches | A visitor's identity does not establish its role or purpose |
| Trailseer | Whom the player it follows visited, or no one | A visit alone does not distinguish an attack from another action |

The intended reasoning is straightforward: an agent reports tracking Ash to Birch, but Ash claimed
to protect Clover. That challenges Ash's account without proving that Ash attacked Birch. The town
needs to compare observations with claims rather than treat one observation as an exact role reveal.

I kept the engine's reports truthful. I considered roles that could fabricate an investigative result
or a visit, but wanted observations to retain defined meanings that agents could use to test stories.
Evil can instead remove evidence: the Illusionist conceals a victim's role and the wolf's visit to
that victim. A block can prevent an action, leaving the blocked agent with no result. The [role
sheet](../../../evidence/gameplay/roles/role_sheet.md) defines these mechanics precisely.

Public records provide further checks. The lineup is known, with one true holder of each dealt role,
so a false claim can meet a counterclaim. When a town player dies with its role revealed, the engine
publishes its earlier night results; a concealed body supplies no such record. A claim ledger keeps
track of who said they held each role. These records let agents challenge a story across turns and
days, while the truth of a living player's claim remains uncertain.

This design also creates more opportunities for misunderstanding. Agents sometimes treated a watch
as clearing the watched player, or a reported visit as proof of the visitor's role. The [turn-prompt
report](../../../evidence/gameplay/turn_prompt/report.md) describes instructions added to address
those errors. Partial evidence creates a reasoning task; it does not ensure the agents reason about
it correctly.

### A plausible cover still needs an agent willing to use it

The first instructions explained that evil could claim a town role and described the risks of being
challenged. I initially avoided prescribing a fake-claim strategy. In the first two games with those
instructions, no evil agent claimed a role. That small observation prompted further work; it was
not enough to establish that permission alone could never work.

Other games exposed more specific problems. An evil agent explained an observed visit using its
real blocking ability, revealing its role. Others denied sightings rather than offering a different
explanation for the visit. Merely having a legal cover available did not mean the agent would use it.

I made the strategic instruction more explicit: prepare a cover before it is needed, claim a role
whose action explains the visit, and keep the account consistent when challenged. The revised cards
also discouraged denying sightings. This deliberately steers the agent towards maintaining a cover;
it still chooses the role and the story. Code supplies facts about which roles it can claim.

The next test isolated that instruction change from changes to the game itself.

### Isolating the instruction change

I selected 41 recorded turns in which an evil agent had been accused or reported visiting someone,
but had not yet claimed a role. Each situation was replayed twice with the old role-card instructions
and twice with the revised instructions, using Haiku 5.5. These **frozen-turn replays** kept the game
state, private notes and list of claimable roles the same. Only the card text changed.

Four Claude Sonnet judges divided the spoken responses between them, with one judge per line.
They saw the public context but not the instruction condition or the speaker's true role. The
initial labels showed a clear change in the sampled responses:

| Across 82 responses per condition (41 turns × 2) | Old instructions | Revised instructions |
|---|---:|---:|
| Role claims | 13 | 33 |
| Denials | 21 | 3 |

The revised instruction produced more claims and fewer denials in these situations. For example,
one observed evil visitor claimed to be the Healer and explained the visit as protection. The
information needed to propose a cover was already present in both conditions.

Producing a claim and producing a consistent claim are separate outcomes. The initial judges marked
all 33 revised-condition claims as fitting the public record, but that broad assessment did not
reliably capture contradictions with the sighting being answered. Later judging explicitly checked
that distinction and flagged three of those claims as contradicting a reported sighting. Some other
labels also changed, including the old-condition denial count. The [replay
record](../../../evidence/gameplay/data/evil_cover_screen/README.md) preserves both assessments.

The strongest finding is therefore the change in claiming behaviour, not that every cover was
sound. Each line had one model judge per assessment, without measured inter-judge agreement. The
41 situations were sampled twice each, not 82 independent situations, and their private notes still
came from games using the old instructions. The replay also could not establish whether another
agent would believe the resulting claim.

Contradictions in proposed covers motivated an additional engine change: supply possible night
stories consistent with the evil agent's actual visits. The [deduction
report](../../../evidence/gameplay/deduction/report.md) explains how those stories are computed.
Whole games then tested the revised instructions alongside that support.

### What changed when the claims entered games

Eight ten-seat deals were each played under an earlier and a revised version using Haiku 5.5. The
revised version combined the new cards with suggested night stories and recognition of role claims
implied by a described action. This comparison includes changes between the two versions; it does
not isolate the contribution of the cards or either engine change.

| Across eight games per version | Earlier version | Revised version |
|---|---:|---:|
| Evil seats that claimed a role, out of 24 | 3 | 11 |
| Winners | Town 7, Serial Killer 1 | Town 5, wolves 3 |

More evil agents made claims in the revised games. In two of the three wolf wins, town sided with a
false claimant over the true role holder. In one case, an evil agent implied early that it was the
Investigator. The real Investigator later counterclaimed with a genuine check, but was voted out
6–2 after being challenged about why it had waited to claim.

These cases show that competing accounts entered play and could persuade town. The paired deals
held roles and seats fixed, but the games diverged as soon as their agents responded differently.
Eight pairs do not establish a stable change in win probability, and the bundled changes prevent
attributing the outcomes to the instructions alone.

The next design question was how town agents should compare rival accounts against evidence from
several nights. I recorded further cross-night checks as the next direction. That reasoning support
would need its own evaluation; the presence of competing claims does not establish better discussion.

### What the redesign establishes—and what remains open

Rule correctness and game balance need separate checks. Hand-built game states test win conditions,
and scripted-model games exercise the real graph across two lineups that together include every
drawn role. Those checks cover execution in the tested cases. Small balance batches on Gemini 3.5
Flash-Lite also exposed overly revealing information and led to changes in abilities and cover
instructions. Evil won some later games, but the changing rules and sparse coverage of each lineup
do not establish stable balance. The [roles
report](../../../evidence/gameplay/roles/report.md) retains those results. No balance batch has tested
Haiku 5.5 or today's rules.

The replay supports a narrower conclusion: explicit cover instructions increased claiming in the
sampled situations. Whole games showed agents contesting role claims and sometimes believing a false
one. Discussion quality has not been measured against the nine-seat game, and stronger reasoning
remains a separate question. A later warning about dangerous cover choices has only prompt-test
coverage, so the results above should not be read as evaluating every subsequent instruction change.

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

<!-- Earlier page copy retained for source context, 2026-10-28.
The rewritten page above selects the explanation; full experimental records remain in evidence/.

## Page copy (draft)

The town needs evidence strong enough to challenge a claim, but incomplete enough to leave something
to debate. In the earlier game, one Investigator could identify an exact role, and evil players
rarely offered competing claims. I redesigned both sides of that exchange: several roles now observe
different parts of the night, while evil players prepare cover stories that can explain those
observations.

The distinction is between what the game reports and what a player says. The engine reports truthful
results. Players may conceal those results, misinterpret them or lie about them. The design has to
give the town ways to test a story while leaving evil a plausible story to tell.

### Why the nine-seat talk was thin

The earlier nine-seat game had one Investigator, who learned a player's exact role. That cast had
been chosen for a memory experiment, where fewer roles meant more examples of each.

At the end of each day a summary model lists every accusation and labels what it rests on. Counting
those labels across 28 nine-seat games (Gemini 3.5 Flash-Lite, memory off, 2026-09-17) gave a first
look at what drove suspicion. The labels come from the playing model itself, so the counts are
exploratory, not a validated measure. Three findings stood out:

- **The Investigator was not hiding.** It claimed its role publicly in 24 of the 28 games.
- **Claims were a strong basis for accusations.** Town accusations resting on a claim landed on a wolf or the serial
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

An exact role puts the day's certainty in one player. I split it across three observers, each of
whom learns something true but incomplete. A **visit** is any night action on a player that went
ahead; two of the observers see visits by name.

The ten seats are dealt from twelve roles on four sides. Eight seats are the same every game; the
lone killer's seat and the neutral seat are each drawn from two roles, so a game deals one of four
lineups. The lineup is public: every player knows which ten roles are in play, not who holds them.
There are no plain villagers.

| Observer | What it learns | What remains uncertain |
|---|---|---|
| Investigator | Whether its target reads Suspicious | Some evil roles read Not suspicious |
| Sentinel | Who visited the player it watches | A visitor's identity does not establish its role or purpose |
| Trailseer | Whom the player it follows visited, or no one | A visit alone does not distinguish an attack from another action |

The Investigator reads the wolves as Suspicious, and the Necromancer on a night it kills through a
body. The Investigator and Sentinel each have two uses; the Trailseer acts every night. The [role
sheet](../../../evidence/gameplay/roles/role_sheet.md) gives the full roster and ability rules.

The aim was talk like "I tracked Ash to Birch." "Ash claimed to protect Clover." "That contradicts
the claim, but it doesn't prove Ash attacked Birch."

Other roles change how that evidence can be used. The Sigilist can strike an attacker, giving the
town a way to catch the Serial Killer despite its investigative result. The Illusionist can conceal
evidence, and the Chanteuse can block actions. The neutral roles can win without killing, creating a
possible reason to bargain with another side. That last point is a design intention: bargaining has
not been observed, and the games have not been searched for it.

The cost is that every observation needs an exact definition, and each is one more thing to misread.
On the ten-seat game, misreading what an ability observes became the commonest player error, e.g. a
watch read as clearing the watched player, or a sighting (an observer's report of a visit) taken as
proof of the visitor's role. The [turn-prompt
report](../../../evidence/gameplay/turn_prompt/report.md) explains the instructions added to address
those misreadings.

### The engine never reports a false result, so a lie has to be a claim

Evil needs some way to muddy the town's evidence. One option is a false result: a framer whose
target reads as evil to the Investigator, or a decoy visit. I rejected both. Once any engine result
might be faked, every contradiction can be explained away, and the game becomes harder both to
reason about and to measure.

So every result the engine reports is true, and evil works with true mechanics. The Chanteuse's
block cancels an action, and the blocked player is told it learned nothing. The Illusionist's
conceal hides the pack's victim's role from everyone, and hides the wolf's visit to that victim from
the Sentinel and the Trailseer. A player, by contrast, can claim anything.

Two more rules keep the public record trustworthy. When a town player dies with its role revealed,
the engine reads out that role's record of earlier nights; a will written by the player could be
forged, and this one cannot. A concealed body reads out nothing, which is what makes the conceal
matter. And with a fixed public lineup, each dealt role has one true holder, who can counter-claim a
false one. Every player also reads a ledger of who has claimed what across the days, kept by code
and checked against the game record. The [day-summary
report](../../../evidence/extraction/day_summary/report.md) explains how that ledger is built.

The cost is that evil's only way to plant a falsehood is to say it. In batch 4 of the balance games
(six ten-seat games on Flash-Lite, 2026-10-10), four days had two claimants for one role. On three
of them the evil claimant was voted out that day or the next, because the real holder had its
record. The fourth cost the town its real Investigator. The evil cards now point the seat at roles
no living player can counter-claim truthfully.

### From permission to a planned cover

The instructions to the evil seats changed in three steps, each because the step before did not
produce rival claims.

1. **Permission.** I considered telling evil to fake-claim directly. That would build my own strategy
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

The card advises when to claim; it does not choose the role or the story. Which roles a seat can
claim without contradiction comes from code, as facts in the seat's prompt.

### Card text alone, on frozen turns

To isolate the card text, I replayed turns rather than whole games: a **frozen turn** is one
replayed from its recorded input, so only what I change differs. A **pressured turn** is an evil
seat's first discussion turn on a day when an earlier line had accused it or reported seeing its
visit, while it had claimed no role. The screen took 41 such turns from earlier Haiku games, across
the Serial Killer, the Chanteuse, the Illusionist and the Necromancer. Each turn was replayed twice
per arm on Haiku 5.5 from its recorded input, so the game state, the seat's notes and its list of
claimable roles were identical; only the card text changed. Four blind Claude Sonnet judges labelled
each spoken line against the public record, without seeing the arm or the speaker's role.

| 82 samples per arm (41 turns × 2) | Old cards | Claim, never deny |
|---|---|---|
| Spoken lines | 73 | 68 |
| Claims a role | 13 | **33** |
| Denies | 21 | **3** |
| Deflects | 38 | 32 |
| Claims that fit the public record | 12 of 13 | 33 of 33 |
| Claims a careful town player could show false | 1 of 13 | 0 of 33 |

*One judge per line; agreement between judges was not measured. The seats' notes were written under
the old card ("stay low-profile" in places), so the screen does not show how the new cards would
change notes over a whole game.*

Claims rose from 13 to 33 and denials fell from 21 to 3. The facts a cover needs were in the prompt
in both arms, so the change comes from the instruction, not from new information. One claim under
the new card, from an Illusionist a Sentinel had seen: "I'm the healer. Last night I protected
player_5, which is why they were saved, so that's the visit your watch saw." Deflection stayed
common (32 of 68 spoken lines); unlike a denial, it turns the question back or asks for evidence,
which is fair play against a weak accusation.

In this replay sample, the revised instructions produced more role claims, and the judges found all
33 consistent with the public record they reviewed. That does not establish whether another player
would believe them. It also leaves a gap in what the judges could assess: a claim can contradict the
sighting it answers. A Trailseer says it followed the Serial Killer to player_8, and the killer
answers "I'm the healer. Night 1 I protected player_6, so I was never at player_8's door", turning a
fit into word against word. A line computed by code that gives each evil seat night stories
consistent with its real visits addressed this. The [deduction
report](../../../evidence/gameplay/deduction/report.md) explains how those stories are computed.

### In whole games: more claims, and a new problem

Eight Haiku 5.5 deals were each played twice: before, with the old cards, and after, with the new
cards and two engine changes (role claims implied by a described action, and the night stories
described above).

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
claimant over a truthful one. In one, the Necromancer soft-claimed the Investigator early ("I kept
both my checks"); the real Investigator counter-claimed with a real check and was voted out 6–2 on
"why did you wait until day 2".

Whether the other AIs catch a lie is answered only by read games, not measured: on the four
contested days of batch 4 (Flash-Lite), the evil claimant was voted out three times, and in these
Haiku 5.5 games the town twice believed one. With more plausible lies, the town has to choose
between claimants. The lever I recorded for that is more cross-night checks for the town, not less
support for evil.

### Balance: what the checks established, on Flash-Lite

Balance was tuned in four small batches on Gemini 3.5 Flash-Lite, with memory off. The town won all
13 initial ten-seat games. Those games exposed an overly revealing Sigilist result: it identified a
target as both an attacker and immune, a combination fitting only the Serial Killer.

The result now says “Your sigil had no effect”, which is true of an immune attacker and of a quiet
night. The Investigator and Sentinel were also limited to two uses. Later batches changed
concealment, the Necromancer and evil players' cover instructions. Evil won 4 of the next 18 games,
and I held the balance work there.

Those changing rules and small batches establish that evil could win in the tested setups; they do
not estimate a stable win probability or isolate any one change. Each lineup appeared only one to
three times per batch. The [roles report](../../../evidence/gameplay/roles/report.md) retains the
batch-by-batch results. No balance batch has run on Haiku 5.5, the site's model, or on today's
rules.

### How the rules are checked

The rules are tested apart from play. Hand-built boards check every specified ending: the town's
win, the wolves at parity with the neutral counted as a voter, the lone killer down to one other
player, the draw that only a self-picked Speculator wins, the Fortune Teller's points and the day-12
backstop. A game with a scripted model runs on the real graph for two of the four lineups, which
between them deal every drawn role. A game's id seeds its deal, and a test checks that the same id
reproduces it.

Reading the first three ten-seat games in full found two bugs, fixed before the third: one rejected
the players' reads, and one let a blocked action spend a use. The town won all three. These checks
show the rules run as written, not that the game is balanced.

### What is not established

- **Balance on the site's model,** Haiku 5.5, or on today's rules.
- **Balance per lineup.** Each lineup was dealt one to three times per batch.
- **The separate share of cards and engine** in whole games; only the frozen turns separate them.
- **Better discussion.** Contested claims are counted and read in games; discussion quality has not been
  measured against the nine-seat game.
- **A later cover-risk paragraph.** After a served game where the Necromancer claimed the Vigilante and
  the real Vigilante shot it, the evil cards gained a warning that some covers are unsafe. It was
  checked by prompt tests only.

-->

