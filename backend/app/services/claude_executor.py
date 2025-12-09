import asyncio
import logging
from pathlib import Path
from typing import Dict, Optional

from ..models.task import TaskStatus
from ..config import get_settings
from ..database import get_database
from .task_service import TaskService
from .combined_logger import CombinedLogger

logger = logging.getLogger(__name__)

# Global dict to store running processes for stop functionality
running_processes: Dict[str, asyncio.subprocess.Process] = {}


def get_running_process(task_id: str) -> Optional[asyncio.subprocess.Process]:
    """Get process by task_id."""
    return running_processes.get(task_id)


async def stop_task(task_id: str, service: TaskService) -> bool:
    """Stop a running task by killing its process."""
    process = running_processes.get(task_id)
    if not process:
        logger.warning(f"Task {task_id}: No running process found to stop")
        return False

    # Get task to find agent_name for logging
    task = await service.get_task(task_id)
    agent_name = task.agent_name if task else "unknown"

    # Create combined logger
    db = get_database()
    combined_logger = CombinedLogger(db)

    # IMPORTANT: Remove from running_processes FIRST before killing
    # This prevents run_claude_command from setting status to FAILED
    # when it sees non-zero return code from killed process
    running_processes.pop(task_id, None)

    try:
        # Try graceful termination first
        process.terminate()
        try:
            await asyncio.wait_for(process.wait(), timeout=5.0)
            logger.info(f"Task {task_id}: Process terminated gracefully")
        except asyncio.TimeoutError:
            # Force kill if not terminated
            process.kill()
            await process.wait()
            logger.info(f"Task {task_id}: Process force killed")

        # Update task status to CANCELLED
        await service.update_status(
            task_id,
            TaskStatus.CANCELLED,
            error="Task was cancelled by user"
        )

        # Log to file and MongoDB
        await combined_logger.warning(
            agent_name, "Task cancelled by user", task_id
        )

        logger.info(f"Task {task_id}: Cancelled by user")
        return True
    except Exception as e:
        logger.exception(f"Task {task_id}: Error stopping task: {e}")
        await combined_logger.error(
            agent_name, f"Error stopping task: {e}", task_id
        )
        return False


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

    # Create combined logger
    db = get_database()
    combined_logger = CombinedLogger(db)

    # Truncate prompt for logging
    prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt

    await service.update_status(task_id, TaskStatus.RUNNING)
    logger.info(f"Task {task_id}: Starting execution for agent '{agent_name}' in {agent_dir}")

    # Log task start
    await combined_logger.info(
        agent_name, f"Starting task: {prompt_preview}", task_id
    )

    # Validate agent directory exists
    if not agent_dir.exists():
        error_msg = f"Agent directory not found: {agent_dir}"
        await service.update_status(
            task_id,
            TaskStatus.FAILED,
            error=error_msg
        )
        logger.error(f"Task {task_id}: {error_msg}")
        await combined_logger.error(agent_name, error_msg, task_id)
        return

    # Build command arguments
    cmd_args = ["claude", "-p", prompt]

    # Check for CLAUDE.md in agent directory and use as system prompt
    claude_md_path = agent_dir / "CLAUDE.md"
    if claude_md_path.exists():
        try:
            system_prompt = claude_md_path.read_text(encoding="utf-8").strip()
            if system_prompt:
                cmd_args.extend(["--system-prompt", system_prompt])
                logger.info(f"Task {task_id}: Using CLAUDE.md as system prompt ({len(system_prompt)} chars)")
        except Exception as e:
            logger.warning(f"Task {task_id}: Failed to read CLAUDE.md: {e}")

    try:
        process = await asyncio.create_subprocess_exec(
            *cmd_args,
            cwd=str(agent_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Store process handle for stop functionality
        running_processes[task_id] = process

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            # Check if task was cancelled during execution
            if task_id not in running_processes:
                logger.info(f"Task {task_id}: Was cancelled during execution")
                return

            if process.returncode == 0:
                await service.update_status(
                    task_id,
                    TaskStatus.COMPLETED,
                    result=stdout.decode("utf-8")
                )
                logger.info(f"Task {task_id}: Completed successfully")
                await combined_logger.info(
                    agent_name, "Task completed successfully", task_id
                )
            else:
                error_output = stderr.decode("utf-8") or f"Exit code: {process.returncode}"
                await service.update_status(
                    task_id,
                    TaskStatus.FAILED,
                    error=error_output
                )
                logger.error(f"Task {task_id}: Failed with exit code {process.returncode}")
                await combined_logger.error(
                    agent_name, f"Task failed: {error_output[:200]}", task_id
                )

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            error_msg = f"Command timed out after {timeout} seconds"
            await service.update_status(
                task_id,
                TaskStatus.TIMEOUT,
                error=error_msg
            )
            logger.warning(f"Task {task_id}: Timed out after {timeout}s")
            await combined_logger.warning(agent_name, error_msg, task_id)

    except FileNotFoundError:
        error_msg = "Claude CLI not found. Ensure 'claude' is in PATH."
        await service.update_status(
            task_id,
            TaskStatus.FAILED,
            error=error_msg
        )
        logger.error(f"Task {task_id}: Claude CLI not found")
        await combined_logger.error(agent_name, error_msg, task_id)
    except Exception as e:
        error_msg = str(e)
        await service.update_status(
            task_id,
            TaskStatus.FAILED,
            error=error_msg
        )
        logger.exception(f"Task {task_id}: Unexpected error")
        await combined_logger.error(agent_name, f"Unexpected error: {error_msg}", task_id)
    finally:
        # Remove from running processes dict
        running_processes.pop(task_id, None)
