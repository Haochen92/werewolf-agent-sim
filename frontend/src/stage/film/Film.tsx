'use client';

/**
 * The X-ray film: the side slot's other occupant, beside the transcript drawer. It holds
 * *this beat, inside*: what the agents were working from at the moment on stage, which live
 * nobody sees (handoff §2 "The film"). The material is the locked one of bench 52 as bench 74
 * redrew it: a blue-black sheet with a faint grid, cyan ink, and the agent's own note on a
 * paper slip taped on, in a handwriting face.
 *
 * At a turn (and an actor's night act) there are tabs: Note first, in the slip's paper, then
 * one per lesson the agent weighed (L1 to L3) in aqua; a lesson it overrode wears the slip's
 * paper too, with a dot, because an override is the agent's own word. The open tab is held by
 * whoever mounts the stage, so it stays put as the viewer steps through the turns.
 *
 * The film stops above the rail: nothing in it repeats the speech, so the box below keeps the
 * whole band. What each beat holds is worked out in film-model.ts; this only draws it.
 */
import type { ReactNode } from 'react';
import type { Character } from '@/assets/manifest';
import type { GameView } from '@/game/types';
import type { SceneBeat } from '../beats/types';
import { ChipSprite } from '../cast/ChipSprite';
import { Sigil } from '../instruments/Sigil';
import { ACT_VERB } from '../drawer/drawer-lines';
import { ROLE_ARTICLE } from '../paint/role-kit';
import { ROLE_NAME, factionOf, seatNumber, seatify } from '../roles';
import { sideSlot, type Hud } from '../units';
import {
  MARK,
  filmFor,
  type FilmLesson,
  type FilmModel,
  type FilmNote,
} from './film-model';
import styles from './Film.module.css';

const VERDICT: Record<string, string> = {
  follow: 'follows',
  override: 'overrides',
  not_relevant: 'not relevant',
};
const PIP: Record<string, string> = { follow: 'F', override: 'O', not_relevant: '–' };

export interface FilmProps {
  view: GameView;
  beat: SceneBeat;
  hud: Hud;
  cast: readonly Character[];
  /** The view a little past the beat, for the note a turn writes just after it. */
  ahead?: GameView | null;
  /** `note`, or a lesson `L1`–`L3`; a tab the beat does not have falls back to the note. */
  tab?: string;
  onTab?: (tab: string) => void;
}

export function Film({ view, beat, hud, cast, ahead, tab = 'note', onTab }: FilmProps) {
  const model = filmFor(view, beat, ahead);
  if (!model) return null;
  const r = sideSlot(hud);
  return (
    <aside
      className={styles.film}
      style={{ left: r.x, top: r.y, width: r.w, height: r.h }}
      data-film={model.kind}
      aria-label="X-ray film"
    >
      <FilmBody model={model} cast={cast} tab={tab} onTab={onTab} />
    </aside>
  );
}

