from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel

from ..models.task import TaskStatus


class TaskCreateRequest(BaseModel):
    """Request body for creating a new task."""
    agent_name: str
    prompt: str
    timeout: Optional[int] = None


class TaskResponse(BaseModel):
    """Response after creating a task."""
    task_id: str


class TaskStatusResponse(BaseModel):
    """Full task status response."""
    task_id: str
    agent_name: str
    status: TaskStatus
    prompt: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    updated_at: datetime
    duration_sec: Optional[float] = None


class TaskListItem(BaseModel):
    """Task summary for list view."""
    task_id: str
    agent_name: str
    status: TaskStatus
    created_at: datetime
    duration_sec: Optional[float] = None
    prompt_preview: Optional[str] = None


class TaskListResponse(BaseModel):
    """Response for task list endpoint."""
    count: int
    tasks: List[TaskListItem]
