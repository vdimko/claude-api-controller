import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.log import LogDocument, LogLevel

logger = logging.getLogger(__name__)


class LogService:
    """Service for log operations with MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.logs

    async def create_log(
        self,
        agent_name: str,
        level: LogLevel,
        message: str,
        task_id: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> LogDocument:
        """Create a new log entry."""
        log = LogDocument(
            agent_name=agent_name,
            level=level,
            message=message,
            task_id=task_id,
            metadata=metadata or {},
        )
        await self.collection.insert_one(log.to_mongo())
        return log

    async def list_logs(
        self,
        agent_name: Optional[str] = None,
        task_id: Optional[str] = None,
        level: Optional[LogLevel] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[LogDocument]:
        """List logs with optional filters."""
        query = {}

        if agent_name:
            query["agent_name"] = agent_name
        if task_id:
            query["task_id"] = task_id
        if level:
            query["level"] = level.value if isinstance(level, LogLevel) else level
        if since:
            query["timestamp"] = {"$gte": since}

        cursor = self.collection.find(query).sort("timestamp", -1).limit(limit)
        logs = []
        async for doc in cursor:
            log = LogDocument.from_mongo(doc)
            if log:
                logs.append(log)
        return logs

    async def delete_old_logs(self, days: int = 7) -> int:
        """Delete logs older than specified days."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.collection.delete_many({"timestamp": {"$lt": cutoff}})
        logger.info(f"Deleted {result.deleted_count} old logs")
        return result.deleted_count

    async def get_log(self, log_id: str) -> Optional[LogDocument]:
        """Get a single log by ID."""
        doc = await self.collection.find_one({"log_id": log_id})
        return LogDocument.from_mongo(doc)