function FilmBody({
  model,
  cast,
  tab,
  onTab,
}: {
  model: FilmModel;
  cast: readonly Character[];
  tab: string;
  onTab?: (tab: string) => void;
}) {
  const chip = (seat: string, sm = false) => {
    const c = cast[seatNumber(seat) - 1];
    return (
      <span className={sm ? `${styles.chip} ${styles.sm}` : styles.chip}>
        {c ? <ChipSprite character={c} /> : null}
      </span>
    );
  };
  const role = (r: string | null) =>
    r ? <i>{(ROLE_NAME[r] ?? r).toLowerCase()}</i> : null;

  switch (model.kind) {
    case 'inside':
      return <Inside model={model} tab={tab} onTab={onTab} />;

    case 'pack':
      return (
        <>
          <header className={styles.head}>
            <strong>Inside the pack</strong>
            <span>the wolves’ notes</span>
          </header>
          <div className={`${styles.list} ${styles.slips}`}>
            {model.notes.map(({ seat, note }) => (
              <div key={seat}>
                <header>
                  Seat {seatNumber(seat)} <i>wolf</i>
                </header>
                <Slip small note={note} empty="No note tonight." />
              </div>
            ))}
          </div>
          <div className={styles.why}>
            {model.lines
              ? `${model.lines} line${model.lines === 1 ? '' : 's'} of talk, then the vote.`
              : 'A pack of one: no talk, one tooth.'}
          </div>
        </>
      );

    case 'night':
      return (
        <>
          <header className={styles.head}>
            <strong>The night, inside</strong>
            <span>what each did</span>
          </header>
          <div className={styles.list}>
            {model.rows.map((b) => (
              <div key={b.actor} className={styles.row}>
                <span>
                  {b.seats.map((s) => (
                    <span key={s}>{chip(s)}</span>
                  ))}
                </span>
                <span className={styles.nm}>
                  {b.actor === 'pack' ? (
                    <>
                      The pack{' '}
                      <i>{b.seats.map((s) => `seat ${seatNumber(s)}`).join(' and ')}</i>
                    </>
                  ) : (
                    <>
                      Seat {seatNumber(b.actor)} {role(b.role)}
                    </>
                  )}
                </span>
                <span className={styles.pair}>
                  {b.target ? (
                    <>
                      {ACT_VERB[b.role] ?? 'acts on'} {chip(b.target, true)}
                    </>
                  ) : (
                    'holds'
                  )}
                </span>
              </div>
            ))}
          </div>
          <div className={styles.why}>
            In the order the log finished them. Live, nobody sees any of this.
          </div>
        </>
      );

    case 'vote':
      return (
        <>
          <header className={styles.head}>
            <strong>Inside the vote</strong>
            <span>what each voter weighed, day {model.day}</span>
          </header>
          <div className={styles.list}>
            {model.rows.map((v) => (
              <div key={v.voter} className={styles.row}>
                {chip(v.voter)}
                <span className={styles.nm}>
                  Seat {seatNumber(v.voter)} {role(v.role)}
                  <small>
                    {v.votee === 'abstain'
                      ? 'abstains'
                      : `votes seat ${seatNumber(v.votee)}`}
                  </small>
                </span>
                <span className={styles.vd} aria-label="the lessons it weighed">
                  {v.verdicts.length ? (
                    v.verdicts.map((x, i) => (
                      <span key={i} className={x ? styles[x] : undefined} title={x ?? ''}>
                        {x ? PIP[x] : '·'}
                      </span>
                    ))
                  ) : (
                    <small>no lessons</small>
                  )}
                </span>
              </div>
            ))}
          </div>
          <div className={styles.why}>
            The lessons each voter weighed before its ballot, L1 to L3: <b>F</b> followed,{' '}
            <b>O</b> overrode, – not relevant.
          </div>
        </>
      );

    case 'lynch': {
      const n = seatNumber(model.seat);
      const had = model.rows;
      return (
        <>
          <header className={styles.head}>
            <strong>Who had them right</strong>
            <span>
              seat {n} was {ROLE_ARTICLE[model.role] ?? model.role}
            </span>
          </header>
          <div className={styles.list}>
            {had.map((r) => (
              <div key={r.voter} className={`${styles.row} ${styles.rd}`}>
                {chip(r.voter)}
                <span className={styles.nm}>
                  Seat {seatNumber(r.voter)} {role(r.role)}
                  {r.why ? <small>{seatify(r.why)}</small> : null}
                </span>
                <span className={styles.sus}>
                  {r.suspected ? (ROLE_NAME[r.suspected] ?? 'Unclear') : 'No read'}
                  {r.confidence ? (
                    <small>{r.confidence === 'high' ? 'sure' : 'not sure'}</small>
                  ) : null}
                </span>
                <span
                  className={`${styles.mk} ${styles[`m-${r.mark}`] ?? ''}`}
                  title={r.mark}
                >
                  {MARK[r.mark]}
                </span>
              </div>
            ))}
          </div>
          <div className={styles.why}>
            ● had the role · ◐ had the side · ○ no read or wrong.{' '}
            {had.filter((h) => h.mark === 'role').length} of {had.length} had the role;{' '}
            {had.filter((h) => h.mark === 'side').length} more had the side.
          </div>
          {model.note ? (
            <div className={styles.slips}>
              <header>
                Seat {n}’s last note <i>before the vote</i>
              </header>
              <Slip small note={model.note} empty="" />
            </div>
          ) : null}
        </>
      );
    }

    case 'brief':
      return <Brief model={model} chip={chip} />;

    case 'deal':
      return (
        <>
          <header className={styles.head}>
            <strong>{model.truth ? 'The deal, and how it went' : 'The deal'}</strong>
            <span>every seat, face up</span>
          </header>
          <div className={styles.list}>
            {model.rows.map((s) => {
              const f = factionOf(s.role);
              return (
                <div key={s.seat} className={styles.row}>
                  {chip(s.seat)}
                  <span className={styles.nm}>
                    Seat {seatNumber(s.seat)}{' '}
                    {s.role ? (
                      <span className={f ? styles[`c-${f}`] : undefined}>
                        <Sigil role={s.role} className={styles.sigil} /> {role(s.role)}
                      </span>
                    ) : (
                      <i>unknown</i>
                    )}
                  </span>
                  <span className={styles.pair}>{s.fate ?? ''}</span>
                </div>
              );
            })}
          </div>
          <div className={styles.why}>
            {model.truth
              ? 'Withheld all game; every viewer holds it once the game is over.'
              : 'Face up in the X-ray; the table knows only the cast.'}
          </div>
        </>
      );

    case 'notes':
      return (
        <>
          <header className={styles.head}>
            <strong>The winners’ last notes</strong>
            <span>the last note each wrote</span>
          </header>
          <div className={`${styles.list} ${styles.slips}`}>
            {model.rows.map(({ seat, role: r, note }) => (
              <div key={seat}>
                <header>
                  Seat {seatNumber(seat)} {role(r)}
                </header>
                <Slip small note={note} empty="No note." />
              </div>
            ))}
          </div>
        </>
      );

    case 'empty':
      return (
        <>
          <header className={styles.head}>
            <strong>Inside</strong>
            <span>{model.label}</span>
          </header>
          <div className={styles.empty}>
            Nothing inside this beat. The film fills at a turn, the count, the lynch’s card,
            a morning’s brief and the night’s acts.
          </div>
        </>
      );
  }
}

