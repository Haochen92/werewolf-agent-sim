/* Puppet kit — the locked avatar cast for the Werewolf Playhouse. Locked 2026-09-21; dressed and re-locked 2026-09-22.
 * Plain JavaScript, no dependencies. One shared felt glove, eleven heads, drawn as inline SVG.
 *
 *   PuppetKit.svg("whale", { seat: 6 })                                  -> "<svg ...>" string
 *   PuppetKit.svg("shade", { seat: 3, look: "right", state: "talking" })
 *   PuppetKit.svg("owl",   { variant: "chip" })                          -> tight 28:36 crop for the transcript chip
 *   PuppetKit.castForGame(gameId)                                        -> nine ids, index 0 is seat 1, stable per game
 *   PuppetKit.svg("owl", { dress: false })                               -> the bare glove, without the character's outfit
 *   PuppetKit.OUTFIT.owl                                                 -> { who, hat, neck, cloth, obj }, names for the outfit
 *
 * Locked: the cast, the face (dot eyes, little smile, mended), the dyed-felt colours, seat numeral on the belly,
 * and (2026-09-22) one fixed outfit per character: hat, neck item, clothes on the glove, favourite object.
 * Proposals, first guesses only: opts.look ("left" | "right") and opts.state ("talking" | "out").
 * The kit draws only the puppet, flat and evenly lit. Light, shadow and motion belong to the scene
 * (CSS transforms on the returned <svg> are fine: bob, tilt, drop below the playboard).
 */
