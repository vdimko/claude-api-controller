'use client';

import { Card, CardContent } from '@/components/ui/card';
import { TaskCard } from './task-card';
import { TaskListItem } from '@/types/task';

interface TaskListProps {
  tasks: TaskListItem[];
  loading: boolean;
  onDelete: () => void;
}

export function TaskList({ tasks, loading, onDelete }: TaskListProps) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <Card>
        <CardContent className="text-center py-8 text-muted-foreground">
          No tasks found. Create one to get started!
        </CardContent>
      </Card>
    );
  }

  return (
    <div>
      <h2 className="text-lg font-semibold mb-3">Tasks ({tasks.length})</h2>
      {tasks.map((task) => (
        <TaskCard key={task.task_id} task={task} onDelete={onDelete} />
      ))}
    </div>
  );
}
