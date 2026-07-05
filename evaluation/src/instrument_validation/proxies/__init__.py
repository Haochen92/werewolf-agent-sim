"""De-luck proxy validation — do the outcome proxies track the thing they claim to?

Point-biserial / partial-correlation checks that each per-role de-lucked proxy actually correlates
with its own faction's win (monotonicity), plus the rescue/discovery passes that separate a
muted-but-real signal from a still-null one. Also here: ``diagnose_wolf_sk_proxies`` (wolf/SK proxy
revalidation + SK harm-channel check on the paired-A/B corpus) and ``leverage_anchor_separation``
(validates the deterministic leverage anchor — is_swing / distance_to_parity — the pivotalness ruler
the diagnosis sampler and extraction selection lean on). All deterministic, ZERO LLM, recompute-only;
standing — re-run whenever the proxy basket or the underlying record set changes.
"""
