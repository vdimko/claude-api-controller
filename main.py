import asyncio
import logging
import os
import secrets
import sys
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Annotated, Optional

from dotenv import load_dotenv
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

# Load .env file (if exists), environment variables take precedence
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path, override=False)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when required configuration is missing."""
    pass


def get_required_config(key: str) -> str:
    """Get required configuration value from environment."""
    value = os.getenv(key)
    if not value:
        raise ConfigurationError(
            f"Required configuration '{key}' is not set. "
            f"Please set it in .env file or as environment variable."
        )
    return value


def get_optional_config(key: str, default: str) -> str:
    """Get optional configuration value with default."""
    return os.getenv(key, default)


def load_configuration() -> dict:
    """Load and validate all configuration."""
    try:
        # Get agents directory (default to CUSTOM_AGENTS in project root)
        default_agents_dir = str(Path(__file__).parent / "CUSTOM_AGENTS")
        agents_dir = get_optional_config("AGENTS_DIR", default_agents_dir)
        agents_path = Path(agents_dir)

        # Validate agents directory exists
        if not agents_path.exists():
            logger.warning(f"Agents directory does not exist: {agents_dir}")
            agents_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created agents directory: {agents_dir}")

        config = {
            "api_key": get_required_config("CLAUDE_API_KEY"),
            "timeout": int(get_optional_config("CLAUDE_TIMEOUT", "120")),
            "host": get_optional_config("HOST", "127.0.0.1"),
            "port": int(get_optional_config("PORT", "8000")),
            "agents_dir": str(agents_path.resolve()),
        }
        logger.info("Configuration loaded successfully")
        logger.info(f"Agents directory: {config['agents_dir']}")
        return config
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        print(f"\n{'='*60}", file=sys.stderr)
        print("CONFIGURATION ERROR", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\n{e}\n", file=sys.stderr)
        print("Create a .env file with the following content:", file=sys.stderr)
        print("  CLAUDE_API_KEY=your-secret-api-key", file=sys.stderr)
        print("  CLAUDE_TIMEOUT=120       # optional", file=sys.stderr)
        print("  AGENTS_DIR=./CUSTOM_AGENTS  # optional", file=sys.stderr)
        print("  HOST=127.0.0.1           # optional", file=sys.stderr)
        print("  PORT=8000                # optional", file=sys.stderr)
        print(f"\n{'='*60}\n", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Invalid configuration value: {e}")
        print(f"\nConfiguration error: Invalid value - {e}", file=sys.stderr)
        sys.exit(1)


# Load configuration at startup
config = load_configuration()
API_KEY = config["api_key"]
CLAUDE_TIMEOUT = config["timeout"]
AGENTS_DIR = config["agents_dir"]

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Annotated[str | None, Security(api_key_header)]) -> str:
    """Verify the API key from the request header."""
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )
    if not secrets.compare_digest(api_key, API_KEY):
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
    return api_key


app = FastAPI(
    title="Claude API Controller",
    description="Async endpoint to control local Claude CLI installation",
    version="1.0.0",
)


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


class CommandRequest(BaseModel):
    agent_name: str  # Required: name of the agent directory under AGENTS_DIR
    prompt: str
    timeout: Optional[int] = None


class TaskResponse(BaseModel):
    task_id: str


class StatusResponse(BaseModel):
    task_id: str
    agent_name: str
    status: TaskStatus
    result: Optional[str] = None
    error: Optional[str] = None
    created_at: str


# In-memory task store
tasks: dict[str, dict] = {}


async def run_claude_command(task_id: str, agent_name: str, prompt: str, timeout: int) -> None:
    """Execute claude CLI command asynchronously in agent directory."""
    tasks[task_id]["status"] = TaskStatus.RUNNING
    agent_dir = Path(AGENTS_DIR) / agent_name
    logger.info(f"Task {task_id}: Starting execution for agent '{agent_name}' in {agent_dir}")

    # Validate agent directory exists
    if not agent_dir.exists():
        tasks[task_id]["status"] = TaskStatus.FAILED
        tasks[task_id]["error"] = f"Agent directory not found: {agent_dir}"
        logger.error(f"Task {task_id}: Agent directory not found: {agent_dir}")
        return

    try:
        process = await asyncio.create_subprocess_exec(
            "claude",
            "-p",
            prompt,
            cwd=str(agent_dir),  # Run in agent directory
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), timeout=timeout
            )

            if process.returncode == 0:
                tasks[task_id]["status"] = TaskStatus.COMPLETED
                tasks[task_id]["result"] = stdout.decode("utf-8")
                logger.info(f"Task {task_id}: Completed successfully")
            else:
                tasks[task_id]["status"] = TaskStatus.FAILED
                tasks[task_id]["error"] = stderr.decode("utf-8") or f"Exit code: {process.returncode}"
                logger.error(f"Task {task_id}: Failed with exit code {process.returncode}")

        except asyncio.TimeoutError:
            process.kill()
            await process.wait()
            tasks[task_id]["status"] = TaskStatus.TIMEOUT
            tasks[task_id]["error"] = f"Command timed out after {timeout} seconds"
            logger.warning(f"Task {task_id}: Timed out after {timeout}s")

    except FileNotFoundError:
        tasks[task_id]["status"] = TaskStatus.FAILED
        tasks[task_id]["error"] = "Claude CLI not found. Ensure 'claude' is in PATH."
        logger.error(f"Task {task_id}: Claude CLI not found")
    except Exception as e:
        tasks[task_id]["status"] = TaskStatus.FAILED
        tasks[task_id]["error"] = str(e)
        logger.exception(f"Task {task_id}: Unexpected error")


@app.post("/run", response_model=TaskResponse)
async def run_command(
    request: CommandRequest,
    background_tasks: BackgroundTasks,
    _: Annotated[str, Depends(verify_api_key)],
) -> TaskResponse:
    """
    Submit a prompt to be executed by Claude CLI in agent directory.
    Returns a task_id that can be used to poll for results.
    """
    task_id = str(uuid.uuid4())
    timeout = request.timeout or CLAUDE_TIMEOUT

    tasks[task_id] = {
        "status": TaskStatus.PENDING,
        "agent_name": request.agent_name,
        "result": None,
        "error": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    prompt_preview = request.prompt[:50] if len(request.prompt) > 50 else request.prompt
    logger.info(f"Task {task_id}: Agent '{request.agent_name}', prompt: {prompt_preview}...")

    background_tasks.add_task(
        run_claude_command, task_id, request.agent_name, request.prompt, timeout
    )

    return TaskResponse(task_id=task_id)


@app.get("/status/{task_id}", response_model=StatusResponse)
async def get_status(
    task_id: str,
    _: Annotated[str, Depends(verify_api_key)],
) -> StatusResponse:
    """
    Get the status and result of a submitted task.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    task = tasks[task_id]
    logger.info(f"Task {task_id}: Status check - {task['status']}")

    return StatusResponse(
        task_id=task_id,
        agent_name=task["agent_name"],
        status=task["status"],
        result=task["result"],
        error=task["error"],
        created_at=task["created_at"],
    )


@app.get("/tasks")
async def list_tasks(_: Annotated[str, Depends(verify_api_key)]) -> dict:
    """
    List all tasks and their current status.
    """
    return {
        "count": len(tasks),
        "tasks": {
            task_id: {
                "agent_name": task["agent_name"],
                "status": task["status"],
                "created_at": task["created_at"],
            }
            for task_id, task in tasks.items()
        },
    }


@app.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    _: Annotated[str, Depends(verify_api_key)],
) -> dict:
    """
    Delete a task from the store.
    """
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")

    del tasks[task_id]
    logger.info(f"Task {task_id}: Deleted")
    return {"message": "Task deleted", "task_id": task_id}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config["host"], port=config["port"])
