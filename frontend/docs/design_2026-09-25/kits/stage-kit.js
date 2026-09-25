/* Stage kit, VERSION "2026-09-23". Frozen from the Skin bench (production log revision 62): the base day-discussion scene.
 * The dining car under the Quiet cut-outs cue: walnut wall, the brass rounded window with its rolled blind and the snowy
 * country rolling past, the wall clock hung on its string (left), the iron lantern on its bracket (right), the stage floor
 * with one seam and the trapdoor under the puppet, specials (a narrow spot from above on each hung or wall-mounted prop),
 * the room-light rule, the four phase paints, the own stand, the light overlay, and the replay's dressing.
 * No variants: the Skin bench keeps them for comparison. Plain JavaScript, no dependencies, one global: StageKit.
 *
 *   StageKit.geometry(W, H, { phone, hud: "none" | "live" | "replay", side })  -> g   the locked HUD geometry (rail, puppet box, wing, side slot)
 *   StageKit.scene(g, phase, { id, dark, dim })   -> { html, glows, specials, floor }   the backdrop (phase: day | dusk | night | dawn)
 *   StageKit.light(g, sceneOut, { id, dark, from, pool, glows, specials })  -> html   darkness outside the pool; glows and specials left open
 *   StageKit.dressing(g, { id })                   -> svg    the replay's curtains, valance, scalloped border and proscenium (never in live)
 *   StageKit.stand(g, { seat, tag, tagClass, lit, box })  -> html   the own stand (box: false leaves only the dark below the rail)
 *   StageKit.install()                             -> injects StageKit.CSS once (stand, sway, flicker, snow)
 *   StageKit.vars()                                -> the materials as CSS custom properties, for the stage element
 *   StageKit.draw                                  -> the drawing helpers props are built with (inkP, stitch, twine, flameAt, cutout, beam, K2, rnd, mix)
 * Every id a drawing makes is prefixed with opts.id, so several stages can share a page. */
