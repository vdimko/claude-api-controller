# Claude API Controller v2.4

FastAPI service that exposes local Claude CLI as an async HTTP API with MongoDB persistence and Web UI.

## Features

- **Full Claude CLI Support**: All ~30 CLI options available via API and UI
- **MongoDB Storage**: Tasks persist across restarts (Docker container on port 27018)
- **Web Dashboard**: Next.js UI with neon underground theme, dark/light modes
- **API Access**: RESTful endpoints for programmatic control
- **Task Management**: Stop running tasks, delete, real-time status updates
- **Dual Logging**: File logs + MongoDB for queryable history
- **Settings Persistence**: Per-agent settings saved in browser localStorage
- **JSON Viewer**: Pretty syntax-highlighted JSON results with collapsible nodes

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Browser   │────▶│  Next.js UI     │────▶│  FastAPI        │
│   (localhost)   │     │  (port 3000)    │     │  (port 8000)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        ▼
                                                ┌─────────────────┐
                                                │  MongoDB        │
                                                │  (port 27018)   │
                                                └─────────────────┘
```

### Task Flow

1. Submit task → `POST /api/run` → returns `task_id`
2. Task stored in MongoDB with status `pending`
3. Background coroutine runs `claude -p "{prompt}"` in agent directory
4. Status: `pending` → `running` → `completed` | `failed` | `timeout` | `cancelled`
5. Poll `GET /api/status/{task_id}` until terminal state

## Quick Start

```bash
# 1. Start Docker (required for MongoDB)
open -a Docker  # macOS

# 2. Configure
cp .env.example .env
# Edit .env and set CLAUDE_API_KEY

# 3. Run all services
./start.sh
```

Services:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Manual Start

```bash
# MongoDB
cd docker && docker-compose up -d

# Backend
cd backend
python3 -m pip install -r requirements.txt
CLAUDE_API_KEY="your-key" python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

## API Endpoints

All endpoints (except `/health`) require `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/run` | Submit task `{agent_name, prompt, timeout?, options?}` → `{task_id}` |
| GET | `/api/status/{task_id}` | Get task status, result, duration, and prompt |
| GET | `/api/tasks` | List tasks (optional `?agent_name=` filter) |
| POST | `/api/tasks/{task_id}/stop` | Stop running task |
| DELETE | `/api/tasks/{task_id}` | Delete task |
| GET | `/api/agents` | List available agents |
| GET | `/api/logs` | Get logs (optional `?agent_name=`, `?limit=`) |
| GET | `/health` | Health check (no auth) |

## Claude CLI Options

All Claude CLI options supported via `options` field in `/api/run`:

```json
{
  "agent_name": "my_agent",
  "prompt": "Hello",
  "options": {
    "model": "sonnet",
    "output_format": "json",
    "system_prompt": "You are helpful assistant",
    "json_schema": {"type": "object", "properties": {...}},
    "verbose": true,
    "allowed_tools": ["Read", "Bash(git:*)"],
    "permission_mode": "bypassPermissions"
  }
}
```

### Available Options

| Option | Type | Description |
|--------|------|-------------|
| `model` | string | Model: `sonnet`, `opus`, `haiku` |
| `output_format` | string | Output: `text`, `json`, `stream-json` |
| `system_prompt` | string | Override CLAUDE.md |
| `append_system_prompt` | string | Add to system prompt |
| `json_schema` | object | JSON Schema for structured output |
| `verbose` | boolean | Verbose output |
| `allowed_tools` | string[] | Allowed tools list |
| `disallowed_tools` | string[] | Disallowed tools list |
| `dangerously_skip_permissions` | boolean | Skip permission checks |
| `permission_mode` | string | `acceptEdits`, `bypassPermissions`, `default`, `dontAsk`, `plan` |
| `continue_session` | boolean | Continue last session |
| `resume_session` | string | Resume session by ID |
| `mcp_config` | string[] | MCP config files |
| `fallback_model` | string | Fallback model |
| `add_dirs` | string[] | Additional working directories |

## Agents

Create agent directories under `CUSTOM_AGENTS/`:

