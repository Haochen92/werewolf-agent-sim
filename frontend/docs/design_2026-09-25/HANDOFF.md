# Werewolf Playhouse: design handoff

Status as of 2026-09-25, end of day. The visual redesign of wolf.liuhaochen.com, consolidated from the production log's revisions 62 to 75, the transcript decisions of revisions 9 to 52, and the code review of 2026-09-25. This is the document the codebase build starts from. Everything marked **Agreed** is locked; **Proposed** was built and reviewed but not locked; **Open** has not been designed.

The benches (the working HTML pages, one per scene) are listed at the end with their links. They are the record of how each decision was reached; this document is the record of what was decided. Pixel-level tuning (spacing, easing, exact timings) is done in the codebase against real components, not on the benches; where a bench falls short of the intent, this document states the intent.

Scope of this document: the live game, the replay theatre and the X-ray. The landing page and the rooms (lobby, create, join) are a separate piece of work that starts after this one, from a separate chat.

## 1. Principles

These came out of the work rather than going in, and every scene obeys them.

- **By day the theatre, by night your chair.** The day is a puppet theatre seen from the house: the dining car, the stand, one puppet speaking at a time; everyone, including the human, watches it in third person, and on your speaking turn your own puppet takes the stand. At night the acting seat is in its own room, seen from its own chair: no avatar, because you are the one sitting there.
- **Instruments, not props.** The trap (day) and the flies (night) do the work. The trap raises the ballots, takes the lynched player, gives back the role card. The flies lower the chips, the cards, the shutter and, at the end, the verdict. One apparatus, several acts, in one grammar.
- **The token rule.** Chips are the selection token everywhere: at the table by day (the vote), in the lobby by night (the waiting, the morning). Plush dolls appear only in the acting seat's own room. Your own puppet appears only when it is the show (your speaking turn, or you are among the winners at the end) and never at night.
- **Objects are sprites, surfaces are textures, the frame is vector.** Felt figures, dolls, kits and lamps are generated raster on transparent backgrounds. Wood is a seamless tile laid on vector geometry with a homography. The car, the stand, the trap, the shelf, the cards' frames, the sigils, the act marks, the verdict board and the clock's dial are vector: they are symbols and structure, not things.
- **Picture for the body, vector for what changes.** Anything that shows state (the clock's hand and counter, a seat numeral, a cap count, a mark) is drawn over the sprite, never baked into it.
- **The wire decides what is shown.** Every viewer sees exactly its tier: public, seat, faction, observer. Live views never leak who is awake, who voted for whom before the count, or an agent's private reads. The replay has two tiers and the X-ray toggle is the tier: **X-ray off is the public tier replayed** (the spectator's view of the same game); **X-ray on is the observer tier** (everything the log holds, including what the agents were working from). After `game_over` every viewer is an observer.
- **Nothing moves to say "chosen".** Selection is light: the chosen thing is lit and the rest dims. Moving or growing the chosen thing broke every layout it was tried in.
- **Arrive still, play moving.** Every scene renders any beat from state alone. Seeking to a beat renders it at rest; playing forward animates it. (§5.)
- **The dock and the clock never wait for the stage.** Live, a human's turn opens the moment its request arrives and its countdown runs on real time; the stage catches up. (§6.)
- **Tone.** Macabre-cute (Inscryption by way of Sea of Stars). Deaths are toys switched off, not tragedies; the "out" state is closed eyes and a flat mouth, never sad or frightened. The game does this nine times a match and the tone has to survive all nine. The ending is the same: the winners stand in base state, the losers are dimmed, nobody gloats.

## 2. The world

**The dining car** (day, and the night lobby). Walnut panels, a brass dado, a long rounded brass window on the country (day: hills and pines; dusk; night: moon and snow), a wall clock hung on its string at the left, an iron lantern at the right, the floor running to the frame's edge (the apron). The stand: a box below the rail with a plaque (seat, and a tag), the puppet's mount, over the trap; widened for two or three figures at the end of the game. The trap: a two-leaf door a tenth wider than the vote's table, a lift inside it. The shutter: a louvred wooden panel in three hinged sections that concertinas up into a walnut pelmet above the window; the pelmet and stacked shutter are part of the window at every hour; the shutter drops at "voting opens" and at the morning's report, and gathers up at "night falls", at "the day begins" and at the winner's hour. **Agreed** (62, 64, 66, 73).

