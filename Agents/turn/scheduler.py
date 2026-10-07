"""Sequential-discussion speaker selection — the pure core behind route_speaker.

Stateless: every decision is recomputed from the day_channel transcript, so it is
deterministic and unit-testable in isolation. select_next_speaker is the entry point:
reactive obligations → the proactive sweep → terminate, with the utterance cap's drain. The
reactive chains answer whoever is owed an answer, freshest debt first. When nobody is owed, the
sweep gives the floor to the survivors who have not spoken since the day began, one at a time
in seat order, each line's chains running before the next player is asked; a second sweep goes
round those silent since the first began, if the first produced a new line (Phase 2 step 4c,
2026-10-07: the sweep replaced the parallel proactive round, which replaced the old
quietest-first picks). The opening and the closing rounds run outside this module. Kept free
of graph/LLM deps on purpose (test_scheduler.py).
"""

from collections import defaultdict

from Agents.game_config import GameConfig
from Agents.rules.seats import seat_order
from Agents.schemas import (
    Balance,
    DayChannel,
    Decision,
    DiscussionPassReason,
    FiringReason,
    ReactiveItem,
)


# Pass markers whose line was written but never shown (the echo gate or a round filter held it).
# Their tags stay on the marker for records, but they open and discharge nothing here.
_HELD_REASONS = {
    DiscussionPassReason.NOVELTY_GATED,
    DiscussionPassReason.ROUND_ECHO,
    DiscussionPassReason.OPENING_FILTERED,
}


def build_reactive_queue(
    day_channel: list[DayChannel],
    per_pair_cap: int,
    reengagement_cooldown: int,
    valid_players: set[str] | None = None,
) -> list[ReactiveItem]:
    """Net out the open obligations from the transcript, grouped by debtor, freshest first.

    One pass builds a per-directed-pair ledger keyed (creditor, debtor); a `response`
    discharges the speaker's debt to its target, a `question`/`accusation` opens one.
    Freshness skips a re-open while already open; K-cap blocks the (K+1)th open within a
    burst; the cooldown resets the cap once a pair has sat untouched long enough.

    Targets not in valid_players (e.g. "all"/"everyone", or eliminated players) are ignored
    so they never become an obligation's debtor — only real survivors can be scheduled.
    """
    debt_ledger: defaultdict[tuple[str, str], Balance] = defaultdict(Balance)

    def close_open_debt(creditor: str, debtor: str, sequence: int) -> None:
        balance = debt_ledger[(creditor, debtor)]
        if balance.open_sequence is not None:
            balance.cycles += 1
            balance.open_sequence = None
            balance.last_touch_sequence = sequence

    for entry in day_channel:
        # A line held back as an echo was never shown: it must not open a debt nobody can see
        # the cause of (and, since 2026-10-07, it counts for nothing in the closing either).
        if entry.passed and entry.pass_reason in _HELD_REASONS:
            continue
        # A reactive model failure is an attempted turn, not speech. Close exactly the obligations
        # which caused the turn so an unavailable provider cannot re-fire the same debtor forever;
        # do this explicitly rather than fabricating AddressedTarget responses the agent never made.
        if (
            entry.passed
            and entry.pass_reason == DiscussionPassReason.GENERATION_FAILED
            and entry.firing_reason is not None
            and entry.firing_reason.tier == "reactive"
        ):
            for creditor in entry.firing_reason.owes:
                close_open_debt(creditor, entry.player, entry.seq)

        for target in entry.addressed_targets:
            # Skip non-player addressees ("all"/"everyone") and dead players: only a real
            # surviving player can owe/be-owed and therefore be scheduled.
            if valid_players is not None and target.target not in valid_players:
                continue
            # Close the speaker's own open debt to this target: ANY engagement of the
            # creditor discharges — response, mention, or question. A counter-question IS
            # engagement (it opens a fresh debt on the creditor below, so the exchange keeps
            # flowing); excluding it trapped debtors whose replies were tagged all-question
            # in a re-fire loop of near-duplicate turns (reactive turns bypass the novelty
            # gate), seen live 2026-07-26: three consecutive player_7 turns re-asserting
            # "you haven't answered", which the table then treated as evidence.
            close_open_debt(target.target, entry.player, entry.seq)

            # Open (or, if already open, leave alone) an obligation on the target.
            if target.addressed_form == "question" or target.stance == "accusation":
                balance = debt_ledger[(entry.player, target.target)]

                # Freshness: already open → no second obligation, just mark it touched.
                if balance.open_sequence is not None:
                    balance.last_touch_sequence = entry.seq
                    continue

                # Cooldown: a pair untouched for long enough re-earns its full K budget.
                last_touch = balance.last_touch_sequence or 0
                if entry.seq - last_touch >= reengagement_cooldown:
                    balance.cycles = 0
                # K-cap: refuse the (K+1)th open within the burst.
                if balance.cycles >= per_pair_cap:
                    continue

                balance.open_sequence = balance.last_touch_sequence = entry.seq

    # Group the still-open pairs by debtor; a multi-addressed agent answers all at once.
    reactive_items: dict[str, ReactiveItem] = {}
    for (creditor, debtor), balance in debt_ledger.items():
        if balance.open_sequence is None:
            continue
        item = reactive_items.get(debtor)
        if item is None:
            reactive_items[debtor] = ReactiveItem(
                agent_id=debtor,
                creditors=[creditor],
                opened=[balance.open_sequence],
                latest_sequence=balance.open_sequence,
            )
        else:
            item.creditors.append(creditor)
            item.opened.append(balance.open_sequence)
            item.latest_sequence = max(item.latest_sequence, balance.open_sequence)

    return sorted(reactive_items.values(), key=lambda i: i.latest_sequence, reverse=True)


