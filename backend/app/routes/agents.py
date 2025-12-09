from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends

from ..auth import verify_api_key
from ..config import get_settings

router = APIRouter(tags=["agents"])


@router.get("/agents")
async def list_agents(
    _: Annotated[str, Depends(verify_api_key)]
) -> dict:
    """List available agents for the UI."""
    settings = get_settings()
    agents_path = Path(settings.agents_dir)

    agents = []
    if agents_path.exists():
        for item in agents_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                agent_info = {
                    "name": item.name,
                    "has_claude_md": (item / "CLAUDE.md").exists()
                }
                agents.append(agent_info)

    return {"agents": sorted(agents, key=lambda x: x["name"])}
