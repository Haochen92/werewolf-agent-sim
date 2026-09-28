# Beat sheet — the source of truth, beat by beat

Every scene of the live game and the replay, one row per beat. This table is mirrored by
`src/stage/beats/beatsFor(events, { xray })` and checked by goldens on the fixture game
(9369a5c1, memory on; seq numbers below are that game's). Change the table, change the code,
regenerate the golden, in that order. The narrative behind each row is the handoff
([design_2026-09-25/HANDOFF.md](design_2026-09-25/HANDOFF.md) §4, cited as H§n); the code shape is
[stage_architecture.md](stage_architecture.md).

## 0. Conventions

**Columns.** *Anchor*: the wire event (or client condition) the beat is keyed on; a replay
beat exists iff its anchor is in the log. *Sees*: who has the beat — **P** everyone (public),
**S** the seated human it concerns, **F** the wolf pack, **X** X-ray on (observer tier; in live,
everyone after `game_over`). A beat marked S or F is also in the X-ray replay, shown in aqua as
"Only seat n". *Stage*: what changes on the stage. *Slot*: what the drawer (D) or film (F) does;
"—" = nothing new. *Hold*: the replay's wait at normal speed. *Bench*: the revision that drew it.

**Holds** (H§5): shutter 3.0 s · a chip 2.0 s · a card read 2.6 s · the verdict 3.2 s · the vote's
opening move 2.8 s · a plain held beat 2.0 s · **speech** = words ÷ 4 per second, floor 4 s, cap
15 s, held while the pointer or a touch is on the speech; wolf messages the same. Live has no
holds: beats animate as events arrive (§12).

**Live vs replay.** Live plays every beat its tier receives, in arrival order, with the queue
rule of §12. The replay plays the P beats with X-ray off and P+X (plus every S and F beat, in
aqua) with X-ray on; toggling X-ray re-cuts the beat list, so the seek bar re-marks.

**The right slot** holds one thing at a time, the drawer or the film; the two buttons switch;
the X-ray state stays either way. Turning X-ray on resets the drawer's Show › X-ray filter to on.

**Seats** are `player_1..player_9`, shown as the numeral 1–9. The cast (character per seat) is
`castForGame(gameId)`.

## 1. The deal — H§4.0 · bench 75

The first scene of a match. Nothing on the wire narrates it; every line is the client's.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `deal.table-seated` | `game_started` (seq 1) | P | dining car at dawn, shutter up, room empty; nine chips come down from the flies in seat order as the seated table | D: nothing (no wire line) | 3.0 |
| 2 | `deal.cards-dealt` | `game_started.cast_role_counts` | P | nine face-down cards come down on the same strings, one under each chip; the plate reads the cast counts | — | 3.0 |
| 3 | `deal.your-card` | my `role_assigned` (seq 2–10) | S | my card comes down large, centred, on its own string, and turns face up; the box: who I am, my night action; the vigilante counts two caps; the card button appears | D: dashed "Only you" line | 2.6 |
| 4 | `deal.your-pack` | my `role_assigned.pack` | F | the packmate's chip takes the red edge, its small card turns to the wolf; the pack chat opens with the client's game-master line and stays open for the night | D: the pack chat's opening line | 2.6 |
| 5 | `deal.face-up` | `roles_assigned` (seq 11) | X | all nine small cards turn at once; the wing takes its strips and badges | F: the deal listed | 2.6 |
| 6 | `deal.day-begins` | `phase_change: day` (seq 12) | P | cards and chips go up, the paint goes to day, the stand returns with the first speaker. **Chapter mark: Day 1** | — | 3.0 |

Without X-ray the replay sees the backs. The boarding variant (the train at a station) is not a
deal beat; it is the waiting room before it, §1a.

As built 2026-09-25 (no bench gives them; change here first): top strip "Before day 1 · The deal
· <label>"; "Nine at the table"; chips lower 0.1 s + 0.07 s each, cards 0.2 s + 0.08 s each; your
card lowers over 1.2 s and turns at 1.9 s; the stand fades in at 2.6 s of "the day begins". The
stand is empty at `deal.day-begins` because the view holds no turn yet (the first speaker is used
if it ever does). The packmate's hung chip takes the red edge, as its wing tile (the bench drew
amber; the handoff's red won, 2026-09-25). Beside an open side slot the chip row and the cards
under it keep inside the room, 32 units in from the wing and from the room's right edge (the
X-ray night's spokes hang the same row, so they narrow too).

## 1a. The platform — the waiting room · review 2026-09-26 §A5, F1 · live only

A room before its game: `/games/[id]` while the status says `waiting`, on the same stage the game
plays on (landscape, under the orientation guard), so Depart hands straight to §1 row 1. A room has
no event log: every beat is keyed on the status poll (3 s while waiting) or on this device (the
host key, the seat token). Nobody has a seat yet: the i-th person to board stands at the i-th
place and wears `castForGame(gameId)[i]`, with no numeral; seats are dealt at the start and the
empty places go to agents. Never in the replay or the workbench fixture (the workbench draws it from
synthetic rooms, `SYNTHETIC.station`).

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `station.waiting` | status `waiting`, not `locked` | P | the platform at night: the train at the platform with the dining car's window over the nine places; each person aboard on the platform under their place (their name on a paper tag at their feet and on a brass plate under the window; "you", "host" on the tag); open places a dashed amber mark and an "open" plate; their chips on the wing; the station sign with the room's name and "hosted by …"; the Invite and Ticket tags hung from the canopy; the ledge: "3 of 9 aboard · waiting for the host" (the host: "· ready when you are", with the Lock and Depart plates) | — (no drawer, no film) | until the room changes |
| 2 | `station.locked` | status `waiting`, `locked` | P | as 1, with the brass "Locked" plate under the sign; the ledge's line leads "Locked: nobody new can board."; the host's plate reads Unlock | — | until the room changes |
| 3 | `station.departing` | the host's Depart went through (`POST /start`), or the status left `waiting` | P | the ledge reads "All aboard"; the people step off the platform into their places in the window; the blinds unroll on the agents' places with their shadows on them, the plates turn to "agent"; the tags draw up into the canopy; the ledge sinks; the train pulls out to the right; then a curtain falls on the empty platform ("The deal begins in the dining car") and lifts on §1 row 1 | — | 7.0 s, then the curtain 1.2 s down and 1.0 s up |

As built 2026-09-26 (the mockup `claude_artifacts/design/pages/waiting-room.html` gives the
picture and the departure's order; the timings are the build's, change here first). A person who
joins while the page watches rises onto the platform (the puppet's rise, 0.8 s) and their tag fades
in after 0.6 s; what was there when the page opened is simply there. The departure: the people sink
off the platform in 0.45 s and appear in the window (fade and rise, 0.8 s after 0.3 s); the agents'
blinds unroll 0.9 s each from 0.5 s, 0.16 s apart, their shadows 0.6 s from 1.2 s; the tags draw up
0.9 s; the ledge sinks 1.0 s and the train pulls out 4.6 s, both from 2.4 s (the train on the
mockup's ease-in, clipped at the world's edges). A viewer who asked for reduced motion gets a
0.6 s departure. The hand-off (`LiveTheatre`): the game's events are held back from the stage until
the curtain is down, then the deal plays from its first beat at normal speed whether it arrived as
history or as news (`live-state.ts`, `dealEnd`), and the curtain lifts off it; one `<Stage>`
throughout. The snow falls for as long as the room waits (still at `skip` and for reduced motion).
Depart needs one person aboard ("Nobody is aboard yet: Depart needs one person on the platform.");
the server sets no minimum, this is the client's rule from the old lobby card. A newcomer to an open
room with a place left gets the boarding pass first (a page, upright allowed: name, "Step onto the
platform", "Just watch"); a full or locked room, or a device holding a seat, goes straight to the
platform. Not built (no wire for it): the room's code, puppet choice and "Change puppet", Leave,
removing a passenger, the Ticket's model, memory and "who pays" lines, "Change the terms".

## 2. Day discussion — H§4.1 · benches 62, 72

Turns run in the log's order. The film for a turn is *this beat, inside*: the speaker's note
(`strategy_update`, written after the turn), the lessons it weighed (`memory_consulted`, before it;
memory-on games from day 2). Reads (`player_reads`, before the decision) are not in the film: they
are a blue edge on every seat the speaker has a read on, brighter for a sure read; a tap opens the
read card (guess, how sure, why, the truth with ● ◐ ○).

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `day.turn-thinking` | `turn_started` (first: 13) | P | the seat's puppet takes the stand in the thinking state, no clock; the speech box shows a "…" so the state reads as thinking, not idle (ruled 2026-09-25) | D: nothing yet | live: until the turn resolves · replay: folded into the resolving beat: the puppet rises thinking, holds **0.6 s**, then plays it (accepted 2026-09-25) |
| 2 | `day.speech` | `speech` | P | talking state, the line in the speech box; X: the box carries the aqua tags (who it answers, stance) and the plaque tags the role; the wing's blue edges from the turn's `player_reads` | D: the line, lit and scrolled to · F(X): note + lessons weighed | speech |
| 3 | `day.pass` | public: a `turn_started` resolved by no speech (the next `turn_started` or the phase change), live and replay alike, since `turn_started` is public · X-ray: `pass_marker` instead (12 in the fixture), which carries the reason and the draft (ruled 2026-09-25: day 1 of the public replay is three passes, not an empty stand) | P · X | idle state, the box says "passes"; X adds the reason and the held-back draft. Reason wording (accepted 2026-09-25): `voluntary` "chose to pass" · `novelty_gated` "held back: nothing new to say" · `generation_failed` "no line came" | D(X): the pass with its reason and draft | 4.0 |
| 4 | `day.your-turn` | `input_request` `discuss` for me | S | my puppet at the stand, thinking; the wall clock carries the two minutes (`deadline`; null = no ring); the box is a textarea with **Say it**, **Pass**, **Draft from notes** (three per turn, the returned `deadline` is the new countdown); the drawer stops at the rail so the prompt keeps the full width | D: stops at the rail | until answered / deadline |
| 5 | `day.your-line` | my `speech` after 4 | S (P sees a normal turn) | the puppet talks my line as any turn plays; a pass leaves it idle | D: my line | speech |
| 6 | `day.agent-spoke-for-you` | my `speech` arriving with my request unanswered at its deadline (client-known) | S only | the puppet talks the agent's line; the plaque's tag and the box say "your seat's agent spoke for you" | D: the line with the tag | speech |
| — | `day.summary` | `day_summary` (28, 79, 218, 360) | — | **no beat here.** Public on the wire but the live stage has no beat for it; the replay plays it in the Morning of the same day number (§8 row 8) | — | — |

**The one timeout rule** (every human turn: speak, vote, night act, wolf chat): the countdown runs
on `input_request.deadline`; on expiry the seat's agent acts and only the seat is told. A human
who leaves is the same rule made permanent: the table sees nothing; if they come back they arrive
still, at their seat, with the plaque's tag on their own screen ("your seat's agent played 3 turns
for you", counted client-side from unanswered requests). Agents have no client-side timer.

As built 2026-09-25 (no bench gives them; change here first): the public pass has no reason line
(the box reads "passes." under the seat's chip). Live, a line or a pass that follows its own
seat's thinking beat does not rise again: the puppet already at the stand goes on talking (or to
idle). On my turn beside the drawer (which stops at the rail) the side room's paint has no wall
for its clock, so the WallClock instrument, ring and all, hangs in the gap between the wing and
the puppet (centred there, 0.3 of the height down, radius 0.4 of the gap, at most the paint's).
## 3. The vote — H§4.3 · bench 64

`vote_cast` is a batch released at the tally, so the vote is blind and parallel and the replay
must never look like players voting one after another. `phase_progress` (stage `day_vote`) is
ephemeral: it paces the live drop and is not in the log.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `vote.opens` | `phase_change: voting` (81, 220, 362). **Chapter mark: Vote N** | P | the puppet drops behind the stand, the stand goes; dusk; the shutter drops; the trap's leaves open and stand; the table rises on its lift with the jar; the lid's string comes down and the lid lifts. One move | D: the GM's line if any | 2.8 |
| 2 | `vote.ballot-drops` | live only: each `phase_progress` increment | P | one anonymous chip from the flies into the jar; the pill "Ballots in, n of N" | — | real time |
| 3 | `vote.your-ballot` | `input_request` `vote` for me | S | the prompt: a row of the candidates' chips, the empty plate = abstain; tap, confirm on the plate; my chip drops in face up on my screen only; after that I have the spectator's jar | — | until answered / deadline |
| 4 | `vote.ballots-drop` | replay only: the `vote_cast` batch (first: 109, 242, 378) | P | all the chips cascade together into the jar | — | 2.0 |
| 5 | `vote.closes` | live: the pill full · replay: same beat as 4 | P | the lid comes down | — | 1.5 |
| 6 | `vote.count-begins` | the `vote_cast` batch | P | the lid flies out; the shot pushes in; the jar tips to the back rail; plates along the front edge, one per seat with votes, abstain as an upturned saucer at the right; place cards with head, seat, running number | F(X): the voters' consults and reads | 2.0 |
| 7 | `vote.chip-counted` | each `vote_cast` | P (X: the ballot named at the drop) | one chip rolls from the jar's mouth, flips face up, lands on its plate; the card's number ticks; towers cap at four; the chip that settles the winner lands last | D: (the votes are one drawer line per day at the count, pairs as chips, abstain as the empty ring) | 2.0 each |
| 8 | `vote.result` | `lynch_result` (119, 250, 384) | P | the winner's plate and card lit; "Voted out, 3 to 2" · `abstain`: "The table abstains" · `tie`: the tied plates lit equally, the GM's line, one held beat, then the abstain ending | D: the GM line with the lynch sigil lent to it | 3.2 |
| 9 | `vote.table-down` | `lynch_result` | P | the lift lowers the table with the count on it. `lynched`: the leaves stay open → §4. `abstain`/`tie`: the leaves fold, the shot pulls back, the shutter gathers up on the night window → §5 | — | 3.0 |
| — | `vote.skipped` | `lynch_result: no_vote` (31, day 1) | — | **no vote scene**: the day goes straight to night falls (§5 row 1 takes the shutter move) | D: the GM line | — |

As built 2026-09-25 (bench 64's timings; the rest no bench gives, change here first): top strip
"Day N · The vote · <label>" ("Night falls · …" on the abstain ending). The opening: the puppet
drops 0.45 s, the stand fades 0.3 s after 0.38 s, day → dusk 1.2 s after 0.15 s, the shutter 1.1 s
after 0.35 s, the flat leaves fold 0.5 s after 0.3 s and stand 0.45 s after 0.7 s, the lift 1.4 s
after 0.55 s, the lid's string fades in 0.3 s after 1.9 s and the lid lifts 0.7 s after 2.1 s. The
pill: "Ballots in, 0 of N" (N = the living) at the opening, "n of n" at the drop, "All in" at the
close; the replay's chips fall 0.75 s each, 0.09 s apart. The close: the lid down 0.6 s after
0.25 s. The count: the lid out 0.7 s after 0.25 s, the push-in (×1.32) 1.1 s after 0.25 s, the jar
tips 0.8 s after 0.9 s, the plates and cards 0.55 s each from 1.5 s, 0.16 s apart. A chip: the arc
0.85 s, the card's number pops at 0.82 s, the box "Seat 7 votes Seat 2" ("Seat 5 abstains") after
0.7 s; the wing lights the voter. The result: "Seat 2 · Voted out, 3 to 2." · "The table abstains
· 9 to 0. No one is voted out." · "A tie, 3 to 3 · <the GM's last line>"; the plate's glow 0.7 s
after 0.2 s. The down: the lift 1.5 s after 0.35 s; the abstain ending: the standing leaves fold at
2.0 s, the flat ones lay at 2.4 s, the pull-back 1.2 s after 2.2 s, dusk → night after 2.4 s, the
shutter up after 2.5 s; a lynch keeps the close shot. The voted-out seat stays alive on the wing
until the lynch's card clears the rail. The table's top is the walnut tile in perspective, the
bench's cloth hanging from its front edge. The ballot: the chosen chip is lit (amber ring, glow),
the rest dim (the bench raised it); the plate reads "Choose a seat" / "Vote seat 6" / "Abstain";
"Your vote · Tap a chip, or the empty plate to abstain." with "your seat's agent votes for you in
1:14"; sent, "Your ballot is in · no one sees it until voting closes" and the wall clock's ring
goes. Not yet built: the live drop (row 2; the pill reads `turn.progress` once the container feeds
it from `phase_progress`), the count's X-ray film (row 6).

## 4. The lynch — H§4.4 · bench 65

Follows `vote.table-down` when `lynch_result.outcome = lynched` (250: seat 6 villager; 384:
seat 2 serial killer).

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `lynch.stand-returns` | `lynch_result` | P | the shot pulls back; the stand comes up from below the rail with the voted-out puppet rising into it from behind the playboard; the leaves stand either side; the light collapses to one special | — | 3.0 |
| 2 | `lynch.named` | 〃 | P | held; the plaque's tag "voted out". S (if me): the box "You are voted out" | — | 2.0 |
| 3 | `lynch.drop` | 〃 | P | straight down through the trap, no fade; the plaque stays lit over the empty box | — | 2.0 |
| 4 | `lynch.card-up` | `lynch_result.role` | P | the lift raises the role card (name, sigil, figure, front line, faction colour); the wing's tile holds the live face until the card clears the rail, then flips to the sigil | F(X): "Who had them right": each voter's `player_reads` on this seat vs the truth (● role ◐ side ○ none/wrong); the seat's last note | 2.6 |
| 5 | `lynch.truth` | 〃 | P | held. S (if me): "You were a villager" → "You stay at the table as a spectator"; the card button reads "on the wing" | — | 2.6 |
| 6 | `lynch.card-to-wing` | 〃 | P | the card flies up; the stand goes; the shutter gathers up on the night window; the leaves fold → §5. If this lynch ends the game → §10 | — | 3.0 |

As built 2026-09-25 (bench 65's timings; change here first): top strip "Day N · The lynch ·
<label>". The pull-back 1.0 s after 0.1 s; the stand fades in 0.5 s after 0.5 s and the puppet
rises (base state) at 1.05 s; the drop (the out state) 0.5 s after 0.35 s; the card rises 1.3 s
after 0.3 s and the wing's tile turns at 1.45 s; the card flies 0.8 s after 0.3 s, the stand fades
0.6 s after 1.3 s, dusk → night after 1.3 s, the shutter up after 1.4 s, the leaves at 2.0 s /
2.4 s. The box: "Seat 2 · Voted out, 3 to 2." → "Seat 2 was the serial killer · Voted out, 3 to
2." → "· Night falls." at the card to the wing; S: "You are voted out · 3 to 2. Your role is shown
to the table next." → "You were a villager · The table sees your card now." → "· You stay at the
table as a spectator." The film ("Who had them right") shows at the card and the truth: each
voter's last `player_reads` that day before the first ballot; ◐ is town against not town (bench
65: a wolf read on the killer had the side). Not yet: a lynch that ends the game still plays the
night ending in `lynch.card-to-wing` (nothing in the view at that beat says the game is over).

## 5. Night, the lobby — H§4.5 · bench 67

Everyone who is not acting is here for the whole night. The villager's night is this room. Nothing
on stage changes per act beyond the count and the clock; parallelism is stated by the hub, never
by the staging.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `night.hub` | `phase_change: night` (32, 120, 253, 387). **Chapter mark: Night N** | P | the dining car, the shutter up on the night window, the living seats hung as chips in a row (the table asleep), the pill "Acted n of N" (padded; the pack counts as one), the wall clock at midnight | D: the GM's "night falls" line | 3.0 |
| 2 | `night.act-in` | live only: each `phase_progress` (stage `night`) | P | the pill increments; the clock advances toward dawn | — | real time |
| 3 | `night.your-act-in` | my POST confirmed (my room closes) | S | back in the lobby with "Your act is in"; my own mark the only one I see | D: dashed "Only you" line naming my act | 2.0 |

X-ray on (replay): the hub also lights the wing's lamps on every seat that acts tonight (§9).

As built 2026-09-25: N in "Acted n of N" = living seats with a night role by the public census
plus one for the pack (5, 5, 4, 3 in the fixture); a vigilante out of caps is not counted. A seated
actor's box reads "Night falls" with their card's night line; a villager's "You sleep". The
previous hour's paint crossfades 1.2 s; the chips lower 0.6 s + 0.06 s each; on a no-vote day the
hub gathers the shutter up itself (0.2 s in).

## 6. Night, the acting seat — H§4.6 · bench 70

The role's own sleeping compartment (the owner's paintings, 2026-09-28): walnut and brass, the
role's props painted in (the healer's apothecary, the investigator's office, the vigilante's
hideout, the killer's trophy room), the night going by behind the window, dark but for the
candle on the fold-down table. No avatar. On the table by the candle: the framed role card (tap →
the full card centred as an overlay). Under the brass rack: a line of photographs, one per seat
the server offers. No clock: the countdown is on the plate.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `room.opens` | `input_request` for me, kind `healer_target` · `investigator_target` · `vigilante_target` · `serial_killer_target` | S | the role's compartment in the candle's light; the plate's countdown from `deadline`; photos for `candidates` only (the server's list is the only source of legal targets) | D: the drawer stops at the rail (on a phone it runs full height) | until answered / deadline |
| 2 | `room.choose` | tap a photo | S | the wall goes darker, one light finds the chosen photo and a pin goes through it; the plate names the act ("Protect seat 1", "Check seat 4", "Shoot seat 2", "Kill seat 5") with "tap another photo to change" over it; the vigilante also has **Hold fire** | — | — |
| 3 | `room.confirm` | tap the plate → POST (the commit: the server takes one answer and 409s a second) | S | the pin goes fully home; the plate seals into a label ("Seat 1 is protected tonight" · "You check seat 1 tonight" · "You shoot seat 1 tonight" · "You hold fire tonight" · "Seat 1 is marked tonight"), no countdown; a failed send reopens the plate with its words. `night.your-act-in` is not built: the sealed room holds until the next beat the seat sees | — | — |
| 4 | `room.card` | tap the framed card | S | the full role card centred over the room; tap to close | — | — |

Motion for this room, as built 2026-09-25 (no bench gives them; change here first): the light
finding the photo crossfades in 0.6 s; photos arrive 0.6 s each, 0.08 s apart; tapping the chosen
photo again un-chooses it. The plate reads "Choose a seat to protect" until one is chosen, then
"Protect seat 1" (Check · Shoot · Kill likewise).

**The painted rooms** (2026-09-28, owner-approved; they replace the shelf, the kit and the plush
dolls). The room is `SPRITES.rooms[role]` (the wolves' is the pack's, §7), laid right of the wing
and slid left with the side slot open so its window and its wall stay in view
(stage_architecture §4 "The night rooms"). Behind its cleared glass the dining car's night: the
felt country, the near row looping, the snow (still for reduced motion). **The photo line:** thin
dark twine tied to the rack's lowest rail from just over the left wall's hangings to the window's
panel and sagging 34 units, the same line in every room; each candidate's head portrait (`HEAD_FRAME`, square) printed on a cream,
slightly aged border with the seat's numeral written on its foot (vector), a wooden clothes-peg
clipping it, crooked by a fixed table per seat (±3°). Sized for the phone (readability pass,
2026-09-28: at least ~44 css px wide on an iPhone 14): up to four hang in one row, spaced wide
(3: 140 units a print, 4: 118); five or more alternate heights down the wall, the first pegged to
the line, a lower one on its own length of twine 24 units below the one above, neighbours
overlapping across the heights (5–6: 130, 7: 126, 8: 111 units, ~48 css px); a line that would
fall under 104 units hangs at three heights instead (the side slot open: 8 at 107). **The card**
stands on the table's clear spot by the candle, 200 units tall, a soft contact shadow under it.
**The caps** (vigilante) are on the card, under its night line, on the table and opened: "2 caps
left" / "your last cap" (ruled 2026-09-28; the plate's quiet line keeps only "tap another photo
to change"). **The card opened** in the room (and the pack's) drops the front line: the name,
the figure, what you do at night (ruled 2026-09-28; the deal, the lobby and the game over keep
it). **A tap on the empty room** (not a photo, the card, the plate, the drawer or the HUD), or
past the opened card, closes the card and draws the pin out of an unsent choice; once the act
is in it only closes the card (ruled 2026-09-28).

Cute voodoo, as built 2026-09-27 (owner-ruled; change here first). **No clock in the room:** the
plate carries the countdown, `m:ss` rounded up in a small dark box before the act (the day
dock's figures), and a 3.2-unit bar along the plate's top edge draining `remaining / whole`
(eased over the live clock's 250 ms tick), brass, both red (`#e3503f`) from 10 s; no deadline
(solo, the workbench's no-deadline case) shows neither; a sent act drops them. **Candle light**
(re-placed 2026-09-28 for the paintings, which are lit already): warm black at 0.5 over the room,
the key light off; the painted candle's pool falls on the photo line, leaning 18% towards the
candle; the card keeps a soft light (0.85) and the candle its own glow (a halo, 0.22). The light's
colour is the candle's: warm amber, the killer's violet, the wolves' red. Still gradients, no
filter, no blend mode. **Chosen:** over the wall a further 0.62 of dark with a wide hole round
the chosen photo (warmth 0.18 in it), fading out just before the card so the table, its candle
and the card stay as they were, crossfading 0.6 s; the others' prints darken (0.62) where they
hang; the chosen print catches the candle (a warm light over it and a soft glow round it) and
comes forward a touch, scale 1.08 from its peg (0.4 s), over its neighbours: the one place the
room moves to say chosen, and only by a transform. Sealed keeps it so. The chosen photo wears a **pin**: a steel shaft 0.49 of the photo's width, 52° up to the
right from its picture (62% across, 40% down), a round head in the card's colour (town amber,
wolf red, killer violet) with a glint, and a small dent where it enters; tapped, it pushes in
along its line (0.32 s after 0.1 s), un-chosen it draws back out (0.25 s); a seeded choice is at
rest. It replaces the act's `ActMark` (the plate names the act). **The plate** centres in the room
right of the wing (left of an open side slot), so on a phone the drawer runs full height here
(`railHolds` is the pack's only). **The commit** (2026-09-28): the plate is the commit, because
the server takes one answer per seat. Chosen and not sent: the gold button, and a quiet line over
it, "tap another photo to change" (`--meta` × 1.1). Sent: the pin's last push (0.08 of its size
along its line, 0.2 s; still on arrive and seek), the chosen photo stays lit, and the plate becomes a sealed label,
not a button: a dark plate with a brass edge, a wax dot in the side's colour and the act in one
line (`ACT_SEALED` beside `ACT_VERB`); the countdown goes. The container's send state reaches the
scene as `turn.sent` / `turn.sendError` (`actSent`): sealed while sending and once in; a 422 or a
dropped connection ("Could not reach the table. Try again.") reopens the plate with the words over
it; a 409 or the agent's answer seals it as "Your seat's agent acted for you". **The count once sealed**
(2026-09-28): with the plate sealed (and in the pack once my vote is in, or the kill is decided)
the room shows the night lobby's pill, "Acted n of N" at the top centre (`CountPill`, `side` as
the lobby's), from the same census (`nightUnits`) and the same live `phase_progress` count, ticking
up as the others act until the morning; hidden before, when the plate's countdown is the focus.

## 7. Night, the pack — H§4.7 · bench 71

The same room, painted as the wolves' red-lit compartment ("Grandma's things"); the packmate is in
the chat, not on the line. Seats the pack can choose exclude wolves (`candidates`). The wing marks
pack seats with a red edge.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `pack.wakes` | `phase_change: night` while I am a wolf | F | the wolves' compartment; the chat empty or holding the deal's line | D: the pack chat (red edge) | — |
| 2 | `pack.your-line` | `input_request` `wolf_discuss` for me | F | round 1 or 2 is mine: a line and **Say it** (Draft from notes applies here too); the time left under it ("1:14 to say it") | D: stops at the rail | until answered / deadline |
| 3 | `pack.line` | `wolf_message` (first: 33, 122, 271) | F (X in the replay) | the chat keeps the order, the packmate's chip on their lines | D: the line in the pack chat | speech |
| 4 | `pack.vote` | `input_request` `wolf_vote` for me | F | the plate is live at once; the packmate's tooth lands on their photo when their `wolf_vote` arrives (faction tier, live); mine on confirm | — | until answered / deadline |
| 5 | `pack.decided` | `wolf_kill_decided` (56, 154, 264, 395) | F | the kill decided when the second tooth lands | D: "the kill decided" line in the chat | 2.0 |
| 6 | `pack.lone-wolf` | night with a pack of one (night 3+ in the fixture) | F | no talk, one tooth; the SK-whiff note arrives in the chat at morning as a GM line inside the tint (`wolf_message` from `game_master`) | D: the GM line in the chat | — |

Replay: both teeth land together (the translator already buffers `wolf_vote` and flushes it with
`wolf_kill_decided`; the log has no order between the ballots).

As built 2026-09-25 (no bench gives them; change here first): the plate says "Vote seat N" for
a pack of two and "Kill seat N" for the lone wolf; the empty chat reads "Two rounds of talk, then
the vote." (+ "Round 1 is yours to open." on my opening turn) and, alone, "You hunt alone now: no
talk tonight, and the vote is yours."; my own lines say "You"; "You vote … seat N" on confirm;
the decided line "The pack chooses seat N · both teeth"; the lone wolf's header "You are the pack
now". Timings: a tooth drops in 0.45 s after 0.3 s; a chat line fades in 0.5 s. The chat keeps a
sticky header and scrolls to its newest entry. The wing's red edge marks the packmate (not my
own tile, which has the "you" rim), in both night rooms. Not yet built: "Draft from notes" in the
pack's input. As built 2026-09-27, the room re-painted 2026-09-28: §6's candle-lit room, the
wolves' own painting, its red lamp the candle and its light red, a red tint (0.28) on the night
through its glass; the chat keeps the painting's plain bottom-right quarter, the vote's plate the
left. The teeth sit on the photo's picture, half as large again as on the dolls (packmate's left,
mine right); the lit photo (my choice, then the kill decided) wears the pin in the pack's red
beside them; the vote's plate carries the countdown.
The vote's plate commits as the room's does (a `wolf_vote` is one answer too; the server takes
no revision): "tap another photo to change" until pressed, then sealed "You vote seat 4 tonight"
(the lone wolf: "Seat 4 is your kill tonight") with my tooth down and the pin home.

## 8. The morning — H§4.8 · bench 67

Told one chip at a time in an empty room, in the log's order. `gm_message` and `night_result`
arrive together; private results follow them (59, 271→272, 402), never precede.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `morning.shutter-down` | `night_result` (58, 156, 270, 401). **Chapter mark: Morning N** (not a phase change: 156 comes before `phase_change: day` at 159) | P | the shutter comes down; the chips go up; the report plays in the night's paint | D: the GM's dawn line, with the night atoms' sigils lent to it | 3.0 |
| 2 | `morning.chip-attacked` | each entry of `deaths` and `save`, in order | P | the chip comes down alone, at the centre, large: "Seat 3 was attacked in the night" | — | 2.0 |
| 3 | `morning.chip-fell` | a `deaths` entry | P | the act mark appears beneath it (bite · knife · bullet, from `attacker_types`); the string gives way; the chip drops | — | 2.0 |
| 4 | `morning.card-down` | 〃 (`role`) | P | once the chip has fully dropped, the role card comes down large and centred; the wing's tile flips; the card is drawn up out of frame as the next beat begins | — | 2.6 |
| 5 | `morning.chip-saved` | the `save` entry (58: seat 1, wolves + serial killer) | P | the wounds small and the plaster large beneath it, the ribbon on the string; the chip goes back up whole | — | 2.6 |
| 6 | `morning.quiet` | `night_result` with no deaths and no save | P | the line alone | — | 3.0 |
| 7 | `morning.only-you` | `investigation_result` (59) · `vigilante_confirmation` · the pack's failed kill: `wolf_message` from `game_master` (271, arrives after `night_result`) | S · F | one beat after the report, on my screen only. Investigator: the target's chip comes down and turns to its sigil, the lens beneath (the one private result that names a role). Wolf: the target's chip down whole, "Your kill on seat 2 failed. Seat 2 survived", no sigil (the GM's verbatim note names the role; that wording is X-ray's). Vigilante: the same shape, "You shot seat 2. Seat 2 survived", no sigil; the caps count (`bullets_remaining`, 402, is a view update, not a beat). The healer has nothing private. A kill the healer stopped is public (the save names its attackers) and has no private beat | D: dashed "Only you" line · X: in aqua, "Only seat n" / "Only the pack" | 2.6 |
| 8 | `morning.carried-summary` | `day_summary_structured` of day N (the summary of the day just ended) | X | none on stage | F: the typed brief: accusations as rows (accuser → accused, evidence type, defence), then claims, blocs, mood. The summary of a day on which the game ended at the lynch is dropped (never consumed) | reading time |
| 9 | `morning.day-begins` | `phase_change: day` (60, 159, 274). **Chapter mark: Day N+1** | P | the shutter rises on the day's paint; the stand returns with the first speaker. If this morning ends the game → §10 instead | — | 3.0 |

As built 2026-09-25: top strip "Morning N · The report · <label>"; the attacked chip is 1.9× the
lobby's; "Seat 3 was stabbed by the serial killer" / "was bitten by the wolves" / "was shot by
the vigilante", two attackers "was attacked by X and Y, and fell"; the marks pop in and the string
gives way at 1.3 s; the card lowers over 1.2 s after 0.2 s; each box fades in after 0.7 s; the
investigator's target turns at 1.4 s. X-ray wording for only-you: "What only they learn", "Seat
4's reading: …", "The pack's kill on seat 2 failed. Seat 2 survived." The wing tile flips at
`card-down` (bench 67 flipped it at the drop; the sheet wins). Whatever hangs at the centre goes
back up as the next beat starts. The carried summary's panel: "What day N taught" / "No
accusations that day" (a stand-in for the film).

## 9. The replay's night — H§4.9 · benches 67, 73 · replay only

A linear sequence, not a picker. The transport steps through it as beats; the Night N chapter mark
lands on the hub.

**X-ray off:** `night.hub` → §8. Nothing on stage says who was awake.

**X-ray on:**

| # | Beat | Anchor | Stage | Slot | Hold |
|---|---|---|---|---|---|
| 1 | `rnight.hub` | `phase_change: night` | the hub with the wing's lamps lit on every seat that acts tonight | D: the night's lines | 3.0 |
| 2 | `rnight.spoke` (one per actor's branch, branches ordered by their **last** event; a step per pack line and one for the mark. The pack closes nights 1–2 of the fixture; on nights 3–4 the lone wolf votes before the killer and the vigilante act, so the rule is the order, not the pack) | the branch's events: `memory_consulted` · `player_reads` · `night_action`, or for the pack `wolf_message`… `wolf_vote` · `wolf_kill_decided` | a third-person view in the dining car: the actor's figure at the stand, the instrument on the rail, the mark landing on the row; the pack as two figures side by side (one for the lone wolf), its talk in the chat, both teeth landing together; the lamp goes dark as the spoke ends | F: the actor's consult and note | per event: a mark 2.0, a message speech |
| 3 | `rnight.whole` | after the last spoke | every mark on the row at once: the picture the parallel night never shows anyone live | — | 3.0 |

Then §8.

As built 2026-09-25 (bench 67 where it gives them; the rest no bench gives, change here first):
top strip "Night N · In the night · Seat 4" ("· The pack", "· Seat 8" for the lone wolf) and "Night
N · The night, whole". The film is up beside every spoke, so these beats lay the room out for the
open side slot (bench 67's `side`); the scenes before this overlay the film on the full room
instead (**to reconcile** in the container). The spokes hang the living at the window's height
(bench 67's high row), the whole across the room (the lobby's row). A mark is the act's `ActMark`
beneath the target's chip (bite · knife · bullet · plaster · lens), two to a row in spoke order;
bench 67 drew them on the chip (teeth, ribbon, hole, nick, lens). The instrument on the rail is
bench 67's `instrument()` (the vigilante's caps are the shots left, two until
`bullets_remaining`), the wolves' kit sprite for the pack, right of the figure at 0.72 of the
stand's half-width, in a patch of light. The pack stands as two at 0.78, ±0.25 of a puppet width,
the stand ×1.36 (the winners' grammar of §10; bench 67 put them ±0.46 on the plain stand), plaque
"Seats 3 and 8 · Wolves". A single actor's box: its chip, "Seat 4", the role in aqua, "checks
seat 2." (protects · checks · shoots · marks, bench 67's verbs). The pack's chat is headed "The
pack · seats 3 and 8" / "Seat 8 hunts alone"; a line step shows the lines so far, the mark step
adds the votes and "The pack chooses seat 4 · both teeth", and one bite lands. "Acted n of N"
counts the spokes whose mark has landed (N of N at the whole); the wall clock stands at 6·n/N hours
past midnight and sweeps on as a mark lands. The lamps: lit on this actor and those still to come;
this one's goes out at 1.6 s of its mark step (at rest, already out); a seat with no spoke (a
vigilante holding fire) loses its lamp after the hub. Played: a new actor rises at 0.2 s (+0.22 s
for the second wolf), its instrument fades in 0.5 s after 0.6 s, the mark pops at 0.9 s, the box
fades in after 0.7 s, the newest chat line 0.5 s. The film's stand-in: "Inside seat 4 ·
investigator", the lessons weighed as L1–L3 with "followed · overrode · not relevant" and the why,
the note as "Note: “…”" (the actor's last note that night); empty: "No lessons consulted tonight.",
"No note tonight."; the pack: "Inside the pack · the wolves' notes", "4 lines of talk, then the
vote." / "A pack of one: no talk, one tooth."; the whole: "The night, inside · what each did", "In
the order the log finished them. Live, nobody sees any of this." Not built: the vigilante holding
fire as a spoke (bench 67 had one; the cutter drops a branch with no act).

## 10. Game over and the epilogue — H§4.10 · bench 73

Follows §8 or §4 in place of the next phase. `game_over` (406) is thin: winner only. It flips
every client to observer and the server follows it with the withheld backlog, `roles_assigned`
leading. A seated human's "you won / you lost" is client-known from `role_assigned` + `winner`.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `over.where-it-ended` | `game_over`. **Chapter mark: Game over** | P | the last scene's frame, held. After a morning: the night's paint behind the shutter, the room empty, the last card drawn up. After a lynch: dusk, the shutter down, the leaves standing open, the card gone | D: the ending line | 2.0 |
| 2 | `over.winners-hour` | `winner` | P | the shutter rises: full day for the village, night for the wolves, dusk for the serial killer; the leaves fold if open | — | 3.0 |
| 3 | `over.verdict` | 〃 | P | a walnut board comes down on two strings, large and centred: the faction's colour at its edges, its sigil on a paper plate, "The wolves have won" in the card's serif, "Day 4 · at the morning" beneath; drawn up as the next beat begins | — | 3.2 |
| 4 | `over.winners-stand` | 〃 + the roster | P | the stand comes up and the winning faction's **survivors** rise into it, base state: one at full size, two at 0.78, three at 0.6 with the box widened (×1.36, ×1.6); one special each; the plaque names the seats (and roles once the truth is out); the winners' wing tiles lit, the rest dimmed; the fallen stay on the wing as sigils. The box: "The wolves have won", the survivors' chips, "Seat 8 is the last of them standing". S: "You won" / "You lost. You were the vigilante" | — | 3.0 |
| 5 | `over.truth` | `roles_assigned` from the backlog (live) · already in the log (replay) | everyone | every living tile takes its faction strip and sigil badge; live: the X-ray button reads "unlocked" | F: the deal, and how each seat went | 2.6 |
| 6 | `over.epilogue` | `memory_extracted` (407; memory-on games) | everyone | the film comes down over the whole stage, one sheet. Left: one tab per **role** (observations are keyed by role), the chips of the seats that held it, a tally of verdicts as pips. Right: rows grouped by phase (discussion · vote · night), each collapsed to its scenario (chevron, "Scenario", the situation clamped to two lines, "open"); opened: "What it did", "How it went" with the verdict's stitched patch (worked · cost · mixed · unclear). Bottom: the lessons kept (`strategy_points`) as slips, situation → action; empty says "None from this game" | F (full stage) | until dismissed |
| 7 | `over.curtain` | — | P | the winners at the stand in the winner's hour; the result in the box with the way out (live: the replay, the lobby; replay: the transport at its end) | — | hold |

A seat that died earlier is a spectator here: its card button reads "on the wing"; its box says it
was watching from the wing.

As built 2026-09-25 (bench 73's measures and timings; the rest no bench gives, change here first):
the game stopped at a morning if the last day's night was resolved, else at the lynch. Top strip
"Morning N · The report · Where it ended" (after a lynch "Day N · The vote · …") through the hour,
then "Game over · Day N · the wolves have won · <label>". Where it ended: "The report · Seat 1 was
killed by the wolves: a villager. Seat 9 was shot by the vigilante: the healer." or "The vote's
end · Seat 8 is voted out, 3 to 0: a wolf." (bench 73); played after a morning, the last card is
drawn up (0.9 s after 0.1 s). The hour: the paint crossfades 1.2 s after 1.2 s, the shutter rises
after 0.4 s, open leaves fold. The verdict: 1.5 puppet widths wide (at most 0.52 of the stage),
0.17 tall, centred at 0.36; its second line in capitals, "DAY 4 · AT THE MORNING" / "AT THE VOTE";
down 1.1 s after 0.4 s, up 0.8 s after 0.1 s. The stand fades in 0.5 s after 0.6 s; the winners
rise at 1.1 s, 0.22 s apart, out of sight until then; the box after 1.6 s. With the X-ray on, the
film is up and the room is laid out beside it, the winners' set at 0.84 (bench 73's `kk`). The
plaque names the seats ("Seats 3 and 8") and, from the truth on or with the X-ray, the roles in the
winners' colour. S: "You won. You were a wolf." / "You lost. You were the vigilante." (+ "; you
were watching from the wing" when dead). The truth adds "Every card is face up: the wing carries
the whole deal, and the film opens for everyone." (bench 73); "X-ray · unlocked" on the live HUD
only. The film, with the X-ray on as bench 73 has it: at the stand and the curtain "The winners'
last notes · the last note each wrote"; at the truth "The deal, and how it went · every seat, face
up", each seat's role and fate ("night 2, the serial killer", "day 3, voted out", "survived"),
"Withheld all game; every viewer holds it once the game is over." The epilogue: "What the game
taught · each role's own account of its play, before any of it is kept · 51 observations · no
lessons kept"; the winning side's tab open first; the pips grouped as a tally (worked, mixed, cost,
unclear; bench 73 kept the extraction's order); `net_verdict` positive → worked, negative → cost;
an outcome loses its leading verdict word; a tab change closes the open row; "None from this
game."; a game with no extraction gets "No memory was kept." The sheet comes down 0.6 s after
0.5 s over the stage dimmed 0.5 s after 0.3 s. The curtain's way out (live): "Watch the replay",
"Back to the lobby", inert until the container hands the scene something to call. **To
reconcile:** the winners come from the roles the view holds; live, `game_over` arrives before the
backlog's `roles_assigned`, so a spectator's stand is empty until it lands (a seat knows its own
role, a wolf its pack) and the live queue should hold the stand for the backlog.

## 11. The replay's container — H§5

**Chapters** (marks on the seek bar, from events that happened):

| Chapter | Anchored on | Beat |
|---|---|---|
| Day N | `phase_change: day` | `deal.day-begins` (day 1) · `morning.day-begins` |
| Vote N | `phase_change: voting` | `vote.opens` (absent on a no-vote day) |
| Night N | `phase_change: night` | `night.hub` / `rnight.hub` (absent if the game ended at the lynch) |
| Morning N | `night_result` | `morning.shutter-down` |
| Game over | `game_over` | `over.where-it-ended` |

**The transport:** previous chapter · back a beat · play/pause · forward a beat · next chapter.
Chapter jumps land on the chapter's first beat, still. Arrow keys step beats. The beat's name sits
next to the phase label ("Vote 3 · A chip is counted"). The seek bar is the whole log with the
chapter marks. **Speeds:** normal · fast (holds halved, motion kept) · skip (no motion, minimal
holds). No scrubbing over seconds; `seq` is the only clock. **Arrive still, play moving:** seeking
renders the beat at rest; playing forward animates.

**The drawer** (H§2): the public record for everyone (speeches; GM lines verbatim with the sigils
of the lynch/night atoms lent to them; the votes as one line per day, landing with the result
(held back through the count, since `vote_cast` is a batch and the stage reveals it a chip at a
time; ruled 2026-09-26); the game master's vote line, which names the lynched seat's role, held
back on a lynch day until `lynch.truth` for the same reason; the ending); a
seated human's private results as dashed "Only you" lines; a wolf's pack chat with the red edge;
X-ray on adds, in aqua: roles after names, passes with reason and draft, the night acts, the pack's
talk, everyone's private lines as "Only seat 4", the day's brief in its Morning (clamped, opens on
a tap). Chapters run down the drawer as rules; rules with nothing under them disappear. Filters:
days as tabs at the foot; seat chips at the head (dead dimmed, still selectable); Show › Public /
Private / X-ray, all on. In the replay the drawer stops at the current beat.

As built 2026-09-25 (benches 74 and 52 where they give it; the rest no bench gives, change here
first). **The slot:** `Presentation.slot` is `'drawer' | 'film' | null` (null = closed; the film
exists only with the X-ray on, so `film` without it reads as closed); `src/stage/slot.ts` holds
the rules. Transcript brings the drawer, or closes it if it is there. X-ray off → on and the film;
X-ray on with the drawer (or nothing) in the slot → the film (bench 74's revision 41); X-ray on
with the film → off, and the slot closes. The X-ray button reads pressed while the X-ray is on
(bench 74 pressed it only with the film up); Transcript reads pressed while the drawer is open.
The workbench writes both to its URL (`slot=drawer|film|none`, default none; `viewer=xray`,
landing on the same moment of the log in the re-cut beat list). While either is open every scene
lays its room out with `geometry(hud, true)`; the night rooms slide their painting left so its
window and its photo line stay in the narrower room. The replay's night and the ending now follow the slot, not the X-ray (this settles
§9's "to reconcile"), and the film below replaces the stand-in panels §8 and §9 describe.
Nothing sits beside the epilogue: the ledger is the film at full stage.
**The drawer:** 635 units wide (`slotW`), the whole height (its head 73.6 below the top, the top
strip's buttons over it), z under the strip's buttons and the epilogue's veil. It stops at the
rail on the prompts (`day.your-turn`, `vote.your-ballot`) and for the whole of the night rooms
(`room`, `pack`), whose chat and plate keep the band. On a phone (`data-small`) it runs full
height beside the car's prompts and the own room's plate, which stop short of it; only the
pack's chat, which spans the band's right, keeps it at the rail (`railHolds`, 2026-09-27). The lit line scrolls to 0.6 of the list's
height (bench 74); with no line of its own the drawer shows its end. Wording: a pass reads the
box's accepted reasons ("held back: nothing new to say"; bench 74 wrote "held back by the novelty
gate"); the vote "The table votes, 7 ballots at the count"; acts "Seat 4 checks seat 1" (the
bench's verbs); the kill "The pack chooses seat 1"; theirs-only lines "Only seat 4 · the
investigator's reading · Seat 1 is a villager.", "Only seat 7 · Night 4 · Seat 7 shot seat 9.
Seat 9 survived.", "One cap left.", "Only the pack · the game master's note, verbatim"; the brief
"The day's brief, day N · what the agents carry from here", three lines, "open"/"close". The
brief sits after the morning's private results and shows from its own carried-summary beat on
(bench 74 put it straight after the dawn line; that would show it before its beat). The closing
game-master line stands for `game_over` (the Game over rule goes before it); a separate "The
wolves have won." line only when no such line exists. The seat filter is one seat at a time (a
second tap clears it), as bench 74. **The box beside the drawer:** narrows to the room, holds at
most 3.4 lines and fades from the second line (in lines, not percent, so a short line never
fades), header "full line in the transcript". Under the film the box keeps the whole band (bench
74; benches 67 and 73 had narrowed it). **The film:** the `sideSlot` rectangle, turned −1.2°.
A turn: tabs Note, L1–L3 (an override's tab in the slip's paper with the dot); the Note tab's
foot "Note, seq 203, written after the turn; 3 lessons weighed at seq 174, carried over from its
first turn that day; reads seq 175."; a lesson tab: the lesson, the stamp (follows · overrides ·
not relevant) with the agent's why, then "When it applies" and the situation. The open tab is the
container's, so it holds as turns step. The note is the one written between the turn and the next
slot, read from the view ahead (`SlotInput.ahead`). The count (from the ballots' drop to the
lynch's drop): "Inside the vote · what each voter weighed", a pip per lesson (F · O · –). From the
lynch's card to the card leaving: "Who had them right" and the seat's last note before the vote as
a small slip. The morning's brief: "What day N taught · the brief the agents carry into day N+1",
Accusations (accusers → accused, the evidence type as a stamp, the reasoning, "Defence: …"),
Claims, Blocs, Mood ("None." when empty). The deal face up and the truth reuse one list ("Face up
in the X-ray; the table knows only the cast." / "Withheld all game; …"). A beat with nothing
inside: "Inside · <beat> · Nothing inside this beat. The film fills at a turn, the count, the
lynch's card, a morning's brief and the night's acts." The note's face is Patrick Hand (next/font).
**The reads on the wing:** every seat in the speaker's last `player_reads` before the line takes
the blue edge (unclear reads too, as bench 74), a sure read the brighter ring; a tap opens the
card, 304 wide, docked at the wing's edge level with the tile, kept on the stage; a second tap or
the next beat closes it. The truth is marked ● role · ◐ side · ○ none/wrong (bench 74 drew ✓ ◐ ✗).

As built 2026-09-25, the container (step 6a; bench 73 draws only the five buttons and the seek
bar, the rest no bench gives, change here first). `src/stage/containers/ReplayTheatre.tsx` holds
the state (cursor, playing, speed, X-ray, slot, the drawer's filters, the film's tab); the presses
are one reducer (`replay-state.ts`) over `transport.ts` and `slot.ts`; each beat's fold is kept by
its `end` (`fold-cache.ts`), so a step forward folds only the new events. **The band:** bench 73's
buttons, 46.4 × 40 units, radius 11.2, 6.4 apart, 9.6 off the foot, from the wing's edge + 22.4;
its glyphs, and a pause of two bars (ours); play reads pressed, in amber, while playing. Then the
beat's label from `transportLabel` ("Day 3 · Speaks") over the seek bar, "37 / 109" at its right;
the bar is bench 73's (6.4 tall, cloak, amber to the beat) with a tick per chapter (3.2 × 12.8,
bone3, bone once passed, its name on hover), beat i at i/(n−1) of the width; a click seeks to the
nearest beat, still. Speed: one segmented control, "Normal · Fast · Skip", the pressed one in bone
(as Transcript). The X-ray: a pill, "X-ray on" in the film's ink or "X-ray off" in bone3, which
only says it (the strip's button switches it). Beside a full-height drawer the band ends 12.8
short of it; otherwise (the film, a prompt, the epilogue) 22.4 from the right edge. **Playing:** a
timer on `holdFor`; a beat that waits (the epilogue, the curtain) and the last beat stop the play;
play at the end starts from the first beat, play on a waiting beat steps on at once; stepping or
seeking while playing plays on from there. The hold pauses while a pointer or a touch rests on a
`[data-speech]` (the speech box, the pack's chat) and resumes with what was left; a new beat or a
new speed starts a fresh hold. Keys: ← → step, space plays/pauses, [ ] jump chapters (not while
typing). **The drawer** opens by default, closed when the window is at most 540 px tall (a phone on
its side). **Orientation:** while the viewport is upright (any device) a card covers the page: a
phone outline turning, "Turn your phone", "The stage plays sideways. On a computer, make the window
wider than it is tall."; on a touch screen the first tap asks for fullscreen and
`screen.orientation.lock('landscape')` where the browser has both (Android's Chrome).

As built 2026-09-25, the polish pass (no bench gives these; change here first). **The drawer's
empty text:** "Nothing said yet." while the drawer holds no line at all (the deal), "Nothing here
under these filters." once it does. **At an X-ray night's spoke** the drawer shows that night's
branches (a seat's act; the pack's talk and kill) as far as the spokes have got: the branches
before this one whole, this one up to the beat's `seq`, none after it, a branch ordered by its
last line as the spokes are (`spokeCut` in `drawer-lines.ts`; the beats keep the whole night's
`end`). **The way back:** a "Replays" link to `/replays` at the top strip's left, over the wing,
level with the mode buttons (`SlotInput.back`, handed down by the replay's container only; live
and the workbench have none).

## 12. Live pacing — H§6

Live has no transport. Beats animate as events arrive.

- **The dock and the clock never wait for the stage.** When `input_request` arrives for me, the
  dock opens at once and the countdown runs on real time from `deadline`; beats queued between the
  stage and the request drain at fast speed so the stage catches up to the turn beat.
- Anything queued more than one beat behind the stream drains at fast speed (the count and the
  morning can fall behind; the live ballot drop cannot, it is paced by `phase_progress`).
- On reconnect, history renders still at the latest state; the backlog is not played.
- **The deal on first connection (ruled 2026-09-25):** a solo game starts before its page connects,
  so the deal is history by the time the seated human arrives. Exception to "arrive still": when
  the history holds no `turn_started` yet (nothing has happened but the deal), the stage plays
  from the first beat at normal speed, so the human sees their card. A reconnect later in the
  game lands still as before. A browser reconnect mid-game is a catch-up too: the store marks
  the boundary at reconnect and nothing before it plays.
- Solo games: `deadline` null; the dock opens, the clock shows no ring.
- The ending: `game_over` arrives before the backlog's `roles_assigned`, and the winners' stand
  needs the roles. The live queue holds `over.winners-stand` until the backlog has landed (the
  verdict beat covers the wait); `over.truth` then plays as written.
- **The slot (ruled 2026-09-25):** when the drawer or the film is open, the room lays out for the
  open side slot (the `side` geometry in `units.ts`: the puppet slides left, the box narrows), in
  every scene, live and replay. The stand-in panels that overlaid the room are replaced by this.

As built 2026-09-25, the container (step 6b; bench 72 draws the speaking turn, the rest no bench
gives, change here first). `src/stage/containers/LiveTheatre.tsx` holds the state (the beat on
stage, the slot, the drawer's filters, the film's tab, the open turn); the rules are one pure
reducer (`live-state.ts`) over `live-queue.ts` and `transport.ts`. **History or news:** an event
is news iff the store marked its seq live; the log's head up to the first news is history, and
every beat whose `end` lies inside it lands still (the stage jumps to the last such beat, nothing
plays). News plays: a beat animates in and holds `holdFor(beat, normal | fast)`, the timer steps
on when it runs out; a beat with no hold waits (a prompt while it is open, the epilogue until
"Close the sheet", the curtain). The list is recut on every event and on game over (X-ray on for
everyone: `view.winner !== null`); the stage is carried by which beat it was on, then by seq.
**The prompt:** open iff the status lists the seat (or the request is newer than the status),
this client has not answered it, its deadline has not passed, the seat is alive and the game is
not over. While open and further down the queue, the beat on stage is cut short once and the rest
drain fast (live-queue's rule). The clock runs on the request's `deadline` in server time
(`serverNow()`); its whole is arrival → deadline, or 120 s when the request came as history; a
draft's returned `deadline` replaces it. A request that runs out unanswered from here, or is
handed over, is the agent's: my `speech` answering it carries, on my screen only, the plaque's
tag "your seat's agent" (the agent red) and the box's "your seat's agent spoke for you" (amber).
**The dock** (`instruments/TurnDock.tsx`, bench 72's `.say2`): in the notice zone beside my card,
full band (the drawer stops at the rail); head "Your turn to speak" · "Say something to the
table, or pass." (+ " If the clock runs out, your seat's agent speaks for you." with a deadline)
and the count in red `m:ss` (none in solo); the textarea 64 units tall, "Say something…",
Ctrl/⌘+Enter says it; one row under it: **Say it** (gold; "Saying…"), **Pass**, the notes field
("Or jot notes (“8 dodging, why abstain?”)", 500 chars, Enter drafts), **Draft from notes**
("Drafting…"), "n drafts left", and at the right "Let my agent speak" (`{delegate: true}`); the
server's words under the row in red. Draft errors: 409 → its words and no drafts left, 422 → its
words, anything else → "Could not draft the line; type it instead." (the notes kept). Send
errors: 409 → "That turn was already answered." and the request is let go; 422 → its words. My
puppet stands thinking; the paint's wall clock is swapped for the instrument at 2:12 with the red
ring (beside the drawer, which stops at the rail, it hangs between the wing and the puppet; §2). A prompt that
is not the day's (the ballot, a night act, the pack) gets a pill under the top strip, "Let my agent
play this turn", its error beneath. **Counts:** `phase_progress` feeds the vote's jar and pill
at the opening ("Ballots in, n of N") and the night hub's "Acted n of N" (clamped to the census)
with the wall clock at 6·n/N hours. **The curtain:** "Watch the replay" → `/replays/{id}`, "Back
to the lobby" → `/rooms` (links). The drawer opens by default as the replay's. "Reconnecting…"
under the strip while the stream reconnects. **The deal on first connection:** a new game's
deal is over before the page connects, so while the history holds no `turn_started` it plays from
beat 0 at normal speed (the deal's beats keep normal speed even with news queued behind them,
unless my prompt is waiting); the history counts as all in once news has come after it or it
reaches the status's `last_seq` at connect, and until then the stage waits on "The table is being
seated…" rather than land. **The reconnect boundary:** from the moment the stream drops until a
fresh `GET /games/{id}` after it reopens, every event is catch-up, and after it anything up to
that status's `last_seq` (`hooks/catch-up-boundary.ts`); the store keeps the newest catch-up seq
that extended the log (`caughtUpTo`, not a late insert like the backlog after game over), and the
history runs to it, so the missed events land still. **Not built / to reconcile:** the live
ballot drop (§3 row 2) moves the count, not chips; "your seat's agent played 3 turns for you"
after a return (the client forgets across a reload); Draft from notes in the pack's chat; a
reload during a vote already cast reopens the ballot (a second send gets the 409 line).

## 13. Viewers and tiers — H§7

| Viewer | Day | Vote | Lynch | Night | Morning | Game over |
|---|---|---|---|---|---|---|
| Spectator (P), and the replay with X-ray off | the theatre | the jar, the count | all of it | the lobby: chips, count, clock | the report, chip by chip | the verdict, the winners, the truth, the epilogue |
| Seated human (S) | + my turn: my puppet, the box, the clock, the draft | + my chip row and face-up chip | + "you are voted out", my card | my room on my turn; the lobby after | + what only I learn | + "you won" / "you lost" |
| Wolf (F) | as S | as S | as S | the pack's room, the chat, both teeth as they land | + the pack's note | as S |
| Replay, X-ray on (X) | + notes, reads | + the voters' consults; the ballots named at the drop | + who had them right | hub, spokes, whole; every act, consult, note | + all private results; the carried summary | + the deal and how it went |

## 14. Polish list (seen on the built scenes, not yet fixed)

None open (the 2026-09-25 list is fixed; each fix is an "As built" line in its section).

## 15. Open

- `firing_reason` and `addressed_targets` (deferred by decision; the fold already joins them).
- Motion inside the night rooms beyond the timings above.
- Whether a seat can be reclaimed after leaving (the server's call).
- The landing's miniature replay: which beats it plays (decided with the landing).
