'use client';

import { useMemo, useState } from 'react';
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { getReplay } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { foldEvents } from '@/game/foldEvents';
import type { DurableGameEvent } from '@/types/contracts';

/**
 * WALKING SKELETON — the whole point of this file is to close the loop
 * fetch → fold → render end-to-end, with zero design, before a single real component
 * exists. Every piece of markup here is scaffolding to be replaced by the §9 component
 * inventory; what must survive is the data path it proves.
 *
 * The fold happens ONCE for the whole log and the day switcher merely selects a page out
 * of the result — it is not a re-fold. That is what keeps `?day=` cheap and is why
 * `xray.available` is true from the first render of a finished game.
 */
export function TheaterClient({ gameId }: { gameId: string }) {
  const [day, setDay] = useState(1);
  const [xray, setXray] = useState(false);

  const { data, isPending, error } = useQuery({
    queryKey: queryKeys.replays.detail(gameId),
    queryFn: () => getReplay(gameId),
    staleTime: Infinity, // a finished replay never changes
  });

  const view = useMemo(
    () => (data ? foldEvents(data.events as DurableGameEvent[]) : null),
    [data],
  );

  if (isPending) return <p>Loading replay…</p>;
  if (error) return <p role="alert">Could not load replay: {error.message}</p>;
  if (!view) return null;

  const dayNumbers = Object.keys(view.days)
    .map(Number)
    .sort((a, b) => a - b);
  const page = view.days[day];

  return (
    <div>
      <p>
        <Link href="/replays">← replays</Link>
      </p>
      <h1>{gameId}</h1>
      <p>
        <strong>{view.winner}</strong> won · {dayNumbers.length} days · {view.seats.length}{' '}
        seats · {view.lastSeq} events
      </p>
      <p>
        alive at the end: {view.alive.join(', ') || '—'}
        <br />
        dead:{' '}
        {view.dead.map((d) => `${d.player} (${d.role}, ${d.causes.join('+')})`).join(' · ')}
      </p>

      <p>
        {dayNumbers.map((n) => (
          <button
            key={n}
            onClick={() => setDay(n)}
            disabled={n === day}
            style={{ marginRight: 6 }}
          >
            Day {n}
          </button>
        ))}
      </p>

      <label>
        <input
          type="checkbox"
          checked={xray}
          onChange={(e) => setXray(e.target.checked)}
          disabled={!view.xray.available}
        />{' '}
        X-ray {view.xray.available ? '' : '(no observer data in this log)'}
      </label>

      {!page ? (
        <p>No day {day}.</p>
      ) : (
        <>
          <h2>
            Day {page.day} · phases: {page.phases.join(' → ')}
          </h2>

          {page.summary && xray ? (
            <p>
              <em>summary emitted this day (renders next morning): {page.summary}</em>
            </p>
          ) : null}

          <h3>Transcript</h3>
          <ol>
            {page.slots.map((slot) => {
              const annotation = page.annotations[slot.channelSeq];
              if (slot.kind === 'gm') {
                return (
                  <li key={slot.seq}>
                    <em>GM: {slot.text}</em>
                  </li>
                );
              }
              if (slot.kind === 'pass') {
                if (!xray) return null; // observer tier; hidden with the toggle off
                return (
                  <li key={slot.seq}>
                    <strong>{slot.player}</strong> passed ({slot.passReason ?? 'no reason'})
                    {slot.gated && slot.gatedCandidate ? (
                      <blockquote>
                        <small>vetoed by the novelty gate — would have said:</small>
                        <br />
                        {slot.gatedCandidate}
                      </blockquote>
                    ) : null}
                    {xray && annotation?.firing ? (
                      <small>
                        {' '}
                        [fired {annotation.firing.tier}
                        {annotation.firing.owes.length
                          ? `, owes ${annotation.firing.owes.join(', ')}`
                          : ''}
                        ]
                      </small>
                    ) : null}
                  </li>
                );
              }
              return (
                <li key={slot.seq}>
                  <strong>{slot.player}</strong>
                  {xray && view.xray.roles[slot.player]
                    ? ` (${view.xray.roles[slot.player]})`
                    : ''}
                  : {slot.message}
                  {xray && annotation?.firing ? (
                    <small>
                      {' '}
                      [fired {annotation.firing.tier}
                      {annotation.firing.owes.length
                        ? `, owes ${annotation.firing.owes.join(', ')}`
                        : ''}
                      ]
                    </small>
                  ) : null}
                  {xray && annotation?.addressed.length ? (
                    <small>
                      {' '}
                      [addresses{' '}
                      {annotation.addressed
                        .map((t) => `${t.target}:${t.stance}/${t.addressed_form}`)
                        .join(', ')}
                      ]
                    </small>
                  ) : null}
                </li>
              );
            })}
          </ol>

          <h3>Vote</h3>
          {page.vote.outcome === null ? (
            <p>no vote recorded</p>
          ) : (
            <p>
              outcome: <strong>{page.vote.outcome}</strong>
              {page.vote.lynched
                ? ` — ${page.vote.lynched} (${page.vote.lynchedRole})`
                : ''}
              <br />
              ballots:{' '}
              {page.vote.ballots.map((b) => `${b.voter}→${b.votee}`).join(', ') || '—'}
            </p>
          )}

          <h3>Night {page.day}</h3>
          {!page.night ? (
            <p>no night</p>
          ) : (
            <div>
              <p>
                {page.night.deaths.length
                  ? `died: ${page.night.deaths
                      .map((d) => `${d.player} (${d.role}, ${d.attacker_types.join('+')})`)
                      .join(', ')}`
                  : 'a quiet night'}
                {page.night.save ? ` · saved: ${page.night.save.player}` : ''}
              </p>
              {xray ? (
                <>
                  <p>wolf kill decided: {page.night.wolfKill ?? '—'}</p>
                  <ul>
                    {page.night.wolfChannel.map((w) => (
                      <li key={w.seq}>
                        <strong>{w.wolf}</strong> (round {w.round}): {w.message}
                      </li>
                    ))}
                  </ul>
                  <p>
                    night actions:{' '}
                    {page.night.actions
                      .map((a) => `${a.actor}/${a.role}→${a.target}`)
                      .join(', ') || '—'}
                  </p>
                </>
              ) : null}
            </div>
          )}
        </>
      )}
    </div>
  );
}
