'use client';

import { Select } from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Agent } from '@/types/task';

interface AgentSelectorProps {
  agents: Agent[];
  selected?: string;
  onSelect: (agentName?: string) => void;
}

export function AgentSelector({ agents, selected, onSelect }: AgentSelectorProps) {
  return (
    <div className="flex items-center gap-3">
      <Label htmlFor="filter-agent" className="whitespace-nowrap">
        Фильтр по агенту:
      </Label>
      <Select
        id="filter-agent"
        value={selected || ''}
        onChange={(e) => onSelect(e.target.value || undefined)}
        className="w-48"
      >
        <option value="">Все агенты</option>
        {agents.map((agent) => (
          <option key={agent.name} value={agent.name}>
            {agent.name}
          </option>
        ))}
      </Select>
    </div>
  );
}
