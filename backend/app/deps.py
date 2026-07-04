"""Shared FastAPI app-level singletons: rate limiter, Anthropic concurrency gate."""

import asyncio

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Bounds concurrent Anthropic narrative calls independent of per-IP rate
# limits, so a burst across many IPs still can't run up spend unbounded.
narrate_semaphore: asyncio.Semaphore | None = None


def get_narrate_semaphore(concurrency: int) -> asyncio.Semaphore:
    global narrate_semaphore
    if narrate_semaphore is None:
        narrate_semaphore = asyncio.Semaphore(concurrency)
    return narrate_semaphore
