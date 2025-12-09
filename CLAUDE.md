# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FastAPI service that provides async endpoints to control a local Claude CLI installation. Tasks are submitted with an `agent_name` which determines the working directory where `claude -p "{prompt}"` executes.

## Commands

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Start server (uses PORT from .env)
./start.sh
# or
python3 main.py

# Run tests
CLAUDE_API_KEY="test-key" python3 -m pytest test_main.py -v

# Run single test
CLAUDE_API_KEY="test-key" python3 -m pytest test_main.py::TestClassName::test_method -v
```

## Configuration

Copy `.env.example` to `.env`. Required: `CLAUDE_API_KEY`. Server exits with error if missing.

Environment variables: `CLAUDE_API_KEY` (required), `CLAUDE_TIMEOUT`, `AGENTS_DIR`, `HOST`, `PORT`.

## Architecture

Single-file FastAPI app (`main.py`) with background task execution pattern:

- **POST /run** - Accepts `{agent_name, prompt, timeout?}`, spawns background task, returns `task_id`
- **GET /status/{task_id}** - Poll for task result (pending/running/completed/failed/timeout)
- **GET /tasks** - List all tasks
- **DELETE /tasks/{task_id}** - Remove task from store
- **GET /health** - No auth required

Tasks execute `claude -p "{prompt}"` in `AGENTS_DIR/{agent_name}/` directory. Each agent needs its own subdirectory under `CUSTOM_AGENTS/` with optional `CLAUDE.md` for agent-specific instructions.

Authentication via `X-API-Key` header on all endpoints except `/health`.

## Testing Notes

Tests use `tmp_path` fixture to create isolated agent directories. The `setup_test_agent` fixture auto-creates test agent directory and sets `main.AGENTS_DIR`.
