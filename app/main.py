"""
FastAPI application for the Research Brief Generator.
"""

import time
import structlog
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.config import settings
from app.schemas import BriefRequest, BriefResponse, ErrorResponse
from app.graph import research_graph
from app.database import db_manager


# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Research Brief Generator API")
    
    # Initialize database
    try:
        # Test database connection
        db_manager.get_session()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Research Brief Generator API")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="A context-aware research assistant system using LangGraph and LangChain",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Research Brief Generator API",
        "version": settings.app_version,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": settings.app_version
    }


@app.post("/brief", response_model=BriefResponse)
async def generate_brief(request: BriefRequest):
    """
    Generate a research brief for the given topic.
    
    This endpoint processes the request through the LangGraph workflow:
    1. Context summarization (if follow-up)
    2. Research planning
    3. Web search
    4. Content fetching
    5. Per-source summarization
    6. Synthesis
    7. Post-processing
    """
    start_time = time.time()
    
    try:
        logger.info(
            "Generating research brief",
            topic=request.topic,
            depth=request.depth,
            user_id=request.user_id,
            follow_up=request.follow_up
        )
        
        # Run the research graph
        brief = await research_graph.run(
            topic=request.topic,
            depth=request.depth,
            user_id=request.user_id,
            follow_up=request.follow_up
        )
        
        execution_time = time.time() - start_time
        
        logger.info(
            "Research brief generated successfully",
            brief_id=brief.brief_id,
            execution_time=execution_time,
            token_usage=brief.token_usage,
            cost_estimate=brief.cost_estimate
        )
        
        return BriefResponse(
            brief=brief,
            status="success",
            message="Research brief generated successfully"
        )
    
    except Exception as e:
        execution_time = time.time() - start_time
        
        logger.error(
            "Failed to generate research brief",
            error=str(e),
            execution_time=execution_time,
            topic=request.topic,
            user_id=request.user_id
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate research brief: {str(e)}"
        )


@app.get("/brief/{brief_id}")
async def get_brief(brief_id: str):
    """Get a specific research brief by ID."""
    try:
        # This would need to be implemented in the database manager
        # For now, return a placeholder
        raise HTTPException(
            status_code=404,
            detail="Brief not found"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve brief: {str(e)}"
        )


@app.get("/user/{user_id}/briefs")
async def get_user_briefs(user_id: str, limit: int = 10):
    """Get recent briefs for a user."""
    try:
        briefs = db_manager.get_user_briefs(user_id, limit=limit)
        return {
            "user_id": user_id,
            "briefs": briefs,
            "count": len(briefs)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user briefs: {str(e)}"
        )


@app.get("/user/{user_id}/context")
async def get_user_context(user_id: str):
    """Get user context and preferences."""
    try:
        context = db_manager.get_user_context(user_id)
        if context:
            return context
        else:
            return {
                "user_id": user_id,
                "previous_topics": [],
                "key_themes": [],
                "preferred_depth": 3,
                "last_interaction": None,
                "context_relevance_score": 0.0
            }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve user context: {str(e)}"
        )


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            status="error",
            message="Internal server error",
            error_code="INTERNAL_ERROR"
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 