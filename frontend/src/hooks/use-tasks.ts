'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { TaskListItem } from '@/types/task';

export function useTasks(agentFilter?: string, pollInterval = 3000) {
  const [tasks, setTasks] = useState<TaskListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTasks = useCallback(async () => {
    try {
      const response = await api.listTasks(agentFilter);
      setTasks(response.tasks);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch tasks');
    } finally {
      setLoading(false);
    }
  }, [agentFilter]);

  useEffect(() => {
    fetchTasks();

    // Polling for status updates
    const interval = setInterval(fetchTasks, pollInterval);
    return () => clearInterval(interval);
  }, [fetchTasks, pollInterval]);

  return { tasks, loading, error, refetch: fetchTasks };
}
