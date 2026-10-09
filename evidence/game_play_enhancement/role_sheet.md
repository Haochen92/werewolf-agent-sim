# Werewolf Role Sheet

*The owner's design document, dated 6 Oct 2026, saved on 2026-10-07 as the ruling for Phase 3
(roles and cast), and consolidated on 2026-10-08 with the rulings of 7 and 8 October folded into
the body. Where it differs from §8 of `discussion_evidence.md`, this sheet wins. The text is the
owner's where the design is unchanged; the rulings are in the owner's sense and Claude's wording.
The change log at the end says what moved and when.*

## Renames

Seven roles take new names to fit the 1920s setting and move away from Town of Salem. Sentinel now
names the former Lookout; the former Sentinel is the Sigilist. Mechanics are unchanged; every rule
below uses the new names.

| Old name | New name | Side | Optional flavour line |
|---|---|---|---|
| Consort | Chanteuse | Wolves | "The Chanteuse kept you at her table all night." |
| Janitor | Illusionist | Wolves | "Mara died. Her role vanished like a stage trick." |
| Sentinel | Sigilist | Town kill | Miss: "Your sigil never burned." |
| Lookout | Sentinel | Town info | Sets a candle at one door and sees everyone who passes its light |
| Tracker | Trailseer | Town info | Follows one player's trail through the night |
| Oracle | Speculator | Neutral | The faction pick, now read as buying into a side |
| Gambler | Fortune Teller | Neutral | Bets read as fortunes told |

Kept as they were: Investigator, Vigilante, Healer, Serial Killer, Necromancer.

The side is **"Town"**, never "Villagers", everywhere the UI prints it. The wire's `villagers` id
stays until the engine renames it. The Villager role is not dealt in the ten-seat game.

## The lineup

The game seats 10 players, from a pool of 12 roles: 6 town (3 info, 2 kill, 1 protect), 2
wolves, 1 lone evil killer and 1 neutral. Eight seats are the same every game. The lone killer's
seat and the neutral seat are each drawn at random per game from two roles, unless the user chose
one, so a game deals one of four lineups.

| Seat | Roles |
|---|---|
| Town info (3) | Investigator, Sentinel, Trailseer |
| Town kill (2) | Vigilante, Sigilist |
| Town protect (1) | Healer |
| Wolves (2) | Chanteuse, Illusionist |
| Lone evil killer (1), drawn | Serial Killer or Necromancer |
| Neutral (1), drawn | Speculator or Fortune Teller |

- Built: already in the game. New: still to build.
- Level 1 and level 2 are build order only, not separate games: level 1 roles are built and
  tested first (one choice per night), level 2 roles (Necromancer, Fortune Teller) after.
- Roles considered but not chosen are listed under Deferred.

## Shared rules

Defined once, in the engine's night layer (`Agents/rules/night.py`) and in the rules prompt, so
each role card stays short. The night resolves in one pass, all actions simultaneous: blocks
cancel actions first, then every action that went ahead on a player is a visit, kills become
attacks, a sigil on anyone who attacked adds the Sigilist's retaliation, each attacked player gets
one verdict, and a conceal hides the pack's victim if that kill landed.

- **Morning report:** names each death and its attacker type (the wolves, the serial killer, the
  vigilante, a sigil). A save names the saved player and the attackers: "X was attacked by the
  wolves but was saved by the healer!" The attacked player learns of the attack from that line.
  An attack on an immune player is not mentioned.
- **Visits:** a night action on a player is a visit, seen by the Sentinel and Trailseer. A block
  is a visit; the Illusionist's conceal is a visit to the victim; a blocked player does not
  visit. Fortune Teller bets and the Speculator's pick are not visits. A Necromancer's borrowed
  body shows as the visitor.
- **Attacks:** the wolf kill, the Serial Killer, the Vigilante, the Sigilist's retaliation and the
  Necromancer's borrowed kills. Healer protection and night immunity stop attacks, the retaliation
  included.
- **Night immunity:** the Serial Killer always; the Necromancer on Night 1 only.
- **Roleblock:** only the Chanteuse blocks. A block takes on town and on wolves; the Serial
  Killer, the Necromancer and the neutral can never be blocked. A blocked player is told "You were
  roleblocked" and gets no action, no visit and no result that night. A block that did not take
  tells the Chanteuse so (accepted: it outs the target as the lone killer or the neutral).
