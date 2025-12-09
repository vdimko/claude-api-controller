import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorDatabase

from .file_logger import agent_file_logger
from .log_service import LogService
from ..models.log import LogLevel

logger = logging.getLogger(__name__)


class CombinedLogger:
    """Logger that writes to both file and MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.log_service = LogService(db)

    async def log(
        self,
        agent_name: str,
        level: str,
        message: str,
        task_id: Optional[str] = None,
    ) -> None:
        """Write log entry to both file and MongoDB.

        Args:
            agent_name: Name of the agent
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            message: Log message
            task_id: Optional task ID
        """
        # File logging (sync)
        agent_file_logger.log(
            agent_name, level, task_id or "system", message
        )

        # MongoDB logging (async)
        try:
            log_level = LogLevel(level.lower())
        except ValueError:
            log_level = LogLevel.INFO

        try:
            await self.log_service.create_log(
                agent_name=agent_name,
                level=log_level,
                message=message,
                task_id=task_id,
            )
        except Exception as e:
            logger.error(f"Failed to write log to MongoDB: {e}")

    async def info(
        self, agent_name: str, message: str, task_id: Optional[str] = None
    ) -> None:
        """Log INFO level message."""
        await self.log(agent_name, "INFO", message, task_id)

    async def warning(
        self, agent_name: str, message: str, task_id: Optional[str] = None
    ) -> None:
        """Log WARNING level message."""
        await self.log(agent_name, "WARNING", message, task_id)

    async def error(
        self, agent_name: str, message: str, task_id: Optional[str] = None
    ) -> None:
        """Log ERROR level message."""
        await self.log(agent_name, "ERROR", message, task_id)

    async def debug(
        self, agent_name: str, message: str, task_id: Optional[str] = None
    ) -> None:
        """Log DEBUG level message."""
        await self.log(agent_name, "DEBUG", message, task_id)
