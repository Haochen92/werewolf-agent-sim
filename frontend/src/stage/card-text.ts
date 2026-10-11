/**
 * What a role card says: its name, its front line, and the briefing on its back (by day, at
 * night, how you win; the landing turns the card to it). The words are the design bundle's role kit (docs/design_2026-09-25/kits/role-kit.js, `CARD`),
 * copied as they are so the card on the shelf and the card the designs were reviewed with
 * read the same. The kit writes a line break as `<br>`; here it is `\n`, and the card draws
 * each piece on its own line. Where the rules moved after the kit (the role sheet,
 * evidence/game_play_enhancement/role_sheet.md), the words follow the rules.
 */
export interface CardText {
  name: string;
  /** The front line, under the name. */
  line: string;
  /** The briefing's "By day": how the role plays the discussion and the vote. */
  day: string;
  /** What the role does at night, as the card's "At night" part says it. */
  night: string;
  /** The briefing's "How you win". */
  win: string;
  /** The wolf's night line once its packmate is gone. */
  nightAlone?: string;
}

export const CARD_TEXT: Record<string, CardText> = {
  villager: {
    name: 'Villager',
    line: 'No tricks up their sleeve.\nOnly wits and a vote.',
    day: "Push for concrete reads and ask for the reasons behind them. It's fine to hold off rather than invent a suspicion. The voting record is your hardest evidence.",
    night: 'Nothing to do. You sleep and wait for the morning report.',
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  healer: {
    name: 'Healer',
    line: 'Mends what the night would tear.',
    day: 'Blend in like any town player. Too directive draws attention, and too quiet looks like a power role hiding.',
    night: "Protect one player from being killed tonight. You can't protect yourself.",
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  investigator: {
    name: 'Investigator',
    line: 'Peeks inside one glove\nwhen it counts.',
    day: 'A result only helps once the town acts on it. Revealing can rally them, and it also marks you for the night.',
    night:
      'Check one player, two checks in the game. Wolves read Suspicious, and so does the necromancer on a night it attacks; everyone else, the serial killer included, reads Not suspicious. Only you see the result.',
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  vigilante: {
    name: 'Vigilante',
    line: 'Takes the law into their own hands,\none bullet at a time.',
    day: 'Vote like any town player, and watch who deserves one of your few bullets. A target who survives your shot tells you something.',
    night:
      "You may shoot one player. Bullets are never reloaded, and a shot can't kill the serial killer.",
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  wolf: {
    name: 'Wolf',
    line: 'Two of them,\nand neither is Grandma.',
    day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
    night: 'Talk with your packmate in private, then choose one player to kill.',
    nightAlone: 'Choose one player to kill. You hunt alone now.',
    win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber everyone else alive.',
  },
  serial_killer: {
    name: 'Serial killer',
    line: 'Plays well with no one.\nCuts one thread each night.',
    day: 'Blend in as an ordinary town player, neither dominating the talk nor vanishing from it. Only a day vote can remove you.',
    night: "Kill one player. You can't be killed at night.",
    win: 'Alone, when at most one other player is left alive.',
  },
  // The eight 1920s roles (frontend/docs/role_cards_brief.md §4). Every card's win line says
  // "the town" and "the lone killer" (the owner's ruling, 2026-10-07).
  sentinel: {
    name: 'Sentinel',
    line: 'Lights one candle at one door,\nand counts who passes.',
    day: "You hold names, not verdicts. A visitor at a victim's door is a lead; say when you saw it and let the room weigh it. A dead name at a door is no ghost: someone is working the body.",
    night:
      'Watch one player, two watches in the game. In the morning you learn the names of everyone who visited them.',
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  trailseer: {
    name: 'Trailseer',
    line: 'Follows one trail through the night,\nall the way to the door.',
    day: "Where someone went is a fact; why is for the room to argue. Pair your trail with the Sentinel's names and the morning report.",
    night: 'Follow one player. You learn who they visited, or that they visited no one.',
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  sigilist: {
    name: 'Sigilist',
    line: 'Marks a door with a sign.\nWhoever strikes from it answers for it.',
    day: 'Your sigils are few; spend them where the talk points. A miss means your target struck no one with their own hand that night, or was the serial killer, whom no sigil can kill.',
    night:
      'Place a sigil on one player, two in the game. If they attack anyone tonight, your sigil strikes them back afterwards; the victim still dies. The serial killer survives it, and you learn only that your sigil had no effect.',
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  chanteuse: {
    name: 'Chanteuse',
    line: 'Keeps one guest at her table\nuntil the night is over.',
    day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
    night:
      'Talk with your packmate and choose the kill. Then keep one player at your table all night: their act comes to nothing, and they learn they were held, not by whom. The lone killer and the neutral are never held, and you are told so.',
    nightAlone:
      'Choose one player to kill, then keep one player at your table; only a town player is held. You hunt alone now.',
    win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber everyone else alive.',
  },
  illusionist: {
    name: 'Illusionist',
    line: "Makes a body's secret\nvanish with the body.",
    day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
    night:
      "Talk with your packmate and choose the kill. Twice in the game you may conceal the victim's role from the morning report; you learn it yourself.",
    nightAlone:
      'Choose one player to kill, and conceal if you still can. You hunt alone now.',
    win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber everyone else alive.',
  },
  necromancer: {
    name: 'Necromancer',
    line: 'Pulls the strings\nof those already gone.',
    day: 'Blend in as an ordinary town player, neither dominating the talk nor vanishing from it. The vote can remove you; from the second night, so can a bullet.',
    night:
      'Night 1: nothing, and nothing can kill you. From Night 2: pick a dead, unconcealed player and use their night ability on one target.',
    win: 'Alone, when at most one other player is left alive.',
  },
  speculator: {
    name: 'Speculator',
    line: 'Backs a side like a stock.\nCollects if it pays.',
    day: 'Watch which side is pulling ahead. Once your pick is announced, help that side win; until then, stay alive.',
    night:
      'Pick the side you think will win, or yourself, on any night you like; there is no deadline, but dying unpicked loses. The next morning announces the pick, not your name.',
    win: 'When the side you picked wins, alive or dead. A pick of yourself wins only as the last one standing.',
  },
  fortune_teller: {
    name: 'Fortune teller',
    line: "Reads tomorrow's news\nin tonight's glass.",
    day: 'Nobody fears you and nobody needs you. Listen for who the night will take, and keep your own name out of it; the vote never pays.',
    night:
      'As the night begins, bet on who dies tonight: one point for the player, two for the player and their role. Or, twice in the game, bet on yourself, which scores nothing but helps you live through the night. You learn how the bet went once the night is over.',
    win: 'Once you hold two points, whether or not you live to see the end.',
  },
};

/**
 * The six nine-seat roles as their cards read before the ten-seat pool (frozen: an archived
 * game's cards say the rules it was played by). The investigator learns an exact role every
 * night; the rest of the abilities read as they did. The side is named the town and the lone
 * killer, as everywhere in the UI (the owner's ruling, 2026-10-07); in these games the lone
 * killer is always the serial killer.
 */
export const LEGACY_CARD_TEXT: Readonly<Record<string, CardText>> = {
  villager: {
    name: 'Villager',
    line: 'No tricks up their sleeve.\nOnly wits and a vote.',
    day: "Push for concrete reads and ask for the reasons behind them. It's fine to hold off rather than invent a suspicion. The voting record is your hardest evidence.",
    night: 'Nothing to do. You sleep and wait for the morning report.',
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  healer: {
    name: 'Healer',
    line: 'Mends what the night would tear.',
    day: 'Blend in like any town player. Too directive draws attention, and too quiet looks like a power role hiding.',
    night: "Protect one player from being killed tonight. You can't protect yourself.",
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  investigator: {
    name: 'Investigator',
    line: 'Peeks inside one glove each night.',
    day: 'A result only helps once the town acts on it. Revealing can rally them, and it also marks you for the night.',
    night: "Learn one player's exact role. Only you see the result.",
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  vigilante: {
    name: 'Vigilante',
    line: 'Takes the law into their own hands,\none bullet at a time.',
    day: 'Vote like any town player, and watch who deserves one of your few bullets. A target who survives your shot tells you something.',
    night:
      "You may shoot one player. Bullets are never reloaded, and a shot can't kill the serial killer.",
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  wolf: {
    name: 'Wolf',
    line: 'Two of them,\nand neither is Grandma.',
    day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
    night: 'Talk with your packmate in private, then choose one player to kill.',
    nightAlone: 'Choose one player to kill. You hunt alone now.',
    win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber the town.',
  },
  serial_killer: {
    name: 'Serial killer',
    line: 'Plays well with no one.\nCuts one thread each night.',
    day: 'Blend in as an ordinary town player, neither dominating the talk nor vanishing from it. Only a day vote can remove you.',
    night: "Kill one player. You can't be killed at night.",
    win: 'Alone, when at most one other player is left alive.',
  },
};

/** The game shown is an archived nine-seat one: its `game_started` named no lineup. */
export const isNineSeat = (view: { lineup: readonly string[] }) => view.lineup.length === 0;

/**
 * A role's card words for the game shown: a nine-seat game's (`legacy`, see `isNineSeat`) read
 * its own rules, a ten-seat game's the pool's. The ticket and the landing read the pool's.
 */
export function cardTextFor(role: string, legacy = false): CardText | undefined {
  return (legacy ? LEGACY_CARD_TEXT[role] : undefined) ?? CARD_TEXT[role];
}
