'use client';

/**
 * The gameplay guide (`/guide`): the game modes, a day phase by phase (a railway line, each stop
 * working), after the game (the case file), the tools (working), then the roles, one row per
 * side. A desktop gets a side nav that stays in view; a phone gets one sticky line naming the
 * section in view, which opens the list of sections (Mantine's Menu). Both track the section in
 * view, so the nav always says where the reader is.
 */
import { useEffect, useState, type ReactNode } from 'react';
import { Menu, UnstyledButton } from '@mantine/core';
import { FACTION_NAME, type Faction } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { stageFonts } from '@/stage/fonts';
import { SIDES } from '../sides';
import { CaseFile } from './CaseFile';
import { DayLine } from './DayLine';
import { GameModes } from './GameModes';
import { SideRow } from './SideRow';
import { ToolsTray } from './ToolsTray';
import classes from './Guide.module.css';

const RULES: { id: string; label: string; icon: ReactNode }[] = [
  {
    id: 'modes',
    label: 'Game modes',
    // a ticket, its stub torn along the dashes
    icon: (
      <>
        <rect x="4" y="6" width="16" height="12" rx="2" />
        <path d="M15 6v12" strokeDasharray="2 2" />
      </>
    ),
  },
  {
    id: 'day',
    label: 'A day, phase by phase',
    // the sun on the horizon
    icon: (
      <path d="M3 17h18M6.5 17a5.5 5.5 0 0 1 11 0M12 5v3M5.2 8.7l1.9 1.9M18.8 8.7l-1.9 1.9" />
    ),
  },
  { id: 'after', label: 'After the game', icon: <path d="M8 5v14l11-7z" /> },
  {
    id: 'tools',
    label: 'Tools',
    icon: (
      <>
        <path d="M4 20l4-1 11-11-3-3L5 16z" />
        <path d="M14 6l3 3" />
      </>
    ),
  },
];

const SECTIONS: { id: string; label: string; icon?: ReactNode; faction?: Faction }[] = [
  ...RULES,
  ...SIDES.map((s) => ({
    id: `side-${s.faction}`,
    label: FACTION_NAME[s.faction],
    faction: s.faction,
  })),
];

function SectionIcon({ faction, icon }: { faction?: Faction; icon?: ReactNode }) {
  return faction ? (
    <FactionMark faction={faction} format="mark" className={classes.navIcon} />
  ) : (
    <svg
      className={`${classes.navIcon} ${classes.lineIcon}`}
      viewBox="0 0 24 24"
      aria-hidden="true"
    >
      {icon}
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
    <main className={`${classes.guide} ${stageFonts}`}>
      <nav className={classes.nav} aria-label="Guide sections">
        {SECTIONS.map((s, i) => (
          <a
            key={s.id}
            href={`#${s.id}`}
            className={classes.navLink}
            aria-current={s.id === current ? 'location' : undefined}
            data-first-side={i === RULES.length || undefined}
          >
            <SectionIcon faction={s.faction} icon={s.icon} />
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
                <SectionIcon faction={here.faction} icon={here.icon} />
                <span className={classes.mobileHere}>{here.label}</span>
                <svg className={classes.chevron} viewBox="0 0 24 24" aria-hidden="true">
                  <path d="M6 9l6 6 6-6" />
                </svg>
              </UnstyledButton>
            </Menu.Target>
            <Menu.Dropdown>
              {RULES.map((s) => (
                <Menu.Item
                  key={s.id}
                  component="a"
                  href={`#${s.id}`}
                  leftSection={<SectionIcon icon={s.icon} />}
                  data-current={s.id === current || undefined}
                >
                  {s.label}
                </Menu.Item>
              ))}
              <Menu.Label>Roles</Menu.Label>
              {SECTIONS.slice(RULES.length).map((s) => (
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

        <section id="modes" className={classes.section} aria-labelledby="modes-head">
          <h2 id="modes-head">Game modes</h2>
          <p className={classes.sub}>
            Play alone against the agents, or bring friends to the table.
          </p>
          <GameModes />
        </section>

        <section id="day" className={classes.section} aria-labelledby="day-head">
          <h2 id="day-head">A day, phase by phase</h2>
          <DayLine />
        </section>

        <section id="after" className={classes.section} aria-labelledby="after-head">
          <h2 id="after-head">After the game</h2>
          <CaseFile />
        </section>

        <section id="tools" className={classes.section} aria-labelledby="tools-head">
          <h2 id="tools-head">Tools</h2>
          <p className={classes.sub}>
            Two aids for your seat at the table: notes to keep track of everyone, and your
            own agent to help you write your turn.
          </p>
          <ToolsTray />
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
