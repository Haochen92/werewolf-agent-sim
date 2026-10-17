/**
 * What a role card says: its name, its front line, and on its back the rules (owner, 2026-10-15:
 * the ability, a wolf's pack ability first, and when it wins; no playing advice; checked against
 * the engine), which the site's cards turn to. The game's own card says only the short "At
 * night". The words are the design bundle's role kit (docs/design_2026-09-25/kits/role-kit.js, `CARD`),
 * copied as they are so the card on the shelf and the card the designs were reviewed with
 * read the same. The kit writes a line break as `<br>`; here it is `\n`, and the card draws
 * each piece on its own line. Where the rules moved after the kit (the role sheet,
 * evidence/game_play_enhancement/role_sheet.md), the words follow the rules.
 */
export interface CardText {
  name: string;
  /** The front line, under the name. */
  line: string;
  /** The back's "Ability": the rules of what the role does (a `\n` starts a new paragraph). */
  ability: string;
  /** A wolf's back opens with the pack's shared rules ("Pack ability"). */
  pack?: string;
  /**
   * What the role does at night, short, as the game's own card says it ("At night"; owner,
   * 2026-10-16: shortened). A limited ability's count is not in it: the card's uses line says it.
   */
  night: string;
  /** The back's "You win when". */
  win: string;
  /** The wolf's night line once its packmate is gone. */
  nightAlone?: string;
}

