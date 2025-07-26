import asyncio
import pytest
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from retry_utils import retry_async

counter = 0

async def flaky():
    global counter
    counter += 1
    if counter < 3:
        raise RuntimeError("fail")
    return 42

@pytest.mark.asyncio
async def test_retry_async_succeeds():
    global counter
    counter = 0
    result = await retry_async(flaky, attempts=5, wait=0)
    assert result == 42
