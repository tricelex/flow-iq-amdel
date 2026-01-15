"""Domain entities/DTOs."""

# Add your domain entities here

from dataclasses import dataclass

from pydantic import BaseModel


@dataclass
class AgentContextDTO:
    conversation_id: str
    org_id: str


class ChatMessageDTO(BaseModel):
    message: str
