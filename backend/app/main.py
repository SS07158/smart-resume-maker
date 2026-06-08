"""
Smart Resume Maker - AI-Powered Resume Optimizer
Full-Stack Application with LLM Integration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.models.database import init_db
from app.api import auth, resume, job_description, generation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"DB init failed: {str(e)}")
    
    logger.info("✅ Application ready!")
    yield
    
    logger.info("🛑 Shutting down...")

# Create app
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered resume optimizer and cover letter generator",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ROUTES ====================

# Authentication
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

# Resume Management
app.include_router(
    resume.router,
    prefix="/api/v1/resumes",
    tags=["Resumes"]
)

# Job Descriptions
app.include_router(
    job_description.router,
    prefix="/api/v1/job-descriptions",
    tags=["Job Descriptions"]
)

# Health check
@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }

# Error handling
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Request logging middleware
from time import time

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log requests"""
    start_time = time()
    response = await call_next(request)
    process_time = time() - start_time
    
    logger.info(
        f"{request.method} {request.url.path} - "
        f"{response.status_code} - {process_time:.2f}s"
    )
    
    response.headers["X-Process-Time"] = str(process_time)
    return response

"""
FastAPI Application - Complete with Generation
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from app.core.config import settings
from app.models.database import init_db
from app.api import auth, resume, job_description, generation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown"""
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} starting...")
    
    try:
        init_db()
        logger.info("✅ Database initialized")
    except Exception as e:
        logger.error(f"DB init failed: {str(e)}")
    
    logger.info("✅ Application ready!")
    yield
    
    logger.info("🛑 Shutting down...")

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered resume optimizer",
    version=settings.APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(resume.router, prefix="/api/v1/resumes", tags=["Resumes"])
app.include_router(job_description.router, prefix="/api/v1/job-descriptions", tags=["Jobs"])
app.include_router(generation.router, prefix="/api/v1/generate", tags=["Generation"])

@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.APP_VERSION}

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.APP_NAME}", "docs": "/docs"}

from fastapi import Request
from fastapi.responses import JSONResponse
from time import time

@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Error: {str(exc)}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal error"})

@app.middleware("http")
async def log_middleware(request: Request, call_next):
    start = time()
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {time()-start:.2f}s")
    return response




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


