# Node-factory collapse — day & night actor nodes

Part of the pre-v5 structural pass. Two commits:
- `d37369f` — day discuss/vote nodes → two factories (`Agents/nodes/day/actors.py`)
- `1db5d7b` — single-actor night nodes → shared factory (`Agents/nodes/night/factory.py`)

Behaviour-neutral. Acceptance gate held on both: 95 tests, import-sweep 0 failed,
`runtime_fingerprint` byte-identical (`prompt_bundle_hash c35e68e2d0cca9f0`), ruff clean.

---

## What the BEFORE was for

In LangGraph a node is addressed by a **string name** in the graph topology. The
day graph registers one node per role and routes a speaker to the node *named
after their role*:

```python
# graphs/day.py
day_graph.add_node("villager_discuss", villager_discuss)
day_graph.add_node("wolf_discuss",     wolf_discuss)
...
# the scheduler dispatches by name:
return Send(f"{role}_discuss", payload)        # nodes/day/flow.py
```

So the codebase needed a distinct *registered* node per role. The original
implementation satisfied that with one hand-written function per role — 12 for
day (6 roles × discuss/vote), 4 for the single-actor night roles. Each looked
like this:

```python
# BEFORE — nodes/day/actors.py (×12)
def villager_discuss(payload: VillagerDayState, config, runtime):
    return _run_memory_informed_action(
        payload, config, runtime,
        "day_discussion", VILLAGER_DAY_DISCUSS, DayDiscussOutput, "day_channel",
    )

def wolf_discuss(payload: WolfDayState, config, runtime):
    return _run_memory_informed_action(
        payload, config, runtime,
        "day_discussion", WOLF_DAY_DISCUSS, DayDiscussOutput, "day_channel",
    )
# ... 10 more, identical except the prompt
```

That's the key observation: **the bodies are identical.** A discuss node differs
from another discuss node only by its prompt. A discuss node differs from a vote
node only by four constants (`action_phase`, prompt, output schema, output key).
Everything that does real work lives one layer down in the shared engine
(`_run_memory_informed_action` / `_run_memory_informed_night_action`). The
per-role functions were *plumbing to give the engine a name the graph can route
to* — not 12 different behaviours.

## Why the AFTER is the same — just much less code

Replace the 12 (and 4) repeated bodies with a factory that closes over the
varying constants and returns the wrapper:

```python
# AFTER — nodes/day/actors.py
def _make_discuss_node(prompt, state_type=VillagerDayState):
    def discuss(payload: state_type, config, runtime):
        return _run_memory_informed_action(
            payload, config, runtime,
            "day_discussion", prompt, DayDiscussOutput, "day_channel",
        )
    return discuss

villager_discuss = _make_discuss_node(VILLAGER_DAY_DISCUSS, VillagerDayState)
wolf_discuss     = _make_discuss_node(WOLF_DAY_DISCUSS, WolfDayState)
# ... one line per role
```

The produced function is **the same callable the graph had before** — same engine
call, same constants, registered under the same string name. The factory is just
a different way to *write* the 12 functions; it is not a different runtime object
in any way the graph or the engine can observe. Three facts make that exact, not
approximate:

1. **Node identity is the registration string, not the function.** `graphs/day.py`
   still does `add_node("villager_discuss", villager_discuss)` and the scheduler
   still routes `Send("villager_discuss", payload)`. The factory changes *how the
   function is built*, never its registered name.

2. **The first-arg type annotation was always cosmetic.** These nodes are reached
   via `Send(name, payload)` with an **explicitly constructed payload**, so
   LangGraph passes that dict through — it never used the annotation to filter
   state. We preserve each role's annotation anyway (the factory takes
   `state_type`), so even that documentation is unchanged. (Note SK and vigilante
   share `VillagerDayState` in both before and after — that was already the case.)

3. **Nothing reads `func.__name__`.** Grep confirms the only `__name__` uses are
   logger names and one enum name derived from the *output schema*, never from the
   node function. So the closures all being named `discuss`/`vote`/`act` internally
   is invisible.

Net: ~190 lines → ~50 in day actors; ~20 lines → ~8 per night role file. Adding a
role becomes one line.

---

## Day vs night — a deliberate structural difference

The day collapse put all 12 bindings in **one** `actors.py` table, because they
were already one pile of functions in one file — collapsing them into a table is a
pure readability win.

Night is different on purpose. The night folder is **one file per role**
(`night/healer.py`, `night/investigator.py`, …) so a role can be added or evolved
in isolation — that granularity is *why* the night refactor was done. So night
keeps the per-role files and each one becomes a one-line binding over a shared
`make_night_act_node` (in `night/factory.py`):

```python
# nodes/night/healer.py — the whole file
from Agents.nodes.night.factory import make_night_act_node
from Agents.prompts import HEALER_NIGHT
from Agents.schemas import HealerOutput
from Agents.state import HealerNightGraph

healer_act = make_night_act_node(
    HEALER_NIGHT, HealerOutput, "healer_target", HealerNightGraph
)
```

The seam this preserves: when a role's night logic later **diverges** — the way
`wolf` already has a real multi-node discussion flow (`prepare_wolf_night` →
`wolf_fan_out` → `wolf_night_discuss` → `collect_wolf_night_discussion`) — you
replace that role's one-line binding with a real function *in the same file*.
`wolf.py` and `resolution.py` (cross-role kill resolution) are untouched; they
were never instances of the common pattern.

---

## Does it affect tracing quality? No.

Span names are derived from **runtime data**, not from the Python function. In the
engine (`engine/actions.py`):

```python
span_name = f"agent_action_eval_{player_id}_day_{day}_round_{round_num}_{action_phase}"
with langfuse.start_as_current_observation(as_type="span", name=span_name, input={...}):
```

`player_id`, `day`, `round_num`, `action_phase` all come from the payload — so the
span name, its `input` block, and its `metadata` are identical whether the node
was hand-written or factory-built. The LangGraph-level span (if the langfuse
callback handler tags it) is named by the `add_node` string, which is unchanged.

So: same span names, same nesting, same inputs/metadata. Tracing is byte-for-byte
the same. (This was the precondition checked *before* doing the collapse, not an
after-the-fact hope — the gate's fingerprint can't see tracing, so it was verified
by reading the span-naming code.)
