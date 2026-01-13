from agents import function_tool, RunContextWrapper
from pydantic import Field
from typing import Annotated
from app.domain.entities import AgentContextDTO
from typing import Optional
import logging

logger = logging.getLogger(__name__)

@function_tool
async def get_occupancy(
    wrapper: RunContextWrapper[AgentContextDTO],
    unit_id: Annotated[str, Field(description="The ID of the room to get the occupancy for")]
) -> Optional[str]:
    """
    Get the occupancy of a room
    """
    agent_context = wrapper.context
    logger.info(f"Conversation ID: {agent_context.conversation_id}")
    return f"The occupancy of the unit {unit_id} is unoccupied."