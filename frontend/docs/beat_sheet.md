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
everyone after `game_over`, from the moment the stage reaches the ending, 2026-10-01; the live
cut has no X beat before it). A beat marked S or F is also in the X-ray replay, shown in the
X-ray's verdigris (aqua until 2026-09-29) as "Only seat n". *Stage*: what changes on the stage.
*Slot*: what the drawer (D) or the case file (F, the X-ray's pane; the film until 2026-09-29) does;
"—" = nothing new. *Hold*: the replay's wait at normal speed. *Bench*: the revision that drew it.

**Holds** (H§5; raised to a reading pace 2026-09-30, the replay's Normal having felt fast; raised
again 2026-10-01 for a live game at reading pace, where music will sit in these holds; live and
the replay share them): shutter 6.0 s (3.5 until 2026-10-01, 3.0 before 2026-09-30) · a chip
2.5 s (was 2.0) · the lid 2.5 s (was 1.5) · a card read 4.0 s (was 3.2, 2.6) · your own card at
the deal 8.0 s (was 6.0) · your pack at the deal 6.0 s (was 4.0, ruled 2026-09-28) · the verdict
6.0 s (was 3.2) · the vote's opening move 4.0 s (was 3.2, 2.8) · the morning's roll 6.0 s and
2.0 s a row read (was 3.5 and 1.5) · a room's last step in the X-ray night (the mark, or the
hold) 4.0 s (was 2.5, a chip's 2.0) · a plain held beat 2.0 s · a pass 4.0 s · **speech** = words
÷ 2.4 per second (2026-09-30; was 3, and 4 before 2026-09-28), held while the pointer or a touch
is on the speech. (2026-09-30 kept the count's chip, lid and verdict; 2026-10-01 raised them
too.) The scenes' Hold columns below are the values as first drawn; these rule. Fast (the
replay's) halves every one. **A day speech is told in pages (ruled
2026-09-29):** the speech box is a fixed three lines, so a line longer than a page
(`PAGE_CHARS` = 150 characters, `beats/pages.ts`) is cut into pages, each its own `day.speech`
beat marked `page` n of m, all sharing the speech's anchor; a page ends at the last sentence end
that fits, else the last clause break (, ; : —), else the last whole word, never mid-word. Each
page holds for its own words at 2.4 per second, floor 5 s, cap 15 s (was 3, 2.5 s, 9 s); a tap on the box moves on to
the next page. Wolf messages and the X-ray night's spokes are read in a chat, whole: words ÷ 2.4,
floor 5 s, cap 15 s. Live plays every beat at these holds at normal speed, in arrival order,
however many are queued (§12, ruled 2026-10-01).

