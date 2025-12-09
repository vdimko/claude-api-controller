'use client';

import { useState } from 'react';
import { TaskList } from '@/components/tasks/task-list';
import { TaskForm } from '@/components/tasks/task-form';
import { AgentSelector } from '@/components/agents/agent-selector';
import { LogPanel } from '@/components/logs/log-panel';
import { useTasks } from '@/hooks/use-tasks';
import { useAgents } from '@/hooks/use-agents';
import { useLogs } from '@/hooks/use-logs';
import { Bot, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const [selectedAgent, setSelectedAgent] = useState<string | undefined>();
  const { tasks, loading: tasksLoading, error: tasksError, refetch } = useTasks(selectedAgent);
  const { agents, loading: agentsLoading, error: agentsError } = useAgents();
  const { logs, loading: logsLoading } = useLogs(selectedAgent);

  const error = tasksError || agentsError;

  return (
    <div className="min-h-screen bg-background pb-14">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bot className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-xl font-bold">Пульт Управления Клодом</h1>
                <p className="text-sm text-muted-foreground">
                  Гоняем агентов как надо
                </p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={refetch}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Обновить
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
            <p className="font-medium">Ёпта, ошибка!</p>
            <p className="text-sm">{error}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left column - Task creation */}
          <div className="lg:col-span-1">
            <TaskForm
              agents={agents}
              onTaskCreated={refetch}
            />

            {agentsLoading && (
              <p className="mt-4 text-sm text-muted-foreground">
                Подгружаем агентов...
              </p>
            )}

            {agents.length === 0 && !agentsLoading && (
              <p className="mt-4 text-sm text-muted-foreground">
                Агентов нет. Создай папку в CUSTOM_AGENTS/ чтобы добавить агента.
              </p>
            )}
          </div>

          {/* Right column - Task list */}
          <div className="lg:col-span-2">
            <div className="mb-4 flex items-center justify-between">
              <AgentSelector
                agents={agents}
                selected={selectedAgent}
                onSelect={setSelectedAgent}
              />
              <p className="text-sm text-muted-foreground">
                Автообновление: 3 сек
              </p>
            </div>
            <TaskList
              tasks={tasks}
              loading={tasksLoading}
              onDelete={refetch}
            />
          </div>
        </div>
      </main>

      <footer className="border-t mt-8">
        <div className="container mx-auto px-4 py-4 text-center text-sm text-muted-foreground">
          Пульт Управления Клодом v2.0 — Монга рулит
        </div>
      </footer>

      {/* Log Panel - fixed at bottom */}
      <LogPanel logs={logs} loading={logsLoading} />
    </div>
  );
}
