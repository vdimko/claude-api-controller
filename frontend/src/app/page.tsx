'use client';

import { useState } from 'react';
import { TaskList } from '@/components/tasks/task-list';
import { TaskForm } from '@/components/tasks/task-form';
import { AgentSelector } from '@/components/agents/agent-selector';
import { useTasks } from '@/hooks/use-tasks';
import { useAgents } from '@/hooks/use-agents';
import { Bot, RefreshCw } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Dashboard() {
  const [selectedAgent, setSelectedAgent] = useState<string | undefined>();
  const { tasks, loading: tasksLoading, error: tasksError, refetch } = useTasks(selectedAgent);
  const { agents, loading: agentsLoading, error: agentsError } = useAgents();

  const error = tasksError || agentsError;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Bot className="h-8 w-8 text-primary" />
              <div>
                <h1 className="text-xl font-bold">Claude API Dashboard</h1>
                <p className="text-sm text-muted-foreground">
                  Task management for Claude CLI agents
                </p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={refetch}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-4 py-6">
        {error && (
          <div className="mb-6 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
            <p className="font-medium">Error</p>
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
                Loading agents...
              </p>
            )}

            {agents.length === 0 && !agentsLoading && (
              <p className="mt-4 text-sm text-muted-foreground">
                No agents found. Create a directory in CUSTOM_AGENTS/ to add an agent.
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
                Auto-refresh: 3s
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
          Claude API Controller v2.0 - MongoDB Storage
        </div>
      </footer>
    </div>
  );
}