def select_next_speaker(
    day_channel: list[DayChannel],
    surviving_players: list[str],
    game_config: GameConfig,
) -> Decision:
    """Pick the next speaker (or terminate): reactive → sweep → terminate, with a drain once the
    cap hits.

    The reactive queue holds every player who owes someone an answer; the freshest debt
    speaks first and answers all its creditors at once. With nothing owed, the sweep gives the
    floor to the next player who has not spoken (next_sweep_speaker); when the sweeps are done
    too, the day router decides what comes next (the closing or the summary).

    The utterance cap does not cut a chain mid-air (owner, 2026-10-07). Once the cap-th real
    utterance is in, the day DRAINS: only debts opened at or before that point are answered,
    each debtor answers at most once more (so a reply that fails to tag its creditor cannot
    re-fire forever), and anything a post-cap reply opens is left for the closing. The day
    ends with reason "cap" when nothing is left to drain.
    """
    cap = game_config.utterance_cap(len(surviving_players))
    real_utterances = [entry for entry in day_channel if not entry.passed]
    capped = len(real_utterances) >= cap
    cap_seq = real_utterances[cap - 1].seq if capped else None

    reactive_queue = build_reactive_queue(
        day_channel,
        per_pair_cap=game_config.per_pair_reengagement_cap,
        reengagement_cooldown=game_config.reengagement_cooldown(len(surviving_players)),
        valid_players=set(surviving_players),
    )
    if capped:
        reactive_queue = _drainable(reactive_queue, day_channel, cap_seq)

    if reactive_queue:
        top = reactive_queue[0]
        return Decision(
            speaker=top.agent_id,
            firing_reason=FiringReason(tier="reactive", owes=top.creditors),
        )

    if capped:
        return Decision(terminate=True, terminate_reason="cap")

    sweep_decision = next_sweep_speaker(day_channel, surviving_players, game_config.max_proactive_sweeps)
    if sweep_decision is not None:
        return sweep_decision
    return Decision(terminate=True, terminate_reason="no_obligations")


