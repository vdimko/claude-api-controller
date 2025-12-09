'use client';

import { useMemo, useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Check } from 'lucide-react';

interface JsonViewerProps {
  data: string;
  className?: string;
}

// Проверяем, является ли строка валидным JSON
function tryParseJson(str: string): { isJson: boolean; data: unknown } {
  try {
    const trimmed = str.trim();
    // Должен начинаться с { или [
    if (!trimmed.startsWith('{') && !trimmed.startsWith('[')) {
      return { isJson: false, data: null };
    }
    const parsed = JSON.parse(trimmed);
    return { isJson: true, data: parsed };
  } catch {
    return { isJson: false, data: null };
  }
}

// Цвета для разных типов
const typeColors: Record<string, string> = {
  string: 'text-green-600 dark:text-green-400',
  number: 'text-blue-600 dark:text-blue-400',
  boolean: 'text-purple-600 dark:text-purple-400',
  null: 'text-gray-500 dark:text-gray-400',
  key: 'text-amber-700 dark:text-amber-400',
};

interface JsonNodeProps {
  data: unknown;
  depth?: number;
  keyName?: string;
  isLast?: boolean;
}

function JsonNode({ data, depth = 0, keyName, isLast = true }: JsonNodeProps) {
  const [collapsed, setCollapsed] = useState(depth > 2); // Автосворачивание глубоких уровней
  const indent = depth * 16;

  if (data === null) {
    return (
      <div style={{ marginLeft: indent }} className="flex items-center">
        {keyName && (
          <>
            <span className={typeColors.key}>"{keyName}"</span>
            <span className="text-gray-500">: </span>
          </>
        )}
        <span className={typeColors.null}>null</span>
        {!isLast && <span className="text-gray-500">,</span>}
      </div>
    );
  }

  if (typeof data === 'string') {
    return (
      <div style={{ marginLeft: indent }} className="flex items-start">
        {keyName && (
          <>
            <span className={typeColors.key}>"{keyName}"</span>
            <span className="text-gray-500">: </span>
          </>
        )}
        <span className={`${typeColors.string} break-all whitespace-pre-wrap`}>"{data}"</span>
        {!isLast && <span className="text-gray-500">,</span>}
      </div>
    );
  }

  if (typeof data === 'number') {
    return (
      <div style={{ marginLeft: indent }} className="flex items-center">
        {keyName && (
          <>
            <span className={typeColors.key}>"{keyName}"</span>
            <span className="text-gray-500">: </span>
          </>
        )}
        <span className={typeColors.number}>{data}</span>
        {!isLast && <span className="text-gray-500">,</span>}
      </div>
    );
  }

  if (typeof data === 'boolean') {
    return (
      <div style={{ marginLeft: indent }} className="flex items-center">
        {keyName && (
          <>
            <span className={typeColors.key}>"{keyName}"</span>
            <span className="text-gray-500">: </span>
          </>
        )}
        <span className={typeColors.boolean}>{data.toString()}</span>
        {!isLast && <span className="text-gray-500">,</span>}
      </div>
    );
  }

  if (Array.isArray(data)) {
    if (data.length === 0) {
      return (
        <div style={{ marginLeft: indent }} className="flex items-center">
          {keyName && (
            <>
              <span className={typeColors.key}>"{keyName}"</span>
              <span className="text-gray-500">: </span>
            </>
          )}
          <span className="text-gray-500">[]</span>
          {!isLast && <span className="text-gray-500">,</span>}
        </div>
      );
    }

    return (
      <div>
        <div
          style={{ marginLeft: indent }}
          className="flex items-center cursor-pointer hover:bg-muted/50 rounded"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? (
            <ChevronRight size={14} className="text-gray-400 flex-shrink-0" />
          ) : (
            <ChevronDown size={14} className="text-gray-400 flex-shrink-0" />
          )}
          {keyName && (
            <>
              <span className={typeColors.key}>"{keyName}"</span>
              <span className="text-gray-500">: </span>
            </>
          )}
          <span className="text-gray-500">[</span>
          {collapsed && (
            <>
              <span className="text-gray-400 text-xs ml-1">{data.length} items</span>
              <span className="text-gray-500">]</span>
              {!isLast && <span className="text-gray-500">,</span>}
            </>
          )}
        </div>
        {!collapsed && (
          <>
            {data.map((item, idx) => (
              <JsonNode
                key={idx}
                data={item}
                depth={depth + 1}
                isLast={idx === data.length - 1}
              />
            ))}
            <div style={{ marginLeft: indent }} className="text-gray-500">
              ]{!isLast && ','}
            </div>
          </>
        )}
      </div>
    );
  }

  if (typeof data === 'object') {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0) {
      return (
        <div style={{ marginLeft: indent }} className="flex items-center">
          {keyName && (
            <>
              <span className={typeColors.key}>"{keyName}"</span>
              <span className="text-gray-500">: </span>
            </>
          )}
          <span className="text-gray-500">{'{}'}</span>
          {!isLast && <span className="text-gray-500">,</span>}
        </div>
      );
    }

    return (
      <div>
        <div
          style={{ marginLeft: indent }}
          className="flex items-center cursor-pointer hover:bg-muted/50 rounded"
          onClick={() => setCollapsed(!collapsed)}
        >
          {collapsed ? (
            <ChevronRight size={14} className="text-gray-400 flex-shrink-0" />
          ) : (
            <ChevronDown size={14} className="text-gray-400 flex-shrink-0" />
          )}
          {keyName && (
            <>
              <span className={typeColors.key}>"{keyName}"</span>
              <span className="text-gray-500">: </span>
            </>
          )}
          <span className="text-gray-500">{'{'}</span>
          {collapsed && (
            <>
              <span className="text-gray-400 text-xs ml-1">{entries.length} keys</span>
              <span className="text-gray-500">{'}'}</span>
              {!isLast && <span className="text-gray-500">,</span>}
            </>
          )}
        </div>
        {!collapsed && (
          <>
            {entries.map(([key, value], idx) => (
              <JsonNode
                key={key}
                data={value}
                depth={depth + 1}
                keyName={key}
                isLast={idx === entries.length - 1}
              />
            ))}
            <div style={{ marginLeft: indent }} className="text-gray-500">
              {'}'}{!isLast && ','}
            </div>
          </>
        )}
      </div>
    );
  }

  return <div style={{ marginLeft: indent }}>{String(data)}</div>;
}

export function JsonViewer({ data, className = '' }: JsonViewerProps) {
  const [copied, setCopied] = useState(false);

  const parseResult = useMemo(() => tryParseJson(data), [data]);

  const handleCopy = async () => {
    try {
      // Копируем отформатированный JSON если это JSON, иначе как есть
      const textToCopy = parseResult.isJson
        ? JSON.stringify(parseResult.data, null, 2)
        : data;
      await navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback
    }
  };

  // Если не JSON — показываем как обычный текст
  if (!parseResult.isJson) {
    return (
      <pre className={`whitespace-pre-wrap break-words ${className}`}>
        {data}
      </pre>
    );
  }

  return (
    <div className={`relative group ${className}`}>
      <button
        onClick={handleCopy}
        className="absolute top-2 right-2 p-1.5 rounded bg-muted/80 hover:bg-muted opacity-0 group-hover:opacity-100 transition-opacity"
        title="Копировать JSON"
      >
        {copied ? (
          <Check size={14} className="text-green-500" />
        ) : (
          <Copy size={14} className="text-muted-foreground" />
        )}
      </button>
      <div className="font-mono text-xs leading-relaxed">
        <JsonNode data={parseResult.data} />
      </div>
    </div>
  );
}
