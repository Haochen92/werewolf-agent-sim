/**
 * Reducer tests, against the REAL archived game — `seed-chunk-catalogue`, 593 events,
 * fetched verbatim from `GET /replays/{id}` (build_plan ruling 8: fixtures are real
 * archived-game JSON, not hand-written stubs).
 *
 * The fixture is a genuine served flash-lite game and covers 25 of the 27 durable event
 * types. The two it lacks cannot occur in it: `input_request` needs a human seat
 * (`n_humans: 0`) and `day_summary_structured` is never emitted by the engine at all. Both
 * are covered by synthetic cases at the bottom.
 *
 * Several assertions below encode facts about the wire that were VERIFIED against this data
 * rather than assumed — they are regression tests on the reducer AND a tripwire on the
 * server's event semantics.
 */
import { describe, expect, it } from 'vitest';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import { emptyGameView, foldEvent, foldEvents } from './foldEvents';
import type { PassSlot, SpeechSlot } from './types';
import fixture from './__fixtures__/seed-chunk-catalogue.json';

const replay = fixture as unknown as ReplayGame;
const events = replay.events as DurableGameEvent[];
const view = foldEvents(events);

describe('the fixture itself', () => {
  it('is the archived game we think it is', () => {
    expect(replay.game_id).toBe('seed-chunk-catalogue');
    expect(events).toHaveLength(593);
    expect(replay.winner).toBe('wolves');
    expect(replay.days).toBe(5);
    expect(replay.n_humans).toBe(0);
  });

  it('covers 25 of the 27 durable event types', () => {
    const present = new Set(events.map((e) => e.type));
    expect(present.size).toBe(25);
    expect(present.has('input_request')).toBe(false);
    expect(present.has('day_summary_structured')).toBe(false);
  });

  it('carries observer-tier content — the X-ray half is exercised, not stubbed', () => {
    const count = (t: string) => events.filter((e) => e.type === t).length;
    expect(count('strategy_update')).toBe(139);
    expect(count('firing_reason')).toBe(85);
    expect(count('addressed_targets')).toBe(64);
    expect(count('pass_marker')).toBe(18);
  });
});

describe('full-game fold', () => {
  it('seats the table from game_started', () => {
    expect(view.seats).toHaveLength(9);
    expect(view.castRoleCounts).toEqual({
      wolf: 2,
      healer: 1,
      villager: 3,
      vigilante: 1,
      investigator: 1,
      serial_killer: 1,
    });
  });

  it('lands on the winner and the final seq', () => {
    expect(view.winner).toBe('wolves');
    expect(view.lastSeq).toBe(593);
  });

  it('leaves nothing thinking at the end of a finished game', () => {
    expect(view.thinking).toBeNull();
  });

  it('drops nothing it was not told to drop', () => {
    expect(view.droppedEventTypes).toEqual([]);
  });

  it('ends with the roster the server last published', () => {
    // Final roster_update (seq 590) — two survivors, both on the winning side.
    expect(view.alive).toEqual(['player_8', 'player_9']);
    expect(view.packRoster).toEqual(['player_9']);
  });

  it('accounts for every death exactly once, with cause and revealed role', () => {
    expect(view.dead).toHaveLength(7);
    expect(view.alive.length + view.dead.length).toBe(view.seats.length);
    const byPlayer = Object.fromEntries(view.dead.map((d) => [d.player, d]));
    expect(byPlayer['player_5'].causes).toEqual(['wolves']);
    expect(byPlayer['player_6'].causes).toEqual(['wolves']);
    expect(byPlayer['player_6'].role).toBe('villager');
    // Every dead seat has a revealed role: deaths are role-revealing in both directions.
    expect(view.dead.every((d) => d.role !== null)).toBe(true);
  });
});

