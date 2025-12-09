import logging
from typing import Optional

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..auth import verify_api_key
from ..database import get_database
from ..schemas.log import LogResponse, LogListResponse
from ..services.log_service import LogService
from ..models.log import LogLevel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["logs"])


def get_log_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> LogService:
    return LogService(db)


@router.get("/logs", response_model=LogListResponse)
async def list_logs(
    agent_name: Optional[str] = None,
    task_id: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
    service: LogService = Depends(get_log_service),
    _: str = Depends(verify_api_key),
) -> LogListResponse:
    """List logs with optional filters."""
    log_level = None
    if level:
        try:
            log_level = LogLevel(level.lower())
        except ValueError:
            pass  # Invalid level, ignore filter

    logs = await service.list_logs(
        agent_name=agent_name,
        task_id=task_id,
        level=log_level,
        limit=min(limit, 500),  # Cap at 500
    )

    return LogListResponse(
        count=len(logs),
        logs=[
            LogResponse(
                log_id=log.log_id,
                task_id=log.task_id,
                agent_name=log.agent_name,
                level=log.level,
                message=log.message,
                timestamp=log.timestamp,
            )
            for log in logs
        ],
    )
