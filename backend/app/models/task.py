import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskDocument(BaseModel):
    """MongoDB document model for tasks."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_name: str
    prompt: str
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    timeout_seconds: int = 120
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    def to_mongo(self) -> dict:
        """Convert to MongoDB document."""
        return self.model_dump()

    @classmethod
    def from_mongo(cls, doc: dict) -> "TaskDocument":
        """Create from MongoDB document."""
        if doc is None:
            return None
        return cls(**doc)
