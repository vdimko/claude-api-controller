import asyncio
import logging
from pathlib import Path

from ..models.task import TaskStatus
from ..config import get_settings
from .task_service import TaskService

logger = logging.getLogger(__name__)


async def run_claude_command(
    service: TaskService,
    task_id: str,
    agent_name: str,
    prompt: str,
    timeout: int
) -> None:
    """Execute claude CLI command asynchronously in agent directory."""
    settings = get_settings()
    agent_dir = Path(settings.agents_dir) / agent_name

    await service.update_status(task_id, TaskStatus.RUNNING)
    logger.info(f"Task {task_id}: Starting execution for agent '{agent_name}' in {agent_dir}")

    # Validate agent directory exists
    if not agent_dir.exists():
        await service.update_status(
            task_id,
            TaskStatus.FAILED,
            error=f"Agent directory not found: {agent_dir}"
        )
        logger.error(f"Task {task_id}: Agent directory not found: {agent_dir}")
        return

    try:
        process = await asyncio.create_subprocess_exec(
            "claude",
            "-p",
            prompt,
            cwd=str(agent_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            if process.returncode == 0:
                await service.update_status(
                    task_id,
                    TaskStatus.COMPLETED,
                    result=stdout.decode("utf-8")
                )
                logger.info(f"Task {task_id}: Completed successfully")
            else:
                await service.update_status(
                    task_id,
                    TaskStatus.FAILED,
                    error=stderr.decode("utf-8") or f"Exit code: {process.returncode}"
                )
                logger.error(f"Task {task_id}: Failed with exit code {process.returncode}")

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            await service.update_status(
                task_id,
                TaskStatus.TIMEOUT,
                error=f"Command timed out after {timeout} seconds"
            )
            logger.warning(f"Task {task_id}: Timed out after {timeout}s")

    except FileNotFoundError:
        await service.update_status(
            task_id,
            TaskStatus.FAILED,
            error="Claude CLI not found. Ensure 'claude' is in PATH."
        )
        logger.error(f"Task {task_id}: Claude CLI not found")
    except Exception as e:
        await service.update_status(
            task_id,
            TaskStatus.FAILED,
            error=str(e)
        )
        logger.exception(f"Task {task_id}: Unexpected error")
