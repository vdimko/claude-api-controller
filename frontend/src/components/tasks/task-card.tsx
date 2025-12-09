'use client';

import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TaskStatusBadge } from './task-status-badge';
import { TaskListItem, Task } from '@/types/task';
import { api } from '@/lib/api';
import { formatDate, truncate, formatDuration } from '@/lib/utils';
import { Trash2, ChevronDown, ChevronUp, Eye, Square } from 'lucide-react';

interface TaskCardProps {
  task: TaskListItem;
  onDelete: () => void;
}

export function TaskCard({ task, onDelete }: TaskCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [details, setDetails] = useState<Task | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Poll for updates when expanded and task is still running/pending
  useEffect(() => {
    const shouldPoll = expanded && details && (details.status === 'running' || details.status === 'pending');

    if (shouldPoll) {
      pollIntervalRef.current = setInterval(async () => {
        try {
          const taskDetails = await api.getTaskStatus(task.task_id);
          setDetails(taskDetails);
          // Stop polling if task is no longer running/pending
          if (taskDetails.status !== 'running' && taskDetails.status !== 'pending') {
            if (pollIntervalRef.current) {
              clearInterval(pollIntervalRef.current);
              pollIntervalRef.current = null;
            }
          }
        } catch (error) {
          console.error('Failed to poll task details:', error);
        }
      }, 2000);
    }

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [expanded, details?.status, task.task_id]);

  const handleExpand = async () => {
    if (!expanded) {
      // Always fetch fresh data when expanding
      setLoading(true);
      try {
        const taskDetails = await api.getTaskStatus(task.task_id);
        setDetails(taskDetails);
      } catch (error) {
        console.error('Failed to load task details:', error);
      } finally {
        setLoading(false);
      }
    }
    setExpanded(!expanded);
  };

  const handleDelete = async () => {
    if (!confirm('Точно удалить эту задачу?')) return;
    setDeleting(true);
    try {
      await api.deleteTask(task.task_id);
      onDelete();
    } catch (error) {
      console.error('Failed to delete task:', error);
    } finally {
      setDeleting(false);
    }
  };

  const handleStop = async () => {
    if (!confirm('Остановить эту задачу?')) return;
    setStopping(true);
    try {
      await api.stopTask(task.task_id);
      onDelete(); // Refresh the list
    } catch (error) {
      console.error('Failed to stop task:', error);
    } finally {
      setStopping(false);
    }
  };

  return (
    <Card className="mb-3">
      <CardHeader className="py-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <TaskStatusBadge status={task.status} />
            <CardTitle className="text-sm font-medium truncate">
              {task.agent_name}
            </CardTitle>
            <span className="text-xs text-muted-foreground hidden sm:inline">
              {formatDate(task.created_at)}
            </span>
            {task.duration_sec !== undefined && task.duration_sec !== null && (
              <span className="text-xs text-muted-foreground hidden sm:inline">
                ({formatDuration(task.duration_sec)})
              </span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              onClick={handleExpand}
              disabled={loading}
            >
              {expanded ? <ChevronUp size={16} /> : <Eye size={16} />}
            </Button>
            {task.status === 'running' && (
              <Button
                variant="ghost"
                size="icon"
                onClick={handleStop}
                disabled={stopping}
                className="text-orange-500 hover:text-orange-600"
                title="Стоп"
              >
                <Square size={16} />
              </Button>
            )}
            <Button
              variant="ghost"
              size="icon"
              onClick={handleDelete}
              disabled={deleting}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 size={16} />
            </Button>
          </div>
        </div>
        {task.prompt_preview && (
          <p className="text-xs text-muted-foreground mt-1 truncate">
            {truncate(task.prompt_preview, 80)}
          </p>
        )}
      </CardHeader>

      {expanded && (
        <CardContent className="pt-0 pb-4">
          {loading ? (
            <p className="text-sm text-muted-foreground">Загружаем...</p>
          ) : details ? (
            <div className="space-y-3 text-sm">
              <div className="flex flex-wrap gap-4">
                <div>
                  <span className="font-medium">ID:</span>
                  <code className="ml-2 text-xs bg-muted px-1 py-0.5 rounded">
                    {details.task_id}
                  </code>
                </div>
                {details.duration_sec !== undefined && details.duration_sec !== null && (
                  <div>
                    <span className="font-medium">Время:</span>
                    <span className="ml-2 text-xs">{formatDuration(details.duration_sec)}</span>
                  </div>
                )}
              </div>

              {details.prompt && (
                <div>
                  <span className="font-medium">Промпт:</span>
                  <pre className="mt-1 p-2 bg-muted rounded text-xs whitespace-pre-wrap max-h-32 overflow-auto">
                    {details.prompt}
                  </pre>
                </div>
              )}

              {details.result && (
                <div>
                  <span className="font-medium text-green-600 dark:text-green-400">Результат:</span>
                  <pre className="mt-1 p-2 bg-green-50 dark:bg-green-950 border border-green-200 dark:border-green-800 rounded text-xs whitespace-pre-wrap max-h-64 overflow-auto">
                    {details.result}
                  </pre>
                </div>
              )}

              {details.error && (
                <div>
                  <span className="font-medium text-destructive">Ошибка:</span>
                  <pre className="mt-1 p-2 bg-red-50 dark:bg-red-950 border border-red-200 dark:border-red-800 rounded text-xs whitespace-pre-wrap">
                    {details.error}
                  </pre>
                </div>
              )}
            </div>
          ) : null}
        </CardContent>
      )}
    </Card>
  );
}
