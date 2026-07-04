"""Public demo routes: container status, logs, stats, and the fixed diagnostic menu.

Every route validates the container name against demo_policy.DEMO_CONTAINERS
before touching Docker at all — no route in this module accepts an
arbitrary container_id or arbitrary shell command.
"""

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from python_on_whales import docker
from python_on_whales.exceptions import DockerException

from cyberrescue import core
from cyberrescue.demo_policy import DEMO_CONTAINERS, DEMO_COMMAND_MENU, resolve_demo_command
from cyberrescue.security import ValidationError

from app.config import settings
from app.deps import limiter

logger = logging.getLogger("cyberrescue.backend.containers")

router = APIRouter(prefix="/api/containers", tags=["containers"])

DEMO_DESCRIPTIONS = {
    "broken-flask": "Crashes on startup with a missing DATABASE_URL environment variable.",
    "leaking-node": "Leaks ~10MB/sec until it's OOM-killed by Docker.",
    "crashed-nginx": "Fails to start due to invalid nginx config syntax.",
}


def _require_demo_container(name: str) -> str:
    if name not in DEMO_CONTAINERS:
        raise HTTPException(status_code=404, detail=f"Unknown demo container: {name!r}")
    return name


@router.get("")
@limiter.limit(settings.rate_limit_read)
async def list_containers(request: Request):
    results = []
    for name in sorted(DEMO_CONTAINERS):
        state = "unknown"
        try:
            container = docker.container.inspect(name)
            state = container.state.status
        except DockerException:
            state = "not_found"
        results.append(
            {
                "name": name,
                "state": state,
                "description": DEMO_DESCRIPTIONS.get(name, ""),
            }
        )
    return {"containers": results}


@router.get("/{name}/logs")
@limiter.limit(settings.rate_limit_read)
async def get_logs(request: Request, name: str, tail: int = 100):
    _require_demo_container(name)
    try:
        return await core.stream_container_logs(name, tail=tail)
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{name}/stats")
@limiter.limit(settings.rate_limit_read)
async def get_stats(request: Request, name: str):
    _require_demo_container(name)
    try:
        return await core.inspect_memory_dump(name)
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.get("/{name}/menu")
@limiter.limit(settings.rate_limit_read)
async def get_menu(request: Request, name: str):
    _require_demo_container(name)
    menu = DEMO_COMMAND_MENU.get(name, {})
    return {
        "commands": [
            {"key": key, "label": label} for key, (label, _command) in menu.items()
        ]
    }


class DiagnoseRequest(BaseModel):
    command_key: str


@router.post("/{name}/diagnose")
@limiter.limit(settings.rate_limit_diagnose)
async def diagnose(request: Request, name: str, body: DiagnoseRequest):
    _require_demo_container(name)
    try:
        literal_command = resolve_demo_command(name, body.command_key)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        result = await core.execute_isolated_script(name, literal_command)
    except (ValidationError, ValueError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    logger.info("diagnose container=%s command_key=%s", name, body.command_key)
    return result
