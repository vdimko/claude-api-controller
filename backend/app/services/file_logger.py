import logging
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..config import get_settings


class AgentFileLogger:
    """Logger that writes to agent-specific log files in ./logs directory."""

    def __init__(self):
        self._handlers: Dict[str, logging.FileHandler] = {}
        self._loggers: Dict[str, logging.Logger] = {}
        self._initialized = False

    def _ensure_init(self):
        """Lazy initialization to avoid issues during import."""
        if self._initialized:
            return
        settings = get_settings()
        self.logs_dir = Path(settings.logs_dir)
        self.logs_dir.mkdir(exist_ok=True)
        self._initialized = True

    def _get_logger(self, agent_name: str) -> logging.Logger:
        """Get or create logger for agent."""
        self._ensure_init()

        if agent_name not in self._loggers:
            log_file = self.logs_dir / f"{agent_name}.log"

            # Create a unique logger for this agent
            logger = logging.getLogger(f"agent.{agent_name}")
            logger.setLevel(logging.DEBUG)

            # Prevent propagation to root logger
            logger.propagate = False

            # Create file handler
            handler = logging.FileHandler(log_file, encoding="utf-8")
            handler.setLevel(logging.DEBUG)
            handler.setFormatter(
                logging.Formatter(
                    "[%(asctime)s] [%(levelname)s] %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )

            logger.addHandler(handler)
            self._handlers[agent_name] = handler
            self._loggers[agent_name] = logger

        return self._loggers[agent_name]

    def log(
        self, agent_name: str, level: str, task_id: str, message: str
    ) -> None:
        """Write log entry to agent's log file.

        Args:
            agent_name: Name of the agent
            level: Log level (DEBUG, INFO, WARNING, ERROR)
            task_id: Task ID or 'system' for system messages
            message: Log message
        """
        logger = self._get_logger(agent_name)
        log_level = getattr(logging, level.upper(), logging.INFO)

        # Format message with task_id prefix
        formatted_message = f"[{task_id[:8] if len(task_id) > 8 else task_id}] {message}"

        logger.log(log_level, formatted_message)

    def info(self, agent_name: str, task_id: str, message: str) -> None:
        """Log INFO level message."""
        self.log(agent_name, "INFO", task_id, message)

    def warning(self, agent_name: str, task_id: str, message: str) -> None:
        """Log WARNING level message."""
        self.log(agent_name, "WARNING", task_id, message)

    def error(self, agent_name: str, task_id: str, message: str) -> None:
        """Log ERROR level message."""
        self.log(agent_name, "ERROR", task_id, message)

    def debug(self, agent_name: str, task_id: str, message: str) -> None:
        """Log DEBUG level message."""
        self.log(agent_name, "DEBUG", task_id, message)


# Singleton instance
agent_file_logger = AgentFileLogger()
