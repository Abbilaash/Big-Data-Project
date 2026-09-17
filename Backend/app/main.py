import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database.mongodb import connect_to_mongo, close_mongo_connection, db_manager
from app.database.neo4j import connect_to_neo4j, close_neo4j_connection, neo4j_manager
from app.database.init_db import initialize_databases

from app.routes import auth, users, events, social, feed, admin, comments

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("campusconnect.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing CampusConnect Backend...")
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
origins = [origin.strip() for origin in settings.FRONTEND_URL.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "message": "An internal server error occurred",
            "errors": str(exc)
        }
    )

# Health Check
@app.get("/health", tags=["Health"], summary="Health Check Endpoint")
async def health_check():
    mongo_status = "connected" if db_manager.client is not None else "disconnected"
    neo4j_status = "connected" if neo4j_manager.driver is not None else "disconnected"
    return {
        "status": "ok" if mongo_status == "connected" and neo4j_status == "connected" else "degraded",
        "mongodb": mongo_status,
        "neo4j": neo4j_status
    }

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(events.router)
app.include_router(social.router)
app.include_router(feed.router)
app.include_router(admin.router)
app.include_router(comments.router)
