"""FastAPI entrypoint for the public CyberRescue web demo backend."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from python_on_whales import docker
from python_on_whales.exceptions import DockerException
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.deps import limiter
from app.logging_config import configure_logging
from app.middleware import AccessLogMiddleware
from app.routes import containers, narrative

configure_logging(settings.log_level)
logger = logging.getLogger("cyberrescue.backend")

app = FastAPI(title="CyberRescue Demo API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
app.add_middleware(AccessLogMiddleware)

app.include_router(containers.router)
app.include_router(narrative.router)


@app.get("/healthz")
async def healthz():
    docker_ok = True
    try:
        docker.system.info()
    except DockerException:
        docker_ok = False

    status_code = 200 if docker_ok else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if docker_ok else "degraded", "docker_reachable": docker_ok},
    )