- **Investigator results:** wolves read "Suspicious". So does the Necromancer, on nights it
  attacks. Everyone else reads "Not suspicious".
- **Death reveal:** a dead player's role is public, unless the Illusionist concealed it, when the
  report reads "Their role is hidden by an illusionist." Concealed roles are revealed at game end
  and shown in the X-ray.
- **The dead role's record (the will):** there are no written wills. When a town player dies and
  the role is revealed, the GM reads out that role's night record as a public fact, with the
  reveal: what it did each earlier night and what came of it. The state is updated first, then
  announced. The night of death is left out, because a player does not receive its result the
  night it dies (this balances the game; Town of Salem does the same). Neutrals are never read
  out. Evil's records are a dial, off to start; if switched on, the Illusionist's learned role
  stays hidden or the will undoes the conceal. A concealed body reads out nothing. The Vigilante's
  immune result is read out.
- **Sides:** Town, the Wolves, the lone evil killer and the neutral each win on their own terms;
  the rules are under Win logic below.
- **Formal claims and accusations:** accusations are already structured, through the
  addressed-target tags on every message. Role claims get a `claim` field on the day discussion
  output, an enum of the dealt roles plus "none", so an invented role is impossible at the schema
  level; it feeds the claim ledger directly, and the summariser's transcription becomes a
  cross-check. A prompt epoch.
- **A night off:** a role may decline to act only when acting has a cost. The Vigilante (hold
  fire, as built), the Sigilist (2 sigils) and the Illusionist (2 conceals; its choice is
  conceal tonight or not) get a no-action option; the Necromancer gets "Stay put tonight", and is
  held to it when no usable body exists; the Speculator may answer "not yet" on any night, since it has no deadline.
  Every-night roles with no cost act every night: the Healer, the Investigator, the Sentinel, the
  Trailseer, the Chanteuse, the Fortune Teller, and the killers (the pack and the Serial Killer
  always attack someone).
- **State in every prompt:** uses left and past results are given to agents each turn, never left
  to memory. Each wolf gets its own private result for its skill.
