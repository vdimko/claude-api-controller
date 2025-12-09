import logging
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from .config import get_settings

logger = logging.getLogger(__name__)


class Database:
    client: AsyncIOMotorClient = None
    db: AsyncIOMotorDatabase = None


db = Database()


async def connect_to_mongo():
    """Connect to MongoDB on startup."""
    settings = get_settings()
    logger.info(f"Connecting to MongoDB at {settings.mongodb_url.split('@')[-1]}...")

    db.client = AsyncIOMotorClient(settings.mongodb_url)
    db.db = db.client[settings.mongodb_database]

    # Test connection
    await db.client.admin.command('ping')

    # Create indexes for logs collection
    await db.db.logs.create_index("agent_name")
    await db.db.logs.create_index("task_id")
    await db.db.logs.create_index("timestamp")
    await db.db.logs.create_index([("agent_name", 1), ("timestamp", -1)])

    logger.info("Successfully connected to MongoDB")


async def close_mongo_connection():
    """Close MongoDB connection on shutdown."""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """Get database instance for dependency injection."""
    return db.db
