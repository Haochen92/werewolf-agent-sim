# Town echo read — (a) ignored vs (b) followed-but-worse

Paired at game level on the 12 games nh_town has completed so far.
echo = fraction of a town agent's updated_strategy words drawn from its retrieved memory.
(a) ignored => nh echo << raw echo ;  (b) followed-but-worse => nh echo ~= raw echo.

## raw_town (immediate-first)
- decisions=711 (games=12, avg retrieved=3.20)
- echo vs approach+situation (stable/actionable): 0.341
- echo vs full entry (incl rewritten outcome):    0.377
- shuffled-memory floor (vocabulary baseline):    0.284 (real lift +0.057)

## nh_town (net-first)
- decisions=671 (games=12, avg retrieved=3.30)
- echo vs approach+situation (stable/actionable): 0.327
- echo vs full entry (incl rewritten outcome):    0.375
- shuffled-memory floor (vocabulary baseline):    0.279 (real lift +0.048)

## verdict
- Δecho approach+situation: -0.014 (Mann-Whitney p=0.015)
- Δecho full entry:         -0.001 (Mann-Whitney p=0.731)
- genuine engagement = echo ABOVE shuffle floor: raw +0.057 -> nh +0.048 (-16% relative)

=> nh echo still sits clearly above its OWN shuffle floor (genuine lift retained, 84% of raw's) -> predominantly shape (b): town agents still DRAW ON the memories, but the rewritten guidance is worse (lost CORRECTNESS). A faint (a) tint (engagement lift softened ~16%), but nowhere near 'ignored' -> the 0.559 collapse is mostly active misdirection, not memory-off.