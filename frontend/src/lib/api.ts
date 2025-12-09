import { Task, TaskListResponse, AgentsResponse, LogListResponse, ClaudeOptions } from '@/types/task';

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

// Убираем undefined значения и UI-only поля из объекта
function cleanOptions(options?: ClaudeOptions): ClaudeOptions | undefined {
  if (!options) return undefined;

  // Поля, которые только для UI и не отправляются на сервер
  const uiOnlyFields = ['override_claude_md'];

  const cleaned: Record<string, unknown> = {};
  for (const [key, value] of Object.entries(options)) {
    // Пропускаем UI-only поля
    if (uiOnlyFields.includes(key)) continue;
    if (value !== undefined && value !== null && value !== '') {
      // Для массивов проверяем что они не пустые
      if (Array.isArray(value) && value.length === 0) continue;
      cleaned[key] = value;
    }
  }

  return Object.keys(cleaned).length > 0 ? cleaned as ClaudeOptions : undefined;
}

export const api = {
  // Tasks
  createTask: (agentName: string, prompt: string, timeout?: number, options?: ClaudeOptions) =>
    apiRequest<{ task_id: string }>('/run', {
      method: 'POST',
      body: { agent_name: agentName, prompt, timeout, options: cleanOptions(options) },
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