export const CARD_TEXT: Record<string, CardText> = {
  villager: {
    name: 'Villager',
    line: 'No tricks up their sleeve.\nOnly wits and a vote.',
    ability: 'None at night: you sleep and wait for the morning report.',
    night: 'Nothing to do. You sleep and wait for the morning report.',
    win: 'All wolves and the lone killer are eliminated, with at least one Town player still alive.',
  },
  healer: {
    name: 'Healer',
    line: 'Keeps a needle and thread for those who barely make it through the night.',
    ability:
      'Each night, protect one other player from night attacks. You cannot protect yourself.',
    night: "Protect one player from being killed tonight. You can't protect yourself.",
    win: 'All wolves and the lone killer are eliminated, with at least one Town player still alive.',
  },
  investigator: {
    name: 'Investigator',
    line: 'Every passenger has a story; they look for the loose thread.',
    ability:
      'On up to two nights, check one player. You privately learn whether they are Suspicious or Not suspicious. Wolves are Suspicious, as is the Necromancer on nights it attacks. Everyone else—including the Serial killer—is Not suspicious.',
    night:
      'Check one player. Wolves read Suspicious, and so does the necromancer on a night it attacks. Everyone else reads Not suspicious.',
    win: 'All wolves and the lone killer are eliminated, with at least one Town player still alive.',
  },
  vigilante: {
    name: 'Vigilante',
    line: 'Packed a pistol, hoping they wouldn’t need it.',
    ability:
      'Each night, shoot one player or hold your fire. You have two bullets for the whole game. Protection and immunity can stop your shot. A shot uses a bullet even if the target survives, unless your action is blocked.',
    night: "Shoot one player. A shot can't kill the serial killer.",
    win: 'All wolves and the lone killer are eliminated, with at least one Town player still alive.',
  },
  wolf: {
    name: 'Wolf',
    line: 'Two of them,\nand neither is Grandma.',
    ability: 'Choose one player to kill when it is your turn to carry out the attack.',
    pack: 'You know your fellow wolf and can talk privately at night. The pack attacks one player each night. Surviving wolves take turns choosing and carrying out the attack.',
    night: 'Talk with your packmate in private, then choose one player to kill.',
    nightAlone: 'Choose one player to kill. You hunt alone now.',
    win: 'The lone killer is eliminated and the surviving wolves equal or outnumber all other living players combined.',
  },
  serial_killer: {
    name: 'Serial killer',
    line: 'Waits for the carriage to fall quiet before cutting another thread.',
    ability:
      'Each night, attack one player. You cannot be killed at night or blocked, and the Investigator sees you as Not suspicious. You can still be eliminated by a daytime vote.',
    night: "Kill one player. You can't be killed at night.",
    win: 'You are alive with no more than one other player remaining.',
  },
  // The eight 1920s roles (frontend/docs/role_cards_brief.md §4). Every card's win line says
  // "the town" and "the lone killer" (the owner's ruling, 2026-10-07).
  sentinel: {
    name: 'Sentinel',
    line: 'Keeps a candle burning and an eye on the compartment door.',
    ability:
      'On up to two nights, watch one player. You privately learn who visited them that night, excluding yourself. This shows who came to them, not where they went. Visits hidden by concealment do not appear.',
    night: 'Watch one player. In the morning you learn who visited them.',
    win: 'All wolves and the lone killer are eliminated, with at least one Town player still alive.',
  },
  trailseer: {
    name: 'Trailseer',
    line: 'Follows footsteps down the corridor long after lights-out.',
    ability:
      'Each night, follow one player. You privately learn whom they visited, or that they visited no one. This shows where they went, not who came to them. Visits hidden by concealment do not appear.',
    night: 'Follow one player. You learn who they visited, or that they visited no one.',
    win: 'All wolves and the lone killer are eliminated, with at least one Town player still alive.',
  },
  sigilist: {
    name: 'Sigilist',
    line: 'Leaves a mark on the door for trouble to find on its way out.',
    ability:
      'Place a sigil on one player, or save it for later. You have two sigils. If your target attacks that night, the sigil attacks them in return without stopping their original attack. Protection and immunity can stop the retaliation; attacks through a Necromancer’s borrowed body do not trigger it. A placed sigil is spent even if nothing happens, unless your action is blocked.',
    night:
      'Place a sigil on one player. If they attack tonight, they are struck in return. Some roles are immune.',
    win: 'All wolves and the lone killer are eliminated, with at least one Town player still alive.',
  },
  chanteuse: {
    name: 'Chanteuse',
    line: 'There’s always one more song before her guest can leave.',
    ability:
      'Each night, block one player’s night action. The lone killer and neutral player cannot be blocked; you are told if your block fails. You can block on the same night you carry out the pack’s attack.',
    pack: 'You know your fellow wolf and can talk privately at night. The pack attacks one player each night. Surviving wolves take turns choosing and carrying out the attack.',
    night:
      'Discuss who to kill tonight. Also enchant one player: their night action has no effect. Some roles are immune.',
    nightAlone:
      'Choose one player to kill, and enchant one player: their night action has no effect. You hunt alone now.',
    win: 'The lone killer is eliminated and the surviving wolves equal or outnumber all other living players combined.',
  },
  illusionist: {
    name: 'Illusionist',
    line: 'When the curtain lifts, a passenger’s secret has vanished.',
    ability:
      'Twice per game, conceal the pack’s victim’s role; the whole pack learns it. This also hides the attacking wolf’s visit. Your own concealment visit remains visible unless you carried out the attack yourself. A use is spent only if the victim dies.',
    pack: 'You know your fellow wolf and can talk privately at night. The pack attacks one player each night. Surviving wolves take turns choosing and carrying out the attack.',
    night:
      "Discuss who to kill tonight. You may also conceal the victim's role and information from the morning report; the whole pack learns it.",
    nightAlone:
      'Choose one player to kill. You may also conceal their role and information from the morning report and learn it yourself. You hunt alone now.',
    win: 'The lone killer is eliminated and the surviving wolves equal or outnumber all other living players combined.',
  },
  necromancer: {
    name: 'Necromancer',
    line: 'Picks up the strings of puppets who have taken their final bow.',
    ability:
      'On Night 1, you take no action and cannot be killed. From Night 2, use an eligible dead player’s ability on a target, or take no action. You can reuse the same body; concealed bodies cannot be used.\nThe body appears as the visitor instead of you. You cannot be blocked, but from Night 2 you can be killed. The Investigator sees you as Suspicious on nights you attack.',
    night:
      "From Night 2, use a dead player's night ability on one target; with no such body, you do nothing that night. On Night 1 you do nothing, and can't be killed.",
    win: 'You are alive with no more than one other player remaining.',
  },
  speculator: {
    name: 'Speculator',
    line: 'Has a wager on who will make it to the end of the line.',
    ability:
      'On any night, back Town, the Wolves, the lone killer or yourself. You choose only once and cannot change your choice. It is announced the next morning, but your identity stays hidden. You may wait, but you lose if you die, or the game ends, before you choose.',
    night:
      'Bet once on the side that will win, or on yourself, on any night you like. Die before you bet and you lose.',
    win: 'Your chosen side wins, even if you have died. If you chose yourself, you must be the only player left alive.',
  },
  fortune_teller: {
    name: 'Fortune teller',
    line: 'Sees an empty seat in tomorrow’s carriage.',
    ability:
      'Each night, predict which player will die that night. A correct prediction earns one point, or two if you also name their role correctly. A wrong role still earns one point if the player dies.\nTwice per game, you may instead choose yourself: you earn no points, but cannot be killed that night. Your ability cannot be blocked.',
    night:
      "Predict who dies tonight: a point for the player, two with their role. Or bet on yourself: no points, but you can't be killed tonight.",
    win: 'You earn two points. Your win is kept if you die, and the game continues for the other players.',
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
    ability: 'Nothing to do. You sleep and wait for the morning report.',
    night: 'Nothing to do. You sleep and wait for the morning report.',
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  healer: {
    name: 'Healer',
    line: 'Mends what the night would tear.',
    ability: "Protect one player from being killed tonight. You can't protect yourself.",
    night: "Protect one player from being killed tonight. You can't protect yourself.",
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  investigator: {
    name: 'Investigator',
    line: 'Peeks inside one glove each night.',
    ability: "Learn one player's exact role. Only you see the result.",
    night: "Learn one player's exact role. Only you see the result.",
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  vigilante: {
    name: 'Vigilante',
    line: 'Takes the law into their own hands,\none bullet at a time.',
    ability:
      "You may shoot one player. Bullets are never reloaded, and a shot can't kill the serial killer.",
    night:
      "You may shoot one player. Bullets are never reloaded, and a shot can't kill the serial killer.",
    win: 'With the town, when both the wolves and the lone killer are gone.',
  },
  wolf: {
    name: 'Wolf',
    line: 'Two of them,\nand neither is Grandma.',
    ability: 'Talk with your packmate in private, then choose one player to kill.',
    night: 'Talk with your packmate in private, then choose one player to kill.',
    nightAlone: 'Choose one player to kill. You hunt alone now.',
    win: 'When the lone killer is gone and, at the start of a day, the wolves equal or outnumber the town.',
  },
  serial_killer: {
    name: 'Serial killer',
    line: 'Plays well with no one.\nCuts one thread each night.',
    ability: "Kill one player. You can't be killed at night.",
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
