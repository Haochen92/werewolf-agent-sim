'use client';

/**
 * "How a game goes" (landing v5), beside the roles: the day's four steps as a dotted track, one
 * lit at a time. While it is on screen and nobody has pressed a step, it walks itself slowly;
 * a press stops the walk, and a viewer who asked for reduced motion gets no walk at all.
 */
import { useEffect, useRef, useState } from 'react';
import { useReducedMotion } from 'motion/react';
import classes from './GameLoop.module.css';

const ICON = {
  dawn: (
    <path d="M3 17h18M6.5 17a5.5 5.5 0 0 1 11 0M12 5v3M5.2 8.7l1.9 1.9M18.8 8.7l-1.9 1.9M8 21h8" />
  ),
  talk: (
    <>
      <path d="M4 5h16v10H10l-4 4v-4H4z" />
      <path d="M8 9h8M8 12h5" />
    </>
  ),
  vote: (
    <>
      <path d="M6 10h12l-1 10H7z" />
      <path d="M9 10V6h6v4M10 3.5h4" />
    </>
  ),
  night: <path d="M17.5 15.5A7 7 0 0 1 9 4.2a7.5 7.5 0 1 0 8.5 11.3z" />,
};

const STEPS: { icon: keyof typeof ICON; title: string; text: string }[] = [
  {
    icon: 'dawn',
    title: 'A new day',
    text: 'The morning report: anyone killed in the night is named, and their card is turned. On day 1, no one has died yet.',
  },
  {
    icon: 'talk',
    title: 'Discuss',
    text: 'Seats speak in turn, and any seat may pass. After it speaks, each agent rewrites its private note and its reads on the others.',
  },
  {
    icon: 'vote',
    title: 'Vote',
    text: 'Every living seat votes at once, blind. The seat with the most votes is out and its card is turned; a tie sends no one out. Day 1 has no vote.',
  },
  {
    icon: 'night',
    title: 'Night',
    text: 'Hidden acts: the wolves kill, block and hide a body; the healer protects; the investigator, the sentinel and the trailseer gather evidence; the vigilante may shoot and the sigilist mark a door; the lone killer strikes; the neutral places its bet.',
  },
];

const WALK_MS = 3600;

export function GameLoop() {
  const [cur, setCur] = useState(0);
  const [touched, setTouched] = useState(false);
  const [onScreen, setOnScreen] = useState(false);
  const still = useReducedMotion() === true;
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([e]) => setOnScreen(e.isIntersecting), {
      threshold: 0.5,
    });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  useEffect(() => {
    if (!onScreen || touched || still) return;
    const t = setInterval(() => setCur((c) => (c + 1) % STEPS.length), WALK_MS);
    return () => clearInterval(t);
  }, [onScreen, touched, still]);

  return (
    <div ref={ref} className={classes.loop}>
      <h3 className={classes.head}>How a game goes</h3>
      <ol className={classes.steps}>
        {STEPS.map((s, i) => (
          <li key={s.title}>
            <button
              type="button"
              className={classes.step}
              aria-pressed={i === cur}
              onClick={() => {
                setTouched(true);
                setCur(i);
              }}
            >
              <span className={classes.md} aria-hidden="true">
                <svg viewBox="0 0 24 24">{ICON[s.icon]}</svg>
              </span>
              <span className={classes.tx}>
                <b>{s.title}</b>
                <span>{s.text}</span>
              </span>
            </button>
          </li>
        ))}
      </ol>
      <div className={classes.repeat}>
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <path d="M20 7v5h-5" />
          <path d="M19.5 12A7.5 7.5 0 1 1 17 6.5" />
        </svg>
        <span>
          <b>Then find out what happens the next day.</b> The game goes on until one side
          has won.
        </span>
      </div>
    </div>
  );
}
