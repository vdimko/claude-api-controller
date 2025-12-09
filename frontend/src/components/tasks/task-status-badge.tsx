'use client';

import { Badge } from '@/components/ui/badge';
import { TaskStatusType } from '@/types/task';

const statusConfig: Record<TaskStatusType, { label: string; variant: 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning' }> = {
  pending: { label: 'Ждём', variant: 'secondary' },
  running: { label: 'Пашет', variant: 'default' },
  completed: { label: 'Готово', variant: 'success' },
  failed: { label: 'Обосрался', variant: 'destructive' },
  timeout: { label: 'Завис', variant: 'warning' },
  cancelled: { label: 'Отменено', variant: 'warning' },
};

interface TaskStatusBadgeProps {
  status: TaskStatusType;
}

export function TaskStatusBadge({ status }: TaskStatusBadgeProps) {
  const config = statusConfig[status];
  return <Badge variant={config.variant}>{config.label}</Badge>;
}