describe('day pagination', () => {
  it('produces exactly the five days the archive claims', () => {
    expect(
      Object.keys(view.days)
        .map(Number)
        .sort((a, b) => a - b),
    ).toEqual([1, 2, 3, 4, 5]);
  });

  it('keeps each day channel dense and in order — the annotation join depends on it', () => {
    for (const day of Object.values(view.days)) {
      const seqs = day.slots.map((s) => s.channelSeq);
      expect(seqs).toEqual([...seqs].sort((a, b) => a - b));
      expect(new Set(seqs).size).toBe(seqs.length);
      expect(seqs).toEqual(seqs.map((_, i) => i)); // dense: 0..n-1
    }
  });

  it('mixes speech, pass and GM into ONE per-day channel counter', () => {
    // Day 1 is the proof: three passes then two GM lines, slots 0..4, no speeches at all.
    const day1 = view.days[1];
    expect(day1.slots.map((s) => s.kind)).toEqual(['pass', 'pass', 'pass', 'gm', 'gm']);
    expect(day1.slots.filter((s) => s.kind === 'speech')).toHaveLength(0);
  });

  it('records only the phases a day actually entered', () => {
    // Day 1 never enters `voting` — it goes straight from day to night after three passes.
    expect(view.days[1].phases).toEqual(['day', 'night']);
    expect(view.days[2].phases).toEqual(['day', 'voting', 'night']);
  });

  it('builds the scrubber timeline from real phase changes (14, not 15)', () => {
    expect(view.timeline).toHaveLength(14);
    expect(view.timeline[0]).toEqual({ day: 1, phase: 'day', seq: 12 });
    expect(view.timeline.at(-1)).toEqual({ day: 5, phase: 'night', seq: 584 });
  });

  it('files each day_summary on the day that emitted it (the view renders it next morning)', () => {
    for (const day of [1, 2, 3, 4, 5]) {
      expect(view.days[day].summary).toBeTruthy();
    }
  });
});

describe('the vote block', () => {
  it('collects the batch and its result on the same day', () => {
    const day2 = view.days[2].vote;
    expect(day2.outcome).toBe('lynched');
    expect(day2.lynched).toBeTruthy();
    expect(day2.ballots.length).toBeGreaterThan(0);
    expect(Object.keys(day2.voteCounts).length).toBeGreaterThan(0);
  });

  it('handles a day that voted nobody out', () => {
    // Day 1: no ballots at all (everyone passed), outcome no_vote.
    expect(view.days[1].vote.outcome).toBe('no_vote');
    expect(view.days[1].vote.ballots).toHaveLength(0);
    expect(view.days[1].vote.lynched).toBeNull();
    // Day 3 tied.
    expect(view.days[3].vote.outcome).toBe('tie');
    expect(view.days[3].vote.lynched).toBeNull();
  });

  it('ballots reconcile with the tally the server computed', () => {
    for (const day of Object.values(view.days)) {
      if (day.vote.ballots.length === 0) continue;
      const derived: Record<string, number> = {};
      for (const b of day.vote.ballots) derived[b.votee] = (derived[b.votee] ?? 0) + 1;
      // The vote matrix (D16) is derived from ballots; it must agree with vote_counts.
      expect(derived).toEqual(day.vote.voteCounts);
    }
  });
});

describe('nights', () => {
  it('keys a night on its own day, not the following dawn', () => {
    expect(view.days[1].night?.day).toBe(1);
    expect(view.days[1].night?.resolved).toBe(true);
  });

  it('captures the wolf channel, the pack vote and the decision', () => {
    const night1 = view.days[1].night!;
    expect(night1.wolfChannel.length).toBeGreaterThan(0);
    expect(night1.wolfVotes.length).toBeGreaterThan(0);
    expect(night1.wolfKill).toBeTruthy();
    expect(night1.actions.length).toBeGreaterThan(0);
  });

  it('distinguishes a save from a quiet night from a kill', () => {
    expect(view.days[1].night!.deaths).toHaveLength(0);
    expect(view.days[1].night!.save?.player).toBe('player_1');
    expect(view.days[4].night!.deaths.map((d) => d.player)).toEqual([
      'player_1',
      'player_4',
    ]);
    expect(view.days[5].night!.save).toBeNull();
  });

  it('every night the game reached is resolved', () => {
    for (const day of [1, 2, 3, 4, 5]) {
      expect(view.days[day].night?.resolved).toBe(true);
    }
  });
});

