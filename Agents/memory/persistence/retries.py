from __future__ import annotations

import logging
import time
from typing import Any, Callable

from langgraph.store.base import BaseStore, PutOp

from .config import (
    _TRANSIENT_MEMORY_STORE_ERROR_MARKERS,
    _TRANSIENT_MEMORY_STORE_STATUS_CODES,
)

logger = logging.getLogger(__name__)


def _memory_store_call_with_retries(
    call: Callable[[], Any],
    *,
    operation_name: str,
    retry_attempts: int,
    retry_initial_delay: float,
    retry_max_delay: float,
    sleep: Callable[[float], None] = time.sleep,
) -> Any:
    attempts = max(1, retry_attempts)
    for attempt in range(1, attempts + 1):
        try:
            return call()
        except Exception as exc:
            if attempt >= attempts or not _is_transient_memory_store_error(exc):
                raise

            delay = min(retry_max_delay, retry_initial_delay * (2 ** (attempt - 1)))
            logger.warning(
                "Memory store %s failed with a transient error; "
                "retrying in %.1fs (attempt %s/%s): %s",
                operation_name,
                delay,
                attempt + 1,
                attempts,
                exc,
            )
            sleep(delay)

    raise RuntimeError(f"Memory store {operation_name} retry loop exited unexpectedly")


def _batch_with_retries(
    target_store: BaseStore,
    ops: list[PutOp],
    *,
    retry_attempts: int,
    retry_initial_delay: float,
    retry_max_delay: float,
    sleep: Callable[[float], None] = time.sleep,
) -> None:
    _memory_store_call_with_retries(
        lambda: target_store.batch(ops),
        operation_name="batch",
        retry_attempts=retry_attempts,
        retry_initial_delay=retry_initial_delay,
        retry_max_delay=retry_max_delay,
        sleep=sleep,
    )


def _is_transient_memory_store_error(exc: BaseException) -> bool:
    for current in _exception_chain(exc):
        status_code = getattr(current, "status_code", None)
        if status_code in _TRANSIENT_MEMORY_STORE_STATUS_CODES:
            return True

        response = getattr(current, "response", None)
        response_status = getattr(response, "status_code", None)
        if response_status in _TRANSIENT_MEMORY_STORE_STATUS_CODES:
            return True

        message = str(current).lower()
        if any(marker in message for marker in _TRANSIENT_MEMORY_STORE_ERROR_MARKERS):
            return True

    return False


def _exception_chain(exc: BaseException) -> list[BaseException]:
    chain = [exc]
    seen = {id(exc)}
    current = exc
    while True:
        next_exc = current.__cause__ or current.__context__
        if next_exc is None or id(next_exc) in seen:
            return chain
        chain.append(next_exc)
        seen.add(id(next_exc))
        current = next_exc
