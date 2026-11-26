# When a model call fails: timeouts, failover and the circuit breaker

*Level 2 · [Running it in production](../running_in_production.md)*

## Page copy (draft)

### Keeping the game moving when a model call fails

Every decision by an AI seat depends on a call to an external model provider, and that call can fail in several ways. The model can reply in the wrong format or choose an illegal action. The provider can report a rate limit or an overload, or take minutes to answer. The provider can also refuse the key that pays for the game.

The engine handles each kind of failure differently. An invalid answer gets one correction attempt. A primary model that fails or stalls is replaced by a *rescue model*, a second model configured for the game, where the game has one. If no model supplies a usable answer, the engine applies a legal default so that the phase can finish. A refused primary key ends the game.

A slow provider is the hardest case, because a request that is still waiting has reported no error for the engine to act on. Two further mechanisms deal with it: a time limit on each attempt, and a per-game circuit breaker that keeps later turns from repeating the same wait.

### Failure handling for one model call: correction, timeout, failover, fallback

Suppose the town is voting and the AI seat has three legal targets. The engine asks the primary model to choose. What it does next depends on what comes back.

| What the engine or provider reports | How this seat gets a vote |
|---|---|
| The model replies in the wrong format or picks an ineligible player | Give the primary one opportunity to correct the answer. If the vote is still invalid, ask the rescue model when one is configured. |
| The provider stays silent or reports overload | On clients with the game timeout, an ordinary attempt has a 30-second limit. The client library can retry once. When it reports a stall, the engine can go directly to rescue. |
| Neither model supplies a usable vote, or the primary stalls and the game has no rescue | Choose a random legal target and record the vote. This lets the phase finish, and it can change who is eliminated. |
| The provider refuses the primary key | End the game and tell the player why. Every later seat would need the same credential. |

A malformed reply shows that the provider is answering, which makes a correction worth trying. A silent primary may already have consumed two attempts by the time the library returns control. Sending the decision back to it at that point would make the player wait through the same sequence again. Discussion and night actions have their own final defaults. Discussion gets a technical pass, a wolf kill gets a random legal target, and a night role uses its “do nothing” action where the rules provide one. The [agent turn page](../../game_design_orchestration/agent_turn/agent_turn.md) explains reply validation and the correction attempt in detail.

### The per-game circuit breaker and the choice of rescue model

A rescue model can finish this vote while leaving the next voter exposed to exactly the same delay. After two consecutive primary stalls, a game with a rescue model sends subsequent seat decisions directly to rescue for five minutes. The model calls that prepare a lesson query or check a draft also follow this *circuit breaker*. After the interval the game can try its primary again.

The breaker belongs to the game because every AI seat there shares a model configuration. One player's key may be over quota while the next game's calls succeed. A server-wide breaker would divert both games. The trade-off shows up in a provider-wide outage, when each game encounters the failure separately. Two stalls and five minutes were design choices. No comparison established an optimal threshold.

The rescue model's provider matters too. In the first pairing, two models on the same provider used different quota pools. One player key could pay for either model, and congestion in the primary pool could still leave the rescue available. A provider-wide outage could affect both. Players can also supply a second provider's key for rescue. A game without a rescue model proceeds to its legal default when the primary is exhausted.

### The 30-second timeout: why it exists, what it bounds and what it leaves open

The timeout was added after a player waited 301 seconds for an AI line in a hosted game. Throughout the wait the browser received keep-alives and the server answered status requests. Of those 301 seconds, 282 went into retrieving lessons for the speaker, a step that itself calls a model. The provider held requests for minutes before returning a rate-limit error. Its client library retried, and the framework above it could retry again. The number of requests actually sent during that wait is unknown.

A rescue model was already configured. To hand the turn to it, the engine first had to learn that the primary had stalled. For as long as the client library was waiting or retrying internally, the engine had no failure to act on. A time limit on each attempt turns that silence into a reported stall.

The 30-second limit is a working value chosen by judgment, not one tuned by comparing alternatives. A later sample of 389 discussion calls to one model had a slowest response of 16.6 seconds. All those calls would have fit inside 30 seconds. That checks the threshold against one kind of call. The summary of a full day's discussion has a separate 90-second allowance and can fall back to the transcript.

Coverage also depended on which client made the request. The first fix reached one provider client. Three weeks later, a game using another client waited through three attempts with that library's 600-second timeout before rescue answered. The game timeout was then extended to additional clients. One provider client still has no explicit game timeout.

Even where the 30-second setting applies, it covers one attempt. If the primary and rescue each make two attempts and all four stall, the configured timeouts alone add up to 120 seconds for that decision. A discussion turn may also call a model to prepare its lesson search before drafting and to check the draft afterwards. Retry delays and those additional calls contribute to what the player experiences. There is no deadline covering the whole turn.

### What is tested and what is not measured

Engine tests exercise primary-to-rescue handover, an exhausted discussion turn becoming a pass, and a failed rescue producing a legal target. The hosted records distinguish rescued turns from rule-based moves, but a retry that succeeds inside the library can hide an earlier timeout. How often a hosted player still encounters a long wait has not been measured.

<!-- Sources
evidence/production/dependency_failures/report.md §§1–3, 5; evidence/tracing/report.md §4.4.
-->
