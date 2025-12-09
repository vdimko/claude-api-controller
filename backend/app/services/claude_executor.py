import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from ..models.task import TaskStatus
from ..config import get_settings
from ..database import get_database
from ..schemas.task import ClaudeOptions
from .task_service import TaskService
from .combined_logger import CombinedLogger

logger = logging.getLogger(__name__)

# Global dict to store running processes for stop functionality
running_processes: Dict[str, asyncio.subprocess.Process] = {}


def build_command_args(prompt: str, options: Optional[ClaudeOptions] = None) -> List[str]:
    """Построить аргументы команды claude CLI."""
    args = ["claude", "-p", prompt]

    if not options:
        return args

    # Основные опции
    if options.verbose:
        args.append("--verbose")

    if options.output_format:
        args.extend(["--output-format", options.output_format.value])

    if options.input_format:
        args.extend(["--input-format", options.input_format.value])

    if options.model:
        args.extend(["--model", options.model])

    if options.fallback_model:
        args.extend(["--fallback-model", options.fallback_model])

    # Промпты
    if options.system_prompt:
        args.extend(["--system-prompt", options.system_prompt])

    if options.append_system_prompt:
        args.extend(["--append-system-prompt", options.append_system_prompt])

    # JSON вывод
    if options.json_schema:
        args.extend(["--json-schema", json.dumps(options.json_schema)])

    if options.include_partial_messages:
        args.append("--include-partial-messages")

    # Инструменты
    if options.allowed_tools:
        args.extend(["--allowed-tools", *options.allowed_tools])

    if options.disallowed_tools:
        args.extend(["--disallowed-tools", *options.disallowed_tools])

    if options.tools:
        args.extend(["--tools", *options.tools])

    if options.dangerously_skip_permissions:
        args.append("--dangerously-skip-permissions")

    if options.allow_dangerously_skip_permissions:
        args.append("--allow-dangerously-skip-permissions")

    # Сессии
    if options.continue_session:
        args.append("--continue")

    if options.resume_session:
        args.extend(["--resume", options.resume_session])

    if options.fork_session:
        args.append("--fork-session")

    if options.session_id:
        args.extend(["--session-id", options.session_id])

    # MCP и плагины
    if options.mcp_config:
        args.extend(["--mcp-config", *options.mcp_config])

    if options.strict_mcp_config:
        args.append("--strict-mcp-config")

    if options.mcp_debug:
        args.append("--mcp-debug")

    if options.plugin_dirs:
        args.extend(["--plugin-dir", *options.plugin_dirs])

    if options.disable_slash_commands:
        args.append("--disable-slash-commands")

    # Агенты
    if options.agent:
        args.extend(["--agent", options.agent])

    if options.agents_json:
        args.extend(["--agents", json.dumps(options.agents_json)])

    # Настройки
    if options.permission_mode:
        args.extend(["--permission-mode", options.permission_mode.value])

    if options.betas:
        args.extend(["--betas", *options.betas])

    if options.settings_file:
        args.extend(["--settings", options.settings_file])

    if options.add_dirs:
        args.extend(["--add-dir", *options.add_dirs])

    if options.setting_sources:
        args.extend(["--setting-sources", options.setting_sources])

    # Дебаг
    if options.debug:
        args.extend(["--debug", options.debug])

    # IDE
    if options.ide:
        args.append("--ide")

    # Streaming
    if options.replay_user_messages:
        args.append("--replay-user-messages")

    return args


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
    timeout: int,
    options: Optional[ClaudeOptions] = None
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

    # Build command arguments using options
    effective_options = options or ClaudeOptions()

    # Check for CLAUDE.md in agent directory and use as system prompt if not overridden
    if not effective_options.system_prompt:
        claude_md_path = agent_dir / "CLAUDE.md"
        if claude_md_path.exists():
            try:
                system_prompt = claude_md_path.read_text(encoding="utf-8").strip()
                if system_prompt:
                    effective_options = effective_options.model_copy(
                        update={"system_prompt": system_prompt}
                    )
                    logger.info(f"Task {task_id}: Using CLAUDE.md as system prompt ({len(system_prompt)} chars)")
            except Exception as e:
                logger.warning(f"Task {task_id}: Failed to read CLAUDE.md: {e}")

    cmd_args = build_command_args(prompt, effective_options)
    logger.debug(f"Task {task_id}: Command args: {' '.join(cmd_args[:5])}...")

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
