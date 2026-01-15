import logging
from typing import Annotated

from agents import RunContextWrapper, function_tool
from pydantic import Field

from app.domain.entities import AgentContextDTO

logger = logging.getLogger(__name__)


@function_tool
async def get_occupancy(
    wrapper: RunContextWrapper[AgentContextDTO],
    unit_id: Annotated[str, Field(description="The ID of the room to get the occupancy for")],
) -> str | None:
    """Get the occupancy of a room"""
    agent_context = wrapper.context
    logger.info(f"Conversation ID: {agent_context.conversation_id}")
    return f"The occupancy of the unit {unit_id} is unoccupied."
