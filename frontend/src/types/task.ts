export type TaskStatusType = 'pending' | 'running' | 'completed' | 'failed' | 'timeout';

export interface Task {
  task_id: string;
  agent_name: string;
  status: TaskStatusType;
  prompt?: string;
  result?: string;
  error?: string;
  created_at: string;
  updated_at: string;
  prompt_preview?: string;
}

export interface TaskListItem {
  task_id: string;
  agent_name: string;
  status: TaskStatusType;
  created_at: string;
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