const PuppetKit = (() => {
  const VERSION = "2026-09-22";
  const IDS = ["owl", "hare", "cat", "badger", "cyclops", "threeEyes", "dragon", "onion", "whale", "polarBear", "shade"];
  const NAMES = { owl: "Owl", hare: "Hare", cat: "Cat", badger: "Badger", cyclops: "Cyclops", threeEyes: "Three-eyes",
    dragon: "Dragon", onion: "Onion", whale: "Whale", polarBear: "Polar bear", shade: "Shade" };

  /* Nine of the eleven for a game, from a hash of the game id, so a replay matches the live game
     and nothing has to be added to the wire contract. */
  function castForGame(gameId, seats = 9) {
    let h = 2166136261;
    for (let i = 0; i < gameId.length; i++) { h ^= gameId.charCodeAt(i); h = Math.imul(h, 16777619); }
    let s = h >>> 0;
    const rnd = () => {
      s = (s + 0x6d2b79f5) | 0;
      let t = Math.imul(s ^ (s >>> 15), 1 | s);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const pool = IDS.slice();
    for (let i = pool.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [pool[i], pool[j]] = [pool[j], pool[i]]; }
    return pool.slice(0, seats);
  }

  /* ---------- colour ---------- */
  const INK = "#24180c", WHITE = "#f6f1e4";
  const SAGE = "#8b9a7a", BLUE = "#7f93a3", OAT = "#b9a48a";            // patch fabrics
  const pal = (main, belly, dark, accent, nose, inner = belly, body = main) => ({ main, body, belly, light: belly, dark, accent, nose, inner });
  const rgb = (h) => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const hex = (a) => "#" + a.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("");
  const mix = (a, b, t) => { const x = rgb(a), y = rgb(b); return hex(x.map((v, i) => v + (y[i] - v) * t)); };
  const lum = (h) => { const c = rgb(h); return (0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]) / 255; };
  const thread = (on) => (lum(on) > 0.3 ? mix(on, INK, 0.5) : mix(on, WHITE, 0.55));   // a thread that shows on this felt

  /* ---------- geometry ---------- */
  const W = 210, H = 240, CX = 105, CY = 104;
  const r1 = (v) => Math.round(v * 10) / 10;
  const p = (s, ...v) => s.reduce((a, str, i) => a + str + (i < v.length ? r1(v[i]) : ""), "");   // path template, rounds numbers

  function tools(g) {
    const { S, F, cx } = g;
    const shape = (d, fill, sw = S) => `<path d="${d}" fill="${fill}" stroke="${INK}" stroke-width="${r1(sw)}" stroke-linejoin="round" stroke-linecap="round"/>`;
    const flat = (d, fill) => `<path d="${d}" fill="${fill}"/>`;
    const line = (d, col, w, dash) => `<path d="${d}" fill="none" stroke="${col}" stroke-width="${r1(w)}" stroke-linecap="round" stroke-linejoin="round"${dash ? ` stroke-dasharray="${dash}"` : ""}/>`;
    const tube = (ds, col, w) => ds.map((d) => line(d, INK, w + 2 * S)).join("") + ds.map((d) => line(d, col, w)).join("");   // felt tube with an ink outline
    const mirror = (s) => s + `<g transform="translate(${2 * cx},0) scale(-1,1)">${s}</g>`;
    const stroke = (sw) => (sw ? ` stroke="${INK}" stroke-width="${r1(sw)}"` : "");
    const circ = (x, y, r, fill, sw = S) => `<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(r)}" fill="${fill}"${stroke(sw)}/>`;
    const ell = (x, y, a, b, fill, sw = S, rot) => `<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(a)}" ry="${r1(b)}" fill="${fill}"${stroke(sw)}${rot ? ` transform="rotate(${rot} ${r1(x)} ${r1(y)})"` : ""}/>`;
    const dash = `${r1(F * 2.6)} ${r1(F * 2.6)}`;
    const stitch = (d, on) => (F ? line(d, thread(on), F, dash) : "");
    const ring = (x, y, a, b, on) => (F ? `<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(a)}" ry="${r1(b)}" fill="none" stroke="${thread(on)}" stroke-width="${F}" stroke-dasharray="${dash}" stroke-linecap="round"/>` : "");
    const seam = (x1, y1, x2, y2, n, col, len) => {                        // a sewn seam: a line with cross ticks
      if (!F) return "";
      const dx = x2 - x1, dy = y2 - y1, L = Math.hypot(dx, dy), px = (-dy / L) * len, py = (dx / L) * len;
      let s = line(p`M${x1},${y1} L${x2},${y2}`, col, F * 1.2);
      for (let i = 1; i <= n; i++) { const t = i / (n + 1), x = x1 + dx * t, y = y1 + dy * t; s += line(p`M${x - px},${y - py} L${x + px},${y + py}`, col, F * 1.2); }
      return s;
    };
    const chin = (top) => {                                                // a pale lower face, drawn inside the head clip
      const { cy, rx, ry, c } = g;
      return flat(p`M${cx - rx},${cy + ry * top} Q${cx},${cy + ry * (top - 0.34)} ${cx + rx},${cy + ry * top} L${cx + rx},${cy + ry * 1.2} L${cx - rx},${cy + ry * 1.2} Z`, c.light);
    };
    const patch = (x, y, w, h, rot, fab, rad) => `<g transform="rotate(${rot} ${r1(x)} ${r1(y)})"><rect x="${r1(x - w / 2)}" y="${r1(y - h / 2)}" width="${w}" height="${h}" rx="${rad}" fill="${fab}" stroke="${INK}" stroke-width="${r1(S * 0.5)}"/>`
      + (F ? `<rect x="${r1(x - w / 2 + 3.7)}" y="${r1(y - h / 2 + 3.7)}" width="${r1(w - 7.4)}" height="${r1(h - 7.4)}" rx="2" fill="none" stroke="${thread(fab)}" stroke-width="${F}" stroke-dasharray="${dash}"/>` : "") + `</g>`;
    return { shape, flat, line, tube, mirror, circ, ell, stitch, ring, seam, chin, patch, dash };
  }

  /* ---------- the eleven heads ----------
     back: behind glove and head (ears, horns, wings).  face: markings, clipped to the head.  front: noses and beaks. */
  const CAST = {
    owl: {
      rx: 58, ry: 52, patch: BLUE, beak: true,
      c: pal("#7a6650", "#dccaa4", "#4f4030", "#a88a5c", "#1c120a", "#a88a5c"),
      back: ({ cx, cy, rx, ry, c }, t) => t.mirror(t.shape(p`M${cx - rx * 0.88},${cy - ry * 0.3} L${cx - rx * 0.95},${cy - ry * 1.24} L${cx - rx * 0.2},${cy - ry * 0.85} Z`, c.main)),
      face: ({ cx, rx, c, E }, t) => t.mirror(t.circ(cx - rx * 0.42, E[0].y, rx * 0.4, c.light, 0) + t.ring(cx - rx * 0.42, E[0].y, rx * 0.4 - 4, rx * 0.4 - 4, c.light)),
      front: ({ cx, cy, ry, c, S }, t) => t.shape(p`M${cx - 8},${cy + ry * 0.04} L${cx + 8},${cy + ry * 0.04} L${cx},${cy + ry * 0.04 + 17} Z`, c.accent, S * 0.8),
    },
    hare: {
      rx: 58, ry: 52, patch: SAGE,
      c: pal("#a9784a", "#ead8b6", "#6e4a2a", "#ead8b6", "#3a2416", "#e0b9a6"),   // the stag's fawn
      back: ({ cx, cy, rx, ry, c }, t) => { const ty = 8; return (
        t.shape(p`M${cx - rx * 0.68},${cy - ry * 0.5} C${cx - rx},${ty + 34} ${cx - rx * 0.85},${ty} ${cx - rx * 0.5},${ty} C${cx - rx * 0.18},${ty} ${cx - rx * 0.08},${ty + 34} ${cx - rx * 0.16},${cy - ry * 0.78} Z`, c.main)
        + t.ell(cx - rx * 0.5, ty + 30, 6, 19, c.inner, 0)
        + t.shape(p`M${cx + rx * 0.14},${cy - ry * 0.78} C${cx + rx * 0.08},${ty + 42} ${cx + rx * 0.3},${ty + 12} ${cx + rx * 0.66},${ty + 12} C${cx + rx * 1.2},${ty + 12} ${cx + rx * 1.55},${ty + 46} ${cx + rx * 1.42},${ty + 80} C${cx + rx * 1.2},${ty + 54} ${cx + rx * 0.98},${ty + 40} ${cx + rx * 0.7},${ty + 42} L${cx + rx * 0.62},${cy - ry * 0.5} Z`, c.main)
        + t.line(p`M${cx + rx * 0.56},${ty + 27} Q${cx + rx},${ty + 26} ${cx + rx * 1.26},${ty + 52}`, c.inner, 7)); },
      face: ({ cx, cy, rx, ry, c }, t) => t.ell(cx, cy + ry * 0.5, rx * 0.46, ry * 0.42, c.light, 0),
      front: ({ cx, cy, ry, c, S }, t) => { const y = cy + ry * 0.2; return t.shape(p`M${cx - 6},${y - 3} L${cx + 6},${y - 3} L${cx},${y + 5} Z`, c.nose, S * 0.66); },
    },
    cat: {
      rx: 58, ry: 52, patch: OAT, seamOn: "dark",
      c: pal("#7d8590", "#cfd3d7", "#565d68", "#c9958c", "#c9958c", "#c9958c"),
      back: ({ cx, cy, rx, ry, c }, t) => t.mirror(
        t.shape(p`M${cx - rx * 0.95},${cy - ry * 0.25} L${cx - rx * 0.86},${cy - ry * 1.32} L${cx - rx * 0.16},${cy - ry * 0.9} Z`, c.main)
        + t.flat(p`M${cx - rx * 0.8},${cy - ry * 0.6} L${cx - rx * 0.76},${cy - ry * 1.1} L${cx - rx * 0.42},${cy - ry * 0.9} Z`, c.inner)),
      face: ({ cx, cy, rx, ry, c }, t) => t.line(p`M${cx},${cy - ry} L${cx},${cy - ry * 0.55}`, c.dark, 7)
        + t.mirror(t.line(p`M${cx - 15},${cy - ry} L${cx - 14},${cy - ry * 0.66}`, c.dark, 6)
          + t.line(p`M${cx - rx},${cy + ry * 0.12} L${cx - rx * 0.72},${cy + ry * 0.16}`, c.dark, 6)
          + t.line(p`M${cx - rx},${cy + ry * 0.4} L${cx - rx * 0.78},${cy + ry * 0.4}`, c.dark, 6))
        + t.ell(cx, cy + ry * 0.5, rx * 0.4, ry * 0.36, c.light, 0),
      front: ({ cx, cy, rx, ry, c, S, F }, t) => { const y = cy + ry * 0.2; return (
        t.shape(p`M${cx - 5.5},${y - 2} L${cx + 5.5},${y - 2} L${cx},${y + 5} Z`, c.nose, S * 0.66)
        + (F ? t.mirror(t.line(p`M${cx - rx * 0.42},${cy + ry * 0.42} L${cx - rx * 1.12},${cy + ry * 0.3}`, INK, F * 0.9)
          + t.line(p`M${cx - rx * 0.42},${cy + ry * 0.56} L${cx - rx * 1.1},${cy + ry * 0.66}`, INK, F * 0.9)) : "")); },
    },
    badger: {
      rx: 58, ry: 52, patch: SAGE, eyeOnDark: true, scarOn: "dark",
      c: pal("#ece6d8", "#cfcabd", "#2b2b31", "#17161a", "#17161a", "#cfcabd", "#5b5b63"),
      back: ({ cx, cy, rx, ry, c }, t) => t.mirror(t.circ(cx - rx * 0.72, cy - ry * 0.76, 13, c.dark) + t.circ(cx - rx * 0.72, cy - ry * 0.76, 5.5, c.inner, 0)),
      face: ({ cx, cy, rx, ry, c }, t) => t.mirror(t.flat(p`M${cx - rx * 0.58},${cy - ry * 1.1} L${cx - rx * 0.16},${cy - ry * 1.1} L${cx - rx * 0.2},${cy + ry * 0.05} L${cx - rx * 0.5},${cy + ry * 0.8} L${cx - rx * 1.15},${cy + ry * 0.55} L${cx - rx * 0.8},${cy - ry * 0.2} Z`, c.dark)),
      front: ({ cx, cy, ry, c, S }, t) => t.ell(cx, cy + ry * 0.2 + 2, 9, 6.5, c.nose, S * 0.66),
    },
    cyclops: {
      rx: 68, ry: 46, patch: BLUE, mouthY: 0.62, mouthW: 1.25, wideSmile: true,
      c: pal("#b8a58c", "#e9dfcc", "#8d7a60", "#efe4cb", "#4a3a2a"),
      eyes: (cx, cy, rx, ry) => [{ x: cx, y: cy - ry * 0.14, k: 1.5 }],
      back: ({ cx, cy, rx, ry, c }, t) => t.mirror(t.shape(p`M${cx - rx * 0.66},${cy - ry * 0.6} Q${cx - rx * 0.72},${cy - ry * 1.42} ${cx - rx * 0.5},${cy - ry * 1.44} Q${cx - rx * 0.3},${cy - ry * 1.36} ${cx - rx * 0.3},${cy - ry * 0.8} Z`, c.accent)),
      face: (g, t) => t.chin(0.64),
    },
    threeEyes: {
      rx: 48, ry: 60, patch: OAT,
      c: pal("#5f8a8b", "#c3d8d2", "#446667", "#efe4cb", "#2c4445"),             // dusty teal, clear of the whale
      eyes: (cx, cy, rx, ry) => { const e = rx * 0.46, y = cy - ry * 0.08; return [{ x: cx - e, y: y + 6, k: 0.8 }, { x: cx + e, y: y + 6, k: 0.8 }, { x: cx, y: y - 24, k: 0.8 }]; },
      back: ({ cx, cy, ry, c }, t) => t.tube([p`M${cx + 2},${cy - ry + 6} C${cx + 2},${cy - ry - 14} ${cx + 10},${cy - ry - 24} ${cx + 22},${cy - ry - 25}`], c.main, 5) + t.circ(cx + 24, cy - ry - 25, 8.5, c.accent),
    },
    dragon: {
      rx: 58, ry: 54, patch: OAT, mouthY: 0.64,
      c: pal("#6f8250", "#ead8b6", "#4f5f38", "#efe4cb", "#2f3a20", "#7f93a3"),
      eyes: (cx, cy, rx, ry) => { const e = rx * 0.44, y = cy - ry * 0.26; return [{ x: cx - e, y, k: 0.9 }, { x: cx + e, y, k: 0.9 }]; },
      back: ({ cx, cy, rx, ry, ny, c, F }, t) => t.mirror(
        t.shape(p`M${cx - 44},${ny + 16} L${cx - 97},${ny - 36} Q${cx - 102},${ny - 4} ${cx - 93},${ny + 14} Q${cx - 83},${ny + 3} ${cx - 77},${ny + 18} Q${cx - 67},${ny + 7} ${cx - 58},${ny + 22} Z`, c.inner)
        + (F ? t.line(p`M${cx - 50},${ny + 12} L${cx - 92},${ny + 12}`, mix(c.inner, INK, 0.45), F * 1.2) + t.line(p`M${cx - 50},${ny + 10} L${cx - 95},${ny - 12}`, mix(c.inner, INK, 0.45), F * 1.2) : "")
        + t.shape(p`M${cx - rx * 0.9},${cy - ry * 0.45} L${cx - rx - 24},${cy - ry * 0.72} L${cx - rx - 15},${cy - ry * 0.3} L${cx - rx - 28},${cy - ry * 0.08} L${cx - rx - 13},${cy + ry * 0.1} L${cx - rx * 0.95},${cy + ry * 0.12} Z`, c.inner)
        + t.shape(p`M${cx - rx * 0.52},${cy - ry * 0.76} Q${cx - rx * 0.78},${cy - ry * 1.34} ${cx - rx * 0.42},${cy - ry * 1.5} Q${cx - rx * 0.2},${cy - ry * 1.2} ${cx - rx * 0.18},${cy - ry * 0.9} Z`, c.accent)),
      face: ({ cx, cy, rx, ry, c }, t) => t.ell(cx, cy + ry * 0.46, rx * 0.68, ry * 0.5, c.light, 0),
      front: ({ cx, cy, ry, c }, t) => t.mirror(t.ell(cx - 9, cy + ry * 0.2, 2.4, 3.2, c.nose, 0)),
    },
    onion: {
      rx: 56, ry: 50, patch: SAGE,
      c: pal("#ece0c4", "#fbf5e6", "#c4b38e", "#c4b38e", "#6e5f42"),
      eyes: (cx, cy, rx, ry) => { const e = rx * 0.27, y = cy - ry * 0.04; return [{ x: cx - e, y, k: 0.85 }, { x: cx + e, y, k: 0.85 }]; },
      headPath: ({ cx, cy, rx, ry }) => { const k = 0.5523; return p`M${cx},${cy - ry - 24} C${cx + 6},${cy - ry - 6} ${cx + rx},${cy - ry * 0.78} ${cx + rx},${cy} C${cx + rx},${cy + ry * k * 1.25} ${cx + rx * k * 1.15},${cy + ry} ${cx},${cy + ry} C${cx - rx * k * 1.15},${cy + ry} ${cx - rx},${cy + ry * k * 1.25} ${cx - rx},${cy} C${cx - rx},${cy - ry * 0.78} ${cx - 6},${cy - ry - 6} ${cx},${cy - ry - 24} Z`; },
      back: ({ cx, cy, ry, c }, t) => t.tube([p`M${cx},${cy - ry - 20} c9,-5 11,-17 0,-17 c-6,0 -7,7 -2,9`], c.main, 4),
      face: ({ cx, cy, rx, ry, c }, t) => t.circ(cx - rx * 0.58, cy - ry * 0.42, 6, c.dark, 0) + t.circ(cx + rx * 0.2, cy - ry * 0.74, 4, c.dark, 0) + t.circ(cx + rx * 0.7, cy + ry * 0.08, 4.5, c.dark, 0)
        + t.circ(cx - rx * 0.72, cy + ry * 0.26, 4.5, c.dark, 0) + t.circ(cx + rx * 0.5, cy + ry * 0.62, 3.5, c.dark, 0),
    },
    whale: {
      rx: 70, ry: 46, patch: SAGE, mouthY: 0.38, mouthW: 1.7, wideSmile: true, cropUp: 6,
      c: pal("#4f6a86", "#dfe8ea", "#3a5068", "#a9d3da", "#22303f"),
      eyes: (cx, cy, rx) => { const e = rx * 0.68; return [{ x: cx - e, y: cy, k: 0.7 }, { x: cx + e, y: cy, k: 0.7 }]; },
      back: ({ cx, cy, ry, c }, t) => { const y = cy - ry; return t.tube([p`M${cx},${y + 4} L${cx},${y - 12}`,
        p`M${cx},${y - 12} C${cx - 2},${y - 30} ${cx - 22},${y - 30} ${cx - 25},${y - 15}`, p`M${cx},${y - 12} C${cx + 2},${y - 30} ${cx + 22},${y - 30} ${cx + 25},${y - 15}`], c.accent, 6); },
      face: ({ cx, cy, rx, ry, c, F }, t) => t.chin(0.46) + t.circ(cx - rx * 0.2, cy - ry * 0.55, 4, c.dark, 0) + t.circ(cx + rx * 0.32, cy - ry * 0.4, 3, c.dark, 0)
        + (F ? t.line(p`M${cx - 30},${cy + ry * 0.66} Q${cx},${cy + ry * 0.8} ${cx + 30},${cy + ry * 0.66}`, thread(c.light), F) + t.line(p`M${cx - 20},${cy + ry * 0.84} Q${cx},${cy + ry * 0.94} ${cx + 20},${cy + ry * 0.84}`, thread(c.light), F) : ""),
    },
    polarBear: {
      rx: 54, ry: 56, patch: BLUE, mouthY: 0.42, brows: "worried",
      c: pal("#edf0ef", "#fafbfa", "#b4bcc0", "#c9d3d8", "#5a4a3a", "#c9d3d8"),
      eyes: (cx, cy, rx) => { const e = rx * 0.5; return [{ x: cx - e, y: cy, k: 0.75 }, { x: cx + e, y: cy, k: 0.75 }]; },
      back: ({ cx, cy, rx, ry, c }, t) => t.mirror(t.circ(cx - rx * 0.62, cy - ry * 0.86, 10.5, c.main) + t.circ(cx - rx * 0.62, cy - ry * 0.86, 4.5, c.inner, 0)),
      front: ({ cx, cy, ry, c, S }, t) => t.ell(cx, cy + ry * 0.2, 5, 3.8, c.nose, S * 0.5),
    },
    shade: {
      rx: 66, ry: 48, patch: OAT, mouthY: 0.56, brows: "cross", eyeOnDark: true, mouthOnDark: true,
      c: pal("#454c5c", "#8a93a6", "#2e3340", "#8a93a6", "#1a1d26"),
      eyes: (cx, cy, rx, ry) => { const e = rx * 0.42, y = cy - ry * 0.04; return [{ x: cx - e, y, k: 0.95 }, { x: cx + e, y, k: 0.95 }]; },
      back: ({ cx, cy, ry, c }, t) => { const y = cy - ry; return (
        t.shape(p`M${cx - 32},${y + 12} C${cx - 44},${y - 8} ${cx - 26},${y - 22} ${cx - 15},${y - 9} C${cx - 13},${y - 31} ${cx + 10},${y - 36} ${cx + 14},${y - 15} C${cx + 22},${y - 30} ${cx + 45},${y - 24} ${cx + 35},${y - 5} C${cx + 42},${y - 1} ${cx + 40},${y + 10} ${cx + 32},${y + 12} Z`, c.main)
        + t.circ(cx + 50, y - 27, 6.5, c.main) + t.circ(cx + 61, y - 40, 3.5, c.main)); },
    },
  };

  /* Seat numerals as single stitched strokes in a 20 x 30 box, so they need no font. */
  const DIGITS = { 1: "M6,7 L11,2 L11,28 M5,28 L17,28", 2: "M3,8 C3,0 17,0 17,8 C17,14 8,20 3,28 L18,28", 3: "M3,3 L17,3 L9,13 C18,13 19,28 9,28 C5,28 3,26 2,23",
    4: "M14,28 L14,2 L2,20 L19,20", 5: "M17,2 L5,2 L4,13 C10,10 18,13 18,20 C18,29 6,30 3,24", 6: "M16,3 C8,4 3,12 3,20 C3,30 18,30 18,20 C18,12 6,12 3,19",
    7: "M2,2 L18,2 L8,28", 8: "M10,14 C2,12 3,2 10,2 C17,2 18,12 10,14 C1,16 2,28 10,28 C18,28 19,16 10,14", 9: "M17,11 C14,19 2,18 2,10 C2,0 17,0 17,10 C17,18 14,26 5,28" };

  const roundHead = ({ cx, cy, rx, ry }) => { const k = 0.5523;   // a little heavier below the middle, so every head has cheeks
    return p`M${cx - rx},${cy} C${cx - rx},${cy - ry * k} ${cx - rx * k},${cy - ry} ${cx},${cy - ry} C${cx + rx * k},${cy - ry} ${cx + rx},${cy - ry * k} ${cx + rx},${cy} C${cx + rx},${cy + ry * k * 1.25} ${cx + rx * k * 1.15},${cy + ry} ${cx},${cy + ry} C${cx - rx * k * 1.15},${cy + ry} ${cx - rx},${cy + ry * k * 1.25} ${cx - rx},${cy} Z`; };


  /* ---------- outfits (dressed 2026-09-22) ----------
     Every character wears a fixed outfit, part of its design: a hat, a neck item, clothes on the glove,
     and a favourite object in the right mitten. The glove's shape stays shared. Rule for every item:
     nothing that hints at a role (no role props, no role hats or clothing, no faction colours, no sigil
     shapes, no basket). Clothes are masked to the glove body, clear of the head, the belly patch and its numeral.
     Everything stays inside the 210 x 240 canvas, and nothing covers the mouth. */
  const Dress = (() => {
  const K='#24180c', WH='#f6f1e4', CREAM='#efe4cb', SAGE='#8b9a7a', BLUE='#7f93a3', OAT='#b9a48a', ROSE='#c9958c', PEWTER='#c9ced2', WOOD='#8b6a4a', DENIM='#6e86a0', BUTTER='#eadb9e', STRAW='#d8c48f', NAVY='#3e5470';
  const CX=105, CY=104;

  const OUTFIT = {
    owl:{who:'Tea-loving elder', hat:'Small beret', neck:'Bow tie', cloth:'Tweed waistcoat', obj:'Teacup and saucer'},
    hare:{who:'Gardener', hat:'Straw sunhat', neck:'Daisy chain', cloth:'Denim dungarees', obj:'Watering can'},
    cat:{who:'Pampered housecat', hat:'Bow on one ear', neck:'Bell collar', cloth:'Striped jumper', obj:'Ball of yarn'},
    badger:{who:'Woodland forager', hat:'Pompom beanie', neck:'Acorn pendant', cloth:'Cable-knit jumper', obj:'Mushroom'},
    cyclops:{who:'Theatre ham', hat:'Laurel wreath', neck:'Theatre ruff', cloth:'Harlequin diamonds', obj:'Bouquet'},
    threeEyes:{who:'Tinkerer', hat:'Ribbon on the antenna', neck:'Wooden beads', cloth:'Zigzag knit', obj:'Pinwheel'},
    dragon:{who:'Little royal', hat:'Felt crown', neck:'Ermine collar', cloth:'Scales', obj:'Dragon egg'},
    onion:{who:'Picnic-goer', hat:'Straw boater', neck:'Round lace collar', cloth:'Gingham', obj:'Balloon'},
    whale:{who:'Sailor', hat:'Sailor cap', neck:'Sailor collar', cloth:'Breton stripes', obj:'Rubber duck'},
    polarBear:{who:'Winter one', hat:'Earmuffs', neck:'Chunky knit cowl', cloth:'Fair Isle jumper', obj:'Mug of cocoa'},
    shade:{who:'Grumpy, secretly sweet', hat:'Paper party hat', neck:'Ribbon bow', cloth:'Patchwork', obj:'Lollipop'},
  };
  const rgb=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
  const hex=a=>'#'+a.map(v=>Math.max(0,Math.min(255,Math.round(v))).toString(16).padStart(2,'0')).join('');
  const mix=(a,b,t)=>{const x=rgb(a),y=rgb(b);return hex(x.map((v,i)=>v+(y[i]-v)*t));};
  const lum=h=>{const c=rgb(h);return (0.2126*c[0]+0.7152*c[1]+0.0722*c[2])/255;};
  const thread=on=>lum(on)>0.3?mix(on,K,0.5):mix(on,WH,0.55);
  const r1=v=>Math.round(v*10)/10;
  let uid=0;
  const geom=ch=>{const d=CAST[ch],ny=CY+d.ry-8;return {rx:d.rx,ry:d.ry,body:d.c.body,belly:d.c.belly,ny,top:CY-d.ry};};
  const shape=(d,f,sw)=>`<path d="${d}" fill="${f}" stroke="${K}" stroke-width="${sw}" stroke-linejoin="round" stroke-linecap="round"/>`;
  const line=(d,c,w,dash)=>`<path d="${d}" fill="none" stroke="${c}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"${dash?` stroke-dasharray="${dash}"`:''}/>`;
  const tube=(d,c,w,S)=>line(d,K,w+2*S)+line(d,c,w);
  const circ=(x,y,r,f,sw)=>`<circle cx="${r1(x)}" cy="${r1(y)}" r="${r1(r)}" fill="${f}"${sw?` stroke="${K}" stroke-width="${sw}"`:''}/>`;
  const ell=(x,y,a,b,f,sw,rot=0)=>`<ellipse cx="${r1(x)}" cy="${r1(y)}" rx="${r1(a)}" ry="${r1(b)}" fill="${f}"${sw?` stroke="${K}" stroke-width="${sw}"`:''}${rot?` transform="rotate(${rot} ${r1(x)} ${r1(y)})"`:''}/>`;
  const bow=(x,y,s,f,S)=>shape(`M${x},${y} L${x-9*s},${y-6*s} Q${x-11*s},${y} ${x-9*s},${y+6*s} Z`,f,S*0.7)+shape(`M${x},${y} L${x+9*s},${y-6*s} Q${x+11*s},${y} ${x+9*s},${y+6*s} Z`,f,S*0.7)+circ(x,y,2.6*s,mix(f,K,.15),S*0.6);
  const daisy=(x,y,s,S)=>{let o='';for(let i=0;i<8;i++){const a=i*45*Math.PI/180;o+=ell(x+Math.cos(a)*6*s,y+Math.sin(a)*6*s,4.3*s,2.4*s,WH,S*0.4,i*45);}return o+circ(x,y,3.4*s,STRAW,S*0.45);};

  /* ---------- hats ---------- */
  function hat(ch,S,F){
    const {rx,ry,top}=geom(ch), cx=CX, cy=CY, st=(d,on)=>F?line(d,thread(on),F,`${r1(F*2.6)} ${r1(F*2.6)}`):'';
    switch(ch){
    case 'owl': return ell(cx+4,top+2,27,9,SAGE,S,-8)+circ(cx+6,top-8,3.4,SAGE,S*0.7)+st(`M${cx-18},${top+5} Q${cx+4},${top+11} ${cx+26},${top+1}`,SAGE);
    case 'hare': { const y=top+12; return shape(`M${cx-rx-8},${y} Q${cx},${y-12} ${cx+rx+8},${y} Q${cx},${y+16} ${cx-rx-8},${y} Z`,STRAW,S)
        +shape(`M${cx-30},${y-3} C${cx-30},${y-30} ${cx+30},${y-30} ${cx+30},${y-3} Q${cx},${y+4} ${cx-30},${y-3} Z`,STRAW,S)
        +line(`M${cx-29},${y-8} Q${cx},${y-1} ${cx+29},${y-8}`,SAGE,4)+st(`M${cx-rx},${y+2} Q${cx},${y+10} ${cx+rx},${y+2}`,STRAW); }
    case 'cat': return bow(cx+rx*0.6,cy-ry*1.02,1.3,ROSE,S);
    case 'badger': { const y=cy-ry*0.62, w=rx*0.66;
        return shape(`M${cx-w},${y} C${cx-w},${top-26} ${cx+w},${top-26} ${cx+w},${y} Z`,SAGE,S)
          +[-0.6,-0.3,0,0.3,0.6].map(t=>F?line(`M${cx+w*t},${y-4} L${cx+w*t*0.8},${top-8}`,mix(SAGE,K,.3),F,`${F*2} ${F*2}`):'').join('')
          +shape(`M${cx-w-4},${y-9} Q${cx},${y-15} ${cx+w+4},${y-9} L${cx+w+4},${y+3} Q${cx},${y-3} ${cx-w-4},${y+3} Z`,mix(SAGE,WH,.2),S)
          +circ(cx,top-24,11,CREAM,S); }
    case 'cyclops': { let o=''; const n=9; for(let i=0;i<n;i++){ const t=i/(n-1), x=cx-rx*0.52+rx*1.04*t, y=top+10-Math.sin(t*Math.PI)*10;
        o+=ell(x-4,y-3,7,3.2,SAGE,S*0.5,-30)+ell(x+4,y-3,7,3.2,mix(SAGE,WH,.15),S*0.5,30);} return line(`M${cx-rx*0.52},${top+10} Q${cx},${top-10} ${cx+rx*0.52},${top+10}`,WOOD,2.4)+o; }
    case 'threeEyes': return bow(cx+10,top-15,1.1,ROSE,S);
    case 'dragon': { const b=top+10, h=top-24;
        return shape(`M${cx-28},${b} L${cx-32},${h} L${cx-16},${top-8} L${cx},${h-6} L${cx+16},${top-8} L${cx+32},${h} L${cx+28},${b} Z`,CREAM,S)
          +circ(cx,top-6,4.4,BLUE,S*0.5)+circ(cx-17,top+1,3.4,SAGE,S*0.5)+circ(cx+17,top+1,3.4,SAGE,S*0.5); }
    case 'onion': { const x=cx+rx*0.42, y=top+10;
        return `<g transform="rotate(20 ${x} ${y})">`+ell(x,y+2,30,7,STRAW,S)+shape(`M${x-19},${y+1} L${x-18},${y-16} Q${x},${y-20} ${x+18},${y-16} L${x+19},${y+1} Q${x},${y+5} ${x-19},${y+1} Z`,STRAW,S)
          +line(`M${x-18.6},${y-4} Q${x},${y} ${x+18.6},${y-4}`,BLUE,4)+`</g>`; }
    case 'whale': { const x=cx-rx*0.52, y=top+8;
        return `<g transform="rotate(-18 ${x} ${y}) translate(${x} ${y}) scale(1.35) translate(${-x} ${-y})">`+shape(`M${x-26},${y} C${x-24},${y-24} ${x+24},${y-24} ${x+26},${y} Z`,WH,S)
          +shape(`M${x-30},${y-7} Q${x},${y-12} ${x+30},${y-7} L${x+30},${y+3} Q${x},${y-2} ${x-30},${y+3} Z`,WH,S)+line(`M${x-24},${y-2} Q${x},${y-7} ${x+24},${y-2}`,BLUE,3)+`</g>`; }
    case 'polarBear': { const ex=rx*0.62, ey=cy-ry*0.86;
        return tube(`M${cx-ex},${ey} Q${cx},${ey-ry*0.62} ${cx+ex},${ey}`,OAT,6,S)+circ(cx-ex,ey,14,BLUE,S)+circ(cx+ex,ey,14,BLUE,S)
          +st(`M${cx-ex-7},${ey-5} a8,8 0 1 0 1,0 M${cx+ex-7},${ey-5} a8,8 0 1 0 1,0`,BLUE); }
    case 'shade': { const x=cx-24, y=top-14;
        return `<g transform="rotate(-16 ${x} ${y})">`+shape(`M${x-15},${y+4} L${x},${y-34} L${x+15},${y+4} Z`,CREAM,S)
          +line(`M${x-10},${y-8} L${x+9},${y-4} M${x-6},${y-20} L${x+5},${y-18}`,SAGE,3.4)+circ(x,y-35,5,ROSE,S*0.7)+line(`M${x-14},${y+4} Q${x},${y+8} ${x+14},${y+4}`,K,1.2)+`</g>`; }
    } return '';
  }
  /* ---------- necks ---------- */
  function neck(ch,S,F){
    const {rx,ny}=geom(ch), cx=CX, st=(d,on)=>F?line(d,thread(on),F,`${r1(F*2.6)} ${r1(F*2.6)}`):'';
    switch(ch){
    case 'owl': return shape(`M${cx},${ny+4} L${cx-27},${ny-9} Q${cx-32},${ny+4} ${cx-27},${ny+17} Z`,OAT,S)+shape(`M${cx},${ny+4} L${cx+27},${ny-9} Q${cx+32},${ny+4} ${cx+27},${ny+17} Z`,OAT,S)+ell(cx,ny+4,6,7,mix(OAT,K,.15),S);
    case 'hare': { let o=line(`M${cx-38},${ny-4} Q${cx},${ny+18} ${cx+38},${ny-4}`,SAGE,2.4); [0,.25,.5,.75,1].forEach(t=>{const x=cx-38+76*t,y=ny-4+(1-(2*t-1)**2)*11;o+=daisy(x,y,1,S);}); return o; }
    case 'cat': return tube(`M${cx-40},${ny-4} Q${cx},${ny+16} ${cx+40},${ny-4}`,ROSE,10,S)+st(`M${cx-34},${ny-1} Q${cx},${ny+14} ${cx+34},${ny-1}`,ROSE)+circ(cx,ny+17,8,PEWTER,S)+line(`M${cx-4},${ny+19} L${cx+4},${ny+19}`,K,S*0.6)+circ(cx,ny+21.5,1.8,K);
    case 'badger': return line(`M${cx-26},${ny-4} Q${cx},${ny+16} ${cx+26},${ny-4}`,K,1.6)+shape(`M${cx-7},${ny+14} Q${cx},${ny+28} ${cx+7},${ny+14} Z`,WOOD,S*0.7)+shape(`M${cx-8.5},${ny+14} Q${cx},${ny+6} ${cx+8.5},${ny+14} Z`,mix(WOOD,K,.35),S*0.7)+line(`M${cx},${ny+8} L${cx+2},${ny+4}`,K,1.4);
    case 'cyclops': { let o=''; const n=11; for(let i=0;i<n;i++){ const t=i/(n-1), x=cx-50+100*t, y=ny+2+Math.sin(t*Math.PI)*10; o+=circ(x,y,9,WH,S*0.8);} return o; }
    case 'threeEyes': { let o=''; const n=9; for(let i=0;i<n;i++){ const t=i/(n-1), x=cx-34+68*t, y=ny-2+(1-(2*t-1)**2)*18; o+=circ(x,y,6,i%2?OAT:WOOD,S*0.7);} return o; }
    case 'dragon': { let o=`<path d="M${cx-44},${ny-2} Q${cx},${ny+26} ${cx+44},${ny-2}" fill="none" stroke="${K}" stroke-width="${16+S*2}" stroke-linecap="round"/><path d="M${cx-44},${ny-2} Q${cx},${ny+26} ${cx+44},${ny-2}" fill="none" stroke="${WH}" stroke-width="16" stroke-linecap="round"/>`;
        [.12,.3,.5,.7,.88].forEach(t=>{const x=cx-44+88*t,y=ny-2+(1-(2*t-1)**2)*14;o+=`<path d="M${x} ${y-3} l-2 5 l2 -1.5 l2 1.5 z" fill="${K}"/>`;}); return o; }
    case 'onion': { const flap=sg=>shape(`M${cx},${ny-2} C${cx+sg*10},${ny+20} ${cx+sg*42},${ny+20} ${cx+sg*42},${ny-2} Q${cx+sg*22},${ny+4} ${cx},${ny-2} Z`,'#fbf5e6',S*0.8);
        return flap(-1)+flap(1)+st(`M${cx-6},${ny+6} C${cx-14},${ny+15} ${cx-34},${ny+15} ${cx-37},${ny+2} M${cx+6},${ny+6} C${cx+14},${ny+15} ${cx+34},${ny+15} ${cx+37},${ny+2}`,'#fbf5e6'); }
    case 'whale': return shape(`M${cx-40},${ny-4} L${cx},${ny+26} L${cx+40},${ny-4} L${cx+30},${ny-8} L${cx},${ny+12} L${cx-30},${ny-8} Z`,NAVY,S)
        +line(`M${cx-33},${ny-3} L${cx},${ny+20} L${cx+33},${ny-3}`,WH,2)+shape(`M${cx-6},${ny+22} L${cx},${ny+30} L${cx+6},${ny+22} L${cx},${ny+16} Z`,WH,S*0.6);
    case 'polarBear': return tube(`M${cx-40},${ny-2} Q${cx},${ny+18} ${cx+40},${ny-2}`,CREAM,15,S)+(F?[-30,-18,-6,6,18,30].map(dx=>line(`M${cx+dx},${ny-2+(1-(dx/40)**2)*9} l${dx>0?2:-2} 9`,mix(CREAM,K,.25),1.4)).join(''):'');
    case 'shade': { const y=ny+6; return shape(`M${cx},${y} C${cx-16},${y-16} ${cx-36},${y-6} ${cx-31},${y+6} C${cx-24},${y+13} ${cx-10},${y+8} ${cx},${y} Z`,OAT,S)
        +shape(`M${cx},${y} C${cx+16},${y-16} ${cx+36},${y-6} ${cx+31},${y+6} C${cx+24},${y+13} ${cx+10},${y+8} ${cx},${y} Z`,OAT,S)+ell(cx,y+2,6,7,mix(OAT,K,.15),S); }
    } return '';
  }
  /* ---------- favourite object, held in the right mitten (drawn, then the mitten is redrawn over its lower end) ---------- */
  function obj(ch,S,F){
    const {ny,top,body,belly}=geom(ch), cx=CX, x=cx+80, y=ny+10;
    let o='';
    switch(ch){
    case 'owl': o=ell(x+4,y-6,17,4.5,WH,S)+shape(`M${x-8},${y-26} L${x+16},${y-26} Q${x+15},${y-9} ${x+4},${y-8} Q${x-7},${y-9} ${x-8},${y-26} Z`,WH,S)+line(`M${x+15},${y-22} q8 1 5 8 q-2 3 -6 2`,K,S*0.7)+line(`M${x-7},${y-22} Q${x+4},${y-19} ${x+15},${y-22}`,BLUE,2.4)
        +(F?line(`M${x},${y-32} q-3 -5 0 -9 M${x+7},${y-32} q-3 -5 0 -9`,WH,1.6):''); break;
    case 'hare': o=shape(`M${x-6},${y-2} L${x-4},${y-24} L${x+16},${y-24} L${x+18},${y-2} Z`,SAGE,S)+shape(`M${x+14},${y-18} L${x+19},${y-42} L${x+23},${y-41} L${x+18},${y-14} Z`,SAGE,S*0.8)+ell(x+21,y-44,6,3.6,mix(SAGE,WH,.2),S*0.7,-12)+line(`M${x-2},${y-28} Q${x+6},${y-38} ${x+14},${y-28}`,K,S*0.8); break;
    case 'cat': o=circ(x+6,y-14,14,ROSE,S)+line(`M${x-4},${y-22} Q${x+6},${y-12} ${x+14},${y-26} M${x-6},${y-12} Q${x+8},${y-4} ${x+18},${y-16} M${x},${y-4} Q${x+10},${y-10} ${x+19},${y-8}`,mix(ROSE,K,.3),1.6)+line(`M${x+16},${y-6} C${x+24},${y+4} ${x+14},${y+14} ${x+22},${y+24}`,ROSE,2.4); break;
    case 'badger': o=`<g transform="translate(-4 0)">`+shape(`M${x},${y} Q${x-1},${y-14} ${x+3},${y-18} L${x+11},${y-18} Q${x+14},${y-14} ${x+13},${y} Z`,CREAM,S*0.9)+shape(`M${x-12},${y-16} C${x-10},${y-38} ${x+26},${y-38} ${x+26},${y-16} Q${x+7},${y-10} ${x-12},${y-16} Z`,OAT,S)+circ(x-1,y-24,2.6,CREAM)+circ(x+9,y-30,2.2,CREAM)+circ(x+17,y-22,2.4,CREAM)+`</g>`; break;
    case 'cyclops': o=`<g transform="translate(-5 0)">`+shape(`M${x+2},${y+2} L${x-12},${y-26} L${x+22},${y-26} Z`,CREAM,S)+circ(x-6,y-30,6,ROSE,S*0.7)+circ(x+6,y-35,6,WH,S*0.7)+circ(x+16,y-29,6,BLUE,S*0.7)+ell(x-12,y-24,6,3,SAGE,S*0.5,-30)+ell(x+22,y-24,6,3,SAGE,S*0.5,30)+`</g>`; break;
    case 'threeEyes': { const px=x+8, py=y-40; o=line(`M${x+4},${y+4} L${px},${py}`,WOOD,3);
        [[0,BLUE],[90,SAGE],[180,CREAM],[270,ROSE]].forEach(([a,c])=>{o+=`<path d="M${px} ${py} L${px} ${py-14} Q${px+10} ${py-10} ${px} ${py} Z" fill="${c}" stroke="${K}" stroke-width="${S*0.6}" transform="rotate(${a} ${px} ${py})"/>`;}); o+=circ(px,py,2.4,K); break; }
    case 'dragon': o=ell(x+6,y-14,12,16,WH,S)+circ(x+2,y-20,3,BLUE)+circ(x+11,y-11,2.4,SAGE)+circ(x+4,y-6,2,BLUE)+circ(x+12,y-24,1.8,SAGE); break;
    case 'onion': o=line(`M${x+4},${y+2} C${x+10},${y-24} ${x+2},${y-44} ${x+6},${y-66}`,K,1.2)+ell(x+7,y-84,15,19,SAGE,S)+`<path d="M${x+6} ${y-65.5} l-3 4 h6 z" fill="${SAGE}" stroke="${K}" stroke-width="${S*0.6}"/>`+(F?line(`M${x},${y-92} q2 -5 7 -6`,WH,2):''); break;
    case 'whale': o=`<g transform="translate(-6 0)">`+shape(`M${x-6},${y-6} Q${x-8},${y-22} ${x+8},${y-20} Q${x+10},${y-30} ${x+18},${y-28} Q${x+26},${y-26} ${x+22},${y-18} L${x+28},${y-16} L${x+22},${y-12} Q${x+22},${y} ${x+6},${y-2} Q${x-4},${y-2} ${x-6},${y-6} Z`,BUTTER,S)+circ(x+19,y-24,1.6,K)+`</g>`; break;
    case 'polarBear': o=shape(`M${x-6},${y-2} L${x-6},${y-26} L${x+16},${y-26} L${x+16},${y-2} Q${x+5},${y+2} ${x-6},${y-2} Z`,BLUE,S)+line(`M${x+16},${y-20} q9 1 7 9 q-2 4 -7 2`,K,S*0.7)+ell(x+5,y-26,11,3,'#6a4a34',S*0.6)+circ(x+2,y-28,3,WH,S*0.4)+circ(x+8,y-29,2.6,WH,S*0.4)
        +(F?line(`M${x},${y-34} q-3 -5 0 -9 M${x+8},${y-34} q-3 -5 0 -9`,WH,1.6):''); break;
    case 'shade': o=line(`M${x+4},${y+4} L${x+10},${y-26}`,WH,3)+circ(x+12,y-38,13,WH,S)+`<path d="M${x+12} ${y-38} m-9 0 a9 9 0 0 1 18 0 a6.5 6.5 0 0 1 -13 0 a4 4 0 0 1 8 0 a1.8 1.8 0 0 1 -3.6 0" fill="none" stroke="${ROSE}" stroke-width="2.6"/>`; break;
    }
    const mit = ell(cx+64,ny+25,28,13.5,body,S,-34)+circ(cx+79,ny+15,5.5,belly,0);
    return o+mit;
  }
  /* ---------- clothes: masked to the glove body, the belly patch and seat numeral stay clear ---------- */
  function cloth(ch,S,F,id){
    const {rx,ry,ny,body}=geom(ch), cx=CX, cy=CY, dark=lum(body)<0.45;
    const ink = dark ? mix(body,WH,0.42) : mix(body,K,0.28);
    const P=(w,h,inner)=>`<pattern id="${id}p" width="${w}" height="${h}" patternUnits="userSpaceOnUse">${inner}</pattern>`;
    let pat='', over='', op=dark?.5:.55;
    const R=`<rect x="0" y="0" width="210" height="240" fill="url(#${id}p)"`;
    switch(ch){
      case 'owl': pat=P(12,10,`<path d="M0 5 L6 0 L12 5 M0 10 L6 5 L12 10" fill="none" stroke="${mix(OAT,K,.35)}" stroke-width="1.6"/>`);
        over=`<path d="M${cx-60} ${ny} L${cx-8} ${ny+8} L${cx-6} 236 L${cx-64} 236 Z M${cx+60} ${ny} L${cx+8} ${ny+8} L${cx+6} 236 L${cx+64} 236 Z" fill="${OAT}"/><path d="M${cx-60} ${ny} L${cx-8} ${ny+8} L${cx-6} 236 L${cx-64} 236 Z M${cx+60} ${ny} L${cx+8} ${ny+8} L${cx+6} 236 L${cx+64} 236 Z" fill="url(#${id}p)"/>`
          +`<path d="M${cx-8} ${ny+8} L${cx-6} 236 M${cx+8} ${ny+8} L${cx+6} 236" stroke="${K}" stroke-width="${S*0.7}"/>`+[0,1,2].map(i=>circ(cx+14,ny+100+i*14,2.8,WOOD,S*0.5)).join(''); pat=pat; op=1; break;
      case 'hare': over=`<path d="M${cx-40} ${ny+30} H${cx+40} L${cx+46} 236 H${cx-46} Z" fill="${DENIM}"/><path d="M${cx-40} ${ny+30} L${cx-30} ${ny-6} M${cx+40} ${ny+30} L${cx+30} ${ny-6}" stroke="${DENIM}" stroke-width="9"/>`
          +circ(cx-36,ny+32,3.2,PEWTER,S*0.5)+circ(cx+36,ny+32,3.2,PEWTER,S*0.5)+(F?`<path d="M${cx-37} ${ny+36} H${cx+37} M${cx-44} 226 H${cx+44}" stroke="${mix(DENIM,WH,.5)}" stroke-width="1.3" stroke-dasharray="3 3"/>`:''); break;
      case 'cat': pat=P(40,14,`<rect width="40" height="5" fill="${ink}"/>`); break;
      case 'badger': pat=P(16,20,`<path d="M4 0 V20 M12 0 V20" stroke="${ink}" stroke-width="1.4" stroke-dasharray="3 2"/><path d="M4 4 Q8 8 12 12 M12 4 Q8 8 4 12" fill="none" stroke="${ink}" stroke-width="1.6"/>`); break;
      case 'cyclops': pat=P(24,24,`<path d="M12 0 L24 12 L12 24 L0 12 Z" fill="${mix(BLUE,WH,.2)}" opacity=".6"/><path d="M0 0 L12 12 M24 0 L12 12 M0 24 L12 12 M24 24 L12 12" stroke="${K}" stroke-width=".6" opacity=".5"/>`); op=1; break;
      case 'threeEyes': pat=P(16,14,`<path d="M0 10 L4 4 L8 10 L12 4 L16 10" fill="none" stroke="${ink}" stroke-width="2.2"/>`); break;
      case 'dragon': pat=P(16,12,`<path d="M0 12 A8 8 0 0 1 16 12 M-8 6 A8 8 0 0 1 8 6 M8 6 A8 8 0 0 1 24 6" fill="none" stroke="${ink}" stroke-width="1.5"/>`); break;
      case 'onion': pat=P(16,16,`<rect width="8" height="16" fill="${SAGE}" opacity=".35"/><rect width="16" height="8" fill="${SAGE}" opacity=".35"/>`); op=1; break;
      case 'whale': pat=P(40,15,`<rect width="40" height="6" fill="${mix(body,WH,.75)}"/>`); op=.9; break;
      case 'polarBear': over=[0,1,2,3,4,5,6,7,8,9].map(i=>{const x=cx-58+i*13,y=ny+34;return `<path d="M${x} ${y} l6.5 -6 l6.5 6 l-6.5 6 z" fill="${i%2?BLUE:SAGE}"/>`;}).join('')+`<path d="M${cx-62} ${ny+24} H${cx+62} M${cx-62} ${ny+44} H${cx+62}" stroke="${BLUE}" stroke-width="2.4"/>`
          +`<path d="M${cx-62} 214 H${cx+62}" stroke="${BLUE}" stroke-width="3"/>`; break;
      case 'shade': over=[[cx-50,ny+18,26,22,SAGE],[cx+22,ny+30,28,24,OAT],[cx-10,ny+86,30,22,BLUE],[cx+30,ny+80,24,26,mix(body,WH,.3)]].map(([x,y,w,h,f])=>
          `<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="2" fill="${f}" stroke="${K}" stroke-width="${S*0.45}" transform="rotate(${(x%7)-3} ${x+w/2} ${y+h/2})"/><rect x="${x+3}" y="${y+3}" width="${w-6}" height="${h-6}" rx="1.5" fill="none" stroke="${thread(f)}" stroke-width="1.3" stroke-dasharray="3 3" transform="rotate(${(x%7)-3} ${x+w/2} ${y+h/2})"/>`).join(''); break;
    }
    const glove=`M${cx-24},${ny-8} C${cx-44},${ny+6} ${cx-58},${ny+30} ${cx-60},${ny+70} L${cx-62},236 L${cx+62},236 L${cx+60},${ny+70} C${cx+58},${ny+30} ${cx+44},${ny+6} ${cx+24},${ny-8} Z`;
    const hg={cx,cy,rx,ry}, head=CAST[ch].headPath?CAST[ch].headPath(hg):roundHead(hg);
    const by=(ny+16+216)/2, bry=Math.min(30,(216-(ny+16))/2), brx=bry*0.95;
    const mask=`<mask id="${id}m" maskUnits="userSpaceOnUse" x="0" y="0" width="210" height="240"><path d="${glove}" fill="#fff"/><path d="${head}" fill="#000"/>`
      +`<ellipse cx="${cx}" cy="${r1(by)}" rx="${r1(brx+3)}" ry="${r1(bry+3)}" fill="#000"/><rect x="${cx-50}" y="186" width="30" height="28" fill="#000" transform="rotate(-10 ${cx-36} 200)"/>`
      +`<path d="M${cx-60} 224 H${cx+60}" stroke="#000" stroke-width="5"/><path d="${glove}" fill="none" stroke="#000" stroke-width="${S+1}"/></mask>`;
    return `<defs>${pat}${mask}</defs><g mask="url(#${id}m)">`+(pat&&ch!=='owl'?R+` opacity="${op}"/>`:'')+over+`</g>`;
  }
  /* the four layers for one character; the chip keeps only what its crop can show (hat and neck) */
  function parts(ch,S,F,chip,id){ return { cloth: chip?'':cloth(ch,S,F,id), neck: neck(ch,S,F), obj: chip?'':obj(ch,S,F), hat: hat(ch,S,F) }; }
  return { parts, OUTFIT };
  })();

  let uid = 0;

  /* opts: seat (1-9, belly numeral; not drawn on a chip), variant ("bust" | "chip"), look ("front" | "left" | "right"),
           state ("idle" | "talking" | "out"), decorative (true when a visible label already names the puppet), id (clip id override) */
  function svg(character, opts = {}) {
    const def = CAST[character];
    if (!def) throw new Error("Unknown puppet: " + character);
    const { seat, variant = "bust", look = "front", state = "idle", decorative = false, dress = true } = opts;
    const chip = variant === "chip";
    const S = chip ? 5 : 3;        // outline
    const F = chip ? 0 : 1.6;      // stitching and other fine detail; 0 switches it off
    const { rx, ry, c } = def, cx = CX, cy = CY, ny = cy + ry - 8;
    const E = def.eyes ? def.eyes(cx, cy, rx, ry) : [{ x: cx - rx * 0.42, y: cy - ry * 0.08, k: 1 }, { x: cx + rx * 0.42, y: cy - ry * 0.08, k: 1 }];
    const g = { cx, cy, rx, ry, ny, S, F, c, E }, t = tools(g);
    const headD = def.headPath ? def.headPath(g) : roundHead(g);
    const clip = opts.id || "pup" + ++uid;
    const D = dress ? Dress.parts(character, S, F, chip, clip + "d") : null;               // outfit layers

    /* the glove, shared by all eleven */
    const by = (ny + 16 + 216) / 2, bry = Math.min(30, (216 - (ny + 16)) / 2), brx = bry * 0.95, ds = (bry / 30) * 1.2;
    const glove = t.ell(cx - 64, ny + 25, 28, 13.5, c.body, S, 34) + t.circ(cx - 79, ny + 15, 5.5, c.belly, 0)
      + t.ell(cx + 64, ny + 25, 28, 13.5, c.body, S, -34) + t.circ(cx + 79, ny + 15, 5.5, c.belly, 0)
      + t.shape(p`M${cx - 24},${ny - 8} C${cx - 44},${ny + 6} ${cx - 58},${ny + 30} ${cx - 60},${ny + 70} L${cx - 62},236 L${cx + 62},236 L${cx + 60},${ny + 70} C${cx + 58},${ny + 30} ${cx + 44},${ny + 6} ${cx + 24},${ny - 8} Z`, c.body)
      + t.ell(cx, by, brx, bry, c.belly, S * 0.66) + t.ring(cx, by, brx - 5, bry - 5, c.belly)
      + t.stitch(p`M${cx - 57},224 L${cx + 57},224`, c.body)
      + (!chip && DIGITS[seat] ? `<g transform="translate(${r1(cx - 10 * ds)},${r1(by - 15 * ds)}) scale(${r1(ds)})">${t.line(DIGITS[seat], mix(c.belly, INK, 0.74), 3.2)}</g>` : "")
      + t.patch(cx - 36, 200, 22, 20, -10, def.patch, 3);                                   // mended: a patch low on the glove

    /* mended: a patch on the head (clipped to it) and a sewn seam on the cheek */
    const headPatch = t.patch(cx + rx * 0.5, cy - ry * 0.62, 30, 26, 16, def.patch, 4);
    const cheekSeam = t.seam(cx - rx * 0.84, cy + ry * 0.2, cx - rx * 0.5, cy + ry * 0.62, 3, thread(c[def.scarOn || "main"]), 4.5);
    const topSeam = t.stitch(p`M${cx},${cy - ry + 4} Q${cx + 3},${cy - ry * 0.78} ${cx},${cy - ry * 0.56}`, c[def.seamOn || "main"]);

    /* eyes: dots. On dark felt they flip to pale. "out" crosses them. */
    const eyeCol = def.eyeOnDark ? WHITE : INK;
    let eyes = E.map((e) => `<g transform="translate(${r1(e.x)},${r1(e.y)}) scale(${e.k})">`
      + (state === "out" ? t.line("M-7,-7 L7,7", eyeCol, S) + t.line("M7,-7 L-7,7", eyeCol, S)
        : t.ell(0, 0, 5.5, 7, eyeCol, 0) + (!def.eyeOnDark && F ? t.circ(1.6, -2.6, 1.7, WHITE, 0) : "")) + `</g>`).join("");
    if (def.brows && state !== "out") {
      const b = def.brows === "cross" ? [[-11, -20], [9, -12]] : [[-9, -13], [8, -19]];
      eyes += E.map((e, i) => { const sg = i % 2 === 0 ? 1 : -1; return t.line(p`M${e.x + sg * b[0][0] * e.k},${e.y + b[0][1] * e.k} L${e.x + sg * b[1][0] * e.k},${e.y + b[1][1] * e.k}`, eyeCol, S); }).join("");
    }

    /* mouth */
    const mcol = def.mouthOnDark ? WHITE : INK, mw = def.mouthW || 1, sw = Math.max(F, 1.6) * 1.3;
    const my = cy + ry * (def.mouthY || (def.beak ? 0.66 : 0.52));
    let mouth = "";
    if (state === "talking") mouth = t.ell(0, 1, def.wideSmile ? 9 * mw : 6, 5.5, "#0e0906", S * 0.7);
    else if (state === "out") mouth = t.line(`M${r1(-8 * mw)},1 L${r1(8 * mw)},1`, mcol, sw);
    else if (def.wideSmile) mouth = t.line(`M${r1(-22 * mw)},-2 Q0,9 ${r1(22 * mw)},-2`, mcol, sw);
    else if (!def.beak) mouth = t.line("M-10,-3 Q-5,5 0,-2 Q5,5 10,-3", mcol, sw);
    if (mouth) mouth = `<g transform="translate(${cx},${r1(my)}) scale(${def.beak ? 0.8 : 1})">${mouth}</g>`;

    const shift = look === "left" ? -5 : look === "right" ? 5 : 0;
    const cw = 2 * rx + 24 + (def.cropUp || 0);
    const vb = chip ? [r1(cx - cw / 2), r1(Math.max(0, cy - ry - 32 - (def.cropUp || 0))), r1(cw), r1((cw * 36) / 28)] : [0, 0, W, H];
    const label = NAMES[character] + " puppet" + (seat != null ? ", seat " + seat : "");

    return `<svg xmlns="http://www.w3.org/2000/svg" class="puppet" data-character="${character}" viewBox="${vb.join(" ")}"`
      + (chip ? ` preserveAspectRatio="xMidYMid slice"` : "")
      + (decorative ? ` aria-hidden="true"` : ` role="img" aria-label="${label}"`) + ` style="display:block;width:100%;height:${chip ? "100%" : "auto"}">`
      + (def.back ? def.back(g, t) : "") + glove + (D ? D.cloth : "") + t.shape(headD, c.main)
      + `<clipPath id="${clip}"><path d="${headD}"/></clipPath><g clip-path="url(#${clip})">${def.face ? def.face(g, t) : ""}${headPatch}</g>`
      + t.shape(headD, "none") + cheekSeam
      + `<g${shift ? ` transform="translate(${shift},0)"` : ""}>${topSeam}${def.front ? def.front(g, t) : ""}${eyes}${mouth}</g>` + (D ? D.neck + D.obj + D.hat : "") + `</svg>`;
  }

  return { VERSION, IDS, NAMES, OUTFIT: Dress.OUTFIT, castForGame, svg };
})();
