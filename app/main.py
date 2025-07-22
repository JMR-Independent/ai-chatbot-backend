from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import os

from app.core.config import settings
from app.core.database import engine, Base
from app.api.routes import chat, admin


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="AI Chatbot API",
    description="Advanced AI chatbot with RAG integration",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])


@app.get("/")
async def root():
    return {"message": "AI Chatbot API", "version": "1.0.0", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "openai_configured": bool(settings.OPENAI_API_KEY)}

@app.get("/api/health")
async def api_health_check():
    return {
        "status": "healthy", 
        "openai_status": "connected" if settings.OPENAI_API_KEY else "not configured",
        "timestamp": "2024-07-22T00:00:00Z"
    }


if __name__ == "__main__":
    import sys
    sys.path.append("/app")
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
        workers=1
    )