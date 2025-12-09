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

Services will be available at:
- **Web UI**: http://localhost:3000
- **API**: http://localhost:8000
- **MongoDB**: localhost:27018

## Manual Start

```bash
# Start MongoDB
cd docker && docker-compose up -d

# Start Backend
cd backend
pip install -r requirements.txt
CLAUDE_API_KEY="your-key" python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Start Frontend (new terminal)
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
| GET | `/api/tasks` | List all tasks |
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

# List agents
curl http://localhost:8000/api/agents -H "X-API-Key: your-key"
# {"agents": [{"name": "my_agent", "has_claude_md": true}]}
```

## Project Structure

```
Claude_API/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── routes/
│   │   ├── services/
│   │   └── models/
│   └── requirements.txt
├── frontend/          # Next.js Web UI
│   └── src/
├── docker/            # MongoDB Docker config
├── legacy/            # Old single-file version
├── CUSTOM_AGENTS/     # Agent directories
└── start.sh           # All-in-one starter
```

## Environment Variables

See `.env.example` for all options. Key variables:

- `CLAUDE_API_KEY` (required): API authentication key
- `MONGODB_URL`: MongoDB connection string (default: localhost:27018)
- `CLAUDE_TIMEOUT`: Command timeout in seconds (default: 120)

## Legacy Version

The original single-file version (without MongoDB) is preserved in `legacy/`:

```bash
cd legacy
CLAUDE_API_KEY="your-key" python3 main.py
```
