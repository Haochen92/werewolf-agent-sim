'use client';

/**
 * The gameplay guide (`/guide`): how a game goes, then the roles, one row per side. A desktop
 * gets a side nav that stays in view; a phone gets one sticky line naming the section in view,
 * which opens the list of sections (Mantine's Menu). Both track the section in view, so the nav
 * always says where the reader is.
 */
import { useEffect, useState } from 'react';
import { Menu, UnstyledButton } from '@mantine/core';
import { FACTION_NAME, type Faction } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { SIDES } from '../sides';
import { SideRow } from './SideRow';
import { STEPS, STEP_ICON } from './steps';
import classes from './Guide.module.css';

const SECTIONS: { id: string; label: string; faction?: Faction }[] = [
  { id: 'how', label: 'How a game goes' },
  ...SIDES.map((s) => ({
    id: `side-${s.faction}`,
    label: FACTION_NAME[s.faction],
    faction: s.faction,
  })),
];

function SectionIcon({ faction }: { faction?: Faction }) {
  return faction ? (
    <FactionMark faction={faction} format="mark" className={classes.navIcon} />
  ) : (
    <svg
      className={`${classes.navIcon} ${classes.lineIcon}`}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      {STEP_ICON.dawn}
    </svg>
  );
}

/** The section in view: the last one whose top has passed a third of the way down. */
function useSectionInView(ids: string[]) {
  const [current, setCurrent] = useState(ids[0]);
  useEffect(() => {
    const io = new IntersectionObserver(
      (entries) => {
        for (const e of entries) if (e.isIntersecting) setCurrent(e.target.id);
      },
      { rootMargin: '-30% 0px -60% 0px' },
    );
    for (const id of ids) {
      const el = document.getElementById(id);
      if (el) io.observe(el);
    }
    return () => io.disconnect();
  }, [ids]);
  return current;
}

const IDS = SECTIONS.map((s) => s.id);

export function Guide() {
  const current = useSectionInView(IDS);
  const here = SECTIONS.find((s) => s.id === current) ?? SECTIONS[0];

  return (
    <main className={classes.guide}>
      <nav className={classes.nav} aria-label="Guide sections">
        {SECTIONS.map((s, i) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            className={classes.navLink}
            aria-current={s.id === current ? 'location' : undefined}
            data-first-side={i === 1 || undefined}
          >
            <SectionIcon faction={s.faction} />
            {s.label}
          </a>
        ))}
      </nav>

      <div className={classes.main}>
        <div className={classes.mobileNav}>
          <Menu
            position="bottom-start"
            width="target"
            classNames={{
              dropdown: classes.menu,
              item: classes.menuItem,
              label: classes.menuLabel,
            }}
          >
            <Menu.Target>
              <UnstyledButton
                className={classes.mobileButton}
                aria-label={`Guide sections: ${here.label}`}
              >
                <SectionIcon faction={here.faction} />
                <span className={classes.mobileHere}>{here.label}</span>
                <svg className={classes.chevron} viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </UnstyledButton>
            </Menu.Target>
            <Menu.Dropdown>
              <Menu.Item component="a" href="#how" leftSection={<SectionIcon />}>
                How a game goes
              </Menu.Item>
              <Menu.Label>Roles</Menu.Label>
              {SECTIONS.slice(1).map((s) => (
                <Menu.Item
                  key={s.id}
                  component="a"
                  href={`#${s.id}`}
                  leftSection={<SectionIcon faction={s.faction} />}
                  data-current={s.id === current || undefined}
                >
                  {s.label}
                </Menu.Item>
              ))}
            </Menu.Dropdown>
          </Menu>
        </div>

        <h1 className={classes.title}>Gameplay guide</h1>

        <section id="how" className={classes.section} aria-labelledby="how-head">
          <h2 id="how-head">How a game goes</h2>
          <ol className={classes.steps}>
            {STEPS.map((s) => (
              <li key={s.title}>
                <span className={classes.stepIcon} aria-hidden="true">
                  <svg viewBox="0 0 24 24">{STEP_ICON[s.icon]}</svg>
                </span>
                <b>{s.title}</b>
                <p>{s.text}</p>
              </li>
            ))}
          </ol>
          <p className={classes.again}>
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M20 7v5h-5" />
              <path d="M19.5 12A7.5 7.5 0 1 1 17 6.5" />
            </svg>
            <span>
              <b>Then the next day begins.</b> The game goes on until one side has won.
            </span>
          </p>
        </section>

        <section className={classes.section} aria-labelledby="roles-head">
          <h2 id="roles-head">Roles</h2>
          <p className={classes.sub}>
            Ten seats, four sides. Every seat is dealt one of these cards in secret, and the
            card is the briefing its agent is given.
          </p>
          {SIDES.map((s) => (
            <SideRow key={s.faction} faction={s.faction} roles={s.roles} />
          ))}
        </section>
      </div>
    </main>
  );
}
