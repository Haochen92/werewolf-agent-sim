# Scorecards and the role ledger (plan, 2026-09-28)

**Goal (the owner's):** make the game more fun and show off the eval pipeline. When a game
ends, every seat, human or agent, gets a score for its role. The site also publishes how each
role scores across all the archived games, filterable by model. There is no player
leaderboard (it would need accounts).

Status: planned, nothing built.

## The scores: one per role, from the eval's own ruler

Each score is a proxy from the validated basket (`evidence/metrics/report.md` §2), split down
to one seat. Every score is a count over a count ("3 of 4"), shown as the count rather than
as a rating.

| Role | Score | Numerator / denominator | Evidence |
|---|---|---|---|
| every town seat | **votes on a threat** | its votes on a wolf or the killer / its votes cast (abstains excluded) | `town_vote_accuracy`, +0.62 |
| healer | **saves** | nights its guard stopped an attack on a townmate / nights it guarded | `healer_town_save_rate` ★, +0.36 |
| investigator | **finds that reached the noose** | wolves it found that were later lynched / wolves it found | `investigator_find_to_lynch_rate` ★, +0.40 |
| vigilante | **shots on target** | shots on a wolf or the killer / shots fired | `vigilante_correct_shot_rate`: correct by the game's logic, but not win-validated (report §3) |
| wolf | **blended in** | its votes that went with the day's lynch / its votes on days with a lynch | `wolf_unconditioned_blending_rate` ★, +0.27 |
| serial killer | **kills** | kills landed / nights survived | `sk_kill_rate` ★, +0.26 |

- Every town power role also gets the town's "votes on a threat" line, so all town seats can
  be compared on one score.
- A score whose denominator is 0 is shown as a fact instead: "held fire", "found no wolf",
  "no lynch while alive".
- The figures after each proxy are the correlation with its side's win, from the 2026-07-02
  audit (N=180) or the 2026-06-11 check (n=50). The town's score is the only unambiguously
  validated one. The rest are epoch-local estimates, and the vigilante's has only its logic
  behind it. The ledger page says so in one line.

## Everything comes from the event log

Every input is already in the archived event log, so all 212 archived games get scores the
day this ships, with no game re-run:

- the deal: `roles_assigned`;
- votes: `vote_cast`, `lynch_result`;
- night targets: `night_action`;
- saves and deaths, with the attacker's type: `night_result`;
- finds: `investigation_result`;
- who is human: `GameRow.human_players`.

## Server: the shape, following the existing layers

The same split as the replay archive: a pure function over the log, a table, a service, a
route. Each file does one thing.

- **`server/game/scorecard.py`**: pure, no I/O. `score_seats(log) -> list[SeatScore]`, the
  way `derive_completion_metadata(log)` already turns a log into the completion summary.
  Unit-tested on the fixture game (`replay-9369a5c1.json`) and a few hand-built logs.
- **`server/schemas/scores.py`**: the wire shapes, `SeatScore` and `RoleStats`.
- **`server/database_models/seat_score.py`**: `SeatScoreRow`, one row per (game, seat):
  role, human or agent, won, the game's model and memory switch, and each score's numerator
  and denominator. One row per seat makes the ledger's filters a plain `GROUP BY`.
  Migration: `0007`.
- **Writing:** `GameRepository.complete_game` writes the rows in the same transaction that
  marks the game completed, just as it writes the completion metadata today.
- **Backfill:** `server/housekeeping/backfill_scores.py`, a one-off that scores every
  completed game from its stored log. It costs nothing, since no model is called.
- **Reading:**
  - `ReplayGame.scores` adds the seat lines to the existing replay endpoint.
  - `GET /stats/roles?model=&memory=` goes in `routes/stats.py`, backed by
    `storage/stats_service.py`, which mirrors `ReplayService`.
  - Rates are pooled (the sum of numerators over the sum of denominators), not averaged per
    game, so rare events like vigilante shots don't swing on a few games. That's the
    report's own rule for rare events.
- **One ruler:** a parity test checks that the seat scores, summed back up to the game,
  equal `Agents/compute_metrics.py`'s game-level values for the same game. That way the
  site's numbers and the eval's numbers can't drift apart.

## Frontend

- **Scorecard:** one line per seat on the game-over screen and on the replay page: chip,
  name, role, score as a count, and a mark for the seat that scored best on its side.
  - The game-over screen is the stage's (`GameOverScene`, the other agent's), so that part
    is a brief for them.
  - The replay page's copy is ours.
- **The role ledger:** a site page (Mantine, like the archive). Per role, the agents'
  pooled score and the humans' beside it, with N. Filters: model and memory. The ledger's
  title and route are still to be decided.
- **Landing:** card 3's second half (`landing_features.md`) switches on.

## Limitations (noted, parked)

- **Decisions an agent made for a human.** Drafts, "Let my agent play this turn" and AFK
  hand-overs aren't marked in the event log, so a human's score includes turns their agent
  took. Parked by the owner (2026-09-28) as a fairness note, not a blocker. If it's ever
  fixed, the fix is a `by_agent` flag on `vote_cast`, `night_action` and `speech`.
- **Split to one seat.** The proxies were validated per side, per game. Splitting them to a
  seat is the natural reading, but that split was never itself validated.
- **Epochs.** Prompts, models and the role set change the numbers. The ledger shows the
  model filter for that reason, and says the figures move as the game changes.
- **Few humans.** A human line with a small N is shown with its N. It is not hidden, and not
  presented as a verdict.

## Size (working sessions like the landing's)

| Piece | Size |
|---|---|
| `scorecard.py` + tests + parity test | ~1 |
| table, migration, write at completion, backfill | ~½ |
| replay DTO + stats route/service | ~½ |
| scorecard on the replay page (+ the brief for the game-over scene) | ~1 |
| the role ledger page, with filters | ~1 |
| **Total** | **~4** |
