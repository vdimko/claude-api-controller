# Claude API Controller v2.4

Сервак на FastAPI, который выставляет локальный Claude CLI как HTTP API с MongoDB и Web UI. Короче, управляешь Claude через браузер или curl — красота!

## Чё умеет

- **Все опции Claude CLI**: ~30 настроек прямо из UI или API
- **MongoDB**: Задачи сохраняются, перезапуск не страшен
- **Web UI**: Неоновая тема, тёмный/светлый режим, всё по-пацански
- **REST API**: Для автоматизации и скриптов
- **Управление задачами**: Останавливай, удаляй, следи в реалтайме
- **Логирование**: В файлы + MongoDB, потом можно грепать
- **Настройки запоминаются**: Для каждого агента отдельно в localStorage
- **JSON Viewer**: Красивый вывод JSON с подсветкой и сворачиванием

## Архитектура

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Браузер       │────▶│  Next.js UI     │────▶│  FastAPI        │
│   (localhost)   │     │  (порт 3000)    │     │  (порт 8000)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  MongoDB        │
                                                │  (порт 27018)   │
                                                └─────────────────┘
```

### Как задача живёт

1. Кидаешь задачу → `POST /api/run` → получаешь `task_id`
2. Задача ложится в MongoDB со статусом `Ждём`
3. Фоновый процесс запускает `claude -p "{prompt}"` в папке агента
4. Статусы: `Ждём` → `Пашет` → `Готово` | `Обосрался` | `Завис` | `Отменено`
5. Поллишь `GET /api/status/{task_id}` пока не закончится

## Быстрый старт

```bash
# 1. Запусти Docker (нужен для MongoDB)
open -a Docker  # macOS

# 2. Настрой конфиг
cp .env.example .env
# Впиши CLAUDE_API_KEY в .env

# 3. Погнали!
./start.sh
```

Сервисы:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **Swagger**: http://localhost:8000/docs

## Ручной запуск

```bash
# MongoDB
cd docker && docker-compose up -d

# Backend
cd backend
python3 -m pip install -r requirements.txt
CLAUDE_API_KEY="твой-ключ" python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (в другом терминале)
cd frontend
npm install
npm run dev
```

## API Эндпоинты

Везде (кроме `/health`) нужен заголовок `X-API-Key`.

| Метод | Эндпоинт | Чё делает |
|-------|----------|-----------|
| POST | `/api/run` | Кинуть задачу `{agent_name, prompt, timeout?, options?}` → `{task_id}` |
| GET | `/api/status/{task_id}` | Статус, результат, время выполнения |
| GET | `/api/tasks` | Список задач (можно `?agent_name=` фильтр) |
| POST | `/api/tasks/{task_id}/stop` | Остановить задачу |
| DELETE | `/api/tasks/{task_id}` | Удалить задачу |
| GET | `/api/agents` | Список агентов |
| GET | `/api/logs` | Логи (можно `?agent_name=`, `?limit=`) |
| GET | `/health` | Проверка здоровья (без авторизации) |

## Опции Claude CLI

Все опции CLI доступны через поле `options` в `/api/run`:

```json
{
  "agent_name": "мой_агент",
  "prompt": "Привет",
  "options": {
    "model": "sonnet",
    "output_format": "json",
    "system_prompt": "Ты полезный помощник",
    "json_schema": {"type": "object", "properties": {...}},
    "verbose": true,
    "allowed_tools": ["Read", "Bash(git:*)"],
    "permission_mode": "bypassPermissions"
  }
}
```

### Доступные опции

| Опция | Тип | Чё делает |
|-------|-----|-----------|
| `model` | string | Модель: `sonnet`, `opus`, `haiku` |
| `output_format` | string | Формат: `text`, `json`, `stream-json` |
| `system_prompt` | string | Переопределить CLAUDE.md |
| `append_system_prompt` | string | Добавить к системному промпту |
| `json_schema` | object | JSON Schema для структурированного вывода |
| `verbose` | boolean | Подробный вывод |
| `allowed_tools` | string[] | Разрешённые инструменты |
| `disallowed_tools` | string[] | Запрещённые инструменты |
| `dangerously_skip_permissions` | boolean | Пропустить проверки (осторожно!) |
| `permission_mode` | string | `acceptEdits`, `bypassPermissions`, `default`, `dontAsk`, `plan` |
| `continue_session` | boolean | Продолжить последнюю сессию |
| `resume_session` | string | Возобновить сессию по ID |
| `mcp_config` | string[] | Файлы конфига MCP |
| `fallback_model` | string | Запасная модель |
| `add_dirs` | string[] | Дополнительные рабочие директории |

## Агенты

Создавай папки агентов в `CUSTOM_AGENTS/`:

```
CUSTOM_AGENTS/
├── мой_агент/
│   └── CLAUDE.md  # Инструкции (по умолчанию как system prompt)
├── bold_json/
│   └── CLAUDE.md  # Агент для JSON ответов
└── pushkin/
    └── CLAUDE.md  # Агент в стиле Пушкина