**The acting seat's room** (night). A wall shelf across the upper half on three brass brackets, the generated walnut tile on its face. On it: the role card in a brass-edged frame at the left end (tap to read the full card as a centred overlay), the clock at centre, the role's kit at the right end. Below, eight brass hooks with short strings, one plush doll per living seat other than your own; the room below the shelf dims on a choice and one light finds the chosen doll; the shelf stays lit. The confirm is a brass plate at the bottom naming the act. Bare panelling behind; no window; no lamp. **Agreed** (70).

**The clock.** The carriage clock, vector, drawn after the generated one: an arched brass case, leather handle, columns, ball feet, a felt dial with a stitched ring and sixty ticks, no numerals, one red hand that sweeps once in two minutes with a red arc behind it for what is left, and a split-flap counter in the base. In the dining car the kit's wall clock carries the same red ring on a turn and advances from midnight toward dawn as night acts come in. **Agreed** (70, 67).

**The replay's frame.** The top drape only: the valance with its scalloped gold hem and the scalloped ply border along the top edge. No legs, no proscenium posts: the side curtains took the wing's and the film's room. Live has no frame. **Agreed** (73).

**The film.** The X-ray's material: the blue-black sheet with its grid, the cyan ink, the slip for the agents' notes. It is *this beat, inside*: the speaker's note (written after the turn), the lessons the agent weighed with its verdict on each (Note first, L1 to L3, an override as the bright tab). It lives in the side slot to the right of the stage on every scene, and comes down over the whole stage only once: the epilogue (§4.10). Reads are not in the film: they are on the wing, as a blue edge on every seat the speaker has a read on (a brighter ring for a sure read), and a tap opens the read card beside the seat with the guess, how sure, why, and the truth with a tick, a half-mark or a cross. The speech box carries X-ray's tags in aqua (who a speech answers and with what stance; the night-action tag in the replay's spokes); the plaque tags the role. **Agreed** (27 to 52, 74).

**The transcript.** A drawer on the right side of the frame under the top strip, full height; the puppet slides left for it and the speech box moves in under the puppet, narrower, a long line fading at its foot because the full line is the drawer's last entry; on your turn the drawer stops at the rail so the prompt keeps the full width. Open by default at 16:9, closed on the phone. The Transcript button is pinned at the far right of the top strip in live and replay alike, X-ray beside it. **The slot rule:** the right side holds one thing at a time, the drawer or the film; the two buttons are the switch (X-ray brings the film, Transcript brings the drawer) and the X-ray *state* stays on either way. Lines: the public record for everyone (speeches; the game master's verbatim lines, which are the record, with the sigils of the lynch and night atoms that follow them lent to them so nothing is said twice; the votes as one line per day at the count, the pairs as chips, abstain as the empty ring, because the vote is blind and `vote_cast` is a batch; the ending); a seated human's private results as dashed "Only you" lines that say what happened to your act and when and never what a seat might be (the whiff reads "survived": the human infers what the agent is told outright); a wolf's pack chat with the red edge and the kill decided; and with X-ray on, in aqua, the roles after the names, the passes with their reason and held-back draft, the night acts, the pack's talk, everyone's private lines as "Only seat 4", and the day's brief in its Morning, clamped, opening on a tap. Rules down the drawer are the chapters (§5). The line for the beat on stage is lit and scrolled to; in the replay the drawer stops at the current beat. **Filters:** days as tabs along the drawer's foot; at its head the seats as their chips (the dead dimmed, still selectable) and Show, three tier-named toggles all on by default: Public, Private, X-ray (a spectator has no row). Turning X-ray on resets Show › X-ray to on. Rules with nothing under them disappear; an empty result says so. `firing_reason` and `addressed_targets` are deferred. **Agreed** (9 to 11, 16 to 19, 36, 41, 42, 47, 74; the height question of 48 settled 2026-09-25).

**Orientation.** Landscape only. Request fullscreen and `screen.orientation.lock("landscape")` where the platform allows it (Android Chrome); where it does not (iOS Safari), a portrait interstitial ("turn your phone"). No portrait layout. **Agreed** (2026-09-25).

## 3. The cast and the assets

The cast is eleven characters keyed by name (cat, hare, owl, badger, cyclops, threeEyes, dragon, onion, whale, polarBear, shade); the kit's `castForGame(gameId)` maps seats to characters per game, and every seat numeral is drawn on in vector.

