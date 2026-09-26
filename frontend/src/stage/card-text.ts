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
};
