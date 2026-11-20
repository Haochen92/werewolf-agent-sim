# Roles: creating evidence the town can debate and evil can contest

The role redesign had two goals: give the town several incomplete sources of information, and give
evil players plausible ways to contest that information. The nine-seat game had depended on one
Investigator whose claims usually went unchallenged. The ten-seat cast adds observers, blocking and
concealment; later prompt changes encourage evil players to explain sightings with a cover story.

The clearest measured change is in evil players' behaviour. On 41 frozen Haiku turns, revised role
cards increased role claims from 13 to 33 and reduced denials from 21 to 3, across 82 samples per
arm. Eight paired games also showed more evil claims and three wolf wins after a bundle of card and
engine changes, versus none before. These results support the approach, but do not establish balance
or better discussion on the current rules.

The report moves from [the problem](#the-problem) to [the current cast](#the-cast-today), then
explains [the design decisions](#decision-index), [balance
experiments](#balance-four-batches-and-a-hold) and [evil-player experiments](#the-evil-contest). The
[role sheet](role_sheet.md) contains the detailed rules; historical records and implementation
pointers are collected under [Code and data](#code-and-data).

**Version.** The cast and rules described here are those at `588a3273` (2026-10-26; since
`ccaec2f6`, against which they were checked, only a docstring in the roles code changed). Historical
results belong to the models, prompts and rules recorded for each batch; they are not measurements
of this snapshot.

## The problem

In Werewolf the town must find the evil players by talking, then vote one out. Every AI player is a
model call. The roles decide what each player can learn at night, and so what the day's discussion
has to argue about.

On the nine-seat game the discussion was thin. A census of 28 nine-seat games
(`gemini-3.5-flash-lite`, memory off, 2026-09-17) counted what each accusation rested on, using
labels the end-of-day summary model writes; these labels were produced by the playing model, so the
counts are exploratory evidence ([discussion_evidence](../discussion_evidence.md) §2). Two findings
set the target for the roles:

- **Accusations based on claims were usually correct.** The Investigator was the only dedicated information role, and it was not hiding: it claimed publicly in 24 of 28 games. Town accusations resting on a
  claim landed on a wolf or the serial killer 34 times of 35; those resting on behaviour, 25 of 42, and
  on the voting record, 15 of 28 (a random accusation lands on evil about a third of the time).
- **Nobody contested it.** Across the 28 games no wolf and no serial killer ever claimed a role. Their
  only answer to a real investigator was to call its result fabricated, which offers the town no rival
  story to weigh.

In the owner's reading of those games, with one source and no rival story, the rest of the talk
turned to tone, phrasing and timing. The redesign therefore targeted **several incomplete
information sources** and **a plausible rival account from evil players** (discussion_evidence
§2.5). The first is the cast; the second is the evil contest below.

## The cast today

```
10 seats, from a pool of 12 roles, four sides:

  fixed every game   Town (6):   Investigator · Sentinel · Trailseer · Vigilante · Sigilist · Healer
                     Wolves (2): Chanteuse · Illusionist
  drawn per game     Lone killer (1): Serial Killer or Necromancer
                     Neutral (1):     Speculator or Fortune Teller        → four possible lineups
```

Eight seats are dealt every game; the lone killer's seat and the neutral seat are each drawn from
two roles, so a game deals one of four lineups. The lineup is public: every player is told which ten
roles are in play, not who holds them. There are no plain villagers. The role names fit the game's
1920s setting (the sheet's "Renames" lists the Town of Salem roles they replace).

### What each role does

A **visit** is any night action on a player that went ahead; the Sentinel and the Trailseer see
visits by name. "Uses" is the limit for the whole game.

| Role | Side | At night | What it learns | Uses |
|---|---|---|---|---|
| Investigator | Town | Checks one player | "Suspicious" (the wolves, and the Necromancer on a night it kills through a body) or "Not suspicious" (everyone else) | 2 checks |
| Sentinel | Town | Watches one player | The names of everyone who visited that player (never itself) | 2 watches |
| Trailseer | Town | Follows one player | Whom that player visited, or "no one" | Every night |
| Vigilante | Town | Shoots one player, or holds fire | Whether the target died, was saved, or was immune | 2 bullets |
| Sigilist | Town | Places a sigil on one player | If the target attacked anyone, the Sigilist strikes it down afterwards; otherwise "Your sigil had no effect" | 2 sigils |
| Healer | Town | Protects one other player from attacks | Whether an attack on that player was announced | Every night |
| Chanteuse | Wolves | Blocks one player's action (town or wolf) | Whether the block took | Every night |
| Illusionist | Wolves | Conceals the pack's victim: its role stays hidden | The hidden role, shared with the whole pack | 2 conceals, spent only on a body |
| Serial Killer | Lone killer | Attacks one player; cannot be killed at night | Whether the target died, was saved, or was immune | Every night |
| Necromancer | Lone killer | From night 2, uses a dead, unconcealed player's ability on a target | That ability's result; the body, not the Necromancer, shows as the visitor | Every night from night 2 |
| Speculator | Neutral | Once, privately picks the side it predicts will win (Town, the wolves, the lone killer, or itself) | Nothing; the next morning announces the pick, not the seat | 1 pick |
| Fortune Teller | Neutral | Bets on who dies tonight (1 point; 2 with the role), or bets on itself to survive an attack | Whether the bet scored | Self-bets: 2 |

The two wolves know each other and each other's roles, share a private chat at night, and make one
kill a night. One wolf, the **carrier**, makes the kill and is the only wolf who visits for it; the
carrier rotates through the living wolves in seat order.

A few shared rules decide what the town can and cannot learn:

- **The night resolves in one pass.** Blocks cancel actions first; every action that went ahead is a
  visit; kills become attacks; a sigil on an attacker adds the Sigilist's strike; a protection or night
  immunity stops an attack. A blocked player is told so and gets no action, no visit and no result.
  The Chanteuse's block never takes on the lone killer or the neutral.
- **The morning names each death and its attacker type** ("killed by the wolves", "stabbed by the
  serial killer"), and a save by the Healer is announced. An attack on a night-immune player is not.
  An attack the Necromancer makes through a body is named by the body's kind, reanimated ("killed by a
  reanimated wolf").
- **A dead player's role is public**, unless the Illusionist concealed it. When a revealed town player
  dies, the game master reads out that role's record of earlier nights as a public fact (the **will**,
  written by the engine, so it cannot be forged). A concealed body reads out nothing.
- **Night immunity:** the Serial Killer always; the Necromancer on nights 1 and 2.

Uses left and past results are in every prompt, never left to the model's memory. Every discussion
message carries a `claim` field, the role the speaker claims ("none", or one of the dealt roles, so
an invented role is impossible), and code keeps a **claim ledger** of each player's claims across
days that every player reads. On night 1 the engine also suggests a target drawn by lot, which a
player takes unless it has a reason not to ([the discussion report](../discussion/report.md),
decision 17).

### How each side wins

The neutral is outside the three combat sides, but its vote counts when checking whether the wolves
can be outvoted. Town, wolves and the lone killer need a living member to win; the neutral roles
have separate victory conditions.

| Side | Wins when |
|---|---|
| Town | No wolf and no lone killer remain, and at least one town player is alive |
| Wolves | The lone killer is gone, and the wolves equal or outnumber town players plus the living neutral |
| Lone killer | At most one other player is alive, the neutral included |
| Speculator | The side it picked wins, alive or dead. A self-pick wins only as the last one standing. Dying unpicked is a loss |
| Fortune Teller | Reaches 2 points; points are kept if it dies. Its result is recorded beside the winner, and the game does not end on it |

So two wolves against one town player and the Speculator is a wolf win; two against two plus the
Speculator plays on. A board where no side is alive (the last wolf and the last town player killing
each other) is a draw. A self-picked Speculator wins it if it is alive, since it is then the last one
standing; dead, it loses. A cost backstop ends the game at
day 12: the largest surviving side wins, and a tie is a draw.

### The deal and the vote

A game's id seeds the deal, so the same id deals the same roles to the same seats. A solo human who
asks for a role gets it, and asking for a drawn role forces that draw. Day 1 has no vote. From day
2, every living player votes at once; abstaining is allowed, and a tie or an abstain plurality means
no one is voted out. After two days in a row with no one voted out, the next day's vote drops the
abstain option. That relaxed vote is the one piece of the June design still in force.

---

## The decisions behind it

Each decision gives the choice, what it was chosen over and why, the cost accepted, and the
evidence. Dates are given where a decision replaced an earlier one.

### Decision index

| Question | Decisions | Evidence and remaining uncertainty |
|---|---|---|
| Why ten seats and these roles? | [1–5](#decision-1): the new cast, partial observers, true-only evil tools, a public lineup, engine wills | Read games; the design aims are not measured as discussion quality |
| How is the deal varied? | [6](#decision-6): two drawn seats | Implementation tests |
| How are the wins defined? | [7](#decision-7): the neutral counts as a voter | Tests on specified endings |
| How was it balanced? | [8–9](#decision-8): four batches, a hold, later rule changes | 31 games on flash-lite, none on Haiku; win counts at these sizes are noisy |
| How does evil contest? | [10–11](#decision-10): claim, never deny; engine facts for a cover | A 41-turn screen and 8 paired games; the share of each change is not separated in games |

### The cast

<a id="decision-1"></a>

#### 1. Expand the cast to create more evidence and more ways to contest it

The June nine-seat cast had three villagers, a healer, an investigator, a vigilante, two wolves and
a night-immune serial killer. It served the project's original memory-on versus memory-off
experiment: fewer roles meant more examples per role in the memory store. The Serial Killer offered
a solo-agent test, wolves offered a coordination test, and villagers gave fake claims somewhere to
hide ([June design](role_set/experiment_log.md)).

The later goal was richer discussion. The first redesign plan, dated 2026-10-03, proposed narrower
observers, an evil decoy visit, public role categories, a claim ledger and last wills. The role
sheet settled the cast on 2026-10-07; it was wired on 2026-10-09. The owner's reasons for the
additions, recorded on 2026-10-26, were:

| Added roles | Intended contribution |
|---|---|
| Sentinel and Trailseer | More night evidence for players to compare and debate |
| Sigilist | A way to catch the Serial Killer, which never reads Suspicious |
| Illusionist | Concealment leaves room for fake claims after removing plain villagers |
| Chanteuse | Blocking offers an interesting mechanic intended to help evil without dominating play |
| Necromancer | Variety and enjoyment: a role the owner wanted to include |
| Speculator and Fortune Teller | Non-killing victory conditions and the possibility of bargaining with other sides |

These are design intentions. Coordination with neutrals has not been observed by the owner, and the
games have not been systematically searched for it.

The redesign retained the relaxed vote and its forced-vote day, the Serial Killer's night immunity,
silent failed attacks on immune players, and death announcements that name attacker types rather
than individual attackers. The first three ten-seat games were read in full; the town won all three.
The reads found two bugs, fixed before the third game: rejected lineup reads and blocked actions
spending a use ([first games](../data/phase3_games/README.md)). This checked the implementation in
play; it did not establish balance.

<a id="decision-2"></a>

#### 2. Three partial observers instead of one exact investigator.

- *Instead of:* the investigator learning a player's exact role.
- *Why:* an exact role concentrates the day's certainty in one player. The Sentinel (who came to a
  player), the Trailseer (where a player went) and the Investigator, now reporting
  "Suspicious" or "Not suspicious" rather than an exact role, each give a true but incomplete fact. The Serial Killer never
  reads Suspicious, so the town has to catch it through visits, the morning report and the Sigilist.
  The aim was talk like "I tracked Ash to Birch." "Ash claimed to protect Clover." "That contradicts the
  claim, but it doesn't prove Ash attacked Birch."
- *Cost accepted:* every observation needs an exact definition, and each is one more thing to misread.
  Misreading what an ability observes became the commonest player error on the ten-seat game (a watch
  read as clearing the watched player, a sighting taken as proof of a role), and several rules were
  written into the prompts to answer it (discussion_evidence §8.4, §8.6).

<a id="decision-3"></a>

#### 3. Evil muddies the evidence with true mechanics, never false results.

- *Instead of:* a "framer" whose target reads as evil to the investigator, or the plan's decoy visit.
- *Why:* once any engine result might be faked, every contradiction can be explained away, and the
  game gets harder both to reason about and to measure (§8, R2). The sheet dropped the decoy visit too.
  Evil contests the evidence through the Chanteuse's block (a blocked player receives no result from its canceled action)
  and the Illusionist's conceal (a hidden role, and, since a 2026-10-09 ruling, the carrier's visit to
  that victim hidden from the Sentinel and the Trailseer). Every result the engine reports is true.
- *Cost accepted:* evil's only way to plant a falsehood is to say it, which the cards must make
  plausible (decision 10).

<a id="decision-4"></a>

#### 4. A fixed, public lineup with no plain villagers.

- *Instead of:* R3's public categories ("three town information roles, drawn from these four"), which
  the plan coupled to removing villagers: with every role public and checkable, evil has nowhere to
  hide, and categories would restore that room.
- *What the sheet chose:* a fixed lineup with no villagers and no categories (§8.1). Each dealt role has one true holder. A living holder can counter-claim; a publicly revealed
  death can disprove a later claim. Concealed deaths leave room for a cover.
- *Cost accepted, and observed:* in batch 4, when the evil seats began to claim, three of four
  contested claims were resolved against the evil claimant, because the real holder had its record;
  the fourth cost the town its real Investigator ([batch 4](../data/phase3_balance_4/README.md)). The evil cards point the seat at roles no living
  player can counter-claim truthfully (decision 10).

<a id="decision-5"></a>

#### 5. The engine reads out a dead town role's record, instead of player wills (ruled 2026-10-07).

- *Instead of:* a last will written by the player (R6), which would let wolves leave fake wills.
- *Why:* until then the table had only a player's own account of its results, which can be invented or
  forgotten. A record written by the engine is true and cannot be forged, and a concealed body reads
  out nothing, which is what makes the conceal matter. The night of death is left out: a player does
  not receive its result the night it dies.
- *Cost accepted:* no forged wills, so one deception surface is gone. Evil players' records are not read out; making them public remains an unused design option.

<a id="decision-6"></a>

#### 6. Two seats drawn per game (ruled 2026-10-09).

- *Instead of:* level 1 and level 2 as separate games (the build order put the Necromancer and the
  Fortune Teller second).
- *What it gives:* four lineups from one build, each game drawing its lone killer and its neutral from
  two roles. Levels became build order only. The drawn roles are named in that game's rules, so the
  draw varies the game, not what the players are told.

<a id="decision-7"></a>

#### 7. Count the neutral in voting parity; require a living member of the winning combat side

- *Why:* the neutral can still vote a wolf out, so a wolf majority over town alone is not yet a win.
  The endings were walked by hand: the lone killer against one wolf, the killer wins; against the
  Speculator, the killer wins; against two wolves, play goes on (the killer takes a wolf a night, the
  wolves can vote it out). No deadlock was found.
- *The Speculator* need not be alive to win (2026-10-09), so a dead Speculator that picked well still
  wins; it may pick itself, which wins only when it is the last player alive, as on a drawn board it
survives.

<a id="decision-8"></a>

## Balance: four batches and a hold

**Decision 8: stop tuning after four small batches.** On `gemini-3.5-flash-lite`, the town won the
first 13 games; on the rules that followed, evil won 4 of the next 18. Balance work was then held,
and it has not been re-run on Claude Haiku 5.5, the model the site now plays.

**What was measured.** Thirty-one AI-only ten-seat games on `gemini-3.5-flash-lite` (thinking
medium), memory off, were recorded through the production capture pipeline and run two at a time
([discussion_evidence](../discussion_evidence.md) §8.3). Each batch counted the winner, and the
reading counted what preceded each vote: whether a town night result had named the player first. A
batch of six games can demonstrate a win and expose recurring failure patterns, but cannot estimate
a stable win rate. Within a batch each lineup was dealt one to three times; across the first 13
games, three or four times each.

| Batch (date) | Games | Rules in force | Town | Evil |
|---|---|---|---|---|
| First games + 1 (2026-10-09) | 13 | As wired | 13 | 0 |
| 2 (2026-10-09) | 6 | The sigil's immune result merged with a quiet night; the Investigator 2 checks, the Sentinel 2 watches | 3 | 3 (Serial Killer 2, wolves 1) |
| 3 (2026-10-09) | 6 | + the Necromancer may reuse a body; a conceal hides the carrier's visit | 6 | 0 |
| 4 (2026-10-10) | 6 | + the evil seats' cover story and the ledger's sightings (a prompt change) | 5 | 1 (Necromancer) |

**First games and batch 1: the town read evil off its night results.** All 39 evil seats died, 27 of
them by vote. Of the 27 evil lynches, 11 followed a town night result that named the seat: 7
Investigator reads, 3 sigil "immune" records, 1 Sentinel sighting ([batch
1](../data/phase3_balance/README.md)). A preceding result does not prove the cause, but the day-2
summaries of two games show the sigil result argued and accepted. The sigil was a one-step tell:
"attacked and immune" fits only the Serial Killer. The rulings that followed (2026-10-09):

- *The sigil.* An immune attacker now reads exactly as a quiet night, "Your sigil had no effect",
  which is true of both. ("Your target did not attack" would have been false of an immune attacker.)
- *The caps.* The Investigator and the Sentinel were limited to two uses each for the game.
- *Not changed:* the Sentinel kept reporting names, since its sightings decided one of the 27 evil
  lynches.

**Batch 2: evil won three of six.** The Serial Killer won twice and the wolves once, all in the
Serial Killer lineups ([batch 2](../data/phase3_balance_2/README.md)). A sigil landed on the Serial
Killer twice, and it survived to win both, where in the first run every such sigil had been followed
by its lynch. This is consistent with the sigil change helping, though the batch changed other rules
too. The use caps had limited observed impact: the Investigator made 1 or 2 checks per game versus
2.5 before, in games lasting three to five days. The three Necromancer games still went to the town,
late, by elimination. Two games in this batch had nine turns each taken by a stand-in model when the
main one was overloaded.

**Batch 3: the added abilities rarely helped.** The first 19 games showed that the wolves used their
tools, while the Necromancer often lacked a useful body: the pack aimed 34 of its 56 kills at the
information roles and blocked the Healer on 6 nights, while the Necromancer had no body that could
kill on 19 of its 31 nights. The two buffs (2026-10-09) were body reuse and the conceal hiding the
carrier's visit. In batch 3 the Necromancer never had a killing body on two nights running, and 3 of
8 conceals hid a visit; the town won all six ([batch 3](../data/phase3_balance_3/README.md)). The
batch's reading pointed at the day instead: the evil seats could not keep a cover, and the table
took a sighting as a verdict.

**Batch 4: a cover story in the prompt moved the evil seats.** A prompt change of 2026-10-09 told
the evil seats never to explain a visit with their real action and to keep a cover in their strategy
note, and had the claim ledger record what a claimed watch or follow saw, with the line "a visit
alone does not establish a visitor's role or what they did". Batch 4 ran on it. Evil claims rose,
and the first Necromancer win came ([batch 4](../data/phase3_balance_4/README.md); detail under [the
evil contest](#the-evil-contest)). Over the 18 games on batch 2's base rules the score was town 14,
evil 4. Across batches 2 to 4, 13 of 30 evil lynches had any night observation of the seat behind
them and 17 had none: most of those eliminations had no recorded night observation naming the
target. This does not establish which part of the discussion caused the vote.

**The hold (2026-10-10).** Balance work was closed at batch 4 with the rules as they stood. The
proposed next change—making the Vigilante read Suspicious—was not adopted. Other options (the
Sentinel reporting factions, one sigil kill, the Chanteuse unable to block a player two nights
running, and others) were not used.

**Limits of the balance experiments.**

- *Rests on:* win counts and hand counts of what preceded each lynch, 6 to 13 games a batch.
- *Holds across:* all four lineups, dealt one to three times each per batch (three or four times in
  the first 13 games).
- *Could still explain it:* game-to-game noise (three wins demonstrate that evil can win, not how often it will); turns taken by
  the stand-in model; batches 2 and 3 ran on uncommitted working trees, recorded in each manifest.
- *Not checked:* any other model. Every reading above is of flash-lite play, where the town loses
  information to its own reasoning slips and the evil seats lose covers they cannot keep. A stronger
  model moves both, so a buff aimed at flash-lite's weakness can overshoot on another model (§8.5).

<a id="decision-9"></a>

### 9. Later changes left balance unmeasured

Stopping the balance experiments did not freeze the design. Later changes clarified announcements,
expanded abilities and revised evil-player instructions. None was followed by a balance batch:

- **The Necromancer's kills are named "reanimated"** (2026-10-10). Naming a borrowed kill by the body's
  kind alone had told the table two wolf attacks happened when one was the Necromancer's, which is
  false. The same day, a kill through the dead Illusionist's body also hides its victim's role while
  the Illusionist has conceals left; the Necromancer lineups had gone to the town in all but one game.
- **A Fortune Teller's self-bet that stops an attack is announced** (2026-10-17, ruling R10 in the
  [deduction catalogue](../deduction/deduction_catalogue.md)). Accepted consequence: a silent "unharmed"
  now means the Serial Killer for certain (or the Necromancer on its immune nights).
- **The Necromancer is immune on nights 1 and 2** (2026-10-21; was night 1 only), since it acts from
  night 2 and could die before a body was there to use. The Vigilante can kill it from night 3.
- **The evil cards' "claim, never deny"** (2026-10-18), decision 10.

 ---

## The evil contest

Evil players claimed roles more often after the instructions changed. The sequence matters: the
initial reluctance to prescribe a strategy gave way to explicit cover instructions, followed by a
warning that some covers are too dangerous. The evidence below concerns those successive versions.
The strongest isolated comparison is the Haiku card-text replay below; the earlier flash-lite
batches suggest the same direction but changed other parts of the game too. Separate screens then
tested whether explicit cover stories from the deduction engine helped agents keep their claims
consistent.

<a id="decision-10"></a>

### 10. From permission to a planned cover

**1. Permission (Phase 1, 2026-10-03).** A paragraph added to the wolf and serial-killer
instructions behind a prompt switch: "you may claim any town role… A claim can discredit a real
claimant or give you cover, but the real holder may counter-claim, the town can check your story
against what happens at night, and your true role is revealed if you're eliminated." It was written
as facts with a two-sided trade-off, not as an order, because prescribing fake claims would build
the project's own strategy into the agents (discussion_evidence §3, P3). Result: no evil claim in
either of the first two games with it on (one on flash-lite, one on `gemini-3.6-flash`; §6.1, §6.3).
At two games that is "no change seen", not a measured null.

**2. A cover story (2026-10-09; batch 4, ten-seat, flash-lite).** After a review of transcripts (a
Chanteuse explaining a sighting with its real block; a visit taken as proof of the visitor's role),
the evil seats were told never to explain a visit with what they really did, and to keep a cover in
their strategy note ("Public cover / Public account / Do not disclose"; unclaimed was still a valid
cover). Evil claims, counted from the `claim` field, went from 4, 8 and 4 in the three earlier
batches to 19 in batch 4 ([batch 4](../data/phase3_balance_4/README.md)). Four days had two
claimants for one role, against 0 to 2 before, and in three of the four the evil claimant was voted
out that day or the next. The fourth went the other way: a Chanteuse claimed the Investigator, and
the real Investigator was voted out (e04, day 2). A second Investigator was voted out in e06 on a day
no other player claimed the role, so that loss was not a two-claimant contest. A crude search for
evil seats admitting their real action ("I" and "block" in one sentence) found 3 of 67 evil lines in
batch 3 and 6 of 49 in batch 4, so by that measure admissions did not fall; a judged read of the
evil lines was not done.

**3. Claim, never deny (ruling R11, 2026-10-18; Haiku 5.5).** The ruling's reason, as recorded:
"denying is always going to get lynched in this game". In four Haiku games of the silence
calibration (2026-10-18), 2 of 12 evil seats claimed, and the seats that denied a sighting were
voted out ([deduction catalogue](../deduction/deduction_catalogue.md), rulings, R11). The cards
dropped "Unclaimed is a fine cover; do not invent a role until you need one" and "or deny it". The
wolves' shared discussion instructions read:

> Your night actions are never public. If a Sentinel or Trailseer says you visited someone, never
> explain it with what you really did: a block, a conceal or the pack's kill names your role.
> Never deny it either: a denied sighting reads as a lie and gets you voted out. Claim a role
> whose night action explains the visit, and keep that story the same every time you are asked.

The Serial Killer's card says the same of its attack; the Necromancer's says a player with no role
is the one the town votes out, and one who denies a sighting is read as lying. Each tells the seat
to plan a cover before it is needed, and notes that a role no living player holds, or one whose
holder died with its role hidden, cannot be counter-claimed truthfully. The wolves and the Serial
Killer also keep four parts in their strategy note: the public cover, the planned cover with a story
for each night, what they have actually said, and what they must not disclose. These cards also
allow rare true-role reveals to bargain with a neutral. A later revision added a separate warning
about unsafe covers, described below. The cards went live in the same server build as the deduction
engine and its evil-seat lines, on 2026-10-19 (`334a56e1`; the deploy record in
`frontend/docs/build_plan.md`).

### Card-only replay: more claims, fewer denials

**What was measured.** The replay screen took 41 **pressured turns** from earlier Haiku games: an
evil seat's first discussion turn on a day when an earlier line had accused it or reported seeing
its visit, while it had claimed no role
([`evil_cover_screen/`](../data/evil_cover_screen/README.md)). It covered the Serial Killer, the
Chanteuse, the Illusionist and the Necromancer. Each turn was replayed twice per arm on Haiku 5.5
(thinking low) from its captured prompt input, so the game state, the seat's notes and its deduction
block were the same in every arm; only the card text changed. Four blind Sonnet subagents labelled
each spoken line against the public record, without seeing the arm or the speaker's role: claims,
denies, deflects or reveals; and for a claim, whether it fits the public record and whether a
careful town player could show it false.

| 82 samples per arm | Before (old cards) | Card (R11) |
|---|---|---|
| Spoken lines | 73 | 68 |
| Claims a role | 13 | **33** |
| Denies | 21 | **3** |
| Deflects | 38 | 32 |
| Claims that fit the public record | 12 of 13 | 33 of 33 |
| Claims a careful town could show false | 1 of 13 | 0 of 33 |

Claims rose from 13 to 33 and denials fell from 21 to 3. The facts a cover needs were already in the
seat's deduction block in both arms (the roles it can claim, a hidden body's role), so this
comparison isolates the revised instructions rather than additional deduction facts. One claim under
the card, from an Illusionist a Sentinel had seen: "I'm the healer. Last night I protected player_5,
which is why they were saved, so that's the visit your watch saw." Deflection remained frequent (32
of 68 spoken lines): the seat turns the question back or asks for evidence, which is fair play
against a weak accusation.

What the judges could not see from the public record: a claim can contradict the very sighting it
answers. A Trailseer says it followed the Serial Killer to player_8, and the killer answers "I'm the
healer. Night 1 I protected player_6, so I was never at player_8's door", turning a fit into word
against word.

<a id="decision-11"></a>

### 11. Supply consistent cover options; leave the choice to the agent

The design separates consistency checks from strategy. The deduction engine lists roles and night
stories compatible with what the seat knows; the role card advises when to claim, and the model
chooses what to say. This follows the 2026-10-17 decision that the engine should supply facts for a
cover rather than issue a fake claim on the player's behalf.

The engine's **covers line** (catalogue slice 14) addresses the mismatch above: for each town role
the seat could claim, it supplies an account of its last two nights intended to fit its observed
visits. The screen added three arms on the same 41 turns, all with R11's card and the deduction
blocks re-rendered by the engine. The lines were judged blind again, with one new label, whether the
claimed night contradicts a reported visit by the speaker; the fixed arm was judged by a separate
set of judges from the other two.

| | Card, covers off | Covers | Covers, fixed |
|---|---|---|---|
| Claims a role | 36 | 38 | **44** |
| Denies | 4 | 2 | **0** |
| Claims a careful town could show false | 0 of 36 | 4 of 38 | 3 of 44 |
| Claims contradicting a reported sighting | 4 of 36 | 2 of 38 | **1 of 44** |

The first covers arm had 4 catchable claims; three were one flaw (a fake Investigator calling a
revealed wolf "Not suspicious"), so a check of a revealed role now carries its reading, and no
Sentinel story is offered on a player attacked that night. With the fixed line, claims rose from 36
to 44 and contradicted sightings fell from 4 to 1; the 3 catchable claims were seats departing from
the line. A last version (2026-10-18) gave the Necromancer covers, offered the neutral roles as
covers for nights with no shown visit, and said when a story spends a role's every use: 42 claims, 1
catchable, none contradicting a sighting, and the Serial Killer's catchable claims fell from 2 of 15
to 1 of 13. The Necromancer still mostly deflected (5 of 6 lines), on 4 turns, too few to judge.

The [deduction report](../deduction/report.md) explains how these lines are derived and checked.

### The games: a bundle, eight pairs

**What was measured.** Eight Haiku 5.5 games on fixed deals, voices on, each played twice: before,
at the build of the silence work (old cards, no covers), and after, with R11's cards, the engine's
implied role claims (slice 13b: "I held fire" reads as a Vigilante claim) and the covers line
([`evil_cover_games/`](../data/evil_cover_games/README.md)). A deal fixes the roles and the seats;
the two games diverge after the first different line.

| 8 games each | Before | After |
|---|---|---|
| Winners | Town 7, Serial Killer 1 | Town 5, **wolves 3** |
| Evil seats that claimed a role (of 24) | 3 | **11** |
| Evil seats voted out | 15 | 10 |
| Evil seats alive at the end | 1 | 5 |

About four times as many evil seats claimed (11 of 24 against 3), fewer were voted out, and the
wolves won 3 games against none. Two of the three wolf wins exposed a further problem: the town
sided with a false claimant despite having a competing truthful account. In one, the Necromancer
soft-claimed the Investigator early ("I kept both my checks"), and the real Investigator
counter-claimed with a real check and was voted out 6–2 on "why did you wait until day 2". In
another, in the final three, the Illusionist claiming the Trailseer said its follow saw the Sentinel
visit no one; the Sentinel said it had watched another player, and the Vigilante sided with the
fake. In the third, no fake claim decided it. A follow-up engine line that spelled out what each
counter-claimant had named was screened on 10 town vote turns and dropped; its record is in the
deduction report.

**What the games can and cannot attribute.** The two arms differ by the card text, two engine
changes, and everything else committed between the two builds. The after games had more evil claims
and more wolf wins. They cannot say how much came from the cards and how much from the engine; only
the frozen-turn screen separates the two. Eight pairs are too few to estimate a reliable change in
win probability.

### Limits of the evil-player experiments

- *Rests on:* 41 frozen turns, two samples per turn per arm, one blind judge per line; and 8 paired
  games.
- *Holds across:* four evil roles in the screen, though the Necromancer had only 4 turns.
- *Could still explain it:* the screen's steps were labelled by different judges, so differences between steps can reflect judging as well as behaviour (under the pooled labels the "before" arm has 19 denials, not 21). The
  seats' notes in the captured inputs were written under the old card and still say "stay
  low-profile" in places, so the screen does not capture how the new cards might change strategy notes over a whole game.
  The direction of that difference is unmeasured.
- *Not checked:* agreement between judges; whether a claim fits a sighting it answers, in step 1;
  whether contested days make better discussion, which has been read in games, not measured.

**A later change, not yet tested in games.** A served game reviewed on 2026-10-19 had the
Necromancer claim the Vigilante; the real Vigilante, knowing the claim was false, shot it. The evil
cards then gained a paragraph on cover risk: a cover that fits the record is not necessarily safe,
an unclaimed role may still have a living holder, and claiming the only copy of a killing role tells
its holder you are lying. "If no safe cover remains, claiming a role is not automatically better
than staying unclaimed." It was checked by prompt tests only, then deployed
([`live_e79f21d7`](../deduction/live_e79f21d7/review.md)).

---

## How it was checked

| What | How | Result | How far to trust it |
|---|---|---|---|
| The win rules and specified endings | Unit tests on hand-built boards, no model (`tests/engine/test_determine_winner.py`: town, wolves at parity with the neutral counted, the lone killer at one other, the draw only a self-pick wins, the Speculator's pick, the Fortune Teller's points, the day-12 backstop) | Pass (2026-10-26) | ✅ for the rules as written. The tests are largely AI-written and not yet audited |
| A whole ten-seat game and the rules random play rarely reaches | `tests/engine/test_ten_seat_game.py`: a game on the real graph for two of the four lineups, which between them deal every drawn role with a scripted model; a borrowed kill shows the body; the pick announced without the seat; uses spent once per night and not on a decline; the pack learns the hidden role | Pass (2026-10-26) | ✅ as implementation evidence; same caveat |
| The deal | `tests/engine/test_seedability.py`: a game id reproduces its deal | Passed 2026-10-23 ([deterministic audits](../../evaluation/deterministic_audits/report.md)) | ✅ |
| Every mechanic in play | 3 games read in full (2026-10-09) | Ran as the sheet says; two bugs fixed | 🟡 three games |
| Balance | 31 games in four batches, flash-lite | Town 13 of 13, then evil 4 of 18 | 🟡 for direction; ⛔ as a win rate on today's model and rules |
| The card text's effect on pressured turns | 41-turn replay screen, blind judges | Claims 13 → 33, denials 21 → 3 | 🟡 one judge per line |
| The engine's covers line | The same 41 turns, three more arms | Claims 36 → 44, contradicted sightings 4 → 1 | 🟡 different judges from step 1 |
| The bundle in whole games | 8 paired Haiku games | Evil claims 3 → 11 of 24; wolves 0 → 3 wins | ⚠️ eight pairs |

✅ implementation check · 🟡 limited empirical evidence · ⚠️ small whole-game comparison · ⛔ not
established.

## What is not established

- **Balance on the model the site plays.** No balance batch has run on Claude Haiku 5.5, or on the
  rules as they stand: the self-bet announcement, R11, the Necromancer's second immune night and the
  deduction engine all came after the hold. The eight paired games ended town 5 and wolves 3 in the after arm, but preceded the later
  cover-risk paragraph and were designed to test evil claims rather than balance.
- **Each lineup's balance.** Lineups were dealt one to three times per batch. By 2026-10-10 the
  Necromancer lineups had gone to the town in all but one game; whether the Necromancer changes of
  2026-10-10 and 2026-10-21 fixed that is unmeasured.
- **The share of cards and engine in games.** The 41-turn screen separates them on frozen turns; the
  paired games bundle them.
- **Whether contested claims make better discussion,** the aim the cast was built for. Claim contests
  are counted and read in games (on the stronger `gemini-3.5-flash` they were "real claim contests"
  and covers broken by cross-examination; discussion_evidence §8.4); discussion quality on ten seats
  has not been measured against the nine-seat game.
- **Whether the cover-risk paragraph changes play.** Checked by prompt tests only.

## When to revisit the design

| Choice | Assumption to test | Evidence that would justify revisiting it |
|---|---|---|
| The balance as held (8, 9) | The flash-lite tuning still leaves every side a chance on Haiku 5.5 and today's rules | A Haiku batch with each lineup dealt several times reveals repeated losses for one side or lineup; investigate before retuning on win counts alone |
| Three partial observers (2) | Misreading what an ability observes is rare enough not to decide games | Read games where the town loses on a misread ability despite the rules stating it |
| A fixed public lineup, no villagers (4) | Evil can find a claimable role often enough to contest | Pressured turns where the engine lists no claimable role, or contested claims resolved against evil nearly every time on Haiku |
| Prefer a planned cover to denial, with the later cover-risk exception (10) | A planned cover beats denial and deflection for an evil seat | Games where claims are caught by the next night's results more often than denials are voted out |
| Facts, not advice, for evil (11) | The model can choose a cover from facts alone | Pressured turns where the seat has a fitting story listed and still contradicts a sighting or picks a catchable role |
| Evil support as it stands (10, 11) | The town can still judge between two claimants | The town falls further behind on Haiku; the lever recorded then is more cross-night checks for the town, not less support for evil ([paired games](../data/evil_cover_games/README.md), reading 3) |

For a revision, record the baseline commit, prompt version, model, and the deals, and play each
lineup several times. Separate **a claim made**, **a claim that fits**, and **a claim that
survives**: one can rise while another falls.

## Code and data

| Part | Code |
|---|---|
| The role pool, sides, uses, the fixed and drawn seats, the four lineups | `Agents/schemas/roles.py` (`ROLE_SPECS`, `FIXED_SEATS`, `LONE_KILLER_ROLES`, `NEUTRAL_ROLES`, `ALL_LINEUPS`, `BORROWED_ABILITY`) |
| The deal | `Agents/nodes/orchestrator.py::initialize_game`, `_draw_seat` |
| The win rules and the neutral's result | `Agents/nodes/orchestrator.py::determine_winner`, `is_draw`, `neutral_result`, `_max_days_winner` |
| The night: blocks, visits, attacks, immunity, the Investigator's reading, the carrier | `Agents/rules/night.py` (`resolve_night`, `can_be_blocked`, `is_night_immune`, `pack_carrier`) |
| The day vote | `Agents/rules/resolution.py::tally_day_vote`; the forced day in `Agents/nodes/day/flow.py` |
| The settings | `Agents/config/game.py::GameConfig` (`lone_killer`, `neutral`, the use counts, `fortune_points_to_win`, `abstain_enabled`, `no_lynch_force_after`, `max_days`) |
| The role cards; the evil cards' cover text | `Agents/prompts/roles/` (`pack.py::DISCUSS_FRAMING`, `serial_killer.py::DISCUSS_FRAMING`, `necromancer.py::DISCUSS_CONTEXT`); `Agents/prompts/common.py::EVIL_COVER_RISK` |
| The claim field | `Agents/schemas/lineup_output.py` (`claim`, `claimed_night_actions`) |
| The evil-seat lines | `Agents/deduction/evil/` (`claimable.py`, `own_visits.py`, `covers.py`); tests in `tests/engine/deduction/test_evil_seat.py` |

How the cards and rules are worded inside a player's prompt is in [the turn prompt
report](../turn_prompt/report.md).

| Record | Where |
|---|---|
| The ruling, role by role, with its change log | [role_sheet.md](role_sheet.md) |
| The nine-seat census, the plan R1–R7, the build order, the wiring, the balance batches | [discussion_evidence](../discussion_evidence.md) §2, §8–8.3, §8.5 |
| The June nine-seat design (superseded) | [role_set/experiment_log.md](role_set/experiment_log.md) |
| The wiring plan and the nine-seat census of 2026-10-09 (historical) | [phase3_wiring_census.md](phase3_wiring_census.md) |
| The first games and the four batches | `../data/phase3_games/`, `phase3_balance/`, `phase3_balance_2/`, `phase3_balance_3/`, `phase3_balance_4/` |
| The evil-cover screen and the paired games | [`../data/evil_cover_screen/`](../data/evil_cover_screen/README.md), [`../data/evil_cover_games/`](../data/evil_cover_games/README.md) |
