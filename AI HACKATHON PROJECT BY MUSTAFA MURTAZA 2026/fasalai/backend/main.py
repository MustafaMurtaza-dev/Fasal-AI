from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from loguru import logger
import os
from config import settings
from app.api.routes import diagnosis, advisory, market, weather, voice, farm, health


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("🌾 FasalAI Starting...")
    logger.info(f"🔵 Primary: {settings.PRIMARY_MODEL}")
    logger.info(f"🔄 Backup:  {settings.BACKUP_MODEL}")
    logger.info("=" * 50)

    os.makedirs("app/data/trained_models", exist_ok=True)
    os.makedirs("temp_audio", exist_ok=True)

    from app.services.rag_service import rag_service
    await rag_service.initialize()

    try:
        from app.ai.llm_client import llm_client
        t = await llm_client.generate_quick("Say ready in 1 word.")
        logger.info(f"✅ LLM: {t.strip()[:50]}")
    except Exception as e:
        logger.warning(f"⚠️ LLM test: {e}")

    logger.info("🚀 FasalAI LIVE → http://localhost:8000/docs")
    yield
    logger.info("🛑 Shutdown")


app = FastAPI(title="FasalAI 🌾", version="1.0.0",
              description="AI Agriculture for Pakistan", lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])

app.include_router(health.router, prefix=settings.API_PREFIX, tags=["Health"])
app.include_router(diagnosis.router, prefix=settings.API_PREFIX, tags=["Diagnosis"])
app.include_router(advisory.router, prefix=settings.API_PREFIX, tags=["Advisory"])
app.include_router(market.router, prefix=settings.API_PREFIX, tags=["Market"])
app.include_router(weather.router, prefix=settings.API_PREFIX, tags=["Weather"])
app.include_router(voice.router, prefix=settings.API_PREFIX, tags=["Voice"])
app.include_router(farm.router, prefix=settings.API_PREFIX, tags=["Farm"])

@app.get("/")
async def root():
    return {
        "name": "🌾 FasalAI",
        "status": "operational ✅",
        "models": {
            "primary": settings.PRIMARY_MODEL,
            "backup": settings.BACKUP_MODEL,
        },
        "docs": "/docs",
    }