describe('X-ray annotations', () => {
  it('reports observer data as available for a finished replay', () => {
    expect(view.xray.available).toBe(true);
  });

  it('knows every seat’s role', () => {
    expect(Object.keys(view.xray.roles).sort()).toEqual(view.seats.slice().sort());
  });

  it('joins every annotation onto a real slot — none orphaned', () => {
    let annotatedSlots = 0;
    let withFiring = 0;
    let withAddressed = 0;
    for (const day of Object.values(view.days)) {
      const slotSeqs = new Set(day.slots.map((s) => s.channelSeq));
      for (const [key, annotation] of Object.entries(day.annotations)) {
        expect(slotSeqs.has(Number(key))).toBe(true);
        annotatedSlots += 1;
        if (annotation.firing) withFiring += 1;
        if (annotation.addressed.length > 0) withAddressed += 1;
      }
    }
    // The 149 annotation EVENTS land on 85 distinct slots: every one of the 85 turns
    // carries a firing_reason, and 64 of them (the ones that produced speech) also carry
    // addressed_targets. Orphans would show up as a slotSeqs miss above.
    expect(annotatedSlots).toBe(85);
    expect(withFiring).toBe(85);
    expect(withAddressed).toBe(64);
  });

  it('annotates PASSES as well as speeches — the join is on the slot, not the speech', () => {
    let annotatedPasses = 0;
    for (const day of Object.values(view.days)) {
      for (const slot of day.slots) {
        if (slot.kind === 'pass' && day.annotations[slot.channelSeq]?.firing)
          annotatedPasses += 1;
      }
    }
    expect(annotatedPasses).toBe(18); // every pass in the game is annotated
  });

  it('preserves the vetoed speeches — the differentiator', () => {
    const gated = Object.values(view.days)
      .flatMap((d) => d.slots)
      .filter((s): s is PassSlot => s.kind === 'pass' && s.gated);
    expect(gated).toHaveLength(11);
    expect(gated.every((s) => s.passReason === 'novelty_gated')).toBe(true);
    expect(gated.every((s) => (s.gatedCandidate?.length ?? 0) > 0)).toBe(true);
  });

  it('builds a per-agent strategy timeline in emission order', () => {
    const total = Object.values(view.xray.agents).reduce(
      (n, a) => n + a.strategy.length,
      0,
    );
    expect(total).toBe(139);
    for (const agent of Object.values(view.xray.agents)) {
      const seqs = agent.strategy.map((s) => s.seq);
      expect(seqs).toEqual([...seqs].sort((a, b) => a - b));
    }
  });

  it('carries firing tier and owes onto the annotated slot', () => {
    const withFiring = Object.values(view.days)
      .flatMap((d) => Object.values(d.annotations))
      .filter((a) => a.firing);
    expect(withFiring).toHaveLength(85);
    expect(
      withFiring.every(
        (a) => a.firing!.tier === 'reactive' || a.firing!.tier === 'proactive',
      ),
    ).toBe(true);
  });
});

describe('turn markers', () => {
  it('resolves each turn_started into the slot it produced', () => {
    const markers = Object.values(view.days).flatMap((d) => d.turnMarkers);
    expect(markers).toHaveLength(85); // one per turn_started in the log
    expect(markers.every((m) => m.resolvedChannelSeq !== null)).toBe(true);
  });

  it('links the marker back to a slot by the same player', () => {
    for (const day of Object.values(view.days)) {
      for (const marker of day.turnMarkers) {
        const slot = day.slots.find((s) => s.channelSeq === marker.resolvedChannelSeq);
        expect(slot).toBeDefined();
        expect((slot as SpeechSlot | PassSlot).player).toBe(marker.player);
      }
    }
  });
});