| Asset | Form | Count | Notes |
|---|---|---|---|
| Day figures | raster, 600 px tall in the module (full cuts ~900 px) | 11 × 4 states: base, talking, thinking, out | Two sheets per character, 1536×1024, two columns each; the base sheet is detected by the left figure's open eyes |
| Chips | raster, 200 px, cut from the base figure's head | 11 | Centred on the eye line; whale has a manual centre |
| Plush dolls (seated) | raster, ~450×620 | 11 | Third generation; no numerals; keyed by character |
| Kits | raster | 6 roles + clock + lamp | Healer, investigator, vigilante (popgun, caps, star, notice), serial killer (sickle, letter opener, X bottle), wolves (mask, bone, red hood), villager (tea, spoon, paper); the clock with a blank dial |
| Wood | seamless tile, 1024 | 1 | Walnut planks; on the vote's table via homography, on the shelf's face flat |
| Vector kits | code | stage kit, puppet kit (now fallback), role kit | The puppet kit is no longer drawn; the role kit's figures, sigils, cards and lines are still used |
| Act marks | vector | plaster, bite, knife, bullet, lens | Flat icons in the sigils' ink line |
| Verdict patches | vector | worked, cost, mixed, unclear | Stitched felt patches in the film, for the epilogue |
| Card back | vector | 1 | Paper, the stitched ring and the star; no faction colour anywhere on a face-down card, not even the edge bands |

The `cast.js` module (in `sprites/day/`) exposes `Cast.pup(g, character, seat, state, extra)` and `Cast.chip(character)`. Figures stand on one head-to-toe scale measured from each silhouette (ears, hats and antennae rise above). Plush hang by the same rule.

Generation preamble (for any future asset): handmade felt, visible stitching and patches, brass fittings, soft top-down warm light, matte, muted vintage palette, transparent background, no ground shadow, centred. For figures: "the figure fills the column's height, head within 3% of the top edge, feet within 3% of the bottom". Use toy wording (popgun, caps) to pass content filters.

## 4. The scenes

Each scene lists its beats in order, then who sees what. Events are from the wire's schema; seq numbers refer to game 9369a5c1 (memory on), the fixture used throughout.

### 4.0 The deal — Agreed for MVP (75)

The first scene of a match, on `game_started` and `role_assigned`. A hub for everyone; the tiers are layered on it.

- The table is seated: the dining car at dawn, the shutter up, the room empty; the nine chips come down from the flies as the seated table, in seat order.
- The cards are dealt: nine cards come down on the same strings, one under each chip, face down. The plate reads the cast counts (`cast_role_counts`). This is the public tier, and exactly what the table knows.
- Your card (seated): your own card comes down large and centred on its own string, face down, and turns face up: the morning's card grammar. The box says who you are and your night action; the vigilante counts two caps; the card button appears.
- Your pack (a wolf): the packmate's chip takes the red edge, its small card turns to the wolf, and the pack chat opens with the game master's line, which is the client's, from `role_assigned.pack`. The chat stays open for the night.
- The deal, face up (X-ray on): all nine small cards turn at once on `roles_assigned` and the wing takes its strips and badges; the film lists the deal. Without X-ray the replay sees the backs.
- The day begins: cards and chips go up, the paint goes to day, the stand returns with the first speaker.

The human never leaves the theatre for the deal. Nothing on the wire narrates it; every line is the client's. A boarding variant (the train at a station, each puppet rising into the stand as its chip and card come down, the train pulling out as the day begins) was built on the same bench and set aside for the deal; it is the picture for the rooms' waiting lobby, where seats fill one at a time.

### 4.1 Day discussion — Agreed (62, 72)

The base scene. Turns run in the log's order. Live, on `turn_started` the seat's puppet takes the stand in the thinking state with no clock, because that is what the agent is doing, until `speech` (the talking state, the line in the speech box) or the pass (idle, the box says "passes"; live, a pass is a turn with nothing said; `pass_marker` is observer tier).

Your speaking turn (72): your own puppet at the stand in the thinking state; the wall clock carries the two minutes; the box below is where you write, with Say it and Pass. Say it: the puppet talks your line as any turn plays; Pass: idle. Out of time: the seat's agent speaks for you, the puppet talks the agent's line, and the plaque's tag and the box say "your seat's agent spoke for you" on your screen only; the table sees a normal turn. This is the one timeout rule for every human turn (speak, vote, night act, wolf chat): the countdown runs on `input_request.deadline`; on expiry the seat's agent acts and only the seat is told. Agents have no client-side timer. A human who leaves is the same rule made permanent: the table sees nothing, every turn delegates; if they come back they arrive still, at their seat, with the plaque's tag on their own screen ("your seat's agent played 3 turns for you"). A room with several humans does not end when one leaves; whether a seat can be reclaimed is the server's call.