function Slip({
  note,
  small,
  empty,
}: {
  note: FilmNote | null;
  small?: boolean;
  empty: string;
}) {
  if (!note) return empty ? <div className={styles.none}>{empty}</div> : null;
  return (
    <div className={small ? `${styles.slip} ${styles.small}` : styles.slip}>
      {small ? null : <span className={styles.tape} />}
      {seatify(note.text)}
    </div>
  );
}

/** A turn or an actor's act at night: the note, and the lessons as tabs. */
function Inside({
  model,
  tab,
  onTab,
}: {
  model: Extract<FilmModel, { kind: 'inside' }>;
  tab: string;
  onTab?: (tab: string) => void;
}) {
  const open: FilmLesson | undefined = model.lessons.find((l) => `L${l.n}` === tab);
  const turn = model.when === 'turn';
  return (
    <>
      <header className={styles.head}>
        <strong>Inside seat {seatNumber(model.seat)}</strong>
        {model.role ? (
          <span>{(ROLE_NAME[model.role] ?? model.role).toLowerCase()}</span>
        ) : null}
        <span className={styles.tabs} role="tablist">
          <button
            type="button"
            role="tab"
            className={`${styles.tab} ${styles.note}`}
            aria-selected={!open}
            onClick={() => onTab?.('note')}
          >
            Note
          </button>
          {model.lessons.map((l) => (
            <button
              key={l.n}
              type="button"
              role="tab"
              className={
                l.verdict === 'override' ? `${styles.tab} ${styles.override}` : styles.tab
              }
              aria-selected={open?.n === l.n}
              onClick={() => onTab?.(`L${l.n}`)}
            >
              L{l.n}
              {l.verdict === 'override' ? <span className={styles.dot} /> : null}
            </button>
          ))}
        </span>
      </header>
      {open ? (
        <div className={styles.lesson}>
          {seatify(open.action)}
          <div className={styles.verdict}>
            <span
              className={`${styles.stamp} ${open.verdict ? styles[`v-${open.verdict}`] : ''}`}
            >
              {open.verdict ? VERDICT[open.verdict] : 'no verdict'}
            </span>
            <span>{open.why ? seatify(open.why) : null}</span>
          </div>
          <div className={styles.applies}>
            <b>When it applies</b>
            {seatify(open.situation)}
          </div>
        </div>
      ) : (
        <>
          <div className={styles.slipwrap}>
            <Slip
              note={model.note}
              empty={turn ? 'No note after this turn.' : 'No note tonight.'}
            />
          </div>
          <div className={styles.why}>{insideWhy(model)}</div>
        </>
      )}
      {turn ? (
        <div className={styles.why}>
          Reads are on the wing: the seats this speaker has a read on carry the blue edge;
          tap one for the card.
        </div>
      ) : null}
    </>
  );
}