describe('seat identity', () => {
  it('never guesses "me" from role_assigned — a replay deals every seat a card', () => {
    expect(view.me.seat).toBeNull();
    expect(view.me.role).toBeNull();
    expect(view.me.privateResults).toHaveLength(0);
    expect(Object.values(view.xray.privateResults).flat()).toHaveLength(4);
  });

  it('resolves the role card when the caller names a seat', () => {
    const seated = foldEvents(events, { mySeat: 'player_9' });
    expect(seated.me.seat).toBe('player_9');
    expect(seated.me.role).not.toBeNull();
    expect(seated.me.role!.role).toBe(view.xray.roles['player_9']);
  });

  it('files private results under their recipient and gives me only my own cards', () => {
    const vigilante = foldEvents(events, { mySeat: 'player_1' });
    expect(vigilante.me.privateResults).toHaveLength(3);
    expect(
      vigilante.me.privateResults.every((result) => result.player === 'player_1'),
    ).toBe(true);
    expect(view.xray.privateResults['player_3']).toHaveLength(1);
  });

  it('tracks whether my seat is still alive', () => {
    const survivor = foldEvents(events, { mySeat: 'player_9' });
    expect(survivor.me.alive).toBe(true);
    const casualty = foldEvents(events, { mySeat: 'player_6' });
    expect(casualty.me.alive).toBe(false);
  });

  it('keeps the vigilante’s bullet count current on the role card', () => {
    const bullets = events.filter((e) => e.type === 'bullets_remaining');
    const seat = (bullets[0] as { player: string }).player;
    const vig = foldEvents(events, { mySeat: seat });
    const last = bullets.at(-1) as { count: number };
    expect(vig.me.role!.bullets).toBe(last.count);
  });
});

describe('incremental folding equals whole-log folding', () => {
  it('gives an identical view whether folded at once or event by event', () => {
    const incremental = events.reduce((v, e) => foldEvent(v, e), emptyGameView());
    expect(incremental).toEqual(view);
  });

  it('changes day object identity when that day is written to — memoised views must re-render', () => {
    const upTo = (seq: number) => foldEvents(events.filter((e) => e.seq <= seq));
    const before = upTo(55); // day 2, before the first speech (seq 56)
    const after = upTo(56);
    expect(after.days[2]).not.toBe(before.days[2]);
    expect(after.days[1]).toEqual(before.days[1]);
  });

  it('is a pure function — folding does not mutate the input view', () => {
    const start = foldEvents(events.slice(0, 100));
    const snapshot = structuredClone(start);
    foldEvent(start, events[100]);
    expect(start).toEqual(snapshot);
  });
});

