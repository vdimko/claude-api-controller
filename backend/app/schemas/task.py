from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any

from pydantic import BaseModel, Field

from ..models.task import TaskStatus


class OutputFormat(str, Enum):
    """Формат вывода Claude CLI."""
    TEXT = "text"
    JSON = "json"
    STREAM_JSON = "stream-json"


class InputFormat(str, Enum):
    """Формат ввода Claude CLI."""
    TEXT = "text"
    STREAM_JSON = "stream-json"


class PermissionMode(str, Enum):
    """Режим разрешений Claude CLI."""
    ACCEPT_EDITS = "acceptEdits"
    BYPASS_PERMISSIONS = "bypassPermissions"
    DEFAULT = "default"
    DONT_ASK = "dontAsk"
    PLAN = "plan"


class ClaudeOptions(BaseModel):
    """Опции для Claude CLI."""

    # Основные
    verbose: Optional[bool] = None
    output_format: Optional[OutputFormat] = None
    input_format: Optional[InputFormat] = None
    model: Optional[str] = Field(None, description="sonnet, opus, haiku или полное имя модели")
    fallback_model: Optional[str] = None

    # Промпты
    system_prompt: Optional[str] = None
    append_system_prompt: Optional[str] = None

    # JSON вывод
    json_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema для структурированного вывода")
    include_partial_messages: Optional[bool] = None

    # Инструменты
    allowed_tools: Optional[List[str]] = Field(None, description="Разрешённые инструменты (e.g. 'Bash(git:*) Edit')")
    disallowed_tools: Optional[List[str]] = Field(None, description="Запрещённые инструменты")
    tools: Optional[List[str]] = Field(None, description="Набор доступных инструментов ('' для отключения, 'default' для всех)")
    dangerously_skip_permissions: Optional[bool] = None
    allow_dangerously_skip_permissions: Optional[bool] = None

    # Сессии
    continue_session: Optional[bool] = Field(None, alias="continue", description="Продолжить последнюю сессию")
    resume_session: Optional[str] = Field(None, description="ID сессии для возобновления")
    fork_session: Optional[bool] = None
    session_id: Optional[str] = Field(None, description="UUID сессии")

    # MCP и плагины
    mcp_config: Optional[List[str]] = Field(None, description="JSON файлы или строки конфигурации MCP")
    strict_mcp_config: Optional[bool] = None
    mcp_debug: Optional[bool] = Field(None, description="[DEPRECATED] Режим отладки MCP")
    plugin_dirs: Optional[List[str]] = Field(None, description="Директории плагинов")
    disable_slash_commands: Optional[bool] = None

    # Агенты
    agent: Optional[str] = Field(None, description="Агент для текущей сессии")
    agents_json: Optional[Dict[str, Any]] = Field(None, description="JSON с кастомными агентами")

    # Настройки
    permission_mode: Optional[PermissionMode] = None
    betas: Optional[List[str]] = Field(None, description="Beta headers для API запросов")
    settings_file: Optional[str] = Field(None, description="Путь к файлу настроек или JSON строка")
    add_dirs: Optional[List[str]] = Field(None, description="Дополнительные директории для доступа")
    setting_sources: Optional[str] = Field(None, description="Источники настроек (user, project, local)")

    # Дебаг
    debug: Optional[str] = Field(None, description="Режим отладки с опциональным фильтром (e.g. 'api,hooks')")

    # IDE
    ide: Optional[bool] = Field(None, description="Автоподключение к IDE")

    # Streaming
    replay_user_messages: Optional[bool] = None

    class Config:
        populate_by_name = True


class TaskCreateRequest(BaseModel):
    """Request body for creating a new task."""
    agent_name: str
    prompt: str
    timeout: Optional[int] = None
    options: Optional[ClaudeOptions] = None


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
