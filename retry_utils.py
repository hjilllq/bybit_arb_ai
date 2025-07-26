from __future__ import annotations
import logging
from typing import Awaitable, Callable, TypeVar
import asyncio
try:
    import tenacity
except ImportError:  # pragma: no cover - optional dependency
    tenacity = None

logger = logging.getLogger(__name__)
_T = TypeVar("_T")

async def retry_async(
    func: Callable[[], Awaitable[_T]],
    *, attempts: int = 4, wait: float = 0.5, backoff: float = 2.0
) -> _T:
    if tenacity is None:
        for n in range(attempts):
            try:
                return await func()
            except Exception as exc:
                if n == attempts - 1:
                    raise
                logger.warning("retry %s/%s: %s", n + 1, attempts, exc)
                await asyncio.sleep(wait * (backoff ** n))
        raise RuntimeError("unreachable")
    @tenacity.retry(
        reraise=True,
        stop=tenacity.stop_after_attempt(attempts),
        wait=tenacity.wait_exponential(multiplier=wait, exp_base=backoff),
        before_sleep=lambda rs: logger.warning(
            "retry %s/%s: %s", rs.attempt_number, attempts, rs.outcome.exception()
        ),
    )
    async def _wrapper() -> _T:
        return await func()
    return await _wrapper()
