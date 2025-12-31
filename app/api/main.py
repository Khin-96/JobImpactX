from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config.settings import get_settings
from app.config.logging import setup_logging
from app.api.routes import assess, routes as explain_routes, scenario, audit, governance, auth
from app.api.middleware import AuthMiddleware, AuditMiddleware
import logging

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events for application startup and shutdown.
    Load models and resources on startup.
    """
    logger.info("Application startup: Loading models and resources...")
    
    try:
        # Load model for explain route
        from app.api.routes.routes import load_model_and_explainer
        load_model_and_explainer()
        
        # Load model for scenario route
        from app.api.routes.scenario import load_model as load_scenario_model
        load_scenario_model()
        
        # Load model for governance route
        from app.api.routes.governance import load_model as load_governance_model
        load_governance_model()
        
        logger.info("Models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models on startup: {e}", exc_info=True)
    
    yield
    
    logger.info("Application shutdown")


# Create app with lifespan
app = FastAPI(
    title="AI Job Impact Platform",
    version="1.0.0",
    description="Enterprise decision support for understanding AI's impact on workforce roles",
    lifespan=lifespan
)

# Settings
settings = get_settings()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(AuthMiddleware)
app.add_middleware(AuditMiddleware)

# Routes
app.include_router(auth.router)
app.include_router(assess.router)
app.include_router(explain_routes.router)
app.include_router(scenario.router)
app.include_router(audit.router)
app.include_router(governance.router)


# Root endpoints
@app.get("/")
async def root():
    return {
        "name": "AI Job Impact Platform",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "authentication": "/auth/token",
            "assessment": "/api/v1/assess",
            "explanation": "/api/v1/explain",
            "scenario": "/api/v1/scenario",
            "audit": "/api/v1/audit",
            "governance": "/api/v1/governance/bias"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "service": "ai-job-impact-api"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return {
        "detail": "An internal error occurred. Please contact support if the issue persists.",
        "status_code": 500
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.api.main:app",
        host="0.0.0.0",
        port=settings.api_port,
        workers=settings.api_workers,
        reload=settings.debug
    )