```

CLAUDE.md автоматом используется как system prompt, если не переопределишь в options.

## Примеры использования API

```bash
# Кинуть задачу с опциями
curl -X POST http://localhost:8000/api/run \
  -H "X-API-Key: твой-ключ" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "мой_агент",
    "prompt": "Привет",
    "options": {
      "model": "sonnet",
      "output_format": "json"
    }
  }'
# {"task_id": "abc-123"}

# Проверить статус
curl http://localhost:8000/api/status/abc-123 -H "X-API-Key: твой-ключ"
# {"status": "completed", "result": "...", "duration_sec": 5.2}

# Остановить задачу
curl -X POST http://localhost:8000/api/tasks/abc-123/stop -H "X-API-Key: твой-ключ"

# Список задач с фильтром
curl "http://localhost:8000/api/tasks?agent_name=мой_агент" -H "X-API-Key: твой-ключ"

# Посмотреть логи
curl "http://localhost:8000/api/logs?agent_name=мой_агент&limit=50" -H "X-API-Key: твой-ключ"

# Список агентов
curl http://localhost:8000/api/agents -H "X-API-Key: твой-ключ"
# {"agents": [{"name": "мой_агент", "has_claude_md": true}]}
```

## Фичи Web UI

- **Создание задач**: Выбираешь агента, пишешь промпт, настраиваешь опции
- **Панель настроек CLI**: Сворачиваемая панель со всеми опциями Claude
- **Настройки по агентам**: Сохраняются в localStorage для каждого агента
- **Список задач**: Реалтайм обновление (каждые 3 сек)
- **Стоп/Удалить**: Управляй запущенными задачами
- **JSON Viewer**: Красивый вывод с подсветкой синтаксиса и сворачиванием
- **Фильтр по агенту**: Выпадашка (синхронизирует задачи и логи)
- **Статусы по-пацански**: Ждём, Пашет, Готово, Обосрался, Завис, Отменено
- **Логи внизу**: Сворачиваемая панель с логами
- **Тёмная/Светлая тема**: Переключалка с неоновым стилем

## Структура проекта

```
Claude_API/
├── backend/           # FastAPI приложение
│   ├── app/
│   │   ├── main.py        # Инициализация, CORS, lifespan
│   │   ├── config.py      # Pydantic Settings
│   │   ├── database.py    # Motor MongoDB клиент
│   │   ├── routes/        # API эндпоинты
│   │   ├── services/      # Бизнес-логика (claude_executor, task_service)
│   │   ├── models/        # MongoDB модели документов
│   │   └── schemas/       # Request/Response схемы (ClaudeOptions)
│   └── requirements.txt
├── frontend/          # Next.js Web UI
│   └── src/
│       ├── app/           # Страницы (App Router)
│       ├── components/    # React компоненты
│       │   ├── tasks/     # TaskForm, TaskList, TaskCard, TaskOptions
│       │   ├── logs/      # LogPanel
│       │   └── ui/        # Базовые компоненты, JsonViewer
│       ├── hooks/         # Хуки (use-tasks, use-logs)
│       └── lib/           # API клиент
├── docker/            # MongoDB Docker конфиг
├── logs/              # Файловые логи по агентам
├── legacy/            # Старая версия (один файл)
├── CUSTOM_AGENTS/     # Папки агентов
├── .env.example       # Шаблон переменных окружения
└── start.sh           # Запуск всего
```

## Переменные окружения

Смотри `.env.example` для полного списка.

| Переменная | Обязательно | По умолчанию | Чё делает |
|------------|-------------|--------------|-----------|
| `CLAUDE_API_KEY` | Да | - | Ключ для авторизации API |
| `MONGODB_URL` | Нет | `mongodb://...@localhost:27018/claude_api` | Подключение к MongoDB |
| `CLAUDE_TIMEOUT` | Нет | `120` | Таймаут команды (секунды) |
| `AGENTS_DIR` | Нет | `./CUSTOM_AGENTS` | Путь к папкам агентов |
| `CORS_ORIGINS` | Нет | `["http://localhost:3000"]` | Разрешённые CORS origins |

## История версий

- **v2.4**: Все опции Claude CLI, сохранение настроек, JSON viewer
- **v2.3**: Трекинг времени выполнения, CLAUDE.md как system prompt
- **v2.2**: Неоновая тема, переключатель тёмный/светлый режим
- **v2.1**: Стоп/удаление задач, двойное логирование, русский UI
- **v2.0**: MongoDB, Next.js Web UI, модульная архитектура
- **v1.0**: Один файл FastAPI с хранением в памяти (смотри `legacy/`)

## Legacy версия

Старая версия одним файлом (без MongoDB) лежит в `legacy/`:

```bash
cd legacy
CLAUDE_API_KEY="твой-ключ" python3 main.py
```
