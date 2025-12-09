export type TaskStatusType = 'pending' | 'running' | 'completed' | 'failed' | 'timeout' | 'cancelled';

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
