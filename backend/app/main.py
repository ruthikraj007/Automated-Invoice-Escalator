import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import get_supabase_client
from app.api.v1.api import api_router
from app.services.escalation_service import escalation_service

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.APP_NAME}...")
    get_supabase_client()
    escalation_service.start_scheduler()
    yield
    # Shutdown
    logger.info("Shutting down application...")
    escalation_service.stop_scheduler()

app = FastAPI(
    title=settings.APP_NAME,
    description="Automated Invoice & Payment Escalator - Streamline collection sequences and recover overdue revenue.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Assemble allowed origins
cors_origins = list(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]
if settings.ALLOWED_ORIGINS:
    extra_origins = settings.ALLOWED_ORIGINS if isinstance(settings.ALLOWED_ORIGINS, list) else [settings.ALLOWED_ORIGINS]
    cors_origins.extend(extra_origins)

# Ensure essential domains are always permitted
essential_origins = [
    "http://localhost:3000",
    "https://frontend-eight-delta-26.vercel.app",
]
for origin in essential_origins:
    if origin not in cors_origins:
        cors_origins.append(origin)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def read_root():
    return {
        "app": settings.APP_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR
    }

# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "app": settings.APP_NAME,
        "version": "1.0.0",
        "scheduler_running": escalation_service.scheduler.running
    }

# Include API V1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
