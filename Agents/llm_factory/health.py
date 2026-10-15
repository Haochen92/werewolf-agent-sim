"""Whether a game's primary model is answering, so a seat can go straight to its rescue.

Vertex's shared pool for a new model can hold a request for minutes and then bounce it
(429 RESOURCE_EXHAUSTED, seen live 2026-09-30: one draft waited 282 s). The request budget
in ``accessors`` turns such a wait into a failed call, and the seat's turn goes to the rescue
model (``agent_player.run_agent``). This keeps the count: after ``rescue_after`` stalled
turns in a row the game's next turns skip the primary and start on the rescue for
``cooldown_s`` seconds, then try the primary once more; another stall re-arms the rescue, a
good answer clears the count. One per served game, shared by every seat's thread
(``GameLLM.health``), so a squeeze one seat ran into spares the others the wait.
"""

from __future__ import annotations

import os
import threading
import time


class ModelHealth:
    def __init__(self, *, rescue_after: int | None = None, cooldown_s: float | None = None):
        self.rescue_after = (
            rescue_after if rescue_after is not None
            else max(1, int(os.getenv("GAME_STALL_RESCUE_AFTER", "2")))
        )
        self.cooldown_s = (
            cooldown_s if cooldown_s is not None
            else float(os.getenv("GAME_STALL_RESCUE_COOLDOWN_S", "300"))
        )
        self._lock = threading.Lock()
        self.stalls = 0
        self.rescue_until: float | None = None

    def note_stall(self) -> int:
        """The primary timed out or was bounced on a turn. Returns the stalls in a row."""
        with self._lock:
            self.stalls += 1
            if self.stalls >= self.rescue_after:
                self.rescue_until = time.monotonic() + self.cooldown_s
            return self.stalls

    def note_ok(self) -> None:
        """The primary answered a turn: the count and any rescue window are cleared."""
        with self._lock:
            self.stalls = 0
            self.rescue_until = None

    def prefer_rescue(self) -> bool:
        """Whether a turn should start on the rescue model rather than try the primary."""
        with self._lock:
            return self.rescue_until is not None and time.monotonic() < self.rescue_until
