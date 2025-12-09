'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { TaskStatusBadge } from './task-status-badge';
import { TaskListItem, Task } from '@/types/task';
import { api } from '@/lib/api';
import { formatDate, truncate } from '@/lib/utils';
import { Trash2, ChevronDown, ChevronUp, Eye } from 'lucide-react';

interface TaskCardProps {
  task: TaskListItem;
  onDelete: () => void;
}

export function TaskCard({ task, onDelete }: TaskCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [details, setDetails] = useState<Task | null>(null);
  const [loading, setLoading] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleExpand = async () => {
    if (!expanded && !details) {
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
    if (!confirm('Are you sure you want to delete this task?')) return;
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
            <p className="text-sm text-muted-foreground">Loading...</p>
          ) : details ? (
            <div className="space-y-3 text-sm">
              <div>
                <span className="font-medium">Task ID:</span>
                <code className="ml-2 text-xs bg-muted px-1 py-0.5 rounded">
                  {details.task_id}
                </code>
              </div>

              {details.prompt && (
                <div>
                  <span className="font-medium">Prompt:</span>
                  <pre className="mt-1 p-2 bg-muted rounded text-xs whitespace-pre-wrap max-h-32 overflow-auto">
                    {details.prompt}
                  </pre>
                </div>
              )}

              {details.result && (
                <div>
                  <span className="font-medium text-green-600">Result:</span>
                  <pre className="mt-1 p-2 bg-green-50 border border-green-200 rounded text-xs whitespace-pre-wrap max-h-64 overflow-auto">
                    {details.result}
                  </pre>
                </div>
              )}

              {details.error && (
                <div>
                  <span className="font-medium text-destructive">Error:</span>
                  <pre className="mt-1 p-2 bg-red-50 border border-red-200 rounded text-xs whitespace-pre-wrap">
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
