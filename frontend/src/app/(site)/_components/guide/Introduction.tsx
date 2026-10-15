/**
 * The guide's opening (owner, 2026-10-15): a short piece of story beside the carriage at the
 * deal, then who is aboard (the four sides, their numbers and what each must do to win, every
 * one in view), and what a day and a night are for. Theme first, then the goal, then the
 * rules; the game modes follow. The pictures are stills of the game's own parts (the waiting
 * room's platform and figures, the dining car with the row of chips), one image each, so a
 * phone draws no stage here.
 */
import Image from 'next/image';
import { FACTION_NAME, type Faction } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import platform from '@/assets/site/guide/platform.webp';
import day from '@/assets/site/guide/day.webp';
import night from '@/assets/site/guide/night.webp';
import classes from './Introduction.module.css';

const ABOARD: { faction: Faction; count: string; goal: string }[] = [
  {
    faction: 'villagers',
    count: '6 passengers',
    goal: 'Find and eliminate the wolves and the lone killer. At least one Town player must survive.',
  },
  {
    faction: 'wolves',
    count: '2 passengers',
    goal: 'You know each other and hunt together. Eliminate the lone killer, then equal or outnumber everyone else alive.',
  },
  {
    faction: 'serial_killer',
    count: '1 passenger',
    goal: 'Work alone. Survive until no more than one other player remains.',
  },
  {
    faction: 'neutral_benign',
    count: '1 passenger',
    goal: 'Pursue your own objective: back the side you think will win, or predict who dies at night. You can win alongside any side.',
  },
];

export function Introduction() {
  return (
    <>
      <div className={classes.opening}>
        <div className={classes.story}>
          <p>
            Ten puppets share a carriage, but not a destination. Wolves sit among the
            passengers, a lone killer watches for an opening, and someone has a wager of
            their own.
          </p>
          <p className={classes.you}>
            You play one passenger with a secret role. Work out whom to trust, decide what
            to reveal, and help your side win.
          </p>
        </div>
        <Image
          src={platform}
          alt="Puppets queuing on the platform in front of the train, at night"
          className={classes.picture}
          sizes="(max-width: 1000px) 100vw, 480px"
          priority
        />
      </div>

      <h3 className={classes.head}>Who&rsquo;s aboard</h3>
      <ul className={classes.sides}>
        {ABOARD.map((s) => (
          <li key={s.faction} className={classes.side} data-faction={s.faction}>
            <div className={classes.sideHead}>
              <FactionMark faction={s.faction} format="mark" className={classes.mark} />
              <b>{FACTION_NAME[s.faction]}</b>
              <span className={classes.count}>{s.count}</span>
            </div>
            <p>{s.goal}</p>
          </li>
        ))}
      </ul>
      <p className={classes.note}>
        Every game deals the six Town roles and both wolves, then either the Serial killer
        or the Necromancer, and either the Speculator or the Fortune teller. You know which
        roles are aboard. Who holds each role is the secret.
      </p>

      <div className={classes.pair}>
        <figure>
          <Image
            src={day}
            alt="The dining car by day, the ten passengers in a row"
            className={classes.picture}
            sizes="(max-width: 760px) 100vw, 420px"
          />
          <figcaption>
            <b>By day</b>
            Share what you know, question other passengers and make your case. From Day 2,
            vote on whom to eliminate.
          </figcaption>
        </figure>
        <figure>
          <Image
            src={night}
            alt="The same car at night, lit by its lamps"
            className={classes.picture}
            sizes="(max-width: 760px) 100vw, 420px"
          />
          <figcaption>
            <b>By night</b>
            Use your role&rsquo;s ability in private. Morning reveals who died, and gives
            everyone more to argue about.
          </figcaption>
        </figure>
      </div>
    </>
  );
}
