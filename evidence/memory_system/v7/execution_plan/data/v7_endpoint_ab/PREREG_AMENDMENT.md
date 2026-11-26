# Pre-registration amendment — endpoint design (2026-07-20)

Signed pre-reg specified the endpoint as 20 shared boards x 3 conditions (final store / gen-1 store / memory-OFF). Owner amended BEFORE any endpoint game was played:

- **New design: 30 shared boards x 2 conditions (final store vs memory-OFF).**
- Rationale (owner, 2026-07-20): the SP-vs-tells decomposition via the gen-1 condition is not needed — proving the matured store (SPs + tells) beats OFF is the claim of interest; the freed 20 games buy ~22% tighter SE on that primary contrast. Also noted: the gen-1 snapshot has zero SPs and no per-generation tell-book snapshot exists (only checklists were versioned), so the gen-1 condition would have needed the seed book as a stand-in.
- Primary readout unchanged: final-store ON vs OFF on the town proxy basket, paired per board; a board counts only when BOTH its arms completed; halted partials are quarantined and replayed same-epoch, never pooled one-sided.
- All other pre-reg commitments unchanged (null reported as null; frozen repo a010dc6; flash-lite; one same-epoch block).