### 4.2 The day's summary — Agreed (64, 73; X-ray only)

`day_summary` is emitted between the last turn and the vote (seq 28, 79, 218, 360). It is the agents' compressed memory of the day: from day N+1 their prompts drop the raw transcript and keep only this, while the human scrolls back through the conversation. Public on the wire, hidden from the live client until X-ray unlocks. No live beat.

In the replay it is an X-ray-only beat placed by its **day number, not its log position**: day N's summary plays in Morning N, after the dawn results and before the first speech of day N+1, because that is when the agents first read it. It is a typed brief in the film: the accusations parsed into rows (accuser → accused, evidence type, defence), then claims, blocs, mood. The summary of a day on which the game ends at the lynch has no morning and was never consumed: it is dropped.

### 4.3 The vote — Agreed (64, 73)

- Voting opens: the puppet drops behind the stand, the stand goes; the car goes to dusk and the shutter drops; the trap's leaves open and stand; the table rises through the trap on its lift with the glass jar on it; the lid's string comes down and the lid lifts. One move, ~2.8 s.
- A ballot drops (live): one anonymous chip per `phase_progress` increment, from the flies into the jar; the count pill reads "Ballots in, n of N". The seated human chooses from a row of the candidates' chips in the prompt (the empty plate is abstain), taps one, confirms on the plate, and their chip drops in face up on their screen only; after that they have the spectator's jar.
- A ballot drops (replay): `phase_progress` is ephemeral and never in the log, so the replay has no pacing for the drop. The drop is **one beat**, the chips cascading together into the jar, and the count is the reading of a tally. Voting must not look like players voting one after another; the vote is blind and parallel.
- Voting closes: the lid comes down.
- The count begins: the lid flies out, the shot pushes in on the table, the jar tips onto its side at the back rail; plates along the front edge, one per seat with votes, abstain as an upturned saucer at the right; place cards on the cloth with head, seat and running number.
- A chip is counted: one per beat rolls from the jar's mouth, flips face up mid-air, lands on its plate; the card's number ticks; towers cap at four. The chip that settles the winner lands last.
- The result: the winner's plate and card lit; "Voted out, 3 to 2" or "The table abstains". A tie: the tied plates lit equally and the game master's line ("A tie: no one is voted out"), one held beat, then the abstain ending. `no_vote` (day 1 only): the vote scene is skipped entirely; the day goes straight to night falls.
- The table goes down: the lift lowers it with the count on it; the leaves stay open for a lynch. On an abstain day the leaves fold, the shot pulls back, the shutter gathers up on the night window: night.

### 4.4 The lynch — Agreed (65)

- The vote's end: the close shot, the open trap.
- The stand returns: the shot pulls back; the stand comes up from below the rail with the voted-out puppet, which rises into it from behind the playboard; the leaves stand either side of the box; the light collapses to one special.
- Named: a held beat; the plaque's tag reads "voted out".
- The drop: straight down through the trap, no fade; the plaque stays lit over an empty box.
- The card comes up: the lift raises the role card (name, sigil, figure, front line, faction colour); the wing's tile holds the live face until the card clears the rail, then flips to the sigil.
- The truth: a held beat.
- The card goes to the wing: the card flies up; the stand goes; the shutter gathers up on the night window; the leaves fold. Night. (If this lynch ends the game: §4.10 instead.)

The X-ray film here is "Who had them right": each voter's `player_reads` on the lynched seat against the truth (● role, ◐ side, ○ none/wrong), and the seat's last note. A human who is lynched sees "You are voted out" → "You were a villager" → "You stay at the table as a spectator", their card button reading "on the wing".

### 4.5 Night, the lobby — Agreed (67)

Everyone who is not acting is here for the whole night: the dining car, the shutter up, the living seats hung from the flies as chips in a row under the window (the table asleep), the count pill "Acted n of N" (from `phase_progress`, anonymous by design, padded, the pack as one) and the wall clock advancing toward dawn as acts come in. Nothing else on stage changes per act. The villager's night is this room. A seat that acts confirms in its own room and rejoins here with "Your act is in", its own mark the only one it sees.

### 4.6 Night, the acting seat — Agreed (70)

The shelf room (§2). Your turn: choose a doll (tap), the room below dims and the light finds it, the plate names the act ("Protect seat 1", "Check", "Shoot", "Kill", plus "Hold fire" for the vigilante), confirm. Roles: healer, investigator, vigilante, serial killer. The room's motion (the light finding the doll, the hand sweeping) is not built; timings follow the vote's.

