import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorDatabase

from ..auth import verify_api_key
from ..config import get_settings
from ..database import get_database
from ..schemas import (
    TaskCreateRequest,
    TaskResponse,
    TaskStatusResponse,
    TaskListItem,
    TaskListResponse,
)
from ..services import TaskService, run_claude_command, stop_task
from ..models.task import TaskStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["tasks"])


def get_task_service(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> TaskService:
    return TaskService(db)


@router.post("/run", response_model=TaskResponse)
async def create_task(
    request: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    service: TaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
) -> TaskResponse:
    """
    Submit a prompt to be executed by Claude CLI in agent directory.
    Returns a task_id that can be used to poll for results.
    """
    settings = get_settings()
    timeout = request.timeout or settings.claude_timeout

    task = await service.create_task(request.agent_name, request.prompt, timeout)

    prompt_preview = request.prompt[:50] if len(request.prompt) > 50 else request.prompt
    logger.info(f"Task {task.task_id}: Agent '{request.agent_name}', prompt: {prompt_preview}...")

    background_tasks.add_task(
        run_claude_command,
        service,
        task.task_id,
        request.agent_name,
        request.prompt,
        timeout
    )

    return TaskResponse(task_id=task.task_id)


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
) -> TaskStatusResponse:
    """Get the status and result of a submitted task."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    logger.info(f"Task {task_id}: Status check - {task.status}")

    return TaskStatusResponse(
        task_id=task.task_id,
        agent_name=task.agent_name,
        status=task.status,
        prompt=task.prompt,
        result=task.result,
        error=task.error,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(
    agent_name: str = None,
    service: TaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
) -> TaskListResponse:
    """List all tasks with optional agent filter."""
    tasks = await service.list_tasks(agent_name=agent_name)

    return TaskListResponse(
        count=len(tasks),
        tasks=[
            TaskListItem(
                task_id=t.task_id,
                agent_name=t.agent_name,
                status=t.status,
                created_at=t.created_at,
                prompt_preview=t.metadata.get("prompt_preview") if t.metadata else None
            )
            for t in tasks
        ]
    )


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
) -> dict:
    """Delete a task from the store."""
    deleted = await service.delete_task(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted", "task_id": task_id}


@router.post("/tasks/{task_id}/stop")
async def stop_running_task(
    task_id: str,
    service: TaskService = Depends(get_task_service),
    _: str = Depends(verify_api_key),
) -> dict:
    """Stop a running task."""
    task = await service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status != TaskStatus.RUNNING:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not running (current status: {task.status})"
        )

    success = await stop_task(task_id, service)
    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to stop task - process may have already completed"
        )

    logger.info(f"Task {task_id}: Stopped by user request")
    return {"message": "Task stopped", "task_id": task_id}
