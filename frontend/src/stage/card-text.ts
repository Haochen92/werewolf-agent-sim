/**
 * What a role card says: its name, its front line, and what the role does at night. The
 * words are the design bundle's role kit (docs/design_2026-09-25/kits/role-kit.js, `CARD`),
 * copied as they are so the card on the shelf and the card the designs were reviewed with
 * read the same. The kit writes a line break as `<br>`; here it is `\n`, and the card draws
 * each piece on its own line.
 */
export interface CardText {
  name: string;
  /** The front line, under the name. */
  line: string;
  /** What the role does at night, as the card's "At night" part says it. */
  night: string;
  /** The wolf's night line once its packmate is gone. */
  nightAlone?: string;
}

export const CARD_TEXT: Record<string, CardText> = {
  villager: {
    name: 'Villager',
    line: 'No tricks up their sleeve.\nOnly wits and a vote.',
    night: 'Nothing to do. You sleep and wait for the morning report.',
  },
  healer: {
    name: 'Healer',
    line: 'Mends what the night would tear.',
    night: "Protect one player from being killed tonight. You can't protect yourself.",
  },
  investigator: {
    name: 'Investigator',
    line: 'Peeks inside one glove each night.',
    night: "Learn one player's exact role. Only you see the result.",
  },
  vigilante: {
    name: 'Vigilante',
    line: 'Takes the law into their own hands,\none bullet at a time.',
    night:
      "You may shoot one player. Bullets are never reloaded, and a shot can't kill the serial killer.",
  },
  wolf: {
    name: 'Wolf',
    line: 'Two of them,\nand neither is Grandma.',
    night: 'Talk with your packmate in private, then choose one player to kill.',
    nightAlone: 'Choose one player to kill. You hunt alone now.',
  },
  serial_killer: {
    name: 'Serial killer',
    line: 'Plays well with no one.\nCuts one thread each night.',
    night: "Kill one player. You can't be killed at night.",
  },
};