### 4.7 Night, the pack — Agreed (71, 73)

The same room with the wolves' kit on the shelf and the packmate in the wolf chat, not on the shelf. Beats: the pack wakes (the chat empty, round 1 yours to open with a line and "Say it"); round 1; round 2 (the talk is in sequence, the chat keeps the order with the packmate's chip on their lines); the vote (live, faction tier: the plate is live at once, the packmate's tooth lands on their doll whenever their vote arrives, yours on confirm, the kill decided when the second tooth lands); decided. Night 3 is the lone wolf: no talk, one tooth, and at morning the game master's note in the chat that the kill failed and seat 2 is the serial killer. The seats the pack can choose exclude wolves. The wing marks pack seats with a red edge.

In the replay both teeth land together: the translator buffers `wolf_vote` and flushes it with `wolf_kill_decided`, so the log has no order between the ballots and the vote is shown as what it is, blind and parallel.

### 4.8 The morning — Agreed (67)

Told one chip at a time in an empty room, in the order the log delivers it. `gm_message` and `night_result` arrive together; private results follow them (seq 59, 271, 402), never precede them.

- The shutter comes down; the chips go up: the report plays in the night's paint.
- For each chip that had something done to it: comes down alone, at the centre, large ("Seat 3 was attacked in the night"); then either fell (the act mark appears beneath it: a bite, a knife, a bullet; the string gives way; the chip drops; once it has fully dropped the role card comes down large and centred, is read on the next beat, the wing's tile flips, and the card is drawn up out of the frame as the next beat begins) or saved (the wounds small and the plaster large beneath it, the ribbon on the string; the chip goes back up whole). A quiet night is the line alone.
- What only you learn, one beat after the report, on the seat's screen only: the investigator's target comes down and turns to its sigil, with the lens beneath (`investigation_result` names a role; that is the one private result that does); a wolf whose kill failed sees the target's chip come down whole with the line "Your kill on seat 2 failed. Seat 2 survived", no sigil; the vigilante whose shot whiffed (`vigilante_confirmation`) sees the same shape, "You shot seat 2. Seat 2 survived", no sigil, and counts its caps. The human infers what the agent is told outright; the game master's verbatim note, which names the role, is X-ray's. Every private result is also a dashed "Only you" line in the seat's transcript. The healer has nothing private. Spectators get nothing; the replay's film (X-ray on) lists all of it. Ruled 2026-09-25, superseding bench 67's sigil on the wolf's whiff.
- The carried summary (X-ray on): §4.2.
- The day begins: the shutter rises on the day's paint; the stand returns with the first speaker. (If this morning ends the game: §4.10 instead.)

### 4.9 The replay's night — Agreed (67, 73; linear)

A linear sequence, not a branching picker. The transport steps through it as beats like any other chapter, and the Night N chapter mark lands on the hub.

**X-ray off:** the hub (the lobby with its chips, the count and the clock), then Morning. The spectator's night, replayed; nothing on stage says who was awake.

**X-ray on:** the hub with the wing's lamps lit on every seat that acts tonight; then one spoke per **actor's branch**, the branches ordered by their last event, each a third-person view in the dining car (the actor's figure at the stand, the instrument on the rail, the mark landing on the row; the pack as two figures side by side, or one for the lone wolf, with its talk in the chat and both teeth landing together), the lamp going dark as the spoke ends; then "the night, whole": every mark on the row at once, the picture the parallel night never shows anyone live. The night branches run in parallel and their events interleave in the log; a spoke gathers its branch's events (the pack's first message is seq 122, its kill 154, with every other actor in between), so the pack's spoke always closes the night, which makes the right climax. Parallelism is stated by the hub, never by the staging. The film adds each actor's consult and note.

### 4.10 Game over and the epilogue — Agreed for MVP (73)

Follows the morning (§4.8) or the lynch (§4.4) in place of the next phase.

- Where it ended: the last scene's frame, held. After a morning: the night's paint behind the shutter, the room empty, the last card drawn up. After a lynch: dusk, the shutter down, the trap's leaves standing open, the card gone. The next phase does not begin.
- The shutter rises on the winner's hour: full day for the village, the night for the wolves, dusk for the serial killer (the leaves fold if open). The paint says who won before anything is read.
- The verdict comes down: the flies lower a walnut board on two strings, large and centred, in the morning's card grammar: the faction's colour at its edges, its sigil on a paper plate, "The wolves have won" in the card's serif, "Day 4 · at the morning" beneath. Read, then drawn up out of the frame as the next beat begins.
- The winners take the stand: the stand comes up from below the rail and the winning faction's **survivors** rise into it from behind the playboard, base state: one puppet at full size, two at 0.78, three at 0.6 with the box widened (×1.36, ×1.6); one special each; the plaque names the seats and, once the truth is out, their roles. The winners' tiles in the wing are lit and the rest dimmed. The winning faction's fallen are not brought back: they stay in the wing as sigils. The box reads "The wolves have won", the survivors' chips and "Seat 8 is the last of them standing"; a seated human's box adds "You won" or "You lost. You were the vigilante" (the client knows both from `role_assigned` and `game_over`; nothing on the wire says it).
- The truth is everyone's: `game_over` is thin by ruling (winner only) and flips every client to observer; `roles_assigned` leads the withheld backlog. Every living tile in the wing takes its faction strip and a sigil badge (the dead already wear theirs); the X-ray button reads "unlocked" for live viewers; the film lists the deal and how each seat went.
- What the game taught (memory-on games): the film comes down over the whole stage, one sheet. Down the left, one tab per perspective: the wire keys `memory_extracted.observations` by **role**, not seat, so a tab is a role, the chips of the seats that held it, and a tally of verdicts as pips. On the right, the rows grouped under the phase they came from (the discussion, the vote, the night), each **collapsed to its scenario alone**: a chevron, the label "Scenario", the situation clamped to two lines, an "open" tag; opened, the chevron turns and two blocks drop below at a larger size, "What it did" and "How it went", the verdict's stitched patch (worked, cost, mixed, unclear) sitting with "How it went" because a verdict is on the outcome, not the scenario. Along the bottom, the lessons kept (`strategy_points`) as slips: situation → action; an empty list is said plainly ("None from this game", the fixture's case). The epilogue is drawn in the film for every viewer, live and replay alike: the observations were private all game and are the X-ray's material, and after `game_over` the X-ray is everyone's.
- Curtain: the winners at the stand in the winner's hour, the result in the box with the way out (live: the replay, the lobby; replay: the transport at its end).

A seat that died earlier is a spectator here: its card button reads "on the wing" and its box says it was watching from the wing.

## 5. The replay's container — Agreed (73, code review 2026-09-25)

**Beats, not seconds.** The replay's unit of time is the beat. Every scene renders any beat from state alone (the roster, the marks, the wing), so seeking lands still and playing forward animates. The log's `seq` is the only clock; the replay never needs timestamps.

**Chapters.** A mark on the seek bar per chapter, from events that happened:

| Chapter | Anchored on | Notes |
|---|---|---|
| Day N | `phase_change: day` | the first speaker's turn follows |
| Vote N | `phase_change: voting` | absent on a day with no vote |
| Night N | `phase_change: night` | the hub; absent if the game ended at the lynch |
| Morning N | `night_result` | not a phase change: `night_result` is seq 156 and the next `phase_change: day` is 159, so anchoring on phase changes would put the dawn deaths at the end of Night. Holds the report, the private results and the carried summary (X-ray on) |
| Game over | `game_over` | §4.10; the epilogue is inside it |

**The transport.** Five buttons, as the benches draw them: previous chapter, back a beat, play/pause, forward a beat, next chapter. Chapter jumps land on the chapter's first beat, still. Arrow keys step beats. The beat's name sits next to the phase label in one short line ("A chip is counted", "Seat 3 comes down"), so a viewer arriving cold knows where they are. The seek bar is the whole log with the chapter marks on it.

**Waits.** Per-beat durations as the benches use them (the shutter ~3 s, a chip ~2 s, a card read ~2.6 s, the verdict ~3.2 s). Speech beats hold for reading time: 4 words per second, floor 4 s, cap 15 s (the fixture's 20 speeches run 21 to 59 words, median 38.5; a 12 s cap cut four of them). The wait holds while the pointer or a touch is on the speech. Wolf messages (20 to 36 words) follow the same rule.

**Speeds.** One control: normal; fast (waits halved, motion kept); skip (no motion, minimal waits). No scrubbing over seconds.

**The night.** §4.9: hub then Morning with X-ray off; hub, spokes grouped by actor's branch, whole, with X-ray on.

**The vote.** §4.3: the drop is one beat in the replay; the count is a tally being read.

**The slot.** The right side of the frame holds the drawer or the film, one at a time (§2); the container keeps both in step with the beat. The X-ray state is the tier (§1): switching it changes which beats exist (the summary, the spokes, the private results, the lynch's reads are X-ray-on beats), so the seek bar re-marks on toggle, and it resets the drawer's Show › X-ray filter to on.

## 6. Live pacing — Agreed (code review 2026-09-25)

Live has no transport. Beats animate as events arrive, and the risk is the stage falling behind the stream: a batch of nine counted ballots takes ~18 s to play at ~2 s a chip, and a human's `input_request` carries a real `deadline`.

- **The dock and the clock never wait for the stage.** When `input_request` arrives for the seated human, the dock opens at once and the countdown runs on real time from `deadline` (the live seat clock uses real time; "the client never needs timestamps" is a replay statement only). Beats queued between the stage and the request drain at fast speed so the stage catches up to the turn beat; the human is never made to wait for a count to finish.
- Anything queued more than one beat behind the stream drains at fast speed; the count and the morning are the beats that can fall behind. The live ballot drop cannot: it is paced by `phase_progress` in real time.
- On reconnect, history renders still at the latest state ("arrive still"); the backlog is not played.
- Solo games have no deadline (`deadline` null): the dock opens and the clock shows no ring.

## 7. Viewers and tiers, in one table

| Viewer | Day | Vote | Lynch | Night | Morning | Game over |
|---|---|---|---|---|---|---|
| Spectator (public), and the replay with X-ray off | the theatre | the jar, the count, the count on the table | all of it | the lobby: chips, count, clock | the report, chip by chip | the verdict, the winners, the truth, the epilogue |
| Seated human (seat) | + your turn: your puppet, the box, the clock | + your chip row and your face-up chip | + "you are voted out", your card | your room on your turn; the lobby after | + what only you learn | + "you won" / "you lost" |
| Wolf (faction) | as seated | as seated | as seated | the pack's room, the chat, both teeth as they land | + the pack's note | as seated |
| Replay with X-ray on (observer) | + notes, reads | + the voters' consults; the ballots named at the drop | + who had them right | hub, spokes, whole; every act, consult and note | + all private results; the carried summary | + the deal and how it went; the winners' last notes |

## 8. Stage kit changes to consolidate

The benches draw these over the frozen kit; the kit should absorb them:

- The trap widened to the vote table's width plus a tenth, with two leaves and a lift platform.
- The apron: floor to the frame's edge once the stand has gone.
- The shutter and pelmet as part of the window in every phase; a `shutter: closed` scene option.
- The vote's props (table, jar, lid, chips, plates, saucer, place cards), the act marks, the role card on the lift and on the string.
- The shelf room as a second scene (shelf, brackets, hooks, wood face, the framed card, the plate).
- The cast module replacing the puppet kit's drawing; the puppet kit kept only for `castForGame` and the chip crops' fallback. `Cast.pup` to take a horizontal offset and a scale (the benches wrap it to place two or three figures).
- The stand widened for two or three figures (a width factor on the box and its footlights).
- The verdict board on strings; the wing's "truth" state (strip and sigil badge on living tiles; lit and dimmed states).
- The ledger (the epilogue's sheet, tabs, rows, patches, slips) as the film's full-stage form.
- `dressing()` replaced by the top-only drape; the legs and posts removed.
- The camera moves: push-in for the count, pull-back for the lynch and the abstain ending.
- The drawer (the transcript's panel, its lines by kind, the day tabs, the seat chips, the Show toggles) and the read card on the wing.
- The dealt cards: the card back, the small card (sigil first), nine on strings under the chips; the station cloth as a window variant, kept for the rooms.
- Motion timings for the night rooms, as numbers in the kit rather than a bench.

## 9. For the codebase

Every scene of the live game and the replay has an agreed bench or an agreed rule. What remains is assembly, in the codebase against this document:

1. The replay theatre page: the container (§5) over the scenes, the top drape, the slot with the drawer and the film, reads on the wing, the epilogue.
2. The live game page: the scenes over the stream with the pacing rule (§6), the dock, the drawer, the rooms for the seated human and the pack.
3. Kit consolidation (§8) and the sprites into the build.
4. Phone proportions, which every bench leaves to the build.
5. Assets: the shade regenerated without its baked "3"; optional 2× upscale of anything shown large on retina.

Three decisions to settle before assembly, because they are expensive to retrofit (carried from the landing handoff): names or seat numbers (everything is built around numbers); the sprite canvas size (one number everything else scales from); whether the landing's miniature replay is the theatre component in reduced mode or a separate cut-down build.

Deferred by decision: `firing_reason` and `addressed_targets` in the film or the drawer; motion for the night rooms beyond timings in the kit.

Separate chat, after this: the landing page against the finished theatre, and the rooms (lobby, create, join), which take the boarding opening from bench 75 for the waiting lobby.

## 10. The benches

| Rev | Bench | File in this bundle | Link (needs a claude.ai login) |
|---|---|---|---|
| 63 | Vote, first pass (options) | (not in the bundle: superseded by 64) | https://claude.ai/artifact/8Vi4iZmjnxEuud2Ztwsyt3 |
| 64 | Vote as decided, chip row, the X-ray brief | benches/rev-64-vote.html | https://claude.ai/artifact/TEPg6bVys335Qy7ZmSHGSK |
| 65 | Lynch | benches/rev-65-lynch.html | https://claude.ai/artifact/KXDjdmHniAWf93v1y7Zb4n |
| 66 | The window's cover (shutter agreed) | benches/rev-66-shutter.html | https://claude.ai/artifact/5KMp2fVqi1XSkFbUEPDbB2 |
| 67 | Night lobby, replay hub and spokes, the morning | benches/rev-67-night-lobby-morning.html | https://claude.ai/artifact/WpAuQKWTihtVVdHrpzNBNT |
| 68 | The cabin (superseded by 70) | (not in the bundle: superseded by 70) | https://claude.ai/artifact/LdqzVkf5VFAyekrxyKchyh |
| 69 | The table (superseded by 70) | (not in the bundle: superseded by 70) | https://claude.ai/artifact/C6wztUiYPo85RnezLx4jEJ |
| 70 | The shelf room (agreed) | benches/rev-70-shelf-room.html | https://claude.ai/artifact/NekcJPhyMzHM3A4dGhA6ha |
| 71 | The pack | benches/rev-71-pack.html | https://claude.ai/artifact/2BLYiLNY7mEAYRffKhuJEu |
| 72 | Your speaking turn | benches/rev-72-your-turn.html | https://claude.ai/artifact/1TgXhqZbfiyR511ZuLhCyP |
| 73 | Game over, the epilogue, the top drape | benches/rev-73-game-over.html | https://claude.ai/artifact/8Nwgsb8YAfr5asxEW98Vdi |
| 74 | The transcript drawer, its filters, the film in the slot, reads on the wing | benches/rev-74-transcript.html | https://claude.ai/artifact/JG1bpNGUasSy4ukYG25Kjs |
| 75 | The deal (and the boarding variant, parked for the lobby) | benches/rev-75-deal.html | https://claude.ai/artifact/ABrQPVi55CA5jwJFg4Fep3 |
| 52 | The X-ray bench, locked (the film, the read card) | benches/rev-52-xray.html | https://claude.ai/artifact/DiTohJSQ1x9CGWXfVMxjxR |

Sprites are decoded as files under `sprites/` (day/<character>/{base,talking,thinking,out,chip}.png, plush/, kits/, wood/) with `sprites/manifest.json` carrying the sizes and the body measures; the kits are standalone under `kits/` (stage-kit.js, role-kit.js, puppet-kit.js, cast.js). Benches 73 to 75 are self-contained and carry the stage kit, the role kit, the cast module and the day sprites inline; 75 is the most recent copy of all four, and 74 carries the fixture's transcript as data.

## 11. This bundle

- `HANDOFF.md`: this document, the one the build starts from.
- `README.md`: how to use the bundle from the codebase.
- `benches/`: the working pages, self-contained HTML; open in a browser or render headless (Playwright) to compare against a build. `hud-blockout.html` (revision 7 to 11: the HUD's geometry and the transcript's placement) and `landing-prototype-v1.html` (the landing, for the next chat) are included for reference.
- `production-log-rev-62.html`: the log up to revision 62, the record of how every early decision was reached (the HUD, the transcript, the X-ray, the setting). Revisions 63 to 75 are recorded in the benches' own "How we got here" sections and in this document.
- `kits/`: the three vector kits and the cast module, as the benches froze them (§8 lists what the benches draw over them that the kit should absorb).
- `sprites/`: every raster asset, decoded; `manifest.json` has sizes and body measures.
- `reference-events-schema.py`: the wire contract the beats are built on. `landing-handoff-2026-09-22.md`: the landing's state, for the chat after this one.
