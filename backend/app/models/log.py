import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class LogLevel(str, Enum):
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogDocument(BaseModel):
    """MongoDB document model for logs."""

    log_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: Optional[str] = None
    agent_name: str
    level: LogLevel = LogLevel.INFO
    message: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True

    def to_mongo(self) -> dict:
        """Convert to MongoDB document."""
        return self.model_dump()

    @classmethod
    def from_mongo(cls, doc: dict) -> Optional["LogDocument"]:
        """Create from MongoDB document."""
        if doc is None:
            return None
        return cls(**doc)
