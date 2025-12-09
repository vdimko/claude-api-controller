# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI service with MongoDB persistence and Next.js Web UI that provides async endpoints to control a local Claude CLI installation. Tasks are submitted with an `agent_name` which determines the working directory where `claude -p "{prompt}"` executes.

## Commands

```bash
# Start all services (MongoDB + Backend + Frontend)
./start.sh

# Or start individually:

# MongoDB
cd docker && docker-compose up -d

# Backend
cd backend
python3 -m pip install -r requirements.txt
CLAUDE_API_KEY="test-key" python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Run backend tests
cd backend
CLAUDE_API_KEY="test-key" python3 -m pytest tests/ -v
```

## Configuration

Copy `.env.example` to `.env`. Required: `CLAUDE_API_KEY`. Server exits with error if missing.

Environment variables:
- `CLAUDE_API_KEY` (required) - API authentication
- `MONGODB_URL` - MongoDB connection string (default: localhost:27018)
- `CLAUDE_TIMEOUT` - Command timeout seconds (default: 120)
- `AGENTS_DIR` - Agent directories location (default: ./CUSTOM_AGENTS)
- `CORS_ORIGINS` - Allowed CORS origins (default: ["http://localhost:3000"])

## Architecture

### Backend (FastAPI + MongoDB)

Modular structure in `backend/app/`:

- **main.py** - App initialization, CORS, lifespan (MongoDB connection)
- **config.py** - Pydantic Settings for configuration
- **database.py** - Motor async MongoDB client
- **routes/** - API endpoints (tasks.py, agents.py, health.py)
- **services/** - Business logic (task_service.py, claude_executor.py)
- **models/** - MongoDB document models
- **schemas/** - Request/Response Pydantic models
- **auth/** - API key verification

API Endpoints (prefixed with `/api`):
- **POST /api/run** - Submit task, returns `task_id`
- **GET /api/status/{task_id}** - Get task status and result
- **GET /api/tasks** - List all tasks (with optional agent_name filter)
- **DELETE /api/tasks/{task_id}** - Delete task
- **GET /api/agents** - List available agents
- **GET /health** - Health check (no auth)

### Frontend (Next.js + shadcn/ui)

Located in `frontend/src/`:

- **app/** - Next.js app router pages
- **components/** - React components (tasks/, agents/, ui/)
- **hooks/** - Custom React hooks (use-tasks.ts, use-agents.ts)
- **lib/** - API client and utilities
- **types/** - TypeScript type definitions

### MongoDB

Docker container on port 27018 (non-standard for security):
- Database: `claude_api`
- Collection: `tasks`
- User: `claude_user` / `claude_pass_2024`

### Legacy Version

Original single-file version preserved in `legacy/` for reference and fallback.

## Testing Notes

Backend tests in `backend/tests/` use mongomock-motor for database mocking.
