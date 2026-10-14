import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection, db_manager
from app.database.neo4j import (
    connect_to_neo4j, close_neo4j_connection, check_neo4j_health, GraphUnavailableError
)
from app.database.init_db import initialize_databases

from app.utils.errors import NotFoundError, ConflictError
from app.routes import auth, users, events, social, feed, admin, comments
from app.routes.xml_routes import router as xml_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("campusconnect.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CampusConnect Backend...")
    problems = get_settings().validate_for_runtime()
    if problems:
        for problem in problems:
            logger.critical(f"Configuration error: {problem}")
        raise RuntimeError("Invalid production configuration: " + "; ".join(problems))

    # 1. Connect MongoDB
    await connect_to_mongo()
    # 2. Connect Neo4j
    await connect_to_neo4j()
    # 3. Initialize DB indexes & constraints
    await initialize_databases()
    logger.info("CampusConnect Backend startup complete.")
    yield
    logger.info("Shutting down CampusConnect Backend...")
    await close_mongo_connection()
    await close_neo4j_connection()
    logger.info("CampusConnect Backend shutdown complete.")

settings = get_settings()

app = FastAPI(
    title="CampusConnect API",
    description="Backend for CampusConnect Social Platform - PSG Tech",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(GraphUnavailableError)
async def graph_unavailable_handler(request: Request, exc: GraphUnavailableError):
    logger.error(f"Graph database unavailable on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "success": False,
            "message": "The social graph service is temporarily unavailable. Please try again shortly.",
            "detail": "The social graph service is temporarily unavailable. Please try again shortly.",
        },
    )

@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"success": False, "detail": str(exc)})

@app.exception_handler(ConflictError)
async def conflict_handler(request: Request, exc: ConflictError):
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"success": False, "detail": str(exc)})

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # Full details go to the server log only; clients get a generic message.
    logger.error(f"Unhandled exception on {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "detail": "An internal server error occurred",
        },
    )

# Health Check
@app.get("/health", tags=["Health"], summary="Health Check Endpoint")
async def health_check():
    mongo_status = "disconnected"
    if db_manager.client is not None:
        try:
            await db_manager.client.admin.command("ping")
            mongo_status = "connected"
        except Exception:
            mongo_status = "disconnected"
    neo4j_status = "connected" if await check_neo4j_health() else "disconnected"
    return {
        "status": "ok" if mongo_status == "connected" and neo4j_status == "connected" else "degraded",
        "mongodb": mongo_status,
        "neo4j": neo4j_status,
    }

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(social.router)
app.include_router(feed.router)
app.include_router(admin.router)
app.include_router(comments.router)

# XML Integration routes (Neo4j + MongoDB unified XML output)
app.include_router(xml_router)
