import logging
import random
import time
from collections.abc import Callable
from typing import TypeVar

from app.ai.errors import AITransientError

logger = logging.getLogger(__name__)

T = TypeVar("T")


def retry_call(
    fn: Callable[[], T],
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 8.0,
    jitter: bool = True,
    sleep: Callable[[float], None] = time.sleep,
    retry_on: tuple[type[Exception], ...] = (AITransientError,),
) -> T:
    """
    Call `fn`, retrying only on transient errors with exponential backoff.

    Centralising retries here keeps every provider call consistent and stops the
    policy from being re-implemented per feature. Key rules:

      * Only exceptions in `retry_on` (transient by default) are retried.
        Validation errors, parse errors, config errors, and non-transient
        provider errors propagate immediately — retrying them is pointless.
      * Backoff is exponential (base_delay * 2**n), capped at max_delay, with
        optional jitter to avoid thundering-herd retries.
      * `sleep` is injectable so tests run instantly without real delays.

    The last transient error is re-raised once attempts are exhausted.
    """
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except retry_on as exc:
            last_exc = exc
            if attempt >= max_attempts:
                break
            delay = min(max_delay, base_delay * (2 ** (attempt - 1)))
            if jitter:
                # 50–100% of the computed delay.
                delay *= 0.5 + random.random() / 2
            logger.warning(
                "Transient AI failure (attempt %d/%d): %s — retrying in %.2fs",
                attempt,
                max_attempts,
                exc,
                delay,
            )
            sleep(delay)

    assert last_exc is not None  # only reachable after a caught transient error
    raise last_exc
