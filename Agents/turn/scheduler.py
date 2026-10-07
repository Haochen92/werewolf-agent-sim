"""Sequential-discussion speaker selection — the pure core behind route_speaker.

Stateless: every decision is recomputed from the day_channel transcript, so it is
deterministic and unit-testable in isolation. select_next_speaker is the entry point: cap →
reactive obligations → terminate. Since Phase 2 (2026-10-07) the scheduler fires only the
reactive chains; players with nothing owed speak in the day's rounds (the opening, the
proactive round, the closing), which run in parallel outside this module. Kept free of
graph/LLM deps on purpose (test_scheduler.py).
"""

from collections import defaultdict

from Agents.game_config import GameConfig
from Agents.schemas import (
    Balance,
    DayChannel,
    Decision,
    DiscussionPassReason,
    FiringReason,
    ReactiveItem,
)


# Pass markers whose line was written but never shown (a round filter held it). Their tags stay
# on the marker for the closing's count, but they open and discharge nothing here.
_HELD_REASONS = {DiscussionPassReason.ROUND_ECHO, DiscussionPassReason.OPENING_FILTERED}


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
        # A proactive-round line held back as an echo was never shown: its tags count for the
        # closing (closing_speakers) but must not open a debt nobody can see the cause of.
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
    """Pick the next speaker (or terminate): reactive → terminate, with a drain once the cap hits.

    The reactive queue holds every player who owes someone an answer; the freshest debt
    speaks first and answers all its creditors at once. With nothing owed, the chains are over
    and the day router decides what comes next (another round, the closing, or the summary).

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
    return Decision(terminate=True, terminate_reason="no_obligations")


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
