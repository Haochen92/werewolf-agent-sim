/* Role kit — the locked role set for the Werewolf Playhouse. Locked 2026-09-22.
 * Plain JavaScript, no dependencies, the companion to the puppet kit. Draws the six role figures and sigils as SVG strings
 * and carries the card text. Keys are the wire's role names.
 *
 *   RoleKit.fig("wolf")               -> "<svg ...>"  the felt figure for the role card
 *   RoleKit.avatar("wolf")            -> "<svg ...>"  head and shoulders, for your card at rest in the game
 *   RoleKit.sigil("serial_killer")    -> "<svg ...>"  a line sigil in currentColor (set stroke width and colour in CSS)
 *   RoleKit.CARD.healer               -> { name, faction, line, day, night, win }
 *   RoleKit.FACTION                   -> faction id -> display name ("Villagers" for now)
 *
 * Locked: felt figures drawn like the puppets (glove body, mitten arms, the kit's outline, eyes and mouth, one mend),
 * human heads as eggs with no nose, no platform; the wolf in grandmother's bonnet; the ghost reaper; the green-cap
 * popgun vigilante. Sigils: house, cross, magnifier, bullet, crescent moon; the serial killer's (scythe) is still open.
 * Card text: the front line, then By day / At night / How you win, summarised from what the agents are told.
 * In the game: your card rests beside the speech box as the avatar (head and shoulders, "your card" beneath); opened, it
 * shows name and sigil, the three parts and the live fields, with no figure. The full card with figure is for the landing page.
 */
