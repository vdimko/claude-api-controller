import logging
from datetime import datetime, timezone
from typing import Optional, List

from motor.motor_asyncio import AsyncIOMotorDatabase

from ..models.task import TaskDocument, TaskStatus

logger = logging.getLogger(__name__)


class TaskService:
    """Service for task CRUD operations with MongoDB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.collection = db.tasks

    async def create_task(
        self,
        agent_name: str,
        prompt: str,
        timeout: int
    ) -> TaskDocument:
        """Create a new task in the database."""
        task = TaskDocument(
            agent_name=agent_name,
            prompt=prompt,
            timeout_seconds=timeout,
            metadata={"prompt_preview": prompt[:100] if len(prompt) > 100 else prompt}
        )
        await self.collection.insert_one(task.to_mongo())
        logger.info(f"Task {task.task_id}: Created for agent '{agent_name}'")
        return task

    async def get_task(self, task_id: str) -> Optional[TaskDocument]:
        """Get a task by its ID."""
        doc = await self.collection.find_one({"task_id": task_id})
        return TaskDocument.from_mongo(doc) if doc else None

    async def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: str = None,
        error: str = None
    ) -> bool:
        """Update task status and optionally result/error."""
        now = datetime.now(timezone.utc)
        status_value = status.value if isinstance(status, TaskStatus) else status

        update = {
            "status": status_value,
            "updated_at": now
        }

        # Set started_at when transitioning to RUNNING
        if status_value == TaskStatus.RUNNING.value:
            update["started_at"] = now

        # Calculate duration for terminal states
        if status_value in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value,
                           TaskStatus.TIMEOUT.value, TaskStatus.CANCELLED.value]:
            task = await self.get_task(task_id)
            if task and task.started_at:
                started = task.started_at
                # Make timezone-aware if naive (MongoDB returns naive datetimes)
                if started.tzinfo is None:
                    started = started.replace(tzinfo=timezone.utc)
                duration = (now - started).total_seconds()
                update["duration_sec"] = round(duration, 2)

        if result is not None:
            update["result"] = result
        if error is not None:
            update["error"] = error

        result_op = await self.collection.update_one(
            {"task_id": task_id},
            {"$set": update}
        )
        return result_op.modified_count > 0

    async def list_tasks(
        self,
        agent_name: str = None,
        status: TaskStatus = None,
        limit: int = 100
    ) -> List[TaskDocument]:
        """List tasks with optional filters."""
        query = {}
        if agent_name:
            query["agent_name"] = agent_name
        if status:
            query["status"] = status.value if isinstance(status, TaskStatus) else status

        cursor = self.collection.find(query).sort("created_at", -1).limit(limit)
        tasks = []
        async for doc in cursor:
            tasks.append(TaskDocument.from_mongo(doc))
        return tasks

    async def delete_task(self, task_id: str) -> bool:
        """Delete a task by its ID."""
        result = await self.collection.delete_one({"task_id": task_id})
        if result.deleted_count > 0:
            logger.info(f"Task {task_id}: Deleted")
            return True
        return False
