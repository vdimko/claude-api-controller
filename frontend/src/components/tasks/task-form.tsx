'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { api } from '@/lib/api';
import { Agent } from '@/types/task';
import { Play } from 'lucide-react';

interface TaskFormProps {
  agents: Agent[];
  onTaskCreated: () => void;
}

export function TaskForm({ agents, onTaskCreated }: TaskFormProps) {
  const [agentName, setAgentName] = useState('');
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!agentName || !prompt.trim()) return;

    setLoading(true);
    setError(null);

    try {
      await api.createTask(agentName, prompt);
      setPrompt('');
      onTaskCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create task');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Play size={20} />
          Create New Task
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="agent">Agent</Label>
            <Select
              id="agent"
              value={agentName}
              onChange={(e) => setAgentName(e.target.value)}
            >
              <option value="">Select an agent...</option>
              {agents.map((agent) => (
                <option key={agent.name} value={agent.name}>
                  {agent.name} {agent.has_claude_md ? '(has CLAUDE.md)' : ''}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="prompt">Prompt</Label>
            <Textarea
              id="prompt"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Enter your prompt for the Claude agent..."
              rows={5}
            />
          </div>

          {error && (
            <p className="text-sm text-destructive">{error}</p>
          )}

          <Button
            type="submit"
            disabled={loading || !agentName || !prompt.trim()}
            className="w-full"
          >
            {loading ? 'Creating...' : 'Run Task'}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
