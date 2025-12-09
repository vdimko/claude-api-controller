'use client';

import { Badge } from '@/components/ui/badge';
import { TaskStatusType } from '@/types/task';

const statusConfig: Record<TaskStatusType, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' }> = {
  pending: { label: 'Pending', variant: 'secondary' },
  running: { label: 'Running', variant: 'default' },
  completed: { label: 'Completed', variant: 'success' },
  failed: { label: 'Failed', variant: 'destructive' },
  timeout: { label: 'Timeout', variant: 'warning' },
};

interface TaskStatusBadgeProps {
  status: TaskStatusType;
}

export function TaskStatusBadge({ status }: TaskStatusBadgeProps) {
  const config = statusConfig[status];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
