# Evil covers, replay screen: R11's card text (2026-10-18)

**Question (owner):** do the evil seats fake-claim, and intelligently? Ruling R11 (deduction
catalogue, `evidence/reasoning_failures/deduction_catalogue.md`): "denying is always going to get
lynched in this game". The evil cards lose "Unclaimed is a fine cover; do not invent a role until you
need one" and "or deny it", and gain a planned cover chosen from the roles the seat can claim. The
one exception the cards name is revealing the true role to bargain with a neutral, which is rare.

**Method.**
- Runner: `evaluation/experiments/evil_cover_screen.py`.
- Turns: the first discuss turn of each evil seat's day on which an earlier line accused it or
  claimed a sighting of its visit, while the seat had made no role claim.
  - Sources: the 16 persona voice games and the 4 silence calibration games, all with captured
    prompt inputs and deductions "full".
  - 41 turns: Serial Killer, Chanteuse, Illusionist, Necromancer.
- Arms, each replayed twice per turn (Haiku 5.5, thinking low; 164 calls, about $0.25):
  - `before`: the cards as they were, rebuilt word for word by swapping R11's text back;
  - `card`: R11's card text.

  The captured prompt input is the same in both arms, including the seat's deduction block. That
  block already lists the roles it can claim and a hidden body's role (slice 13).
- Judging: four blind Sonnet subagents saw each spoken line with the public record (the line-up,
  the dead, the earlier days' summary, today's discussion), not the arm or the speaker's role.
  Labels:
  - the answer: claims a role, denies, deflects, or reveals an evil role;
  - for a claim: whether it fits the public record, whether a living player already claims the role
    (contested), and whether a careful town player could show it false;
  - whether the line explains the accusation or the reported visit.

## Results

| | Before | Card (R11) |
|---|---|---|
| Spoken lines (of 82 samples) | 73 | 68 |
| Claims a role | 13 | **33** |
| Denies | 21 | **3** |
| Deflects | 38 | 32 |
| Claims that fit the public record | 12/13 | 33/33 |
| Claims of a role a living player already claims | 0/13 | 3/33 |
| Claims a careful town could show false | 1/13 | 0/33 |
| Lines that explain the accusation or visit | 29/73 | 42/68 |
| Answering a reported visit (28–33 lines): claims, of them explaining it, denials | 7, 7, 11 | 14, 13, 1 |

Roles claimed under the card: investigator 9, healer 7, sigilist 6, sentinel, vigilante and
speculator 3 each, trailseer and fortune teller 1 each.

## Reading

1. **The card text alone does most of it.** Claims rise from 13 to 33 and denials fall from 21 to 3,
   and every claim fits the public record. The facts were already in the deduction block (slice 13);
   what changed is the permission. Examples:
   - an Illusionist whose visit a sentinel saw: "I'm the healer. Last night I protected player_5,
     which is why they were saved, so that's the visit your watch saw";
   - a Serial Killer followed to the dead Illusionist: "I'm the Investigator; I checked them and got
     Suspicious";
   - a Chanteuse watched at player_7: "I'm the sigilist, and I put a sigil on them, which had no
     effect since they didn't attack anyone".
2. **Deflection is still the commonest answer** (32 of 68). It is not denial: the seat turns the
   question back or asks for evidence. Some of it is fair play on a weak accusation.
3. **What the judges cannot see:** a claim can contradict the very sighting it answers, which the
   public record alone does not show. A trailseer says it followed the Serial Killer to player_8,
   and the killer answers "I'm the healer. Night 1 I protected player_6, so I was never at player_8's
   door", turning a fit into word against word. This is what slice 14's night stories (the claims
   that fit the seat's real visits and the reported sightings) are for: arm 3.

**Limits.**
- The seat's note, carried in the captured input, was written under the old card and still says
  "stay low-profile" in places. In a real game under the new card the notes would plan a cover, so
  this probably understates the change.
- Two samples per turn, 41 turns, one judge per line.
- "Fits" is judged from the public record only.

# Step 2: slice 14's covers line (2026-10-18)

**Method.**
- The same 41 turns, two new arms, each replayed twice. Both use R11's card and re-render both
  deduction blocks with the checked-out engine from the turn's rebuilt payload (the block census's
  rebuild; without covers it reproduced all 41 captured seat blocks exactly):
  - `card_now`: covers off;
  - `covers`: covers on (a line on 27 of the 41 turns).
- All four arms' lines were pooled and judged blind again by eight Sonnet subagents (`v2_*`), with
  one new label: `contradicts_sighting`, whether the claimed night conflicts with a visit by the
  speaker that another player reported.
- 164 calls, about $0.25.

# Step 3: the covers line fixed (2026-10-18)

Step 2's covers arm had 4 claims a careful town could catch, where `card_now` had none. Three were
the same flaw: an Investigator story on a player later revealed as a wolf, offered with no reading,
and the seat said "Not suspicious". The fourth was a Sentinel story on the pack's victim, whose watch
would have seen the killer.

The fixes:
- a check of a revealed role carries its reading ("you checked player_5 on night 2, who read
  Suspicious");
- no Sentinel story on a player attacked that night.

`covers2` was rerun (82 calls) and judged blind by four more subagents (`v3_*`).

| | before | card | card_now | covers | covers2 |
|---|---|---|---|---|---|
| Spoken lines | 73 | 68 | 68 | 69 | 72 |
| Claims a role | 13 | 33 | 36 | 38 | **44** |
| Denies | 19 | 3 | 4 | 2 | **0** |
| Claims that fit the public record | 12/13 | 32/33 | 36/36 | 34/38 | 41/44 |
| Claims a careful town could show false | 1/13 | 1/33 | 0/36 | 4/38 | 3/44 |
| Claims contradicting a reported sighting | 1/13 | 3/33 | 4/36 | 2/38 | **1/44** |
| Lines that explain the accusation or visit | 19/73 | 35/68 | 35/68 | 38/69 | 42/72 |

(The before and card arms' step-1 labels are in `verdicts_*`; this table uses the pooled `v2_*`
labels for the first four arms and `v3_*` for covers2.)

## Reading

1. **With covers the seats claim more and contradict sightings less:** 44 claims against 36, and 1
   contradicting a reported sighting against 4.
2. **The 3 catchable claims under covers2 are the seats departing from the line,** not the line
   being wrong:
   - an Illusionist told a different night-3 follow from the one listed;
   - a Serial Killer, offered only a counter-claimed Trailseer story, twice claimed "I'm the
     Vigilante, I shot player_8", though player_8 died to the Serial Killer and no shot was
     announced.

   The line now ends "No other town role you can claim has a story that fits these nights." when
   some do not (not replayed).
3. **Limits.**
   - Different judges labelled step 1, step 2 and covers2.
   - Small cells: 3 or 4 claims a careful town could catch, out of about 40.
   - The notes in the captured inputs were written under the old card.

   Whole games are the next measure.
