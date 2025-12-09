from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from ..models.log import LogLevel


class LogResponse(BaseModel):
    """Single log entry response."""

    log_id: str
    task_id: Optional[str] = None
    agent_name: str
    level: LogLevel
    message: str
    timestamp: datetime


class LogListResponse(BaseModel):
    """Response for log list endpoint."""

    count: int
    logs: List[LogResponse]
