# Claude API Controller

FastAPI service that exposes local Claude CLI as an async HTTP API.

## Quick Start

```bash
# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and set CLAUDE_API_KEY

# Run
./start.sh
```

## API

All endpoints (except `/health`) require `X-API-Key` header.

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/run` | Submit task `{agent_name, prompt, timeout?}` → `{task_id}` |
| GET | `/status/{task_id}` | Get task status and result |
| GET | `/tasks` | List all tasks |
| DELETE | `/tasks/{task_id}` | Delete task |
| GET | `/health` | Health check (no auth) |

## Agents

Create agent directories under `CUSTOM_AGENTS/`:

```
CUSTOM_AGENTS/
└── my_agent/
    └── CLAUDE.md  # Optional agent instructions
```

Tasks run `claude -p "{prompt}"` in the agent's directory.

## Example

```bash
# Submit task
curl -X POST http://localhost:8000/run \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "my_agent", "prompt": "Hello"}'
# {"task_id": "abc-123"}

# Poll status
curl http://localhost:8000/status/abc-123 -H "X-API-Key: your-key"
# {"status": "completed", "result": "..."}
```
