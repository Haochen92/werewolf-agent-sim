# Music brief: the missing cues

For the agent composing the remaining music for *The Ninth Express*. The game is played by AI
agents (and people) aboard a night express train in the 1920s–30s: a dining car of brass and dark
wood. By day the passengers argue about who among them is a killer and vote someone out. By night
the killers strike. Each of the game's stages has its own music, which the site plays as the
stage changes. Most cues exist already; this brief asks for the ones still missing.

## The existing score (match it)

Key and tempo are estimated from the audio; treat them as a guide. Loudness is the RMS of the
mono mix over the whole file, in dBFS.

| Cue | File | Length | Type | Key (est.) | Tempo (est.) | RMS |
|---|---|---|---|---|---|---|
| Lobby | bossa_lobby | 60.0 s | loop | D minor | ~65 bpm | −20.1 |
| Lobby | groove_lobby | 76.8 s | loop | F major | ~99 bpm | −20.0 |
| Lobby | original_lobby | 68.6 s | loop | F major | ~112 bpm | −20.1 |
| Lobby | elders_council_discussion | 87.3 s | loop | D minor | ~96 bpm | −20.7 |
| Discussion | masked_accusations_discussion | 72.0 s | loop | E minor | ~81 bpm | −20.5 |
| Discussion | parlour_suspicion_discussion | 85.3 s | loop | D minor | ~91 bpm | −19.9 |
| Vote | day_C_whodunit_lounge | 40.0 s | loop | D minor | ~96 bpm | −20.6 |
| Lynch | lynch_5_psalm | 19.6 s | one-shot | G minor | — | −23.7 |
| Lynch | sting_death | 4.6 s | one-shot | E minor | — | −21.7 |
| Morning | dawn_3_suspense | 17.0 s | one-shot | G minor | ~72 bpm | −24.4 |
| Night | night_1_original_creep | 45.7 s | loop | E minor | ~85 bpm | −23.0 |
| Night | night_6_hide_and_seek | 45.7 s | loop | E minor | ~85 bpm | −23.2 |

Most of the score centres on **D minor and F major**. New pieces should sit in that family
unless a cue below names another key.

## What to make

### 1. Victory stings (four, the priority)

When a game ends, the screen rises on a different hour for each winner. A short sting plays as
it rises; then the ending music (a lobby loop) comes in underneath and carries on until the
player leaves.

| Winner | Hour on screen | Character |
|---|---|---|
| The town | day | Warm and resolved: relief after a long hunt. Major key (F major), a full cadence. |
| The wolves (a pack of two killers) | night | Dark and certain: the hunters won. Minor (D minor), low strings or brass. |
| The lone killer (a Serial Killer or a Necromancer) | dusk | Unsettling and solitary: one figure walks away. D minor with a flattened second or a tritone; one solo voice (music box, solo violin, celesta). |
| A draw (nobody won) | grey dawn | Unresolved and empty: it ends on a suspended or open chord, without a cadence. |

- **Length:** 5–8 s in all, tail included.
- **Shape:** the sound starts within the first 10 ms, with no leading silence; the site starts the
  file on the exact moment the hour rises. The main statement is in the first 1–2 s, it resolves
  by about 5 s, and the tail decays to silence by the end of the file.
- **Hand-over:** the ending loop fades in under the sting from about 4 s. End on a chord of D
  minor or F major so the loop doesn't clash (except the draw, which stays open).
- **Loudness:** RMS −20 to −22 dBFS; the town's and the wolves' may peak a little hotter than the
  rest of the score. Peak at most −1 dBFS.
- 2–3 candidates for each winner are welcome.

### 2. A morning bed (loop, to follow dawn)

The morning scene, where the night's deaths are read out, lasts 23–40 s. `dawn_3_suspense` is a
single rise and fall (peak at about 7 s, silent by 17 s), so it can't loop. Make a quiet loop
that can play straight after it until the day begins.

- **Key and tempo:** G minor, about 72 bpm (dawn's own), and the same instruments as dawn.
- **Length:** 20–40 s per cycle, seamless (see the loop rules below).
- **Character:** suspense held low; the screen is reading names. RMS about −26 dBFS, quieter than
  the other loops.
- An alternative is a longer dawn: one 40 s piece that rises like `dawn_3` and then settles into a
  low held section, ending at low level.

### 3. Optional

- **The deal** (the game opening: every player is dealt a role card; about 18 s): a one-shot of
  15–18 s, anticipation, in the lobby's key. Without it, the lobby music carries on through the
  deal.
- **A second vote candidate:** a 35–45 s loop, D minor, tension rising toward the count.

## Technical rules (all files)

- **Deliver MP3**, as the existing tracks are: 44.1 kHz stereo, 192 kbps, encoded with LAME (or
  ffmpeg's libmp3lame), which writes the header that lets a player skip the encoder's padding.
  The site plays these files as they are; nothing is re-encoded.
- **Loops must be seamless at the sample.** The last sample flows into the first; the length is a
  whole number of bars; no fade-in, no fade-out, no silence at either end. Reverb and
  delay tails that run past the end must already be wrapped into the start. Render two cycles and
  keep the second, so the tail of the end is already sounding at the start.
- **One-shots:** sound within the first 10 ms; the tail decays to true silence by the end, and
  0.3–1 s of silence at the end is fine.
- **No clipping:** peak at most −1 dBFS.
- **No vocals or lyrics, no quotation of a recognisable melody, no third-party samples.**
- **Names:** lowercase, underscores, no spaces: `<cue>_<winner or descriptor>_<n>.wav`, for
  example `win_town_1.wav`, `win_wolves_2.wav`, `morning_bed_1.wav`.
- **Keep the source:** for every file, keep the code or prompt that made it, so a piece can be
  revised later. Don't put it in the same folder as the audio: that folder is served to the public
  as it is.

## How each piece is placed (for reference)

Times are the scene's holds at normal speed in a real game; a replay on Fast halves them.

| Scene | Beats | Music |
|---|---|---|
| Lynch (24 s) | the stand returns 6 s · voted out 2 s · the drop 2 s · the card comes up 4 s · the truth 4 s · the card goes to the wing 6 s | the psalm from the scene's start, its hit at 15.3 s landing on "the truth"; the 4.6 s sting on "voted out" on Fast |
| Morning (23–40 s) | the shutter 6 s · each death 2.5–4 s · the roll 8–12 s · the day begins 6 s | dawn from the start, then the morning bed |
| Ending (30 s, then the curtain stays up) | where it ended 8 s · the winners' hour 6 s · the verdict 6 s · the winners stand 6 s · the truth 4 s · the curtain | the winner's sting on "the winners' hour", then the ending loop through the curtain |
