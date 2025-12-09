'use client';

import { useState } from 'react';
import { ChevronDown, ChevronRight, Settings } from 'lucide-react';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { ClaudeOptions, OutputFormat, PermissionMode } from '@/types/task';

interface TaskOptionsProps {
  options: ClaudeOptions;
  onChange: (options: ClaudeOptions) => void;
}

export function TaskOptions({ options, onChange }: TaskOptionsProps) {
  const [isOpen, setIsOpen] = useState(false);

  const updateOption = <K extends keyof ClaudeOptions>(key: K, value: ClaudeOptions[K]) => {
    onChange({ ...options, [key]: value });
  };

  // Парсим строку в массив (по запятым или пробелам)
  const parseList = (value: string): string[] => {
    if (!value.trim()) return [];
    return value.split(/[,\s]+/).filter(Boolean);
  };

  // Массив в строку для отображения
  const listToString = (arr?: string[]): string => {
    return arr?.join(', ') || '';
  };

  return (
    <div className="border rounded-lg">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 hover:bg-accent/50 transition-colors"
      >
        <div className="flex items-center gap-2 text-sm font-medium">
          <Settings size={16} />
          Доп. настройки CLI
        </div>
        {isOpen ? <ChevronDown size={16} /> : <ChevronRight size={16} />}
      </button>

      {isOpen && (
        <div className="p-4 pt-0 space-y-6">
          {/* Основные */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground">Основные</h4>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="model">Модель</Label>
                <Select
                  id="model"
                  value={options.model || ''}
                  onChange={(e) => updateOption('model', e.target.value || undefined)}
                >
                  <option value="">По умолчанию</option>
                  <option value="sonnet">Sonnet (быстрый)</option>
                  <option value="opus">Opus (умный)</option>
                  <option value="haiku">Haiku (лёгкий)</option>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="output_format">Формат вывода</Label>
                <Select
                  id="output_format"
                  value={options.output_format || ''}
                  onChange={(e) => updateOption('output_format', (e.target.value || undefined) as OutputFormat | undefined)}
                >
                  <option value="">text (по умолч.)</option>
                  <option value="text">text</option>
                  <option value="json">json</option>
                  <option value="stream-json">stream-json</option>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="fallback_model">Fallback модель</Label>
                <Input
                  id="fallback_model"
                  placeholder="sonnet, opus, haiku..."
                  value={options.fallback_model || ''}
                  onChange={(e) => updateOption('fallback_model', e.target.value || undefined)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="permission_mode">Режим разрешений</Label>
                <Select
                  id="permission_mode"
                  value={options.permission_mode || ''}
                  onChange={(e) => updateOption('permission_mode', (e.target.value || undefined) as PermissionMode | undefined)}
                >
                  <option value="">default</option>
                  <option value="default">default</option>
                  <option value="acceptEdits">acceptEdits</option>
                  <option value="bypassPermissions">bypassPermissions</option>
                  <option value="dontAsk">dontAsk</option>
                  <option value="plan">plan</option>
                </Select>
              </div>
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.verbose || false}
                  onChange={(e) => updateOption('verbose', e.target.checked || undefined)}
                  className="rounded"
                />
                <span className="text-sm">Verbose</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.dangerously_skip_permissions || false}
                  onChange={(e) => updateOption('dangerously_skip_permissions', e.target.checked || undefined)}
                  className="rounded"
                />
                <span className="text-sm text-destructive">Skip permissions</span>
              </label>
            </div>
          </div>

          {/* Промпты */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground">Промпты</h4>

            <div className="p-3 bg-muted/30 rounded-lg text-sm text-muted-foreground">
              По умолчанию используется CLAUDE.md агента (если есть)
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options.override_claude_md || false}
                onChange={(e) => {
                  const checked = e.target.checked;
                  if (checked) {
                    onChange({ ...options, override_claude_md: true });
                  } else {
                    // Снимаем галку и очищаем system_prompt за один вызов
                    const { override_claude_md, system_prompt, ...rest } = options;
                    onChange(rest);
                  }
                }}
                className="rounded"
              />
              <span className="text-sm">Переопределить CLAUDE.md</span>
            </label>

            {options.override_claude_md && (
              <div className="space-y-2">
                <Label htmlFor="system_prompt">System prompt</Label>
                <Textarea
                  id="system_prompt"
                  placeholder="Твой кастомный системный промпт"
                  rows={3}
                  value={options.system_prompt || ''}
                  onChange={(e) => updateOption('system_prompt', e.target.value || undefined)}
                />
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="append_system_prompt">Append system prompt</Label>
              <Textarea
                id="append_system_prompt"
                placeholder="Добавить к системному промпту (работает и с CLAUDE.md)"
                rows={2}
                value={options.append_system_prompt || ''}
                onChange={(e) => updateOption('append_system_prompt', e.target.value || undefined)}
              />
            </div>
          </div>

          {/* JSON */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground">JSON вывод</h4>

            <div className="space-y-2">
              <Label htmlFor="json_schema">JSON Schema</Label>
              <Textarea
                id="json_schema"
                placeholder='{"type":"object","properties":{"name":{"type":"string"}}}'
                rows={3}
                value={options.json_schema ? JSON.stringify(options.json_schema) : ''}
                onChange={(e) => {
                  if (!e.target.value) {
                    updateOption('json_schema', undefined);
                    return;
                  }
                  try {
                    const parsed = JSON.parse(e.target.value);
                    updateOption('json_schema', parsed);
                  } catch {
                    // Пока вводится - ничего не делаем
                  }
                }}
              />
            </div>

            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={options.include_partial_messages || false}
                onChange={(e) => updateOption('include_partial_messages', e.target.checked || undefined)}
                className="rounded"
              />
              <span className="text-sm">Include partial messages (stream-json)</span>
            </label>
          </div>

          {/* Инструменты */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground">Инструменты</h4>

            <div className="space-y-2">
              <Label htmlFor="allowed_tools">Разрешённые (allowed-tools)</Label>
              <Input
                id="allowed_tools"
                placeholder='Bash(git:*), Edit, Read...'
                value={listToString(options.allowed_tools)}
                onChange={(e) => updateOption('allowed_tools', parseList(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="disallowed_tools">Запрещённые (disallowed-tools)</Label>
              <Input
                id="disallowed_tools"
                placeholder='Bash(rm:*), Write...'
                value={listToString(options.disallowed_tools)}
                onChange={(e) => updateOption('disallowed_tools', parseList(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="tools">Доступные инструменты (tools)</Label>
              <Input
                id="tools"
                placeholder='"" для отключения, "default" для всех, или список'
                value={listToString(options.tools)}
                onChange={(e) => updateOption('tools', parseList(e.target.value))}
              />
            </div>
          </div>

          {/* Сессии */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground">Сессии</h4>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.continue_session || false}
                  onChange={(e) => updateOption('continue_session', e.target.checked || undefined)}
                  className="rounded"
                />
                <span className="text-sm">Continue (последняя сессия)</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.fork_session || false}
                  onChange={(e) => updateOption('fork_session', e.target.checked || undefined)}
                  className="rounded"
                />
                <span className="text-sm">Fork session</span>
              </label>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="resume_session">Resume (ID сессии)</Label>
                <Input
                  id="resume_session"
                  placeholder="session-id или поисковый запрос"
                  value={options.resume_session || ''}
                  onChange={(e) => updateOption('resume_session', e.target.value || undefined)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="session_id">Session ID (UUID)</Label>
                <Input
                  id="session_id"
                  placeholder="uuid..."
                  value={options.session_id || ''}
                  onChange={(e) => updateOption('session_id', e.target.value || undefined)}
                />
              </div>
            </div>
          </div>

          {/* MCP */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground">MCP и плагины</h4>

            <div className="space-y-2">
              <Label htmlFor="mcp_config">MCP конфиг (JSON файлы/строки)</Label>
              <Input
                id="mcp_config"
                placeholder="path/to/config.json, ..."
                value={listToString(options.mcp_config)}
                onChange={(e) => updateOption('mcp_config', parseList(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="plugin_dirs">Директории плагинов</Label>
              <Input
                id="plugin_dirs"
                placeholder="path/to/plugins, ..."
                value={listToString(options.plugin_dirs)}
                onChange={(e) => updateOption('plugin_dirs', parseList(e.target.value))}
              />
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.strict_mcp_config || false}
                  onChange={(e) => updateOption('strict_mcp_config', e.target.checked || undefined)}
                  className="rounded"
                />
                <span className="text-sm">Strict MCP config</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.disable_slash_commands || false}
                  onChange={(e) => updateOption('disable_slash_commands', e.target.checked || undefined)}
                  className="rounded"
                />
                <span className="text-sm">Disable slash commands</span>
              </label>
            </div>
          </div>

          {/* Агенты */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground">Агенты</h4>

            <div className="space-y-2">
              <Label htmlFor="agent">Agent</Label>
              <Input
                id="agent"
                placeholder="Имя агента для сессии"
                value={options.agent || ''}
                onChange={(e) => updateOption('agent', e.target.value || undefined)}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="agents_json">Agents JSON</Label>
              <Textarea
                id="agents_json"
                placeholder='{"reviewer": {"description": "...", "prompt": "..."}}'
                rows={2}
                value={options.agents_json ? JSON.stringify(options.agents_json) : ''}
                onChange={(e) => {
                  if (!e.target.value) {
                    updateOption('agents_json', undefined);
                    return;
                  }
                  try {
                    const parsed = JSON.parse(e.target.value);
                    updateOption('agents_json', parsed);
                  } catch {
                    // Пока вводится - ничего не делаем
                  }
                }}
              />
            </div>
          </div>

          {/* Дополнительно */}
          <div className="space-y-4">
            <h4 className="text-sm font-semibold text-muted-foreground">Дополнительно</h4>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="debug">Debug filter</Label>
                <Input
                  id="debug"
                  placeholder="api,hooks или !statsig,!file"
                  value={options.debug || ''}
                  onChange={(e) => updateOption('debug', e.target.value || undefined)}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="betas">Beta headers</Label>
                <Input
                  id="betas"
                  placeholder="beta1, beta2..."
                  value={listToString(options.betas)}
                  onChange={(e) => updateOption('betas', parseList(e.target.value))}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="add_dirs">Дополнительные директории</Label>
              <Input
                id="add_dirs"
                placeholder="/path/to/dir1, /path/to/dir2..."
                value={listToString(options.add_dirs)}
                onChange={(e) => updateOption('add_dirs', parseList(e.target.value))}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="settings_file">Settings file/JSON</Label>
              <Input
                id="settings_file"
                placeholder="path/to/settings.json или JSON строка"
                value={options.settings_file || ''}
                onChange={(e) => updateOption('settings_file', e.target.value || undefined)}
              />
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.ide || false}
                  onChange={(e) => updateOption('ide', e.target.checked || undefined)}
                  className="rounded"
                />
                <span className="text-sm">Auto-connect IDE</span>
              </label>

              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={options.mcp_debug || false}
                  onChange={(e) => updateOption('mcp_debug', e.target.checked || undefined)}
                  className="rounded"
                />
                <span className="text-sm">MCP debug (deprecated)</span>
              </label>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
