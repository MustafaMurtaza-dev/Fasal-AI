from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import asyncio
import os
import time
from config import settings
from app.api.routes import diagnosis, advisory, market, weather, voice, farm, health, calendar


@asynccontextmanager
async def lifespan(app: FastAPI):
    t0 = time.time()
    logger.info("=" * 50)
    logger.info("FasalAI Starting...")
    logger.info(f"Primary: {settings.PRIMARY_MODEL}")
    logger.info(f"Backup:  {settings.BACKUP_MODEL}")
    logger.info("=" * 50)

    os.makedirs("app/data/trained_models", exist_ok=True)
    os.makedirs("temp_audio", exist_ok=True)

    from app.services.rag_service import rag_service
    await rag_service.initialize()

    # Run LLM check in background so it doesn't block startup
    async def check_llm():
        try:
            from app.ai.llm_client import llm_client
            # Verify connectivity only
            logger.info("Testing LLM connectivity...")
            t = await llm_client.generate_quick("Say ready in 1 word.")
            logger.info(f"✅ LLM OK: {t.strip()[:50]}")
        except Exception as e:
            logger.warning(f"⚠️ LLM test failed (non-fatal): {e}")

    asyncio.create_task(check_llm())

    elapsed = time.time() - t0
    logger.info(f"🚀 FasalAI LIVE in {elapsed:.1f}s -> http://localhost:8000/docs")
    yield
    logger.info("Shutdown")


app = FastAPI(title="FasalAI", version="1.0.0",
              description="AI Agriculture for Pakistan", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


# ─── Global exception handler — consistent JSON errors ───
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc) if settings.DEBUG else "Internal server error",
                 "status_code": 500}
    )


app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(diagnosis.router, prefix=settings.API_PREFIX, tags=["Diagnosis"])
app.include_router(advisory.router, prefix=settings.API_PREFIX, tags=["Advisory"])
app.include_router(market.router, prefix=settings.API_PREFIX, tags=["Market"])
app.include_router(weather.router, prefix=settings.API_PREFIX, tags=["Weather"])
app.include_router(voice.router, prefix=settings.API_PREFIX, tags=["Voice"])
app.include_router(farm.router, prefix=settings.API_PREFIX, tags=["Farm"])
app.include_router(calendar.router, prefix=settings.API_PREFIX, tags=["Calendar"])

@app.get("/")
async def root():
    return {
        "name": "FasalAI",
        "status": "operational",
        "version": settings.APP_VERSION,
        "models": {
            "primary": settings.PRIMARY_MODEL,
            "backup": settings.BACKUP_MODEL,
        },
        "docs": "/docs",
    }