def next_sweep_speaker(
    day_channel: list[DayChannel], surviving_players: list[str], max_sweeps: int
) -> Decision | None:
    """The next player the proactive sweep gives the floor to, or None when the sweeps are done.

    Sweep 1 goes round the survivors with no spoken line today, in seat order (a player who
    spoke in the opening or answered a debt is not asked). It continues until everyone in it has
    had the floor once, chains included in between. Sweep 2 then goes round those silent since
    sweep 1 began, so a player who only spoke in the opening is asked once more, but only if
    sweep 1 produced a new line, and so on up to ``max_sweeps``. A player whose earlier sweep
    line was held by the echo gate is not asked again that day: they had the floor and repeated
    the table, and asked again they repeated themselves (owner, 2026-10-07, after the recaptured
    game). Which sweep is running, and where it began, is read back from the sweep marks on the
    proactive entries (FiringReason.sweep), so this stays stateless.
    """
    sweep_starts = _sweep_starts(day_channel)
    current_sweep = len(sweep_starts)

    if current_sweep >= 1:
        waiting = _players_to_sweep(day_channel, surviving_players, current_sweep, sweep_starts)
        if waiting:
            return Decision(
                speaker=waiting[0],
                firing_reason=FiringReason(tier="proactive", sweep=current_sweep),
            )

    if current_sweep >= max_sweeps:
        return None
    if current_sweep >= 1:
        previous_began = sweep_starts[current_sweep - 1]
        if not _anyone_spoke_since(day_channel, previous_began):
            return None
    next_sweep = current_sweep + 1
    waiting = _players_to_sweep(day_channel, surviving_players, next_sweep, sweep_starts)
    if not waiting:
        return None
    return Decision(
        speaker=waiting[0],
        firing_reason=FiringReason(tier="proactive", sweep=next_sweep),
    )


def _sweep_starts(day_channel: list[DayChannel]) -> list[int]:
    """The seq where each sweep began, sweep 1 first: the lowest seq among the proactive entries
    marked with that sweep."""
    first_seq_by_sweep: dict[int, int] = {}
    for entry in day_channel:
        firing = entry.firing_reason
        if firing is None or firing.tier != "proactive" or firing.sweep < 1:
            continue
        known = first_seq_by_sweep.get(firing.sweep)
        if known is None or entry.seq < known:
            first_seq_by_sweep[firing.sweep] = entry.seq
    starts: list[int] = []
    for sweep in sorted(first_seq_by_sweep):
        starts.append(first_seq_by_sweep[sweep])
    return starts


def _players_to_sweep(
    day_channel: list[DayChannel], surviving_players: list[str], sweep: int, sweep_starts: list[int]
) -> list[str]:
    """Who is still owed the floor in ``sweep``, in seat order: survivors with no spoken line
    since the previous sweep began (the day's start for sweep 1) who have not had a turn in this
    sweep yet (a pass or a held line is a turn), and whose line in an earlier sweep was not held
    by the echo gate."""
    if sweep == 1:
        since_seq = 0
    else:
        since_seq = sweep_starts[sweep - 2]

    spoke: set[str] = set()
    asked: set[str] = set()
    held_earlier: set[str] = set()
    for entry in day_channel:
        if entry.player == "game_master":
            continue
        if not entry.passed and entry.seq >= since_seq:
            spoke.add(entry.player)
        firing = entry.firing_reason
        if firing is None or firing.tier != "proactive":
            continue
        if firing.sweep == sweep:
            asked.add(entry.player)
        if firing.sweep < sweep and entry.passed and entry.gated:
            held_earlier.add(entry.player)

    waiting: list[str] = []
    for player in seat_order(surviving_players):
        if player in spoke or player in asked or player in held_earlier:
            continue
        waiting.append(player)
    return waiting


def _anyone_spoke_since(day_channel: list[DayChannel], since_seq: int) -> bool:
    """Whether any player's spoken line sits at or after ``since_seq``."""
    for entry in day_channel:
        if entry.player == "game_master":
            continue
        if not entry.passed and entry.seq >= since_seq:
            return True
    return False


def _drainable(
    reactive_queue: list[ReactiveItem], day_channel: list[DayChannel], cap_seq: int
) -> list[ReactiveItem]:
    """The part of the reactive queue the drain still answers: debts opened at or before the
    cap, owed by players who have not spoken since the cap was reached."""
    spoke_after_cap = {entry.player for entry in day_channel if entry.seq > cap_seq}

    drainable: list[ReactiveItem] = []
    for item in reactive_queue:
        if item.agent_id in spoke_after_cap:
            continue
        creditors: list[str] = []
        opened: list[int] = []
        for creditor, opened_at in zip(item.creditors, item.opened):
            if opened_at <= cap_seq:
                creditors.append(creditor)
                opened.append(opened_at)
        if creditors:
            drainable.append(ReactiveItem(
                agent_id=item.agent_id, creditors=creditors, opened=opened,
                latest_sequence=max(opened),
            ))
    return drainable