const RoleKit = (() => {
  const VERSION = "2026-09-22";
const FB = { K:'#24180c', S:3, skin:'#e4c8a4', W:'#efe4cb', X:'#3a2e24', WH:'#f6f1e4',
  body:{villager:'#6f7d5c',healer:'#6d8294',investigator:'#6b5b4b',vigilante:'#4a4f5a',wolf:'#7b4a44',killer:'#3e3656'},
  acc:{town:'#c9a25e',wolf:'#b0584c',killer:'#8f7cc0'} };
const sh=(d,f,w=FB.S)=>`<path d="${d}" fill="${f}" stroke="${FB.K}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round"/>`;
const ln=(d,c,w)=>`<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"/>`;
const st=(d,c=FB.W)=>`<path d="${d}" fill="none" stroke="${c}" stroke-width="1.2" stroke-dasharray="2.6 2.4" stroke-linecap="round" opacity=".85"/>`;
const ce=(x,y,rx,ry,f,w=FB.S,rot=0)=>`<ellipse cx="${x}" cy="${y}" rx="${rx}" ry="${ry}" fill="${f}" stroke="${FB.K}" stroke-width="${w}"${rot?` transform="rotate(${rot} ${x} ${y})"`:''}/>`;
const patchB=(x,y,w,h,rot,fab='#8b9a7a')=>`<g transform="rotate(${rot} ${x} ${y})"><rect x="${x-w/2}" y="${y-h/2}" width="${w}" height="${h}" rx="1.6" fill="${fab}" stroke="${FB.K}" stroke-width="1.4"/>${st(`M${x-w/2+2.4} ${y-h/2+2.4} h${w-4.8} v${h-4.8} h-${w-4.8} z`,'#efe4cb')}</g>`;
const HEAD='M28 52 C28 30 42 21 60 21 C78 21 92 30 92 52 C92 70 78 80 60 80 C42 80 28 70 28 52 Z';
const GLOVE='M47 74 C36 84 30 106 29 147 L91 147 C90 106 84 84 73 74 Z';
const eyesB=(x1=47,x2=73,y=51)=>[x1,x2].map(x=>`<ellipse cx="${x}" cy="${y}" rx="3" ry="3.9" fill="${FB.K}"/><circle cx="${x+.9}" cy="${y-1.5}" r="1" fill="${FB.WH}"/>`).join('');
const mouthB=(y=63)=>ln(`M54 ${y-1.5} Q57 ${y+2.5} 60 ${y-1} Q63 ${y+2.5} 66 ${y-1.5}`,FB.K,1.9);
const seamB=`${ln('M32 60 L38 70',FB.K,1)}${ln('M33 66 l3.4 -2 M35 69.5 l3.4 -2',FB.K,1)}`;
const mitt=(x,y,rot,col)=>ce(x,y,12,6.2,col,FB.S,rot);
function gloveBody(role, extra=''){ const b=FB.body[role];
  return `${sh(GLOVE,b)}${extra}${st('M33 140 H87')}${patchB(40,128,10,9,-10)}`; }
  /* the wolf keeps its own head */
  const WOLF = ()=>{ const G='#7d7670',G2='#cfc6b8',b=FB.body.wolf; return `
  ${gloveBody('wolf', sh('M36 78 Q60 68 84 78 L60 108 Z','#9a6a60',2.4)+st('M42 80 Q60 73 78 80'))}
  ${ln('M30 146 q3.8 5 7.5 0 q3.8 5 7.5 0 q3.8 5 7.5 0 q3.8 5 7.5 0 q3.8 5 7.5 0 q3.8 5 7.5 0 q3.8 5 7.5 0 q3.8 5 7.5 0',FB.W,2.2)}
  ${mitt(46,104,20,G)}${mitt(74,104,-20,G)}
  ${sh('M36 30 L32 4 L52 24 Z',G)}${sh('M66 22 L80 2 L84 30 Z',G)}
  ${sh('M30 54 C28 32 44 22 60 22 C76 22 86 30 88 42 L110 49 Q114 58 106 61 L86 66 C80 76 70 80 58 80 C40 80 31 70 30 54 Z',G)}
  <path d="M86 44 L110 49 Q114 58 106 61 L86 66 Q80 56 86 44 Z" fill="${G2}"/>${sh('M30 54 C28 32 44 22 60 22 C76 22 86 30 88 42 L110 49 Q114 58 106 61 L86 66 C80 76 70 80 58 80 C40 80 31 70 30 54 Z','none')}
  ${ce(109,53,3.2,2.6,FB.K,0)}
  ${sh('M27 62 C22 30 44 16 62 17 C76 17 82 28 82 38 C72 42 62 50 56 62 C50 74 36 74 27 62 Z',FB.W)}
  ${ln('M82 38 q-2 5 -6 4.6 q-1 5 -5.6 5.4 q0 5 -5 6.4 q.4 5 -4.2 7',FB.K,1.6)}
  ${st('M34 36 Q50 26 68 28','#b4a07c')}
  ${ln('M56 70 Q62 80 70 80',FB.K,4)}${ln('M56 70 Q62 80 70 80','#b9a48a',2)}
  <ellipse cx="74" cy="47" rx="3" ry="3.9" fill="${FB.K}"/><circle cx="74.9" cy="45.5" r="1" fill="${FB.WH}"/>
  ${ln('M90 66 Q97 70 106 63',FB.K,1.9)}<path d="M95 67.5 L96.6 71 L98.4 67.8" fill="${FB.WH}" stroke="${FB.K}" stroke-width="1"/>`; };
  /* human heads: an egg, taller than wide, eyes set low, no nose */
const EGG='M60 16 C76 16 85 33 85 52 C85 69 74 80 60 80 C46 80 35 69 35 52 C35 33 44 16 60 16 Z';
const eyesE=(y=54,a=50.5,b=69.5)=>[a,b].map(x=>`<ellipse cx="${x}" cy="${y}" rx="2.6" ry="3.4" fill="${FB.K}"/><circle cx="${x+.8}" cy="${y-1.3}" r=".9" fill="${FB.WH}"/>`).join('');
const seamE=`${ln('M38 60 L43 69',FB.K,1)}${ln('M38.6 65 l3 -1.8 M40.4 68 l3 -1.8',FB.K,1)}`;
  const mouthE=(y)=>ln(`M54.5 ${y-2} Q57.2 ${y+1.8} 60 ${y-1.4} Q62.8 ${y+1.8} 65.5 ${y-2}`,FB.K,1.8);
  const GEO = {
villager:()=>{ const b=FB.body.villager; return `
  ${ln('M100 22 V147','#5a4632',3.6)}${ln('M91 24 Q90 14 92 6 M100 24 V2 M109 24 Q110 14 108 6 M91 24 Q100 30 109 24','#5a4632',2.6)}
  ${ce(60,12,8.5,7.5,FB.X)}
  ${gloveBody('villager', sh('M40 78 Q60 70 80 78 L72 96 Q60 102 48 96 Z',FB.W,2.2))}
  ${mitt(27,96,40,b)}${mitt(96,92,-60,b)}
  ${sh(EGG,FB.skin)}
  ${sh('M36 49 C35 31 45 16 60 16 C75 16 85 31 84 49 C79 39 72 34 65 33 C61 38 51 38 44 36 C40 40 37 44 36 49 Z',FB.X)}
  ${eyesE()}${ln('M45.5 47.5 L53 49.5 M74.5 47.5 L67 49.5',FB.K,1.9)}${mouthE(69)}${seamE}`; },
healer:()=>{ const b=FB.body.healer, A=FB.acc.town; return `
  ${gloveBody('healer', sh('M46 94 H74 L78 146 L42 146 Z',FB.W,2.2)+`<path d="M57 104 H63 V113 H72 V119 H63 V128 H57 V119 H48 V113 H57 Z" fill="${A}" stroke="${FB.K}" stroke-width="1.2"/>`)}
  ${mitt(26,98,40,b)}
  ${sh('M97 96 C 104 108, 94 116, 102 128 C 107 136, 98 142, 103 148 L 97 148 C 92 140, 101 134, 96 128 C 89 118, 99 110, 92 98 Z',FB.W,1.6)}
  ${mitt(94,92,-40,b)}${ce(99,86,7,6,FB.W,2.2)}${ce(99,86,2.4,2,FB.X,0)}
  ${sh(EGG,FB.skin)}
  ${sh('M34.5 50 C34 30 45 12 60 12 C75 12 86 30 85.5 50 C77 41 69 38 60 38 C51 38 43 41 34.5 50 Z',FB.W)}
  ${st('M40 32 Q60 20 80 32','#b4a07c')}
  ${sh('M83 40 L96 33 L94 47 Z',FB.W,2)}${sh('M83 44 L94 53 L84 55 Z',FB.W,2)}
  ${eyesE(56)}${mouthE(70.5)}${seamE}`; },
investigator:()=>{ const b=FB.body.investigator; return `
  ${gloveBody('investigator', ln('M49 76 L56 92 L60 82 L64 92 L71 76',FB.K,2)+[98,112,126].map(y=>`<circle cx="60" cy="${y}" r="2.6" fill="${FB.X}"/>`).join(''))}
  ${mitt(26,98,40,b)}
  ${sh(EGG,FB.skin)}
  ${ce(60,27,30,5,FB.X)}${sh('M42 27 Q43 3 60 4 Q77 3 78 27 Z',FB.X)}${ln('M43.4 22 Q60 25 76.6 22','#b9a48a',2.2)}
  <ellipse cx="50" cy="54" rx="2.6" ry="3.4" fill="${FB.K}"/><circle cx="50.8" cy="52.7" r=".9" fill="${FB.WH}"/>
  ${ln('M80 64 L96 80','#5a4632',6)}
  ${ce(71,53,11,11,FB.W,3)}${ce(71,54,4.6,5.6,FB.K,0)}<circle cx="72.8" cy="51.4" r="1.6" fill="${FB.WH}"/>
  ${mitt(96,84,-50,b)}
  ${mouthE(69)}${seamE}`; },
vigilante:()=>{ const b=FB.body.vigilante, A=FB.acc.town, G='#6d8a4e', G2='#56703c'; return `
  ${gloveBody('vigilante', sh('M44 118 Q42 132 49 133 Q56 132 54 118 Z','#b9a48a',1.6)+ln('M31 116 H89',FB.K,3))}
  ${ln('M52 112 L100 62',FB.K,11.5)}${ln('M52 112 L100 62','#8b9a7a',8)}${ln('M89 73.5 L93.5 78',FB.K,2.2)}
  ${sh('M101 55 L109 63 L104 68 L96 60 Z','#c9a878',1.8)}${ln('M106 66 C 112 78, 100 88, 90 84',FB.K,1)}
  ${mitt(40,106,-20,b)}${mitt(74,92,-40,b)}
  ${sh('M42 74 Q60 82 78 74 L77 80 Q60 88 43 80 Z',A,2)}${sh('M44 78 Q34 86 30 98 L35 100 Q40 90 47 83 Z',A,2)}
  ${sh(EGG,FB.skin)}
  ${sh('M81 27 C84 12 91 1 101 -9 C100 4 94 17 88 29 Z','#b8574a',1.8)}${ln('M84 26 Q91 10 100 -7',FB.K,1)}
  ${sh('M23 45 C32 31 48 17 68 12 C80 9 88 15 89 25 L91 35 C74 36 50 40 23 45 Z',G)}
  ${ln('M38 36 Q54 22 74 14',G2,2)}${st('M46 30 Q60 20 76 17','#c9d3a8')}
  ${sh('M21 47 L26 41 C46 35 70 31 88 27 L98 21 L93 36 C71 38 46 42 21 47 Z','#87a463',2.2)}
  ${st('M29 43.5 C48 38.5 70 35 90 32','#56703c')}
  ${sh('M36 51 Q48 45 60 50 Q72 45 84 51 Q85 61 73 60 Q65 60 60 56 Q55 60 47 60 Q35 61 36 51 Z',FB.X,2)}
  <circle cx="49.5" cy="53.5" r="2.8" fill="${FB.W}"/><circle cx="70.5" cy="53.5" r="2.8" fill="${FB.W}"/>
  ${mouthE(71)}`; },
  };
  GEO.wolf = WOLF;
  const GEOB2 = GEO;
  GEOB2.reaper = ()=>{ const R1='#2b2433', IN='#140f18', GH='#eeeae0', A=FB.acc.killer; return `
  ${ln('M99 147 L94 -8',FB.K,6.4)}${ln('M99 147 L94 -8','#5a4632',3.6)}
  ${sh('M95 -6 C74 -15 46 -10 30 6 C50 -2 72 -3 95.5 4 Z','#dcd6ca',2.4)}${ln('M44 -4 Q62 -10 80 -9',A,1.8)}
  ${sh('M44 70 C32 84 26 112 24 140 q6 8 12 0 q6 8 12 0 q6 8 12 0 q6 8 12 0 q6 8 12 0 C94 112 88 84 76 70 Z',R1)}
  ${st('M32 128 Q60 134 88 128','#8f86a8')}${patchB(42,116,10,9,-10)}
  ${sh('M60 12 C82 12 94 32 93 56 C92 72 84 82 72 84 L48 84 C36 82 28 72 27 56 C26 32 38 12 60 12 Z',R1)}
  <path d="M60 26 C74 26 82 40 82 54 C82 67 72 76 60 76 C48 76 38 67 38 54 C38 40 46 26 60 26 Z" fill="${IN}"/>
  ${sh('M60 31 C71 31 78 42 78 54 C78 65 70 72 60 72 C50 72 42 65 42 54 C42 42 49 31 60 31 Z',GH,1.6)}
  <ellipse cx="52.5" cy="53" rx="2.6" ry="3.4" fill="${FB.K}"/><circle cx="53.3" cy="51.7" r=".9" fill="${FB.WH}"/>
  <ellipse cx="67.5" cy="53" rx="2.6" ry="3.4" fill="${FB.K}"/><circle cx="68.3" cy="51.7" r=".9" fill="${FB.WH}"/>
  ${ln('M55.5 62.5 Q58 65.5 60 63 Q62 65.5 64.5 62.5',FB.K,1.8)}
  ${st('M36 40 Q60 22 84 40','#8f86a8')}
  ${mitt(29,98,55,R1)}<circle cx="22" cy="90" r="4.6" fill="${GH}" stroke="${FB.K}" stroke-width="2"/>
  ${mitt(92,94,-70,R1)}`; };
  GEO.serial_killer = GEO.reaper;
  const VIEW = { serial_killer: "2 -18 118 170" };
  const fig = (role) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="${VIEW[role] || "2 -8 118 160"}" aria-hidden="true">${GEO[role]()}</svg>`;

  const SIG = {
    villager:'<path d="M6 20 L20 8 L34 20 M10 18 V32 H30 V18 M17 32 V24 H23 V32"/>',
    healer:'<path d="M16 7 H24 V16 H33 V24 H24 V33 H16 V24 H7 V16 H16 Z"/>',
    investigator:'<circle cx="17" cy="17" r="9"/><path d="M24 24 L34 34"/>',
    vigilante:'<path d="M14.5 29 V17 Q14.5 7.5 20 5.5 Q25.5 7.5 25.5 17 V29 Z"/><path d="M14.5 23 H25.5"/><path d="M12 33 H28"/>',
    wolf:'<path d="M25 5 A15.5 15.5 0 1 0 35 27 A12 12 0 0 1 25 5 Z"/>',
    serial_killer:'<path d="M30 37 L24 4"/><path d="M24.5 5 C14 2 5 8 4 19 C9 11.5 16 9.5 25.3 11"/>',
  };
  const sigil = (role) => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${SIG[role]}</svg>`;

  const FACTION = { villagers: "Villagers", wolves: "Wolves", serial_killer: "Serial killer" };
  const CARD = {
    villager:{ name:'Villager', faction:'villagers', line:'No tricks up their sleeve.<br>Only wits and a vote.',
      day:'Push for concrete reads and ask for the reasons behind them. It\'s fine to hold off rather than invent a suspicion. The voting record is your hardest evidence.',
      night:'Nothing to do. You sleep and wait for the morning report.', win:'With the villagers, when both the wolves and the serial killer are gone.' },
    healer:{ name:'Healer', faction:'villagers', line:'Mends what the night would tear.',
      day:'Blend in like any villager. Too directive draws attention, and too quiet looks like a power role hiding.',
      night:'Protect one player from being killed tonight. You can\'t protect yourself.', win:'With the villagers, when both the wolves and the serial killer are gone.' },
    investigator:{ name:'Investigator', faction:'villagers', line:'Peeks inside one glove each night.',
      day:'A result only helps once the village acts on it. Revealing can rally them, and it also marks you for the night.',
      night:'Learn one player\'s exact role. Only you see the result.', win:'With the villagers, when both the wolves and the serial killer are gone.' },
    vigilante:{ name:'Vigilante', faction:'villagers', line:'Takes the law into their own hands,<br>one bullet at a time.',
      day:'Vote like any villager, and watch who deserves one of your few bullets. A target who survives your shot tells you something.',
      night:'You may shoot one player. Bullets are never reloaded, and a shot can\'t kill the serial killer.', win:'With the villagers, when both the wolves and the serial killer are gone.' },
    wolf:{ name:'Wolf', faction:'wolves', line:'Two of them,<br>and neither is Grandma.',
      day:'Offer genuine, specific reasoning and vote with the majority. A protest vote is a permanent record.',
      night:'Talk with your packmate in private, then choose one player to kill.', nightAlone:'Choose one player to kill. You hunt alone now.',
      win:'When the serial killer is gone and, at the start of a day, the wolves equal or outnumber the villagers.' },
    serial_killer:{ name:'Serial killer', faction:'serial_killer', line:'Plays well with no one.<br>Cuts one thread each night.',
      day:'Blend in as an ordinary villager, neither dominating the talk nor vanishing from it. Only a day vote can remove you.',
      night:'Kill one player. You can\'t be killed at night.', win:'Alone, when at most one other player is left alive.' },
  };
  /* the card at rest in the game: the figure cropped to head and shoulders (the opened card carries no figure) */
  const CROP = { serial_killer: "14 -20 92 100", wolf: "20 -12 96 100" };
  const avatar = (role) => fig(role).replace(/viewBox="[^"]*"/, `viewBox="${CROP[role] || "14 -10 92 96"}" preserveAspectRatio="xMidYMin slice"`);
  const ROLES = Object.keys(CARD);
  return { VERSION, ROLES, CARD, FACTION, fig, avatar, sigil };
})();