- **The public alive-roles census** (cast minus revealed dead, written by code) cannot subtract a
  concealed death, so it says so in one phrase ("one of these is dead: a body whose role is
  hidden") and the count stays exact.

## Town information

Three seats. Each gives partial evidence; together they trace wolves from three directions.

| Role | Status | Acts | What it does |
|---|---|---|---|
| Investigator | Built, changed | Every night | Checks one player: "Suspicious" or "Not suspicious" (see Shared rules) |
| Sentinel | New, level 1 | Every night | Watches one player and learns the names of everyone who visited them |
| Trailseer | New, level 1 | Every night | Follows one player and learns whom they visited, or "no one" |

- Investigator is now a pure wolf detector. The Serial Killer never reads suspicious; town catches
  it through visits, the morning report and the Sigilist.
- Sentinel and Trailseer see a Necromancer's borrowed body, never the Necromancer itself. An agent
  Sentinel or Trailseer must be told, in the rules prompt, that a dead name at a door is a
  borrowed body (level 2). Whether the Sentinel reads "Y was lifted from the grave and visited Z"
  or just the visit is open.
- A Chanteuse block leaves an info role with no result that night, and the role knows it was
  blocked.
- The Sentinel can catch both wolves on one night, since the carrier and the Illusionist both
  visit the victim. Accepted for now; the dial is "the Sentinel reports factions instead of
  names", pulled only if the balance run shows it.

## Town killing and protection

Three seats: one killer acting on suspicion, one on prediction, and one protector.

| Role | Status | Acts | Uses | What it does |
|---|---|---|---|---|
| Vigilante | Built | Night | As built (2 bullets, misfire penalty as built) | Shoots one player |
| Sigilist | New, level 1 | Night | 2 sigils | Places a sigil on one player. If they attack anyone tonight, the Sigilist kills them afterwards. The victim still dies. |
| Healer | Built | Night | Every night | Protects one other player from attacks |

- The Sigilist visits its target, so a Sentinel can see the sigil being placed. A Sentinel's own
  visit is not among the visitors it is told of (it knows it went).
- "Attacked" means any kill that went ahead (not blocked), whatever came of it: a saved or immune
  victim still counts. The retaliation is an ordinary attack, so the healer's protection saves the
  attacker from it, and the morning report names the death as "struck down by a sigil".
- The Sigilist learns all three outcomes: the target attacked and was struck down; attacked but
  was unharmed (the Serial Killer tell, hard evidence for a lynch); attacked but the healer saved
  them. Otherwise "Your target did not attack tonight."
- A sigil is spent when placed, hit or miss. A sigil on a Vigilante who shoots kills the Vigilante.
- An action a block cancelled spends nothing: a blocked shot keeps its bullet, a blocked sigil its
  sigil (ruling from game2, 2026-10-09: the vigilante lost a bullet to a block).
- Sigilist vs. Necromancer: no kill and no trace, because the borrowed body made the attack.
- Vigilante can kill the Necromancer from Night 2, but not the night-immune Serial Killer.

## Wolves

Two wolves share one kill each night. Each also has one skill.

**Pack rules**

- Wolves know each other and share a private wolf chat.
- One wolf, the carrier, performs the kill and is the only wolf who visits for it. The carrier
  rotates through the living wolves in seat order; a lone wolf always carries. (Naming a
  different carrier in chat was in the draft and is not built: the rotation only, 2026-10-09.)
- There is no pack vote: after the chat, the carrier alone names the target.
- A wolf may carry the kill and use its skill on the same night.
- Prompt flow: the wolf chat, the carrier's target, then one short skill prompt per wolf.
- The wolf chat: wolves speak one at a time, the carrier first in each round; a wolf may pass;
  hard cap of three rounds; the talk ends early when both wolves pass back to back; the prompt
  shows the rounds left. A lone wolf has no chat.

**Skills**

| Skill | Status | Uses | What it does |
|---|---|---|---|
| Chanteuse | New, level 1 | Every night; the same target is allowed | Blocks one player's night action (town or wolf; see Roleblock) |
| Illusionist | New, level 1 | 2 conceals | Conceals the pack's victim and privately learns their role |

- A conceal is spent only when a body is actually concealed; a saved or immune victim keeps the
  use, because the Illusionist cannot know in advance.
- Illusionist conceals hide roles from everyone except the engine. The Fortune Teller's role bonus
  is still scored correctly (so a two-point result tells her the hidden role; accepted).
- Concealed bodies cannot be borrowed by the Necromancer.

## Lone evil killer

One seat. Both options work alone and win by being the last standing.

| Role | Status | Acts | What it does | Counters |
|---|---|---|---|---|
| Serial Killer | Built, level 1 | Every night | Attacks one player. Night-immune. Never reads suspicious. | Sentinel and Trailseer trails, the morning report, Sigilist evidence, lynch |
| Necromancer | New, level 2 | From Night 2 | Uses a dead player's night ability (rules below) | Vigilante from Night 2, Investigator on attack nights, lynch |

**Necromancer rules**

- Night 1: no action, immune to attacks. From Night 2 it can be killed; it stays that way (a
  second permanently immune solo killer would be too hard to beat).
- From Night 2: picks a dead, unconcealed body and a target, then uses that body's night ability.
  Results come to the Necromancer.
- Same body: never two nights in a row. Otherwise no use limits.
- Wolf bodies: a dead Illusionist gives an attack. A dead Chanteuse gives a block, under the block
  rules above (so it can block a living wolf).
- Town bodies: a dead Vigilante gives a shot with no misfire penalty. Info roles give private
  results. A dead Healer gives a protect. A dead Sigilist gives a sigil.
- Stealth: the borrowed body shows as the visitor, and the Sigilist cannot punish it.
- Trace: reads suspicious to the Investigator on nights it attacks.

## Neutral

One seat. Both options win on their own terms, alongside whoever else wins. Both read "Not
suspicious" and never count toward any faction's numbers, but both are living voters (see Win
logic).

| Role | Status | Acts | What it does | How it wins |
|---|---|---|---|---|
| Speculator | New, level 1 | A night action, on any night, made once | Privately picks the side it predicts will win: Town, the Wolves, the lone killer, or itself. The next morning report announces the pick, but not who the Speculator is. | Its side wins, alive or dead. A self-pick wins only as the last one standing. Dying unpicked is a loss. |
| Fortune Teller | New, level 2 | Every night | Bets on who dies tonight, by any cause: 1 point for the victim, 2 for victim and role. Or bets on itself to survive an attack, scoring nothing. | Reaches 2 points; points are kept if it dies |

