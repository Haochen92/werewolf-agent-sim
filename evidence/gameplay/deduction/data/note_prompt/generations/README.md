# The private-note screen's generations

The two arms' samples for the note rewrite screen (`../../../experiment_log.md` §6), copied byte for
byte on 2026-10-23, at commit `1a5c0da1`, from the git-ignored `evaluation/eval_results/note_prompt_screen/`.
The run used only the bench's generation step, with no API judge; a chat subagent judged the samples, and
its verdicts are in `../judging/`. No config was saved with the run, so `eval-graduate` did not fit. The
source folder's README read:

> Arms: note_current (worktree ../ww-note-current = HEAD + this tree's uncommitted Agents/evaluation
> changes, minus the note rewrite), note_new (this tree). Haiku 5.5, thinking low, memory off, n=4.
