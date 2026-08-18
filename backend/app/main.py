from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.core.database import create_tables

import asyncio
from app.services.thingspeak_poller import polling_loop

@app.on_event('startup')
async def startup():
    await create_tables()
    asyncio.create_task(polling_loop(app))

from app.routers.auth import router as auth_router
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["Auth"])

from app.routers.nodes import router as nodes_router
from app.routers.sensors import router as sensors_router
from app.routers.actuators import router as actuators_router
from app.routers.channels import router as channels_router

app.include_router(nodes_router, prefix=settings.API_V1_STR, tags=["Nodes"])
app.include_router(sensors_router, prefix=settings.API_V1_STR, tags=["Sensors"])
app.include_router(actuators_router, prefix=settings.API_V1_STR, tags=["Actuators"])
app.include_router(channels_router, prefix=settings.API_V1_STR, tags=["Channels"])

from app.routers.ws import router as ws_router
from app.routers.telemetry import router as telemetry_router
from app.routers.event_logs import router as event_logs_router
app.include_router(ws_router)  # no prefix, WS uses /ws/{node_id}
app.include_router(telemetry_router, prefix=settings.API_V1_STR, tags=["Telemetry"])
app.include_router(event_logs_router, prefix=f"{settings.API_V1_STR}/event-logs", tags=["Events"])


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get(f"{settings.API_V1_STR}/health", tags=["System"])
async def api_health_check():
    return {
        "status": "ok",
        "service": "FastAPI Core",
        "version": settings.VERSION
    }
