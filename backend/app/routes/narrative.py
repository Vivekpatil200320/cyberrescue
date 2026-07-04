"""AI root-cause narrative route.

Re-derives all evidence (logs, stats) server-side rather than trusting
client-submitted "evidence" — the client only ever names which container
it wants narrated, never supplies the data the LLM reasons over.
"""

import logging

import anthropic
from fastapi import APIRouter, HTTPException, Request

from cyberrescue import core

from app.config import settings
from app.deps import get_narrate_semaphore, limiter
from app.routes.containers import DEMO_DESCRIPTIONS, _require_demo_container

logger = logging.getLogger("cyberrescue.backend.narrative")

router = APIRouter(prefix="/api/containers", tags=["narrative"])

SYSTEM_PROMPT = (
    "You are CyberRescue, an assistant that explains Docker container failures. "
    "Given logs and stats already captured from a container, write a short "
    "(3-5 sentence) root-cause explanation and a one-line suggested fix. "
    "Be concrete and reference specifics from the evidence provided."
)


@router.post("/{name}/narrate")
@limiter.limit(settings.rate_limit_narrate)
async def narrate(request: Request, name: str):
    _require_demo_container(name)

    if not settings.anthropic_api_key:
        raise HTTPException(status_code=503, detail="Narrative generation is not configured.")

    logs_result = await core.stream_container_logs(name, tail=100)
    try:
        stats_result = await core.inspect_memory_dump(name)
    except RuntimeError:
        stats_result = {"note": "stats unavailable (container likely not running)"}

    evidence = (
        f"Container: {name}\n"
        f"Known issue: {DEMO_DESCRIPTIONS.get(name, 'unknown')}\n\n"
        f"Logs (last 100 lines):\n{chr(10).join(logs_result['log_lines'])}\n\n"
        f"Stats: {stats_result}"
    )

    semaphore = get_narrate_semaphore(settings.narrate_concurrency)
    async with semaphore:
        try:
            client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            message = await client.messages.create(
                model="claude-sonnet-5",
                max_tokens=400,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": evidence}],
            )
            narrative_text = "".join(
                block.text for block in message.content if block.type == "text"
            )
        except anthropic.APIError as exc:
            logger.error("Anthropic API error for container %s: %s", name, exc)
            raise HTTPException(
                status_code=502, detail="Narrative generation failed. Try again shortly."
            ) from None

    return {"container": name, "narrative": narrative_text}
