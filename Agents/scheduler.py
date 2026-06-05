from collections import defaultdict
import random
import zlib

from Agents.game_config import GameConfig
from Agents.schemas import Balance, DayChannel, Decision, FiringReason, ReactiveItem


def cycle_seed(game_id: str, day: int, cycle: int) -> int:
    """Deterministic per-cycle seed for proactive ranking.

    Stable within a run (game_id is fixed); replayable across runs if game_id is pinned.
    Pure (primitives only) so it stays unit-testable with the rest of the scheduler.
    """
    return zlib.crc32(f"{game_id}:{day}:{cycle}".encode())

def build_reactive_queue(
    day_channel: list[DayChannel],
    per_pair_cap: int,
    reengagement_cooldown: int,
) -> list[ReactiveItem]:
    """Net out the open obligations from the transcript, grouped by debtor, freshest first.

    One pass builds a per-directed-pair ledger keyed (creditor, debtor); a `response`
    discharges the speaker's debt to its target, a `question`/`accusation` opens one.
    Freshness skips a re-open while already open; K-cap blocks the (K+1)th open within a
    burst; the cooldown resets the cap once a pair has sat untouched long enough.
    """
    debt_ledger: defaultdict[tuple[str, str], Balance] = defaultdict(Balance)

    for entry in day_channel:
        for target in entry.addressed_targets:
            # Close the speaker's own open debt to this target. (B) Any non-question
            # engagement of the creditor discharges -- a `mention` of who you owe counts,
            # not just a `response` -- so a correctly-aimed turn always clears the debt
            # even when the agent mislabels the form.
            if target.addressed_form in ("response", "mention"):
                balance = debt_ledger[(target.target, entry.player)]
                if balance.open_sequence is not None:
                    balance.cycles += 1
                    balance.open_sequence = None
                    balance.last_touch_sequence = entry.seq

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
                latest_sequence=balance.open_sequence,
            )
        else:
            item.creditors.append(creditor)
            item.latest_sequence = max(item.latest_sequence, balance.open_sequence)

    return sorted(reactive_items.values(), key=lambda i: i.latest_sequence, reverse=True)


def rank_proactive(
    day_channel: list[DayChannel],
    surviving_players: list[str],
    seed: int,
) -> list[str]:
    """Role-blind proactive ranking: quietest-first, seeded-random tiebreak.

    A pass marker advances its passer's recency (it's a real `DayChannel` entry), so the
    passer sinks to the bottom and the next pick auto-rotates. Never-spoke agents rank
    first (the opener is one big tie, broken by the seed).
    """
    last_spoke: dict[str, int] = {}
    for entry in day_channel:
        last_spoke[entry.player] = entry.seq

    candidates = list(surviving_players)
    random.Random(seed).shuffle(candidates)
    candidates.sort(key=lambda p: last_spoke.get(p, -1))
    return candidates


def select_next_speaker(
    day_channel: list[DayChannel],
    surviving_players: list[str],
    game_config: GameConfig,
    seed: int,
    *,
    utterance_cap: int | None = None,
) -> Decision:
    """Pick the next speaker (or terminate): cap → reactive → trailing-pass → proactive.

    utterance_cap overrides the config-derived cap (the caller uses this for the
    lighter pre-voting-day cap); falls back to game_config.utterance_cap otherwise.
    """
    num_survivors = len(surviving_players)
    proactive_budget = game_config.proactive_budget
    cap = utterance_cap if utterance_cap is not None else game_config.utterance_cap(num_survivors)

    # 1. Hard cap backstop — real utterances only; pass markers don't count.
    real_utterances = sum(1 for entry in day_channel if not entry.passed)
    if real_utterances >= cap:
        return Decision(terminate=True, terminate_reason="cap")

    # 2. Open obligations take priority — the obligated agent answers everyone owed.
    reactive_queue = build_reactive_queue(
        day_channel,
        per_pair_cap=game_config.per_pair_reengagement_cap,
        reengagement_cooldown=game_config.reengagement_cooldown(num_survivors),
    )
    if reactive_queue:
        top = reactive_queue[0]
        return Decision(
            speaker=top.agent_id,
            firing_reason=FiringReason(tier="reactive", owes=top.creditors),
        )

    # 3. Proactive path — terminate if the trailing P picks all declined.
    if len(day_channel) >= proactive_budget and all(
        entry.passed for entry in day_channel[-proactive_budget:]
    ):
        return Decision(terminate=True, terminate_reason="trailing_passes")

    ranked = rank_proactive(day_channel, surviving_players, seed)
    if not ranked:
        return Decision(terminate=True, terminate_reason="no_eligible")
    return Decision(speaker=ranked[0], firing_reason=FiringReason(tier="proactive"))


    
    
    