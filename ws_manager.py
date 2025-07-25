from __future__ import annotations
import asyncio, logging
from typing import Awaitable, Callable, TypeVar
import tenacity

logger = logging.getLogger(__name__)
_T = TypeVar("_T")

async def retry_async(
    func: Callable[[], Awaitable[_T]],
    *, attempts: int = 4, wait: float = 0.5, backoff: float = 2.0
) -> _T:
    @tenacity.retry(
        reraise=True,
        stop=tenacity.stop_after_attempt(attempts),
        wait=tenacity.wait_exponential(multiplier=wait, exp_base=backoff),
        before_sleep=lambda rs: logger.warning(
            "retry %s/%s: %s", rs.attempt_number, attempts, rs.outcome.exception()),
    )
    async def _wrapper() -> _T:
        return await func()
    return await _wrapper()