import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import connect_to_mongo, close_mongo_connection
from .routes import tasks, agents, health, logs

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - connect/disconnect MongoDB."""
    await connect_to_mongo()
    yield
    await close_mongo_connection()


app = FastAPI(
    title="Claude API Controller",
    description="Async endpoint to control local Claude CLI installation with MongoDB persistence",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(tasks.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(logs.router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True
    )