describe('partial and out-of-order logs', () => {
  it('folds a prefix without inventing anything', () => {
    const partial = foldEvents(events.filter((e) => e.seq <= 48));
    expect(partial.winner).toBeNull();
    expect(partial.days[2]).toBeUndefined();
    expect(partial.days[1].night!.resolved).toBe(true);
    expect(partial.lastSeq).toBe(48);
  });

  it('leaves a thinking marker when the log ends mid-turn (D12’s live tail)', () => {
    const midTurn = foldEvents(events.filter((e) => e.seq <= 55)); // turn_started, no slot yet
    expect(midTurn.thinking).toEqual({ seq: 55, day: 2, player: expect.any(String) });
  });

  it('survives a public-tier-only log — the live spectator is not a degraded case', () => {
    // D24: a live spectator receives the PUBLIC tier and nothing else — no observer
    // annotations, no faction wolf channel, no seat-private cards. The server withholds
    // them, so the reducer simply never sees them; this is the shape it must still fold.
    const PUBLIC_TIER = new Set([
      'game_started',
      'phase_change',
      'game_over',
      'turn_started',
      'speech',
      'day_summary',
      'vote_cast',
      'gm_message',
      'lynch_result',
      'roster_update',
      'night_result',
    ]);
    const live = foldEvents(events.filter((e) => PUBLIC_TIER.has(e.type)));
    expect(live.xray.available).toBe(false);
    expect(live.xray.roles).toEqual({});
    expect(live.xray.agents).toEqual({});
    expect(live.xray.privateResults).toEqual({});
    expect(live.winner).toBe('wolves');
    expect(live.alive).toEqual(['player_8', 'player_9']);
    expect(live.dead).toHaveLength(7); // public deaths are fully knowable
    expect(live.days[1].night!.wolfChannel).toHaveLength(0);
    // The transcript stays ORDERED but is no longer dense: the withheld passes leave gaps
    // in the channel counter. Nothing may assume 0..n-1 outside a full-tier replay.
    const day2 = live.days[2].slots.map((s) => s.channelSeq);
    expect(day2).toEqual([...day2].sort((a, b) => a - b));
    expect(day2.length).toBeLessThan(view.days[2].slots.length);
  });

  it('a seated wolf sees its own card but no observer role map', () => {
    // The faction/seat tiers a live wolf actually receives, plus public.
    const wolfSeat = 'player_9';
    const visible = events.filter(
      (e) =>
        ![
          'roles_assigned',
          'pass_marker',
          'firing_reason',
          'addressed_targets',
          'strategy_update',
          'night_action',
        ].includes(e.type) &&
        !(
          'player' in e &&
          typeof e.player === 'string' &&
          [
            'role_assigned',
            'investigation_result',
            'vigilante_confirmation',
            'bullets_remaining',
          ].includes(e.type) &&
          e.player !== wolfSeat
        ),
    );
    const wolf = foldEvents(visible, { mySeat: wolfSeat });
    expect(wolf.me.role!.role).toBe('wolf');
    expect(wolf.me.role!.pack).not.toBeNull();
    expect(wolf.xray.roles).toEqual({}); // own card is NOT observer knowledge
    expect(wolf.xray.available).toBe(false);
    expect(wolf.days[1].night!.wolfChannel.length).toBeGreaterThan(0); // faction tier arrives
    expect(wolf.days[5].night!.packRoster).toEqual(['player_9']);
  });

  it('R7 re-fold: replaying the full log over a public-only view reaches the same place', () => {
    // The post-game unlock is not a special case — the same fold absorbs the backlog.
    const full = foldEvents(events);
    expect(full.xray.available).toBe(true);
    expect(full.winner).toBe('wolves');
  });
});

describe('synthetic cases the fixture cannot contain', () => {
  const base = { seq: 900, day: 3 } as const;

  it('files a pending input_request for the dock', () => {
    const withInput = foldEvent(emptyGameView({ mySeat: 'player_1' }), {
      ...base,
      type: 'input_request',
      player: 'player_1',
      action_kind: 'vote',
      candidates: ['player_2', 'player_3'],
      deadline: '2026-08-21T10:00:00Z',
    } as DurableGameEvent);
    expect(withInput.me.pending).toEqual({
      seq: 900,
      day: 3,
      actionKind: 'vote',
      candidates: ['player_2', 'player_3'],
      deadline: '2026-08-21T10:00:00Z',
    });
  });

  it('records day_summary_structured as dropped rather than swallowing it', () => {
    const dropped = foldEvent(emptyGameView(), {
      ...base,
      type: 'day_summary_structured',
      data: {},
    } as unknown as DurableGameEvent);
    expect(dropped.droppedEventTypes).toEqual(['day_summary_structured']);
    // It still counts as observer-tier arrival.
    expect(dropped.xray.available).toBe(true);
  });

  it('handles an unresolved turn_started followed by another', () => {
    let v = emptyGameView();
    v = foldEvent(v, {
      seq: 1,
      day: 1,
      type: 'turn_started',
      player: 'a',
    } as DurableGameEvent);
    v = foldEvent(v, {
      seq: 2,
      day: 1,
      type: 'turn_started',
      player: 'b',
    } as DurableGameEvent);
    expect(v.thinking!.player).toBe('b');
    expect(v.days[1].turnMarkers).toEqual([
      { seq: 1, day: 1, player: 'a', resolvedChannelSeq: null },
    ]);
  });
});
