'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronUp, ChevronDown, Terminal } from 'lucide-react';
import { Log, LogLevel } from '@/types/task';
import { formatDate } from '@/lib/utils';

const levelColors: Record<LogLevel, string> = {
  debug: 'bg-gray-100 text-gray-800',
  info: 'bg-blue-100 text-blue-800',
  warning: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
};

interface LogPanelProps {
  logs: Log[];
  loading: boolean;
}

export function LogPanel({ logs, loading }: LogPanelProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div
      className={`fixed bottom-0 left-0 right-0 bg-background border-t shadow-lg transition-all duration-300 z-50 dark:border-t-2 dark:border-[hsl(320_100%_60%_/_0.5)] dark:shadow-[0_-5px_20px_hsl(320_100%_60%_/_0.2)] ${
        expanded ? 'h-72' : 'h-12'
      }`}
    >
      {/* Header - always visible */}
      <div
        className="h-12 px-4 flex items-center justify-between cursor-pointer hover:bg-muted/50 border-b"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center gap-2">
          <Terminal className="h-4 w-4" />
          <span className="font-medium">Логи</span>
          <Badge variant="secondary" className="text-xs">
            {logs.length}
          </Badge>
          {loading && (
            <span className="text-xs text-muted-foreground ml-2">
              обновляем...
            </span>
          )}
        </div>
        <Button variant="ghost" size="icon" className="h-8 w-8">
          {expanded ? <ChevronDown size={16} /> : <ChevronUp size={16} />}
        </Button>
      </div>

      {/* Content - visible when expanded */}
      {expanded && (
        <div className="h-60 overflow-auto px-4 py-2">
          {logs.length === 0 ? (
            <p className="text-sm text-muted-foreground py-4 text-center">
              Логов пока нет. Появятся когда запустишь задачу.
            </p>
          ) : (
            <div className="space-y-1">
              {logs.map((log) => (
                <div
                  key={log.log_id}
                  className="flex items-start gap-2 text-xs font-mono py-1 border-b border-muted last:border-0"
                >
                  <span className="text-muted-foreground whitespace-nowrap min-w-[140px]">
                    {formatDate(log.timestamp)}
                  </span>
                  <Badge
                    className={`${levelColors[log.level]} text-xs px-1.5 py-0 h-5 min-w-[60px] justify-center`}
                  >
                    {log.level.toUpperCase()}
                  </Badge>
                  <span className="text-primary font-semibold whitespace-nowrap">
                    [{log.agent_name}]
                  </span>
                  {log.task_id && (
                    <span className="text-muted-foreground whitespace-nowrap">
                      {log.task_id.slice(0, 8)}
                    </span>
                  )}
                  <span className="flex-1 break-all">{log.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
