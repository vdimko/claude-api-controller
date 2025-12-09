export type TaskStatusType = 'pending' | 'running' | 'completed' | 'failed' | 'timeout' | 'cancelled';

// Claude CLI опции
export type OutputFormat = 'text' | 'json' | 'stream-json';
export type InputFormat = 'text' | 'stream-json';
export type PermissionMode = 'acceptEdits' | 'bypassPermissions' | 'default' | 'dontAsk' | 'plan';

export interface ClaudeOptions {
  // Основные
  verbose?: boolean;
  output_format?: OutputFormat;
  input_format?: InputFormat;
  model?: string;
  fallback_model?: string;

  // Промпты
  override_claude_md?: boolean;  // UI-only: показать поле system_prompt
  system_prompt?: string;
  append_system_prompt?: string;

  // JSON вывод
  json_schema?: Record<string, unknown>;
  include_partial_messages?: boolean;

  // Инструменты
  allowed_tools?: string[];
  disallowed_tools?: string[];
  tools?: string[];
  dangerously_skip_permissions?: boolean;
  allow_dangerously_skip_permissions?: boolean;

  // Сессии
  continue_session?: boolean;
  resume_session?: string;
  fork_session?: boolean;
  session_id?: string;

  // MCP и плагины
  mcp_config?: string[];
  strict_mcp_config?: boolean;
  mcp_debug?: boolean;
  plugin_dirs?: string[];
  disable_slash_commands?: boolean;

  // Агенты
  agent?: string;
  agents_json?: Record<string, unknown>;

  // Настройки
  permission_mode?: PermissionMode;
  betas?: string[];
  settings_file?: string;
  add_dirs?: string[];
  setting_sources?: string;

  // Дебаг
  debug?: string;

  // IDE
  ide?: boolean;

  // Streaming
  replay_user_messages?: boolean;
}

export interface Task {
  task_id: string;
  agent_name: string;
  status: TaskStatusType;
  prompt?: string;
  result?: string;
  error?: string;
  created_at: string;
  started_at?: string;
  updated_at: string;
  duration_sec?: number;
  prompt_preview?: string;
}

export interface TaskListItem {
  task_id: string;
  agent_name: string;
  status: TaskStatusType;
  created_at: string;
  duration_sec?: number;
  prompt_preview?: string;
}

export interface TaskListResponse {
  count: number;
  tasks: TaskListItem[];
}

export interface Agent {
  name: string;
  has_claude_md: boolean;
}

export interface AgentsResponse {
  agents: Agent[];
}

// Logs
export type LogLevel = 'debug' | 'info' | 'warning' | 'error';

export interface Log {
  log_id: string;
  task_id?: string;
  agent_name: string;
  level: LogLevel;
  message: string;
  timestamp: string;
}

export interface LogListResponse {
  count: number;
  logs: Log[];
}
