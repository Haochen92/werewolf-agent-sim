# Measurement scripts behind the notes

The small scripts that produced the figures quoted in the notes, kept so a figure can be re-run or
checked when the write-up is written. Each is a dated, one-off probe, not part of the evaluation
pipeline and not maintained. None calls a model or a real database: the slow parts are replaced by
fixed sleeps or in-memory stand-ins, so the figures show how the code behaves, not how fast
production is. Run from the repository root with `poetry run python <path>`.

| Script | Date | What it shows | Quoted in |
|---|---|---|---|
| `u2_loop_lab.py` | 2026-11-12 | Four predict-then-run experiments on the event loop (`await`, `create_task`, `gather`, a blocking call) | U2 Part 1 walkthrough |
| `u2_subgraph_threads.py`, `u2_subgraph_threads_ctx.py` | 2026-11-11 | A phase run with a blocking call gets its own thread pool: ten 0.5 s seats take 1.0 s in two waves of 8 and 2 | U2 3.3 |
| `u2_saver_lock.py` | 2026-11-11 | One checkpoint saver runs every game's saves one at a time: eight 0.2 s saves take 1.6 s; a save waiting for a thread holds the lock | U2 3.5 |
| `u2_store_lock_overlap.py` | 2026-11-11 | Lesson lookups do not overlap: four with a 1 s embedder finish at 1, 2, 3, 4 s; with the lock removed, all at 1 s | U2 3.5 |
| `u2_toy.py` | 2026-11-12 | `max_concurrency` on a phase's configuration reaches its pool (1.01 s to 0.51 s); on the main graph it limits the whole step (0.5 s to 1.5 s at a value of 3) | U2 3.7 gap 5 |
| `u2_real_day.py` | 2026-11-12 | The real day phase, ten seats, model turns replaced by 0.5 s sleeps: 1.00 s on 8 threads before, 0.51 s on 10 after | U2 3.7 gap 5 |
| `u2_compile_cost.py` | 2026-11-12 | A graph per game: compile 40 ms and 72 KiB; copy with another saver 0.1 ms and 4 KiB; a copy saves through its own saver | U2 3.7 gap 1.2 |
| `u2_diag_vig.py`, `u2_off_plugin.py`, `u2_diag_runs.txt` | 2026-11-12 | Replays of the test that fails by thread order, with and without the pool setting, and what happened to the Vigilante's shot in each | U2 3.7 gap 5; U13 seed |
| `u3_kill_resume_toy.py`, `u3_kill_rerun.out` | 2026-11-12 | What runs again after a kill and after a pause, on a small graph with an in-memory saver | U3 3.6 |
| `u3_nested_interrupt_state.py` | 2026-11-12 | Whether the main graph's state shows a pause raised inside a nested phase | U3 3.5 |