```
CUSTOM_AGENTS/
├── my_agent/
│   └── CLAUDE.md  # Agent instructions (used as system prompt by default)
├── bold_json/
│   └── CLAUDE.md  # JSON response agent
└── pushkin/
    └── CLAUDE.md  # Pushkin-style response agent
```

CLAUDE.md is automatically used as system prompt unless overridden in options.

## Example API Usage

```bash
# Submit task with options
curl -X POST http://localhost:8000/api/run \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "my_agent",
    "prompt": "Hello",
    "options": {
      "model": "sonnet",
      "output_format": "json"
    }
  }'
# {"task_id": "abc-123"}

# Poll status
curl http://localhost:8000/api/status/abc-123 -H "X-API-Key: your-key"
# {"status": "completed", "result": "...", "duration_sec": 5.2}

# Stop running task
curl -X POST http://localhost:8000/api/tasks/abc-123/stop -H "X-API-Key: your-key"

# List tasks with filter
curl "http://localhost:8000/api/tasks?agent_name=my_agent" -H "X-API-Key: your-key"

# Get logs
curl "http://localhost:8000/api/logs?agent_name=my_agent&limit=50" -H "X-API-Key: your-key"

# List agents
curl http://localhost:8000/api/agents -H "X-API-Key: your-key"
# {"agents": [{"name": "my_agent", "has_claude_md": true}]}
```

## Web UI Features

- **Create tasks**: Select agent, enter prompt, configure CLI options
- **CLI Options Panel**: Collapsible panel with all Claude CLI settings
- **Per-agent Settings**: Options saved in localStorage for each agent
- **View tasks**: Real-time status updates (3s polling)
- **Stop/Delete**: Control running tasks
- **JSON Viewer**: Pretty syntax-highlighted results with collapsible nodes
- **Filter by agent**: Dropdown selector (syncs tasks and logs)
- **Status badges**: Color-coded task states (Russian UI)
- **Dual logging**: View logs in collapsible bottom panel
- **Dark/Light modes**: Theme toggle with neon underground style

## Project Structure

```
Claude_API/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── main.py        # App init, CORS, lifespan
│   │   ├── config.py      # Pydantic Settings
│   │   ├── database.py    # Motor MongoDB client
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic (claude_executor, task_service)
│   │   ├── models/        # MongoDB document models
│   │   └── schemas/       # Request/Response schemas (ClaudeOptions)
│   └── requirements.txt
├── frontend/          # Next.js Web UI
│   └── src/
│       ├── app/           # Pages (App Router)
│       ├── components/    # React components
│       │   ├── tasks/     # TaskForm, TaskList, TaskCard, TaskOptions
│       │   ├── logs/      # LogPanel
│       │   └── ui/        # Base components, JsonViewer
│       ├── hooks/         # Custom hooks (use-tasks, use-logs)
│       └── lib/           # API client
├── docker/            # MongoDB Docker config
├── logs/              # File logs per agent
├── legacy/            # Original single-file version
├── CUSTOM_AGENTS/     # Agent directories
├── .env.example       # Environment template
└── start.sh           # All-in-one starter
```

## Environment Variables

See `.env.example` for all options.

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CLAUDE_API_KEY` | Yes | - | API authentication key |
| `MONGODB_URL` | No | `mongodb://...@localhost:27018/claude_api` | MongoDB connection |
| `CLAUDE_TIMEOUT` | No | `120` | Command timeout (seconds) |
| `AGENTS_DIR` | No | `./CUSTOM_AGENTS` | Agent directories path |
| `CORS_ORIGINS` | No | `["http://localhost:3000"]` | Allowed CORS origins |

## Version History

- **v2.4**: Full Claude CLI options support, settings persistence, JSON viewer
- **v2.3**: Task duration tracking, CLAUDE.md system prompt
- **v2.2**: Neon underground theme, dark/light mode toggle
- **v2.1**: Stop/delete tasks, dual logging (file + MongoDB), Russian UI
- **v2.0**: MongoDB storage, Next.js Web UI, modular architecture
- **v1.0**: Single-file FastAPI with in-memory storage (see `legacy/`)

## Legacy Version

Original single-file version (without MongoDB) preserved in `legacy/`:

```bash
cd legacy
CLAUDE_API_KEY="your-key" python3 main.py
```