const StageKit = (() => {
  const VERSION = "2026-09-23";
  const MATERIALS = {   // the HUD's materials, from the X-ray bench (locked revision 52) and the HUD blockout
    ink: "#24180c", bone: "#efe4cb", bone2: "#cdbb93", bone3: "#8d7a55",
    cloak0: "#0e0906", cloak1: "#241910", cloak2: "#4d3824",
    paper: "#ecdfc3", paperInk: "#24180c",
    glassTop: "rgba(33,27,20,.96)", glassBot: "rgba(14,9,6,.96)",
    film: "#0b191f", filmInk: "#7fdcf2", filmText: "#c6e2ea", filmMain: "#eefaff", filmMut: "#7ea9b6", filmLine: "#264a56", filmBorder: "#dfe9ec", sure: "#7fdcf2",
    slip: "#fbf7ea", slipInk: "#26283a", slipRule: "#c3d3e8",
    amber: "#e0a63a", warm: "#ffb35c",
    town: "#e0a63a", wolf: "#e3503f", sk: "#9d7cff", townInk: "#4a2e0a", wolfInk: "#4a120c", skInk: "#241548",
    border: "#1b120b", frameLine: "#8d7a55", floor: "#0c0a07",
  };
  const PHASES = {   // one set of shapes, four paints (the car shows them through its glass)
    day:   { name: "Day", skyTop: "#c9b26e", skyMid: "#e6d59d", band: "#f3d98d", edge: "#fbe8b0", halo: "#fff3c8", far: "#a0955c", far2: "#7f7c4a", row: "#5f5e3c", roof: "#4a4530", tree: "#556a44", win: "#3d4030", orb: "#f6dd8e", ray: "#d8b65a", floor: "#4a4a30", orbAt: "hiR", cold: false, lit: false },
    dusk:  { name: "Voting (dusk)", skyTop: "#5a4a6a", skyMid: "#ecd2bd", band: "#e8905e", edge: "#f5c07a", halo: "#ffdcae", far: "#5b4756", far2: "#463a4a", row: "#3a3040", roof: "#2c2434", tree: "#34313d", win: "#ffd27a", orb: "#f3a86a", ray: "#d8804f", floor: "#2a2430", orbAt: "loR", cold: false, lit: true },
    night: { name: "Night", skyTop: "#0d1626", skyMid: "#15253c", band: "#2b7381", edge: "#6fc3c9", halo: "#bfe3ea", far: "#17303a", far2: "#102631", row: "#0e1c24", roof: "#0a141a", tree: "#0f2026", win: "#ffd27a", orb: "#e3ecee", ray: "#bcd0d4", floor: "#0b161c", orbAt: "hiL", cold: true, lit: true },
    dawn:  { name: "Dawn", skyTop: "#7d8b94", skyMid: "#dcdfd6", band: "#efd2a0", edge: "#f8e6c2", halo: "#fff3d6", far: "#6a7a72", far2: "#55655e", row: "#46534c", roof: "#363f3a", tree: "#3f5145", win: "#4a5550", orb: "#f8e2b4", ray: "#dcc08a", floor: "#3a463f", orbAt: "loL", cold: false, lit: false },
  };
  /* the room-light rule: the phase's ambient multiplied over the walls (not the glass), then a warm pool per source */
  const ROOMLIGHT = { day: { tint: null, a: 0, glow: 0.35 }, dusk: { tint: "#c0703a", a: 0.24, glow: 0.7 }, night: { tint: "#0c1426", a: 0.66, glow: 1 }, dawn: { tint: "#6d7c86", a: 0.26, glow: 0.3 } };
  const CLOCK = { day: [2, 12], dusk: [6, 12], night: [12, 12], dawn: [6, 6] };   // the wall clock keeps the phase
  const CAR = { dadoH: 0.15, wall: "#4a2c18", wallDark: "#3a2212", dado: "#3a2212", brass: "#b08a4a" };
  const BOARD = "#5a3f26", BOARD2 = "#4a3320", K2 = "#24180c";

  /* ---------- helpers ---------- */
  const rnd = (i, k) => { const v = Math.sin(i * 127.1 + k * 311.7) * 43758.5453; return v - Math.floor(v); };
  const hex = (h) => { h = h.replace("#", ""); if (h.length === 3) h = h.split("").map((c) => c + c).join(""); return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16)); };
  const toHex = (r) => "#" + r.map((v) => Math.round(Math.max(0, Math.min(255, v))).toString(16).padStart(2, "0")).join("");
  const mix = (a, b, t) => toHex(hex(a).map((v, i) => v + (hex(b)[i] - v) * t));
  const inkP = (d, f, w, x = "") => `<path d="${d}" fill="${f}" stroke="${K2}" stroke-width="${w}" stroke-linejoin="round" stroke-linecap="round" ${x}/>`;
  const stitch = (d, col, w, o = 0.7) => `<path d="${d}" fill="none" stroke="${col}" stroke-width="${w}" stroke-dasharray="${w * 2.4} ${w * 2.4}" stroke-linecap="round" opacity="${o}"/>`;
  const flameAt = (x, y, k) => `<g class="sk-flk">${inkP(`M${x},${y - 10 * k} C${x + 6 * k},${y - 3 * k} ${x + 5 * k},${y + 6 * k} ${x},${y + 8 * k} C${x - 5 * k},${y + 6 * k} ${x - 6 * k},${y - 3 * k} ${x},${y - 10 * k}Z`, "#f0a33a", 1.3 * k)}<path d="M${x},${y - 4 * k} C${x + 3 * k},${y} ${x + 2.4 * k},${y + 5 * k} ${x},${y + 6 * k} C${x - 2.4 * k},${y + 5 * k} ${x - 3 * k},${y} ${x},${y - 4 * k}Z" fill="#fff0b8"/></g>`;
  /* a pale string with a dark edge, readable on a light wall and a dark one */
  const twine = (x1, y1, x2, y2, s) => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#24180c" stroke-opacity=".8" stroke-width="${3 * s}"/><line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="#d9c9a0" stroke-width="${1.4 * s}"/>`;
  /* quiet cut-outs: a soft shadow on the wall, no ply edge. P is the id prefix whose shadf filter the scene defines */
  const cutout = (P, s, m, depth = 1) => { const e = (3 + depth * 2) * s; return `<g filter="url(#${P}shadf)" opacity=".75" transform="translate(${(e * 1.6).toFixed(1)},${(e * 1.4).toFixed(1)})">${m}</g>${m}`; };
  /* a special's visible beam: a narrow cone from above, drawn faint (the light overlay leaves its footprint open) */
  const beam = (x, y0, y1, rx, dark = 50) => `<path d="M${(x - rx * 0.35).toFixed(0)},${y0} H${(x + rx * 0.35).toFixed(0)} L${(x + rx).toFixed(0)},${(y1 + rx * 0.4).toFixed(0)} H${(x - rx).toFixed(0)}Z" fill="#fff8e0" opacity="${(0.05 + 0.05 * dark / 100).toFixed(3)}" style="mix-blend-mode:screen"/>`;

  /* ---------- geometry: the locked HUD's numbers (X-ray bench revision 51; live rail from the HUD blockout) ---------- */
  function geometry(W, H, o = {}) {
    const phone = !!o.phone, hud = o.hud || "live", on = hud !== "none";
    const wingN = on ? W * (phone ? 0.049 : 0.055) : 0, area = W - wingN, slotW = area * (phone ? 0.46 : 0.42);
    const rail = hud === "replay" ? (phone ? 55 : 68) : (phone ? 64 : 71);
    const railY = rail / 100 * H, room = o.side ? area - slotW : area;
    let ph = (railY - 0.05 * H) / 0.925, pwid = ph * 210 / 240;
    if (pwid > room * 0.96) { pwid = room * 0.96; ph = pwid * 240 / 210; }
    const top = railY - 0.925 * ph, left = wingN + (room - pwid) / 2, s = H / 900;
    return { Wf: W, H, phone, hud, wingN, area, slotW, rail, railY, room, side: !!o.side, ph, pwid, top, left, cx: left + pwid / 2, s, u: pwid / 525,
      headTop: top + 49 / 240 * ph, headBot: top + 159 / 240 * ph, headC: top + 104 / 240 * ph };
  }

  /* ---------- the car's pieces ---------- */
  function winSky(ctx, c, x, y, w, h, s, opt = {}) {   // the phase's sky cloth, seen through glass
    const id = ctx.P + "ws" + Math.round(x);
    let d = `<defs><linearGradient id="${id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="${c.skyTop}"/><stop offset=".55" stop-color="${c.skyMid}"/><stop offset=".85" stop-color="${c.band}"/><stop offset="1" stop-color="${c.edge}"/></linearGradient>
      <clipPath id="${id}c"><rect x="${x}" y="${y}" width="${w}" height="${h}" rx="${opt.r || 0}"/></clipPath></defs><g clip-path="url(#${id}c)"><rect x="${x}" y="${y}" width="${w}" height="${h}" fill="url(#${id})"/>`;
    if (ctx.phase === "night") for (let i = 0; i < 26; i++) d += `<circle cx="${(x + rnd(i, 121) * w).toFixed(0)}" cy="${(y + rnd(i, 122) * h * 0.6).toFixed(0)}" r="${((0.6 + rnd(i, 123)) * s).toFixed(1)}" fill="${c.orb}" fill-opacity=".7"/>`;
    if (opt.orb && !c.orbAt.startsWith("lo")) d += ctx.phase === "night" ? `<path d="M${x + w * 0.8},${y + h * 0.12} a${22 * s},${22 * s} 0 1 0 ${14 * s},${36 * s} a${17 * s},${17 * s} 0 1 1 ${-14 * s},${-36 * s}Z" fill="${c.orb}" stroke="${K2}" stroke-width="${2 * s}"/>` : `<circle cx="${x + w * 0.8}" cy="${y + h * 0.2}" r="${18 * s}" fill="${c.orb}" stroke="${K2}" stroke-width="${2 * s}"/>`;
    const hill = (y0, a, col, ph) => { let p = `M${x},${y0}`; for (let t = 0; t <= w + 30; t += 30) p += ` L${x + t},${(y0 - a * Math.abs(Math.sin((t + ph) / (90 * s)))).toFixed(0)}`; return `<path d="${p} L${x + w},${y + h} L${x},${y + h}Z" fill="${col}"/>`; };
    d += hill(y + h * 0.7, h * 0.12, c.far, 40) + hill(y + h * 0.7, h * 0.03, c.halo, 40).replace('fill="', 'fill-opacity=".45" fill="') + hill(y + h * 0.82, h * 0.06, c.far2, 300);
    { const P = 120 * s; let row = ""; for (let t = -P; t < w + 2 * P; t += P / 3) { const k = Math.round(t / P * 3), ht = (36 + rnd(k, 131) * 30) * s; row += `<path d="M${(x + t).toFixed(0)},${y + h * 0.9} l${10 * s},${-ht} l${10 * s},${ht}Z" fill="${c.tree}"/>`; }
      d += `<g class="sk-scrl" style="--p:${P.toFixed(1)}px">${row}</g>`; for (let t = 0; t < w; t += 160 * s) d += `<rect x="${x + t + 40 * s}" y="${y + h * 0.55}" width="${3 * s}" height="${h * 0.4}" fill="${c.roof}"/>`; }
    d += `<rect x="${x}" y="${y + h * 0.9}" width="${w}" height="${h * 0.1}" fill="${c.halo}" fill-opacity=".6"/>` + Array.from({ length: 30 }, (_, i) => `<circle cx="${(x + rnd(i, 141) * w).toFixed(0)}" cy="${(y + rnd(i, 142) * h).toFixed(0)}" r="${((1 + rnd(i, 143)) * s).toFixed(1)}" fill="#fff" fill-opacity=".75"/>`).join("");
    return d + `</g>`;
  }
  const snowfall = (x, y, w, h, s) => { let f = ""; for (let i = 0; i < 40; i++) f += `<circle cx="${(x + rnd(i, 241) * w).toFixed(0)}" cy="${(y + rnd(i, 242) * h).toFixed(0)}" r="${((0.9 + rnd(i, 243) * 1.4) * s).toFixed(1)}" fill="#fff" fill-opacity=".8"/>`; return `<g class="sk-snw" style="--sh:${h.toFixed(0)}px">${f}<g transform="translate(0,${-h.toFixed(0)})">${f}</g></g>`; };
  function clockAt(ctx, x, y, r, s, face = "#ecdfc3") {
    const [hh, mm] = CLOCK[ctx.phase], ha = (hh % 12) / 12 * 2 * Math.PI - Math.PI / 2, ma = (mm % 60) / 60 * 2 * Math.PI - Math.PI / 2;
    return `<circle cx="${x}" cy="${y}" r="${r}" fill="${face}" stroke="${K2}" stroke-width="${2 * s}"/><circle cx="${x}" cy="${y}" r="${r * 0.8}" fill="none" stroke="${K2}" stroke-width="${s}" stroke-dasharray="${1.2 * s} ${r * 0.8 * 0.5236 - 1.2 * s}"/>`
      + `<path d="M${x},${y} l${Math.cos(ha) * r * 0.5},${Math.sin(ha) * r * 0.5} M${x},${y} l${Math.cos(ma) * r * 0.72},${Math.sin(ma) * r * 0.72}" stroke="${K2}" stroke-width="${2.2 * s}" stroke-linecap="round"/><circle cx="${x}" cy="${y}" r="${1.8 * s}" fill="${K2}"/>`;
  }
  /* the window behind the puppet: brass, rounded corners, the blind rolled at the top, frost, the country rolling past */
  function carWindow(ctx, sh, c) {
    const { s, H, W, cx, x0, x1, dado } = sh, ww = Math.min(0.5 * W, x1 - x0 - 0.3 * W), wx = cx - ww / 2, wy = 0.12 * H, wh = dado - 0.04 * H - wy, rr = 0.04 * H;
    let d = `<rect x="${wx - 10 * s}" y="${wy - 10 * s}" width="${ww + 20 * s}" height="${wh + 20 * s}" rx="${rr + 8 * s}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${2.2 * s}"/>` + winSky(ctx, c, wx, wy, ww, wh, s, { orb: true, r: rr }) + `<g clip-path="url(#${ctx.P}ws${Math.round(wx)}c)">${snowfall(wx, wy, ww, wh, s)}</g>`;
    d += `<rect x="${wx}" y="${wy}" width="${ww}" height="${wh}" rx="${rr}" fill="none" stroke="#2a180c" stroke-width="${3 * s}"/>`;
    for (const [kx, ky, dx, dy] of [[wx, wy, 1, 1], [wx + ww, wy, -1, 1], [wx, wy + wh, 1, -1], [wx + ww, wy + wh, -1, -1]]) d += `<path d="M${kx},${ky + dy * wh * 0.28} Q${kx + dx * ww * 0.06},${ky + dy * wh * 0.1} ${kx + dx * ww * 0.16},${ky}" fill="#fff" fill-opacity=".38"/>`;
    d += `<rect x="${wx - 4 * s}" y="${wy - 22 * s}" width="${ww + 8 * s}" height="${14 * s}" rx="${7 * s}" fill="#efe4cb" stroke="${K2}" stroke-width="${2 * s}"/><path d="M${wx + ww / 2},${wy - 8 * s} v${16 * s}" stroke="#2a180c" stroke-width="${2 * s}"/><circle cx="${wx + ww / 2}" cy="${wy + 12 * s}" r="${5 * s}" fill="none" stroke="${CAR.brass}" stroke-width="${2 * s}"/>`;
    d += `<rect x="${wx - 12 * s}" y="${wy + wh + 14 * s}" width="${ww + 24 * s}" height="${8 * s}" rx="${4 * s}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${1.6 * s}"/>`;
    sh.winL = wx - 0.02 * W; sh.winR = wx + ww + 0.02 * W; ctx.special(wx + ww / 2, wy + wh, ww * 0.55, 0.45);
    return { d: cutout(ctx.P, s, d, 1), emit: "", glows: [], wins: [[wx, wy, ww, wh]] };
  }
  /* the right piece: an iron carriage lantern, six-sided, peaked roof and finial, on a scrolled bracket from a round plate */
  function lantern(ctx, sh, c, slot) {
    const { s, H, W } = sh, x = (slot[0] + slot[1]) / 2, y = 0.3 * H, iron = "#1c1a18", glows = []; let d = "", emit = "";
    const px = x - 0.032 * W, py = y + 0.1 * H;
    d += `<circle cx="${px}" cy="${py}" r="${12 * s}" fill="${iron}" stroke="${K2}" stroke-width="${1.6 * s}"/><circle cx="${px}" cy="${py}" r="${5 * s}" fill="#3a3a3a"/><path d="M${px},${py} h${0.02 * W} q${0.02 * W},0 ${0.025 * W},${-0.04 * H} V${y + 0.03 * H}" fill="none" stroke="${iron}" stroke-width="${5 * s}" stroke-linecap="round"/><path d="M${px + 0.02 * W},${py} q${0.012 * W},${-0.01 * H} ${0.01 * W},${-0.03 * H}" fill="none" stroke="${iron}" stroke-width="${3 * s}" stroke-linecap="round"/>`;
    const bw = 0.042 * W, bh = 0.075 * H, bx = x - bw / 2, by = y - bh * 0.5;
    d += `<rect x="${bx - 6 * s}" y="${by + bh}" width="${bw + 12 * s}" height="${8 * s}" rx="${2 * s}" fill="${iron}" stroke="${K2}" stroke-width="${1.6 * s}"/>`;
    const glass = c.lit ? "#ffd27a" : "#f1e6c8", gop = c.lit ? 0.95 : 0.55;
    d += `<path d="M${bx - 8 * s},${by + 6 * s} L${bx},${by} V${by + bh} L${bx - 8 * s},${by + bh - 4 * s}Z" fill="${glass}" fill-opacity="${gop * 0.7}" stroke="${iron}" stroke-width="${2.2 * s}"/><path d="M${bx + bw + 8 * s},${by + 6 * s} L${bx + bw},${by} V${by + bh} L${bx + bw + 8 * s},${by + bh - 4 * s}Z" fill="${glass}" fill-opacity="${gop * 0.7}" stroke="${iron}" stroke-width="${2.2 * s}"/>`;
    d += `<rect x="${bx}" y="${by}" width="${bw}" height="${bh}" fill="${glass}" fill-opacity="${gop}" stroke="${iron}" stroke-width="${2.4 * s}"/><path d="M${bx + bw / 2},${by} V${by + bh}" stroke="${iron}" stroke-width="${1.6 * s}" stroke-opacity=".6"/>`;
    d += inkP(`M${bx - 12 * s},${by} L${x},${by - bh * 0.45} L${bx + bw + 12 * s},${by}Z`, iron, 2 * s) + `<rect x="${x - 3 * s}" y="${by - bh * 0.62}" width="${6 * s}" height="${bh * 0.2}" fill="${iron}"/><circle cx="${x}" cy="${by - bh * 0.66}" r="${4 * s}" fill="${iron}" stroke="${K2}" stroke-width="${1.2 * s}"/>`;
    ctx.special(x, by + bh, 0.055 * W, 0.85);
    const hid = ctx.P + "lh" + Math.round(x), halo = c.lit ? 0.34 : 0.1, rr = c.lit ? 0.26 * H : 0.09 * H;
    emit += `<defs><radialGradient id="${hid}" cx="${x}" cy="${y}" r="${rr.toFixed(0)}" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#ffd27a" stop-opacity="${halo}"/><stop offset=".35" stop-color="#ffb35c" stop-opacity="${(halo * 0.5).toFixed(2)}"/><stop offset="1" stop-color="#ffb35c" stop-opacity="0"/></radialGradient></defs><circle cx="${x}" cy="${y}" r="${rr.toFixed(0)}" fill="url(#${hid})"/>`;
    if (c.lit) { emit += `<path d="M${x - bw * 0.7},${by + bh} L${x - 0.11 * W},${sh.floorY} H${x + 0.11 * W} L${x + bw * 0.7},${by + bh}Z" fill="#ffb35c" opacity=".09"/>` + flameAt(x, y + 0.005 * H, 1.2 * s); glows.push([x, y, 0.3 * H, "#ffb35c"]); } else glows.push([x, y, 0.06 * H, "#ffb35c"]);
    return { d: cutout(ctx.P, s, d, 1), emit, glows, wins: [] };
  }
  /* the left piece: a wall clock hung by its ring on a long string from above, keeping the phase's time */
  function wallClock(ctx, sh, c, slot) {
    const { s, H } = sh, x = (slot[0] + slot[1]) / 2, y = 0.3 * H, r = Math.min(0.085 * H, (slot[1] - slot[0]) * 0.48); let d = "";
    ctx.special(x, y + r, r * 1.35);
    d += twine(x, 0, x, y - r - 0.03 * H, s) + `<circle cx="${x}" cy="${y - r - 0.018 * H}" r="${8 * s}" fill="none" stroke="${CAR.brass}" stroke-width="${3 * s}"/><rect x="${x - 5 * s}" y="${y - r - 0.01 * H}" width="${10 * s}" height="${0.012 * H}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${1.2 * s}"/>`;
    d += `<circle cx="${x}" cy="${y}" r="${r}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${2.4 * s}"/>` + clockAt(ctx, x, y, r * 0.8, s);
    for (let k = 0; k < 12; k++) { const a = k / 12 * Math.PI * 2; d += `<circle cx="${(x + Math.cos(a) * r * 0.66).toFixed(1)}" cy="${(y + Math.sin(a) * r * 0.66).toFixed(1)}" r="${(k % 3 ? 1.4 : 2.4) * s}" fill="${K2}"/>`; }
    return { d: `<g class="sk-hang">${cutout(ctx.P, s, d, 1)}</g>`, emit: "", glows: [], wins: [] };
  }
  function roomLight(ctx, f, wins, glows) {
    const Lt = ROOMLIGHT[ctx.phase], P = ctx.P; let d = ""; ctx.glows = glows.map(([x, y, r]) => [x, y, r * 0.55, Lt.glow]);
    if (Lt.tint) d += `<defs><mask id="${P}rmask" maskUnits="userSpaceOnUse" x="0" y="0" width="${f.W}" height="${f.H}"><rect width="${f.W}" height="${f.H}" fill="#fff"/>${wins.map(([x, y, w, h]) => `<rect x="${x}" y="${y}" width="${w}" height="${h}" fill="#000"/>`).join("")}</mask></defs>
      <rect width="${f.W}" height="${f.H}" fill="${Lt.tint}" opacity="${Lt.a}" mask="url(#${P}rmask)" style="mix-blend-mode:multiply"/>`;
    d += `<defs>${glows.map(([, , , col], i) => `<radialGradient id="${P}rg${i}"><stop offset="0" stop-color="${col}" stop-opacity=".55"/><stop offset=".4" stop-color="${col}" stop-opacity=".18"/><stop offset="1" stop-color="${col}" stop-opacity="0"/></radialGradient>`).join("")}</defs>`;
    d += glows.map(([x, y, r], i) => `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(0)}" fill="url(#${P}rg${i})" opacity="${Lt.glow}" style="mix-blend-mode:screen"/>`).join("");
    d += ctx.specials.map(([x, y0, y1, rx]) => beam(x, y0, y1, rx, ctx.dark)).join("");
    return d;
  }

  /* ---------- the scene ---------- */
  function scene(g, phase, o = {}) {
    const P = (o.id || "sk") + "-", c = PHASES[phase], W = g.Wf, H = g.H, s = g.s, B = g.railY, cx = g.cx, pw = g.pwid;
    const ctx = { P, phase, dark: o.dark == null ? 50 : o.dark, specials: [], glows: [] };
    ctx.special = (x, y1, rx, a = 0.9, y0 = 0) => ctx.specials.push([x, y0, y1, rx, a]);
    const floorH = 0.065 * H, floorY = B - floorH, dado = floorY - CAR.dadoH * H;
    let d = `<defs><filter id="${P}shadf" x="-10%" y="-10%" width="120%" height="120%"><feFlood flood-color="#000" flood-opacity=".5"/><feComposite in2="SourceAlpha" operator="in"/><feGaussianBlur stdDeviation="${(5 * s).toFixed(1)}"/></filter>
      <filter id="${P}grain" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".9" numOctaves="2" seed="7" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/><feComponentTransfer><feFuncA type="linear" slope=".55"/></feComponentTransfer></filter>
      <linearGradient id="${P}qfade" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="#0c0a07" stop-opacity=".95"/><stop offset=".12" stop-color="#0c0a07" stop-opacity="0"/><stop offset=".88" stop-color="#0c0a07" stop-opacity="0"/><stop offset="1" stop-color="#0c0a07" stop-opacity=".95"/></linearGradient></defs>`;
    d += `<rect width="${W}" height="${H}" fill="#0c0a07"/>`;
    // the back flat: walnut, its panel lines, the dado and its brass rail; hazed toward one value, its ends fading into the dark
    d += `<rect x="0" y="0" width="${W}" height="${floorY}" fill="${CAR.wall}"/>`;
    for (let px = 0; px < W; px += 0.08 * W) d += `<path d="M${px.toFixed(0)},0 V${dado}" stroke="${CAR.wallDark}" stroke-width="${4 * s}"/>`;
    d += `<rect x="0" y="${dado}" width="${W}" height="${floorY - dado}" fill="${CAR.dado}"/><rect x="0" y="${dado - 4 * s}" width="${W}" height="${8 * s}" fill="${CAR.brass}" stroke="${K2}" stroke-width="${1.4 * s}"/>`;
    d += `<rect x="0" y="0" width="${W}" height="${floorY}" fill="${CAR.wallDark}" opacity=".38"/><rect x="0" y="0" width="${W}" height="${floorY}" fill="url(#${P}qfade)"/>`;
    // the stage floor: boards with one seam, and the trapdoor under the puppet (a seam and a hinge line; its front edge hidden by the stand)
    d += `<rect x="0" y="${floorY}" width="${W}" height="${floorH}" fill="${BOARD}"/><path d="M0,${(floorY + floorH / 2).toFixed(0)} H${W}" stroke="${BOARD2}" stroke-width="${1.6 * s}" opacity=".7"/><rect x="0" y="${floorY}" width="${W}" height="${floorH}" fill="url(#${P}qfade)"/>`;
    const tw = pw * 0.9, tx = cx - tw / 2, ty = floorY + floorH * 0.3;
    d += `<rect x="${tx}" y="${ty}" width="${tw}" height="${B - ty}" fill="${BOARD}" stroke="#2a1a0c" stroke-width="${2.4 * s}"/><path d="M${tx + 10 * s},${ty + 6 * s} H${tx + tw - 10 * s}" stroke="#2a1a0c" stroke-width="${2 * s}"/>`;
    const sh = { W, H, s, B, cx, pw, x0: 0, x1: W, dado, floorY, floorH };
    const edge = 0.03 * W, slotL = [edge, cx - pw * 0.55 - 0.02 * W], slotR = [cx + pw * 0.55 + 0.02 * W, W - edge];
    const parts = [carWindow(ctx, sh, c)];
    slotL[1] = Math.min(slotL[1], sh.winL); slotR[0] = Math.max(slotR[0], sh.winR);
    if (slotL[1] - slotL[0] > 0.06 * W) parts.push(wallClock(ctx, sh, c, slotL));
    if (slotR[1] - slotR[0] > 0.06 * W) parts.push(lantern(ctx, sh, c, slotR));
    const wins = [], glows = []; let emit = "";
    for (const p of parts) { d += p.d; emit += p.emit; glows.push(...p.glows); wins.push(...p.wins); }
    d += roomLight(ctx, { W, H }, wins, glows) + emit;
    d += `<rect width="${W}" height="${H}" fill="#fff" filter="url(#${P}grain)" opacity=".1" style="mix-blend-mode:overlay"/>`;
    const dim = o.dim == null ? 10 : o.dim;
    return { html: `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg">${d}</svg><div style="position:absolute;inset:0;background:#0c0a07;opacity:${dim / 100}"></div>`,
      glows: ctx.glows, specials: ctx.specials, floor: { floorY, floorH, B, trap: [tx, ty, tw, B - ty] }, slots: { L: slotL, R: slotR }, window: parts[0].wins[0] };
  }

  /* ---------- light: darkness outside the pool; the room's glows and the specials left open ---------- */
  function light(g, sc, o = {}) {
    const P = (o.id || "sk") + "-", W = g.Wf, H = g.H, p = g.pwid, dark = (o.dark == null ? 50 : o.dark) / 100;
    const e = o.pool || (o.from === "over" ? { x: g.cx, y: g.railY - p * 0.95, rx: p * 0.58, ry: p * 0.95 } : { x: g.cx, y: g.railY - p * 0.1, rx: p * 0.66, ry: p * 0.82 });
    const blur = p * 0.16, glows = sc.glows.concat(o.glows || []), specials = sc.specials.concat(o.specials || []);
    const svg = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%"><defs><filter id="${P}lbl" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation="${blur.toFixed(0)}"/></filter><mask id="${P}lmask" maskUnits="userSpaceOnUse" x="0" y="0" width="${W}" height="${H}"><rect width="${W}" height="${H}" fill="#fff"/><ellipse cx="${e.x.toFixed(0)}" cy="${e.y.toFixed(0)}" rx="${e.rx.toFixed(0)}" ry="${e.ry.toFixed(0)}" fill="#000" filter="url(#${P}lbl)"/>`
      + glows.map(([x, y, r, a]) => `<circle cx="${x.toFixed(0)}" cy="${y.toFixed(0)}" r="${r.toFixed(0)}" fill="#000" opacity="${a}" filter="url(#${P}lbl)"/>`).join("")
      + specials.map(([x, y0, y1, rx, a]) => `<rect x="${(x - rx).toFixed(0)}" y="${y0}" width="${(2 * rx).toFixed(0)}" height="${(y1 - y0 + rx * 0.6).toFixed(0)}" rx="${rx.toFixed(0)}" fill="#000" opacity="${a}" filter="url(#${P}lbl)"/>`).join("")
      + `</mask></defs><rect width="${W}" height="${H}" fill="#0c0a07" opacity="${dark}" mask="url(#${P}lmask)"/></svg>`;
    const glow = `<div style="position:absolute;inset:0;mix-blend-mode:screen;background:radial-gradient(ellipse ${(e.rx * 0.9).toFixed(0)}px ${(e.ry * 0.9).toFixed(0)}px at ${e.x.toFixed(0)}px ${e.y.toFixed(0)}px, rgba(255,179,92,.16), rgba(255,179,92,0) 70%)"></div>`;
    return svg + glow;
  }

  /* ---------- the replay's dressing: curtains drawn back with gold tie-backs, a valance, the scalloped border, the proscenium ---------- */
  function dressing(g, o = {}) {
    const P = (o.id || "sk") + "-", W = g.Wf, H = g.H, s = g.s, m = MATERIALS, floorY = g.railY - 0.065 * H, bot = floorY + 0.065 * H * 0.85, red = "#8a2a24", fold = "#6a1e1a", gold = "#c9a25e";
    let d = `<svg viewBox="0 0 ${W} ${H}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0;width:100%;height:100%"><defs><filter id="${P}dshadf" x="-10%" y="-10%" width="120%" height="120%"><feFlood flood-color="#000" flood-opacity=".5"/><feComposite in2="SourceAlpha" operator="in"/><feGaussianBlur stdDeviation="${(5 * s).toFixed(1)}"/></filter></defs>`;
    const leg = (x, dir) => { const wTop = 0.17 * W, wTie = 0.09 * W, tieY = 0.52 * H;
      let q = inkP(`M${x},0 H${x + dir * wTop} C${x + dir * wTop * 0.9},${tieY * 0.5} ${x + dir * wTie},${tieY - 0.04 * H} ${x + dir * wTie},${tieY} C${x + dir * wTie * 1.1},${tieY + 0.1 * H} ${x + dir * wTop * 0.95},${bot - 0.06 * H} ${x + dir * wTop * 0.85},${bot} H${x}Z`, red, 2.4 * s);
      for (let i = 1; i < 5; i++) { const t = i / 5; q += `<path d="M${x + dir * wTop * t},${4 * s} C${x + dir * wTop * t * 0.9},${tieY * 0.5} ${x + dir * wTie * t},${tieY - 0.04 * H} ${x + dir * wTie * t},${tieY} C${x + dir * wTie * t * 1.1},${tieY + 0.1 * H} ${x + dir * wTop * t * 0.95},${bot - 0.06 * H} ${x + dir * wTop * t * 0.85},${bot - 4 * s}" fill="none" stroke="${fold}" stroke-width="${3 * s}"/>`; }
      q += `<path d="M${x},${tieY - 0.01 * H} q${dir * wTie * 0.6},${-0.03 * H} ${dir * wTie * 1.15},${0.01 * H}" fill="none" stroke="${gold}" stroke-width="${4 * s}" stroke-linecap="round"/><path d="M${x + dir * wTie * 1.12},${tieY} v${0.03 * H} m${-6 * s},0 h${12 * s} l${-2 * s},${0.02 * H} h${-8 * s}Z" fill="${gold}" stroke="${K2}" stroke-width="${1.6 * s}"/>`;
      return q + `<path d="M${x},${bot} H${x + dir * wTop * 0.85}" stroke="${gold}" stroke-width="${3.5 * s}"/>`; };
    d += `<g filter="url(#${P}dshadf)" opacity=".6" transform="translate(${(6 * s).toFixed(1)},${(5 * s).toFixed(1)})">${leg(0, 1)}${leg(W, -1)}</g>` + leg(0, 1) + leg(W, -1);
    d += `<rect x="0" y="0" width="${W}" height="${0.075 * H}" fill="#4a1418"/>`;
    let hem = `M0,${0.075 * H}`; for (let x = 0; x < W; x += 0.08 * W) hem += ` q${0.04 * W},${0.025 * H} ${0.08 * W},0`;
    d += `<path d="${hem} V0 H0Z" fill="#4a1418"/><path d="${hem}" fill="none" stroke="${gold}" stroke-width="${3 * s}"/><path d="M0,${0.012 * H} H${W}" stroke="${gold}" stroke-width="${2 * s}" stroke-opacity=".7"/>`;
    let sc = ""; for (let x = -80 * s; x < W + 160 * s; x += 160 * s) sc += `M${x.toFixed(0)},0 V${(30 * s).toFixed(0)} a${80 * s},${66 * s} 0 0 0 ${160 * s},0 V0Z`;
    d += `<path d="${sc}" fill="${m.border}"/>`;
    let fr = ""; for (let x = -80 * s; x < W + 160 * s; x += 160 * s) fr += `M${x.toFixed(0)},${(30 * s).toFixed(0)} a${80 * s},${66 * s} 0 0 0 ${160 * s},0`;
    d += `<path d="${fr}" fill="none" stroke="${m.frameLine}" stroke-width="${3 * s}"/>`;
    const pw = W * 0.035; d += `<rect x="0" y="0" width="${pw}" height="${H}" fill="${m.border}"/><rect x="${W - pw}" y="0" width="${pw}" height="${H}" fill="${m.border}"/><path d="M${pw},0 V${H} M${W - pw},0 V${H}" stroke="${m.frameLine}" stroke-width="${3 * s}"/><path d="M${pw * 0.45},${H * 0.12} V${H * 0.9} M${W - pw * 0.45},${H * 0.12} V${H * 0.9}" stroke="${m.frameLine}" stroke-opacity=".5" stroke-width="${2 * s}"/>`;
    return d + `</svg>`;
  }

  /* ---------- the own stand (stage blockout, locked 2026-09-21; drawn as the X-ray bench draws it, revision 51) ---------- */
  function stand(g, o = {}) {
    const u = g.u, cx = g.cx, lit = o.lit !== false;
    const pit = `<div class="sk-stand" style="top:${g.railY.toFixed(0)}px">`;
    if (o.box === false) return pit + `</div>`;
    const domes = [-130, 90].map((dx) => `<i class="sk-fl${lit ? " on" : ""}" style="left:calc(50% + ${dx} * var(--u))"></i>`).join("");
    return pit + `<div class="sk-wbox" style="left:${(cx - 302.5 * u).toFixed(0)}px;width:${(605 * u).toFixed(0)}px;--u:${u}px">${domes}<div class="sk-plaque">Seat ${o.seat}${o.tag ? `<span class="sk-role ${o.tagClass || ""}">${o.tag}</span>` : ""}</div></div></div>`;
  }

  const CSS = `
.sk-stand{position:absolute;left:0;right:0;bottom:0;overflow:visible;background:linear-gradient(180deg,rgba(12,10,7,.3),rgba(12,10,7,.62) 40%,rgba(12,10,7,.82))}
.sk-wbox{position:absolute;top:0;bottom:0;background:linear-gradient(180deg,var(--cloak0) 0 calc(39*var(--u)),var(--cloak1) calc(39*var(--u)))}
.sk-wbox::before{content:"";position:absolute;z-index:1;left:calc(-14*var(--u));right:calc(-14*var(--u));top:0;height:calc(30*var(--u));border-radius:calc(4*var(--u));
  background:linear-gradient(180deg,var(--bone3) 0 calc(3*var(--u)),#5c432a calc(3*var(--u)),var(--cloak2) calc(15*var(--u)),#42301e);box-shadow:0 calc(4*var(--u)) calc(8*var(--u)) rgba(0,0,0,.45)}
.sk-wbox::after{content:"";position:absolute;left:calc(26*var(--u));right:calc(26*var(--u));top:calc(82*var(--u));height:calc(330*var(--u));border-radius:calc(6*var(--u));
  background:#1b120b;border:calc(3*var(--u)) solid var(--cloak2);box-shadow:inset 0 calc(6*var(--u)) calc(10*var(--u)) rgba(0,0,0,.45)}
.sk-fl{position:absolute;z-index:2;top:calc(-16*var(--u));width:calc(40*var(--u));height:calc(20*var(--u));box-sizing:border-box;border-radius:calc(20*var(--u)) calc(20*var(--u)) 0 0;background:var(--bone3);border:calc(3*var(--u)) solid var(--ink);border-bottom:0}
.sk-fl.on{background:var(--bone);box-shadow:0 calc(-4*var(--u)) calc(22*var(--u)) rgba(255,179,92,.55)}
.sk-plaque{position:absolute;left:50%;top:calc(3*var(--u));z-index:3;transform:translateX(-50%);display:flex;gap:.5cqw;align-items:center;background:var(--bone2);color:var(--ink);white-space:nowrap;font-weight:600;
  min-height:calc(34*var(--u));box-sizing:border-box;border:calc(2.5*var(--u)) solid var(--ink);border-radius:calc(5*var(--u));font-size:max(var(--meta,1cqw),calc(17*var(--u)));padding:0 calc(10*var(--u));box-shadow:0 calc(3*var(--u)) calc(6*var(--u)) rgba(0,0,0,.4)}
.sk-role{font-weight:500;padding:0 .5cqw;border-radius:.2cqw;color:#fff}
@media (prefers-reduced-motion:no-preference){
  .sk-hang{animation:sk-sway 7s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:50% -60%}
  .sk-flk{animation:sk-flk .45s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:50% 100%}
  .sk-scrl{animation:sk-scrl 5s linear infinite}
  .sk-snw{animation:sk-snw 7s linear infinite}
}
@keyframes sk-sway{from{transform:rotate(-1.1deg)}to{transform:rotate(1.1deg)}}
@keyframes sk-flk{to{transform:scale(.88,1.1) rotate(-3deg)}}
@keyframes sk-scrl{to{transform:translateX(calc(-1 * var(--p)))}}
@keyframes sk-snw{to{transform:translateY(var(--sh))}}`;
  function install() { if (typeof document === "undefined" || document.getElementById("stage-kit-css")) return; const el = document.createElement("style"); el.id = "stage-kit-css"; el.textContent = CSS; document.head.appendChild(el); }
  function vars() { const m = MATERIALS; return { "--ink": m.ink, "--bone": m.bone, "--bone2": m.bone2, "--bone3": m.bone3, "--cloak0": m.cloak0, "--cloak1": m.cloak1, "--cloak2": m.cloak2, "--paper": m.paper, "--paper-ink": m.paperInk, "--glass-top": m.glassTop, "--glass-bot": m.glassBot,
    "--film": m.film, "--film-ink": m.filmInk, "--film-text": m.filmText, "--film-main": m.filmMain, "--film-mut": m.filmMut, "--film-line": m.filmLine, "--film-border": m.filmBorder, "--sure": m.sure, "--slip": m.slip, "--slip-ink": m.slipInk, "--slip-rule": m.slipRule,
    "--amber": m.amber, "--town": m.town, "--wolf": m.wolf, "--sk": m.sk, "--town-ink": m.townInk, "--wolf-ink": m.wolfInk, "--sk-ink": m.skInk }; }

  return { VERSION, MATERIALS, PHASES, ROOMLIGHT, CLOCK, geometry, scene, light, dressing, stand, CSS, install, vars,
    draw: { inkP, stitch, twine, flameAt, cutout, beam, K2, rnd, mix, BOARD, BOARD2, brass: CAR.brass } };
})();
