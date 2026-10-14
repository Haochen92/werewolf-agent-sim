/**
 * How a game goes, as the guide's first section: the day's four steps (they were the landing's
 * "How a game goes" track before the rules moved here).
 */
import type { ReactNode } from 'react';

export const STEP_ICON: Record<'dawn' | 'talk' | 'vote' | 'night', ReactNode> = {
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

export const STEPS: { icon: keyof typeof STEP_ICON; title: string; text: string }[] = [
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
