/* Cast module: expects a global DAYCAST = { <character>: { base|talking|thinking|out|chip: {w,h,src}, body:{top,body} } }; see sprites/manifest.json and sprites/day/. */
const Cast = {
  states: { idle: "base", talking: "talking", out: "out", thinking: "thinking" },
  // a figure at the stand: feet on the rail, one body height for every character (ears and hats rise above), the seat numeral drawn on the belly
  pup(g, id, seat, state, extra) { const C = DAYCAST[id], P = C[Cast.states[state] || "base"], bodyH = g.ph * 0.98, h = bodyH / C.body.body, w = h * P.w / P.h, top = g.railY - h * (C.body.top + C.body.body) + h * C.body.body * 0.08;
    return `<div class="pup raster${extra && extra.cls ? " " + extra.cls : ""}" style="left:${(g.cx - w / 2).toFixed(0)}px;top:${top.toFixed(0)}px;width:${w.toFixed(0)}px;height:${h.toFixed(0)}px${extra && extra.style ? extra.style : ""}"><img src="${P.src}" alt=""><svg class="numeral" viewBox="0 0 100 100" style="left:${(50 - 12).toFixed(0)}%;top:${(C.body.top * 100 + C.body.body * 100 * 0.62 - 12 * P.w / P.h).toFixed(0)}%;width:24%;height:${(24 * P.w / P.h).toFixed(1)}%"><circle cx="50" cy="50" r="46" fill="#efe4cb" stroke="#24180c" stroke-width="5"/><circle cx="50" cy="50" r="36" fill="none" stroke="#8d7a55" stroke-width="3" stroke-dasharray="6 5"/><text x="50" y="68" text-anchor="middle" font-family="'IM Fell English',Georgia,serif" font-size="54" fill="#24180c">${seat}</text></svg></div>`; },
  chip(id) { return `<img class="rchip" src="${DAYCAST[id].chip.src}" alt="">`; },
};
