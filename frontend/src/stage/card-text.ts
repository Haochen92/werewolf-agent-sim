/**
 * What a role card says: its name, its front line, and the briefing on its back (by day, at
 * night, how you win; the landing turns the card to it). The words are the design bundle's role kit (docs/design_2026-09-25/kits/role-kit.js, `CARD`),
 * copied as they are so the card on the shelf and the card the designs were reviewed with
 * read the same. The kit writes a line break as `<br>`; here it is `\n`, and the card draws
 * each piece on its own line.
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
    win: 'With the villagers, when both the wolves and the serial killer are gone.',
  },
  healer: {
    name: 'Healer',
    line: 'Mends what the night would tear.',
    day: 'Blend in like any villager. Too directive draws attention, and too quiet looks like a power role hiding.',
    night: "Protect one player from being killed tonight. You can't protect yourself.",
    win: 'With the villagers, when both the wolves and the serial killer are gone.',
  },
  investigator: {
    name: 'Investigator',
    line: 'Peeks inside one glove each night.',
    day: 'A result only helps once the village acts on it. Revealing can rally them, and it also marks you for the night.',
    night: "Learn one player's exact role. Only you see the result.",
    win: 'With the villagers, when both the wolves and the serial killer are gone.',
  },
  vigilante: {
    name: 'Vigilante',
    line: 'Takes the law into their own hands,\none bullet at a time.',
    day: 'Vote like any villager, and watch who deserves one of your few bullets. A target who survives your shot tells you something.',
    night:
      "You may shoot one player. Bullets are never reloaded, and a shot can't kill the serial killer.",
    win: 'With the villagers, when both the wolves and the serial killer are gone.',
  },
  wolf: {
    name: 'Wolf',
    line: 'Two of them,\nand neither is Grandma.',
    day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
    night: 'Talk with your packmate in private, then choose one player to kill.',
    nightAlone: 'Choose one player to kill. You hunt alone now.',
    win: 'When the serial killer is gone and, at the start of a day, the wolves equal or outnumber the villagers.',
  },
  serial_killer: {
    name: 'Serial killer',
    line: 'Plays well with no one.\nCuts one thread each night.',
    day: 'Blend in as an ordinary villager, neither dominating the talk nor vanishing from it. Only a day vote can remove you.',
    night: "Kill one player. You can't be killed at night.",
    win: 'Alone, when at most one other player is left alive.',
  },
  // The eight 1920s roles (frontend/docs/role_cards_brief.md §4), ahead of the engine, which
  // does not deal them yet. Their win lines already say "the town" (the owner's ruling,
  // 2026-10-07); the cards above change theirs with the engine.
  sentinel: {
    name: 'Sentinel',
    line: 'Lights one candle at one door,\nand counts who passes.',
    day: "You hold names, not verdicts. A visitor at a victim's door is a lead; say when you saw it and let the room weigh it. A dead name at a door is no ghost: someone is working the body.",
    night:
      'Watch one player. In the morning you learn the names of everyone who visited them.',
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
    day: 'Your sigils are few; spend them where the talk points. A miss means only that your target struck no one with their own hand that night.',
    night:
      'Place a sigil on one player, two in the game. If they attack anyone tonight, your sigil strikes them back afterwards; the victim still dies. The serial killer survives it, and you learn they attacked.',
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  chanteuse: {
    name: 'Chanteuse',
    line: 'Keeps one guest at her table\nuntil the night is over.',
    day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
    night:
      "Talk with your packmate and choose the kill. Then keep one player at your table all night: a town player's act comes to nothing, and they learn they were held, not by whom. Anyone else is unaffected, and you are told so.",
    nightAlone:
      'Choose one player to kill, then keep one player at your table; only a town player is held. You hunt alone now.',
    win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber the town.',
  },
  illusionist: {
    name: 'Illusionist',
    line: "Makes a body's secret\nvanish with the body.",
    day: 'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
    night:
      "Talk with your packmate and choose the kill. Twice in the game you may conceal the victim's role from the morning report; you learn it yourself.",
    nightAlone:
      'Choose one player to kill, and conceal if you still can. You hunt alone now.',
    win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber the town.',
  },
  necromancer: {
    name: 'Necromancer',
    line: 'Pulls the strings\nof those already gone.',
    day: 'Blend in as an ordinary town player, neither dominating the talk nor vanishing from it. The vote can remove you; from the second night, so can a bullet.',
    night:
      'Night 1: nothing, and nothing can kill you. From Night 2: pick a dead, unconcealed player and use their night ability on one target, never the same body two nights running.',
    win: 'Alone, when at most one other player is left alive.',
  },
  speculator: {
    name: 'Speculator',
    line: 'Backs a side like a stock.\nCollects if it pays.',
    day: 'Watch which side is pulling ahead. Once your pick is announced, keep that side winning and keep yourself alive.',
    night:
      'Pick the side you think will win, at the latest on the night after Day 2. The next morning announces the pick, not your name.',
    win: 'When the side you picked wins and you are still alive.',
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