- Speculator with no pick: there is no deadline and no "made no choice" announcement; a Speculator
  that dies before picking has lost. The trade-off is the role: an early pick gives it a side for
  more of the game, a late pick more to go on at the risk of dying unpicked (owner, 2026-10-09).
- Speculator cover: any player can claim to be the Speculator, so a wolf may borrow the announced
  pick's trust.
- The pick names a side, not a player, so it is not a visit.
- Fortune Teller: the bet is placed at the start of every night and settled at the very end of the
  night's resolution, when she learns whether it was right. Lynches never score. 2 self-bets per
  game; the self-bet helps her survive that night, exact rule decided later. Bets are not visits.

## Win logic

The neutrals are never members of a faction, but they vote, so they count in the numbers that
decide whether a faction can still be out-voted. A faction wins only with a member alive.

- **Town** wins when no wolf and no lone killer remain, and at least one town player is alive.
- **Wolves** win when the lone killer is gone and the wolves equal or outnumber town plus the
  living neutrals. Two wolves against one town player and the Speculator cannot be out-voted, so
  that is a win; two against two plus the Speculator plays on.
- **Lone killer** wins when at most one other living player remains, neutrals included. The Serial
  Killer, the Speculator and one town player play on, and that day's two-against-one vote can end
  it.
- **Speculator:** wins when the side it picked wins, alive or dead (ruling 2026-10-09; the alive
  requirement is dropped). The pick gets a fourth option, **itself**, which wins only as the last
  one standing. A board with no faction alive (the last wolf and the last town player killing
  each other, by a shot or a sigil; the Serial Killer cannot die at night) is a draw, and only a
  self-pick wins it. Dying before picking is a loss.
- **Fortune Teller:** the same place in the counts; her win is a running score recorded beside
  whichever faction wins; the game does not end on it.
- Endings walked, no deadlock found: lone killer vs. one wolf (killer wins); killer vs. the
  Speculator (killer wins); killer vs. two wolves (plays on: the killer takes a wolf each night, the
  wolves can vote the killer out).

## What players see: the exact strings

The spec for what a player sees. Public strings go in the morning report; private strings go in
the actor's own night record. Built in `Agents/rules/night_record.py` and the night resolution
node.

**Public**

| Event | String |
|---|---|
| Pack kill | `X was killed by the wolves last night. They were a {role}.` |
| Serial Killer kill | `X was stabbed by the serial killer last night. They were a {role}.` |
| Vigilante kill | `X was shot by the vigilante last night. They were a {role}.` |
| Sigil retaliation | `X was struck down by a sigil last night. They were a {role}.` |
| Two attackers | `X was attacked by the wolves and the serial killer last night. They were a {role}.` |
| Save | `X was attacked by {attackers} but was saved by the healer!` |
| Attack on an immune player | nothing |
| Concealed body | `X was killed by the wolves last night. Their role is hidden by an illusionist.` |
| The will | `The record of X, the {role}: night 1, protected Y; no attack on them was announced; night 2, checked Z: they were a villager.` (one clause per earlier night) |
| No deaths | `No one died last night.` |

**Private**

