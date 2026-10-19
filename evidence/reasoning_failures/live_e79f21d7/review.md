# Live game e79f21d7: claim safety and repeated result requests

Reviewed 2026-10-19. Replay: `e79f21d7-e0d5-4baa-b478-303aa21ace68`, model `anthropic/claude-haiku-5-5`, memory off. This is a diagnosis and prompt revision, not a model-quality experiment.

## Observed in the archived event stream

- Player 1 was the Necromancer; player 5 the Vigilante; player 7 the human Investigator; player 8 the Illusionist; player 6 the Chanteuse.
- At seq 524, day 4, player 1 claimed Vigilante and said it held fire. At seq 592, the real Vigilante's private note recognized that claim as false while recording two unused bullets. At seq 609, it explicitly chose to shoot player 1 because the false claim made them the likely Necromancer. The shot at seq 608 and death at seq 617 confirm the outcome.
- At seq 125, player 8 claimed Investigator and explicitly said it held its night-1 check. It repeated that at seq 149 and 195. At seq 350 and 372, town players still requested a result despite acknowledging the held checks.
- At seq 553, the human Investigator said they held on night 1 and checked player 9 on night 2. The Chanteuse repeated the night-1 question at seq 564 and claimed it was unanswered at seq 576. Evil pressure is possible, but the transcript does not support calling that question unanswered.

## Wiring and limits

The running `wolf-server` imports `Agents.deduction.evil.covers`; `RunConfig().deduction_mode` is `full` with no side overrides. Served games use `server/game/run_config.py`, then `build_runnable_config`, the turn pipeline's deduction-mode forwarding, and prompt-input deduction blocks. Nonstandard ability limits can explicitly disable deductions; human seats do not receive private solver assistance.

The evil cover generator checks public consistency, private visit compatibility and existing claimants. It does not rank the likelihood of retaliation. In particular, an unclaimed Vigilante can still be alive, and a fabricated held-fire story can be logically consistent while immediately revealing the liar to the true holder. The code's existing Necromancer cover test explicitly permits a held-fire Vigilante story. This is not evidence that the solver was absent.

## Local changes

- Correct the shared rule sentence saying every night role acts: optional abilities may be held, including night 1, without spending a use or producing a result.
- Distinguish a held ability from a result withheld; ask models to consult prior answers before repeating a question. The holding account remains a claim, not verified truth.
- Add cover-risk guidance to wolf, Serial Killer and Necromancer discussion prompts: logical consistency is not strategic safety; unclaimed does not mean absent; a killing-role claim can invite retaliation; do not invent knowledge of another player's remaining uses.
- Regenerate the composed-rule and captured discussion-prompt goldens deliberately. This changes the prompt epoch.

No paid model calls or new games were run for this review. Prompt/solver tests can verify wiring and consistency, not prove that Haiku will obey the guidance or that evil win rates improve. These changes have not been deployed.

## Verification

The targeted cover, evil-seat and comparison tests passed. All 43 prompt/rules/draft-preview tests passed against the final prompt snapshots. An earlier long-running test process had imported the first wording before the final edit and reported a snapshot mismatch; the fresh run above passed. The broader unchanged randomized deduction suite was stopped after 90 passes, rather than treated as completed.

The accompanying frontend changes keep a single vertical stack with tally-independent chip size, move the flying chip in a small HTML transform layer, release it after landing, bound each plate's SVG, and avoid the number bounce on small screens. Nineteen geometry/count tests passed, the two new browser regressions passed, existing desktop/phone vote screenshots matched, and the phone-rule walk completed all 27 spectator vote beats with zero findings. TypeScript passed.

Chromium traces showed substantially smaller SVG paint clip areas, but did not establish lower total paint CPU time; the comparison also used the production baseline and a development candidate. This is not an iPad Safari thermal benchmark, and no claim is made that device heating is resolved. Physical-device verification remains necessary.
