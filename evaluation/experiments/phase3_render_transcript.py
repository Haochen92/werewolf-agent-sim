"""(evaluation/experiments/phase3_render_transcript.py; run: poetry run python -m evaluation.experiments.phase3_render_transcript <batch dir> <label> <out.md>)
Render one captured ten-seat game as a readable transcript: roles, each day's lines (speaker,
true role, the claim field), the summary agents carry forward, the vote, then the night (the
pack's chat, every real choice, each actor's private record) and the evil seats' strategy notes."""
import json, sys, collections
from pathlib import Path

base = Path(sys.argv[1]); label = sys.argv[2]; out = Path(sys.argv[3])
rec = json.load(open(base / f"{label}.record.json"))
roles = rec["roles"]
EVIL = {"chanteuse", "illusionist", "serial_killer", "necromancer"}
evil = {p for p, r in roles.items() if r in EVIL}

wolf_chat = []; notes = collections.defaultdict(list); cur_day = 1; phase = "day"
for line in open(base / f"{label}.chunks.jsonl"):
    ch = json.loads(line)
    if ch["type"] != "updates":
        continue
    for node, delta in (ch["data"] or {}).items():
        if not isinstance(delta, dict):
            continue
        for e in delta.get("day_channel") or []:
            cur_day, phase = e["day"], "day"
        if delta.get("night_choices"):
            phase = "night"
        for e in delta.get("wolf_channel") or []:
            wolf_chat.append(e)
        for p, note in (delta.get("agent_strategies") or {}).items():
            if p in evil and (not notes[p] or notes[p][-1][2] != note):
                notes[p].append((cur_day, phase, note))

def who(p):
    return f"{p} ({roles.get(p, '?')})"

L = [f"# {label}  winner={rec['winner']}  neutral={rec['neutral_result']}", "",
     "Roles: " + ", ".join(f"{p}={r}" for p, r in sorted(roles.items(), key=lambda x: int(x[0].split('_')[1]))), ""]
nights = {n["day"]: n for n in rec["night_resolutions"]}
votes = {d["day"]: d for d in rec["day_resolutions"]}
summaries = {s["day"]: s for s in rec["day_summaries"] if s.get("source") != "game_master"}
for day in range(1, rec["current_day"] + 1):
    L += [f"================ DAY {day} ================"]
    for e in sorted([e for e in rec["day_channel"] if e["day"] == day], key=lambda e: e["seq"]):
        if e["player"] == "game_master":
            L.append(f"[GM] {e['message']}")
        elif e.get("passed"):
            if e.get("gated_candidate"):
                L.append(f"  {who(e['player'])} [HELD by the filter, table never heard it]: {e['gated_candidate']}")
            continue
        else:
            claim = e.get("claim", "none")
            L.append(f"  {who(e['player'])}" + (f" [claim field: {claim}]" if claim != "none" else "") + f" <{e.get('day_round','discussion')}>: {e['message']}")
    if day in summaries:
        L += ["", f"-- Day {day} summary (what agents read on later days) --", summaries[day]["summary"]]
    if day in votes:
        v = votes[day]
        L += ["", f"-- Day {day} vote -- " + ", ".join(f"{x['voter']}->{x['votee']}" for x in (v.get("votes") or []))
              + f"  => voted out: {who(v['voted_player']) if v.get('voted_player') else 'nobody'}"]
    if day in nights:
        n = nights[day]
        L += ["", f"================ NIGHT {day} ================"]
        chat = [e for e in wolf_chat if e["day"] == day]
        if chat:
            L.append("-- pack chat (private to wolves) --")
            for e in chat:
                if e.get("vote"):
                    L.append(f"  {who(e['wolf'])} names the kill: {e['vote']}")
                elif e.get("passed"):
                    L.append(f"  {who(e['wolf'])} passes")
                else:
                    L.append(f"  {who(e['wolf'])} r{e['round']}: {e['message']}")
        L.append("-- what everyone actually did --")
        for c in n["choices"]:
            L.append(f"  {who(c['actor'])} {c['kind']} -> {c['target']}" + (f" via body of {who(c['via'])}" if c.get("via") else "")
                     + (f" naming {c['role_named']}" if c.get("role_named") else "")
                     + ("  [BLOCKED]" if c["actor"] in n.get("blocked", []) else ""))
        L.append(f"-- deaths: {', '.join(who(p) for p in n['deaths']) or 'none'}")
        L.append("-- private records (each actor's own) --")
        for a in rec["night_actions"]:
            if a["day"] == day:
                L.append(f"  {a['actor']}: {a['outcome']}")
    for p in sorted(evil):
        for d, ph, note in notes[p]:
            if d == day:
                L.append(f"  [strategy note, {who(p)}, {ph} {d}]: {note}")
    L.append("")
out.write_text("\n".join(L))
print(out, len(L), "lines")
