import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware import _MiddlewareFactory

from src.adapters.driven.db import models  # noqa: F401
from src.adapters.driven.db.database import init_db
from src.adapters.driven.seed import load_seed_data
from src.adapters.driving.http import register_error_handlers
from src.adapters.driving.http import router as api_router
from src.adapters.driving.mcp_server import build_mcp_server
from src.config import get_settings
from src.container import get_container

logger = logging.getLogger("popote")

settings = get_settings()
mcp_server = build_mcp_server(get_container)
mcp_app = mcp_server.streamable_http_app(
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=settings.MCP_ALLOWED_HOSTS,
        allowed_origins=[f"http://{host}" for host in settings.MCP_ALLOWED_HOSTS],
    ),
)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    container = get_container()
    if container.engine is not None:
        await init_db(container.engine)
    if settings.SEED_ON_STARTUP:
        report = await container.seed_database.seed_if_empty(load_seed_data(settings.seed_paths))
        logger.info("Seed : %s", report.model_dump())
    async with mcp_server.session_manager.run():
        yield
    if container.engine is not None:
        await container.engine.dispose()


app = FastAPI(title="Popote API", lifespan=lifespan)

app.add_middleware(
    cast(_MiddlewareFactory, CORSMiddleware),
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_error_handlers(app)
app.include_router(api_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.mount("/", mcp_app)
