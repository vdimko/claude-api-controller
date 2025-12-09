import sys
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Security
    claude_api_key: str

    # MongoDB
    mongodb_url: str = "mongodb://claude_user:claude_pass_2024@localhost:27018/claude_api"
    mongodb_database: str = "claude_api"

    # Claude CLI
    claude_timeout: int = 120
    agents_dir: str = str(Path(__file__).parent.parent.parent / "CUSTOM_AGENTS")

    # Server
    host: str = "127.0.0.1"
    port: int = 8000

    # CORS - for Next.js frontend
    cors_origins: List[str] = ["http://localhost:3000"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    try:
        return Settings()
    except Exception as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print("CONFIGURATION ERROR", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\n{e}\n", file=sys.stderr)
        print("Create a .env file with the following content:", file=sys.stderr)
        print("  CLAUDE_API_KEY=your-secret-api-key", file=sys.stderr)
        print("  MONGODB_URL=mongodb://claude_user:claude_pass_2024@localhost:27018/claude_api", file=sys.stderr)
        print(f"\n{'='*60}\n", file=sys.stderr)
        sys.exit(1)
