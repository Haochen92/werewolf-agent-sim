'use client';

/**
 * The gameplay guide (`/guide`): the game modes, a day phase by phase (a railway line, each stop
 * working), after the game (the case file), the tools (working), then the roles, one row per
 * side. A desktop gets a side nav that stays in view. A phone gets one bar in the site strip's
 * place (owner, 2026-10-15: two stacked bars read badly), down once the nav has scrolled away:
 * a Top button back to the nav, the section being read, which opens the list of sections
 * (Mantine's Menu), and how far through the guide that is. Both track the section in view, so
 * the nav always says where the reader is.
 */
import {
  useEffect,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
  type RefObject,
} from 'react';
import { Menu, UnstyledButton } from '@mantine/core';
import { FACTION_NAME, type Faction } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { useReplaceSiteStrip } from '@/components/site';
import { stageFonts } from '@/stage/fonts';
import { SIDES } from '../sides';
import { CaseFile } from './CaseFile';
import { DayLine } from './DayLine';
import { GameModes } from './GameModes';
import { Introduction } from './Introduction';
import { SideRow } from './SideRow';
import { ToolsTray } from './ToolsTray';
import classes from './Guide.module.css';

type Entry = { id: string; label: string; icon: ReactNode };

/** The sections before the roles: the story and goal, starting, the day, the tools. */
const RULES: Entry[] = [
  {
    id: 'intro',
    label: 'Introduction',
    // a carriage: its windows, its wheels
    icon: (
      <>
        <rect x="3" y="5" width="18" height="12" rx="2" />
        <path d="M6.5 9.5h3M11 9.5h2M14.5 9.5h3M7 20l1.5-3M17 20l-1.5-3" />
      </>
    ),
  },
  {
    id: 'modes',
    label: 'Take your seat',
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

/** After the roles: once a game is played, its replay. */
const AFTER: Entry = {
  id: 'after',
  label: 'After the game',
  icon: <path d="M8 5v14l11-7z" />,
};

const SECTIONS: { id: string; label: string; icon?: ReactNode; faction?: Faction }[] = [
  ...RULES,
  ...SIDES.map((s) => ({
    id: `side-${s.faction}`,
    label: FACTION_NAME[s.faction],
    faction: s.faction,
  })),
  AFTER,
];
/** Where the nav draws a rule: before the roles, and after them. */
const RULED = new Set([RULES.length, RULES.length + SIDES.length]);

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

/**
 * The section being read: the last one whose heading has reached the bottom of what is pinned
 * at the top (the phone's line, else the site's strip), so the nav changes as a section's
 * title comes up under it. At the page's foot, the last section.
 */
function useSectionInView(ids: string[], line: RefObject<HTMLElement | null>) {
  const [current, setCurrent] = useState(ids[0]);
  useEffect(() => {
    const heads = ids.map((id) => {
      const el = document.getElementById(id);
      return el?.querySelector('h2, h3') ?? el;
    });
    let frame = 0;
    const update = () => {
      frame = 0;
      const bar = line.current?.getBoundingClientRect();
      const strip = parseFloat(
        getComputedStyle(document.documentElement).getPropertyValue('--site-strip'),
      );
      // the phone's bar (its foot, or the top while it is up), else the strip (none at the page's
      // top); an anchor lands its heading 16 under that (Guide.module.css), so a jump counts
      const under = (bar && bar.height > 0 ? Math.max(bar.bottom, 0) : strip || 0) + 24;
      const atFoot =
        window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 2;
      let at = 0;
      heads.forEach((h, i) => {
        if (h && h.getBoundingClientRect().top <= under) at = i;
      });
      setCurrent(ids[atFoot ? ids.length - 1 : at]);
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', onScroll);
    return () => {
      window.removeEventListener('scroll', onScroll);
      window.removeEventListener('resize', onScroll);
      cancelAnimationFrame(frame);
    };
  }, [ids, line]);
  return current;
}

const IDS = SECTIONS.map((s) => s.id);

export function Guide() {
  const line = useRef<HTMLDivElement>(null);
  const { pinned, backToTop } = useReplaceSiteStrip();
  const current = useSectionInView(IDS, line);
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
            data-ruled={RULED.has(i) || undefined}
          >
            <SectionIcon faction={s.faction} icon={s.icon} />
            {s.label}
          </a>
        ))}
      </nav>

      <div className={classes.main}>
        <div
          ref={line}
          className={classes.mobileNav}
          data-on={pinned || undefined}
          inert={!pinned}
        >
          <div className={classes.mobileBar}>
            <button type="button" className={classes.toTop} onClick={backToTop}>
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M8 13V3.5M3.5 8 8 3.5 12.5 8" />
              </svg>
              Top
            </button>
            <span className={classes.barRule} aria-hidden="true" />
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
                {SECTIONS.slice(RULES.length, RULES.length + SIDES.length).map((s) => (
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
                <Menu.Divider />
                <Menu.Item
                  component="a"
                  href={`#${AFTER.id}`}
                  leftSection={<SectionIcon icon={AFTER.icon} />}
                  data-current={AFTER.id === current || undefined}
                >
                  {AFTER.label}
                </Menu.Item>
              </Menu.Dropdown>
            </Menu>
            <span
              className={classes.progress}
              style={
                {
                  '--done': (SECTIONS.indexOf(here) + 1) / SECTIONS.length,
                } as CSSProperties
              }
              aria-hidden="true"
            />
          </div>
        </div>

        <h1 className={classes.title}>Gameplay guide</h1>

        <section id="intro" className={classes.section} aria-labelledby="intro-head">
          <h2 id="intro-head">Aboard the Ninth Express</h2>
          <Introduction />
        </section>

        <section id="modes" className={classes.section} aria-labelledby="modes-head">
          <h2 id="modes-head">Take your seat</h2>
          <p className={classes.sub}>
            Play solo with nine AI players, or invite friends and let AI players fill the
            empty seats.
          </p>
          <GameModes />
        </section>

        <section id="day" className={classes.section} aria-labelledby="day-head">
          <h2 id="day-head">A day, phase by phase</h2>
          <DayLine />
        </section>

        <section id="tools" className={classes.section} aria-labelledby="tools-head">
          <h2 id="tools-head">Tools</h2>
          <p className={classes.sub}>
            Two aids while you play: notes on the other players, and your own agent to help
            write your messages.
          </p>
          <ToolsTray />
        </section>

        <section className={classes.section} aria-labelledby="roles-head">
          <h2 id="roles-head">Roles</h2>
          <p className={classes.sub}>
            All twelve role cards, by side. Select a card to turn it over for its briefing,
            the same one its AI player is given, or switch on Briefings to turn a whole
            side.
          </p>
          {SIDES.map((s) => (
            <SideRow key={s.faction} faction={s.faction} roles={s.roles} />
          ))}
        </section>

        <section id="after" className={classes.section} aria-labelledby="after-head">
          <h2 id="after-head">After the game</h2>
          <p className={classes.sub}>
            Rewatch a finished game to see how it unfolded. Turn on Reveal to see the hidden
            roles, the night actions and the wolves&rsquo; private chat.
          </p>
          <CaseFile />
        </section>
      </div>
    </main>
  );
}