**Live vs replay.** Live plays every beat its tier receives, in arrival order, with the queue
rule of §12. The replay plays the P beats with X-ray off and P+X (plus every S and F beat, in
verdigris) with X-ray on; toggling X-ray re-cuts the beat list, so the seek bar re-marks (the
cursor keeps its beat where both cuts have it; a room of the X-ray's night, its hub or its whole
lands on that night's public `night.hub`, never the morning, 2026-09-30).

**The right slot** holds one thing at a time, the drawer or the case file; the two buttons switch;
the X-ray state stays either way. The viewer knows the X-ray as **Reveal** (owner, 2026-09-29): the
strip's switch, "Reveal" / "Revealed"; the code and these notes keep "X-ray". Turning X-ray on resets the drawer's Show › X-ray filter to on.

**Seats** are `player_1..player_9`, shown as the numeral 1–9. The cast (character per seat) is
`castForGame(gameId)`.

**The seat rail (the wing; HUD pass 2, ruled 2026-09-29, "B on photo stock").** Every seat is a
card down the stage's left edge, printed as the same head-portrait photo the night rooms pin up
(cream print stock, the numeral in Young Serif on its corner), each tacked with a brass tack to
a cork board in a walnut frame with a brass edge, a soft contact shadow under it (v2, owner
2026-09-29: the cards read as hung in the air on the plain walnut). The layout comes from the seat count, never from nine (`rail-layout.ts`): two
columns, the cards as tall as the rail allows; the suspect slot takes the spare cell (odd
count) or a strip across the foot (even count); more than six rows takes a third column. The
rail is 192 units inside the world, 12% of it (the room is laid out right of it; 144 drew the
desk's cards too thin), and on a screen wider than 16:9 it grows out into the bleed: 310 units in
all for two columns, about 134 css px on an iPhone 14, 51 of them in the letterbox. One card stock for every state: the speaker's
card is edged in brass; a dead seat is the same photo gone grey with its role on its faction's
ink band and a black crepe mourning ribbon across the photo's top corner (2026-09-29); your own seat an amber "You" band; with the X-ray on, a living seat its faction's band
and the sigil badge; the game's losers dimmed. Lit and dimmed are light only.
**Notes (live, seated only).** Tapping another seat's card opens its note editor (the seat's
head, number, alive or dead; a ruled writing area; "Mark as suspect", not for the dead; Done;
Escape or a tap outside closes). The editor stays open while the beats, the scenes and the
recuts go by under it (2026-10-01; it closed on every beat, the wing being remounted with each):
the container holds which seat it is on (`SlotInput.notebook`), the words are the notebook's as
typed, and a remounted editor puts the focus and the caret back where they were (an open role
list stays open). It closes on Done, Escape or a tap outside, when its seat dies (as the stage
tells the death; a seat already dead when opened stays open), or when the seat can no longer be
written on; the focus goes back to the card that opened it if that card is still on the rail,
else nowhere. The first time in a game a paper slip beside the rail says "Tap a
card to write notes" until the first tap. A card the player may write on has two or three
faint ruled lines on its foot, the note's first words on them in Literata, never under 11 css
px; where they would be smaller (a phone) the card shows two short pencil strokes instead, and a
tap reads the note. One suspect at a time: a wax seal on its card and its
head in the suspect slot (a suspect who dies leaves the slot empty). Under the note (owner,
2026-09-30), a role guess, "I think they are… ▾": the roles a living seat could still hold (the
cast's counts less the roles the dead have shown, "Wolf · 1 left"), and "not sure"; not for the
dead. A guess shows as the role's sigil on a small paper disc with a pencilled (dashed) edge at
the photo's lower left, never the X-ray's badge. All of it stays on the
device (`notes_{gameId}`, the guesses an added field an older notebook reads without); it reaches the server only with a speech draft the player sends it
along with ("Use my seat notes", ticked; D25), the guess folded into that seat's note on the
device ("(I think: wolf) …") so the request is the server's as it was, and the suspect never preselects a ballot. In a replay and for an observer the cards are only shown: no editor, hint or pencil lines.

## 1. The deal — H§4.0 · bench 75

The first scene of a match. Nothing on the wire narrates it; every line is the client's.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `deal.table-seated` | `game_started` (seq 1) | P | dining car at dawn, shutter up, room empty; nine chips come down from the flies in seat order as the seated table | D: nothing (no wire line) | 3.0 |
| 2 | `deal.cards-dealt` | `game_started.cast_role_counts` | P | nine face-down cards come down on the same strings, one under each chip; the plate reads the cast counts | — | 3.0 |
| 3 | `deal.your-card` | my `role_assigned` (seq 2–10) | S | my card comes down large, centred, on its own string, and turns face up; the box: who I am, my night action; the vigilante counts two caps; the card button appears | D: dashed "Only you" line | 6.0 |
| 4 | `deal.your-pack` | my `role_assigned.pack` | F | the packmate's chip takes the red edge, its small card turns to the wolf; the pack chat opens with the client's game-master line and stays open for the night | D: the pack chat's opening line | 4.0 |
| 5 | `deal.face-up` | `roles_assigned` (seq 11) | X | all nine small cards turn at once; the wing's cards take their bands and badges | F: the deal listed | 2.6 |
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
X-ray night's spokes hang the same row, so they narrow too). A small card's face (2026-09-30; it
was the sigil, large): the role's name over its felt figure, the big card's and the night room's
table card's art, and the sigil small by "Seat n" at its foot. At the deal's size on a phone the
name is a few css px, past reading: there the figure and the faction's bands carry the role, and
the wing's bands name it.

## 1a. The platform — the waiting room · review 2026-09-26 §A5, F1 · live only

A room before its game: `/games/[id]` while the status says `waiting`, on the same stage the game
plays on (landscape, under the orientation guard), so Depart hands straight to §1 row 1. A room has
no event log: every beat is keyed on the status poll (3 s while waiting) or on this device (the
host key, the seat token). Nobody has a seat yet: the i-th person to board stands at the i-th
place and wears `castForGame(gameId)[i]`, with no numeral; seats are dealt at the start and the
empty places go to agents. Never in the replay or the workbench fixture (the workbench draws it from
synthetic rooms, `SYNTHETIC.station`).
**The loading still (2026-09-30)**, not a beat: while `/games/[id]` or `/replays/[id]` loads (its
`loading.tsx`, the page's Suspense fallback, and the game page while its status or a rejoin is on
its way) the page is this platform empty (`scenes/StationStill.tsx`: the train, the lamps, the sign
"The Ninth Express", the rail's empty cards, the snow; no people, plates or chips), its ledge
fading in after 0.3 s with "Boarding…", "Reclaiming your seat…" or "Rewinding the reels…".

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
history or as news (`live-state.ts`), and the curtain lifts off it; one `<Stage>` throughout.
Whatever the log already held when the curtain came down plays on after the deal at normal
speed, as a queue (2026-10-01: a solo game's agents have taken their first turns by then, and the
stage had jumped past the deal to the latest of them; `historyLanding`'s `departed`). The snow
falls for as long as the room waits (still for reduced motion).
Depart needs one person aboard ("Nobody is aboard yet: Depart needs one person on the platform.");
the server sets no minimum, this is the client's rule from the old lobby card. A newcomer to an open
room with a place left gets the boarding pass first (a page, upright allowed: name, "Step onto the
platform", "Just watch"); a full or locked room, or a device holding a seat, goes straight to the
platform. Not built (no wire for it): the room's code, puppet choice and "Change puppet", Leave,
removing a passenger, the Ticket's model, memory and "who pays" lines, "Change the terms".

## 2. Day discussion — H§4.1 · benches 62, 72

Turns run in the log's order. The case file at a turn opens the speaker's file (§12): its notes
(`strategy_update`) written by the beat, its latest reads (`player_reads`), the precedents it
weighed (`memory_consulted`, before the turn; memory-on games from day 2). The reads are also a
verdigris edge on every seat the speaker has a read on, brighter for a sure read; a tap opens the
read card (guess, how sure, why, the truth with ● ◐ ○), a paper index card from the file.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `day.turn-thinking` | `turn_started` (first: 13) | P | the seat's puppet takes the stand in the thinking state, no clock; the speech box shows a "…" so the state reads as thinking, not idle (ruled 2026-09-25) | D: nothing yet | live: until the turn resolves · replay: folded into the resolving beat: the puppet rises thinking, holds **0.6 s**, then plays it (accepted 2026-09-25) |
| 2 | `day.speech` (one per page, §0) | `speech` | P | talking state, the line in the speech box a page at a time, "1 / 2 ▼" at its foot while more follows; X: the box carries the aqua tags (who it answers, stance) and the plaque tags the role; the wing's verdigris edges from the turn's `player_reads` | D: the line, lit and scrolled to · F(X): the speaker's file | speech |
| 3 | `day.pass` | public: a `turn_started` resolved by no speech (the next `turn_started` or the phase change), live and replay alike, since `turn_started` is public · X-ray: `pass_marker` instead (12 in the fixture), which carries the reason and the draft (ruled 2026-09-25: day 1 of the public replay is three passes, not an empty stand) | P · X | idle state, the box says "passes"; X adds the reason and the held-back draft. Reason wording (accepted 2026-09-25): `voluntary` "chose to pass" · `novelty_gated` "held back: nothing new to say" · `generation_failed` "no line came" | D(X): the pass with its reason and draft | 4.0 |
| 4 | `day.your-turn` | `input_request` `discuss` for me | S | my puppet at the stand, thinking; the dock carries the two minutes (`deadline`; null = no countdown; the car's wall clock is gone, ruled 2026-09-29); one flow: an optional steer for your agent + **Draft** / **Redraft** (the seat's own agent's line, as it would say it, steered and revising the box's line when the field holds something; "Use my seat notes" sends the notebook along when ticked; three per turn, the returned `deadline` is the new countdown), then the textarea the draft lands in, editable, with **Send** and **Pass** (no hand-over on this turn: the agent speaks only when the clock runs out; HUD pass 3b, 2026-09-29); the drawer stops at the rail so the prompt keeps the full width | D: stops at the rail | until answered / deadline |
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
idle). The car has no wall clock since 2026-09-29 (the car is a painting); my turn's time is on
the dock alone.
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
| 5 | `vote.closes` | live: the pill full · replay: same beat as 4 | P | the lid comes down. **X-ray replay: the vote's stop** (§11): the play pauses here; the notice "7 ballots in. Tap a seat to read what it voted on." with **Count the votes ▶** (plays on); every wing card opens its file | — | 1.5 (a stop: waits) |
| 6 | `vote.count-begins` | the `vote_cast` batch | P | the lid flies out; the shot pushes in; the jar tips to the back rail; plates along the front edge, one per seat with votes, abstain's an ordinary empty plate at the right, laid as the others, its place card reading "Abstain" (2026-09-30; it was an upturned saucer); every plate the painted plate (`SPRITES.props.plate`, 2026-09-30); place cards with head, seat, running number | F(X): the voters' consults and reads | 2.0 |
| 7 | `vote.chip-counted` | each `vote_cast` | P (X: the ballot named at the drop) | one chip rolls from the jar's mouth, flips face up, lands on its plate; the card's number ticks; towers cap at four; the chip that settles the winner lands last | D: (the votes are one drawer line per day at the count: a tally per seat voted for, the voters' faces its marks, and the who-voted-whom sentence) | 2.0 each |
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
1:14"; sent, "Your ballot is in · no one sees it until voting closes" (the time is on the plate; the
car's wall clock is gone since 2026-09-29). Not yet built: the live drop (row 2; the pill reads `turn.progress` once the container feeds
it from `phase_progress`), the count's X-ray film (row 6).

## 4. The lynch — H§4.4 · bench 65

Follows `vote.table-down` when `lynch_result.outcome = lynched` (250: seat 6 villager; 384:
seat 2 serial killer).

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `lynch.stand-returns` | `lynch_result` | P | the shot pulls back; the stand comes up from below the rail with the voted-out puppet rising into it from behind the playboard; the leaves stand either side; the light collapses to one special | — | 3.0 |
| 2 | `lynch.named` | 〃 | P | held; the plaque's tag "voted out". S (if me): the box "You are voted out" | — | 2.0 |
| 3 | `lynch.drop` | 〃 | P | straight down through the trap, no fade; the plaque stays lit over the empty box | — | 2.0 |
| 4 | `lynch.card-up` | `lynch_result.role` | P | the lift raises the role card (name, sigil, figure, front line, faction colour); the wing's card holds the live photo until the card clears the rail, then turns grey with the role's band | F(X), the docket: "Who had them right": each voter's `player_reads` on this seat vs the truth (● role ◐ side ○ none/wrong); the seat's last note | 2.6 |
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
table as a spectator." The docket ("Who had them right") shows at the card and the truth: each
voter's last `player_reads` that day before the first ballot; ◐ is town against not town (bench
65: a wolf read on the killer had the side). Not yet: a lynch that ends the game still plays the
night ending in `lynch.card-to-wing` (nothing in the view at that beat says the game is over).

## 5. Night, the lobby — H§4.5 · bench 67

Everyone who is not acting is here for the whole night. The villager's night is this room. Nothing
on stage changes per act beyond the count and the clock; parallelism is stated by the hub, never
by the staging.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `night.hub` | `phase_change: night` (32, 120, 253, 387). **Chapter mark: Night N** | P | the dining car, the shutter up on the night window, the living seats hung as chips in a row (the table asleep), the pill "Acted n of N" (padded; the pack counts as one) | D: the GM's "night falls" line | 3.0 |
| 2 | `night.act-in` | live only: each `phase_progress` (stage `night`) | P | the pill increments | — | real time |
| 3 | `night.your-act-in` | my POST confirmed (my room closes) | S | back in the lobby with "Your act is in"; my own mark the only one I see | D: dashed "Only you" line naming my act | 2.0 |

X-ray on (replay): the hub also lights the wing's lamps on every seat that acts tonight (§9), and a
tap on a lit card seeks to that actor's first spoke (a wolf's: the pack's); any other card opens
that seat's file. The play still runs the spokes in order.

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
| 1 | `morning.shutter-down` | `night_result` (58, 156, 270, 401). **Chapter mark: Morning N** (not a phase change: 156 comes before `phase_change: day` at 159) | P | the shutter comes down; the chips go up; the report plays in the night's paint. The notice is **the morning roll** (2026-09-30), on the walnut board: a row per death (the chip, "Seat 1 · Villager", the attacker's felt sigil and the game's words: "killed by the wolves" · "stabbed by the serial killer" · "shot by the vigilante"; two attackers "attacked by X and Y, and fell"), a row for a seat saved ("attacked by X, saved by the healer", no role), a quiet night "No one died in the night."; the rows fade in 0.6 s apart. A game that ends at this morning shows the same roll at `over.where-it-ended` (§10), at the same hold | D: the GM's dawn line, with the night atoms' sigils lent to it | 3.5 + 1.5 a row |
| 2 | `morning.chip-attacked` | each entry of `deaths` and `save`, in order | P | the chip comes down alone, at the centre, large: "Seat 3 was attacked in the night" | — | 2.0 |
| 3 | `morning.chip-fell` | a `deaths` entry | P | the act mark appears beneath it (from `attacker_types`: the attacker's felt sigil tacked on, 2026-09-30: wolf's head · scythe · bullet); the string gives way; the chip drops | — | 2.0 |
| 4 | `morning.card-down` | 〃 (`role`) | P | once the chip has fully dropped, the role card comes down large and centred; the wing's tile flips; the card is drawn up out of frame as the next beat begins | — | 2.6 |
| 5 | `morning.chip-saved` | the `save` entry (58: seat 1, wolves + serial killer) | P | the attackers' marks small and the healer's cross large beneath it, the ribbon on the string; the chip goes back up whole | — | 2.6 |
| 6 | `morning.quiet` | `night_result` with no deaths and no save | P | the line alone | — | 3.0 |
| 7 | `morning.only-you` | `investigation_result` (59) · `vigilante_confirmation` · the pack's failed kill: `wolf_message` from `game_master` (271, arrives after `night_result`) | S · F | one beat after the report, on my screen only. Investigator: the target's chip comes down and turns to its sigil, the lens beneath (the one private result that names a role). Wolf: the target's chip down whole, "Your kill on seat 2 failed. Seat 2 survived", no sigil (the GM's verbatim note names the role; that wording is X-ray's). Vigilante: the same shape, "You shot seat 2. Seat 2 survived", no sigil; the caps count (`bullets_remaining`, 402, is a view update, not a beat). The healer has nothing private. A kill the healer stopped is public (the save names its attackers) and has no private beat | D: dashed "Only you" line · X: in aqua, "Only seat n" / "Only the pack" | 2.6 |
| 8 | `morning.carried-summary` | `day_summary_structured` of day N (the summary of the day just ended) | X | none on stage | F, the docket: the typed brief: accusations as rows (accuser → accused, evidence type, defence), then claims, blocs, mood. The summary of a day on which the game ended at the lynch is dropped (never consumed) | reading time |
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

A linear sequence, not a picker, with a stop at its hub (owner, 2026-09-30). The transport steps
through it as beats; the Night N chapter mark lands on the hub.

**The night stop (X-ray on).** The play pauses at `rnight.hub`, at normal and fast speed alike,
and a seek or a chapter jump lands there paused too (`containers/stops.ts`; a night with no room
to visit plays on). On the wing the seats that acted (read from the log ahead: a branch's seats,
the pack's as its wolves living at the hub) breathe a clear verdigris glow, a 3.2 unit bright
edge and a glow whose opacity alone moves (2.0 s; still for reduced motion); a seat whose room
has been seen keeps a steady, quieter verdigris edge and its lamp goes out. **The word says it
(2026-09-30; the glow alone did not read as lit):** on the cream between each actor's photo and its
band, "Visit ▸" in the typewriter, bold, in the paper's verdigris ink (`--ink-follow`), and
"Seen" in a muted grey once its room has been visited; the glow is secondary. The notice at the
foot (the walnut board with a brass edge, the speech box's material, in the Notice zone): "Night
2 · 5 acted." (rooms, as the pill counts them: the pack's two wolves are one) "Tap a lit seat to
visit its room." and two buttons, **Watch them all ▶** (the play goes on through every room in
order, seen or not, then the whole, then on) and **End the night →** (to the first beat after
`rnight.whole`, playing). A lit seat's tap plays that actor's room from its first step (a
wolf's, the pack's) at its holds and **rests on its last step**, paused (2026-09-30; it came back
to the hub by itself): **← Back to the night** is the way back, and the same seat tapped again,
from the hub or its own room, plays it again from its first step. **From inside a room** the
wing works as at the hub: another actor's card ("Visit ▸" or "Seen" on it) goes straight to its
room, the room's own actor plays it again, anyone else's opens its file. Play (the band's ▶) from
a room goes on linearly; the arrows and the step buttons always step linearly. In a room the
notice (the act's line; the pack's chat, in its header) has the back button. **Every seat that
took a night decision has a room (2026-09-30),** a decision not to act included: a seat that
consulted or read its night and chose no one (the vigilante holding its fire; the log has no act
for it, only its `memory_consulted`/`player_reads`) gets a one-step room, its card on the table,
no light, pin or mark on the wall, the box "Seat 7 · vigilante · holds its fire." (anyone else
who chose no one: "does not act."), counted in "N acted" and in the pill as its step shows, a
row "holds" on the night's sheet. With the file up, the night's sheet ("The night") leads with
"Visit a room", each actor's faces a button into its room, then the file's call to action (§11).
Nothing of it is kept: which rooms were seen lasts as long as the page.

**X-ray off:** `night.hub` → §8. Nothing on stage says who was awake.

**X-ray on:**

| # | Beat | Anchor | Stage | Slot | Hold |
|---|---|---|---|---|---|
| 1 | `rnight.hub` | `phase_change: night` | **the night stop** (above): the hub with the wing's lamps lit on every seat that acts tonight, the ones that acted glowing, the visited a steady mark; a lit card plays that actor's room, any other opens its file; the notice with Watch them all ▶ · End the night → | D: the night's lines | 3.0 (a stop: waits) |
| 2 | `rnight.spoke` (one per actor's branch, branches ordered by their **last** event; a step per pack line and one for the mark. The pack closes nights 1–2 of the fixture; on nights 3–4 the lone wolf votes before the killer and the vigilante act, so the rule is the order, not the pack) | the branch's events: `memory_consulted` · `player_reads` · `night_action`, or for the pack `wolf_message`… `wolf_vote` · `wolf_kill_decided` | the actor's own painted night room (the one live play seats that role in): its card on the table, the seats it could choose as photographs on the line, the choice landing as live shows one (the light and the pin on the target's photo), then the act's mark on the print; the pack's room for the pack, its talk in the chat a line at a time, then the votes and the kill decided, both teeth landing with the pin; the lamp goes dark as the spoke ends; "← Back to the night" on the act's notice (the pack's: in its chat's header); a room visited by a tap rests on its last step (2026-09-30); a seat that held has a one-step room with no mark | F: the actor's file (the pack's spoke: either wolf's, flipped from the cover) | per event: a mark (or a hold) 2.5, a message speech |
| 3 | `rnight.whole` | after the last spoke | every mark on the row at once: the picture the parallel night never shows anyone live | — | 3.0 |

Then §8.

**Ruled 2026-09-29: the spokes are told in the actor's room** (`ReplayNightScene` mounts `NightRoom`
with the actor's role; it replaces the car-and-stand spoke described below, whose stand, figures,
rail instrument and window-height row are gone; the hub and the whole stay in the car). The photos:
the living but the actor (the pack: the living who are not wolves), in seat order. At a solo
spoke's one step the light finds the target's photo and the pin goes through it at 0.9 s, the act's
`ActMark` pops on the print's lower left at 1.4 s, the box ("Seat 4 · investigator · checks seat
1.") at the foot as before. The pack's line steps are the same room at rest, only the newest line
arriving; its mark step lands each wolf's tooth on the photo it voted for and the pin in the kill,
at 0.9 s; the chat keeps to the room (from past the wing to the slot's edge). The card on the table
is the actor's, not the viewer's; since 2026-09-30 it opens all the same ("tap to read"; the card over the room, "Seat 4 · tap anywhere to close", closed by any tap as live), the play going on under it untouched; it closes when the play moves to another actor's room. Arrived at, all of it is simply there.
The wing lights the actor and keeps the lamps; the strip and the pill are as below.

As built 2026-09-25 (bench 67 where it gives them; the rest no bench gives, change here first):
top strip "Night N · In the night · Seat 4" ("· The pack", "· Seat 8" for the lone wolf) and "Night
N · The night, whole". The file is up beside every spoke, so these beats lay the room out for the
open side slot (bench 67's `side`); the scenes before this overlay the file on the full room
instead (**to reconcile** in the container). The spokes hang the living at the window's height
(bench 67's high row), the whole across the room (the lobby's row). A mark is the act's `ActMark`
beneath the target's chip (bite · knife · bullet · plaster · lens, drawn since 2026-09-30 as the acting role's felt sigil with a brass tack through it: wolf's head · scythe · bullet · cross · magnifier), two to a row in spoke order;
bench 67 drew them on the chip (teeth, ribbon, hole, nick, lens). The instrument on the rail is
bench 67's `instrument()` (the vigilante's caps are the shots left, two until
`bullets_remaining`), the wolves' kit sprite for the pack, right of the figure at 0.72 of the
stand's half-width, in a patch of light. The pack stands as two at 0.78, ±0.25 of a puppet width,
the stand ×1.36 (the winners' grammar of §10; bench 67 put them ±0.46 on the plain stand), plaque
"Seats 3 and 8 · Wolves". A single actor's box: its chip, "Seat 4", the role in aqua, "checks
seat 2." (protects · checks · shoots · marks, bench 67's verbs). The pack's chat is headed "The
pack · seats 3 and 8" / "Seat 8 hunts alone"; a line step shows the lines so far, the mark step
adds the votes and "The pack chooses seat 4 · both teeth", and one bite lands. "Acted n of N"
counts the spokes whose mark has landed (N of N at the whole). The lamps: lit on this actor and those still to come;
this one's goes out at 1.6 s of its mark step (at rest, already out); a seat with no spoke (a
vigilante holding fire) loses its lamp after the hub. Played: a new actor rises at 0.2 s (+0.22 s
for the second wolf), its instrument fades in 0.5 s after 0.6 s, the mark pops at 0.9 s, the box
fades in after 0.7 s, the newest chat line 0.5 s. The case file (2026-09-29, replacing the film's
"Inside seat 4" panels): at a spoke, the actor's file; at the pack's, the first wolf's, with "⇄ Seat
8" on the cover to flip to the other; the whole, on the docket: "The night, inside · Night N · what
each did", "In the order the log finished them. Live, nobody sees any of this." Not built: the vigilante holding
fire as a spoke (bench 67 had one; the cutter drops a branch with no act).

## 10. Game over and the epilogue — H§4.10 · bench 73

Follows §8 or §4 in place of the next phase. `game_over` (406) is thin: winner only. It flips
every client to observer and the server follows it with the withheld backlog, `roles_assigned`
leading. A seated human's "you won / you lost" is client-known from `role_assigned` + `winner`.

| # | Beat | Anchor | Sees | Stage | Slot | Hold |
|---|---|---|---|---|---|---|
| 1 | `over.where-it-ended` | `game_over`. **Chapter mark: Game over** | P | the last scene's frame, held. After a morning: the night's paint behind the shutter, the room empty, the last card drawn up. After a lynch: dusk, the shutter down, the leaves standing open, the card gone. The notice: after a lynch the vote's end line; after a morning that morning's roll (§8) | D: the ending line | 2.0; after a morning the roll's 3.5 + 1.5 a row |
| 2 | `over.winners-hour` | `winner` | P | the shutter rises: full day for the village, night for the wolves, dusk for the serial killer; the leaves fold if open | — | 3.0 |
| 3 | `over.verdict` | 〃 | P | a walnut board comes down on two strings, large and centred: the faction's colour at its edges, its sigil on a paper plate, "The wolves have won" in the card's serif, "Day 4 · at the morning" beneath; drawn up as the next beat begins | — | 3.2 |
| 4 | `over.winners-stand` | 〃 + the roster | P | the stand comes up and the winning faction's **survivors** rise into it, base state: one at full size, two at 0.78, three at 0.6 with the box widened (×1.36, ×1.6); one special each; the plaque names the seats (and roles once the truth is out); the winners' wing tiles lit, the rest dimmed; the fallen stay on the wing as grey cards with their roles' bands. The box: "The wolves have won", the survivors' chips, "Seat 8 is the last of them standing". S: "You won" / "You lost. You were the vigilante" | — | 3.0 |
| 5 | `over.truth` | `roles_assigned` from the backlog (live) · already in the log (replay) | everyone | every living tile takes its faction strip and sigil badge; live: the File tab reads "File · unlocked" (the X-ray button's "unlocked" until 2026-09-29) | F, the docket: the case, closed (the deal, and how each seat went) | 2.6 |
| 6 | `over.epilogue` | `memory_extracted` (407; memory-on games) | everyone | the case's closing spread comes down over the whole stage, one sheet (the case file's look since 2026-09-30: manila round a typed paper sheet, IM Fell titles, the typewriter's labels, the file's calm stamp inks; it was the X-ray's blue-black film). Left: one file tab per **role** (observations are keyed by role), the open one the sheet's own paper joined to it, the chips of the seats that held it, a tally of verdicts as pips. Right: rows grouped by phase (discussion · vote · night, the case file's phase icons), each collapsed to its scenario (chevron, its ✓ ✗ ± ? mark, "Scenario", the situation clamped to two lines, "open"); opened: "What it did", "How it went" with the verdict stamped on it, mark and word (Worked · Cost · Mixed · Unclear; it was a stitched felt patch). Bottom: the lessons kept (`strategy_points`) as index cards, situation → action; empty says "None from this game" | F (full stage) | until dismissed |
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
rise at 1.1 s, 0.22 s apart, out of sight until then; the box after 1.6 s. The winners' puppets
keep the belly numeral when two or three share the stand (its one plate, "Nos. 3 and 8", does not
say which is which); alone, the plate names it and the belly is bare (2026-09-30). With the X-ray on, the
case file is up and the room is laid out beside it, the winners' set at 0.84 (bench 73's `kk`). The
plaque names the seats ("Seats 3 and 8") and, from the truth on or with the X-ray, the roles in the
winners' colour. S: "You won. You were a wolf." / "You lost. You were the vigilante." (+ "; you
were watching from the wing" when dead). The truth adds "Every card is face up: the wing carries
the whole deal, and the case file opens for everyone." (bench 73; "the film" until 2026-09-29); "File · unlocked" on the live HUD (it was "X-ray · unlocked" until 2026-09-29)
only. The case file's docket, with the X-ray on: at the stand "The winners' last notes · the last
note each wrote"; at the truth and the curtain (where a live game rests) "The case, closed · the
deal, and how each seat went", each seat's role and fate ("night 2, the serial killer", "day 3,
voted out", "survived"), a row a tap that opens the seat's final file (its last note page, last
reads, lessons and findings), "Withheld all game; every viewer holds it once the game is
over." (2026-09-29: the curtain showed the winners' notes.) The epilogue: "What the game
taught · each role's own account of its play, before any of it is kept · 51 observations · no
lessons kept"; the winning side's tab open first; the pips grouped as a tally (worked, mixed, cost,
unclear; bench 73 kept the extraction's order); `net_verdict` positive → worked, negative → cost;
an outcome loses its leading verdict word; a tab change closes the open row; "None from this
game."; a game with no extraction gets "No memory was kept." The sheet comes down 0.6 s after
0.5 s over the stage dimmed 0.5 s after 0.3 s. The curtain's way out (live): "Watch the replay",
"Back to the lobby", inert until the container hands the scene something to call. **The
curtain's wait (2026-10-01):** the replay is filed only when the engine's run ends, which with
memory on is after the lessons are written, a minute or more after `game_over`; the link went to
"No such replay." until then. Until the archive answers for the replay (asked every 5 s from
`game_over`; the status cannot say it, since a game leaves the live registry, and its status
turns `archived`, only once nobody watches it), a quiet plaque that cannot be pressed stands in
the link's place, dashed edge, bone ink: "Winding the reels… come back in a few minutes", and,
in a memory-on game whose lessons have not come in, "Your seat's lessons are being written."
under it (a spectator: "The seats' lessons…"). The link comes in where the plaque stood (both
lie in one cell, the plaque kept unseen), "Back to the lobby" unmoved; the case file's "watch
the replay →" waits likewise. The workbench draws the link's state. The replay page waits too:
a 404 asks the status, and a game over but not filed shows the empty platform with "Winding the
reels… come back in a few minutes", asking for the replay every 5 s until it comes; a status
from the row means it landed between the two calls (asked once more at once); a dropped game
says "This game was dropped."; only an id unknown to both is "No such replay.". **To
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

**The transport:** previous chapter · back a beat · play/pause · forward a beat · next chapter. Chapter jumps land on the chapter's first beat, still. Arrow keys step beats. The beat's name sits
next to the phase label ("Vote 3 · A chip is counted"). The seek bar is the whole log with the
chapter marks. **Speed:** one toggle, normal · fast (holds halved, motion kept); skip was removed
2026-09-29 (an old `skip` reads as normal, the workbench's `motion=skip|0` as fast). No scrubbing over seconds; `seq` is the only clock. **Arrive still, play moving:** seeking
renders the beat at rest; playing forward animates.

**The drawer** (H§2): the public record for everyone (speeches; GM lines verbatim with the sigils
of the lynch/night atoms lent to them; the votes as one line per day, landing with the result
(held back through the count, since `vote_cast` is a batch and the stage reveals it a chip at a
time; ruled 2026-09-26); the game master's vote line, which names the lynched seat's role, held
back on a lynch day until `lynch.truth` for the same reason; the day's brief in its Morning
(clamped, opens on a tap; public, so everyone's since 2026-09-29, when it was X-ray only); the ending); a
seated human's private results as dashed "Only you" lines; a wolf's pack chat with the red edge;
X-ray on adds, in the X-ray's verdigris (aqua until 2026-09-29): roles after names, passes with
reason and draft, the night acts, the pack's talk, everyone's private lines as "Only seat 4".
Chapters run down the drawer as rules; rules with nothing under them disappear. Filters:
days as tabs at the foot; seat chips at the head (dead dimmed, still selectable); Show › Public /
Private (ruled 2026-09-29: no X-ray toggle; the X-ray's lines follow the X-ray's one switch).
In the replay the drawer stops at the current beat.

As built 2026-09-25 (benches 74 and 52 where they give it; the rest no bench gives, change here
first). **The slot:** `Presentation.slot` is `'drawer' | 'film' | null` (null = closed; the film
exists only with the X-ray on, so `film` without it reads as closed); `src/stage/slot.ts` holds
the rules. **Ruled 2026-09-29, replacing bench 74's X-ray tab:** the strip's two tabs are
**File | Transcript** and only choose the pane: each brings its pane, or closes it if it is there;
File (the case file, below; the film until 2026-09-29) is greyed without the X-ray. The
X-ray is one switch, **Reveal**, on the strip just left of the tabs (ruled 2026-09-29; it was the
band's "X-ray on/off" button): its own small walnut plaque, a brass escutcheon with a keyhole riding
a dark slot, "Reveal" at the slot's left, "Revealed" slid right with the keyhole lit in verdigris
(`aria-pressed`, named "Reveal"; only the knob's transform and the light's opacity move). It re-cuts
the beats, adds the drawer's revealed lines and enables File; off with the file up, the pane falls
back to the transcript. Each tab reads pressed while its pane is open. Live: the switch is drawn
locked (disabled, keyhole dark, "Revealed after the game") until `game_over`, then on for good
(the game's end is the switch), and File reads "File · unlocked" until opened. With the slot
closed the strip's left row stops short of the switch and the tabs, so a count pill wraps under
the plaques rather than run under them (checked at 667×375 and 568×320). **A seat tapped for its
file (2026-09-29):** with the X-ray on, at a beat with no speaker (the vote and the count, the
lynch, the morning, the night hub and whole), every wing card is a button, a steady verdigris
edge (2.4 units; the thin muted one was missed, 2026-09-30) and the Reveal switch's keyhole, lit
verdigris on a small walnut disc, on the card's top-right corner, brighter under the pointer (no
breathing: only the night stop's actors breathe), and the no-seat sheet of the case file leads
with it (2026-09-30, it was one small line): the headline is the action, the keyhole and "Tap a
seat to open its file" in IM Fell, large, then every seat's face as a button that opens its
file (at the night stop "Visit a room" with the actors' faces comes first, §9); what the sheet
holds goes to a small typewriter footnote at its foot; the count's sheet, whose rows are every
voter already, keeps the one small line. A tap on the wing opens that seat's file in the pane at the playhead (the pane
switches to File from the transcript or closed); the pick holds like the chooser's. At a vote or
the lynch the file is what the voter voted on: its reads and its consult as they stood at the day's
first ballot (`ballotCut`), so Lessons reads "Consulted Day N · vote". The docket's vote rows and
night rows open a file too. A turn's wing keeps its read cards. The workbench writes the slot to its URL (`slot=drawer|film|none`, default none; `viewer=xray`,
landing on the same moment of the log in the re-cut beat list). While either is open every scene
lays its room out with `geometry(hud, true)`; the night rooms slide their painting left so its
window and its photo line stay in the narrower room. The replay's night and the ending now follow the slot, not the X-ray (this settles
§9's "to reconcile"), and the case file below replaces the stand-in panels §8 and §9 describe.
Nothing sits beside the epilogue: the ledger (the case's closing spread, in the file's paper
since 2026-09-30, §10) comes down over it all.
**The slot's width (2026-09-30):** on a screen wider than 16:9 the slot (the drawer and the case
file alike) grows out past the world's right edge into the bleed, as the rail does on the left:
by the bleed shown there, at most 118 units (the rail's reach for nine seats; `SLOT_REACH`,
`--slot-reach`), so on a phone the wing and the pane stand alike. Its left edge, and the room
beside it, never move; the strip's Reveal and tabs keep to its right edge (and the left row gains
that room when the slot is closed); on a 16:9 desk nothing changes. **The drawer:** 635 units wide (`slotW`, plus that reach), the whole height (its head 73.6 below the top, the top
strip's buttons over it), z under the strip's buttons and the epilogue's veil. It stops at the
rail on the prompts (`day.your-turn`, `vote.your-ballot`) and for the whole of the night rooms
(`room`, `pack`), whose chat and plate keep the band. On a phone (`data-small`) it runs full
height beside the car's prompts and the own room's plate, which stop short of it; only the
pack's chat, which spans the band's right, keeps it at the rail (`railHolds`, 2026-09-27). The lit line scrolls to 0.6 of the list's
height (bench 74); with no line of its own the drawer shows its end. It follows only while the
reader is at now (the lit line in view, or the end): scrolled away, new lines arrive without
moving it and a "↓ Back to now" pill sits at its foot until tapped or scrolled back (ruled
2026-09-29; the place and the follow outlive the scene, `useDrawerFilters().scroll`). The day's
brief is set as a labelled row per heading of `day_summary` (a small label over its words, the
accusations one per item); the headings that say only "None." fold into one quiet line ("No
accusations, claims or alliances yet"); a text without the four headings is set as it came. Wording: a pass reads the
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
second tap clears it), as bench 74. **The drawer's look (HUD pass 3a, ruled 2026-09-29, from the
owner's transcript mock; replaces bench 74's cards and the wording above where they differ):** a
warm dark ground under the HUD's brass edge; no card per entry, the entries set apart by space and
type. The chapters as headings: "Day 3" in Young Serif, large, "Discussion" small and muted beside
it; "Vote", "Morning 2", "Game over" and the night (a crescent before "Night 2", in a cool pale
blue-grey, never lavender: that is the serial killer's) smaller, each under a hairline. A speech:
a small head, "Seat 2" in brass-cream Young Serif, the words in Literata. A run of passes one after
another is one quiet italic line ("Seat 7 passed. Seat 9 held back."; `groupPasses`), each
held-back draft under it with "Seat 9 held back"; still X-ray only, in verdigris. The vote: a row per
seat voted for, most votes first and abstentions last ("Seat 6", the voters' faces as its marks,
about 24 css px on an iPhone 14, the count at the right; `voteTally`), then "Seats 1, 2, 5, 7, 8
and 9 voted for seat 6. Seat 6 voted for seat 7." (`voteSentence`). The game master's lines keep
their words but are set as short sentences, one per seat they name, each with the sigil of the
role it tells ("Seat 3 was stabbed by the serial killer last night. They were a wolf."), the dead
in terracotta; the heading the drawer already draws goes ("Night of day 2:", "Here's the vote
result for day 3:"), and so do the ballots when the day's votes line tells them (`reportParts`).
"Only you" lines and the pack keep an amber or red edge; X-ray lines their verdigris. The lit line: a
brass edge on a lamp's warmth. One column at every width (at the desktop's 530-odd css px two
columns would not hold a speech). The controls are the strip's plaque tabs: the seat filter's
"All" and Show in walnut with a thin brass edge, a pressed seat's head ringed in brass, the day
tabs a walnut plaque along the foot split by brass rules; pressed is the dark inset well, the
label in cream over a short brass underline. **The speech box (ruled 2026-09-29, the HUD's look):** a
walnut board with a thin brass edge and a still grain, the seat's nameplate (chip and "Seat n" in
Young Serif) on a brass-edged tab at its top-left corner, the words in Literata, lamp-glow cream.
A fixed size: three lines of a 30-em measure, the same count on every screen; paging replaces
overflow and ellipsis (§0), "1 / 2 ▼" at its foot while more follows, and a tap on the board
turns the page (the replay steps, live ends the page's hold). The transcript still holds the
whole line. **Beside the drawer** it narrows to the room with the same pages: at full size the
room holds the measure; on a phone the board keeps its height and sets the page in four lines of
22 ems, the words a step smaller (about 15 css px on an iPhone 14; replaces the 2026-09-28
"3 whole lines + ellipsis"). Under the film the box keeps the whole band (bench 74; benches 67
and 73 had narrowed it): a three-line board no longer rises past the rail on a phone. **The case file (ruled 2026-09-29, from the owner's case-file bench; replaces the X-ray film,
bench 74's blue-black sheet with its aqua ink and paper slips):** the `sideSlot` rectangle,
upright, a manila folder (`Film.tsx`; the data in `film/case-file.ts` and, for the docket,
`film/film-model.ts`). A seat's file: the cover (the seat's face, "Seat 2 ▾", "As of Day 3 ·
discussion", its role stamped on in the faction's ink) over divider tabs **Notes · Reads ·
Lessons · Findings** (the viewer's word for the agents' precedents since 2026-09-30; the code
keeps `precedents`). Notes: a typed page per `strategy_update` the seat wrote by the beat (the
view is folded at the beat, so the file holds only what exists there; a turn's own note lands at
the next beat), newest first opened, "Page 3 of 8", "Written Day 2 · vote", a pager with a page
glyph per note, and one pencil line in the margin: "first page", "rewritten from scratch" (under
half the previous page's words kept), `edited from p. 2, added: "…"` (the longest run added, at
most nine words), "edited from p. 2" (only cuts), "unchanged from p. 2". Reads: the seat's latest
`player_reads`, a row per seat read (face, seat, the guess or "unclear", sure / not sure, the why,
● ◐ ○ against the truth). Lessons (memory-on games; greyed until the seat's first consult):
"Lessons · advice from past games", its latest `memory_consulted`, "Consulted Day 3 ·
discussion", an index "No. 1 · Followed" with a verdict dot; the chosen one: the agent's why,
large, on a clipped card with the verdict stamped on it (Followed · Overrode · Doesn't apply,
for `follow` · `override` · `not_relevant`; 2026-09-30, they were Followed · Overruled · Not
applicable); "The lesson, from a past game" (dimmed when it doesn't apply); "Written for" (the situation's lead); a **Situation on file** form (Heat None · Low ·
Moderate · High · Max; Position Driving · With majority · Holding out; Information Starved ·
Rich), folded by default on a phone; the other facets one sentence each, "Show the full wording".
The situation is split at `compose_situation_embed`'s labels (and the older stores' Game phase,
Consensus texture, Agent exposure); none, it is shown whole. **A box is ticked only when the
facet's value, lower-cased with `_` as a space, starts with the box's word as a whole word and
names no other box of its row** (a range, "Moderate to high", is neither); otherwise the value's
short form (to its first `;` or `.`) is written in pencil and nothing is ticked (owner: a wrong
tick misstates what the agent believed). **From the record's fields (2026-09-30):** a memory
record on the wire now carries `dimensions` (server 18ebf3e: the store's structured situation,
verbatim; null for a legacy record). With them the file never parses the string: the lead is
`situation` and the facets are the named fields (Information `information_landscape`, Stakes
`criticality_stakes`, Consensus `consensus_text`, Position `my_position`, Heat `heat_now`,
Exposure `forward_exposure`, Targets `target_landscape`, Public vs private
`public_private_text`), in that order; Information is ticked from `info_landscape_class`
exactly (Starved · Rich), and the form gains an **Exposure** row, Safe · Exposed from
`exposure_class` exactly; Heat and Position keep the leading-word rule on their text (no class
for them); Consensus has its direction typed small under its words ("aligns with my read" ·
"opposes my read" · "no clear direction"); one quiet typed line gives the players alive (and
"a swing vote" when `is_swing`). Under each lesson's action and each finding, the record's tags
typed small, "defensive · honest" (`direction` · `honesty`); nothing without them. Without
`dimensions` (an old replay) the string is split at its labels as before, with no Exposure row.
The form's label column is 12 of the typewriter's characters, so "Information" never runs into
its boxes (it was 96 px × `--legible-ui`, which the labels outgrew on a phone); on a phone each
label sits above its boxes (and a facet's name above its words). Findings (memory-on games, after `game_over`): the
`memory_extracted` observations for the seat's role (served games extract observations only),
then any strategy points, "What this game taught serial killers: filed by role, not seat, so
from every serial killer seat"; an index of numbers grouped under the phase they came from, with
the ledger's phase icons ("Discussion 1 2 3 · Vote 4 5 · Night 6 7 8 9"; one row that wraps, no
third row of tabs), each number with its verdict's mark, ✓ positive · ✗ negative · ± mixed ·
? unclear (never colour alone; the epilogue ledger's rows carry the same marks), the chosen one
opened, "No. 6 · The night": its
situation (the lead under "The situation", the form folded), then on a card "What was done" (the
approach) and "How it turned out" (the outcome, its leading verdict word dropped) with
`net_verdict` stamped on it with its mark, Positive · Negative · Mixed · Unclear in calm inks
(`--ink-good` #3d6653, `--ink-bad` #8c3a2b, `--ink-mixed` #94650f amber, unclear grey); greyed
when there is none. Lessons keep their own words (Followed · Overrode · Doesn't apply). A tab a file lacks (memory off: no Lessons, no Findings) is not drawn; the open tab is the
container's, and a file without it opens Notes. **Whose file:** at a day turn the speaker's, at a
night spoke the actor's (the pack's: the first wolf's, "⇄ Seat 8" on the cover flips to the
other). **Choosing a file (2026-09-29, "Seat 5 ▾" read as a title):** where the slot is drawn at
least 424 css px wide (three-quarters of its full size), a tab per seat stands up off the
folder's top edge, its face and number, like a filing drawer's: the open file's raised, the dead
greyed but openable, the docket's own tab (a small folder glyph, no word) first at a beat that has one; narrower (a phone), the
cover's name is a bordered button, "Seat 5 · change ▾", opening a small card of every seat's face
(and the docket, by its title). Either opens that file at the playhead; **the pick holds until a beat brings a
different seat into focus** (another turn, another spoke), through the docket beats between
(`shownSeat`). **The docket** (the code's name; viewers never see the word since 2026-09-30: the
sheet is titled by what it holds, `docketTitle`, on its cover, its tab's name and the phone's
chooser: "The vote", "The lynch", "Day 2's brief", "The night", "The deal", "The case, closed",
"The winners' notes", "Nothing on file"; where a tap on the wing opens a file, its first line is
the keyhole and "Tap a seat to open its file"): the beats with no seat in focus, one sheet in the same paper: the
count (from the ballots' drop to the lynch's drop) "Inside the vote · Day N · what each voter
weighed", a dot per lesson (F · O · –: followed, overrode, doesn't apply); from the lynch's card to the card leaving "Who had them
right" and the seat's last note before the vote; the morning's brief "What day N taught · the
brief carried into day N+1" (Accusations, Claims, Blocs, Mood); the night whole; the deal face up
("The deal · every seat, face up"); at the truth and the curtain "The case, closed · the deal,
and how each seat went", its rows opening each seat's final file (live, after the game: "File ·
unlocked"; there the closed file, docket and each seat's, opens with "This is how each file
ended. To see what each seat was thinking turn by turn, watch the replay →", the curtain's
replay link; not in the replay); the winners' stand "The winners' last notes"; any other beat "Nothing on file
at this beat." The type: Literata for everything read (upright, never rotated), IM Fell English
for the titles and the cover's name, Courier Prime (the typewriter) for labels, tabs and stamps,
Patrick Hand for pencil. Only the stamps and the ticks sit crooked; the stamps' worn ink is a
still mask tile (`scripts/make-stamp-ink.mjs`), no live filter. On a phone the cover and the tabs
share one row when they fit, else the tabs wrap under the cover (the "As of" line and the tabs'
counts drop; the strip says where the playhead is; the role stamp shrinks); the tabs, the name's
chooser and the pager are set at the paper's label size (`--legible`) with a finger's height, and
the sheet scrolls in place.
**The reads on the wing:** every seat in the speaker's last `player_reads` before the line takes
the verdigris edge (blue until 2026-09-29; unclear reads too, as bench 74), a sure read the brighter ring, and breathes a slow
glow (opacity only, 2.4 s; still for reduced motion) while it can be tapped; a read new or changed
since the speaker's previous `player_reads` flashes once, brighter (`freshReads`). The card's head
says whose read on whom, face by face: "[chip] Seat 8's read on [chip] Seat 1" (ruled
2026-09-29); a tap opens the card, 304 wide, docked at the wing's edge level with the tile, kept on the stage; a second tap or
the next beat closes it. The truth is marked ● role · ◐ side · ○ none/wrong (bench 74 drew ✓ ◐ ✗).
The card is a small paper index card, a leaf of the speaker's case file (cream stock, a red rule
under its head, the labels typed, the truth in its faction's stamp ink; 2026-09-29, it was a film
print). **The X-ray's colour outside the file** (2026-09-29): a muted verdigris, old brass gone
green, in place of the film's aqua: `--xray` #86b0a0 (7.3:1 on the walnut), `--xray-hi` #b9d6c8
for a sure read's ring and the flash, `--xray-text` #cbdcd2, `--xray-mut` #6f978a, `--xray-line`
#34544a (materials.ts); the file itself is manila, never verdigris.

As built 2026-09-25, the container (step 6a; bench 73 draws only the five buttons and the seek
bar, the rest no bench gives, change here first). `src/stage/containers/ReplayTheatre.tsx` holds
the state (cursor, playing, speed, X-ray, slot, the drawer's filters, the film's tab); the presses
are one reducer (`replay-state.ts`) over `transport.ts` and `slot.ts`; each beat's fold is kept by
its `end` (`fold-cache.ts`), so a step forward folds only the new events. **The band:** bench 73's
buttons, 46.4 × 40 units, radius 11.2, 6.4 apart, 9.6 off the foot, from the wing's edge + 22.4;
its glyphs, and a pause of two bars (ours); play reads pressed, in amber, while playing. Then the
beat's label from `transportLabel` ("Day 3 · Speaks") over the seek bar (the "37 / 109" count
went 2026-09-29); the bar is bench 73's (6.4 tall, cloak, amber to the beat) with a tick per chapter (3.2 × 12.8,
bone3, bone once passed, its name on hover), beat i at i/(n−1) of the width; a click seeks to the
nearest beat, still. Speed: one toggle that says what it plays at, "Normal", or "Fast" in bone
(2026-09-29; it was "Normal · Fast · Skip"). The X-ray's switch left the band for the strip on
2026-09-29 (Reveal, above); the band keeps the transport only. Beside a full-height drawer the band ends 12.8
short of it; otherwise (the film, a prompt, the epilogue) 22.4 from the right edge. **Playing:** a
timer on `holdFor`; a beat that waits (the epilogue, the curtain) and the last beat stop the play;
play at the end starts from the first beat, play on a waiting beat steps on at once; stepping or
seeking while playing plays on from there. **The stops (2026-09-30, `containers/stops.ts`):** with
the X-ray on, the night hub (§9) and the ballots in (`vote.closes`, §3) pause the play however
the cursor got there (a tick, a step, a seek, a chapter jump), at either speed; play (the
notice's ▶) steps on from a stop at once, as from a beat that waits. The reducer also keeps the
visit (the room tapped at the hub or from another room, `day:actor`: its last step's tick
pauses the play there, 2026-09-30, it returned to the hub until then; the visit ends as soon as
the cursor leaves that room, or on play, which then goes on linearly) and the rooms seen (the
wing's "Seen" and steady marks); "End the
night" seeks to the first beat after the night whole and plays; "Back to the night" seeks to the
hub. A preview's loop has no stops. Nothing is persisted. The hold pauses while a pointer or a touch rests on a
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
`end`). **The way out (ruled 2026-09-29, replaces the small "Replays" link over the wing):** a
plaque of the day plaque's material and height just before it, "← Replays" to `/replays`, or
"← Home" to `/` when the viewer came from the landing (its links carry `?from=home`), there from
the first frame on the desktop and the phone (`SlotInput.back`, handed down by the replay's
container only; live, the workbench and the landing's carriage have none). It widens the strip's
row, so in the replay the count pill follows the plaques in their row instead of the room's
centre, and wraps under them where the room is too narrow (a phone with the slot open). A live
game's way out is the curtain's "Watch the replay" and "Back to the lobby" (§12).

## 12. Live pacing — H§6

Live has no transport. Beats animate as events arrive.

- **The dock and the clock never wait for the stage.** When `input_request` arrives for me, the
  dock opens at once and the countdown runs on real time from `deadline`; the beat on stage is
  cut short once (its hold ends now) and the beats queued between it and the request play at
  normal speed (ruled 2026-10-01; until then they drained at fast speed).
- **No backlog is hurried (ruled 2026-10-01).** Every queued beat plays at its normal hold,
  however many are waiting: a solo game's agents play at machine speed, so the stage plays at
  reading pace and lags the server, and that is the design. Until 2026-10-01 a backlog of three or
  more drained at fast speed (ruled 2026-09-28, was "more than one"; a speech told in pages
  counted as one item, ruled 2026-09-29), which in a solo game was nearly always. The live ballot
  drop is paced by `phase_progress`. A tap on the speech box ends the page's hold.
- **The deal always plays at normal speed (ruled 2026-09-28).** The game start lands as one burst
  (`game_started`, `role_assigned`, the day's `phase_change`); every beat now keeps normal speed,
  and the deal beat on stage is not cut short for my prompt (the dock still opens at once; a
  prompt first seen during the deal cuts nothing, 2026-10-01).
- **The deal after a departure (ruled 2026-10-01).** A page that watched its platform depart
  (§1a) lands on the deal's first beat when the curtain is down, whatever the history holds; the
  deal plays at normal speed from it, and the beats after it (history by seq, unseen by this
  viewer) play on at normal speed as a queue. A reconnect later catches up still, as anywhere.
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
- **Reveal and File follow the stage's end (ruled 2026-10-01).** `game_over` can land while the
  stage is still playing the last night's backlog. The X-ray is the viewer's (the Reveal switch
  on, the File tab open, the wing's truth, the strip's door gone) only once the stage is at or
  past the first `over.*` beat, never on the server's clock; and the live cut puts no X-ray or
  "Only seat n" beat before the ending, so nothing the X-ray knows plays in the night it catches
  up on.
- **The slot (ruled 2026-09-25):** when the drawer or the film is open, the room lays out for the
  open side slot (the `side` geometry in `units.ts`: the puppet slides left, the box narrows), in
  every scene, live and replay. The stand-in panels that overlaid the room are replaced by this.

As built 2026-09-25, the container (step 6b; bench 72 draws the speaking turn, the rest no bench
gives, change here first). `src/stage/containers/LiveTheatre.tsx` holds the state (the beat on
stage, the slot, the drawer's filters, the film's tab, the open turn); the rules are one pure
reducer (`live-state.ts`) over `live-queue.ts` and `transport.ts`. **History or news:** an event
is news iff the store marked its seq live; the log's head up to the first news is history, and
every beat whose `end` lies inside it lands still (the stage jumps to the last such beat, nothing
plays). News plays: a beat animates in and holds `holdFor(beat, 'normal')` (live never picks
fast since 2026-10-01), the timer steps on when it runs out; a beat with no hold waits (a prompt
while it is open, the epilogue until "Close the sheet", the curtain). The list is recut on every
event and on game over (X-ray on for everyone: `view.winner !== null`; what the viewer is shown
of it, `seesXray`, waits for the stage's first `over.*` beat, 2026-10-01); the stage is carried
by which beat it was on, then by seq. The live cut keeps the beats it played under the X-ray (no
`rnight.*`: the last night is not told again between the seat's own night and the morning; no X
or aqua beat before the ending, 2026-10-01); the seat's own pack line, the log's
copy of what it wrote at its prompt, lands still (an agent's line for it plays); closing the
epilogue's sheet lands on the curtain still (2026-09-30).
**The prompt:** open iff the status lists the seat (or the request is newer than the status),
this client has not answered it, its deadline has not passed, the seat is alive and the game is
not over. When first seen open further down the queue, the beat on stage is cut short once (a
deal beat is not, and then nothing is), and the rest play at normal speed (live-state's rule;
they drained fast until 2026-10-01). The clock runs on the request's `deadline` in server time
(`serverNow()`); its whole is arrival → deadline, or 120 s when the request came as history; a
draft's returned `deadline` replaces it. A request that runs out unanswered from here, or is
handed over, is the agent's: my `speech` answering it carries, on my screen only, the plaque's
tag "your seat's agent" (the agent red) and the box's "your seat's agent spoke for you" (amber).
**The dock** (`instruments/TurnDock.tsx`, bench 72's `.say2` placement; HUD pass 3b, 2026-09-29,
one flow): in the notice zone beside my card, full band (the drawer stops at the rail), on the
speech box's walnut board with its brass edge. Head "Your turn to speak" (Young Serif) · "Nothing
is said until you send it." (+ " If the clock runs out, your agent speaks for you." with a
deadline) and the count in red `m:ss` (none in solo). Then, top to foot: **1.** "Your agent"
(brass) and a Literata field, "Optional — steer or revise, e.g. push on seat 5 / softer, ask
seat 4 instead" (500 chars, Enter drafts when it holds something), **Draft** with the reply box
empty, **Redraft** once it holds a line ("Drafting…"; the seat's own agent writes the line it
would say, `{notes, current}`, the steer revising the box's line), "n drafts left", and, when
the seat notebook holds a note or a suspect, a small "Use my seat notes" tick (ticked to start;
ticked, the notebook goes with the draft, D25); **2.** the reply
textarea (64 units tall, "Type your line, or draft one above…", Ctrl/⌘+Enter sends) the draft
lands in, editable, and beside it **Send** (brass; "Sending…") over **Pass** (quiet walnut
plaques). No "Let my agent speak" on this turn (owner playtest: it sent the agent's line unseen);
the clock running out still has the agent speak. **The composer** (2026-09-30): a keyboard button at the dock's
head (and, on a frame 900 css px wide or narrower, a tap on the reply box, read-only there) opens
the same line over the whole stage, in css px and fitted to `visualViewport` so a soft keyboard
never hides the box or Send: the clock large, the steer with Draft and "n drafts left", a big box,
"n words" and "612 / 700", Pass and Send, the refused line's words; Close (the X, Esc, a tap
outside) keeps the line, the reply box is its preview, and it shuts when the turn closes. The server's words under the box in red. Draft errors: 409 → its words and no drafts left, 422 → its
words, anything else → "Could not draft the line; type it instead." (the notes kept); an empty
draft (the agent would pass) keeps the box's line: "Your agent would pass here. Pass, or tell it
what to say." Send
errors: 409 → "That turn was already answered." and the request is let go; 422 → its words. My
puppet stands thinking; the time left is on the dock (the car's wall clock is gone since
2026-09-29). A prompt that
is not the day's (the ballot, a night act, the pack) gets a pill under the top strip, "Let my agent
play this turn", its error beneath. **Counts:** `phase_progress` feeds the vote's jar and pill
at the opening ("Ballots in, n of N") and the night hub's "Acted n of N" (clamped to the census).
**The curtain:** "Watch the replay" → `/replays/{id}`, "Back
to the lobby" → `/rooms` (links). The drawer opens by default as the replay's. "Reconnecting…"
under the strip while the stream reconnects. **The deal on first connection:** a new game's
deal is over before the page connects, so while the history holds no `turn_started` it plays from
beat 0 at normal speed (as every beat does since 2026-10-01); after a departure on this page it
plays from beat 0 whatever the history holds (`historyLanding`'s `departed`, up to the status's
`last_seq` at connect); the history counts as all in once news has come after it or it
reaches the status's `last_seq` at connect, and until then the stage waits on "The table is being
seated…" rather than land. **The reconnect boundary:** from the moment the stream drops until a
fresh `GET /games/{id}` after it reopens, every event is catch-up, and after it anything up to
that status's `last_seq` (`hooks/catch-up-boundary.ts`); the store keeps the newest catch-up seq
that extended the log (`caughtUpTo`, not a late insert like the backlog after game over), and the
history runs to it, so the missed events land still. **Not built / to reconcile:** the live
ballot drop (§3 row 2) moves the count, not chips; "your seat's agent played 3 turns for you"
after a return (the client forgets across a reload); the draft helper in the pack's chat (the
pack's turn still has the "Let my agent play this turn" pill); a
reload during a vote already cast reopens the ballot (a second send gets the 409 line).

## 13. Viewers and tiers — H§7

| Viewer | Day | Vote | Lynch | Night | Morning | Game over |
|---|---|---|---|---|---|---|
| Spectator (P), and the replay with X-ray off | the theatre | the jar, the count | all of it | the lobby: chips, count | the report, chip by chip | the verdict, the winners, the truth, the epilogue |
| Seated human (S) | + my turn: my puppet, the box, the countdown, the draft | + my chip row and face-up chip | + "you are voted out", my card | my room on my turn; the lobby after | + what only I learn | + "you won" / "you lost" |
| Wolf (F) | as S | as S | as S | the pack's room, the chat, both teeth as they land | + the pack's note | as S |
| Replay, X-ray on (X) | + notes, reads | + the voters' consults; the ballots named at the drop | + who had them right | hub, spokes, whole; every act, consult, note | + all private results; the carried summary | + the deal and how it went |

## 14. Polish list (seen on the built scenes, not yet fixed)

None open (the 2026-09-25 list is fixed; each fix is an "As built" line in its section).

## 15. Open

- `firing_reason` and `addressed_targets` (deferred by decision; the fold already joins them).
- Motion inside the night rooms beyond the timings above.
- Whether a seat can be reclaimed after leaving (the server's call).
- The landing's miniature replay: which beats it plays (decided with the landing).