| Action | String |
|---|---|
| Protect, a save | `Y was attacked by {attackers}, and your protection saved them.` |
| Protect, nothing | `No attack on Y was announced.` |
| Kill or shoot, landed | `Y died. They were a {role}.` (concealed: `Y died. Their role was concealed.`) |
| Kill or shoot, saved | `Y survived: the healer saved them.` |
| Kill or shoot, immune | `Y was unharmed: immune to night kills tonight. The public was told nothing about this attack.` (which roles can be immune on which nights is in the rules; the string names none, since the Necromancer on night 1 and a self-betting Fortune Teller are immune too) |
| Hold fire | `You held your fire.` |
| Watch | `Tonight Y was visited by A and B.` / `No one visited Y tonight.` |
| Follow | `Tonight Y visited Z.` / `Y visited no one tonight.` |
| Sigil, hit | `Y attacked someone tonight, and your sigil struck them down.` |
| Sigil, immune | `Y attacked someone tonight, but your sigil could not kill them: they are immune to night kills.` |
| Sigil, saved | `Y attacked someone tonight, but the healer's protection saved them from your sigil.` |
| Sigil, miss | `Your target did not attack tonight.` |
| Block, took | `Y was roleblocked tonight.` |
| Block, no effect | `Your block did not affect Y.` |
| Conceal, a body | `You concealed Y's body. They were a {role}.` |
| Conceal, no body | `The pack's victim did not die, so no body was concealed.` |
| Any action a block cancelled | `You were roleblocked: your action was not carried out and you learned nothing tonight.` |
| Investigate | `Y reads Suspicious.` / `Y reads Not suspicious.` (in the night record like every other result; the investigator's day and night prompts read its record) |
| Pick | `You picked town. The morning will announce the pick, not you.` (the morning: `The Speculator has picked Town.`) |
| Bet, scored | `Y died and was a healer: two points.` / `Y died: one point. They were not a healer.` |
| Bet, missed | `Y did not die tonight: no points.` |
| Self-bet | `You bet on yourself: an attack on you tonight fails, and nothing is scored.` |
| Borrowed action | the body's own string, prefixed `Through Y's body: ` (the body is the first name in `seen`) |
| Declined action (keep_sigil, no_conceal, stay_put, not_yet) | no record (the vigilante's hold_fire keeps its line) |

## Frontend notes (for the integration pass)

- The will is shown in the side-wing photo-frame notes card after a player dies. How to display
  it cleanly and thematically is for the frontend pass.
- A concealed role shows nothing or "record cleaned"; X-ray on reveals it. The hidden card's look
  (a blank card, or a question mark) is undecided.
- The 14 sigils, the faction marks and the role figures already exist on the stage.
- Wolves' reads at night (2026-10-09): every wolf night turn now gives reads, so a wolf can emit
  up to five `player_reads` in one night: each chat round, the carrier's turn, and its skill turn.
  The translator sends one per player, day, round and phase, so each of a wolf's night turns
  carries its own round number: the chat rounds 1 to 3, the carrier's kill round 4, a skill turn
  round 5 (`SKILL_ROUND`; the first wiring stamped the skill with the kill's round and the
  carrier's skill reads were dropped as repeats, review 2026-10-09).
- The stage already files a wolf's reads under the pack's branch of the night, and the case
  file's Reads tab shows a seat's latest reads, so the wolves' reads need no new UI. Check in the
  workbench that a wolf with several reads in one night shows the last, and that the fresh-read
  flash compares against its previous turn.
- The pack vote is gone: no `wolf_vote` event; the carrier's choice is the kill
  (`wolf_kill_decided`). The night beat builder's `wolf_vote` case and anything that shows a vote
  in the pack's night change with it. A wolf may now pass a chat round; whether a pass shows on
  the pack's branch is a frontend choice (the day's round passes are shown as no speech).

## Deferred

Considered and kept for later. Full designs are in this doc's version history. These keep their
working names; rename any that get promoted.

| Role or mechanic | Side | One-line mechanic | Why deferred |
|---|---|---|---|
| Seer | Town info | Learns whether two players are on the same side | Two targets; test later |
| List Investigator | Town info | Learns 2–3 possible roles for a player | Replaced by the suspicious / not version |
| Spy | Town info | Sees every player the wolves visited | Too strong |
| Jailor | Town kill | Jails, interrogates privately, may execute | Needs a new sub-loop |
| Inquisitor | Town kill | Names a player's role; kills if right | Not chosen |
| Truthseeker | Town support | Publicly checks if a formal claim is true | Not chosen |
| Escort | Town support | Town roleblocker | Not chosen |
| Mayor | Town support | Reveals for double votes | Needs a day action |
| Medium | Town support | Publishes a dead player's night results | Only needed if wills are off |
| Guardian Angel | Neutral | Protects an assigned player | Not chosen |
| Werewolf | Lone killer | Even nights: kills a house's owner and its visitors | Name clashes with the wolf team |
| Consigliere | Wolf skill | Learns a player's exact role | Not chosen |
| Potion Master | Wolf skill | One heal and one poison | Two choices per night |
| Blackmailer | Wolf skill | Silences a player for a day | Needs new day mechanics |
| Ninja | Wolf skill | Hides a player's night traces | Not chosen |
| Framer | Wolf skill | Makes a player read suspicious | Not chosen |
| Blood Moon | Wolf mechanic | Once per game, a double-kill night | Not chosen |

## Balance dials

The balance run (about 20 agent-only games) comes after level 2 is built. Change one dial at a
time:

- Town too strong: the Sentinel reports factions instead of names; the Sigilist is capped at 1 kill.
- Wolves too strong: the Chanteuse cannot block the same player two nights in a row; the
  Illusionist drops to 1 conceal; evil's records are read out at death.
- Serial Killer too strong: it reads suspicious on nights it attacks.
- Necromancer too strong: each body can be used only once.
- Neutral rarely wins: the Fortune Teller gets a third self-bet.

Track each faction's win rate, the day games end, how many nights the Investigator gets results,
and how often the Illusionist conceals an info role.

## Change log

- **2026-10-07 (role cards review):** the side is "Town" in the UI; Fortune Teller timing and
  self-bet; a block on a non-town pick tells the Chanteuse; the Fortune Teller's bonus on a
  concealed victim; the Speculator picks at night; the borrowed-body note for the rules prompt.
  Also, from the build order (§8.1 of `discussion_evidence.md`): no wills, the engine discloses a
  dead town role's record instead; the Vigilante stays as built; the balance run waits for level 2.
- **2026-10-08 (the shared night layer, before the code review):** the sheet was checked
  against the game as it runs. Changed against the 6 October draft: the save line stays named (the
  draft said "someone was attacked but survived"); a block takes on wolves too, and never on the
  lone killer or the neutral (the draft said town only); the will reads earlier nights only, town
  only, evil as a dial; the pack vote is removed in favour of the carrier; the conceal is spent
  only on a body; a sigil counts any attack and is stopped by the healer; the win logic counts the
  neutrals as voters and requires a living member, and the Speculator may pick itself; formal
  claims become a `claim` field; the "What players see" columns are replaced by the exact strings;
  the Necromancer stays killable from Night 2. The sheet's open decisions (wills, Vigilante values)
  are closed by the above.
- **2026-10-08 (later):** which roles may take a night off (the "A night off" rule under Shared
  rules); the Necromancer's "Stay put tonight".
- **2026-10-08 (later):** the wolf chat gets a pass and a hard cap of three rounds, ending on a double pass, carrier first.
- **2026-10-09:** the Speculator need not be alive to win; it picks on any night, once, with no deadline, and loses if it dies unpicked.
- **2026-10-09 (wiring):** the wiring landed (evidence/game_play_enhancement/phase3_wiring_census.md): the investigator's result is a night record like every other; the immune string names no role; a borrowed kill is announced as the body's would be (an Illusionist's body reads as the wolves', a Vigilante's as the vigilante's); the carrier is the rotation only (a chat override is not built); a declined action leaves no record; the neutral's result rides beside the winner (`neutral_result`), and a self-picked Speculator wins a drawn board.
- **2026-10-09 (later):** levels are build order only. A game seats 10 from a pool of 12: the
  lone killer's seat (Serial Killer or Necromancer) and the neutral seat (Speculator or Fortune
  Teller) are each drawn at random per game unless the user chose one (owner).
- **2026-10-09 (review):** an external review of the wiring found six gaps the suite missed, all fixed: the Fortune Teller's self-bets are now its limited ability (2 uses in the registry, spent on a self-bet only, not offered once spent; the ordinary bet goes on every night); carrying the pack's kill spends no conceal (a use is charged only by the role's own action); the conceal is a visit to the pack's victim whenever the conceal went ahead on a named target, dead or saved (the Sentinel at that door sees the carrier and the Illusionist, as the pack rules say; a blocked Illusionist goes nowhere); a wolf's skill turn is stamped with its own round so its reads reach the wire; a human Necromancer's announced turn carries its bodies (`input_request.bodies`); and the formal-claims ruling is built: the speaker's `claim` rides the spoken line (`DayChannel.claim`, `speech.claim` on the wire) and makes the ledger's role lines, the summariser's transcription of the role is taken only for a player who set no claim that day (a human's line) and dropped where it disagrees, its night actions, retractions and plans stand. The pack rules now say the rotation only (the chat override was never built).
