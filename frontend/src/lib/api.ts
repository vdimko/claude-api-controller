import { Task, TaskListResponse, AgentsResponse, LogListResponse } from '@/types/task';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

interface RequestOptions {
  method?: string;
  body?: unknown;
}

async function apiRequest<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': API_KEY,
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

export const api = {
  // Tasks
  createTask: (agentName: string, prompt: string, timeout?: number) =>
    apiRequest<{ task_id: string }>('/run', {
      method: 'POST',
      body: { agent_name: agentName, prompt, timeout },
    }),

  getTaskStatus: (taskId: string) =>
    apiRequest<Task>(`/status/${taskId}`),

  listTasks: (agentName?: string) =>
    apiRequest<TaskListResponse>(`/tasks${agentName ? `?agent_name=${agentName}` : ''}`),

  deleteTask: (taskId: string) =>
    apiRequest<{ message: string }>(`/tasks/${taskId}`, { method: 'DELETE' }),

  stopTask: (taskId: string) =>
    apiRequest<{ message: string }>(`/tasks/${taskId}/stop`, { method: 'POST' }),

  // Agents
  listAgents: () =>
    apiRequest<AgentsResponse>('/agents'),

  // Logs
  listLogs: (agentName?: string, limit: number = 50) => {
    const params = new URLSearchParams();
    if (agentName) params.append('agent_name', agentName);
    params.append('limit', limit.toString());
    return apiRequest<LogListResponse>(`/logs?${params.toString()}`);
  },
};
