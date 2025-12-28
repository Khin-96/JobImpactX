from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import get_settings
from app.config.logging import setup_logging
from app.api.routes import assess, explain
from app.api.middleware import AuthMiddleware, AuditMiddleware
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create app
app = FastAPI(
    title="AI Job Impact Platform",
    version="1.0.0",
    description="Enterprise decision support for understanding AI's impact on workforce roles"
)

# Settings
settings = get_settings()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(AuditMiddleware)

# Routes
app.include_router(assess.router)
app.include_router(explain.router)

# Root
@app.get("/")
async def root():
    return {
        "name": "AI Job Impact Platform",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )