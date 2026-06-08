"""
Smart Resume Maker - AI-Powered Resume Optimizer
Full-Stack Application with LLM Integration
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
from time import time

from app.core.config import settings
from app.models.database import init_db
from app.api import auth, resume, job_description, generation

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    
    try:
        init_db()
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}", exc_info=True)
        raise
    
    logger.info("✅ Application ready for requests!")
    yield
    
    logger.info("🛑 Shutting down application...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered resume optimizer and cover letter generator using LLMs",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== REQUEST/RESPONSE MIDDLEWARE ====================

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with response time"""
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - Time: {process_time:.2f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ==================== EXCEPTION HANDLERS ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"❌ Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc) if settings.DEBUG else None}
    )


# ==================== API ROUTES ====================

# Authentication endpoints
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

# Resume management endpoints
app.include_router(
    resume.router,
    prefix="/api/v1/resumes",
    tags=["Resumes"]
)

# Job description endpoints
app.include_router(
    job_description.router,
    prefix="/api/v1/job-descriptions",
    tags=["Job Descriptions"]
)

# Generation endpoints (resume variants & cover letters)
app.include_router(
    generation.router,
    prefix="/api/v1/generate",
    tags=["Generation"]
)


# ==================== HEALTH & INFO ENDPOINTS ====================

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


@app.get("/", tags=["Info"])
async def root():
    """Root endpoint with API documentation link"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "openapi_schema": "/openapi.json"
    }


# ==================== STARTUP ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
