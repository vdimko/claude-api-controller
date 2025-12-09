# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI service with MongoDB persistence and Next.js Web UI that provides async endpoints to control a local Claude CLI installation. Tasks are submitted with an `agent_name` which determines the working directory where `claude -p "{prompt}"` executes.

## Commands

```bash
# Start all services (MongoDB + Backend + Frontend)
./start.sh

# Or start individually:

# MongoDB (Docker required)
cd docker && docker-compose up -d

# Backend
cd backend
python3 -m pip install -r requirements.txt
CLAUDE_API_KEY="your-key" python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm install
npm run dev
```

## Configuration

Copy `.env.example` to `.env`. Required: `CLAUDE_API_KEY`. Server exits with error if missing.

Key environment variables:
- `CLAUDE_API_KEY` (required) - API authentication
- `MONGODB_URL` - MongoDB connection (default: mongodb://claude_user:claude_pass_2024@localhost:27018/claude_api)
- `CLAUDE_TIMEOUT` - Command timeout seconds (default: 120)
- `AGENTS_DIR` - Agent directories location (default: ./CUSTOM_AGENTS)

## Architecture

### Task Lifecycle

1. Client submits task via `POST /api/run` with `agent_name` and `prompt`
2. Task stored in MongoDB with status `pending`, returns `task_id`
3. Background coroutine executes `claude -p "{prompt}"` in agent's directory
4. Status transitions: `pending` → `running` → `completed|failed|timeout`
5. Client polls `GET /api/status/{task_id}` until terminal state

### Backend (FastAPI + MongoDB)

Modular structure in `backend/app/`:

- **main.py** - App initialization, CORS, lifespan (MongoDB connection)
- **config.py** - Pydantic Settings for configuration
- **database.py** - Motor async MongoDB client
- **routes/** - API endpoints (tasks.py, agents.py, health.py)
- **services/task_service.py** - MongoDB CRUD operations
- **services/claude_executor.py** - Spawns `claude -p` subprocess with timeout
- **models/task.py** - TaskDocument and TaskStatus enum
- **schemas/** - Request/Response Pydantic models
- **auth/api_key.py** - X-API-Key header verification

### Frontend (Next.js + shadcn/ui)

Located in `frontend/src/`:

- **app/** - Next.js App Router pages
- **components/tasks/** - TaskForm, TaskList, TaskCard, TaskStatusBadge
- **components/ui/** - shadcn-style base components (Button, Card, Badge, etc.)
- **hooks/use-tasks.ts** - Fetches tasks with 3s polling interval
- **lib/api.ts** - API client with X-API-Key header

### MongoDB

Docker container on port 27018 (non-standard for security):
- Database: `claude_api`, Collection: `tasks`
- Credentials: `claude_user` / `claude_pass_2024`
- Indexes: `task_id` (unique), `agent_name`, `status`, `created_at`

### Legacy Version

Original single-file version preserved in `legacy/` for reference and fallback.
