'use client';

import { useState, useEffect, useCallback } from 'react';
import { api } from '@/lib/api';
import { Log } from '@/types/task';

export function useLogs(agentFilter?: string, pollInterval = 2000) {
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      const response = await api.listLogs(agentFilter, 50);
      setLogs(response.logs);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch logs');
    } finally {
      setLoading(false);
    }
  }, [agentFilter]);

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, pollInterval);
    return () => clearInterval(interval);
  }, [fetchLogs, pollInterval]);

  return { logs, loading, error, refetch: fetchLogs };
}