function insideWhy(model: Extract<FilmModel, { kind: 'inside' }>): ReactNode {
  const parts: ReactNode[] = [];
  parts.push(
    <span key="n">
      <b>Note</b>
      {model.note
        ? `, seq ${model.note.seq}, written after ${model.when === 'turn' ? 'the turn' : 'the act'}`
        : ''}
      ;{' '}
    </span>,
  );
  parts.push(
    model.consultSeq !== null ? (
      <span key="c">
        {model.lessons.length} lesson{model.lessons.length === 1 ? '' : 's'} weighed at seq{' '}
        {model.consultSeq}
        {model.carried ? ', carried over from its first turn that day' : ''}
        {model.readsSeq !== null ? `; reads seq ${model.readsSeq}.` : '.'}
      </span>
    ) : (
      <span key="c">no lessons weighed (memory is consulted from day 2).</span>
    ),
  );
  return parts;
}

function Brief({
  model,
  chip,
}: {
  model: Extract<FilmModel, { kind: 'brief' }>;
  chip: (seat: string, sm?: boolean) => ReactNode;
}) {
  const s = model.summary;
  const seats = (list: readonly string[]) =>
    list.map((p) => <span key={p}>{chip(p, true)}</span>);
  return (
    <>
      <header className={styles.head}>
        <strong>What day {model.day} taught</strong>
        <span>the brief the agents carry into day {model.day + 1}</span>
      </header>
      {!s ? (
        <div className={styles.empty}>No summary was carried from this day.</div>
      ) : (
        <div className={styles.list}>
          <div className={styles.sect}>Accusations</div>
          {s.accusations.length ? (
            s.accusations.map((a, i) => (
              <div key={i} className={styles.acc}>
                <header>
                  {seats(a.accusers)}
                  <span>→</span>
                  {chip(a.target, true)}
                  <span>
                    {a.accusers.map((p) => `Seat ${seatNumber(p)}`).join(', ')} → Seat{' '}
                    {seatNumber(a.target)}
                  </span>
                  <span className={styles.stamp}>{a.evidenceType.replace(/_/g, ' ')}</span>
                </header>
                <p>{seatify(a.reasoning)}</p>
                {a.defense ? (
                  <p className={styles.def}>
                    <b>Defence:</b> {seatify(a.defense)}
                  </p>
                ) : null}
              </div>
            ))
          ) : (
            <div className={styles.none}>No accusations that day.</div>
          )}
          <div className={styles.sect}>Claims</div>
          {s.roleClaims.length ? (
            s.roleClaims.map((c, i) => (
              <div key={i} className={styles.acc}>
                <header>
                  {chip(c.player, true)} Seat {seatNumber(c.player)} claims{' '}
                  <span className={styles.aqua}>{c.claimedRole}</span>
                </header>
                {c.evidence ? <p className={styles.def}>{seatify(c.evidence)}</p> : null}
              </div>
            ))
          ) : (
            <div className={styles.none}>None.</div>
          )}
          <div className={styles.sect}>Blocs</div>
          {s.blocs.length ? (
            s.blocs.map((b, i) => (
              <div key={i} className={styles.acc}>
                <header>{seats(b.players)}</header>
                <p className={styles.def}>{seatify(b.basis)}</p>
              </div>
            ))
          ) : (
            <div className={styles.none}>None.</div>
          )}
          <div className={styles.sect}>Mood</div>
          <div className={styles.acc}>
            {[s.dynamics.landscape, s.dynamics.consensus, s.dynamics.drivers]
              .filter(Boolean)
              .map((t, i) => (
                <p key={i}>{seatify(t)}</p>
              ))}
          </div>
        </div>
      )}
    </>
  );
}
