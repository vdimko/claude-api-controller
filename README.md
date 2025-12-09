# Claude API Controller v2.0

FastAPI service that exposes local Claude CLI as an async HTTP API with MongoDB persistence and Web UI.

## Features

- **MongoDB Storage**: Tasks persist across restarts (Docker container on port 27018)
- **Web Dashboard**: Next.js UI with shadcn/ui for task management
- **API Access**: RESTful endpoints for programmatic control
- **Localhost Only**: All services bind to 127.0.0.1 for security

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
4. Status: `pending` → `running` → `completed` | `failed` | `timeout`
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
| POST | `/api/run` | Submit task `{agent_name, prompt, timeout?}` → `{task_id}` |
| GET | `/api/status/{task_id}` | Get task status, result, and prompt |
| GET | `/api/tasks` | List tasks (optional `?agent_name=` filter) |
| DELETE | `/api/tasks/{task_id}` | Delete task |
| GET | `/api/agents` | List available agents |
| GET | `/health` | Health check (no auth) |

## Agents

Create agent directories under `CUSTOM_AGENTS/`:

```
CUSTOM_AGENTS/
└── my_agent/
    └── CLAUDE.md  # Optional agent instructions
```

Tasks run `claude -p "{prompt}"` in the agent's directory.

## Example API Usage

```bash
# Submit task
curl -X POST http://localhost:8000/api/run \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "my_agent", "prompt": "Hello"}'
# {"task_id": "abc-123"}

# Poll status
curl http://localhost:8000/api/status/abc-123 -H "X-API-Key: your-key"
# {"status": "completed", "result": "..."}

# List tasks with filter
curl "http://localhost:8000/api/tasks?agent_name=my_agent" -H "X-API-Key: your-key"

# Delete task
curl -X DELETE http://localhost:8000/api/tasks/abc-123 -H "X-API-Key: your-key"

# List agents
curl http://localhost:8000/api/agents -H "X-API-Key: your-key"
# {"agents": [{"name": "my_agent", "has_claude_md": true}]}
```

## Project Structure

```
Claude_API/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── main.py        # App init, CORS, lifespan
│   │   ├── config.py      # Pydantic Settings
│   │   ├── database.py    # Motor MongoDB client
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic
│   │   ├── models/        # MongoDB document models
│   │   └── schemas/       # Request/Response schemas
│   └── requirements.txt
├── frontend/          # Next.js Web UI
│   └── src/
│       ├── app/           # Pages (App Router)
│       ├── components/    # React components
│       ├── hooks/         # Custom hooks
│       └── lib/           # API client
├── docker/            # MongoDB Docker config
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

## Web UI Features

- **Create tasks**: Select agent, enter prompt, submit
- **View tasks**: Real-time status updates (3s polling)
- **Filter by agent**: Dropdown selector
- **Delete tasks**: Remove from database
- **Status badges**: Color-coded task states

## Legacy Version

Original single-file version (without MongoDB) preserved in `legacy/`:

```bash
cd legacy
CLAUDE_API_KEY="your-key" python3 main.py
```
